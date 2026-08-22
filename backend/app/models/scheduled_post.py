import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True
    )
    social_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "FACEBOOK", "INSTAGRAM", "X", etc.
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="Scheduled", nullable=False, index=True
    )  # "Scheduled", "Publishing", "Published", "Failed", "Cancelled"
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analytics_json: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user = relationship("User", back_populates="scheduled_posts")
    content = relationship("Content", back_populates="scheduled_posts")
    social_account = relationship("SocialAccount")

    def get_analytics_dict(self) -> Dict[str, Any]:
        if not self.analytics_json:
            return {"likes": 0, "comments": 0, "shares": 0, "views": 0, "engagement_rate": 0.0}
        try:
            return json.loads(self.analytics_json)
        except Exception:
            return {}

    def __repr__(self) -> str:
        return f"<ScheduledPost(id={self.id}, platform={self.platform}, status={self.status})>"
