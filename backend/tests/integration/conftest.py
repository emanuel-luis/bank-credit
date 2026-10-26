"""Fixtures for tests that need a real Postgres, named by TEST_DATABASE_URL.

The schema is built with Alembic, never create_all, and the whole `public` schema is dropped
before and after each test: point TEST_DATABASE_URL only at a throwaway database.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from bank_credit.app.jobs.seed import seed

BACKEND = Path(__file__).resolve().parents[2]
URL_VARIABLE = "TEST_DATABASE_URL"


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Abort the run when integration tests are selected but no database is configured."""
    if os.environ.get(URL_VARIABLE):
        return
    if any(item.get_closest_marker("integration") for item in items):
        raise pytest.UsageError(
            f"{URL_VARIABLE} is not set. Integration tests need a throwaway Postgres, for example "
            f"{URL_VARIABLE}=postgresql+psycopg://user:password@localhost:5432/bank_credit_test"
        )


def alembic_config() -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return config


def run_alembic(engine: Engine, action: str, revision: str) -> None:
    """Run `alembic upgrade|downgrade <revision>` on the engine's database."""
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection  # read by alembic/env.py
        getattr(command, action)(config, revision)


def _reset_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


@pytest.fixture
def pg_engine() -> Iterator[Engine]:
    """An engine on an empty schema. The schema is dropped again afterwards."""
    url = os.environ.get(URL_VARIABLE)
    assert url, f"{URL_VARIABLE} is not set"
    database = make_url(url).database or ""
    if "test" not in database:
        pytest.fail(f"refusing to wipe database {database!r}: its name must contain 'test'")
    engine = create_engine(url)
    _reset_schema(engine)
    yield engine
    _reset_schema(engine)
    engine.dispose()


@pytest.fixture
def migrated_engine(pg_engine: Engine) -> Engine:
    """An engine on a schema built by `alembic upgrade head`."""
    run_alembic(pg_engine, "upgrade", "head")
    return pg_engine


@pytest.fixture
def seeded_engine(migrated_engine: Engine) -> Engine:
    """Migrated schema plus the reference data and demo users from `seed`."""
    with Session(migrated_engine) as db:
        seed(db, "pg-test-password")
        db.commit()
    return migrated_engine


@pytest.fixture
def simulated_engine(seeded_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Engine:
    """Seeded schema plus a fixed-seed synthetic history ending at helpers.AS_OF.

    Password hashing is stubbed for the synthetic customers: Argon2 is slow and unrelated here.
    """
    from bank_credit.app.jobs import simulate as simulate_module

    from .helpers import AS_OF

    monkeypatch.setattr(simulate_module, "get_password_hash", lambda password: f"fake${password}")
    with Session(seeded_engine, expire_on_commit=False) as db:
        simulate_module.simulate(db, seed=1, as_of=AS_OF, days=90, clients=40)
    return seeded_engine
