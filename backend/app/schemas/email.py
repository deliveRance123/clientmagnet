import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Email Account Schemas (Never exposes raw credentials to client)
# ---------------------------------------------------------------------------

class EmailAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    provider: str
    email_address: str
    account_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connection_status: str = Field("CONNECTED", description="CONNECTED, DISCONNECTED, EXPIRED, REAUTH_REQUIRED")
    scopes: List[str] = Field(default_factory=list)
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_account(cls, account: Any) -> "EmailAccountOut":
        scopes_list: List[str] = []
        if account.scopes:
            try:
                parsed = json.loads(account.scopes)
                scopes_list = parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                scopes_list = [s.strip() for s in account.scopes.split(",") if s.strip()]

        return cls(
            id=account.id,
            user_id=account.user_id,
            provider=account.provider,
            email_address=account.email_address,
            account_name=account.account_name,
            profile_picture_url=account.profile_picture_url,
            connection_status=account.connection_status,
            scopes=scopes_list,
            token_expires_at=account.token_expires_at,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )


class EmailConnectResponse(BaseModel):
    provider: str = "gmail"
    authorization_url: str
    state: str


class EmailCallbackPayload(BaseModel):
    code: Optional[str] = None
    state: str
    error: Optional[str] = None
    error_description: Optional[str] = None


# ---------------------------------------------------------------------------
# Conversation & Message Schemas
# ---------------------------------------------------------------------------

class EmailMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender: str
    recipient: str
    subject: Optional[str] = None
    message_content: str
    platform: str
    direction: str  # "inbound" | "outbound"
    status: str     # "DRAFT", "SENT", "DELIVERED", "FAILED", "RECEIVED"
    error_message: Optional[str] = None
    external_message_id: Optional[str] = None
    sent_at: datetime
    created_at: datetime


class EmailConversationLeadInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    matched_service_name: Optional[str] = None


class EmailConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    lead_id: Optional[str] = None
    platform: str
    subject: Optional[str] = None
    status: str
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    lead: Optional[EmailConversationLeadInfo] = None
    messages: List[EmailMessageOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationLeadAssociationRequest(BaseModel):
    lead_id: Optional[str] = Field(None, description="Lead ID to associate, or None to unassociate")


# ---------------------------------------------------------------------------
# AI Email Drafting Schemas
# ---------------------------------------------------------------------------

class EmailDraftGenerateRequest(BaseModel):
    lead_id: str = Field(..., description="ID of the lead in PostgreSQL")
    service_id: Optional[str] = Field(None, description="Optional service ID to pitch")
    tone: Optional[str] = Field("Professional, helpful, and concise", description="Tone of the outreach email")
    context_notes: Optional[str] = Field(None, description="Specific project notes, portfolio references, or special points")


class EmailDraftGenerateResponse(BaseModel):
    lead_id: str
    recipient: str
    subject: str
    body: str
    matched_service_id: Optional[str] = None
    matched_service_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Explicit Send Request & Result Schemas
# ---------------------------------------------------------------------------

class EmailSendRequest(BaseModel):
    recipient: str = Field(..., description="Destination email address")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")
    lead_id: Optional[str] = Field(None, description="Associated lead ID")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID to append message to")
    in_reply_to_message_id: Optional[str] = Field(None, description="Message ID being replied to")


class EmailSendResult(BaseModel):
    message_id: str
    conversation_id: str
    status: str = "SENT"
    recipient: str
    subject: str
    external_message_id: Optional[str] = None
    sent_at: datetime
    message: str = "Email dispatched successfully"


# ---------------------------------------------------------------------------
# Internal Provider Models
# ---------------------------------------------------------------------------

class EmailAccountInfo(BaseModel):
    account_identifier: str
    email_address: str
    account_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    raw_profile: Optional[Dict[str, Any]] = None


class EmailMessageData(BaseModel):
    external_id: str
    thread_id: Optional[str] = None
    sender: str
    recipient: str
    subject: Optional[str] = None
    snippet: str
    body_text: str
    received_at: datetime
    is_unread: bool = False
