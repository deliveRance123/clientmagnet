import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    service_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    service_purchased: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", nullable=False, index=True
    )  # "ACTIVE", "COMPLETED", "PAUSED", "LOST"
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
    user = relationship("User", back_populates="clients")
    lead = relationship("Lead", back_populates="clients")
    service = relationship("Service", foreign_keys=[service_id])
    conversations = relationship("Conversation", back_populates="client")
    activities = relationship("ActivityLog", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name={self.name}, status={self.status})>"
