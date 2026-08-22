from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActivityLogCreate(BaseModel):
    lead_id: Optional[str] = None
    client_id: Optional[str] = None
    event_type: str = Field(..., max_length=50, description="Event type enum/string")
    channel: Optional[str] = Field(None, max_length=50, description="email, whatsapp, social, system")
    description: str = Field(..., description="Human-readable description of the activity event")
    metadata_json: Optional[str] = None


class ActivityLogOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    client_id: Optional[str] = None
    event_type: str
    channel: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

    @classmethod
    def from_orm_log(cls, a: Any) -> "ActivityLogOut":
        import json
        meta = {}
        if a.metadata_json:
            try:
                meta = json.loads(a.metadata_json)
            except Exception:
                pass

        return cls(
            id=a.id,
            user_id=a.user_id,
            lead_id=a.lead_id,
            client_id=a.client_id,
            event_type=a.event_type,
            channel=a.channel,
            description=a.description,
            metadata=meta,
            created_at=a.created_at,
        )


class ActivityTimelineResponse(BaseModel):
    entity_id: str
    entity_type: str  # "lead" | "client"
    activities: List[ActivityLogOut]
