import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Examples: LEAD_DISCOVERED, LEAD_ANALYZED, EMAIL_SENT, EMAIL_REPLIED, WHATSAPP_MESSAGE,
    # SOCIAL_INTERACTION, FOLLOW_UP_SCHEDULED, FOLLOW_UP_SENT, STATUS_CHANGED, PROPOSAL_SENT, CLIENT_WON
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # "email", "whatsapp", "linkedin", "system"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="activity_logs")
    lead = relationship("Lead", back_populates="activities")
    client = relationship("Client", back_populates="activities")

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"
