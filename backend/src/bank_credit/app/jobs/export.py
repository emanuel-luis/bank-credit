"""export: publish a dataset as a checked, immutable partition of files.

Flow: read rows (as of a point in time) -> validate each row against its contract -> run the batch
checks -> write the data file and a manifest into a temp directory -> swap it into
`<out>/<dataset>/as_of=<YYYY-MM-DD>/`. A failed validation or check raises before any file is
written, so nothing is published and the job_runs row says failed. Re-running with the same
inputs rewrites the same partition with byte-identical data (stable order and formatting).

As-of semantics. request_events is bitemporal: rows are filtered by `recorded_at <= as_of`, what
the system knew then. The view datasets are derived on business time (`occurred_at`): intervals
that entered by as_of, with exits after as_of hidden; weekly rates only for weeks that ended by
as_of. A later sla-check can still write events whose occurred_at is in the past, so a rerun
after new events is a different input, not a violation of idempotence.
"""

import csv
import hashlib
import json
import logging
import os
import shutil
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from itertools import pairwise
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from bank_credit.app.contracts.exports import (
    CONTRACTS,
    ExportRow,
    RequestEventRow,
    SlaBreachWeeklyRow,
    StageIntervalRow,
    columns_of,
)
from bank_credit.app.jobs.runs import job_run
from bank_credit.app.models import RequestEvent, Sector, Stage

logger = logging.getLogger("bank_credit.jobs.export")

JOB_NAME = "export"
FORMATS = ("csv", "parquet")
MAX_REPORTED = 10  # violations listed in the error; the count covers all of them

# Reads the raw rows of a dataset as of a point in time. Tests inject one for the view datasets,
# which exist only on Postgres.
RowSource = Callable[[Session, datetime], Iterable[Mapping[str, Any]]]


class ExportError(Exception):
    """The export cannot run or must not publish."""


class ExportCheckFailed(ExportError):
    """Rows broke their contract or a batch check."""


# --- Sources ---


def _request_events(db: Session, as_of: datetime) -> Sequence[Mapping[str, Any]]:
    stmt = (
        select(
            RequestEvent.id,
            RequestEvent.request_id,
            RequestEvent.seq,
            RequestEvent.event_type,
            RequestEvent.from_status,
            RequestEvent.to_status,
            Stage.code.label("stage_code"),
            Sector.code.label("sector_code"),
            RequestEvent.sla_due_at,
            RequestEvent.actor_user_id,
            RequestEvent.job_run_id,
            RequestEvent.reason,
            RequestEvent.occurred_at,
            RequestEvent.recorded_at,
        )
        .join(Stage, Stage.id == RequestEvent.stage_id)
        .join(Sector, Sector.id == RequestEvent.sector_id)
        .where(RequestEvent.recorded_at <= as_of)
        .order_by(RequestEvent.request_id, RequestEvent.seq, RequestEvent.id)
    )
    return [dict(r) for r in db.execute(stmt).mappings()]


def _stage_intervals(db: Session, as_of: datetime) -> Sequence[Mapping[str, Any]]:
    sql = text(
        "SELECT * FROM v_request_stage_intervals WHERE entered_at <= :as_of "
        "ORDER BY request_id, entry_seq"
    )
    rows = [dict(r) for r in db.execute(sql, {"as_of": as_of}).mappings()]
    for row in rows:  # an exit after as_of had not happened yet at as_of
        if row["exited_at"] is not None and row["exited_at"] > as_of:
            row.update(exited_at=None, exit_event=None, duration_s=None, sla_breached=None)
    return rows


def _sla_breach_weekly(db: Session, as_of: datetime) -> Sequence[Mapping[str, Any]]:
    last_complete_week = as_of.astimezone(UTC).date() - timedelta(days=7)
    sql = text(
        "SELECT * FROM v_sla_breach_rate_weekly WHERE week_start <= :last_week "
        "ORDER BY week_start, sector_code"
    )
    return [dict(r) for r in db.execute(sql, {"last_week": last_complete_week}).mappings()]


SOURCES: dict[str, RowSource] = {
    "request_events": _request_events,
    "stage_intervals": _stage_intervals,
    "sla_breach_weekly": _sla_breach_weekly,
}


# --- Batch checks: each returns human-readable violations, empty when the batch is sound ---


