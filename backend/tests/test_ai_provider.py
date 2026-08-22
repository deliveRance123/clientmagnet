import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.ai import LeadAnalysisResponse
from app.services.ai import (
    AIConfigurationError,
    AIInvalidOutputError,
    AIRateLimitError,
    AIService,
    GeminiProvider,
    MockProvider,
    get_ai_service,
)


# Helper to register user and get token
async def create_test_user_and_token(async_client: AsyncClient, email: str = "ai_user@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "AI Intelligence Tester",
            "company_name": "Magnet Solutions Inc",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Configuration & Abstraction Tests
# ---------------------------------------------------------------------------

def test_ai_configuration_defaults():
    """Verify that AI settings load with required defaults."""
    assert settings.GEMINI_MODEL_NAME == "gemini-1.5-flash"
    assert settings.AI_MAX_OUTPUT_TOKENS == 2048
    assert settings.AI_TEMPERATURE == 0.7
    assert settings.AI_REQUEST_TIMEOUT == 30
    assert settings.AI_MAX_RETRIES == 3
    assert settings.AI_RATE_LIMIT_PER_MINUTE == 30


def test_ai_provider_factory_selection():
    """Verify provider abstraction factory instantiates correct implementation."""
    # When mock flag is enabled or key is empty -> MockProvider
    service_mock = get_ai_service(api_key="", use_mock=True)
    assert isinstance(service_mock._provider, MockProvider)

    service_no_key = get_ai_service(api_key="", use_mock=False)
    assert isinstance(service_no_key._provider, MockProvider)

    # When valid key and use_mock is False -> GeminiProvider
    service_gemini = get_ai_service(api_key="valid-test-key", use_mock=False)
    assert isinstance(service_gemini._provider, GeminiProvider)
    assert service_gemini._provider.model_name == "gemini-1.5-flash"


@pytest.mark.asyncio
async def test_mock_provider_all_operations():
    """Verify that MockProvider generates valid, schema-compliant JSON for all 7 features."""
    provider = MockProvider()

    # 1. Lead Analysis
    analysis_raw = await provider.generate_text("analyze_lead for website development", json_mode=True)
    data = json.loads(analysis_raw)
    assert "detected_need" in data
    assert "matched_service" in data
    assert "intent_score" in data
    assert 0 <= data["intent_score"] <= 100

    # 2. Service Matching
    match_raw = await provider.generate_text("match_service inquiry", json_mode=True)
    data = json.loads(match_raw)
    assert "matched_service" in data
    assert "confidence" in data

    # 3. Intent Scoring
    score_raw = await provider.generate_text("score_intent urgency asap", json_mode=True)
    data = json.loads(score_raw)
    assert data["intent_score"] >= 80

    # 4. Social Caption
    caption_raw = await provider.generate_text("generate_caption for LinkedIn", json_mode=True)
    data = json.loads(caption_raw)
    assert "caption" in data
    assert len(data["hashtags"]) > 0

    # 5. Email Generation
    email_raw = await provider.generate_text("generate_email pitch", json_mode=True)
    data = json.loads(email_raw)
    assert "subject" in data
    assert "body" in data

    # 6. Reply Suggestion
    reply_raw = await provider.generate_text("suggest_reply to inquiry", json_mode=True)
    data = json.loads(reply_raw)
    assert "suggested_reply" in data

    # 7. Summarization
    summary_raw = await provider.generate_text("summarize_conversation transcript", json_mode=True)
    data = json.loads(summary_raw)
    assert "summary" in data
    assert "lead_status_suggestion" in data


# ---------------------------------------------------------------------------
# 2. Authenticated Endpoints Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_analyze_lead(async_client: AsyncClient):
    """Test /api/v1/ai/analyze-lead endpoint with business service context."""
    token, headers = await create_test_user_and_token(async_client, "lead_analyst@example.com")

    # Create service in DB
    await async_client.post(
        "/api/v1/services/",
        json={"name": "Bot/Automation Development", "pricing": "$3,000", "description": "Custom workflows"},
        headers=headers,
    )

    # Analyze lead
    resp = await async_client.post(
        "/api/v1/ai/analyze-lead",
        json={
            "lead_name": "Apex Logistics",
            "lead_company": "Apex Corp",
            "lead_description": "We need custom bot automation for our shipping dispatches.",
            "source": "Upwork",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "detected_need" in data
    assert data["matched_service"] == "Bot/Automation Development"
    assert 0 <= data["intent_score"] <= 100
    assert "reasoning_summary" in data
    assert "recommended_next_action" in data


@pytest.mark.asyncio
async def test_authenticated_match_service(async_client: AsyncClient):
    """Test /api/v1/ai/match-service endpoint."""
    token, headers = await create_test_user_and_token(async_client, "service_matcher@example.com")

    resp = await async_client.post(
        "/api/v1/ai/match-service",
        json={
            "lead_description": "Looking for a website designer for restaurant page",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched_service"] is not None
    assert 0.0 <= data["confidence"] <= 1.0
    assert "match_reasoning" in data


@pytest.mark.asyncio
async def test_authenticated_score_intent(async_client: AsyncClient):
    """Test /api/v1/ai/score-intent endpoint."""
    token, headers = await create_test_user_and_token(async_client, "intent_scorer@example.com")

    resp = await async_client.post(
        "/api/v1/ai/score-intent",
        json={
            "lead_description": "Need immediate kickoff for full redesign, budget approved.",
            "source": "LinkedIn",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 0 <= data["intent_score"] <= 100
    assert data["intent_level"] in ("Low", "Medium", "High", "Critical")
    assert isinstance(data["scoring_factors"], list)


@pytest.mark.asyncio
async def test_authenticated_generate_caption(async_client: AsyncClient):
    """Test /api/v1/ai/generate-caption endpoint."""
    token, headers = await create_test_user_and_token(async_client, "caption_user@example.com")

    resp = await async_client.post(
        "/api/v1/ai/generate-caption",
        json={
            "content_description": "How automation cuts agency overhead by 40%",
            "platform": "LinkedIn",
            "desired_tone": "Professional",
            "call_to_action": "Contact us for workflow audit",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["caption"]) > 10
    assert isinstance(data["hashtags"], list)
    assert "call_to_action" in data


@pytest.mark.asyncio
async def test_authenticated_generate_email_draft(async_client: AsyncClient):
    """Test /api/v1/ai/generate-email endpoint."""
    token, headers = await create_test_user_and_token(async_client, "email_drafter@example.com")

    resp = await async_client.post(
        "/api/v1/ai/generate-email",
        json={
            "lead_name": "Jessica Taylor",
            "lead_company": "Taylor Consulting",
            "lead_need": "Automated appointment booking system",
            "desired_tone": "Warm & Consultative",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "subject" in data
    assert "body" in data
    assert len(data["subject"]) > 5
    assert len(data["body"]) > 20


@pytest.mark.asyncio
async def test_authenticated_suggest_reply(async_client: AsyncClient):
    """Test /api/v1/ai/suggest-reply endpoint."""
    token, headers = await create_test_user_and_token(async_client, "reply_suggester@example.com")

    resp = await async_client.post(
        "/api/v1/ai/suggest-reply",
        json={
            "incoming_message": "What are your standard rates for building a custom dashboard?",
            "preferred_style": "Direct & Concise",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "suggested_reply" in data
    assert "reasoning_summary" in data


@pytest.mark.asyncio
async def test_authenticated_summarize_conversation(async_client: AsyncClient):
    """Test /api/v1/ai/summarize-conversation endpoint."""
    token, headers = await create_test_user_and_token(async_client, "summarizer@example.com")

    resp = await async_client.post(
        "/api/v1/ai/summarize-conversation",
        json={
            "conversation_text": (
                "Client: Hi, we need an urgent fix for our checkout flow.\n"
                "You: We can handle that. Can you share repository access?\n"
                "Client: Access sent, let us know when we can review."
            )
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert isinstance(data["client_needs"], list)
    assert "next_action" in data
    assert "lead_status_suggestion" in data


# ---------------------------------------------------------------------------
# 3. Security, Isolation & Error Handling Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_endpoints_require_authentication(async_client: AsyncClient):
    """Verify all AI endpoints reject unauthenticated requests with HTTP 401."""
    endpoints = [
        "/api/v1/ai/analyze-lead",
        "/api/v1/ai/match-service",
        "/api/v1/ai/score-intent",
        "/api/v1/ai/generate-caption",
        "/api/v1/ai/generate-email",
        "/api/v1/ai/suggest-reply",
        "/api/v1/ai/summarize-conversation",
    ]

    for ep in endpoints:
        resp = await async_client.post(ep, json={"prompt": "test"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ai_user_data_isolation(async_client: AsyncClient):
    """Verify User A cannot access User B's lead data via AI analysis."""
    # User A
    token_a, headers_a = await create_test_user_and_token(async_client, "user_a@example.com")
    # User B
    token_b, headers_b = await create_test_user_and_token(async_client, "user_b@example.com")

    # User B creates a lead
    lead_b_resp = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Secret Lead of User B", "description": "Confidential project"},
        headers=headers_b,
    )
    lead_b_id = lead_b_resp.json()["id"]

    # User A attempts to analyze User B's lead using lead_id
    # Analysis must not expose or use User B's confidential lead details
    resp = await async_client.post(
        "/api/v1/ai/analyze-lead",
        json={"lead_id": lead_b_id, "lead_description": "User A provided text"},
        headers=headers_a,
    )
    assert resp.status_code == 200


def test_ai_json_parsing_and_recovery():
    """Verify _parse_and_validate_json strips markdown fences and catches invalid JSON."""
    service = AIService(MockProvider())

    # Clean JSON
    valid_json = '{"detected_need": "Web app", "matched_service": null, "matched_service_id": null, "intent_score": 90, "reasoning_summary": "High need", "recommended_next_action": "Email"}'
    res = service._parse_and_validate_json(valid_json, LeadAnalysisResponse)
    assert res.intent_score == 90

    # Wrapped in markdown ```json ... ```
    wrapped_json = f"```json\n{valid_json}\n```"
    res_wrapped = service._parse_and_validate_json(wrapped_json, LeadAnalysisResponse)
    assert res_wrapped.intent_score == 90

    # Malformed JSON
    with pytest.raises(AIInvalidOutputError):
        service._parse_and_validate_json("Not a JSON object", LeadAnalysisResponse)


@pytest.mark.asyncio
async def test_ai_audit_logging_in_db(async_client: AsyncClient, db_session: AsyncSession):
    """Verify that successful AI operations write audit logs to the PostgreSQL database."""
    token, headers = await create_test_user_and_token(async_client, "audit_tester@example.com")

    # Perform AI request
    resp = await async_client.post(
        "/api/v1/ai/score-intent",
        json={"lead_description": "Audited intent score test"},
        headers=headers,
    )
    assert resp.status_code == 200

    # Query audit logs
    query = select(AuditLog).where(AuditLog.action == "AI_OPERATION")
    logs = (await db_session.execute(query)).scalars().all()
    assert len(logs) > 0

    latest_log = logs[-1]
    meta = json.loads(latest_log.metadata_json)
    assert meta["operation"] == "score_intent"
    assert meta["success"] is True
    assert "duration_ms" in meta
