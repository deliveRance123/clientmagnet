import logging
import secrets
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Tuple

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    login_rate_limiter,
    validate_password_strength,
    verify_password,
)
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.auth import UserRegister
from app.schemas.user import UserUpdate
from app.services.otp import otp_service

logger = logging.getLogger("app.services.auth")


class AuthService:
    """Authentication and user session management service."""

    @staticmethod
    async def register_user(
        db: AsyncSession, user_in: UserRegister
    ) -> Tuple[User, str, str, int]:
        """
        Registers a new user after validating email uniqueness and password strength.
        If OTP code is provided, verifies OTP first.
        Returns: (user, access_token, raw_refresh_token, expires_in_seconds)
        """
        normalized_email = user_in.email.strip().lower()

        # 0. If OTP is provided, verify it
        if user_in.otp:
            is_valid_otp, otp_msg = otp_service.verify_otp(
                email=normalized_email, code=user_in.otp, purpose="registration"
            )
            if not is_valid_otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=otp_msg,
                )

        # 1. Validate password complexity
        is_valid_pw, pw_error = validate_password_strength(user_in.password)
        if not is_valid_pw:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=pw_error,
            )

        # 2. Check for duplicate email (case-insensitive)
        query = select(User).where(func.lower(User.email) == normalized_email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        # 3. Hash password using Argon2id
        hashed_pw = hash_password(user_in.password)

        # 4. Create and persist user (auto-verified so all users get immediate access)
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pw,
            full_name=user_in.full_name.strip() if user_in.full_name else None,
            company_name=user_in.company_name.strip() if user_in.company_name else None,
            is_active=True,
            is_verified=True,
        )
        db.add(new_user)
        await db.flush()  # assign user.id

        # 5. Generate JWT Access & Refresh Tokens
        access_token = create_access_token(subject=new_user.id)
        raw_refresh_token, token_db_hash, expires_at = create_refresh_token(
            subject=new_user.id
        )

        # 6. Store refresh token in database for server-side revocation tracking
        token_record = RefreshToken(
            token_hash=token_db_hash,
            user_id=new_user.id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(new_user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        logger.info(f"User successfully registered: user_id={new_user.id}")
        return new_user, access_token, raw_refresh_token, expires_in

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str, client_ip: str = "unknown"
    ) -> Tuple[User, str, str, int]:
        """
        Authenticates user credentials with rate limiting and generic error responses.
        Returns: (user, access_token, raw_refresh_token, expires_in_seconds)
        """
        normalized_email = email.strip().lower()

        # 1. Check rate limit
        rate_limit_key = f"{normalized_email}:{client_ip}"
        is_limited, retry_after = login_rate_limiter.is_rate_limited(rate_limit_key)
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for login attempt: key={rate_limit_key}, retry_after={retry_after}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        # 2. Query user
        query = select(User).where(func.lower(User.email) == normalized_email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        # 3. Verify password
        if not user or not verify_password(password, user.hashed_password):
            login_rate_limiter.record_failure(rate_limit_key)
            logger.warning(f"Failed login attempt for email: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Check active status
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: user_id={user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is currently inactive. Please contact support.",
            )

        # 5. Clear failed attempts on successful login
        login_rate_limiter.reset(rate_limit_key)

        # 6. Issue tokens
        access_token = create_access_token(subject=user.id)
        raw_refresh_token, token_db_hash, expires_at = create_refresh_token(
            subject=user.id
        )

        token_record = RefreshToken(
            token_hash=token_db_hash,
            user_id=user.id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        logger.info(f"User successfully authenticated: user_id={user.id}")
        return user, access_token, raw_refresh_token, expires_in

    @staticmethod
    async def refresh_user_tokens(
        db: AsyncSession, raw_refresh_token: str
    ) -> Tuple[str, str, int, User]:
        """
        Validates refresh token against database and issues rotated tokens.
        Returns: (new_access_token, new_refresh_token, expires_in_seconds, user)
        """
        # 1. Decode JWT payload
        payload = decode_token(raw_refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Check token in database
        token_hash_val = hash_token(raw_refresh_token)
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash_val,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Retrieve and verify user
        user_query = select(User).where(User.id == token_record.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 4. Revoke old refresh token (token rotation)
        token_record.is_revoked = True

        # 5. Issue new token pair
        new_access_token = create_access_token(subject=user.id)
        new_raw_refresh_token, new_token_hash, new_expires_at = create_refresh_token(
            subject=user.id
        )

        new_record = RefreshToken(
            token_hash=new_token_hash,
            user_id=user.id,
            expires_at=new_expires_at,
            is_revoked=False,
        )
        db.add(new_record)
        await db.commit()

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return new_access_token, new_raw_refresh_token, expires_in, user

    @staticmethod
    async def revoke_refresh_token(
        db: AsyncSession, raw_refresh_token: Optional[str]
    ) -> bool:
        """Revokes a refresh token in the database upon user logout."""
        if not raw_refresh_token:
            return False

        token_hash_val = hash_token(raw_refresh_token)
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash_val,
            RefreshToken.is_revoked == False,
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        if token_record:
            token_record.is_revoked = True
            await db.commit()
            return True
        return False

    @staticmethod
    async def update_user_profile(
        db: AsyncSession, user: User, update_in: UserUpdate
    ) -> User:
        """Updates basic user profile details (full_name, company_name)."""
        if update_in.full_name is not None:
            user.full_name = update_in.full_name.strip() or None
        if update_in.company_name is not None:
            user.company_name = update_in.company_name.strip() or None

        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        logger.info(f"User profile updated: user_id={user.id}")
        return user

    @staticmethod
    def get_google_auth_url(redirect_uri: Optional[str] = None) -> Tuple[str, str]:
        """
        Generates Google OAuth 2.0 authorization URL for user login and signup.
        Returns: (authorization_url, state)
        """
        state = secrets.token_urlsafe(32)
        target_redirect = redirect_uri or settings.GOOGLE_AUTH_REDIRECT_URI

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or settings.USE_MOCK_GOOGLE_AUTH:
            # Fallback/mock development authorization URL
            mock_url = f"{target_redirect}?code=mock_google_auth_code_{secrets.token_hex(6)}&state={state}"
            return mock_url, state

        scopes = "openid email profile"
        encoded_scopes = urllib.parse.quote(scopes)
        encoded_redirect = urllib.parse.quote(target_redirect, safe="")
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={encoded_redirect}&"
            f"response_type=code&"
            f"scope={encoded_scopes}&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )
        return auth_url, state

    @staticmethod
    async def authenticate_or_register_google(
        db: AsyncSession,
        code: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        id_token_str: Optional[str] = None,
        email_hint: Optional[str] = None,
        name_hint: Optional[str] = None,
    ) -> Tuple[User, str, str, int]:
        """
        Authenticates an existing user or automatically registers a new user via Google OAuth 2.0.
        Returns: (user, access_token, raw_refresh_token, expires_in_seconds)
        """
        target_redirect = redirect_uri or settings.GOOGLE_AUTH_REDIRECT_URI
        google_email = None
        google_name = None

        # Check if code is mock or in mock mode without live credentials
        is_mock = (
            (code and code.startswith("mock_google_auth_code_"))
            or (not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET)
        )

        if is_mock:
            google_email = (email_hint or "google.user@example.com").strip().lower()
            google_name = name_hint or "Google User"
            logger.info(f"Using Google Auth mock flow for email: {google_email}")
        else:
            if not code and not id_token_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either authorization code or id_token is required for Google Sign-In.",
                )

            if code:
                # Exchange code for access & id tokens
                token_url = "https://oauth2.googleapis.com/token"
                token_payload = {
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": target_redirect,
                    "grant_type": "authorization_code",
                }
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        token_resp = await client.post(token_url, data=token_payload)
                        if token_resp.status_code != 200:
                            logger.error(f"Google token exchange failed: {token_resp.text}")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Failed to exchange authorization code with Google.",
                            )
                        token_data = token_resp.json()
                        google_access_token = token_data.get("access_token")

                    # Fetch user info using access token
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        userinfo_resp = await client.get(
                            "https://www.googleapis.com/oauth2/v2/userinfo",
                            headers={"Authorization": f"Bearer {google_access_token}"},
                        )
                        if userinfo_resp.status_code != 200:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Failed to retrieve Google user profile.",
                            )
                        profile_data = userinfo_resp.json()
                        google_email = profile_data.get("email", "").strip().lower()
                        google_name = profile_data.get("name")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error communicating with Google OAuth API: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="An unexpected error occurred during Google authentication.",
                    )
            elif id_token_str:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        tokeninfo_resp = await client.get(
                            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}"
                        )
                        if tokeninfo_resp.status_code != 200:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid Google ID token.",
                            )
                        tokeninfo_data = tokeninfo_resp.json()
                        google_email = tokeninfo_data.get("email", "").strip().lower()
                        google_name = tokeninfo_data.get("name")
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error verifying Google ID token: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="An unexpected error occurred while verifying Google credentials.",
                    )

        if not google_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account did not return a valid email address.",
            )

        # 1. Query existing user
        query = select(User).where(func.lower(User.email) == google_email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Existing user: update verification & name if missing
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is currently inactive. Please contact support.",
                )
            if not user.is_verified:
                user.is_verified = True
            if not user.full_name and google_name:
                user.full_name = google_name
            user.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Existing user signed in via Google: user_id={user.id}")
        else:
            # New user: auto-register with secure random password hash
            random_pw = f"GoogleAuth_{secrets.token_urlsafe(32)}_A1!"
            hashed_pw = hash_password(random_pw)

            new_user = User(
                email=google_email,
                hashed_password=hashed_pw,
                full_name=google_name,
                company_name=None,
                is_active=True,
                is_verified=True,
            )
            db.add(new_user)
            await db.flush()
            user = new_user
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user registered via Google: user_id={user.id}")

        # 2. Issue JWT tokens
        access_token = create_access_token(subject=user.id)
        raw_refresh_token, token_db_hash, expires_at = create_refresh_token(
            subject=user.id
        )

        token_record = RefreshToken(
            token_hash=token_db_hash,
            user_id=user.id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return user, access_token, raw_refresh_token, expires_in

    @staticmethod
    async def authenticate_or_register_otp(
        db: AsyncSession,
        email: str,
        otp: str,
        full_name: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Tuple[User, str, str, int]:
        """
        Authenticates an existing user or automatically registers a new user after verifying 6-digit OTP.
        Returns: (user, access_token, raw_refresh_token, expires_in_seconds)
        """
        normalized_email = email.strip().lower()

        # 1. Verify OTP code
        is_valid, msg = otp_service.verify_otp(
            email=normalized_email, code=otp, purpose="login"
        )
        if not is_valid:
            # Also check if it was sent as registration or verification
            is_valid_reg, _ = otp_service.verify_otp(
                email=normalized_email, code=otp, purpose="registration"
            )
            if not is_valid_reg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=msg,
                )

        # 2. Query user
        query = select(User).where(func.lower(User.email) == normalized_email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is currently inactive. Please contact support.",
                )
            if not user.is_verified:
                user.is_verified = True
                user.updated_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(user)
        else:
            # Auto-register new user with random password hash and is_verified=True
            random_pw = f"OTPAuth_{secrets.token_urlsafe(32)}_A1!"
            hashed_pw = hash_password(random_pw)

            new_user = User(
                email=normalized_email,
                hashed_password=hashed_pw,
                full_name=full_name.strip() if full_name else None,
                company_name=company_name.strip() if company_name else None,
                is_active=True,
                is_verified=True,
            )
            db.add(new_user)
            await db.flush()
            user = new_user
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user registered via OTP: user_id={user.id}")

        # 3. Generate JWT tokens
        access_token = create_access_token(subject=user.id)
        raw_refresh_token, token_db_hash, expires_at = create_refresh_token(
            subject=user.id
        )

        token_record = RefreshToken(
            token_hash=token_db_hash,
            user_id=user.id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(user)

        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        logger.info(f"User authenticated via OTP: user_id={user.id}")
        return user, access_token, raw_refresh_token, expires_in

    @staticmethod
    async def reset_password_with_otp(
        db: AsyncSession,
        email: str,
        otp: str,
        new_password: str,
    ) -> bool:
        """
        Validates OTP and updates the user's password.
        """
        normalized_email = email.strip().lower()

        # 1. Verify OTP
        is_valid, msg = otp_service.verify_otp(
            email=normalized_email, code=otp, purpose="password_reset"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            )

        # 2. Validate new password strength
        is_valid_pw, pw_error = validate_password_strength(new_password)
        if not is_valid_pw:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=pw_error,
            )

        # 3. Query user
        query = select(User).where(func.lower(User.email) == normalized_email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account associated with this email address.",
            )

        # 4. Hash and update password
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Password reset successfully for user_id={user.id}")
        return True


auth_service = AuthService()