def check_request_events(rows: list[RequestEventRow]) -> list[str]:
    """Unique (request_id, seq), seq contiguous from 1, occurred_at never going back."""
    problems: list[str] = []
    by_request: dict[int, list[RequestEventRow]] = defaultdict(list)
    for row in rows:
        by_request[row.request_id].append(row)
    for request_id, events in by_request.items():
        events.sort(key=lambda e: (e.seq, e.id))
        seqs = [e.seq for e in events]
        duplicated = sorted({s for s in seqs if seqs.count(s) > 1})
        if duplicated:
            problems.append(f"request {request_id}: duplicate seq {duplicated}")
        elif seqs != list(range(1, len(seqs) + 1)):
            problems.append(f"request {request_id}: seq is not contiguous from 1: {seqs}")
        for before, after in pairwise(events):
            if after.occurred_at < before.occurred_at:
                problems.append(
                    f"request {request_id}: occurred_at goes back at seq {after.seq} "
                    f"({after.occurred_at.isoformat()} < {before.occurred_at.isoformat()})"
                )
    return problems


def check_stage_intervals(rows: list[StageIntervalRow]) -> list[str]:
    problems: list[str] = []
    seen: set[tuple[int, int]] = set()
    for row in rows:
        key = (row.request_id, row.entry_seq)
        if key in seen:
            problems.append(f"request {row.request_id}: duplicate entry_seq {row.entry_seq}")
        seen.add(key)
        if row.exited_at is not None and row.exited_at < row.entered_at:
            problems.append(
                f"request {row.request_id} entry {row.entry_seq}: exited_at before entered_at"
            )
    return problems


def check_sla_breach_weekly(rows: list[SlaBreachWeeklyRow]) -> list[str]:
    problems: list[str] = []
    seen: set[tuple[str, date]] = set()
    for row in rows:
        where = f"{row.sector_code} week {row.week_start.isoformat()}"
        if (row.sector_code, row.week_start) in seen:
            problems.append(f"{where}: duplicate row")
        seen.add((row.sector_code, row.week_start))
        if not Decimal(0) <= row.breach_rate <= Decimal(1):
            problems.append(f"{where}: breach_rate {row.breach_rate} is outside [0, 1]")
        if row.breached > row.closed:
            problems.append(f"{where}: breached {row.breached} exceeds closed {row.closed}")
    return problems


CHECKS: dict[str, Callable[[Any], list[str]]] = {
    "request_events": check_request_events,
    "stage_intervals": check_stage_intervals,
    "sla_breach_weekly": check_sla_breach_weekly,
}


def validate_rows(contract: type[ExportRow], raw: Iterable[Mapping[str, Any]]) -> list[Any]:
    """Every row must satisfy the contract; the error lists the first few violations."""
    rows: list[ExportRow] = []
    problems: list[str] = []
    for index, record in enumerate(raw, start=1):
        try:
            rows.append(contract.model_validate(dict(record)))
        except ValidationError as exc:
            detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
            problems.append(f"row {index}: {detail}")
    _raise_if(problems, f"{contract.dataset}: {len(problems)} row(s) break the contract")
    return rows


def _raise_if(problems: list[str], headline: str) -> None:
    if problems:
        shown = "\n  ".join(problems[:MAX_REPORTED])
        more = (
            f"\n  ... and {len(problems) - MAX_REPORTED} more"
            if len(problems) > MAX_REPORTED
            else ""
        )
        raise ExportCheckFailed(f"{headline}:\n  {shown}{more}")


# --- Files ---


