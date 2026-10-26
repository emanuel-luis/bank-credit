"""request_events is append-only

Revision ID: 0002
Revises: 0001

UPDATE and DELETE on request_events raise. TRUNCATE stays allowed so the demo data can be
reseeded; it does not fire row-level triggers.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION request_events_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'request_events is append-only (% not allowed)', TG_OP
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER request_events_append_only
        BEFORE UPDATE OR DELETE ON request_events
        FOR EACH ROW EXECUTE FUNCTION request_events_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER request_events_append_only ON request_events")
    op.execute("DROP FUNCTION request_events_append_only()")
