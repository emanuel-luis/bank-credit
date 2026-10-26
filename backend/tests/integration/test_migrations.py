import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text

from bank_credit.app import models  # noqa: F401  (registers the tables on Base.metadata)
from bank_credit.app.db import Base

from .conftest import run_alembic

pytestmark = pytest.mark.integration


def _tables(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def _drift(engine: Engine) -> list[object]:
    """What `alembic check` would report: differences between the models and the database."""
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        return compare_metadata(context, Base.metadata)


def test_upgrade_head_matches_the_models(pg_engine):
    run_alembic(pg_engine, "upgrade", "head")
    assert _tables(pg_engine) == set(Base.metadata.tables) | {"alembic_version"}
    assert _drift(pg_engine) == []


def test_downgrade_base_removes_everything_and_upgrade_works_again(pg_engine):
    run_alembic(pg_engine, "upgrade", "head")
    run_alembic(pg_engine, "downgrade", "base")
    assert _tables(pg_engine) == {"alembic_version"}
    with pg_engine.connect() as connection:
        functions = connection.scalar(
            text("SELECT count(*) FROM pg_proc WHERE proname = 'request_events_append_only'")
        )
    assert functions == 0

    run_alembic(pg_engine, "upgrade", "head")
    assert _drift(pg_engine) == []
