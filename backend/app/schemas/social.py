import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Public Sanitized Social Account Schemas (Never exposes raw credentials)
# ---------------------------------------------------------------------------

class SocialAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    platform: str
    account_identifier: str
    account_name: Optional[str] = None
    account_username: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connection_status: str = Field("CONNECTED", description="CONNECTED, DISCONNECTED, EXPIRED, REAUTH_REQUIRED, ERROR")
    scopes: Optional[List[str]] = Field(default_factory=list)
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_account(cls, account: Any) -> "SocialAccountOut":
        scopes_list: List[str] = []
        if account.scopes:
            try:
                parsed = json.loads(account.scopes)
                scopes_list = parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                scopes_list = [s.strip() for s in account.scopes.split(",") if s.strip()]

        return cls(
            id=account.id,
            user_id=account.user_id,
            platform=account.platform,
            account_identifier=account.account_identifier,
            account_name=account.account_name,
            account_username=account.account_username,
            profile_picture_url=account.profile_picture_url,
            connection_status=account.connection_status,
            scopes=scopes_list,
            token_expires_at=account.token_expires_at,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )


class OAuthInitiateResponse(BaseModel):
    platform: str
    authorization_url: str
    state: str


class OAuthCallbackPayload(BaseModel):
    code: Optional[str] = Field(None, description="OAuth authorization code")
    state: str = Field(..., description="CSRF state parameter")
    error: Optional[str] = None
    error_description: Optional[str] = None


class SocialDisconnectResponse(BaseModel):
    status: str = "success"
    message: str
    account_id: str


# ---------------------------------------------------------------------------
# Internal Platform Provider Models
# ---------------------------------------------------------------------------

class SocialAccountInfo(BaseModel):
    account_identifier: str
    account_name: str
    account_username: Optional[str] = None
    profile_picture_url: Optional[str] = None
    raw_profile: Optional[Dict[str, Any]] = None


class OAuthTokenResult(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scopes: List[str] = Field(default_factory=list)
    token_type: Optional[str] = "Bearer"
    raw_response: Optional[Dict[str, Any]] = None
