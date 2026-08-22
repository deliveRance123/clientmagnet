import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_whatsapp_service,
)
from app.models.user import User
from app.schemas.whatsapp import (
    WhatsAppAccountCreate,
    WhatsAppAccountOut,
    WhatsAppSendRequest,
    WhatsAppSendResult,
)
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger("app.api.whatsapp")

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. WhatsApp Account Management
# ---------------------------------------------------------------------------

@router.get(
    "/accounts",
    response_model=List[WhatsAppAccountOut],
    summary="List user's connected WhatsApp Business accounts",
)
async def list_whatsapp_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    accounts = await service.get_user_accounts(db=db, user_id=current_user.id)
    return [WhatsAppAccountOut.from_orm_account(a) for a in accounts]


@router.post(
    "/connect",
    response_model=WhatsAppAccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="Connect WhatsApp Business phone number ID and Permanent Access Token",
)
async def connect_whatsapp_account(
    payload: WhatsAppAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    try:
        account = await service.connect_account(db=db, user=current_user, data=payload)
        return WhatsAppAccountOut.from_orm_account(account)
    except Exception as e:
        logger.error(f"Error connecting WhatsApp account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect WhatsApp account: {str(e)}",
        )


@router.post(
    "/accounts/{account_id}/disconnect",
    response_model=WhatsAppAccountOut,
    summary="Disconnect WhatsApp Business account and wipe stored credentials",
)
async def disconnect_whatsapp_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    try:
        account = await service.disconnect_account(db=db, user=current_user, account_id=account_id)
        return WhatsAppAccountOut.from_orm_account(account)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))


# ---------------------------------------------------------------------------
# 2. Meta Official Webhook Handshake & Ingestion
# ---------------------------------------------------------------------------

@router.get(
    "/webhook",
    summary="Meta Webhook Verification Challenge",
)
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    """Handles Meta challenge handshake when registering the Webhook URL in Meta App Dashboard."""
    try:
        challenge = service.verify_webhook_challenge(
            mode=hub_mode, token=hub_verify_token, challenge=hub_challenge
        )
        return Response(content=challenge, media_type="text/plain")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch."
        )


@router.post(
    "/webhook",
    summary="Meta Incoming WhatsApp Events Webhook Listener",
)
async def meta_incoming_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    """Ingests incoming WhatsApp messages, matches to Leads, and updates unified conversations."""
    body_bytes = await request.body()

    # Validate HMAC signature
    if not service.validate_webhook_signature(x_hub_signature_256, body_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Hub-Signature-256 header.",
        )

    try:
        payload = await request.json()
        count = await service.process_incoming_webhook(db=db, payload=payload)
        return {"status": "EVENT_RECEIVED", "messages_ingested": count}
    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}", exc_info=True)
        # Always return 200 to Meta so it does not disable webhooks
        return {"status": "ERROR_HANDLED", "detail": str(e)}


# ---------------------------------------------------------------------------
# 3. AI Suggested Reply & Explicit Human-Approved Message Send
# ---------------------------------------------------------------------------

@router.post(
    "/suggest-reply",
    summary="Generate contextual suggested reply for a WhatsApp thread using Gemini AI",
)
async def suggest_whatsapp_reply(
    conversation_id: str = Query(..., description="Conversation ID to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    try:
        reply = await service.suggest_reply(
            db=db, user=current_user, conversation_id=conversation_id
        )
        return {"conversation_id": conversation_id, "suggested_reply": reply}
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
    except Exception as e:
        logger.error(f"AI reply suggestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest reply: {str(e)}",
        )


@router.post(
    "/send",
    response_model=WhatsAppSendResult,
    summary="Explicit human-in-the-loop approved WhatsApp message dispatch",
)
async def send_approved_whatsapp_message(
    payload: WhatsAppSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: WhatsAppService = Depends(get_whatsapp_service),
):
    try:
        return await service.send_approved_message(db=db, user=current_user, req=payload)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"WhatsApp message send failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Send failed: {str(e)}",
        )
