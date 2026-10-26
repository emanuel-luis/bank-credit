"""analytics views (v1): stage intervals, weekly SLA breach rate, time in stage, daily throughput

The SQL is read from bank_credit/sql/views/*.v1.sql and never edited once released: a change
adds v2 files and a new revision (decision 41).

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op
from bank_credit.app.views import VIEWS_V1, view_sql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name in VIEWS_V1:
        op.execute(view_sql(name, 1).rstrip().removesuffix(";"))  # alembic adds the semicolon


def downgrade() -> None:
    for name in reversed(VIEWS_V1):
        op.execute(f"DROP VIEW {name}")
