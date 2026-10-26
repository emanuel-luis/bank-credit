"""Export job: contracts, batch checks, deterministic CSV, atomic publish, run metadata.

Runs on SQLite with the request_events dataset; the view datasets use an injected source because
the views exist only on Postgres (their real results are checked in tests/integration).
"""

import json
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from test_simulate import simulated_db

from bank_credit.app.cli import main
from bank_credit.app.contracts.exports import (
    CONTRACTS,
    RequestEventRow,
    SlaBreachWeeklyRow,
    StageIntervalRow,
    columns_of,
)
from bank_credit.app.domain.enums import JobStatus
from bank_credit.app.jobs import export as export_module
from bank_credit.app.jobs.export import (
    ExportCheckFailed,
    ExportError,
    check_request_events,
    check_sla_breach_weekly,
    check_stage_intervals,
    csv_cell,
    run_export,
)
from bank_credit.app.models import JobRun

T0 = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)
FUTURE = datetime(2999, 1, 1, tzinfo=UTC)


def event(request_id=1, seq=1, minutes=0, id=None, **overrides):
    values = {
        "id": id or request_id * 100 + seq,
        "request_id": request_id,
        "seq": seq,
        "event_type": "STAGE_APPROVED" if seq > 1 else "SUBMITTED",
        "from_status": "IN_REVIEW" if seq > 1 else None,
        "to_status": "IN_REVIEW",
        "stage_code": "document_check",
        "sector_code": "retail_center",
        "sla_due_at": None,
        "actor_user_id": None,
        "job_run_id": None,
        "reason": None,
        "occurred_at": T0 + timedelta(minutes=minutes),
        "recorded_at": T0 + timedelta(minutes=minutes),
    }
    return RequestEventRow(**{**values, **overrides})


def interval(request_id=1, entry_seq=1, **overrides):
    values = {
        "request_id": request_id,
        "entry_seq": entry_seq,
        "stage_code": "screening",
        "stage_position": 2,
        "sector_code": "retail_center",
        "entered_at": T0,
        "exited_at": T0 + timedelta(hours=2),
        "exit_event": "STAGE_APPROVED",
        "sla_due_at": T0 + timedelta(hours=24),
        "duration_s": Decimal("7200.000000"),
        "sla_breached": False,
    }
    return StageIntervalRow(**{**values, **overrides})


def weekly(sector="retail_center", week=date(2026, 3, 2), closed=8, breached=2, rate="0.2500"):
    return SlaBreachWeeklyRow(
        sector_code=sector,
        week_start=week,
        closed=closed,
        breached=breached,
        breach_rate=Decimal(rate),
    )


# --- Contracts ---


def test_every_dataset_has_a_contract_with_a_version_and_source():
    assert set(CONTRACTS) == {"request_events", "stage_intervals", "sla_breach_weekly"}
    for contract in CONTRACTS.values():
        assert contract.schema_version == 1
        assert contract.source


def test_columns_of_lists_name_type_and_nullability_in_field_order():
    columns = {c["name"]: c for c in columns_of(RequestEventRow)}
    assert list(columns) == list(RequestEventRow.model_fields)
    assert columns["seq"] == {"name": "seq", "type": "integer", "nullable": False}
    assert columns["reason"] == {"name": "reason", "type": "string", "nullable": True}
    assert columns["occurred_at"]["type"] == "timestamp_utc"
    assert columns["job_run_id"]["type"] == "uuid"
    assert {c["name"]: c["type"] for c in columns_of(SlaBreachWeeklyRow)} == {
        "sector_code": "string",
        "week_start": "date",
        "closed": "integer",
        "breached": "integer",
        "breach_rate": "decimal",
    }


def test_contract_rejects_naive_datetimes_unknown_columns_and_missing_values():
    good = event().model_dump()
    with pytest.raises(ValidationError):
        RequestEventRow(**{**good, "occurred_at": datetime(2026, 3, 2, 9, 0)})
    with pytest.raises(ValidationError):
        RequestEventRow(**{**good, "surprise": 1})
    with pytest.raises(ValidationError):
        RequestEventRow(**{**good, "stage_code": None})
    with pytest.raises(ValidationError):
        RequestEventRow(**{**good, "seq": 0})


def test_csv_cell_formats_are_stable():
    assert csv_cell(None) == ""
    assert csv_cell(True) == "true"
    assert csv_cell(7) == "7"
    assert csv_cell(Decimal("0.2500")) == "0.2500"
    assert csv_cell(Decimal("1E+3")) == "1000"
    assert csv_cell(date(2026, 3, 2)) == "2026-03-02"
    assert csv_cell(datetime(2026, 3, 2, 6, 0, tzinfo=UTC)) == "2026-03-02T06:00:00.000000Z"


# --- Batch checks ---