def csv_cell(value: object) -> str:
    """One value as text, the same way on every run: UTC microseconds, plain decimals, no nulls."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, date):
        return value.isoformat()
    return str(value)  # int, str, UUID


def write_csv(path: Path, contract: type[ExportRow], rows: list[ExportRow]) -> None:
    names = list(contract.model_fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(names)
        for row in rows:
            writer.writerow([csv_cell(getattr(row, n)) for n in names])


def write_parquet(path: Path, contract: type[ExportRow], rows: list[ExportRow]) -> None:
    pa, pq = _pyarrow()
    arrow_types = {
        "integer": pa.int64(),
        "string": pa.string(),
        "uuid": pa.string(),
        "boolean": pa.bool_(),
        "date": pa.date32(),
        "timestamp_utc": pa.timestamp("us", tz="UTC"),
        "decimal": pa.decimal128(38, 6),
    }
    columns = columns_of(contract)
    schema = pa.schema([(str(c["name"]), arrow_types[str(c["type"])]) for c in columns])
    data: dict[str, list[object]] = {}
    for column in columns:
        name = str(column["name"])
        values = [getattr(row, name) for row in rows]
        if column["type"] == "uuid":
            values = [None if v is None else str(v) for v in values]
        elif column["type"] == "string":
            values = [
                None if v is None else str(v.value if isinstance(v, Enum) else v) for v in values
            ]
        data[name] = values
    pq.write_table(pa.table(data, schema=schema), path)


def _pyarrow() -> tuple[Any, Any]:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ExportError(
            "Parquet needs pyarrow: install the extra with `uv sync --extra parquet` "
            "or `pip install 'bank-credit[parquet]'`, or use --format csv"
        ) from exc
    return pa, pq


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    *,
    run_id: UUID,
    contract: type[ExportRow],
    fmt: str,
    data_file: Path,
    row_count: int,
    as_of: datetime,
    started_at: datetime,
    finished_at: datetime,
) -> dict[str, Any]:
    def stamp(value: datetime) -> str:
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return {
        "run_id": str(run_id),
        "dataset": contract.dataset,
        "schema_version": contract.schema_version,
        "format": fmt,
        "file": data_file.name,
        "columns": columns_of(contract),
        "row_count": row_count,
        "sha256": sha256_of(data_file),
        "source": contract.source,
        "as_of": stamp(as_of),
        "started_at": stamp(started_at),
        "finished_at": stamp(finished_at),
    }


def publish(staging: Path, final: Path) -> None:
    """Swap a finished staging directory into place; a reader never sees a half-written one.

    Replacing an existing partition is rename-away, rename-in, delete (two renames, so there is
    a moment with no partition, never one with partial files). ponytail: a reader polling during
    that moment sees no partition; add a `_latest` pointer if that ever matters.
    """
    previous = final.with_name(f"{final.name}.replaced-{staging.name}")
    if final.exists():
        os.replace(final, previous)
    try:
        os.replace(staging, final)
    except OSError:
        if previous.exists():
            os.replace(previous, final)
        raise
    shutil.rmtree(previous, ignore_errors=True)


# --- The job ---


@dataclass(frozen=True)
class ExportResult:
    run_id: UUID
    dataset: str
    partition: Path
    row_count: int
    sha256: str


def run_export(
    db: Session,
    dataset: str,
    as_of: datetime,
    out: Path,
    fmt: str = "csv",
    *,
    source: RowSource | None = None,
) -> ExportResult:
    """Export one dataset as of a timestamp. Raises ExportError (nothing published) on a failure."""
    contract = CONTRACTS.get(dataset)
    if contract is None:
        raise ExportError(f"unknown dataset {dataset!r}; choose from {sorted(CONTRACTS)}")
    if fmt not in FORMATS:
        raise ExportError(f"unknown format {fmt!r}; choose from {list(FORMATS)}")
    if as_of.tzinfo is None:
        raise ExportError("as_of must be timezone-aware")
    if fmt == "parquet":
        _pyarrow()  # fail with the install hint before a job run is recorded
    as_of = as_of.astimezone(UTC)
    read = source or SOURCES[dataset]
    params = {"dataset": dataset, "as_of": as_of.isoformat(), "format": fmt, "out": str(out)}

    with job_run(db, JOB_NAME, params) as run:
        # ponytail: whole dataset in memory for the batch checks; stream or chunk past ~1M rows.
        raw = list(read(db, as_of))
        run.rows_read = len(raw)
        rows = validate_rows(contract, raw)
        _raise_if(CHECKS[dataset](rows), f"{dataset}: batch check failed")

        dataset_dir = out / dataset
        staging = dataset_dir / f"_tmp-{run.run_id}"
        final = dataset_dir / f"as_of={as_of.date().isoformat()}"
        staging.mkdir(parents=True)
        try:
            data_file = staging / f"part-0.{'csv' if fmt == 'csv' else 'parquet'}"
            (write_csv if fmt == "csv" else write_parquet)(data_file, contract, rows)
            manifest = build_manifest(
                run_id=run.run_id,
                contract=contract,
                fmt=fmt,
                data_file=data_file,
                row_count=len(rows),
                as_of=as_of,
                started_at=run.started_at,
                finished_at=datetime.now(UTC),
            )
            body = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            (staging / "_manifest.json").write_bytes(body.encode("utf-8"))
            publish(staging, final)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        run.rows_written = len(rows)

    logger.info(
        "export %s as_of=%s wrote %d rows to %s (sha256 %s)",
        dataset,
        as_of.date().isoformat(),
        len(rows),
        final,
        manifest["sha256"],
    )
    return ExportResult(run.run_id, dataset, final, len(rows), manifest["sha256"])
