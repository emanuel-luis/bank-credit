# Refactor plan (phases 2 to 5)

Phase 1 (security + tooling) shipped in PR #1. This plan covers the rest. Decisions are logged
in [DECISIONS.md](DECISIONS.md).

## Principles

- The domain service is the only writer of request state. Routers and jobs own the transaction
  and commit; domain functions never commit.
- Time is a parameter (`now: datetime`, tz-aware UTC) everywhere. The API takes it from a
  `get_now` dependency that tests override.
- Codes are English and stable (`analysis`, `retail_center`). Display names are pt-BR data
  (`Análise`, `Central de Varejo`).
- Unit tests run on in-memory SQLite with `create_all`. Postgres-only behavior uses
  `@pytest.mark.integration`, excluded by default (`-m "not integration"`) and run in CI against
  a Postgres service container.

## Phase 2: schema, migrations, workflow domain

Goal: typed models, an Alembic-owned schema, one transition service with an append-only event
log, authorization by role and sector, seeded reference data and simulated history.

### Files

Add:
- `app/db.py` (replaces `database.py`): `class Base(DeclarativeBase)` with a `MetaData` naming
  convention (`ix_%(column_0_label)s`, `uq_%(table_name)s_%(column_0_name)s`,
  `ck_%(table_name)s_%(constraint_name)s`,
  `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`, `pk_%(table_name)s`); a
  `UTCDateTime` TypeDecorator (`DateTime(timezone=True)`, rejects naive values on bind, attaches
  UTC on read for SQLite); engine and session factories; `get_db`.
- `app/domain/enums.py`: `StrEnum`s `UserRole`, `RequestStatus`, `Action`, `EventType`,
  `JobStatus`.
- `app/domain/documents.py`: CPF and CNPJ normalization and checksum (CNPJ accepts the
  alphanumeric format, character value = ASCII - 48), plus `Annotated` pydantic types.
- `app/domain/workflow.py`: the `TRANSITIONS` table as data, `allowed_actions(request, user, now)`,
  `transition(db, request, action, actor, now, reason=None, job_run_id=None) -> RequestEvent`,
  `resolve_route(stage, amount)`, `validate_routes()`, and `replay(events)` for the consistency
  check.
- `app/notifications.py` (replaces `utils.send_notification`).
- `app/jobs/runs.py`: `job_run(db, name, params)` context manager that writes the `job_runs` row
  and logs `run_id`, UTC start and end, rows read and written.
- `app/jobs/seed.py` (reference data), `app/jobs/simulate.py` (synthetic history),
  `app/jobs/sla_check.py`.
- `app/cli.py`: one `bank-credit` console script with subcommands `serve`, `seed`, `simulate`,
  `sla-check` (and `export` in phase 5).
- `alembic/versions/0001_initial.py`, `0002_request_events_append_only.py`.
- Tests: `test_documents.py`, `test_workflow.py`, `test_sla_check.py`, `test_simulate.py`,
  `tests/integration/test_migrations.py`, `test_append_only.py`, `test_workflow_pg.py`.

Change:
- `models.py`: `Mapped[]` throughout. `schemas.py`: `ConfigDict(from_attributes=True)`, inputs
  `extra="forbid"`, `Decimal` money.
- `config.py`: `DatabaseSettings` (only `database_url`) split out, `Settings` inherits it, so
  Alembic runs without `SECRET_KEY`.
- `routers/credit_request.py` rewritten; `routers/auth.py`: client registration cannot set a role
  or groups, employee self-registration is removed (staff come from the seed).
- `main.py`: drop the lifespan bridge and `init_db`.
- `alembic/env.py`, `alembic.ini`: no placeholder URL, `file_template = %%(rev)s_%%(slug)s`.
- `pyproject.toml`: drop networkx and the `serve`/`populate` scripts, add `psycopg[binary]` and
  mypy, stop excluding `alembic` from ruff.
- `ci.yml`: mypy in the lint job, a `backend-integration` job (service `postgres:17`,
  `TEST_DATABASE_URL`, `pytest -m integration`).
- `conftest.py`: valid CPFs and CNPJs, a `now` fixture, role fixtures.

Delete: `views/`, `utils.py`, `routers/graph.py`, `scripts/populate.py`, `scripts/serve.py`.

### Data model

