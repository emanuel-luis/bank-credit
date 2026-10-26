# Runbook

Commands assume the repository root. Without make, the raw compose commands are at the top of the
`Makefile`.

## Start, stop, reset

| Task | Command |
| --- | --- |
| Start everything | `make up` |
| Follow logs | `make logs` |
| Stop and delete the database | `make down` |
| Rebuild the simulated history only | `docker compose run --rm api bank-credit simulate --seed 42 --reset` |

`make up` writes `.env` from `.env.example` the first time, with a generated `SECRET_KEY` and
`POSTGRES_PASSWORD`. Keep `.env` out of git (it is ignored).

## Scheduled jobs

| Job | Suggested schedule | Command |
| --- | --- | --- |
| SLA check | Every 15 minutes | `make sla-check` |
| Export | Daily, after midnight UTC | `make export DATASET=request_events` (and the other datasets) |

Both are safe to rerun. `sla-check` stamps events with the deadline, so a second run finds nothing
to write. The export replaces the partition of the same as-of date only after all checks pass.

## Checking a run

```sql
SELECT run_id, job_name, status, started_at, finished_at, rows_read, rows_written, error
FROM job_runs ORDER BY started_at DESC LIMIT 10;
```

Events written by a job: `SELECT count(*) FROM request_events WHERE job_run_id = '<run_id>';`

## When something fails

- **API returns 503 on `/health`**: Postgres is down or unreachable. `docker compose ps`, then
  `docker compose logs postgres`.
- **`migrate` exits non-zero**: read `docker compose logs migrate`. Revisions are Postgres-only;
  `DATABASE_URL` must point to Postgres.
- **`simulate` fails with "run bank-credit seed first"**: the reference data or staff users are
  missing; run `docker compose run --rm api bank-credit seed`.
- **Export fails a batch check**: the `job_runs` row has the reason, nothing was published and the
  previous partition is intact. A sequence gap or a time going backwards in `request_events`
  means something wrote to the log outside the transition service; find it by `recorded_at` and
  `job_run_id`.
- **409 `stale_seq` in the UI**: someone else acted on the request first; the page reloads it.
- **A demo request offers no actions**: requests expire 45 days after submission and the demo
  history is dated relative to the day it was simulated. `make down && make up` rebuilds it.

## Integration tests

`make test-integration` starts only the compose `postgres` service, creates `bank_credit_test` and
runs `pytest -m integration` against it. The tests drop and recreate the `public` schema of that
database, so never point `TEST_DATABASE_URL` at data you want to keep.
