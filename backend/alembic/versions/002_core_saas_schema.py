"""core saas database schema

Revision ID: 002_core_saas_schema
Revises: 001_initial_auth
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_core_saas_schema"
down_revision: Union[str, None] = "001_initial_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update leads table with enriched columns and indexes
    op.add_column("leads", sa.Column("company", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("website", sa.String(length=500), nullable=True))
    op.add_column("leads", sa.Column("platform", sa.String(length=50), nullable=True))
    op.add_column("leads", sa.Column("profile_url", sa.String(length=500), nullable=True))
    op.add_column("leads", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("description", sa.String(), nullable=True))
    op.add_column("leads", sa.Column("detected_need", sa.String(), nullable=True))
    op.add_column("leads", sa.Column("intent_score", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("leads", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    
    # Make service nullable for backward compatibility
    op.alter_column("leads", "service", existing_type=sa.String(length=255), nullable=True)

    # Add indexes for leads
    op.create_index(op.f("ix_leads_email"), "leads", ["email"], unique=False)
    op.create_index(op.f("ix_leads_platform"), "leads", ["platform"], unique=False)
    op.create_index(op.f("ix_leads_status"), "leads", ["status"], unique=False)
    op.create_index(op.f("ix_leads_intent_score"), "leads", ["intent_score"], unique=False)
    op.create_index(op.f("ix_leads_created_at"), "leads", ["created_at"], unique=False)

    # 2. Create services table
    op.create_table(
        "services",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("pricing", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)
    op.create_index(op.f("ix_services_user_id"), "services", ["user_id"], unique=False)
    op.create_index(op.f("ix_services_is_active"), "services", ["is_active"], unique=False)

    # 3. Create lead_sources table
    op.create_table(
        "lead_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("source_platform", sa.String(length=100), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_sources_id"), "lead_sources", ["id"], unique=False)
    op.create_index(op.f("ix_lead_sources_user_id"), "lead_sources", ["user_id"], unique=False)
    op.create_index(op.f("ix_lead_sources_lead_id"), "lead_sources", ["lead_id"], unique=False)
    op.create_index(op.f("ix_lead_sources_source_platform"), "lead_sources", ["source_platform"], unique=False)

    # 4. Create clients table
    op.create_table(
        "clients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Active"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_user_id"), "clients", ["user_id"], unique=False)
    op.create_index(op.f("ix_clients_lead_id"), "clients", ["lead_id"], unique=False)
    op.create_index(op.f("ix_clients_email"), "clients", ["email"], unique=False)
    op.create_index(op.f("ix_clients_status"), "clients", ["status"], unique=False)

    # 5. Create social_accounts table
    op.create_table(
        "social_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("account_identifier", sa.String(length=255), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=True),
        sa.Column("connection_status", sa.String(length=50), nullable=False, server_default="Disconnected"),
        sa.Column("encrypted_credentials", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_accounts_id"), "social_accounts", ["id"], unique=False)
    op.create_index(op.f("ix_social_accounts_user_id"), "social_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_social_accounts_platform"), "social_accounts", ["platform"], unique=False)

    # 6. Create email_accounts table
    op.create_table(
        "email_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("connection_status", sa.String(length=50), nullable=False, server_default="Disconnected"),
        sa.Column("encrypted_credentials", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_accounts_id"), "email_accounts", ["id"], unique=False)
    op.create_index(op.f("ix_email_accounts_user_id"), "email_accounts", ["user_id"], unique=False)
    op.create_index(op.f("ix_email_accounts_email_address"), "email_accounts", ["email_address"], unique=False)

    # 7. Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("client_id", sa.String(length=36), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("external_conversation_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)
    op.create_index(op.f("ix_conversations_lead_id"), "conversations", ["lead_id"], unique=False)
    op.create_index(op.f("ix_conversations_client_id"), "conversations", ["client_id"], unique=False)
    op.create_index(op.f("ix_conversations_platform"), "conversations", ["platform"], unique=False)
    op.create_index(op.f("ix_conversations_external_conversation_id"), "conversations", ["external_conversation_id"], unique=False)
    op.create_index(op.f("ix_conversations_status"), "conversations", ["status"], unique=False)

    # 8. Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("message_content", sa.String(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_messages_external_message_id"), "messages", ["external_message_id"], unique=False)
    op.create_index(op.f("ix_messages_sent_at"), "messages", ["sent_at"], unique=False)

    # 9. Create follow_ups table
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("conversation_id", sa.String(length=36), nullable=True),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Pending"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_follow_ups_id"), "follow_ups", ["id"], unique=False)
    op.create_index(op.f("ix_follow_ups_user_id"), "follow_ups", ["user_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_lead_id"), "follow_ups", ["lead_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_scheduled_time"), "follow_ups", ["scheduled_time"], unique=False)
    op.create_index(op.f("ix_follow_ups_status"), "follow_ups", ["status"], unique=False)

    # 10. Create content table
    op.create_table(
        "content",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("media_reference", sa.String(length=1000), nullable=True),
        sa.Column("content_type", sa.String(length=50), nullable=False, server_default="Post"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_id"), "content", ["id"], unique=False)
    op.create_index(op.f("ix_content_user_id"), "content", ["user_id"], unique=False)
    op.create_index(op.f("ix_content_status"), "content", ["status"], unique=False)
    op.create_index(op.f("ix_content_created_at"), "content", ["created_at"], unique=False)

    # 11. Create scheduled_posts table
    op.create_table(
        "scheduled_posts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Scheduled"),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scheduled_posts_id"), "scheduled_posts", ["id"], unique=False)
    op.create_index(op.f("ix_scheduled_posts_user_id"), "scheduled_posts", ["user_id"], unique=False)
    op.create_index(op.f("ix_scheduled_posts_platform"), "scheduled_posts", ["platform"], unique=False)
    op.create_index(op.f("ix_scheduled_posts_scheduled_at"), "scheduled_posts", ["scheduled_at"], unique=False)
    op.create_index(op.f("ix_scheduled_posts_status"), "scheduled_posts", ["status"], unique=False)

    # 12. Create opt_outs table
    op.create_table(
        "opt_outs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("contact_identifier", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "contact_identifier", "platform", name="uq_opt_outs_user_contact_platform"),
    )
    op.create_index(op.f("ix_opt_outs_id"), "opt_outs", ["id"], unique=False)
    op.create_index(op.f("ix_opt_outs_user_id"), "opt_outs", ["user_id"], unique=False)
    op.create_index(op.f("ix_opt_outs_contact_identifier"), "opt_outs", ["contact_identifier"], unique=False)
    op.create_index(op.f("ix_opt_outs_platform"), "opt_outs", ["platform"], unique=False)
    op.create_index(op.f("ix_opt_outs_created_at"), "opt_outs", ["created_at"], unique=False)

    # 13. Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)


def downgrade() -> None:
    # Drop audit logs
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    # Drop opt outs
    op.drop_index(op.f("ix_opt_outs_created_at"), table_name="opt_outs")
    op.drop_index(op.f("ix_opt_outs_platform"), table_name="opt_outs")
    op.drop_index(op.f("ix_opt_outs_contact_identifier"), table_name="opt_outs")
    op.drop_index(op.f("ix_opt_outs_user_id"), table_name="opt_outs")
    op.drop_index(op.f("ix_opt_outs_id"), table_name="opt_outs")
    op.drop_table("opt_outs")

    # Drop scheduled posts
    op.drop_index(op.f("ix_scheduled_posts_status"), table_name="scheduled_posts")
    op.drop_index(op.f("ix_scheduled_posts_scheduled_at"), table_name="scheduled_posts")
    op.drop_index(op.f("ix_scheduled_posts_platform"), table_name="scheduled_posts")
    op.drop_index(op.f("ix_scheduled_posts_user_id"), table_name="scheduled_posts")
    op.drop_index(op.f("ix_scheduled_posts_id"), table_name="scheduled_posts")
    op.drop_table("scheduled_posts")

    # Drop content
    op.drop_index(op.f("ix_content_created_at"), table_name="content")
    op.drop_index(op.f("ix_content_status"), table_name="content")
    op.drop_index(op.f("ix_content_user_id"), table_name="content")
    op.drop_index(op.f("ix_content_id"), table_name="content")
    op.drop_table("content")

    # Drop follow ups
    op.drop_index(op.f("ix_follow_ups_status"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_scheduled_time"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_lead_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_user_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_id"), table_name="follow_ups")
    op.drop_table("follow_ups")

    # Drop messages
    op.drop_index(op.f("ix_messages_sent_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_external_message_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_id"), table_name="messages")
    op.drop_table("messages")

    # Drop conversations
    op.drop_index(op.f("ix_conversations_status"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_external_conversation_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_platform"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_client_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_lead_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_table("conversations")

    # Drop email accounts
    op.drop_index(op.f("ix_email_accounts_email_address"), table_name="email_accounts")
    op.drop_index(op.f("ix_email_accounts_user_id"), table_name="email_accounts")
    op.drop_index(op.f("ix_email_accounts_id"), table_name="email_accounts")
    op.drop_table("email_accounts")

    # Drop social accounts
    op.drop_index(op.f("ix_social_accounts_platform"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_user_id"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_id"), table_name="social_accounts")
    op.drop_table("social_accounts")

    # Drop clients
    op.drop_index(op.f("ix_clients_status"), table_name="clients")
    op.drop_index(op.f("ix_clients_email"), table_name="clients")
    op.drop_index(op.f("ix_clients_lead_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_user_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_table("clients")

    # Drop lead sources
    op.drop_index(op.f("ix_lead_sources_source_platform"), table_name="lead_sources")
    op.drop_index(op.f("ix_lead_sources_lead_id"), table_name="lead_sources")
    op.drop_index(op.f("ix_lead_sources_user_id"), table_name="lead_sources")
    op.drop_index(op.f("ix_lead_sources_id"), table_name="lead_sources")
    op.drop_table("lead_sources")

    # Drop services
    op.drop_index(op.f("ix_services_is_active"), table_name="services")
    op.drop_index(op.f("ix_services_user_id"), table_name="services")
    op.drop_index(op.f("ix_services_id"), table_name="services")
    op.drop_table("services")

    # Roll back leads updates
    op.drop_index(op.f("ix_leads_created_at"), table_name="leads")
    op.drop_index(op.f("ix_leads_intent_score"), table_name="leads")
    op.drop_index(op.f("ix_leads_status"), table_name="leads")
    op.drop_index(op.f("ix_leads_platform"), table_name="leads")
    op.drop_index(op.f("ix_leads_email"), table_name="leads")
    
    op.alter_column("leads", "service", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("leads", "updated_at")
    op.drop_column("leads", "intent_score")
    op.drop_column("leads", "detected_need")
    op.drop_column("leads", "description")
    op.drop_column("leads", "location")
    op.drop_column("leads", "profile_url")
    op.drop_column("leads", "platform")
    op.drop_column("leads", "website")
    op.drop_column("leads", "email")
    op.drop_column("leads", "company")
