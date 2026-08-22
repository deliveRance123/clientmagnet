import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_unified_inbox_service,
)
from app.models.user import User
from app.schemas.unified_inbox import (
    SuggestedReplyResponse,
    UnifiedConversationOut,
    UnifiedConversationSummaryResponse,
)
from app.services.unified_inbox import UnifiedInboxService

logger = logging.getLogger("app.api.inbox")

router = APIRouter()


@router.get(
    "/conversations",
    response_model=List[UnifiedConversationOut],
    summary="List cross-channel unified inbox conversations",
)
async def list_unified_conversations(
    platform: Optional[str] = Query(None, description="Filter by platform: email, whatsapp, facebook, instagram, x, linkedin"),
    lead_status: Optional[str] = Query(None, description="Filter by Lead status: NEW, CONTACTED, QUALIFIED, REPLIED"),
    unread_only: bool = Query(False, description="Show only conversations with unread messages"),
    q: Optional[str] = Query(None, description="Search term for subject or contact identifier"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    return await service.list_conversations(
        db=db,
        user_id=current_user.id,
        platform_filter=platform,
        lead_status_filter=lead_status,
        unread_only=unread_only,
        search_query=q,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=UnifiedConversationOut,
    summary="Get full conversation thread and mark as read",
)
async def get_unified_conversation_thread(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    conv = await service.get_conversation_thread(
        db=db, user_id=current_user.id, conversation_id=conversation_id
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return conv


@router.post(
    "/conversations/{conversation_id}/summary",
    response_model=UnifiedConversationSummaryResponse,
    summary="Generate Gemini AI conversation intelligence summary (needs, objections, next action)",
)
async def summarize_unified_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    try:
        return await service.summarize_conversation(
            db=db, user=current_user, conversation_id=conversation_id
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error summarizing conversation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Summary generation failed.")


@router.post(
    "/conversations/{conversation_id}/suggest-reply",
    response_model=SuggestedReplyResponse,
    summary="Generate Gemini AI suggested reply tailored to conversation history and services",
)
async def suggest_unified_reply(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    try:
        return await service.suggest_reply(
            db=db, user=current_user, conversation_id=conversation_id
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error generating suggested reply: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Reply suggestion failed.")


@router.get(
    "/timeline/{lead_id}",
    response_model=List[Dict[str, Any]],
    summary="Get complete chronological communication and event timeline for a lead",
)
async def get_lead_communication_timeline(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    try:
        return await service.get_lead_timeline(
            db=db, user_id=current_user.id, lead_id=lead_id
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
