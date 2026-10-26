# Architecture

## Components

```mermaid
flowchart LR
  Browser --> Web[web: nginx + React SPA :8080]
  Web -->|/api/* prefix stripped| API[api: FastAPI :8000]
  API --> PG[(postgres 17)]
  Migrate[migrate: alembic upgrade head] --> PG
  Seed[seed: bank-credit seed + simulate] --> PG
  Jobs[sla-check / export] --> PG
  Jobs --> Files[(./data/exports)]
```

Compose starts `postgres`, then the one-shot `migrate` and `seed` containers, then `api` (once
seeding succeeded) and `web` (once the API is healthy). The SPA calls `/api`, which nginx forwards
to the API, so browser and API share an origin and CORS stays closed. API and web listen on
127.0.0.1 only because the demo users have a published password.

## Write path

Every change to a request goes through `app/domain/workflow.py`:

1. Lock the request row (`SELECT ... FOR UPDATE`) and check `expected_seq` against `last_seq`.
2. Apply due system events first (SLA_BREACHED, then EXPIRED, stamped at their deadlines). An
   expired request refuses the action with 409 `request_expired`.
3. Check the transition table: the action must be allowed from the current status, by this actor
   (customer owner, staff or manager of the current sector, admin).
4. Insert the event with `seq = last_seq + 1` and update the projection columns on
   `credit_requests` (status, stage, sector, `sla_due_at`, `expires_at`, `closed_at`) in the same
   transaction.

`unique(request_id, seq)` turns any race the lock misses into a conflict. The projection is a
cache of the log: `workflow.replay(events)` rebuilds it, and the tests compare both for every
request.

`request_events` is append-only. A Postgres trigger rejects UPDATE and DELETE (revision 0002), and
an ORM `before_flush` guard does the same in SQLite unit tests. TRUNCATE stays allowed so the
simulation can reset.

### Workflow

| Stage | Position | Sectors by amount band | SLA |
| --- | --- | --- | --- |
| Checagem | 1 | Central de Varejo below R$ 4,800,000.00; Central de Médio e Grande from it | 24 h / 48 h |
| Triagem | 2 | same bands | 24 h / 48 h |
| Análise | 3 | same bands | 72 h / 120 h |
| Criação de Instrumento | 4 | same bands | 48 h / 72 h |
| Central de Desembolso | 5 | Central de Desembolso for any amount | 24 h |

Statuses: IN_REVIEW, RETURNED (waiting for the customer), and the terminal APPROVED, REJECTED,
CANCELLED, EXPIRED (45 days after submission). Events: SUBMITTED, STAGE_APPROVED, RETURNED,
RESUBMITTED, REJECTED, CANCELLED, EXPIRED, SLA_BREACHED.

## Read path

The analytics views are plain SQL views over `request_events` (decision 53):

- `v_request_stage_intervals`: one row per entry into a review stage, with exit time, exit event,
  duration and whether the SLA was missed. SLA_BREACHED events are not interval boundaries.
- `v_sla_breach_rate_weekly`: closed intervals, breached intervals and the breach rate per sector
  and exit week (UTC Monday).
- `v_time_in_stage_weekly`: n, average, p50 and p90 hours per stage, sector and exit week.
  Percentiles are per bucket and cannot be averaged across weeks.
- `v_throughput_daily`: per sector and day, intervals entered and how they ended.

The SQL lives in `backend/src/bank_credit/sql/views/<name>.v1.sql`; revision 0004 applies it. A
change ships as new `v2` files and a new revision, so released migrations never change.

`/analytics/*` serves the views to managers (own sector only) and admins, and the Reports page
charts them.

## Jobs and run metadata

`job_run(db, name, params)` wraps every job: it inserts a `job_runs` row (`running`), sets
`succeeded` or `failed` with the error, and records UTC start and end plus rows read and written.
Events written by a job carry its `job_run_id`, so any row in the log can be traced to the API
call or the run that produced it.
