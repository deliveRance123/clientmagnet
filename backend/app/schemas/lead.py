from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.service import ServiceOut


class LeadStatus(str, Enum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    INTERESTED = "INTERESTED"
    DISCOVERY = "DISCOVERY"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"
    NOT_A_FIT = "NOT_A_FIT"


class LeadSource(str, Enum):
    MANUAL = "MANUAL"
    WEBSITE = "WEBSITE"
    EMAIL = "EMAIL"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    X = "X"
    LINKEDIN = "LINKEDIN"
    TIKTOK = "TIKTOK"
    OTHER = "OTHER"


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    platform: Optional[str] = Field(None, max_length=50)
    profile_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    source: LeadSource = Field(LeadSource.MANUAL)
    source_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    detected_need: Optional[str] = None
    matched_service_id: Optional[str] = Field(None, max_length=36)
    intent_score: float = Field(0.0, ge=0.0, le=100.0)
    status: LeadStatus = Field(LeadStatus.NEW)
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    platform: Optional[str] = Field(None, max_length=50)
    profile_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    source: Optional[LeadSource] = None
    source_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    detected_need: Optional[str] = None
    matched_service_id: Optional[str] = None
    intent_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


class LeadOut(BaseModel):
    id: str
    user_id: str
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    platform: Optional[str] = None
    profile_url: Optional[str] = None
    location: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    description: Optional[str] = None
    detected_need: Optional[str] = None
    matched_service_id: Optional[str] = None
    matched_service: Optional[ServiceOut] = None
    intent_score: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadStatsSummary(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    interested_leads: int
    won_clients: int
