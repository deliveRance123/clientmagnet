import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OptOut(Base):
    __tablename__ = "opt_outs"
    __table_args__ = (
        UniqueConstraint("user_id", "contact_identifier", "platform", name="uq_opt_outs_user_contact_platform"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # e.g. "email", "all", "linkedin"
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="opt_outs")

    def __repr__(self) -> str:
        return f"<OptOut(id={self.id}, contact={self.contact_identifier}, platform={self.platform})>"
