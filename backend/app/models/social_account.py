import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.encryption import decrypt_credential, encrypt_credential
from app.db.base_class import Base


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    account_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    connection_status: Mapped[str] = mapped_column(
        String(50), default="CONNECTED", nullable=False, index=True
    )
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user = relationship("User", back_populates="social_accounts")

    # Helper property for credentials dictionary (access_token, refresh_token)
    @property
    def credentials(self) -> Optional[Dict[str, Any]]:
        if not self.encrypted_credentials:
            return None
        decrypted = decrypt_credential(self.encrypted_credentials)
        if not decrypted:
            return None
        try:
            return json.loads(decrypted)
        except Exception:
            return {"access_token": decrypted}

    @credentials.setter
    def credentials(self, data: Optional[Dict[str, Any]]) -> None:
        if not data:
            self.encrypted_credentials = None
        else:
            payload_str = json.dumps(data) if isinstance(data, dict) else str(data)
            self.encrypted_credentials = encrypt_credential(payload_str)

    def get_scopes_list(self) -> List[str]:
        if not self.scopes:
            return []
        try:
            parsed = json.loads(self.scopes)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            return [s.strip() for s in self.scopes.split(",") if s.strip()]

    def __repr__(self) -> str:
        return f"<SocialAccount(id={self.id}, platform={self.platform}, status={self.connection_status})>"
