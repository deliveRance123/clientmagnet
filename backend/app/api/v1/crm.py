import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_crm_service,
    get_current_active_user,
    get_db_session,
)
from app.models.user import User
from app.schemas.crm import (
    ClientCreate,
    ClientOut,
    ClientUpdate,
    CRMAnalyticsResponse,
    CRMDashboardMetrics,
    LeadConvertToClientRequest,
    LeadStageUpdate,
)
from app.schemas.lead import LeadOut
from app.services.crm import CRMService

logger = logging.getLogger("app.api.crm")

router = APIRouter()


# ---------------------------------------------------------------------------
# Lead Pipeline Stage & Conversion Endpoints
# ---------------------------------------------------------------------------

@router.patch(
    "/leads/{lead_id}/stage",
    response_model=LeadOut,
    summary="Update a lead's pipeline stage (with audit activity logging)",
)
async def update_lead_pipeline_stage(
    lead_id: str,
    payload: LeadStageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    try:
        updated_lead = await crm_service.update_lead_stage(
            db=db, user=current_user, lead_id=lead_id, stage_update=payload
        )
        return updated_lead
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update lead stage: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post(
    "/leads/{lead_id}/convert-to-client",
    response_model=ClientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Convert a WON lead into a permanent Client record while maintaining history",
)
async def convert_lead_to_client(
    lead_id: str,
    payload: LeadConvertToClientRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    try:
        client = await crm_service.convert_lead_to_client(
            db=db, user=current_user, lead_id=lead_id, req=payload
        )
        return client
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to convert lead to client: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# ---------------------------------------------------------------------------
# Client Directory (CRUD) Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/clients/",
    response_model=List[ClientOut],
    summary="List all clients with optional status and service filters",
)
async def list_clients(
    status_filter: Optional[str] = Query(None, alias="status"),
    service_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    return await crm_service.list_clients(
        db=db,
        user_id=current_user.id,
        status_filter=status_filter,
        service_id_filter=service_id,
        search_query=q,
    )


@router.post(
    "/clients/",
    response_model=ClientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client directly",
)
async def create_client(
    payload: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    return await crm_service.create_client(db=db, user=current_user, data=payload)


@router.get(
    "/clients/{client_id}",
    response_model=ClientOut,
    summary="Get single client details",
)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    client = await crm_service.get_client(db=db, user_id=current_user.id, client_id=client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.patch(
    "/clients/{client_id}",
    response_model=ClientOut,
    summary="Update client details or status",
)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    try:
        return await crm_service.update_client(
            db=db, user=current_user, client_id=client_id, data=payload
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# CRM Dashboard & PostgreSQL Analytics Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard",
    response_model=CRMDashboardMetrics,
    summary="Retrieve live CRM dashboard overview metrics (PostgreSQL aggregation)",
)
async def get_crm_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    return await crm_service.get_dashboard_metrics(db=db, user_id=current_user.id)


@router.get(
    "/analytics",
    response_model=CRMAnalyticsResponse,
    summary="Retrieve comprehensive conversion funnels, service ROI and source performance",
)
async def get_crm_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    crm_service: CRMService = Depends(get_crm_service),
):
    return await crm_service.get_analytics(db=db, user_id=current_user.id)
