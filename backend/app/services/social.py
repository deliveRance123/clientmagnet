import hashlib
import json
import logging
import secrets
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.social import (
    OAuthInitiateResponse,
    OAuthTokenResult,
    SocialAccountInfo,
)

logger = logging.getLogger("app.social")


# ---------------------------------------------------------------------------
# State Security (Signed Tamper-Proof OAuth State)
# ---------------------------------------------------------------------------

def generate_oauth_state(user_id: str, platform: str) -> str:
    """Generates a cryptographically signed state token with 15-minute validity."""
    payload = {
        "sub": user_id,
        "platform": platform.upper(),
        "nonce": secrets.token_hex(8),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def validate_oauth_state(state: str, expected_platform: str) -> str:
    """Validates the state token and returns user_id if valid; raises ValueError if invalid/expired."""
    try:
        payload = jwt.decode(
            state, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("platform") != expected_platform.upper():
            raise ValueError(f"State platform mismatch: expected {expected_platform.upper()}")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("State payload missing subject user ID")
        return str(user_id)
    except jwt.ExpiredSignatureError:
        raise ValueError("OAuth authorization session has expired. Please try connecting again.")
    except Exception as e:
        raise ValueError(f"Invalid or tampered OAuth state parameter: {e}")


# ---------------------------------------------------------------------------
# Provider Abstraction Interface
# ---------------------------------------------------------------------------

class SocialPlatformProvider(ABC):
    """Abstract base class for all social media platform OAuth providers."""

    platform: str = "BASE"

    @abstractmethod
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Returns the official platform OAuth authorization dialog URL."""
        pass

    @abstractmethod
    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        """Exchanges an authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        """Fetches account identity and profile metadata from the platform."""
        pass

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResult:
        """Refreshes an expired access token where supported."""
        raise NotImplementedError(f"Token refresh not implemented for {self.platform}")

    async def revoke_token(self, access_token: str) -> bool:
        """Revokes an access token on account disconnect."""
        return True


# ---------------------------------------------------------------------------
# Meta Provider (Facebook & Instagram)
# ---------------------------------------------------------------------------

class MetaProvider(SocialPlatformProvider):
    """Official Meta Graph API OAuth Provider for Facebook and Instagram."""

    def __init__(self, platform_name: str = "FACEBOOK"):
        self.platform = platform_name.upper()
        self.client_id = settings.META_CLIENT_ID
        self.client_secret = settings.META_CLIENT_SECRET

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = (
            "pages_show_list,pages_read_engagement,pages_manage_posts"
            if self.platform == "FACEBOOK"
            else "instagram_basic,instagram_manage_comments,instagram_content_publish"
        )
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}&scope={scopes}"
        )

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        url = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        scopes_list = [
            "pages_show_list", "pages_read_engagement"
        ] if self.platform == "FACEBOOK" else ["instagram_basic", "instagram_manage_comments"]

        return OAuthTokenResult(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 5184000),  # 60 days long-lived
            scopes=scopes_list,
            raw_response=data,
        )

    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        url = "https://graph.facebook.com/v19.0/me"
        params = {"fields": "id,name,picture", "access_token": access_token}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        pic_url = data.get("picture", {}).get("data", {}).get("url")
        return SocialAccountInfo(
            account_identifier=str(data["id"]),
            account_name=data.get("name", "Meta Connected User"),
            account_username=data.get("name"),
            profile_picture_url=pic_url,
            raw_profile=data,
        )


# ---------------------------------------------------------------------------
# X (Twitter) Provider
# ---------------------------------------------------------------------------

class XProvider(SocialPlatformProvider):
    """Official X (Twitter) API v2 OAuth 2.0 with PKCE Provider."""

    platform = "X"

    def __init__(self):
        self.client_id = settings.X_CLIENT_ID
        self.client_secret = settings.X_CLIENT_SECRET

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = "tweet.read%20tweet.write%20users.read%20offline.access"
        return (
            f"https://twitter.com/i/oauth2/authorize?response_type=code"
            f"&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={scopes}"
            f"&state={state}&code_challenge=challenge&code_challenge_method=plain"
        )

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        url = "https://api.twitter.com/2/oauth2/token"
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "code_verifier": "challenge",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=data, auth=(self.client_id, self.client_secret))
            resp.raise_for_status()
            token_data = resp.json()

        scopes_str = token_data.get("scope", "tweet.read users.read offline.access")
        return OAuthTokenResult(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 7200),
            scopes=[s for s in scopes_str.split(" ") if s],
            raw_response=token_data,
        )

    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        url = "https://api.twitter.com/2/users/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"user.fields": "profile_image_url,username,name"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json().get("data", {})

        return SocialAccountInfo(
            account_identifier=str(data.get("id")),
            account_name=data.get("name", "X User"),
            account_username=f"@{data.get('username', 'user')}",
            profile_picture_url=data.get("profile_image_url"),
            raw_profile=data,
        )


