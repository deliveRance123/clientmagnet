import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_social_account_manager,
)
from app.core.config import settings
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.social import (
    OAuthCallbackPayload,
    OAuthInitiateResponse,
    SocialAccountOut,
    SocialDisconnectResponse,
)
from app.services.social import SocialAccountManager

logger = logging.getLogger("app.api.social")

router = APIRouter()

SUPPORTED_PLATFORMS = {"FACEBOOK", "INSTAGRAM", "X", "LINKEDIN", "TIKTOK"}


# ---------------------------------------------------------------------------
# 1. List Connected Accounts
# ---------------------------------------------------------------------------
@router.get(
    "/accounts",
    response_model=List[SocialAccountOut],
    summary="List user's connected social accounts",
)
async def list_social_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    accounts = await manager.list_user_accounts(db=db, user_id=current_user.id)
    return [SocialAccountOut.from_orm_account(a) for a in accounts]


# ---------------------------------------------------------------------------
# 2. Initiate OAuth Connection
# ---------------------------------------------------------------------------
@router.get(
    "/connect/{platform}",
    response_model=OAuthInitiateResponse,
    summary="Initiate OAuth connection flow for a social platform",
)
async def initiate_social_connect(
    platform: str,
    redirect_uri: Optional[str] = Query(None, description="Optional custom frontend callback URI"),
    current_user: User = Depends(get_current_active_user),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    p_upper = platform.upper()
    if p_upper not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported social platform '{platform}'. Supported: {', '.join(sorted(SUPPORTED_PLATFORMS))}",
        )

    try:
        init_res = manager.initiate_connect(
            user_id=current_user.id,
            platform=p_upper,
            custom_redirect_uri=redirect_uri,
        )
        return init_res
    except Exception as e:
        logger.error(f"Error initiating OAuth connect for {platform}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate OAuth flow: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 3. OAuth Callbacks (GET and POST)
# ---------------------------------------------------------------------------
@router.get(
    "/callback/{platform}",
    summary="Handle OAuth redirect callback from social platform dialogs",
)
async def oauth_redirect_callback(
    platform: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    p_upper = platform.upper()
    if p_upper not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail="Unsupported platform.")

    if error:
        logger.warning(f"OAuth callback returned error for {platform}: {error} ({error_description})")
        # Render a user-friendly HTML error or redirect to frontend
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #f8fafc;">
                    <div style="background: white; padding: 32px; border-radius: 16px; border: 1px solid #e2e8f0; max-width: 420px; text-align: center;">
                        <h2 style="color: #e11d48; margin-bottom: 8px;">Authorization Cancelled</h2>
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 24px;">{error_description or error}</p>
                        <a href="{settings.FRONTEND_SOCIAL_REDIRECT_URL}" style="background: #0f172a; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Return to Dashboard</a>
                    </div>
                </body>
            </html>
            """,
            status_code=400,
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state in OAuth callback.",
        )

    try:
        account = await manager.handle_oauth_callback(
            db=db, platform=p_upper, code=code, state=state
        )
        return HTMLResponse(
            content=f"""
            <html>
                <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #f8fafc;">
                    <div style="background: white; padding: 32px; border-radius: 16px; border: 1px solid #e2e8f0; max-width: 420px; text-align: center;">
                        <h2 style="color: #059669; margin-bottom: 8px;">Account Connected!</h2>
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 24px;">Successfully connected your {p_upper} account: <strong>{account.account_name}</strong>.</p>
                        <a href="{settings.FRONTEND_SOCIAL_REDIRECT_URL}" style="background: #4f46e5; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: bold;">Continue to Client Magnet</a>
                    </div>
                </body>
            </html>
            """
        )
    except ValueError as val_e:
        logger.warning(f"OAuth validation error on {platform}: {val_e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error handling OAuth callback for {platform}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth exchange failed.")


@router.post(
    "/callback/{platform}",
    response_model=SocialAccountOut,
    summary="Handle programmatic OAuth callback from single-page application",
)
async def programmatic_oauth_callback(
    platform: str,
    payload: OAuthCallbackPayload,
    db: AsyncSession = Depends(get_db_session),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    p_upper = platform.upper()
    if p_upper not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail="Unsupported platform.")

    if payload.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authorization failed: {payload.error_description or payload.error}",
        )

    if not payload.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code.",
        )

    try:
        account = await manager.handle_oauth_callback(
            db=db, platform=p_upper, code=payload.code, state=payload.state
        )
        return SocialAccountOut.from_orm_account(account)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error handling programmatic OAuth callback for {platform}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OAuth exchange failed.")


# ---------------------------------------------------------------------------
# 4. Account Details, Disconnect & Refresh
# ---------------------------------------------------------------------------
@router.get(
    "/accounts/{account_id}",
    response_model=SocialAccountOut,
    summary="Get single connected social account details",
)
async def get_social_account_details(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = select(SocialAccount).where(
        SocialAccount.id == account_id,
        SocialAccount.user_id == current_user.id,
    )
    account = (await db.execute(query)).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Social account not found.")
    return SocialAccountOut.from_orm_account(account)


@router.post(
    "/accounts/{account_id}/disconnect",
    response_model=SocialDisconnectResponse,
    summary="Disconnect a social account and revoke tokens",
)
async def disconnect_social_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    try:
        account = await manager.disconnect_account(db=db, user=current_user, account_id=account_id)
        return SocialDisconnectResponse(
            status="success",
            message=f"Successfully disconnected {account.platform} account.",
            account_id=account.id,
        )
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error disconnecting social account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect account.")


@router.post(
    "/accounts/{account_id}/refresh",
    response_model=SocialAccountOut,
    summary="Refresh OAuth token for a connected account",
)
async def refresh_social_account_token(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    manager: SocialAccountManager = Depends(get_social_account_manager),
):
    try:
        account = await manager.refresh_account_token(db=db, user=current_user, account_id=account_id)
        return SocialAccountOut.from_orm_account(account)
    except ValueError as val_e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_e))
    except Exception as e:
        logger.error(f"Error refreshing token for social account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh token.")
