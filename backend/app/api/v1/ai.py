import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ai_provider, get_current_active_user, get_db_session
from app.models.user import User
from app.schemas.ai import (
    CaptionGenerateRequest,
    CaptionGenerateResponse,
    ConversationSummaryRequest,
    ConversationSummaryResponse,
    EmailDraftRequest,
    EmailDraftResponse,
    IntentScoreRequest,
    IntentScoreResponse,
    LeadAnalysisRequest,
    LeadAnalysisResponse,
    ReplySuggestionRequest,
    ReplySuggestionResponse,
    ServiceMatchRequest,
    ServiceMatchResponse,
)
from app.services.ai import (
    AIConfigurationError,
    AIError,
    AIInvalidOutputError,
    AIProviderError,
    AIRateLimitError,
    AIService,
    AITimeoutError,
)

logger = logging.getLogger("app.api.ai")

router = APIRouter()


def _handle_ai_exception(e: Exception) -> None:
    """Translates AI service domain errors into appropriate HTTP exceptions."""
    if isinstance(e, AIRateLimitError):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    if isinstance(e, AITimeoutError):
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"AI Request timed out: {str(e)}",
        )
    if isinstance(e, AIConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service configuration error: {str(e)}",
        )
    if isinstance(e, AIInvalidOutputError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Malformed AI structured output: {str(e)}",
        )
    if isinstance(e, AIProviderError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI provider communication error: {str(e)}",
        )
    logger.error(f"Unexpected error during AI operation: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An error occurred while executing AI intelligence operation: {str(e)}",
    )


# ---------------------------------------------------------------------------
# 1. Lead Analysis Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/analyze-lead",
    response_model=LeadAnalysisResponse,
    summary="Analyze lead requirements and match with user services",
)
async def analyze_lead(
    request: LeadAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """
    Evaluates prospect details, identifies specific service needs,
    matches against user services stored in PostgreSQL, and scores acquisition intent.
    """
    try:
        return await ai_service.analyze_lead(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 2. Service Matching Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/match-service",
    response_model=ServiceMatchResponse,
    summary="Match lead inquiry against user service catalogue",
)
async def match_service(
    request: ServiceMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """Matches a lead description to the user's PostgreSQL services."""
    try:
        return await ai_service.match_service(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 3. Intent Scoring Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/score-intent",
    response_model=IntentScoreResponse,
    summary="Calculate client acquisition intent score (0-100)",
)
async def score_lead_intent(
    request: IntentScoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """Estimates buying intent based on clarity, urgency, and budget indicators."""
    try:
        return await ai_service.score_lead_intent(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 4. Social Caption Generator Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/generate-caption",
    response_model=CaptionGenerateResponse,
    summary="Generate social media captions, hashtags, and CTA",
)
async def generate_caption(
    request: CaptionGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """Generates platform-tailored social media captions and hashtags."""
    try:
        return await ai_service.generate_caption(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 5. Personalized Email Draft Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/generate-email",
    response_model=EmailDraftResponse,
    summary="Draft personalized consultative outreach email",
)
async def generate_email_draft(
    request: EmailDraftRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """
    Drafts an outreach email matching the user's business offering to the lead's problem.
    Advisory only; never automatically sent.
    """
    try:
        return await ai_service.generate_email_draft(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 6. Reply Suggestion Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/suggest-reply",
    response_model=ReplySuggestionResponse,
    summary="Suggest professional reply to an incoming message",
)
async def suggest_reply(
    request: ReplySuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """Generates context-aware response suggestions for client conversations."""
    try:
        return await ai_service.suggest_reply(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)


# ---------------------------------------------------------------------------
# 7. Conversation Summarization Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/summarize-conversation",
    response_model=ConversationSummaryResponse,
    summary="Summarize conversation and suggest pipeline status",
)
async def summarize_conversation(
    request: ConversationSummaryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    ai_service: AIService = Depends(get_ai_provider),
):
    """Summarizes conversation history into key needs, open questions, and next actions."""
    try:
        return await ai_service.summarize_conversation(db=db, user=current_user, request=request)
    except Exception as e:
        _handle_ai_exception(e)
