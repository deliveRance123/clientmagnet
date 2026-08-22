import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # "email", "gmail", "linkedin", etc.
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # "inbound" or "outbound"
    status: Mapped[str] = mapped_column(
        String(50), default="SENT", nullable=False, index=True
    )  # "DRAFT", "QUEUED", "SENT", "DELIVERED", "FAILED", "RECEIVED"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, direction={self.direction}, status={self.status})>"