Postgres DDL. Enums are VARCHAR + CHECK via `sa.Enum(native_enum=False, create_constraint=True)`.

```sql
users(id serial pk, email varchar(254) uq not null, full_name varchar(200) not null,
  phone varchar(20) not null, hashed_password text not null,
  role varchar(16) not null check in ('customer','staff','manager','admin'),
  is_active bool not null default true, created_at timestamptz not null,
  last_login_at timestamptz null)
clients(id pk, user_id int uq not null fk users on delete cascade,
  cnpj char(14) uq not null check (length(cnpj)=14)
    [+ postgres only: cnpj ~ '^[0-9A-Z]{12}[0-9]{2}$'],
  trade_name, legal_name, cnae_primary, cnae_primary_desc, cnae_secondary null,
  cnae_secondary_desc null, legal_nature_code, legal_nature_desc, street, number,
  complement null, postal_code char(8), district, city, state char(2))
sectors(id pk, code varchar(32) uq not null, name varchar(80) uq not null)
employees(id pk, user_id int uq not null fk users on delete cascade,
  employee_number varchar(16) uq not null,
  cpf char(11) uq not null check (length(cpf)=11) [+ postgres only: cpf ~ '^[0-9]{11}$'],
  sector_id int null fk sectors on delete restrict)
stages(id pk, code varchar(32) uq not null, name varchar(80) not null,
  position smallint uq not null check (position > 0))
stage_routes(id pk, stage_id fk stages restrict not null, sector_id fk sectors restrict not null,
  min_amount numeric(14,2) not null default 0, max_amount numeric(14,2) null,
  sla_hours int not null check (sla_hours > 0), uq(stage_id, min_amount),
  check (max_amount is null or max_amount > min_amount))
credit_requests(id pk, client_id fk clients restrict not null,
  amount numeric(14,2) not null check (amount > 0), purpose varchar(500) not null,
  term_days int not null check (term_days > 0), deliver_date date not null,
  status varchar(16) not null
    check in ('IN_REVIEW','RETURNED','APPROVED','REJECTED','CANCELLED','EXPIRED'),
  current_stage_id fk stages restrict not null, current_sector_id fk sectors restrict not null,
  submitted_at timestamptz not null, expires_at timestamptz not null,
  stage_entered_at timestamptz not null, sla_due_at timestamptz null,
  sla_breached_at timestamptz null, closed_at timestamptz null,
  last_seq int not null, updated_at timestamptz not null,
  check ((status in ('APPROVED','REJECTED','CANCELLED','EXPIRED')) = (closed_at is not null)))
  ix (current_sector_id, status, sla_due_at); ix (client_id, submitted_at)
request_events(id bigint identity pk, request_id fk credit_requests restrict not null,
  seq int not null,
  event_type varchar(24) not null check in ('SUBMITTED','STAGE_APPROVED','RETURNED',
    'RESUBMITTED','REJECTED','CANCELLED','EXPIRED','SLA_BREACHED'),
  from_status varchar(16) null, to_status varchar(16) not null,
  stage_id fk stages restrict not null, sector_id fk sectors restrict not null,
  sla_due_at timestamptz null, actor_user_id fk users restrict null,   -- null = system
  job_run_id uuid fk job_runs restrict null, reason text null,
  occurred_at timestamptz not null, recorded_at timestamptz not null default now(),
  uq(request_id, seq), check (event_type not in ('RETURNED','REJECTED') or reason is not null))
  ix (occurred_at); ix (stage_id, sector_id, occurred_at)
notifications(id pk, client_id fk clients cascade not null,
  request_id fk credit_requests restrict null, subject, message text,
  read_at timestamptz null, created_at timestamptz not null) ix (client_id, read_at, created_at)
job_runs(run_id uuid pk, job_name varchar(32) not null,
  status varchar(16) check in ('running','succeeded','failed'), params json not null,
  started_at timestamptz not null, finished_at timestamptz null,
  rows_read int null, rows_written int null, error text null)
```

- Dropped tables: `processes`, `sector_approval`, `groups`, `user_groups`, `sector_groups`,
  `request_history`. Dropped columns: `Sector.limit`, `require_all`, `manager_id`,
  `User.is_superuser`.
- The event PK is `BigInteger().with_variant(Integer, "sqlite")`.
- Current state lives as columns on `credit_requests`: a projection the service updates in the
  same transaction as the event insert. The event log is the source of truth; tests check
  `replay(events) == columns`.
