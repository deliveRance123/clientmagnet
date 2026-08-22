from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm.base import instance_state


# ---------------------------------------------------------------------------
# Unified Message & Conversation Schemas
# ---------------------------------------------------------------------------

class UnifiedMessageOut(BaseModel):
    id: str
    conversation_id: str
    sender: str
    recipient: str
    subject: Optional[str] = None
    message_content: str
    platform: str
    direction: str  # "inbound" | "outbound"
    status: str
    error_message: Optional[str] = None
    external_message_id: Optional[str] = None
    sent_at: datetime
    created_at: datetime

    @classmethod
    def from_orm_message(cls, m: Any) -> "UnifiedMessageOut":
        return cls(
            id=m.id,
            conversation_id=m.conversation_id,
            sender=m.sender,
            recipient=m.recipient,
            subject=m.subject,
            message_content=m.message_content,
            platform=m.platform,
            direction=m.direction,
            status=m.status,
            error_message=m.error_message,
            external_message_id=m.external_message_id,
            sent_at=m.sent_at,
            created_at=m.created_at,
        )


class UnifiedConversationLeadInfo(BaseModel):
    id: str
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    detected_need: Optional[str] = None
    matched_service_name: Optional[str] = None


class UnifiedConversationOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    platform: str  # "email", "whatsapp", "facebook", "instagram", "x", "linkedin"
    subject: Optional[str] = None
    external_conversation_id: Optional[str] = None
    status: str
    unread_count: int
    last_message_at: Optional[datetime] = None
    lead: Optional[UnifiedConversationLeadInfo] = None
    messages: List[UnifiedMessageOut] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Conversation Intelligence (Gemini AI)
# ---------------------------------------------------------------------------

class ConversationSummaryResponse(BaseModel):
    conversation_id: str
    summary: str
    client_needs: List[str] = []
    questions: List[str] = []
    objections: List[str] = []
    next_action: str
    lead_status_suggestion: Optional[str] = None


UnifiedConversationSummaryResponse = ConversationSummaryResponse


class SuggestedReplyResponse(BaseModel):
    conversation_id: str
    suggested_reply: str
    rationale: Optional[str] = None
    platform: str


# ---------------------------------------------------------------------------
# Follow-Up System Schemas
# ---------------------------------------------------------------------------

class FollowUpCreate(BaseModel):
    lead_id: Optional[str] = None
    conversation_id: Optional[str] = None
    channel: str = Field("email", description="email, whatsapp, linkedin, x")
    scheduled_time: datetime
    notes: Optional[str] = None
    message_draft: Optional[str] = None


class FollowUpUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    channel: Optional[str] = None
    notes: Optional[str] = None
    message_draft: Optional[str] = None
    status: Optional[str] = None  # "Pending", "Drafted", "Approved", "Sent", "Cancelled"


class FollowUpOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    conversation_id: Optional[str] = None
    channel: str
    scheduled_time: datetime
    status: str
    notes: Optional[str] = None
    message_draft: Optional[str] = None
    recommended_by_ai: bool = False
    completed_at: Optional[datetime] = None
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_followup(cls, f: Any) -> "FollowUpOut":
        lead_name = None
        lead_company = None
        try:
            state = instance_state(f)
            if "lead" in state.dict and state.dict["lead"] is not None:
                lead_name = state.dict["lead"].name
                lead_company = state.dict["lead"].company
        except Exception:
            pass

        return cls(
            id=f.id,
            user_id=f.user_id,
            lead_id=f.lead_id,
            conversation_id=f.conversation_id,
            channel=f.channel,
            scheduled_time=f.scheduled_time,
            status=f.status,
            notes=f.notes,
            message_draft=f.message_draft,
            recommended_by_ai=f.recommended_by_ai,
            completed_at=f.completed_at,
            lead_name=lead_name,
            lead_company=lead_company,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )


# ---------------------------------------------------------------------------
# Notification Schemas
# ---------------------------------------------------------------------------

class NotificationOut(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    link_url: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_orm_notification(cls, n: Any) -> "NotificationOut":
        return cls(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            is_read=n.is_read,
            link_url=n.link_url,
            created_at=n.created_at,
        )


class NotificationSummary(BaseModel):
    unread_count: int
    notifications: List[NotificationOut]


# ---------------------------------------------------------------------------
# User Communication Preferences Schemas
# ---------------------------------------------------------------------------

class UserCommunicationPreferencesUpdate(BaseModel):
    preferred_tone: Optional[str] = None
    default_signature: Optional[str] = None
    business_intro: Optional[str] = None
    preferred_cta: Optional[str] = None


class UserCommunicationPreferencesOut(BaseModel):
    preferred_tone: Optional[str] = None
    default_signature: Optional[str] = None
    business_intro: Optional[str] = None
    preferred_cta: Optional[str] = None
