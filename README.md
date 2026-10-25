
# Bank Credit

> A bank-credit request platform: a **FastAPI** backend (layered routers/views/models,
> graph-based routing and SLAs) paired with a **React** front end.

![python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)

## What this demonstrates

- **API design & data modeling** — credit requests, auth, notifications, and a relational
  schema in SQLAlchemy.
- **Routing logic** — graph-based request routing and **SLA** tracking.
- **Layered backend** — routers / views / models / schemas separation, with a pytest suite.
- **Full-stack delivery** — typed FastAPI backend + Vite/React front end.

## Architecture

```
frontend (React/Vite) ──HTTP──► backend (FastAPI)
                                  routers ─► views ─► models (SQLAlchemy) ─► DB
                                  graph routing · SLA
```

## Tech stack

Python · FastAPI · SQLAlchemy · pytest · uv · ruff · TypeScript · React · Vite.

## Quickstart

```bash
# backend
cd backend
uv sync
cp .env.example .env         # set SECRET_KEY (see backend/README.md)
uv run populate --seed 42    # optional synthetic demo data
uv run serve

# frontend
cd ../frontend
npm install && npm run dev
```

## Project structure

```
backend/
  src/bank_credit/app/
    routers/   # auth, credit_request, graph, notification
    views/     # auth, credit_request, routing, sla
    models.py schemas.py database.py email.py
  scripts/     # populate, serve
  alembic/  tests/
frontend/      # Vite + React app
```

## License

MIT, see [LICENSE](LICENSE).
