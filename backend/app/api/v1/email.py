import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_email_service,
)
from app.core.config import settings
from app.models.email_account import EmailAccount
from app.models.user import User
from app.schemas.email import (
    ConversationLeadAssociationRequest,
    EmailAccountOut,
    EmailCallbackPayload,
    EmailConnectResponse,
    EmailConversationOut,
    EmailDraftGenerateRequest,
    EmailDraftGenerateResponse,
    EmailSendRequest,
    EmailSendResult,
)
from app.services.email import EmailService

logger = logging.getLogger("app.api.email")

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Accounts & OAuth Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/accounts",
    response_model=List[EmailAccountOut],
    summary="List user's connected email accounts",
)
async def list_email_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = (
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .order_by(EmailAccount.created_at.desc())
    )
    accounts = (await db.execute(query)).scalars().all()
    return [EmailAccountOut.from_orm_account(a) for a in accounts]


@router.get(
    "/connect",
    response_model=EmailConnectResponse,
    summary="Initiate Gmail OAuth connection flow",
)
async def initiate_email_connect(
    provider: str = Query("gmail", description="Email provider name (gmail)"),
    redirect_uri: Optional[str] = Query(None, description="Optional custom redirect URI"),
    current_user: User = Depends(get_current_active_user),
    service: EmailService = Depends(get_email_service),
):
    try:
        return service.initiate_connect(
            user_id=current_user.id, provider_name=provider, custom_redirect_uri=redirect_uri
        )
    except Exception as e:
        logger.error(f"Error initiating email connect: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate email OAuth: {str(e)}",
        )


@router.get(
    "/callback",
    summary="Handle OAuth redirect callback from Google dialog",
)
async def oauth_redirect_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    if error:
        logger.warning(f"Google OAuth returned error: {error} ({error_description})")
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #f8fafc;">
                    <div style="background: white; padding: 32px; border-radius: 16px; border: 1px solid #e2e8f0; max-width: 420px; text-align: center;">
                        <h2 style="color: #e11d48; margin-bottom: 8px;">Google Authorization Cancelled</h2>
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 24px;">{error_description or error}</p>
                        <a href="{settings.FRONTEND_EMAIL_REDIRECT_URL}" style="background: #0f172a; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Return to Inbox</a>
                    </div>
                </body>
            </html>
            """,
            status_code=400,
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state in callback.",
        )

    try:
        account = await service.handle_oauth_callback(
            db=db, code=code, state=state, provider_name="GMAIL"
        )
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #f8fafc;">
                    <div style="background: white; padding: 32px; border-radius: 16px; border: 1px solid #e2e8f0; max-width: 420px; text-align: center;">
                        <h2 style="color: #059669; margin-bottom: 8px;">Gmail Account Connected!</h2>
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 24px;">Connected: <strong>{account.email_address}</strong></p>
                        <a href="{settings.FRONTEND_EMAIL_REDIRECT_URL}" style="background: #4f46e5; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Go to Email Inbox</a>
                    </div>
                </body>
            </html>
            """
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error handling Google OAuth callback: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth exchange failed.")


@router.post(
    "/callback",
    response_model=EmailAccountOut,
    summary="Programmatic SPA callback code exchange",
)
async def programmatic_oauth_callback(
    payload: EmailCallbackPayload,
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    if payload.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth failed: {payload.error_description or payload.error}",
        )

    if not payload.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code."
        )

    try:
        account = await service.handle_oauth_callback(
            db=db, code=payload.code, state=payload.state, provider_name="GMAIL"
        )
        return EmailAccountOut.from_orm_account(account)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error in programmatic email callback: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth exchange failed.")


@router.post(
    "/accounts/{account_id}/disconnect",
    response_model=EmailAccountOut,
    summary="Disconnect email account and wipe stored credentials",
)
async def disconnect_email_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    try:
        account = await service.disconnect_account(db=db, user=current_user, account_id=account_id)
        return EmailAccountOut.from_orm_account(account)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error disconnecting email account: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect account.")


# ---------------------------------------------------------------------------
# 2. Conversations & Inbox Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/conversations",
    response_model=List[EmailConversationOut],
    summary="List email conversations with optional search query",
)
async def list_conversations(
    q: Optional[str] = Query(None, description="Search term for subject or email"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    return await service.list_conversations(db=db, user_id=current_user.id, query_str=q)


@router.get(
    "/conversations/{conversation_id}",
    response_model=EmailConversationOut,
    summary="Get conversation thread with messages and mark as read",
)
async def get_conversation_thread(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    conv = await service.get_conversation(
        db=db, user_id=current_user.id, conversation_id=conversation_id
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # Mark as read
    await service.mark_conversation_as_read(
        db=db, user_id=current_user.id, conversation_id=conversation_id
    )
    conv.unread_count = 0
    return conv


@router.patch(
    "/conversations/{conversation_id}",
    response_model=EmailConversationOut,
    summary="Associate or unassociate a lead with an existing conversation",
)
async def update_conversation_lead(
    conversation_id: str,
    payload: ConversationLeadAssociationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    try:
        return await service.associate_lead_to_conversation(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
            lead_id=payload.lead_id,
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error associating lead to conversation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update conversation.")


# ---------------------------------------------------------------------------
# 3. AI Email Draft Generation
# ---------------------------------------------------------------------------

@router.post(
    "/drafts/generate",
    response_model=EmailDraftGenerateResponse,
    summary="Generate personalized email draft using Gemini AI",
)
async def generate_email_draft_ai(
    payload: EmailDraftGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    try:
        return await service.generate_ai_draft(db=db, user=current_user, request=payload)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error generating AI email draft: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate draft.")


# ---------------------------------------------------------------------------
# 4. Explicit Send Email Approval & Sync
# ---------------------------------------------------------------------------

@router.post(
    "/send",
    response_model=EmailSendResult,
    summary="Explicit human-in-the-loop send approval and dispatch",
)
async def send_approved_email(
    payload: EmailSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    try:
        return await service.send_approved_email(db=db, user=current_user, request=payload)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Send failed: {str(e)}")


@router.post(
    "/sync",
    summary="Sync recent inbox emails and detect replies from connected Gmail",
)
async def sync_inbox_emails(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: EmailService = Depends(get_email_service),
):
    try:
        synced_count = await service.sync_inbox(db=db, user=current_user)
        return {
            "status": "success",
            "message": f"Inbox sync completed. {synced_count} new messages ingested.",
            "synced_count": synced_count,
        }
    except Exception as e:
        logger.error(f"Error syncing inbox: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync inbox.")
