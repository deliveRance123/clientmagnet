import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(50), default="email", nullable=False)  # "email", "whatsapp", "linkedin", "x"
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="Pending", nullable=False, index=True
    )  # "Pending", "Drafted", "Approved", "Sent", "Cancelled", "Failed"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    user = relationship("User", back_populates="follow_ups")
    lead = relationship("Lead", back_populates="follow_ups")
    conversation = relationship("Conversation", back_populates="follow_ups")

    def __repr__(self) -> str:
        return f"<FollowUp(id={self.id}, user_id={self.user_id}, status={self.status}, channel={self.channel})>"
