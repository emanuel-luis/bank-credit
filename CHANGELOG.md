# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Diagrams as code: D2 sources in `docs/diagrams/` (architecture, data flow, four user flows,
  two ERDs) rendered to committed SVGs; `make diagrams`, `diagrams-check`, `diagrams-watch`,
  `d2-install`; CI job `diagrams (D2 render check)`. They replace the Mermaid blocks.
- SLA analytics: versioned SQL views (`v_request_stage_intervals`, `v_sla_breach_rate_weekly`,
  `v_time_in_stage_weekly`, `v_throughput_daily`) applied by Alembic revision 0004,
  `/analytics/*` endpoints for managers and admins, and Reports pages with charts.
- `bank-credit export`: CSV or Parquet partitions with `_manifest.json`, pydantic data contracts
  and batch checks; nothing is published when a check fails.
- Document checklist on submission (`request_documents`, revision 0003).
- Frontend wired to the API with types generated from the OpenAPI document; mock data removed.
- `scripts/smoke.py` end-to-end smoke through the web proxy, run in CI.
- Docker images, `compose.yaml` (postgres, migrate, seed, api, web), Makefile, `/health`.
- CI: lint, unit tests, Postgres integration tests, frontend checks, compose smoke;
  `security.yml` (pip-audit, npm audit); Dependabot.
- Append-only `request_events` log written by a single transition service, with a Postgres
  trigger and an ORM guard; `job_runs` run metadata; `seed`, deterministic `simulate` and
  idempotent `sla-check` jobs behind one `bank-credit` CLI.
- Docs: architecture, data contracts, runbook, decisions log, refactor plan.
- Coverage gate: CI fails below 90% backend unit-test coverage.

### Changed

- Workflow: five ordered stages with sectors chosen by amount band and per-stage SLAs replace the
  process chain walked with networkx.
- Alembic owns the schema; typed SQLAlchemy 2 models, `numeric(14,2)` money, UTC `timestamptz`.
- PyJWT and pwdlib (Argon2) replace python-jose and passlib; settings through pydantic-settings.
- Build with uv_build on Python 3.12; ruff and mypy strict.

### Removed

- Employee self-registration and the role fields on client registration.
- `PATCH /requests/{id}/status`, `/route`, `/estimated-time`, `/graph`.

### Security

- The default `SECRET_KEY` fallback is gone; the API refuses to start without a key of at least
  32 characters. The old value remains in git history and must never be used.
- Approve, return and reject are limited to staff of the current sector (and admins); customers
  can no longer approve their own requests or register as admin.
