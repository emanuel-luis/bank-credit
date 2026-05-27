
# Bank Credit

> A bank-credit request platform: a **FastAPI** backend (clean architecture, Alembic
> migrations, graph-based routing and SLAs) paired with a **React** front end.

![python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)

## What this demonstrates

- **API design & data modeling** — credit requests, auth, notifications, and a relational
  schema managed with **Alembic** migrations.
- **Routing logic** — graph-based request routing and **SLA** tracking.
- **Layered backend** — routers / views / models / schemas separation, with a pytest suite.
- **Full-stack delivery** — typed FastAPI backend + Vite/React front end.

## Architecture

```
frontend (React/Vite) ──HTTP──► backend (FastAPI)
                                  routers ─► views ─► models (SQLAlchemy) ─► DB
                                  alembic migrations · graph routing · SLA
```

## Tech stack

Python · FastAPI · SQLAlchemy + Alembic · pytest · TypeScript · React · Vite.

## Quickstart

```bash
# backend
cd backend
uv sync                      # or: pip install -r requirements.txt
cp .env.example .env         # set SECRET_KEY, DATABASE_URL, ...
alembic upgrade head
python -m bank_credit.scripts.serve   # or: uvicorn ... ; see scripts/serve.py

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

## Security note (do before publicizing)

- [ ] **Rotate `SECRET_KEY`** — the current README/`.env` example shows a real-looking key.
      Replace with an obvious placeholder (`<your-secret-key>`) and regenerate any real secret.
- [ ] Confirm no `.env` with live values is committed.

## License

MIT (add a `LICENSE` file).
