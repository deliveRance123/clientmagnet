import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_unified_inbox_service,
)
from app.models.user import User
from app.schemas.unified_inbox import (
    FollowUpCreate,
    FollowUpOut,
    FollowUpUpdate,
)
from app.services.unified_inbox import UnifiedInboxService

logger = logging.getLogger("app.api.follow_ups")

router = APIRouter()


@router.get(
    "/",
    response_model=List[FollowUpOut],
    summary="List follow-ups with optional status or due filter",
)
async def list_follow_ups(
    status: Optional[str] = Query(None, description="Filter by status: Pending, Drafted, Approved, Sent, Cancelled"),
    due: Optional[str] = Query(None, description="Filter by due: due_today, overdue, upcoming"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    return await service.list_follow_ups(
        db=db, user_id=current_user.id, status_filter=status, due_filter=due
    )


@router.post(
    "/",
    response_model=FollowUpOut,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new follow-up for a lead",
)
async def create_follow_up(
    payload: FollowUpCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    fu = await service.create_follow_up(db=db, user=current_user, data=payload)
    return FollowUpOut.from_orm_followup(fu)


@router.patch(
    "/{follow_up_id}",
    response_model=FollowUpOut,
    summary="Update or reschedule a follow-up",
)
async def update_follow_up(
    follow_up_id: str,
    payload: FollowUpUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    try:
        return await service.update_follow_up(
            db=db, user=current_user, follow_up_id=follow_up_id, data=payload
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))


@router.post(
    "/recommend",
    summary="Scan inactive contacted leads and generate AI recommended follow-up drafts",
)
async def scan_and_recommend_follow_ups(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    try:
        count = await service.recommend_ai_follow_ups(db=db, user=current_user)
        return {
            "status": "success",
            "message": f"Follow-up scan completed. {count} new recommendations generated.",
            "recommended_count": count,
        }
    except Exception as e:
        logger.error(f"Error recommending follow-ups: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Recommendation scan failed.")
