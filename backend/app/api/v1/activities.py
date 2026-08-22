from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_activity_service,
    get_current_active_user,
    get_db_session,
)
from app.models.user import User
from app.schemas.activity import ActivityTimelineResponse
from app.services.activity import ActivityService

router = APIRouter()


@router.get(
    "/lead/{lead_id}",
    response_model=ActivityTimelineResponse,
    summary="Retrieve activity audit trail and timeline for a lead",
)
async def get_lead_activity_timeline(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return await activity_service.get_lead_timeline(
        db=db, user_id=current_user.id, lead_id=lead_id
    )


@router.get(
    "/client/{client_id}",
    response_model=ActivityTimelineResponse,
    summary="Retrieve activity audit trail and timeline for a client",
)
async def get_client_activity_timeline(
    client_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return await activity_service.get_client_timeline(
        db=db, user_id=current_user.id, client_id=client_id
    )
