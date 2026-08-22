"""email and conversations expansion

Revision ID: 006_email_and_conversations_expansion
Revises: 005_social_accounts_expansion
Create Date: 2026-08-22 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_email_and_conversations_expansion"
down_revision: Union[str, None] = "005_social_accounts_expansion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Expand email_accounts
    with op.batch_alter_table("email_accounts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("account_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("profile_picture_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("scopes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.Text(), nullable=True))
        batch_op.create_index(op.f("ix_email_accounts_connection_status"), ["connection_status"], unique=False)

    # 2. Expand conversations
    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(op.f("ix_conversations_last_message_at"), ["last_message_at"], unique=False)

    # 3. Expand messages
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("status", sa.String(length=50), nullable=False, server_default="SENT"))
        batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.Text(), nullable=True))
        batch_op.create_index(op.f("ix_messages_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_messages_status"))
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("error_message")
        batch_op.drop_column("status")
        batch_op.drop_column("subject")

    with op.batch_alter_table("conversations", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_conversations_last_message_at"))
        batch_op.drop_column("last_message_at")
        batch_op.drop_column("unread_count")
        batch_op.drop_column("subject")

    with op.batch_alter_table("email_accounts", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_email_accounts_connection_status"))
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("scopes")
        batch_op.drop_column("profile_picture_url")
        batch_op.drop_column("account_name")
