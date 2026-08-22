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
    AICaptionGenerateRequest,
    AICaptionGenerateResponse,
    ContentCreate,
    ContentOut,
    ContentUpdate,
    PlatformCapabilityReport,
)
from app.services.content_publisher import ContentService

logger = logging.getLogger("app.api.content")

router = APIRouter()


@router.get(
    "/",
    response_model=List[ContentOut],
    summary="List user's social content drafts and posts",
)
async def list_content(
    status: Optional[str] = Query(None, description="Filter by status: Draft, Scheduled, Published"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    items = await service.list_content(db=db, user_id=current_user.id, status_filter=status)
    return [ContentOut.from_orm_content(c) for c in items]


@router.post(
    "/",
    response_model=ContentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new social content draft",
)
async def create_content(
    payload: ContentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    item = await service.create_content(db=db, user=current_user, data=payload)
    return ContentOut.from_orm_content(item)


@router.get(
    "/capabilities",
    response_model=PlatformCapabilityReport,
    summary="Get platform publishing capability matrix and character limits",
)
async def get_platform_capabilities(
    service: ContentService = Depends(get_content_service),
):
    return service.get_capabilities_report()


@router.post(
    "/generate-caption",
    response_model=AICaptionGenerateResponse,
    summary="Generate tailored social media caption, hashtags, and CTA using Gemini AI",
)
async def generate_caption(
    payload: AICaptionGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        return await service.generate_caption(db=db, user=current_user, req=payload)
    except Exception as e:
        logger.error(f"AI caption generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate caption: {str(e)}",
        )


@router.get(
    "/{content_id}",
    response_model=ContentOut,
    summary="Get single content item",
)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    item = await service.get_content(db=db, user_id=current_user.id, content_id=content_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found.")
    return ContentOut.from_orm_content(item)


@router.patch(
    "/{content_id}",
    response_model=ContentOut,
    summary="Update content item",
)
async def update_content(
    content_id: str,
    payload: ContentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        item = await service.update_content(
            db=db, user=current_user, content_id=content_id, data=payload
        )
        return ContentOut.from_orm_content(item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete content draft",
)
async def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: ContentService = Depends(get_content_service),
):
    try:
        await service.delete_content(db=db, user=current_user, content_id=content_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
