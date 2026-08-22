from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WhatsAppAccountCreate(BaseModel):
    phone_number_id: str = Field(..., description="Meta WhatsApp Phone Number ID")
    phone_number: str = Field(..., description="E.164 formatted phone number e.g. +1234567890")
    business_account_id: Optional[str] = Field(None, description="WhatsApp Business Account ID")
    display_name: Optional[str] = Field(None, description="Business display name")
    access_token: str = Field(..., description="Meta System User Permanent Access Token")
    webhook_verify_token: Optional[str] = Field(None, description="Custom webhook verify token")


class WhatsAppAccountOut(BaseModel):
    id: str
    user_id: str
    phone_number_id: str
    phone_number: str
    business_account_id: Optional[str] = None
    display_name: Optional[str] = None
    connection_status: str
    webhook_verify_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_account(cls, a: Any) -> "WhatsAppAccountOut":
        return cls(
            id=a.id,
            user_id=a.user_id,
            phone_number_id=a.phone_number_id,
            phone_number=a.phone_number,
            business_account_id=a.business_account_id,
            display_name=a.display_name,
            connection_status=a.connection_status,
            webhook_verify_token=a.webhook_verify_token,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )


# ---------------------------------------------------------------------------
# WhatsApp Messaging Schemas
# ---------------------------------------------------------------------------

class WhatsAppSendRequest(BaseModel):
    recipient_phone: str = Field(..., description="Recipient E.164 phone number e.g. +1234567890")
    message_text: str = Field(..., description="Text content to send")
    lead_id: Optional[str] = Field(None, description="Optional Lead ID")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID")


class WhatsAppSendResult(BaseModel):
    message_id: str
    conversation_id: str
    status: str
    recipient_phone: str
    external_message_id: Optional[str] = None
    sent_at: datetime
    message: str


# ---------------------------------------------------------------------------
# WhatsApp Webhook Payload Schema
# ---------------------------------------------------------------------------

class WhatsAppWebhookPayload(BaseModel):
    object: Optional[str] = None
    entry: Optional[List[Dict[str, Any]]] = None
