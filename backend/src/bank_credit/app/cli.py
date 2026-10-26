"""The `bank-credit` command: the API server and the batch jobs."""

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import uvicorn

from bank_credit.app.config import get_database_settings, get_settings
from bank_credit.app.db import get_sessionmaker
from bank_credit.app.jobs.runs import job_run
from bank_credit.app.jobs.seed import seed
from bank_credit.app.jobs.simulate import simulate
from bank_credit.app.jobs.sla_check import sla_check
from bank_credit.app.main import create_app

logger = logging.getLogger("bank_credit.cli")


def _iso(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO 8601 timestamp: {value!r}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def openapi_json() -> str:
    """The OpenAPI document, deterministic and independent of the environment."""
    schema = create_app(cors_origins=[]).openapi()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bank-credit", description="Bank Credit API and jobs")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="run the API with uvicorn")
    serve.add_argument("--host", default="127.0.0.1", help="host to bind (default: %(default)s)")
    serve.add_argument("--port", type=int, default=8000, help="port to bind (default: %(default)s)")
    serve.add_argument("--reload", action="store_true", help="reload on code changes (development)")

    seeding = commands.add_parser("seed", help="create reference data and local demo users")
    seeding.add_argument(
        "--demo-password",
        help="password of the demo users (default: DEMO_PASSWORD or demo1234)",
    )

    sim = commands.add_parser("simulate", help="generate synthetic request history")
    sim.add_argument("--seed", type=int, default=42, help="random seed (default: %(default)s)")
    sim.add_argument(
        "--as-of", type=_iso, help="ISO timestamp the history ends at (default: today 00:00 UTC)"
    )
    sim.add_argument("--days", type=int, default=120, help="days of history (default: %(default)s)")
    sim.add_argument(
        "--clients", type=int, default=200, help="synthetic clients (default: %(default)s)"
    )
    sim.add_argument(
        "--reset", action="store_true", help="delete requests and synthetic clients first"
    )

    sla = commands.add_parser("sla-check", help="write the SLA breaches and expiries that came due")
    sla.add_argument("--now", type=_iso, help="ISO timestamp to check against (default: now)")

    spec = commands.add_parser("openapi", help="print the OpenAPI JSON (needs no environment)")
    spec.add_argument("--out", type=Path, help="write to this file instead of stdout")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "openapi":  # before the settings: it must work with an empty environment
        data = openapi_json().encode()  # ASCII only, written as bytes to keep the LF endings
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_bytes(data)
        else:
            sys.stdout.buffer.write(data)
        return
    settings = get_database_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s :: %(name)s :: %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if args.command == "serve":
        get_settings()  # fail early when SECRET_KEY or the database URL is missing
        uvicorn.run(
            "bank_credit.app.main:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
        return
    with get_sessionmaker()() as db:
        if args.command == "seed":
            logger.warning(
                "seeding local demo credentials: the demo users share one well-known password; "
                "never use this in a shared or production database"
            )
            with job_run(db, "seed", {}) as run:
                run.rows_written = seed(db, args.demo_password or settings.demo_password)
        elif args.command == "simulate":
            simulate(
                db,
                seed=args.seed,
                as_of=args.as_of,
                days=args.days,
                clients=args.clients,
                reset=args.reset,
            )
        else:
            sla_check(db, args.now)
