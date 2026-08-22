"""lead discovery tables

Revision ID: 004_lead_discovery_tables
Revises: 003_services_leads_foundation
Create Date: 2026-08-22 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004_lead_discovery_tables"
down_revision: Union[str, None] = "003_services_leads_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lead_discovery_sources table
    op.create_table(
        "lead_discovery_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("feed_url", sa.String(length=500), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(length=50), server_default="MANUAL", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_discovery_sources_id"), "lead_discovery_sources", ["id"], unique=False)
    op.create_index(op.f("ix_lead_discovery_sources_user_id"), "lead_discovery_sources", ["user_id"], unique=False)
    op.create_index(op.f("ix_lead_discovery_sources_source_type"), "lead_discovery_sources", ["source_type"], unique=False)
    op.create_index(op.f("ix_lead_discovery_sources_is_active"), "lead_discovery_sources", ["is_active"], unique=False)

    # Create lead_discovery_runs table
    op.create_table(
        "lead_discovery_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="SUCCESS", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accepted_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["lead_discovery_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_discovery_runs_id"), "lead_discovery_runs", ["id"], unique=False)
    op.create_index(op.f("ix_lead_discovery_runs_user_id"), "lead_discovery_runs", ["user_id"], unique=False)
    op.create_index(op.f("ix_lead_discovery_runs_source_id"), "lead_discovery_runs", ["source_id"], unique=False)
    op.create_index(op.f("ix_lead_discovery_runs_status"), "lead_discovery_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lead_discovery_runs_status"), table_name="lead_discovery_runs")
    op.drop_index(op.f("ix_lead_discovery_runs_source_id"), table_name="lead_discovery_runs")
    op.drop_index(op.f("ix_lead_discovery_runs_user_id"), table_name="lead_discovery_runs")
    op.drop_index(op.f("ix_lead_discovery_runs_id"), table_name="lead_discovery_runs")
    op.drop_table("lead_discovery_runs")

    op.drop_index(op.f("ix_lead_discovery_sources_is_active"), table_name="lead_discovery_sources")
    op.drop_index(op.f("ix_lead_discovery_sources_source_type"), table_name="lead_discovery_sources")
    op.drop_index(op.f("ix_lead_discovery_sources_user_id"), table_name="lead_discovery_sources")
    op.drop_index(op.f("ix_lead_discovery_sources_id"), table_name="lead_discovery_sources")
    op.drop_table("lead_discovery_sources")
