import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Business Profile Fields
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_links_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Communication & AI Preferences
    preferred_tone: Mapped[str | None] = mapped_column(
        String(100), default="Professional & Consultative", nullable=True
    )
    default_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_cta: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # In-App & Email Notification Toggles
    notify_new_lead: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_new_reply: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_follow_up_due: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_post_failed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_account_warning: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    leads = relationship(
        "Lead", back_populates="user", cascade="all, delete-orphan"
    )
    services = relationship(
        "Service", back_populates="user", cascade="all, delete-orphan"
    )
    clients = relationship(
        "Client", back_populates="user", cascade="all, delete-orphan"
    )
    social_accounts = relationship(
        "SocialAccount", back_populates="user", cascade="all, delete-orphan"
    )
    email_accounts = relationship(
        "EmailAccount", back_populates="user", cascade="all, delete-orphan"
    )
    whatsapp_accounts = relationship(
        "WhatsAppAccount", back_populates="user", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    follow_ups = relationship(
        "FollowUp", back_populates="user", cascade="all, delete-orphan"
    )
    content = relationship(
        "Content", back_populates="user", cascade="all, delete-orphan"
    )
    scheduled_posts = relationship(
        "ScheduledPost", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    opt_outs = relationship(
        "OptOut", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    discovery_sources = relationship(
        "LeadDiscoverySource", back_populates="user", cascade="all, delete-orphan"
    )
    discovery_runs = relationship(
        "LeadDiscoveryRun", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"