def test_request_events_check_accepts_a_sound_batch():
    rows = [event(1, 1), event(1, 2, minutes=5), event(2, 1), event(2, 2, minutes=5)]
    assert check_request_events(rows) == []


def test_request_events_check_flags_duplicates_gaps_and_time_going_back():
    assert (
        "duplicate seq [2]"
        in check_request_events([event(1, 1), event(1, 2, id=11), event(1, 2, id=12)])[0]
    )
    assert "not contiguous" in check_request_events([event(1, 1), event(1, 3)])[0]
    assert "not contiguous" in check_request_events([event(1, 2)])[0]  # must start at 1
    assert (
        "occurred_at goes back at seq 2"
        in check_request_events([event(1, 1, minutes=10), event(1, 2, minutes=5)])[0]
    )


def test_stage_interval_check_flags_exit_before_entry_and_duplicates():
    assert check_stage_intervals([interval(1, 1), interval(1, 2), interval(2, 1)]) == []
    assert check_stage_intervals([interval(exited_at=None, exit_event=None)]) == []
    bad = interval(exited_at=T0 - timedelta(minutes=1))
    assert "exited_at before entered_at" in check_stage_intervals([bad])[0]
    assert "duplicate entry_seq" in check_stage_intervals([interval(1, 1), interval(1, 1)])[0]


def test_breach_weekly_check_flags_rate_range_and_counts():
    assert (
        check_sla_breach_weekly([weekly(), weekly("mid_large_center", rate="0.0000", breached=0)])
        == []
    )
    assert "outside [0, 1]" in check_sla_breach_weekly([weekly(rate="1.2000")])[0]
    assert "outside [0, 1]" in check_sla_breach_weekly([weekly(rate="-0.1000")])[0]
    assert "exceeds closed" in check_sla_breach_weekly([weekly(closed=2, breached=3)])[0]
    assert "duplicate row" in check_sla_breach_weekly([weekly(), weekly()])[0]


# --- The job ---


@pytest.fixture(scope="module")
def history_db():
    db = simulated_db()
    yield db
    db.close()


def partition(out: Path, dataset: str, day: str) -> Path:
    return out / dataset / f"as_of={day}"


def test_export_writes_csv_and_manifest_and_records_the_run(history_db, tmp_path):
    result = run_export(history_db, "request_events", FUTURE, tmp_path)

    folder = partition(tmp_path, "request_events", "2999-01-01")
    assert result.partition == folder
    assert sorted(p.name for p in folder.iterdir()) == ["_manifest.json", "part-0.csv"]
    assert [p.name for p in (tmp_path / "request_events").iterdir()] == ["as_of=2999-01-01"]

    data = (folder / "part-0.csv").read_bytes()
    assert b"\r" not in data
    lines = data.decode("utf-8").split("\n")
    assert lines[0] == ",".join(RequestEventRow.model_fields)
    assert lines[-1] == ""
    manifest = json.loads((folder / "_manifest.json").read_text("utf-8"))
    assert manifest["row_count"] == len(lines) - 2 == result.row_count > 0
    assert manifest["sha256"] == result.sha256
    assert manifest["dataset"] == "request_events"
    assert manifest["schema_version"] == 1
    assert manifest["source"] == "request_events"
    assert manifest["as_of"] == "2999-01-01T00:00:00.000000Z"
    assert manifest["run_id"] == str(result.run_id)
    assert manifest["started_at"] <= manifest["finished_at"]
    assert manifest["columns"] == columns_of(RequestEventRow)

    run = history_db.get(JobRun, result.run_id)
    assert run is not None
    assert run.job_name == "export" and run.status is JobStatus.SUCCEEDED
    assert run.rows_read == run.rows_written == manifest["row_count"]
    assert run.params["dataset"] == "request_events"


def test_same_inputs_give_identical_bytes_and_replace_the_partition(history_db, tmp_path):
    first = run_export(history_db, "request_events", FUTURE, tmp_path)
    second = run_export(history_db, "request_events", FUTURE, tmp_path)
    assert first.sha256 == second.sha256
    assert first.run_id != second.run_id
    folder = partition(tmp_path, "request_events", "2999-01-01")
    manifest = json.loads((folder / "_manifest.json").read_text("utf-8"))
    assert manifest["run_id"] == str(second.run_id)  # the partition was replaced, not appended
    assert [p.name for p in (tmp_path / "request_events").iterdir()] == ["as_of=2999-01-01"]


def test_as_of_filters_events_by_recorded_at(history_db, tmp_path):
    result = run_export(history_db, "request_events", datetime(2000, 1, 1, tzinfo=UTC), tmp_path)
    assert result.row_count == 0  # an empty but valid partition: header and manifest only


