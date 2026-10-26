# CLAUDE.md

Credit-request workflow (FastAPI + Postgres + React) with an append-only event log and SLA
analytics. Read `README.md` first; design decisions are in `docs/DECISIONS.md`.

## Commands

```bash
make up | make down | make logs          # compose stack (postgres, migrate, seed, api, web)
make lint                                # ruff, ruff format --check, mypy, eslint, tsc (= CI)
make test                                # backend unit tests on SQLite
make test-integration                    # Postgres integration tests (compose postgres)
make smoke                               # end-to-end API smoke through nginx (stack up)
cd backend && uv run bank-credit --help  # serve | seed | simulate | sla-check | export | openapi
cd frontend && npm run gen:api           # regenerate src/api/schema.d.ts from openapi.json
```

## Repo map

- `backend/src/bank_credit/app/domain/workflow.py`: the only writer of request state.
- `backend/src/bank_credit/app/models.py`, `db.py`: typed models, UTC datetime type, sessions.
- `backend/src/bank_credit/app/routers/`: auth, credit requests, notifications, analytics.
- `backend/src/bank_credit/app/jobs/`: `runs.py` (job_runs), seed, simulate, sla_check, export.
- `backend/src/bank_credit/sql/views/*.v1.sql`: analytics views, applied by Alembic 0004.
- `backend/alembic/versions/`: Postgres-only revisions.
- `frontend/src/api/openapi.json`: committed API contract; `schema.d.ts` is generated from it.
- `scripts/smoke.py`: stdlib end-to-end smoke used by CI.

## Invariants

- State changes go through `workflow.transition()` only; never write `credit_requests` status
  columns or `request_events` directly. `replay(events)` must equal the projection.
- `request_events` is append-only (trigger + ORM guard). Do not add UPDATE/DELETE paths.
- Time is passed in as a tz-aware UTC `now`; no `datetime.now()` inside the domain.
- Money is `Decimal` / `numeric(14,2)` and travels as a JSON string.
- Released migrations and `*.v1.sql` files are immutable: add a new revision or a `v2` file.
- After changing the API, run `uv run bank-credit openapi --out ../frontend/src/api/openapi.json`
  and `npm run gen:api`; CI fails on drift.
- Jobs run inside `job_run(...)` and stay idempotent.

## Conventions

- English for code, comments, logs and API `detail`; pt-BR for UI text and display data.
- Errors are `{detail, code}`; the frontend maps `code` to pt-BR in `src/lib/errors.ts`.
- Conventional Commits; branches `feat/<topic>` or `refactor/<topic>`.
- Unit tests on SQLite; Postgres-only behavior under `@pytest.mark.integration`.
- Never commit `.env`; demo credentials are local-only.
