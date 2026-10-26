# Data contracts

The export job publishes three datasets. Each has one pydantic contract in
`backend/src/bank_credit/app/contracts/exports.py`: it validates every row, drives the CSV and
Parquet columns, and generates the manifest's column list. Unknown columns are an error.

## Datasets

### `request_events` (schema_version 1, source `request_events`)

Grain: one row per event, key `(request_id, seq)`.

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| id | integer | no | Surrogate key of the event |
| request_id | integer | no | |
| seq | integer | no | 1, 2, 3... per request, no gaps |
| event_type | string | no | SUBMITTED, STAGE_APPROVED, RETURNED, RESUBMITTED, REJECTED, CANCELLED, EXPIRED, SLA_BREACHED |
| from_status | string | yes | Null for SUBMITTED |
| to_status | string | no | Status after the event |
| stage_code | string | no | Stage the request is in after the event |
| sector_code | string | no | Sector that holds the request after the event |
| sla_due_at | timestamp_utc | yes | Deadline of the stage entered by this event |
| actor_user_id | integer | yes | Null for system events |
| job_run_id | uuid | yes | Set when a job wrote the event |
| reason | string | yes | Required for RETURNED and REJECTED |
| occurred_at | timestamp_utc | no | Business time |
| recorded_at | timestamp_utc | no | When the row was written; the as-of filter uses it |

Batch checks: unique `(request_id, seq)`; `seq` contiguous from 1 per request; `occurred_at`
non-decreasing per request; required columns not null.

### `stage_intervals` (schema_version 1, source `v_request_stage_intervals`)

Grain: one row per entry into a review stage, key `(request_id, entry_seq)`.

Columns: `request_id`, `entry_seq`, `stage_code`, `stage_position`, `sector_code`, `entered_at`,
`exited_at` (null while open), `exit_event` (null while open), `sla_due_at`, `duration_s`
(decimal seconds), `sla_breached` (null while open).

Batch check: `exited_at >= entered_at` when present. With an as-of, intervals entered after it
are left out and exits after it are hidden (the interval shows as open).

### `sla_breach_weekly` (schema_version 1, source `v_sla_breach_rate_weekly`)

Grain: one row per sector and exit week, key `(sector_code, week_start)`.

Columns: `sector_code`, `week_start` (date, UTC Monday), `closed`, `breached`, `breach_rate`
(decimal 0 to 1, 4 places).

Batch checks: `0 <= breach_rate <= 1`, `breached <= closed`. Only weeks that ended by the as-of
are exported.

## Partition layout

```
data/exports/<dataset>/as_of=<YYYY-MM-DD>/part-0.csv      # or part-0.parquet
data/exports/<dataset>/as_of=<YYYY-MM-DD>/_manifest.json
```

The partition is written to a temporary directory and renamed into place only after every row
and batch check passed. Exporting the same as-of date again replaces it. For identical inputs the
data file is byte-identical: rows sorted by the key, timestamps in UTC with microseconds and `Z`,
plain decimals, empty strings for nulls, LF line endings. Parquet (optional `[parquet]` extra)
uses decimal128(38,6) and microsecond UTC timestamps.

## Manifest

```json
{
  "run_id": "6f1c...",
  "dataset": "sla_breach_weekly",
  "schema_version": 1,
  "format": "csv",
  "file": "part-0.csv",
  "columns": [{"name": "sector_code", "type": "string", "nullable": false}, "..."],
  "row_count": 51,
  "sha256": "9b2e...",
  "source": "v_sla_breach_rate_weekly",
  "as_of": "2026-10-26T00:00:00Z",
  "started_at": "...",
  "finished_at": "..."
}
```

The `run_id` matches the `job_runs` row of the export. A consumer can check `row_count` and
`sha256` before reading, and `schema_version` before mapping columns.

## Changing a contract

Add a column or change a type by bumping `schema_version` in the contract, and keep the old
version readable until consumers move. Views follow the same rule: new behavior ships as
`<name>.v2.sql` plus a new Alembic revision.
