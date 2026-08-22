from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm.base import instance_state


# ---------------------------------------------------------------------------
# Content CRUD Schemas
# ---------------------------------------------------------------------------

class ContentCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Internal title/label for post")
    body: str = Field(..., description="Post copy / caption text")
    hashtags: Optional[str] = Field(None, max_length=500, description="Space/comma separated hashtags")
    call_to_action: Optional[str] = Field(None, max_length=255, description="CTA snippet or link")
    target_platforms: Optional[List[str]] = Field(
        default=["FACEBOOK", "INSTAGRAM", "X", "LINKEDIN"],
        description="Target social platforms",
    )
    media_reference: Optional[str] = Field(None, max_length=1000, description="Direct URL of image/video")
    content_type: str = Field("Post", description="Post, Reel, Story, or Article")
    status: str = Field("Draft", description="Draft, Approved, Scheduled, Published, Archived")


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    hashtags: Optional[str] = None
    call_to_action: Optional[str] = None
    target_platforms: Optional[List[str]] = None
    media_reference: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[str] = None


class ContentOut(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    hashtags: Optional[str] = None
    call_to_action: Optional[str] = None
    target_platforms: List[str] = []
    media_reference: Optional[str] = None
    content_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_content(cls, c: Any) -> "ContentOut":
        return cls(
            id=c.id,
            user_id=c.user_id,
            title=c.title,
            body=c.body,
            hashtags=c.hashtags,
            call_to_action=c.call_to_action,
            target_platforms=c.get_platforms_list(),
            media_reference=c.media_reference,
            content_type=c.content_type,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


# ---------------------------------------------------------------------------
# AI Caption Generation Schemas
# ---------------------------------------------------------------------------

class AICaptionGenerateRequest(BaseModel):
    topic: str = Field(..., description="Core subject or announcement")
    description: Optional[str] = Field(None, description="Additional context or key points")
    platform: str = Field("LINKEDIN", description="FACEBOOK, INSTAGRAM, X, LINKEDIN, TIKTOK")
    tone: Optional[str] = Field("Professional & Engaging", description="Desired tone")
    call_to_action: Optional[str] = Field(None, description="Optional specific CTA prompt")


class AICaptionGenerateResponse(BaseModel):
    caption: str
    hashtags: List[str] = []
    call_to_action: str
    full_formatted_text: str
    platform: str


# ---------------------------------------------------------------------------
# Scheduling & Publishing Schemas
# ---------------------------------------------------------------------------

class PostScheduleRequest(BaseModel):
    content_id: str = Field(..., description="ID of Content item")
    platforms: List[str] = Field(..., description="List of platform names: FACEBOOK, INSTAGRAM, X, etc.")
    scheduled_at: datetime = Field(..., description="Future execution timestamp in ISO-8601")


class PublishNowRequest(BaseModel):
    content_id: str = Field(..., description="ID of Content item to publish immediately")
    platforms: List[str] = Field(..., description="Target platforms")


class ScheduledPostOut(BaseModel):
    id: str
    user_id: str
    content_id: str
    social_account_id: Optional[str] = None
    platform: str
    scheduled_at: datetime
    published_at: Optional[datetime] = None
    status: str
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    analytics: Dict[str, Any] = {}
    content_title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_post(cls, sp: Any) -> "ScheduledPostOut":
        content_title = None
        try:
            state = instance_state(sp)
            if "content" in state.dict and state.dict["content"] is not None:
                content_title = state.dict["content"].title
        except Exception:
            pass

        return cls(
            id=sp.id,
            user_id=sp.user_id,
            content_id=sp.content_id,
            social_account_id=sp.social_account_id,
            platform=sp.platform,
            scheduled_at=sp.scheduled_at,
            published_at=sp.published_at,
            status=sp.status,
            external_post_id=sp.external_post_id,
            error_message=sp.error_message,
            analytics=sp.get_analytics_dict(),
            content_title=content_title,
            created_at=sp.created_at,
            updated_at=sp.updated_at,
        )


class PublishResult(BaseModel):
    post_id: str
    platform: str
    status: str  # "PUBLISHED", "FAILED", "NOT_SUPPORTED"
    external_post_id: Optional[str] = None
    message: str


# ---------------------------------------------------------------------------
# Platform Capabilities Schema
# ---------------------------------------------------------------------------

class PlatformCapabilityInfo(BaseModel):
    platform: str
    supports_text: bool
    supports_image: bool
    supports_video: bool
    supports_reels: bool
    supports_stories: bool
    supports_scheduling: bool
    max_text_length: int
    direct_publishing_supported: bool
    notes: str


class PlatformCapabilityReport(BaseModel):
    capabilities: List[PlatformCapabilityInfo]
