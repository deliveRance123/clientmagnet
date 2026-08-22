from typing import AsyncGenerator, Optional
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db as db_generator
from app.models.user import User
from app.services.ai import AIService, get_ai_service
from app.services.compliance import ComplianceService

# Global compliance service instance
_compliance_service = ComplianceService()

# Optional HTTP Bearer for extracting auth header
security_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to retrieve database session."""
    async for session in db_generator():
        yield session


def get_ai_provider() -> AIService:
    """Dependency to retrieve the AI service orchestrator."""
    return get_ai_service(
        api_key=settings.GEMINI_API_KEY, use_mock=settings.USE_MOCK_AI
    )


def get_compliance_service() -> ComplianceService:
    """Dependency to retrieve the platform compliance service."""
    return _compliance_service


def get_discovery_engine(
    ai_service: AIService = Depends(get_ai_provider),
):
    """Dependency to retrieve the lead discovery engine."""
    from app.services.discovery import DiscoveryEngine
    return DiscoveryEngine(ai_service=ai_service)


def get_social_account_manager():
    """Dependency to retrieve the social account OAuth manager."""
    from app.services.social import SocialAccountManager
    return SocialAccountManager()


def get_email_service(
    ai_service: AIService = Depends(get_ai_provider),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """Dependency to retrieve the email service."""
    from app.services.email import EmailService
    return EmailService(ai_service=ai_service, compliance_service=compliance_service)


def get_content_service(
    ai_service: AIService = Depends(get_ai_provider),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """Dependency to retrieve the content and social publisher service."""
    from app.services.content_publisher import ContentService
    return ContentService(ai_service=ai_service, compliance_service=compliance_service)


def get_whatsapp_service(
    ai_service: AIService = Depends(get_ai_provider),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """Dependency to retrieve the WhatsApp Business Cloud API service."""
    from app.services.whatsapp import WhatsAppService
    return WhatsAppService(ai_service=ai_service, compliance_service=compliance_service)


def get_unified_inbox_service(
    ai_service: AIService = Depends(get_ai_provider),
    compliance_service: ComplianceService = Depends(get_compliance_service),
):
    """Dependency to retrieve the unified cross-channel inbox service."""
    from app.services.unified_inbox import UnifiedInboxService
    return UnifiedInboxService(ai_service=ai_service, compliance_service=compliance_service)


def get_activity_service():
    """Dependency to retrieve the activity logging and timeline service."""
    from app.services.activity import ActivityService
    return ActivityService()


def get_crm_service(
    activity_service = Depends(get_activity_service),
):
    """Dependency to retrieve the CRM pipeline and client management service."""
    from app.services.crm import CRMService
    return CRMService(activity_service=activity_service)


def get_global_search_service():
    """Dependency to retrieve the global search service."""
    from app.services.search import GlobalSearchService
    return GlobalSearchService()


async def get_current_user(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extracts and validates authenticated user from Bearer header or auth cookie.
    Guarantees user identity is resolved server-side.
    """
    token: Optional[str] = None

    # 1. Prefer Authorization Bearer header
    if auth_creds and auth_creds.credentials:
        token = auth_creds.credentials
    # 2. Fallback to cookie
    elif "cm_access_token" in request.cookies:
        token = request.cookies.get("cm_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures that the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return current_user
