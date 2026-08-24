from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest,
    GoogleAuthUrlResponse,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
)
from app.schemas.user import UserOut, UserUpdate
from app.services.auth import auth_service

router = APIRouter()


def _set_auth_cookies(response: Response, refresh_token: str, access_token: str):
    """Sets secure HTTP-only cookies on the response for browser session persistence."""
    # Refresh token cookie (HTTP-only, Lax, 7 days)
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )
    # Access token cookie (optional fallback)
    response.set_cookie(
        key="cm_access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response):
    """Clears authentication cookies."""
    response.delete_cookie(key=settings.AUTH_COOKIE_NAME, path="/")
    response.delete_cookie(key="cm_access_token", path="/")


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Creates a new user account in PostgreSQL, securely hashes the password with Argon2id,
    and returns initial JWT access & refresh tokens.
    """
    user, access_token, raw_refresh_token, expires_in = (
        await auth_service.register_user(db=db, user_in=user_in)
    )
    _set_auth_cookies(response, raw_refresh_token, access_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain tokens",
)
async def login(
    user_in: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticates user with email and password, protected against repeated brute-force attacks,
    and returns JWT tokens.
    """
    client_ip = request.client.host if request.client else "unknown"
    user, access_token, raw_refresh_token, expires_in = (
        await auth_service.authenticate_user(
            db=db,
            email=user_in.email,
            password=user_in.password,
            client_ip=client_ip,
        )
    )
    _set_auth_cookies(response, raw_refresh_token, access_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using refresh token",
)
async def refresh_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Validates the refresh token (from JSON body or HTTP-only cookie),
    rotates the token, and issues a fresh access token.
    """
    raw_token = None
    if body and body.refresh_token:
        raw_token = body.refresh_token
    elif settings.AUTH_COOKIE_NAME in request.cookies:
        raw_token = request.cookies.get(settings.AUTH_COOKIE_NAME)

    if not raw_token:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token was not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access, new_refresh, expires_in, user = (
        await auth_service.refresh_user_tokens(db=db, raw_refresh_token=raw_token)
    )
    _set_auth_cookies(response, new_refresh, new_access)
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out and invalidate session",
)
async def logout(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Revokes the refresh token in PostgreSQL and clears authentication cookies.
    """
    raw_token = None
    if body and body.refresh_token:
        raw_token = body.refresh_token
    elif settings.AUTH_COOKIE_NAME in request.cookies:
        raw_token = request.cookies.get(settings.AUTH_COOKIE_NAME)

    if raw_token:
        await auth_service.revoke_refresh_token(db=db, raw_refresh_token=raw_token)

    _clear_auth_cookies(response)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the authenticated user's profile details.
    """
    return UserOut.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Update basic account information",
)
async def update_me(
    update_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Updates the authenticated user's basic profile details (full name, company name).
    """
    updated_user = await auth_service.update_user_profile(
        db=db, user=current_user, update_in=update_in
    )
    return UserOut.model_validate(updated_user)


# ---------------------------------------------------------------------------
# Google OAuth 2.0 Single Sign-On (Login & Registration)
# ---------------------------------------------------------------------------

@router.get(
    "/google/url",
    response_model=GoogleAuthUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Google OAuth 2.0 authorization URL for user login and signup",
)
async def get_google_auth_url(
    redirect_uri: Optional[str] = None,
):
    """
    Returns the official Google OAuth authorization URL.
    Can be used by the frontend to redirect or open popup for Google Sign-In.
    """
    auth_url, state = auth_service.get_google_auth_url(redirect_uri=redirect_uri)
    return GoogleAuthUrlResponse(authorization_url=auth_url, state=state)


@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate or register user with Google OAuth credentials",
)
async def google_auth(
    payload: GoogleAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Exchanges Google OAuth code or verifies ID token.
    If the user does not exist, an account is automatically created and verified.
    If the user already exists, they are authenticated immediately.
    Returns JWT access & refresh tokens.
    """
    client_ip = request.client.host if request.client else "unknown"
    user, access_token, raw_refresh_token, expires_in = (
        await auth_service.authenticate_or_register_google(
            db=db,
            code=payload.code,
            redirect_uri=payload.redirect_uri,
            id_token_str=payload.id_token,
            email_hint=payload.email,
            name_hint=payload.name,
        )
    )
    _set_auth_cookies(response, raw_refresh_token, access_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.get(
    "/google/callback",
    summary="Direct browser redirect callback from Google OAuth dialog",
)
async def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Handles standard browser redirect callback from Google.
    Logs in or registers user and redirects to frontend application.
    """
    frontend_target = settings.FRONTEND_URL.rstrip("/")
    if error:
        logger.warning(f"Google Auth returned error: {error} ({error_description})")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend_target}/login?error={error}")

    if not code:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend_target}/login?error=missing_code")

    try:
        user, access_token, raw_refresh_token, _ = (
            await auth_service.authenticate_or_register_google(
                db=db,
                code=code,
                redirect_uri=f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback",
            )
        )
        from fastapi.responses import RedirectResponse
        res = RedirectResponse(url=f"{frontend_target}/auth/callback?token={access_token}&refresh={raw_refresh_token}")
        _set_auth_cookies(res, raw_refresh_token, access_token)
        return res
    except Exception as e:
        logger.error(f"Error in Google OAuth browser callback: {e}", exc_info=True)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend_target}/login?error=auth_failed")
