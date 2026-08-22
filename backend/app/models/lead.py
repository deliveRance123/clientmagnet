import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    profile_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_need: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="MANUAL", nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    matched_service_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    intent_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="NEW", nullable=False, index=True
    )  # "NEW", "QUALIFIED", "CONTACTED", "REPLIED", "INTERESTED", "DISCOVERY", "PROPOSAL", "NEGOTIATION", "WON", "LOST"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="leads")
    matched_service = relationship("Service", back_populates="leads")
    lead_sources = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="lead")
    conversations = relationship("Conversation", back_populates="lead")
    follow_ups = relationship("FollowUp", back_populates="lead")
    activities = relationship("ActivityLog", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, user_id={self.user_id}, name={self.name}, status={self.status})>"
