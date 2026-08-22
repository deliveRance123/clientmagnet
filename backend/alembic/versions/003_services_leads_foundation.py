"""services and leads foundation

Revision ID: 003_services_leads_foundation
Revises: 002_core_saas_schema
Create Date: 2026-08-22 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_services_leads_foundation"
down_revision: Union[str, None] = "002_core_saas_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update services table
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.add_column(sa.Column("target_clients", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("portfolio_links", sa.Text(), nullable=True))

    # 2. Update leads table
    with op.batch_alter_table("leads", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("source_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("matched_service_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_leads_matched_service_id_services",
            "services",
            ["matched_service_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_leads_matched_service_id", ["matched_service_id"], unique=False)
        try:
            batch_op.drop_column("service")
        except Exception:
            pass


def downgrade() -> None:
    # 1. Revert leads table
    with op.batch_alter_table("leads", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service", sa.String(length=255), nullable=True))
        batch_op.drop_index("ix_leads_matched_service_id")
        batch_op.drop_constraint("fk_leads_matched_service_id_services", type_="foreignkey")
        batch_op.drop_column("matched_service_id")
        batch_op.drop_column("notes")
        batch_op.drop_column("source_url")
        batch_op.drop_column("phone")

    # 2. Revert services table
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_column("portfolio_links")
        batch_op.drop_column("target_clients")
