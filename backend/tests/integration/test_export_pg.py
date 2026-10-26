"""The export job against real Postgres and the real views."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from bank_credit.app.domain.enums import JobStatus
from bank_credit.app.jobs.export import ExportCheckFailed, run_export
from bank_credit.app.models import JobRun, RequestEvent

from .helpers import FUTURE, monday, python_intervals

pytestmark = pytest.mark.integration

DATASETS = ["request_events", "stage_intervals", "sla_breach_weekly"]


def export(engine: Engine, dataset: str, out: Path, as_of: datetime = FUTURE):
    with Session(engine, expire_on_commit=False) as db:
        return run_export(db, dataset, as_of, out)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("dataset", DATASETS)
def test_exporting_twice_with_the_same_as_of_gives_identical_bytes(
    simulated_engine, tmp_path, dataset
):
    first = export(simulated_engine, dataset, tmp_path)
    second = export(simulated_engine, dataset, tmp_path)
    assert first.row_count == second.row_count > 0
    assert first.sha256 == second.sha256
    folder = tmp_path / dataset / "as_of=2999-01-01"
    manifest = json.loads((folder / "_manifest.json").read_text("utf-8"))
    assert manifest["sha256"] == second.sha256 and manifest["run_id"] == str(second.run_id)
    assert [p.name for p in (tmp_path / dataset).iterdir()] == ["as_of=2999-01-01"]


def test_event_rows_match_the_table(simulated_engine, tmp_path):
    result = export(simulated_engine, "request_events", tmp_path)
    with Session(simulated_engine) as db:
        assert result.row_count == db.scalar(select(func.count()).select_from(RequestEvent))
        runs = db.scalars(select(JobRun).where(JobRun.job_name == "export")).all()
    assert [(r.status, r.rows_read, r.rows_written) for r in runs] == [
        (JobStatus.SUCCEEDED, result.row_count, result.row_count)
    ]


def test_interval_export_matches_python_and_hides_exits_after_as_of(simulated_engine, tmp_path):
    as_of = datetime(2026, 1, 20, tzinfo=UTC)
    result = export(simulated_engine, "stage_intervals", tmp_path, as_of)
    rows = read_csv(result.partition / "part-0.csv")

    expected = [i for i in python_intervals(simulated_engine) if i.entered_at <= as_of]
    assert len(rows) == len(expected)
    still_open = sum(1 for i in expected if i.exited_at is None or i.exited_at > as_of)
    assert sum(1 for r in rows if r["exited_at"] == "") == still_open > 0
    assert all(r["exited_at"] <= "2026-01-20T00:00:00.000000Z" for r in rows if r["exited_at"])
    assert all(r["sla_breached"] == "" for r in rows if r["exited_at"] == "")


def test_breach_export_has_only_complete_weeks(simulated_engine, tmp_path):
    as_of = datetime(2026, 1, 21, 12, 0, tzinfo=UTC)  # a Wednesday: its own week is incomplete
    result = export(simulated_engine, "sla_breach_weekly", tmp_path, as_of)
    weeks = {r["week_start"] for r in read_csv(result.partition / "part-0.csv")}
    assert weeks and max(weeks) <= "2026-01-12"  # the week of Jan 19 ends on Jan 26
    assert monday(datetime(2026, 1, 12).date()).isoformat() == "2026-01-12"


def test_a_planted_bad_row_fails_the_export_and_publishes_nothing(simulated_engine, tmp_path):
    # INSERT is allowed on the append-only table. This one skips a seq, breaking contiguity.
    with simulated_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO request_events (request_id, seq, event_type, from_status, to_status, "
                "stage_id, sector_id, sla_due_at, reason, occurred_at) "
                "SELECT request_id, seq + 2, event_type, from_status, to_status, stage_id, "
                "sector_id, sla_due_at, reason, occurred_at FROM request_events "
                "WHERE request_id = 1 ORDER BY seq DESC LIMIT 1"
            )
        )

    with pytest.raises(ExportCheckFailed, match="request 1: seq is not contiguous"):
        export(simulated_engine, "request_events", tmp_path)

    assert not (tmp_path / "request_events").exists()
    with Session(simulated_engine) as db:
        run = db.scalars(select(JobRun).where(JobRun.job_name == "export")).one()
        assert run.status is JobStatus.FAILED
        assert run.rows_written == 0 and (run.rows_read or 0) > 0
        assert run.error is not None and "not contiguous" in run.error
