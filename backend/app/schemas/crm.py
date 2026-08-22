from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm.base import instance_state


# ---------------------------------------------------------------------------
# Pipeline & Stage Schemas
# ---------------------------------------------------------------------------

VALID_LEAD_STAGES = [
    "NEW",
    "QUALIFIED",
    "CONTACTED",
    "REPLIED",
    "INTERESTED",
    "DISCOVERY",
    "PROPOSAL",
    "NEGOTIATION",
    "WON",
    "LOST",
]

VALID_CLIENT_STATUSES = [
    "ACTIVE",
    "COMPLETED",
    "PAUSED",
    "LOST",
]


class LeadStageUpdate(BaseModel):
    stage: str = Field(..., description="Target pipeline stage")
    notes: Optional[str] = Field(None, description="Optional transition note or rationale")


class LeadConvertToClientRequest(BaseModel):
    service_id: Optional[str] = Field(None, description="Purchased Service ID")
    service_purchased: Optional[str] = Field(None, description="Custom name of service purchased")
    status: str = Field("ACTIVE", description="Initial client status: ACTIVE, PAUSED, etc.")
    notes: Optional[str] = Field(None, description="Client onboarding / handover notes")


# ---------------------------------------------------------------------------
# Client CRUD Schemas
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Client / Contact Name")
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    lead_id: Optional[str] = None
    service_id: Optional[str] = None
    service_purchased: Optional[str] = None
    status: str = Field("ACTIVE", description="ACTIVE, COMPLETED, PAUSED, LOST")
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    service_id: Optional[str] = None
    service_purchased: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ClientOut(BaseModel):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    service_id: Optional[str] = None
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    service_purchased: Optional[str] = None
    service_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_client(cls, c: Any) -> "ClientOut":
        svc_name = None
        try:
            state = instance_state(c)
            if "service" in state.dict and state.dict["service"] is not None:
                svc_name = state.dict["service"].name
        except Exception:
            pass

        return cls(
            id=c.id,
            user_id=c.user_id,
            lead_id=c.lead_id,
            service_id=c.service_id,
            name=c.name,
            company=c.company,
            email=c.email,
            phone=c.phone,
            website=c.website,
            service_purchased=c.service_purchased or svc_name,
            service_name=svc_name,
            status=c.status,
            notes=c.notes,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


# ---------------------------------------------------------------------------
# CRM Dashboard & Analytics Schemas (PostgreSQL Direct Aggregations)
# ---------------------------------------------------------------------------

class CRMDashboardMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    active_conversations: int
    follow_ups_due: int
    active_clients: int
    won_deals: int
    lost_deals: int
    leads_by_service: Dict[str, int] = {}
    leads_by_source: Dict[str, int] = {}
    leads_by_status: Dict[str, int] = {}
    clients_by_service: Dict[str, int] = {}


class ConversionFunnelMetrics(BaseModel):
    lead_to_qualified_pct: float
    qualified_to_contacted_pct: float
    contacted_to_replied_pct: float
    replied_to_won_pct: float
    overall_lead_to_won_pct: float


class ServicePerformanceItem(BaseModel):
    service_name: str
    service_id: Optional[str] = None
    total_leads: int
    qualified_leads: int
    clients_count: int
    won_deals: int


class SourcePerformanceItem(BaseModel):
    source_name: str
    total_leads: int
    qualified_leads: int
    clients_count: int


class CRMAnalyticsResponse(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    hot_leads: int
    contacted_leads: int
    replied_leads: int
    won_leads: int
    lost_leads: int
    conversion_funnel: ConversionFunnelMetrics
    service_performance: List[ServicePerformanceItem]
    source_performance: List[SourcePerformanceItem]