def test_failed_check_publishes_nothing_and_marks_the_run_failed(history_db, tmp_path):
    def bad_source(_db, _as_of):
        return [
            {"sector_code": "retail_center", "week_start": date(2026, 3, 2), "closed": 4,
             "breached": 1, "breach_rate": Decimal("1.5000")}
        ]  # fmt: skip

    with pytest.raises(ExportCheckFailed, match="outside"):
        run_export(history_db, "sla_breach_weekly", FUTURE, tmp_path, source=bad_source)

    assert not (tmp_path / "sla_breach_weekly").exists()
    run = history_db.scalars(
        select(JobRun).where(JobRun.job_name == "export", JobRun.status == JobStatus.FAILED)
    ).one()
    assert run.rows_read == 1 and run.rows_written == 0
    assert run.error is not None and "ExportCheckFailed" in run.error
    history_db.delete(run)  # keep the shared module-scoped database tidy for other tests
    history_db.commit()


def test_a_row_that_breaks_the_contract_fails_the_run(history_db, tmp_path):
    def bad_source(_db, _as_of):
        return [{"sector_code": "retail_center", "week_start": "not-a-date"}]

    with pytest.raises(ExportCheckFailed, match="break the contract"):
        run_export(history_db, "sla_breach_weekly", FUTURE, tmp_path, source=bad_source)
    assert not (tmp_path / "sla_breach_weekly").exists()


def test_view_datasets_export_through_an_injected_source(history_db, tmp_path):
    rows = [
        {"sector_code": "retail_center", "week_start": date(2026, 3, 2), "closed": 8,
         "breached": 2, "breach_rate": Decimal("0.2500")}
    ]  # fmt: skip
    result = run_export(history_db, "sla_breach_weekly", FUTURE, tmp_path, source=lambda *_: rows)
    csv_file = result.partition / "part-0.csv"
    assert csv_file.read_text("utf-8") == (
        "sector_code,week_start,closed,breached,breach_rate\nretail_center,2026-03-02,8,2,0.2500\n"
    )


def test_a_crash_while_writing_leaves_no_partition(history_db, tmp_path, monkeypatch):
    def explode(*_args):
        raise OSError("disk full")

    monkeypatch.setattr(export_module, "write_csv", explode)
    with pytest.raises(OSError, match="disk full"):
        run_export(history_db, "request_events", FUTURE, tmp_path)
    assert list((tmp_path / "request_events").iterdir()) == []  # no partition, no staging left
    history_db.rollback()
    for run in history_db.scalars(select(JobRun).where(JobRun.status == JobStatus.FAILED)):
        history_db.delete(run)
    history_db.commit()


def test_a_crash_while_replacing_keeps_the_previous_partition(history_db, tmp_path, monkeypatch):
    good = run_export(history_db, "request_events", FUTURE, tmp_path)
    monkeypatch.setattr(export_module, "write_csv", lambda *_a: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        run_export(history_db, "request_events", FUTURE, tmp_path)
    assert export_module.sha256_of(good.partition / "part-0.csv") == good.sha256
    assert [p.name for p in (tmp_path / "request_events").iterdir()] == ["as_of=2999-01-01"]
    for run in history_db.scalars(select(JobRun).where(JobRun.status == JobStatus.FAILED)):
        history_db.delete(run)
    history_db.commit()


def test_input_errors_are_reported_before_a_run_is_recorded(history_db, tmp_path):
    before = history_db.scalars(select(JobRun.run_id)).all()
    with pytest.raises(ExportError, match="unknown dataset"):
        run_export(history_db, "nope", FUTURE, tmp_path)
    with pytest.raises(ExportError, match="timezone-aware"):
        run_export(history_db, "request_events", datetime(2026, 1, 1), tmp_path)
    assert history_db.scalars(select(JobRun.run_id)).all() == before


def test_parquet_without_pyarrow_explains_how_to_install_it(history_db, tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "pyarrow", None)  # makes `import pyarrow` fail
    before = history_db.scalars(select(JobRun.run_id)).all()
    with pytest.raises(ExportError, match=r"bank-credit\[parquet\]"):
        run_export(history_db, "request_events", FUTURE, tmp_path, "parquet")
    assert history_db.scalars(select(JobRun.run_id)).all() == before
    assert not (tmp_path / "request_events").exists()


def test_parquet_round_trips_when_pyarrow_is_installed(history_db, tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    first = run_export(history_db, "request_events", FUTURE, tmp_path, "parquet")
    table = pq.read_table(first.partition / "part-0.parquet")
    assert table.num_rows == first.row_count
    assert table.column_names == list(RequestEventRow.model_fields)
    second = run_export(history_db, "request_events", FUTURE, tmp_path, "parquet")
    assert first.sha256 == second.sha256


def test_export_command_has_help():
    with pytest.raises(SystemExit) as stop:
        main(["export", "--help"])
    assert stop.value.code == 0
