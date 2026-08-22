import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

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

logger = logging.getLogger("app.services.auth")


class AuthService:
    """Authentication and user session management service."""

    @staticmethod
    async def register_user(
        db: AsyncSession, user_in: UserRegister
    ) -> Tuple[User, str, str, int]:
        """
        Registers a new user after validating email uniqueness and password strength.
        Returns: (user, access_token, raw_refresh_token, expires_in_seconds)
        """
        normalized_email = user_in.email.strip().lower()

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

        # 4. Create and persist user
        new_user = User(
            email=normalized_email,
            hashed_password=hashed_pw,
            full_name=user_in.full_name.strip() if user_in.full_name else None,
            company_name=user_in.company_name.strip() if user_in.company_name else None,
            is_active=True,
            is_verified=False,
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


auth_service = AuthService()
