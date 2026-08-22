import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.service import Service
from app.models.user import User
from app.schemas.ai import (
    CaptionGenerateRequest,
    CaptionGenerateResponse,
    ChatMessageItem,
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

logger = logging.getLogger("app.ai")

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Exception Hierarchy
# ---------------------------------------------------------------------------

class AIError(Exception):
    """Base exception for all AI operations."""
    def __init__(self, message: str, category: str = "AI_ERROR"):
        super().__init__(message)
        self.category = category


class AIConfigurationError(AIError):
    def __init__(self, message: str):
        super().__init__(message, category="CONFIGURATION_ERROR")


class AIRateLimitError(AIError):
    def __init__(self, message: str):
        super().__init__(message, category="RATE_LIMIT_EXCEEDED")


class AITimeoutError(AIError):
    def __init__(self, message: str):
        super().__init__(message, category="TIMEOUT_ERROR")


class AIProviderError(AIError):
    def __init__(self, message: str):
        super().__init__(message, category="PROVIDER_ERROR")


class AIInvalidOutputError(AIError):
    def __init__(self, message: str):
        super().__init__(message, category="INVALID_OUTPUT_ERROR")


# ---------------------------------------------------------------------------
# AI Provider Interfaces & Implementations
# ---------------------------------------------------------------------------

class AIProvider(ABC):
    """Abstract base class for all AI model providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        **kwargs,
    ) -> str:
        """Asynchronously generates text for a given prompt."""
        pass


class MockProvider(AIProvider):
    """Deterministic, schema-compliant mock provider for testing and keyless development."""

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        **kwargs,
    ) -> str:
        logger.info("[MockProvider] Processing AI request.")
        prompt_lower = prompt.lower()
        sys_lower = (system_instruction or "").lower()

        if not json_mode:
            return "This is a simulated AI text response from the MockProvider."

        # 1. Lead Analysis
        if "[operation: analyze_lead]" in sys_lower or "analyze_lead" in prompt_lower:
            matched_svc = "Website Design"
            matched_id = None
            if "bot" in prompt_lower or "automation" in prompt_lower:
                matched_svc = "Bot/Automation Development"
            elif "graphic" in prompt_lower or "logo" in prompt_lower or "branding" in prompt_lower:
                matched_svc = "Graphics Design"

            id_match = re.search(r"id:\s*([a-f0-9\-]{36})", prompt, re.IGNORECASE)
            if id_match:
                matched_id = id_match.group(1)

            return json.dumps({
                "detected_need": "Complete responsive website redesign and booking system integration.",
                "matched_service": matched_svc,
                "matched_service_id": matched_id,
                "intent_score": 85.0,
                "reasoning_summary": "The prospect clearly outlined an active project requirement and requested an immediate quote.",
                "recommended_next_action": "Send a personalized consultative email highlighting relevant portfolio projects."
            })

        # 2. Service Matching
        if "[operation: match_service]" in sys_lower or "match_service" in prompt_lower:
            return json.dumps({
                "matched_service": "Website Design",
                "matched_service_id": None,
                "confidence": 0.92,
                "match_reasoning": "The prospect's requirements for a web presence directly align with your web design offering."
            })

        # 3. Intent Scoring
        if "[operation: score_intent]" in sys_lower or "score_intent" in prompt_lower:
            score = 80.0
            if "urgency" in prompt_lower or "asap" in prompt_lower or "immediate" in prompt_lower:
                score = 95.0
            return json.dumps({
                "intent_score": score,
                "intent_level": "High" if score >= 75 else "Medium",
                "scoring_factors": [
                    "Explicit project scope stated",
                    "Ready budget mentioned",
                    "Direct outreach looking for provider"
                ],
                "reasoning": "High buying intent indicated by specific timelines and explicit provider search."
            })

        # 4. Social Caption Generation
        if "[operation: generate_caption]" in sys_lower or "generate_caption" in prompt_lower:
            return json.dumps({
                "caption": "Elevate your business online with seamless digital experiences. Whether you need a modern web presence or bespoke automation, our tailored solutions deliver real results. Let's build your next growth engine.",
                "hashtags": ["#WebDesign", "#Automation", "#BusinessGrowth", "#ClientAcquisition", "#SaaS"],
                "call_to_action": "DM us or link in bio to schedule your discovery call today."
            })

        # 5. Email Generation
        if "[operation: generate_email]" in sys_lower or "generate_email" in prompt_lower:
            return json.dumps({
                "subject": "Ideas for scaling your digital presence — Client Magnet Consultation",
                "body": (
                    "Hi there,\n\n"
                    "I noticed your team is looking to enhance your online services. "
                    "We specialize in building modern, high-converting digital solutions tailored specifically to your industry.\n\n"
                    "I would love to share a few ideas on how we can streamline your project and deliver rapid turnaround. "
                    "Are you available for a brief 10-minute chat this Thursday?\n\n"
                    "Best regards,\nClient Magnet Team"
                ),
                "matched_service_name": "Website Design",
                "tone_used": "Professional"
            })

        # 6. Reply Suggestion
        if "[operation: suggest_reply]" in sys_lower or "suggest_reply" in prompt_lower:
            return json.dumps({
                "suggested_reply": (
                    "Thank you for reaching out! We would be delighted to assist you with this project. "
                    "Could you share a bit more detail about your target timeline and specific milestones?"
                ),
                "reasoning_summary": "Acknowledges client inquiry warmly and asks a focused qualifying question."
            })

        # 7. Conversation Summarization
        if "[operation: summarize_conversation]" in sys_lower or "summarize_conversation" in prompt_lower:
            return json.dumps({
                "summary": "The prospect inquired about custom software development pricing and requested portfolio examples.",
                "client_needs": ["Responsive UI", "Automated workflows", "Fast turnaround"],
                "questions": ["What is the estimated delivery timeline?"],
                "next_action": "Send portfolio links and proposal draft.",
                "lead_status_suggestion": "INTERESTED"
            })

        # Fallback structured object
        return json.dumps({"response": "Mock structured response", "status": "success"})


class GeminiProvider(AIProvider):
    """Production provider integrating the Google Gemini API with safety and retry logic."""

    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self.max_tokens = max_tokens or settings.AI_MAX_OUTPUT_TOKENS
        self.temperature = temperature or settings.AI_TEMPERATURE
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT
        self.max_retries = max_retries or settings.AI_MAX_RETRIES
        self._initialized = False

        if not api_key:
            logger.warning("GeminiProvider: GEMINI_API_KEY is not configured.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            self._initialized = True
            logger.info(f"GeminiProvider initialized with model '{self.model_name}'.")
        except ImportError:
            logger.error("GeminiProvider: 'google-generativeai' package is not installed.")
        except Exception as e:
            logger.error(f"GeminiProvider initialization error: {e}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        **kwargs,
    ) -> str:
        if not self._initialized:
            raise AIConfigurationError(
                "GeminiProvider is not initialized. Ensure GEMINI_API_KEY is properly set in backend environment variables."
            )

        model_name = kwargs.get("model", self.model_name)
        temperature = kwargs.get("temperature", self.temperature)
        max_output_tokens = kwargs.get("max_tokens", self.max_tokens)
        timeout = kwargs.get("timeout", self.timeout)

        # Prepare generation config
        gen_config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if json_mode:
            gen_config_kwargs["response_mime_type"] = "application/json"

        generation_config = self.genai.types.GenerationConfig(**gen_config_kwargs)

        model_kwargs: Dict[str, Any] = {"model_name": model_name}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        model = self.genai.GenerativeModel(**model_kwargs)

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Gemini API request attempt {attempt}/{self.max_retries} "
                    f"(model: {model_name}, json_mode: {json_mode}, prompt_len: {len(prompt)})"
                )

                # Wrap asynchronous generation in a timeout
                response = await asyncio.wait_for(
                    model.generate_content_async(
                        contents=prompt,
                        generation_config=generation_config,
                    ),
                    timeout=float(timeout),
                )

                if not response.text:
                    raise AIInvalidOutputError("Gemini returned an empty response.")

                return response.text

            except asyncio.TimeoutError:
                last_error = AITimeoutError(f"Gemini request timed out after {timeout} seconds.")
                logger.warning(f"Attempt {attempt}: Timeout.")
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "rate" in err_str:
                    last_error = AIRateLimitError(f"Gemini rate limit / quota reached: {e}")
                elif "api_key" in err_str or "invalid argument" in err_str:
                    raise AIConfigurationError(f"Gemini API configuration or key error: {e}")
                else:
                    last_error = AIProviderError(f"Gemini provider error: {e}")
                logger.warning(f"Attempt {attempt} failed: {e}")

            if attempt < self.max_retries:
                backoff_sec = 2 ** (attempt - 1)
                logger.info(f"Retrying in {backoff_sec}s...")
                await asyncio.sleep(backoff_sec)

        raise last_error or AIProviderError("Gemini request failed after maximum retries.")


# ---------------------------------------------------------------------------
# AIService Orchestration Layer
# ---------------------------------------------------------------------------

class AIService:
    """
    Central orchestration service for all AI intelligence features in Client Magnet.
    Enforces rate limits, injects PostgreSQL business context, validates JSON outputs,
    and writes safe audit logs.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        self._provider = provider
        # In-memory sliding window rate limiter: {user_id: [timestamp_1, timestamp_2, ...]}
        self._user_request_timestamps: Dict[str, List[float]] = {}

    def set_provider(self, provider: AIProvider) -> None:
        self._provider = provider

    def has_provider(self) -> bool:
        return self._provider is not None

    def _check_rate_limit(self, user_id: str) -> None:
        """Enforces user-level rate limiting (requests per minute)."""
        now = time.time()
        window = 60.0
        limit = settings.AI_RATE_LIMIT_PER_MINUTE

        if user_id not in self._user_request_timestamps:
            self._user_request_timestamps[user_id] = []

        # Prune timestamps older than 60s
        self._user_request_timestamps[user_id] = [
            t for t in self._user_request_timestamps[user_id] if now - t < window
        ]

        if len(self._user_request_timestamps[user_id]) >= limit:
            raise AIRateLimitError(
                f"Rate limit of {limit} AI requests per minute exceeded. Please wait a moment."
            )

        self._user_request_timestamps[user_id].append(now)

    async def _log_ai_request(
        self,
        db: AsyncSession,
        user_id: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error_category: Optional[str] = None,
    ) -> None:
        """Records an AI usage audit log in PostgreSQL without storing API keys or sensitive content."""
        try:
            provider_type = "MockProvider" if isinstance(self._provider, MockProvider) else "GeminiProvider"
            metadata = {
                "operation": operation,
                "provider": provider_type,
                "model": settings.GEMINI_MODEL_NAME if provider_type == "GeminiProvider" else "mock",
                "duration_ms": round(duration_ms, 2),
                "success": success,
                "error_category": error_category,
            }
            audit_entry = AuditLog(
                user_id=user_id,
                action="AI_OPERATION",
                entity_type="ai_request",
                metadata_json=json.dumps(metadata),
            )
            db.add(audit_entry)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record AI audit log: {e}")
            await db.rollback()

    async def get_user_business_context(
        self, db: AsyncSession, user_id: str
    ) -> Dict[str, Any]:
        """
        Dynamically loads the authenticated user's active services and business profile
        directly from PostgreSQL. Never hardcodes service offerings.
        """
        query = select(Service).where(
            Service.user_id == user_id,
            Service.is_active == True
        )
        result = await db.execute(query)
        services = result.scalars().all()

        services_data = [
            {
                "id": svc.id,
                "name": svc.name,
                "description": svc.description or "No description provided.",
                "pricing": svc.pricing or "Contact for quote",
                "target_clients": svc.target_clients or "General businesses",
                "portfolio_links": svc.portfolio_links or "None provided",
            }
            for svc in services
        ]

        return {
            "services": services_data,
            "services_count": len(services_data),
        }

    def _parse_and_validate_json(self, raw_text: str, schema_cls: Type[T]) -> T:
        """
        Cleans and validates AI output against a target Pydantic schema.
        Handles markdown code fences (```json ... ```) and minor formatting quirks.
        """
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            return schema_cls.model_validate(data)
        except json.JSONDecodeError as jde:
            logger.error(f"JSON decode failed on AI output: '{cleaned[:200]}...': {jde}")
            raise AIInvalidOutputError(f"AI returned invalid JSON: {jde}")
        except ValidationError as ve:
            logger.error(f"Pydantic schema validation failed on AI output: {ve}")
            raise AIInvalidOutputError(f"AI response did not match expected structure: {ve}")

    # -----------------------------------------------------------------------
    # 1. Lead Analysis
    # -----------------------------------------------------------------------
    async def analyze_lead(
        self,
        db: AsyncSession,
        user: User,
        request: LeadAnalysisRequest,
    ) -> LeadAnalysisResponse:
        """Analyzes a lead against the user's services stored in PostgreSQL."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        # If lead_id provided, fetch existing lead from DB to enrich context
        lead_name = request.lead_name
        lead_company = request.lead_company
        lead_description = request.lead_description
        lead_source = request.source
        lead_detected_need = request.detected_need

        if request.lead_id:
            lead_query = select(Lead).where(Lead.id == request.lead_id, Lead.user_id == user.id)
            lead_result = await db.execute(lead_query)
            lead_obj = lead_result.scalar_one_or_none()
            if lead_obj:
                lead_name = lead_name or lead_obj.name
                lead_company = lead_company or lead_obj.company
                lead_description = lead_description or lead_obj.description
                lead_source = lead_source or lead_obj.source
                lead_detected_need = lead_detected_need or lead_obj.detected_need

        # Load business context from PostgreSQL
        biz_context = await self.get_user_business_context(db, user.id)

        system_instruction = (
            "[OPERATION: analyze_lead] You are an expert AI sales and client-acquisition analyst for the Client Magnet SaaS platform. "
            "Your role is to strictly analyze prospective client opportunities and match them to the user's available services. "
            "Rules:\n"
            "1. DO NOT invent facts about the lead or user.\n"
            "2. If information is insufficient to ascertain specific needs, state that clearly.\n"
            "3. Always return valid JSON matching the exact required schema.\n"
            "4. Intent score must be a number between 0 and 100.\n"
            "5. Match against the provided user services strictly by name and ID if applicable."
        )

        prompt = f"""
Analyze the following prospective client lead:

Lead Details:
- Name: {lead_name or "Unknown"}
- Company: {lead_company or "Unknown"}
- Source: {lead_source or "Unspecified"}
- Lead Description / Context: {lead_description or "None provided"}
- Previously Detected Need: {lead_detected_need or "None"}
- Additional Context: {request.additional_context or "None"}

User's Available Services (from Database):
{json.dumps(biz_context["services"], indent=2)}

Required JSON Schema:
{{
  "detected_need": "string - specific service or problem the lead requires solved",
  "matched_service": "string or null - exact name of best matching service from user services",
  "matched_service_id": "string or null - exact ID of best matching service",
  "intent_score": number (0 to 100) - likelihood this lead is actively looking to hire a service provider,
  "reasoning_summary": "string - concise factual explanation of the analysis and intent score",
  "recommended_next_action": "string - tactical recommended next outreach or qualification step"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, LeadAnalysisResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "analyze_lead", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "analyze_lead", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 2. Service Matching
    # -----------------------------------------------------------------------
    async def match_service(
        self,
        db: AsyncSession,
        user: User,
        request: ServiceMatchRequest,
    ) -> ServiceMatchResponse:
        """Matches a project description to the user's PostgreSQL services."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        biz_context = await self.get_user_business_context(db, user.id)

        system_instruction = (
            "[OPERATION: match_service] You are a service matching engine. Match the client requirement strictly against the user's available services. "
            "Return valid JSON only."
        )

        prompt = f"""
Match this lead request to the user's available services:

Lead Description:
{request.lead_description}
Known Need: {request.lead_need or "None"}

Available User Services:
{json.dumps(biz_context["services"], indent=2)}

Required JSON Schema:
{{
  "matched_service": "string or null - matched service name",
  "matched_service_id": "string or null - matched service ID",
  "confidence": number (0.0 to 1.0) - confidence in this match,
  "match_reasoning": "string - clear explanation of why this service fits"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, ServiceMatchResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "match_service", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "match_service", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 3. Intent Scoring
    # -----------------------------------------------------------------------
    async def score_lead_intent(
        self,
        db: AsyncSession,
        user: User,
        request: IntentScoreRequest,
    ) -> IntentScoreResponse:
        """Estimates how likely a lead is to become a paying client (0 - 100)."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        system_instruction = (
            "[OPERATION: score_intent] You are an objective lead intent scoring model. Assess explicit request specificity, business context, "
            "urgency, and hiring readiness. Do not treat unrelated social chatter as qualified leads. Return valid JSON."
        )

        prompt = f"""
Calculate the client acquisition intent score for this lead:

Lead Context:
- Description: {request.lead_description}
- Stated Need: {request.lead_need or "None"}
- Source: {request.source or "Unspecified"}

Required JSON Schema:
{{
  "intent_score": number (0 to 100),
  "intent_level": "string ('Low', 'Medium', 'High', or 'Critical')",
  "scoring_factors": ["string - key factor 1", "string - key factor 2"],
  "reasoning": "string - concise rationale for intent score"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, IntentScoreResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "score_intent", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "score_intent", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 4. Social Caption Generation
    # -----------------------------------------------------------------------
    async def generate_caption(
        self,
        db: AsyncSession,
        user: User,
        request: CaptionGenerateRequest,
    ) -> CaptionGenerateResponse:
        """Generates engaging social media captions without copyright infringement."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        biz_context = await self.get_user_business_context(db, user.id)

        target_service = None
        if request.target_service_id:
            for s in biz_context["services"]:
                if s["id"] == request.target_service_id:
                    target_service = s
                    break

        system_instruction = (
            "[OPERATION: generate_caption] You are an organic social media marketing expert for B2B services and freelancers. "
            "Write engaging, authentic, platform-optimized captions. Do NOT generate copyrighted text or impersonate others. "
            "Return valid JSON only."
        )

        prompt = f"""
Generate a social media caption:

Target Platform: {request.platform}
Desired Tone: {request.desired_tone}
Content Topic / Takeaway: {request.content_description}
Specific CTA requested: {request.call_to_action or "None"}
Service Promoted: {json.dumps(target_service) if target_service else "General Agency Services"}

Required JSON Schema:
{{
  "caption": "string - the complete social post body",
  "hashtags": ["string - relevant hashtags starting with #"],
  "call_to_action": "string - explicit closing call to action"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, CaptionGenerateResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "generate_caption", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "generate_caption", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 5. Personalized Email Generation (Draft Only)
    # -----------------------------------------------------------------------
    async def generate_email_draft(
        self,
        db: AsyncSession,
        user: User,
        request: EmailDraftRequest,
    ) -> EmailDraftResponse:
        """Drafts a professional outreach email. Treated strictly as an advisory draft."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        lead_name = request.lead_name
        lead_company = request.lead_company
        lead_need = request.lead_need

        if request.lead_id:
            lead_query = select(Lead).where(Lead.id == request.lead_id, Lead.user_id == user.id)
            lead_res = await db.execute(lead_query)
            lead_obj = lead_res.scalar_one_or_none()
            if lead_obj:
                lead_name = lead_name or lead_obj.name
                lead_company = lead_company or lead_obj.company
                lead_need = lead_need or lead_obj.detected_need or lead_obj.description

        biz_context = await self.get_user_business_context(db, user.id)

        matched_service = None
        if request.matched_service_id:
            for s in biz_context["services"]:
                if s["id"] == request.matched_service_id:
                    matched_service = s
                    break

        system_instruction = (
            "[OPERATION: generate_email] You are an expert consultative outreach copywriter. "
            "Rules:\n"
            "1. Do NOT invent previous conversations, testimonials, fake case studies, or unprovided pricing.\n"
            "2. Keep the email concise, natural, and value-focused.\n"
            "3. Clearly indicate this is a draft for human review.\n"
            "4. Return valid JSON only."
        )

        prompt = f"""
Draft a personalized cold outreach email for this prospect:

Lead Information:
- Prospect Name: {lead_name or "Prospective Client"}
- Company: {lead_company or "your team"}
- Stated Need / Project: {lead_need or "digital services"}

Sender / User Context:
- Full Name: {user.full_name or "Consultant"}
- Company: {user.company_name or "Client Magnet Services"}
- Matched Service: {json.dumps(matched_service) if matched_service else "Custom Business Solutions"}
- Desired Tone: {request.desired_tone}
- Custom Instructions: {request.custom_instructions or "None"}

Required JSON Schema:
{{
  "subject": "string - compelling, professional email subject line",
  "body": "string - complete email body draft formatted cleanly with line breaks",
  "matched_service_name": "string or null - service name highlighted",
  "tone_used": "{request.desired_tone}"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, EmailDraftResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "generate_email", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "generate_email", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 6. Reply Suggestion
    # -----------------------------------------------------------------------
    async def suggest_reply(
        self,
        db: AsyncSession,
        user: User,
        request: ReplySuggestionRequest,
    ) -> ReplySuggestionResponse:
        """Suggests a professional reply to a client message."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        history_items = []
        if request.conversation_history:
            history_items = [
                f"{msg.sender}: {msg.message}" for msg in request.conversation_history
            ]
        elif request.conversation_id:
            # Load messages from database
            msgs_query = (
                select(Message)
                .where(Message.conversation_id == request.conversation_id)
                .order_by(Message.sent_at.asc())
            )
            msgs_res = await db.execute(msgs_query)
            db_msgs = msgs_res.scalars().all()
            history_items = [f"{m.sender}: {m.message_content}" for m in db_msgs]

        biz_context = await self.get_user_business_context(db, user.id)

        system_instruction = (
            "[OPERATION: suggest_reply] You are an AI communication assistant suggesting responses for human review. "
            "Be professional, accurate, and helpful. Do not promise deliverables or pricing not specified in the user's services. "
            "Return valid JSON only."
        )

        prompt = f"""
Suggest a response to the following client message:

Conversation History:
{chr(10).join(history_items) if history_items else "No prior history"}

Incoming Message to Respond To:
"{request.incoming_message}"

User Business Services & Context:
{json.dumps(biz_context["services"], indent=2)}

Preferred Style: {request.preferred_style}

Required JSON Schema:
{{
  "suggested_reply": "string - draft message response",
  "reasoning_summary": "string - brief rationale explaining why this response is suitable"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, ReplySuggestionResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "suggest_reply", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "suggest_reply", duration_ms, False, category)
            raise

    # -----------------------------------------------------------------------
    # 7. Conversation Summarization
    # -----------------------------------------------------------------------
    async def summarize_conversation(
        self,
        db: AsyncSession,
        user: User,
        request: ConversationSummaryRequest,
    ) -> ConversationSummaryResponse:
        """Summarizes a client conversation and suggests pipeline actions."""
        if not self._provider:
            raise AIConfigurationError("No AI provider configured.")

        self._check_rate_limit(user.id)
        start_time = time.time()

        transcript = request.conversation_text or ""
        if request.messages:
            transcript = "\n".join(
                [f"{msg.sender}: {msg.message}" for msg in request.messages]
            )
        elif request.conversation_id:
            msgs_query = (
                select(Message)
                .where(Message.conversation_id == request.conversation_id)
                .order_by(Message.sent_at.asc())
            )
            msgs_res = await db.execute(msgs_query)
            db_msgs = msgs_res.scalars().all()
            transcript = "\n".join([f"{m.sender}: {m.message_content}" for m in db_msgs])

        if not transcript.strip():
            transcript = "No conversation messages provided."

        system_instruction = (
            "[OPERATION: summarize_conversation] You are an executive CRM conversation summarizer. Extract factual needs, outstanding questions, "
            "next steps, and recommend a lead status. Return valid JSON only."
        )

        prompt = f"""
Summarize this conversation:

Transcript:
{transcript}

Required JSON Schema:
{{
  "summary": "string - concise factual summary",
  "client_needs": ["string - need 1", "string - need 2"],
  "questions": ["string - open question 1"],
  "next_action": "string - actionable next step for the user",
  "lead_status_suggestion": "string - one of (QUALIFIED, CONTACTED, REPLIED, INTERESTED, DISCOVERY, PROPOSAL, WON, LOST)"
}}
"""

        try:
            raw_text = await self._provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=True,
            )
            parsed = self._parse_and_validate_json(raw_text, ConversationSummaryResponse)
            duration_ms = (time.time() - start_time) * 1000
            await self._log_ai_request(db, user.id, "summarize_conversation", duration_ms, True)
            return parsed
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            category = getattr(e, "category", "UNKNOWN_ERROR")
            await self._log_ai_request(db, user.id, "summarize_conversation", duration_ms, False, category)
            raise


# ---------------------------------------------------------------------------
# Factory Helper
# ---------------------------------------------------------------------------

def get_ai_service(api_key: Optional[str] = None, use_mock: Optional[bool] = None) -> AIService:
    """Instantiates the appropriate AI provider (Gemini or Mock) within AIService."""
    effective_api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
    effective_use_mock = use_mock if use_mock is not None else settings.USE_MOCK_AI

    if effective_use_mock or not effective_api_key:
        logger.info("Configuring AIService with MockProvider.")
        return AIService(MockProvider())
    else:
        logger.info(f"Configuring AIService with GeminiProvider ({settings.GEMINI_MODEL_NAME}).")
        return AIService(
            GeminiProvider(
                api_key=effective_api_key,
                model_name=settings.GEMINI_MODEL_NAME,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                timeout=settings.AI_REQUEST_TIMEOUT,
                max_retries=settings.AI_MAX_RETRIES,
            )
        )
