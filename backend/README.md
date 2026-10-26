# Bank Credit API

FastAPI backend for bank credit requests: authentication, document checklist, graph-based routing
between approval stages, SLAs and notifications.

## Setup

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 when needed) and a Postgres
database that you can write to.

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste the value into SECRET_KEY
```

Set `DATABASE_URL` in `.env` to your Postgres. The API refuses to start without `SECRET_KEY` and
`DATABASE_URL`; the migrations and the jobs need only `DATABASE_URL`. Every setting is documented
in `.env.example`.

## Run

```bash
uv run alembic upgrade head            # create the schema
uv run bank-credit seed                # reference data and demo users
uv run bank-credit simulate --seed 42  # optional: synthetic request history
uv run bank-credit serve --reload      # http://127.0.0.1:8000, docs at /docs
```

`seed` and `simulate` are safe to re-run. `simulate` accepts `--as-of`, `--days`, `--clients` and
`--reset`. `bank-credit sla-check` records the SLA breaches and expiries that came due; run it on
a schedule. `bank-credit openapi [--out PATH]` prints the OpenAPI JSON and needs no environment.

Demo logins use the password `demo1234` (or `DEMO_PASSWORD`). They exist for local use only:

- `admin@example.com`
- `manager.retail_center@example.com`, `staff1.retail_center@example.com` (also
  `mid_large_center` and `disbursement_center`)
- `customer1@example.com` (a client)

## Test and lint

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check . && uv run mypy
TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/bank_credit_test \
  uv run pytest -m integration   # needs a throwaway Postgres: its public schema is dropped
```

## Main endpoints

- `POST /auth/token`: login (OAuth2 password form), returns a JWT
- `POST /auth/register/client`, `POST /auth/register/employee`: sign-up
- `/requests`: credit requests, status changes, routing and history
- `/graph`: the approval-stage graph
- `/notifications`: client notifications
- `/analytics/sla-breach-rate`, `/analytics/time-in-stage`, `/analytics/throughput`: SLA analytics over the `v_*` SQL views (managers and admins; Postgres only)

Export a checked dataset partition with `bank-credit export --dataset request_events|stage_intervals|sla_breach_weekly --format csv|parquet --out data/exports` (Parquet needs `uv sync --extra parquet`).

## Layout

```
src/bank_credit/
  app/
    config.py     # settings from env / .env
    security.py   # password hashing and JWT
    database.py   # engine, session, get_db
    models.py  schemas.py  email.py  utils.py
    routers/      # auth, credit_request, graph, notification
    views/        # auth, credit_request, routing, sla
  scripts/        # serve, populate
tests/
alembic/
```
