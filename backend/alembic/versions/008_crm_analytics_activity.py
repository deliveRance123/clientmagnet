"""crm analytics and activity logs

Revision ID: 008_crm_analytics_activity
Revises: 007_unified_communication_and_whatsapp
Create Date: 2026-08-22 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008_crm_analytics_activity"
down_revision: Union[str, None] = "007_unified_communication_and_whatsapp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table with business fields and notification settings
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("business_description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("business_website", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("portfolio_links_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("notify_new_lead", sa.Boolean(), server_default=sa.text("true"), nullable=False))
        batch_op.add_column(sa.Column("notify_new_reply", sa.Boolean(), server_default=sa.text("true"), nullable=False))
        batch_op.add_column(sa.Column("notify_follow_up_due", sa.Boolean(), server_default=sa.text("true"), nullable=False))
        batch_op.add_column(sa.Column("notify_post_failed", sa.Boolean(), server_default=sa.text("true"), nullable=False))
        batch_op.add_column(sa.Column("notify_account_warning", sa.Boolean(), server_default=sa.text("true"), nullable=False))

    # 2. Update clients table with phone, website, service fields
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("website", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("service_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("service_purchased", sa.String(length=255), nullable=True))
        batch_op.create_foreign_key("fk_clients_service_id", "services", ["service_id"], ["id"], ondelete="SET NULL")

    # 3. Create activity_logs table
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("client_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_logs_id"), "activity_logs", ["id"], unique=False)
    op.create_index(op.f("ix_activity_logs_user_id"), "activity_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_lead_id"), "activity_logs", ["lead_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_client_id"), "activity_logs", ["client_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_event_type"), "activity_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_activity_logs_channel"), "activity_logs", ["channel"], unique=False)
    op.create_index(op.f("ix_activity_logs_created_at"), "activity_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_logs_created_at"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_channel"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_event_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_client_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_lead_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_user_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_id"), table_name="activity_logs")
    op.drop_table("activity_logs")

    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.drop_constraint("fk_clients_service_id", type_="foreignkey")
        batch_op.drop_column("service_purchased")
        batch_op.drop_column("service_id")
        batch_op.drop_column("website")
        batch_op.drop_column("phone")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("notify_account_warning")
        batch_op.drop_column("notify_post_failed")
        batch_op.drop_column("notify_follow_up_due")
        batch_op.drop_column("notify_new_reply")
        batch_op.drop_column("notify_new_lead")
        batch_op.drop_column("portfolio_links_json")
        batch_op.drop_column("business_website")
        batch_op.drop_column("business_description")
