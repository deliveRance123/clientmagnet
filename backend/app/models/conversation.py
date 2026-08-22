import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "email", "gmail", "linkedin", "x", etc.
    external_conversation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False, index=True)  # "Open", "Archived", "Closed"

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
    user = relationship("User", back_populates="conversations")
    lead = relationship("Lead", back_populates="conversations")
    client = relationship("Client", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sent_at.asc()",
    )
    follow_ups = relationship("FollowUp", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, platform={self.platform}, subject={self.subject}, status={self.status})>"