# ---------------------------------------------------------------------------
# LinkedIn Provider
# ---------------------------------------------------------------------------

class LinkedInProvider(SocialPlatformProvider):
    """Official LinkedIn OAuth 2.0 Provider."""

    platform = "LINKEDIN"

    def __init__(self):
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = "openid%20profile%20email%20w_member_social"
        return (
            f"https://www.linkedin.com/oauth/v2/authorization?response_type=code"
            f"&client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}&scope={scopes}"
        )

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            token_data = resp.json()

        scopes_list = ["openid", "profile", "email", "w_member_social"]
        return OAuthTokenResult(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 5184000),  # 60 days
            scopes=scopes_list,
            raw_response=token_data,
        )

    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return SocialAccountInfo(
            account_identifier=str(data.get("sub", "")),
            account_name=data.get("name", "LinkedIn Member"),
            account_username=data.get("email"),
            profile_picture_url=data.get("picture"),
            raw_profile=data,
        )


# ---------------------------------------------------------------------------
# TikTok Provider
# ---------------------------------------------------------------------------

class TikTokProvider(SocialPlatformProvider):
    """Official TikTok Login Kit OAuth 2.0 Provider."""

    platform = "TIKTOK"

    def __init__(self):
        self.client_key = settings.TIKTOK_CLIENT_KEY
        self.client_secret = settings.TIKTOK_CLIENT_SECRET

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = "user.info.basic,video.list"
        return (
            f"https://www.tiktok.com/v2/auth/authorize/?"
            f"client_key={self.client_key}&scope={scopes}&response_type=code&redirect_uri={redirect_uri}&state={state}"
        )

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, data=data)
            resp.raise_for_status()
            token_data = resp.json().get("data", {})

        return OAuthTokenResult(
            access_token=token_data.get("access_token", ""),
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 86400),
            scopes=["user.info.basic", "video.list"],
            raw_response=token_data,
        )

    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        url = "https://open.tiktokapis.com/v2/user/info/"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"fields": "open_id,union_id,avatar_url,display_name"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            user_data = resp.json().get("data", {}).get("user", {})

        return SocialAccountInfo(
            account_identifier=user_data.get("open_id", "tiktok_user"),
            account_name=user_data.get("display_name", "TikTok Creator"),
            account_username=f"@{user_data.get('display_name', 'creator').lower().replace(' ', '')}",
            profile_picture_url=user_data.get("avatar_url"),
            raw_profile=user_data,
        )


# ---------------------------------------------------------------------------
# Mock Social Provider (for Testing & Offline Development)
# ---------------------------------------------------------------------------