- Concurrency: the service locks the request row (`with_for_update()`), sets
  `seq = last_seq + 1`; `unique(request_id, seq)` catches races; the API takes `expected_seq`.
- An event's `stage_id` is the stage the request is in after the event. Terminal events keep the
  stage where the request closed.
- Append-only: revision 0002 adds `request_events_append_only()` raising on
  `BEFORE UPDATE OR DELETE ... FOR EACH ROW`. TRUNCATE stays allowed for reseeding. An ORM
  `before_flush` guard also raises when a `RequestEvent` is dirty or deleted, so SQLite unit tests
  cover the rule.
- Validation: pydantic checks CPF and CNPJ checksums, accepts formatted input and stores digits
  (and letters for alphanumeric CNPJ) only. Money is `Decimal` (`max_digits=14`,
  `decimal_places=2`, `gt=0`), serialized in JSON as a string.

### Workflow (seed, idempotent get-or-create by `code` and `email`)

| position | stage code | name | routes: sector, amount band, sla_hours |
| --- | --- | --- | --- |
| 1 | document_check | Checagem | retail_center [0, 4,800,000.00) 24; mid_large_center [4,800,000.00, ∞) 48 |
| 2 | screening | Triagem | same bands, 24 / 48 |
| 3 | analysis | Análise | same bands, 72 / 120 |
| 4 | instrument_drafting | Criação de Instrumento | same bands, 48 / 72 |
| 5 | disbursement | Central de Desembolso | disbursement_center [0, ∞) 24 |

Sector names: Central de Varejo, Central de Médio e Grande, Central de Desembolso. The band
boundary matches the frontend's `getCentral`. `validate_routes()` requires each stage's bands to
cover [0, ∞) without gaps or overlaps.

### Transition table

| action / event | actor | from | guard | to status / stage | effects |
| --- | --- | --- | --- | --- | --- |
| submit / SUBMITTED | customer | (none) | amount > 0 | IN_REVIEW, stage 1, sector by band | `expires_at = now + 45d`, `sla_due_at = now + sla_hours` |
| approve / STAGE_APPROVED | staff or manager of the current sector, admin | IN_REVIEW | not the last stage | IN_REVIEW, next stage, sector by band | new `sla_due_at`, `sla_breached_at = null` |
| approve / STAGE_APPROVED | same | IN_REVIEW | last stage | APPROVED | `closed_at`, notification |
| return / RETURNED | same | IN_REVIEW | reason required | RETURNED, same stage | `sla_due_at = null`, notification |
| resubmit / RESUBMITTED | owner | RETURNED | none | IN_REVIEW, same stage | new `sla_due_at` |
| reject / REJECTED | staff or manager of the current sector, admin | IN_REVIEW | reason required | REJECTED | `closed_at`, notification |
| cancel / CANCELLED | owner | IN_REVIEW, RETURNED | none | CANCELLED | `closed_at` |
| (system) / EXPIRED | sla-check or lazy check | IN_REVIEW, RETURNED | `now >= expires_at` | EXPIRED | `occurred_at = expires_at`, notification |
| (system) / SLA_BREACHED | sla-check | IN_REVIEW | `now >= sla_due_at`, not yet breached | unchanged | `occurred_at = sla_due_at`, `sla_breached_at = sla_due_at` |

- Lazy expiry: `transition()` writes EXPIRED first when `now >= expires_at` and raises
  `RequestExpired` (409), so no action lands after the deadline even if the job has not run.
- Each new `occurred_at` must be at or after the request's last one.
- Errors: wrong actor 403; a transition not in the table, a stale `expected_seq` or an expired
  request 409.
- Customers are not notified of SLA breaches; it is an internal metric.

### sla-check (replaces `threading.Timer`)

