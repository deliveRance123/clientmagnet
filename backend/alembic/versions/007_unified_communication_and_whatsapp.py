"""unified communication and whatsapp

Revision ID: 007_unified_communication_and_whatsapp
Revises: 006_email_and_conversations_expansion
Create Date: 2026-08-22 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_unified_communication_and_whatsapp"
down_revision: Union[str, None] = "006_email_and_conversations_expansion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Expand users table with communication preferences
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("preferred_tone", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("default_signature", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("business_intro", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("preferred_cta", sa.String(length=255), nullable=True))

    # 2. Expand content table
    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hashtags", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("call_to_action", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("target_platforms", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.Text(), nullable=True))

    # 3. Expand scheduled_posts table
    with op.batch_alter_table("scheduled_posts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("social_account_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("analytics_json", sa.Text(), nullable=True))
        batch_op.create_foreign_key("fk_scheduled_posts_social_account_id", "social_accounts", ["social_account_id"], ["id"], ondelete="SET NULL")

    # 4. Expand follow_ups table
    with op.batch_alter_table("follow_ups", schema=None) as batch_op:
        batch_op.add_column(sa.Column("channel", sa.String(length=50), nullable=False, server_default="email"))
        batch_op.add_column(sa.Column("message_draft", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("recommended_by_ai", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    # 5. Create whatsapp_accounts table
    op.create_table(
        "whatsapp_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("business_account_id", sa.String(length=255), nullable=True),
        sa.Column("phone_number_id", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("connection_status", sa.String(length=50), nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("webhook_verify_token", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_accounts_id"), "whatsapp_accounts", ["id"], unique=False)
    op.create_index(op.f("ix_whatsapp_accounts_user_id"), "whatsapp_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_accounts_phone_number_id"), "whatsapp_accounts", ["phone_number_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_accounts_phone_number"), "whatsapp_accounts", ["phone_number"], unique=False)
    op.create_index(op.f("ix_whatsapp_accounts_connection_status"), "whatsapp_accounts", ["connection_status"], unique=False)

    # 6. Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"], unique=False)


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("whatsapp_accounts")

    with op.batch_alter_table("follow_ups", schema=None) as batch_op:
        batch_op.drop_column("completed_at")
        batch_op.drop_column("recommended_by_ai")
        batch_op.drop_column("message_draft")
        batch_op.drop_column("channel")

    with op.batch_alter_table("scheduled_posts", schema=None) as batch_op:
        batch_op.drop_constraint("fk_scheduled_posts_social_account_id", type_="foreignkey")
        batch_op.drop_column("analytics_json")
        batch_op.drop_column("error_message")
        batch_op.drop_column("published_at")
        batch_op.drop_column("social_account_id")

    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("target_platforms")
        batch_op.drop_column("call_to_action")
        batch_op.drop_column("hashtags")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("preferred_cta")
        batch_op.drop_column("business_intro")
        batch_op.drop_column("default_signature")
        batch_op.drop_column("preferred_tone")
