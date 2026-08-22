import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_content_service,
    get_current_active_user,
    get_db_session,
)
from app.models.user import User
from app.schemas.content import (
    PostScheduleRequest,
    PublishNowRequest,
    PublishResult,
    ScheduledPostOut,
)
from app.services.content_publisher import ContentService

logger = logging.getLogger("app.api.social_schedule")

router = APIRouter()


@router.get(
    "/schedule",
    response_model=List[ScheduledPostOut],
    summary="List scheduled and published posts (calendar view)",
)
async def list_schedule(
    status: Optional[str] = Query(None, description="Filter by status: Scheduled, Published, Cancelled"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    posts = await service.list_scheduled_posts(db=db, user_id=current_user.id, status_filter=status)
    return [ScheduledPostOut.from_orm_post(p) for p in posts]


@router.post(
    "/schedule",
    response_model=List[ScheduledPostOut],
    status_code=status.HTTP_201_CREATED,
    summary="Schedule content for future multi-platform publishing",
)
async def schedule_post(
    payload: PostScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        posts = await service.schedule_post(
            db=db,
            user=current_user,
            content_id=payload.content_id,
            platforms=payload.platforms,
            scheduled_at=payload.scheduled_at,
        )
        return [ScheduledPostOut.from_orm_post(p) for p in posts]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Scheduling failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to schedule post.")


@router.post(
    "/publish-now",
    response_model=List[PublishResult],
    summary="Explicitly publish approved content immediately across target platforms",
)
async def publish_now(
    payload: PublishNowRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        return await service.publish_now(
            db=db,
            user=current_user,
            content_id=payload.content_id,
            platforms=payload.platforms,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Instant publish failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Publishing failed.")


@router.post(
    "/schedule/{post_id}/cancel",
    response_model=ScheduledPostOut,
    summary="Cancel a scheduled post",
)
async def cancel_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        post = await service.cancel_scheduled_post(db=db, user=current_user, post_id=post_id)
        return ScheduledPostOut.from_orm_post(post)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