`bank-credit sla-check [--now ISO]`: one transaction per request; emits SLA_BREACHED, then
EXPIRED. Event timestamps are the deadlines, not the run time, so a re-run writes nothing new.
Every run writes a `job_runs` row whose `run_id` goes on each event. The API also returns
`is_overdue` (from `sla_due_at`) and `estimated_completion_at` (`sla_due_at` plus the `sla_hours`
of the remaining stages for the request's band).

### simulate (synthetic history)

`bank-credit simulate --seed 42 --as-of 2026-10-01T00:00Z --days 120 --clients 200 [--reset]`

- `random.Random(seed)` and `Faker.seed_instance`; `--as-of` defaults to today 00:00 UTC.
- Log-normal amounts, about 85% retail. Per stage it samples a handling time from 0.3x to 2x
  `sla_hours` (so some breach) and an outcome (approve 85%, return 8%, reject 5%, cancel 2%).
- It calls `transition()` with the simulated `now`, a random staff member of the sector and the
  `job_run_id`. Requests stop at `as_of`, so some stay open. Breaches go through the same
  function sla-check uses.
- Idempotent: skips when a succeeded `simulate` run with the same parameters exists; `--reset`
  truncates the data tables first.

### Alembic

- `env.py`: `target_metadata = Base.metadata`, URL from `DatabaseSettings().database_url`,
  `NullPool`, `compare_type=True`; reuses `config.attributes["connection"]` when tests pass one.
- Migrations target Postgres. 0001 is autogenerated, then reviewed by hand (postgres-only regex
  checks via `ddl_if`, Identity, Numeric). 0002 is hand-written (`op.execute`).

### Tests

- Unit (SQLite): CPF/CNPJ cases; a test generated from the transition table (every status,
  action and role pair allowed or denied as specified); the 5-stage happy path; band routing at
  4,799,999.99 and 4,800,000.00; return then resubmit; cancel; lazy expiry; a clock going
  backwards raises; the ORM append-only guard raises; API authorization (a client approving gets
  403, staff of another sector 403, the right staff 200, stale `expected_seq` 409, a registration
  body with `role` 422); a second sla-check run writes 0 events; simulate is deterministic for a
  given seed and as-of (sha256 of ordered events) and `replay` equals the projection.
- Integration (CI Postgres): `upgrade head`, `alembic check` (no drift), `downgrade base`,
  `upgrade head`; UPDATE and DELETE on events raise; Numeric and timestamptz round-trip; two
  sessions racing the same transition fail on one side.

### Verification

```bash
cd backend
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q
TEST_DATABASE_URL=postgresql+psycopg://... uv run pytest -m integration   # CI
```

Commit order inside the PR: registration security fix, models and Alembic, domain and workflow,
routers, jobs, mypy. The API contract breaks for the frontend until phase 4.

## Phase 3: containers and CI

- `backend/Dockerfile` (multi-stage uv, `uv sync --locked --no-dev`, non-root, HEALTHCHECK),
  `frontend/Dockerfile` (Node build, nginx serving the SPA and proxying `/api` to the api),
  `compose.yaml`, `Makefile`, `.dockerignore` files, `GET /health` (pings the database).
- Compose services: `postgres` (healthcheck, named volume), `migrate` (one-shot
  `alembic upgrade head`), `seed` (one-shot `bank-credit seed && bank-credit simulate`,
  idempotent), `api` (after migrate and seed complete), `web`.
- Makefile: `up` is the one command; also `down`, `lint`, `test`, `test-integration`,
  `sla-check`, `export`, `logs`.
- CI: a `frontend` job (`npm ci`, lint, `tsc -b`, build) and a `compose-smoke` job
  (`docker compose up -d --wait`, curl `/health`, `docker compose down -v`); `security.yml`
  (pip-audit, npm audit); Dependabot for actions, uv and npm.

## Phase 4: frontend wiring

API contract:
- `GET /requests?scope=mine|queue|all&status=&stage=&overdue=&limit=&offset=` returns
  `{items, total}`; scope enforced by role (customer `mine`, staff and manager their sector's
  `queue`, admin `all`).
- `RequestSummary`: `id, amount ("125000.00"), purpose, term_days, deliver_date, status,
  stage {code, name, position}, sector {code, name}, submitted_at, stage_entered_at, sla_due_at,
  is_overdue, closed_at, client {id, cnpj, trade_name, legal_name}`.
- `GET /requests/{id}`: summary plus `documents[]`, `estimated_completion_at`, `last_seq` and
  `allowed_actions[]` computed for the current user; the UI shows only allowed buttons.
- `GET /requests/{id}/history`: `seq, event_type, from_status, to_status, stage, sector,
  actor {id, full_name, role} | null, reason, occurred_at`.
- `POST /requests` `{amount, purpose, term_days, deliver_date, documents}`;
  `POST /requests/{id}/transitions` `{action, reason?, expected_seq}`; `GET /workflow`.
- Errors: `{detail, code}`.
- Revision 0003 adds `request_documents(request_id, document_type, declared_at)`: a declared
  checklist, no file storage.

Frontend:
- Add `src/api/schema.d.ts` generated by `openapi-typescript` (CI fails when stale),
  `src/api/client.ts` (axios, `VITE_API_URL`, logout on 401), `src/api/requests.ts`,
  `src/hooks/useRequests.ts` (react-query), `src/lib/labels.ts` (codes to pt-BR, typed
  `Record<Status, string>`), `src/lib/errors.ts`.
- Rewire Login, RegisterClient, the customer pages and the staff pages (Aprovar, Devolver,
  Rejeitar with a reason dialog). Delete `context/mockdata.tsx`, `api/fetchData.js`,
  `getCentral`, the free-text status and stage options, the dropzone, every hardcoded `fetch`.
- Smoke: a script registers a client, submits, and has staff of each sector approve through all
  five stages.

## Phase 5: analytics, export, docs

SQL lives in `backend/src/bank_credit/sql/views/<name>.v1.sql`, applied by migration 0004;
changes add `v2` files and a new migration. Postgres only.

```sql
-- v_request_stage_intervals.v1.sql
WITH e AS (
  SELECT r.*, LEAD(occurred_at) OVER w AS next_at, LEAD(event_type) OVER w AS next_event
  FROM request_events r WHERE event_type <> 'SLA_BREACHED'
  WINDOW w AS (PARTITION BY request_id ORDER BY seq))
SELECT e.request_id, e.seq AS entry_seq, st.code AS stage_code, st.position,
       sc.code AS sector_code, e.occurred_at AS entered_at, e.next_at AS exited_at,
       e.next_event AS exit_event, e.sla_due_at,
       EXTRACT(EPOCH FROM e.next_at - e.occurred_at) AS duration_s,
       CASE WHEN e.next_at IS NULL THEN NULL ELSE e.next_at > e.sla_due_at END AS sla_breached
FROM e JOIN stages st ON st.id = e.stage_id JOIN sectors sc ON sc.id = e.sector_id
WHERE e.to_status = 'IN_REVIEW';
-- v_sla_breach_rate_weekly: sector_code, week_start, closed, breached, breach_rate
-- v_time_in_stage_weekly: stage_code, sector_code, week_start, n, avg_h, p50_h, p90_h
-- v_throughput_daily: sector_code, day, entered, approved, returned, rejected, cancelled, expired
```

Breach rate and time in stage are bucketed by exit week, when the SLA outcome is known;
percentiles cannot be summed across weeks.

- Endpoints: `GET /analytics/{sla-breach-rate|time-in-stage|throughput}?from=&to=&sector=`
  returning `{data, generated_at, source_view}`; manager (own sector) and admin only. The manager
  and admin Reports pages get three Chart.js charts.
- Export: `bank-credit export --dataset request_events|stage_intervals|sla_breach_weekly
  --as-of ISO --format csv|parquet --out data/exports` writes
  `<dataset>/as_of=<date>/part-0.csv` and `_manifest.json` (run_id, dataset, schema_version,
  columns, row_count, sha256, source, UTC start and end) through a temp dir and rename. Rows are
  validated by pydantic contract models; batch checks (unique `(request_id, seq)`, contiguous
  `seq`, non-decreasing `occurred_at`, required columns not null) fail the run and publish
  nothing. Parquet needs the optional `[parquet]` extra.
- Docs: `docs/architecture.md` (Mermaid data flow), `docs/data-contracts.md`, `docs/runbook.md`,
  README, CHANGELOG, CLAUDE.md.
- Tests (integration): simulate with a fixed seed, then views checked against aggregates computed
  in Python; export twice gives the same sha256; a planted bad row fails the run.

## Cross-cutting

- mypy strict on `src` from phase 2: `strict = true`, `files = ["src"]`,
  `plugins = ["pydantic.mypy"]`; `ignore_missing_imports` overrides only where needed.
- English for code, comments, logs and exception text. API errors are `{detail (English), code}`
  and the frontend maps `code` to pt-BR. Display data (stage, sector and document names),
  customer notifications and emails stay pt-BR. Logging uses %-style arguments.
