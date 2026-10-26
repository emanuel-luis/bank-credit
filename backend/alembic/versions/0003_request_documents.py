"""request_documents: the declared document checklist

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "request_documents",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column(
            "document_type",
            sa.Enum(
                "company_registration",
                "financial_statements",
                "business_plan",
                "tax_clearance",
                "collateral",
                name="document_type",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["credit_requests.id"],
            name=op.f("fk_request_documents_request_id_credit_requests"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("request_id", "document_type", name=op.f("pk_request_documents")),
    )


def downgrade() -> None:
    op.drop_table("request_documents")