class MockSocialProvider(SocialPlatformProvider):
    """Deterministic Mock Provider for testing and local development without credentials."""

    def __init__(self, platform_name: str = "FACEBOOK"):
        self.platform = platform_name.upper()

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        # Returns a mock callback redirect containing state and code
        return f"{redirect_uri}?code=mock_oauth_code_12345&state={state}"

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        scopes_map = {
            "FACEBOOK": ["pages_show_list", "pages_read_engagement", "pages_manage_posts"],
            "INSTAGRAM": ["instagram_basic", "instagram_manage_comments"],
            "X": ["tweet.read", "tweet.write", "users.read", "offline.access"],
            "LINKEDIN": ["openid", "profile", "email", "w_member_social"],
            "TIKTOK": ["user.info.basic", "video.list"],
        }
        return OAuthTokenResult(
            access_token=f"mock_access_token_{self.platform.lower()}_{secrets.token_hex(8)}",
            refresh_token=f"mock_refresh_token_{self.platform.lower()}_{secrets.token_hex(8)}",
            expires_in=3600,
            scopes=scopes_map.get(self.platform, ["basic_access"]),
            raw_response={"mock": True, "status": "authorized"},
        )

    async def get_account_info(self, access_token: str) -> SocialAccountInfo:
        profile_map = {
            "FACEBOOK": {
                "id": "fb-page-100293847",
                "name": "Client Magnet Agency Page",
                "username": "client_magnet_agency",
                "avatar": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150",
            },
            "INSTAGRAM": {
                "id": "ig-account-90283471",
                "name": "Client Magnet Studio",
                "username": "@clientmagnet.official",
                "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            },
            "X": {
                "id": "x-handle-18273645",
                "name": "Client Magnet Growth",
                "username": "@ClientMagnetApp",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            },
            "LINKEDIN": {
                "id": "li-member-77281930",
                "name": "Client Magnet B2B Solutions",
                "username": "client-magnet-b2b",
                "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            },
            "TIKTOK": {
                "id": "tt-creator-66281900",
                "name": "Client Magnet Shorts",
                "username": "@clientmagnethacks",
                "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            },
        }
        info = profile_map.get(
            self.platform,
            {
                "id": f"{self.platform.lower()}-id-12345",
                "name": f"{self.platform} User",
                "username": f"@{self.platform.lower()}_user",
                "avatar": None,
            },
        )
        return SocialAccountInfo(
            account_identifier=info["id"],
            account_name=info["name"],
            account_username=info["username"],
            profile_picture_url=info.get("avatar"),
            raw_profile=info,
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResult:
        return OAuthTokenResult(
            access_token=f"mock_refreshed_token_{secrets.token_hex(8)}",
            refresh_token=refresh_token,
            expires_in=3600,
            scopes=["basic_access"],
        )


# ---------------------------------------------------------------------------
# Social Account Manager
# ---------------------------------------------------------------------------

class SocialAccountManager:
    """
    Central service managing OAuth lifecycle, credential encryption at rest,
    permission checking, and social account state.
    """

    def get_provider(self, platform: str) -> SocialPlatformProvider:
        """Resolves the appropriate platform provider based on environment settings."""
        p_upper = platform.upper()

        if settings.USE_MOCK_SOCIAL_OAUTH:
            return MockSocialProvider(p_upper)

        if p_upper in ("FACEBOOK", "INSTAGRAM"):
            if not settings.META_CLIENT_ID or not settings.META_CLIENT_SECRET:
                return MockSocialProvider(p_upper)
            return MetaProvider(p_upper)
        elif p_upper == "X":
            if not settings.X_CLIENT_ID or not settings.X_CLIENT_SECRET:
                return MockSocialProvider("X")
            return XProvider()
        elif p_upper == "LINKEDIN":
            if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET:
                return MockSocialProvider("LINKEDIN")
            return LinkedInProvider()
        elif p_upper == "TIKTOK":
            if not settings.TIKTOK_CLIENT_KEY or not settings.TIKTOK_CLIENT_SECRET:
                return MockSocialProvider("TIKTOK")
            return TikTokProvider()
        else:
            return MockSocialProvider(p_upper)

    def initiate_connect(
        self, user_id: str, platform: str, custom_redirect_uri: Optional[str] = None
    ) -> OAuthInitiateResponse:
        """Initiates an OAuth connection flow, generating a signed CSRF state and platform dialog URL."""
        p_upper = platform.upper()
        provider = self.get_provider(p_upper)
        state = generate_oauth_state(user_id=user_id, platform=p_upper)

        redirect_uri = custom_redirect_uri or f"{settings.SOCIAL_OAUTH_REDIRECT_BASE_URL}/{platform.lower()}"
        auth_url = provider.get_authorization_url(state=state, redirect_uri=redirect_uri)

        return OAuthInitiateResponse(
            platform=p_upper,
            authorization_url=auth_url,
            state=state,
        )

    async def handle_oauth_callback(
        self,
        db: AsyncSession,
        platform: str,
        code: str,
        state: str,
        custom_redirect_uri: Optional[str] = None,
    ) -> SocialAccount:
        """
        Handles OAuth callback:
        1. Validates state & user ID.
        2. Exchanges code for tokens.
        3. Retrieves profile identity.
        4. Encrypts sensitive tokens at rest.
        5. Creates or updates SocialAccount record in PostgreSQL.
        """
        p_upper = platform.upper()

        # 1. State Validation
        user_id = validate_oauth_state(state=state, expected_platform=p_upper)

        # 2. Token Exchange
        provider = self.get_provider(p_upper)
        redirect_uri = custom_redirect_uri or f"{settings.SOCIAL_OAUTH_REDIRECT_BASE_URL}/{platform.lower()}"
        token_result = await provider.exchange_code(code=code, redirect_uri=redirect_uri)

        # 3. Fetch Account Info
        account_info = await provider.get_account_info(access_token=token_result.access_token)

        # 4. Check for Existing Account
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == p_upper,
            SocialAccount.account_identifier == account_info.account_identifier,
        )
        existing_account = (await db.execute(query)).scalar_one_or_none()

        expires_at = None
        if token_result.expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_result.expires_in)

        credentials_dict = {
            "access_token": token_result.access_token,
            "refresh_token": token_result.refresh_token,
            "token_type": token_result.token_type,
        }

        if existing_account:
            # Update existing connection
            existing_account.account_name = account_info.account_name
            existing_account.account_username = account_info.account_username
            existing_account.profile_picture_url = account_info.profile_picture_url
            existing_account.connection_status = "CONNECTED"
            existing_account.token_expires_at = expires_at
            existing_account.scopes = json.dumps(token_result.scopes)
            existing_account.credentials = credentials_dict
            existing_account.metadata_json = json.dumps(account_info.raw_profile) if account_info.raw_profile else None
            account = existing_account
        else:
            # Create new connection
            account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=user_id,
                platform=p_upper,
                account_identifier=account_info.account_identifier,
                account_name=account_info.account_name,
                account_username=account_info.account_username,
                profile_picture_url=account_info.profile_picture_url,
                connection_status="CONNECTED",
                token_expires_at=expires_at,
                scopes=json.dumps(token_result.scopes),
                metadata_json=json.dumps(account_info.raw_profile) if account_info.raw_profile else None,
            )
            account.credentials = credentials_dict
            db.add(account)

        await db.commit()
        await db.refresh(account)
        logger.info(f"Successfully connected {p_upper} account '{account.account_name}' for user {user_id}")
        return account

    async def disconnect_account(
        self, db: AsyncSession, user: User, account_id: str
    ) -> SocialAccount:
        """Disconnects a connected social account, wiping encrypted credentials."""
        query = select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == user.id,
        )
        account = (await db.execute(query)).scalar_one_or_none()
        if not account:
            raise ValueError("Social account not found.")

        # Attempt platform token revocation if access token exists
        creds = account.credentials
        if creds and creds.get("access_token"):
            try:
                provider = self.get_provider(account.platform)
                await provider.revoke_token(creds["access_token"])
            except Exception as e:
                logger.warning(f"Failed to revoke token on platform {account.platform}: {e}")

        account.connection_status = "DISCONNECTED"
        account.credentials = None
        account.token_expires_at = None
        await db.commit()
        await db.refresh(account)
        logger.info(f"Disconnected {account.platform} account {account_id} for user {user.id}")
        return account

    async def refresh_account_token(
        self, db: AsyncSession, user: User, account_id: str
    ) -> SocialAccount:
        """Refreshes access token for a connected account."""
        query = select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == user.id,
        )
        account = (await db.execute(query)).scalar_one_or_none()
        if not account:
            raise ValueError("Social account not found.")

        creds = account.credentials
        if not creds or not creds.get("refresh_token"):
            account.connection_status = "REAUTH_REQUIRED"
            await db.commit()
            raise ValueError(f"No refresh token available for {account.platform}. Re-authorization is required.")

        try:
            provider = self.get_provider(account.platform)
            token_result = await provider.refresh_token(creds["refresh_token"])

            creds["access_token"] = token_result.access_token
            if token_result.refresh_token:
                creds["refresh_token"] = token_result.refresh_token

            account.credentials = creds
            if token_result.expires_in:
                account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_result.expires_in)
            account.connection_status = "CONNECTED"
            await db.commit()
            await db.refresh(account)
            return account
        except Exception as e:
            account.connection_status = "REAUTH_REQUIRED"
            await db.commit()
            raise ValueError(f"Token refresh failed: {e}. Re-authorization is required.")

    async def list_user_accounts(
        self, db: AsyncSession, user_id: str
    ) -> List[SocialAccount]:
        """Lists all connected social accounts for the user."""
        query = (
            select(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .order_by(SocialAccount.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    def verify_scope_compliance(self, account: SocialAccount, required_scope: str) -> bool:
        """Checks whether the connected account has the required scope granted."""
        granted = account.get_scopes_list()
        return required_scope.lower() in [s.lower() for s in granted]
