from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Internal Opportunity Representation
# ---------------------------------------------------------------------------

class RawOpportunity(BaseModel):
    """Raw opportunity as extracted from an external provider/feed."""
    external_id: Optional[str] = None
    title: str
    company: Optional[str] = None
    description: str
    url: Optional[str] = None
    location: Optional[str] = None
    platform: Optional[str] = None
    source: str
    email: Optional[str] = None
    website: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


class NormalizedOpportunity(BaseModel):
    """Clean, normalized opportunity ready for deduplication and persistence."""
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    platform: str
    profile_url: Optional[str] = None
    location: Optional[str] = None
    description: str
    source: str
    source_url: Optional[str] = None
    external_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Discovery Source Schemas
# ---------------------------------------------------------------------------

class DiscoverySourceCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the source e.g. RemoteOK Web Dev")
    source_type: str = Field("JOB_BOARD", description="Type: JOB_BOARD, RSS, API, MANUAL")
    feed_url: Optional[str] = Field(None, description="Public feed or API endpoint URL")
    config_json: Optional[str] = Field(None, description="JSON configuration with filters/keywords")
    frequency: str = Field("MANUAL", description="Frequency: MANUAL, 30MIN, HOURLY, 6HOURS, DAILY")
    is_active: bool = Field(True, description="Whether this source is currently active")


class DiscoverySourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    feed_url: Optional[str] = None
    config_json: Optional[str] = None
    frequency: Optional[str] = None
    is_active: Optional[bool] = None


class DiscoverySourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    source_type: str
    feed_url: Optional[str] = None
    config_json: Optional[str] = None
    frequency: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Discovery Run Schemas
# ---------------------------------------------------------------------------

class DiscoveryRunRequest(BaseModel):
    source_id: Optional[str] = Field(None, description="Optional specific source ID; runs all active if omitted")
    analyze_with_ai: bool = Field(True, description="Whether to automatically run Gemini analysis on accepted leads")


class DiscoveryRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    source_id: Optional[str] = None
    status: str
    started_at: datetime
    finished_at: datetime
    total_discovered: int
    accepted_count: int
    duplicate_count: int
    rejected_count: int
    error_message: Optional[str] = None
    metadata_json: Optional[str] = None


# ---------------------------------------------------------------------------
# Manual & CSV Import Schemas
# ---------------------------------------------------------------------------

class ManualLeadImportRequest(BaseModel):
    name: str = Field(..., description="Prospect name or project title")
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    platform: Optional[str] = "MANUAL"
    location: Optional[str] = None
    description: str = Field(..., description="Opportunity details or project requirements")
    source: Optional[str] = "MANUAL"
    source_url: Optional[str] = None
    analyze_with_ai: bool = Field(True, description="Trigger AI analysis and scoring on import")


class CSVRowError(BaseModel):
    row_number: int
    error: str
    row_data: Optional[Dict[str, Any]] = None


class CSVImportResult(BaseModel):
    total_rows: int
    imported_count: int
    duplicate_count: int
    rejected_count: int
    errors: List[CSVRowError] = Field(default_factory=list)
