import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_unified_inbox_service,
)
from app.models.user import User
from app.schemas.unified_inbox import NotificationSummary
from app.services.unified_inbox import UnifiedInboxService

logger = logging.getLogger("app.api.notifications")

router = APIRouter()


@router.get(
    "/",
    response_model=NotificationSummary,
    summary="Get user notifications and unread badge count",
)
async def get_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    return await service.get_notifications(
        db=db, user_id=current_user.id, unread_only=unread_only
    )


@router.patch(
    "/{notification_id}/read",
    summary="Mark a single notification as read",
)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    await service.mark_notification_read(
        db=db, user_id=current_user.id, notification_id=notification_id
    )
    return {"status": "success", "notification_id": notification_id, "is_read": True}


@router.post(
    "/mark-all-read",
    summary="Mark all user notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    await service.mark_all_notifications_read(db=db, user_id=current_user.id)
    return {"status": "success", "message": "All notifications marked as read"}
