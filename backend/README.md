# Bank Credit API

FastAPI backend for bank credit requests: authentication, document checklist, graph-based routing
between approval stages, SLAs and notifications.

## Setup

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 when needed).

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste the value into SECRET_KEY
```

The API refuses to start without `SECRET_KEY` and `DATABASE_URL`. Every setting is documented in
`.env.example`.

## Run

```bash
uv run populate --seed 42   # optional: synthetic demo data (Faker)
uv run serve --reload       # http://127.0.0.1:8000, docs at /docs
```

Demo users created by `populate` use the password `123`: `admin@admin.com`, `1@funcionario.com`
(staff) and `1@cliente.com` (customer).

## Test and lint

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Main endpoints

- `POST /auth/token`: login (OAuth2 password form), returns a JWT
- `POST /auth/register/client`, `POST /auth/register/employee`: sign-up
- `/requests`: credit requests, status changes, routing and history
- `/graph`: the approval-stage graph
- `/notifications`: client notifications

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
