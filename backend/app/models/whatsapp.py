import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.encryption import decrypt_credential, encrypt_credential
from app.db.base_class import Base


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    business_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    connection_status: Mapped[str] = mapped_column(
        String(50), default="CONNECTED", nullable=False, index=True
    )  # "CONNECTED", "DISCONNECTED", "EXPIRED", "ERROR"
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_verify_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
    user = relationship("User", back_populates="whatsapp_accounts")

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

    def __repr__(self) -> str:
        return f"<WhatsAppAccount(id={self.id}, phone={self.phone_number}, status={self.connection_status})>"
