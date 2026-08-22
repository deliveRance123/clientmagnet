import json
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Content(Base):
    __tablename__ = "content"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    call_to_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_platforms: Mapped[str | None] = mapped_column(String(255), nullable=True)  # JSON array: ["FACEBOOK", "X"]
    media_reference: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), default="Post", nullable=False)  # "Post", "Reel", "Story", "Article"
    status: Mapped[str] = mapped_column(
        String(50), default="Draft", nullable=False, index=True
    )  # "Draft", "Approved", "Scheduled", "Published", "Archived"
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user = relationship("User", back_populates="content")
    scheduled_posts = relationship("ScheduledPost", back_populates="content", cascade="all, delete-orphan")

    def get_platforms_list(self) -> List[str]:
        if not self.target_platforms:
            return []
        try:
            parsed = json.loads(self.target_platforms)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            return [p.strip() for p in self.target_platforms.split(",") if p.strip()]

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, title={self.title}, status={self.status})>"
