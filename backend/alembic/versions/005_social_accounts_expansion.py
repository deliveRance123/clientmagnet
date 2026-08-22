"""social accounts expansion

Revision ID: 005_social_accounts_expansion
Revises: 004_lead_discovery_tables
Create Date: 2026-08-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_social_accounts_expansion"
down_revision: Union[str, None] = "004_lead_discovery_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("social_accounts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("account_username", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("profile_picture_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("scopes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.Text(), nullable=True))
        batch_op.create_index(op.f("ix_social_accounts_connection_status"), ["connection_status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("social_accounts", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_social_accounts_connection_status"))
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("scopes")
        batch_op.drop_column("profile_picture_url")
        batch_op.drop_column("account_username")
