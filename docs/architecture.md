# Architecture

Diagrams are D2 sources in [diagrams/](diagrams/), rendered to the SVGs shown here by
`make diagrams` and checked in CI. The layer view from the log to analytics and exports is the
[data flow](diagrams/data-flow.svg) ([source](diagrams/data-flow.d2)).

## Components

![Components: the web container (nginx) serves the SPA and proxies /api/* to the api container (FastAPI, JWT, role checks); api, the one-shot migrate and seed containers and the sla-check and export jobs use postgres 17; export writes partitions to ./data/exports; an optional SMTP server receives the welcome email.](diagrams/architecture.svg)

Source: [architecture.d2](diagrams/architecture.d2).

Compose starts `postgres`, then the one-shot `migrate` and `seed` containers, then `api` (once
seeding succeeded) and `web` (once the API is healthy). The SPA calls `/api`, which nginx forwards
to the API, so browser and API share an origin and CORS stays closed. API and web listen on
127.0.0.1 only because the demo users have a published password.

## Write path

Every change to a request goes through `app/domain/workflow.py`:

1. Lock the request row (`SELECT ... FOR UPDATE`).
2. Validate before writing anything: the actor must be a party to the action (customer owner,
   staff or manager of the current sector, admin), `expected_seq` must equal `last_seq`, the
   action must be allowed from the current status, and returns and rejections need a reason. A
   rejected call writes nothing.
3. Apply due system events (SLA_BREACHED, then EXPIRED, stamped at their deadlines). If the
   request expired, the action is refused with 409 `request_expired`; the EXPIRED event is kept.
4. Insert the event with `seq = last_seq + 1` and update the projection columns on
   `credit_requests` (status, stage, sector, `sla_due_at`, `closed_at`) in the same transaction.
   `expires_at` is set once, at submission.

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

### Customer: submit and resubmit

![Customer flow: the SPA keeps Enviar disabled until the four required documents are ticked; POST /requests runs submit_request, which routes stage 1 by amount band and writes the request, its documents and the SUBMITTED event in one transaction. After a reviewer returns it, the customer resubmits with expected_seq and the request re-enters the same stage with a new SLA.](diagrams/user-flows-customer.svg)

Source: [user-flows-customer.d2](diagrams/user-flows-customer.d2).

### Staff: move a request through the stages

![Staff flow: the sector queue lists IN_REVIEW requests ordered by SLA deadline; Aprovar posts a transition with expected_seq, the workflow locks the row, checks the sector, writes due SLA_BREACHED or EXPIRED events first, then moves the request to the next stage with the sector and SLA of its amount band. Return and reject need a reason; a stale sequence answers 409.](diagrams/user-flows-staff.svg)

Source: [user-flows-staff.d2](diagrams/user-flows-staff.d2).

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

![Reports flow: the manager's Reports page calls the three /analytics endpoints with from, to and their own sector; the API holds managers to their sector, applies the default window, reads the matching view and returns counts as integers and rates and hours as decimal strings. Another sector answers 403 scope_not_allowed.](diagrams/user-flows-reports.svg)

Source: [user-flows-reports.d2](diagrams/user-flows-reports.d2).

## Jobs and run metadata

`job_run(db, name, params)` wraps every job: it inserts a `job_runs` row (`running`), sets
`succeeded` or `failed` with the error, and records UTC start and end plus rows read and written.
Events written by a job carry its `job_run_id`, so any row in the log can be traced to the API
call or the run that produced it.

![sla-check flow: a scheduler or operator runs make sla-check; the job inserts a running job_runs row, selects the open requests whose SLA or expiry came due and, one transaction per request, writes SLA_BREACHED at the deadline and EXPIRED at expiry with the run id. It then records the counts; a rerun writes nothing.](diagrams/user-flows-sla-check.svg)

Source: [user-flows-sla-check.d2](diagrams/user-flows-sla-check.d2). Nothing in the repository
schedules the job; the [runbook](runbook.md) suggests every 15 minutes.

## Data model

Every arrow is a declared foreign key; the tables come from Alembic revisions 0001 to 0003.

![Data model of requests: credit_requests with its request_documents and request_events, the workflow reference tables stages, sectors and stage_routes, and job_runs, which request_events points to through job_run_id.](diagrams/data-model.svg)

Source: [data-model.d2](diagrams/data-model.d2).

![Data model of users: users with one clients row for customers or one employees row for staff, managers and admins; employees belong to a sector, and notifications belong to a client.](diagrams/data-model-users.svg)

Source: [data-model-users.d2](diagrams/data-model-users.d2).
