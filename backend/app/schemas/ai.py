from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Lead Analysis Schemas
# ---------------------------------------------------------------------------

class LeadAnalysisRequest(BaseModel):
    lead_id: Optional[str] = Field(None, description="Optional ID of lead stored in database")
    lead_name: Optional[str] = Field(None, description="Name of the lead/prospect")
    lead_company: Optional[str] = Field(None, description="Company name")
    lead_description: Optional[str] = Field(None, description="Project context, inquiry text, or bio")
    source: Optional[str] = Field(None, description="Source platform e.g. Upwork, LinkedIn")
    detected_need: Optional[str] = Field(None, description="Previously noted need, if any")
    additional_context: Optional[str] = Field(None, description="Extra background or instructions")


class LeadAnalysisResponse(BaseModel):
    detected_need: str = Field(..., description="Identified service or business need")
    matched_service: Optional[str] = Field(None, description="Name of user's service that best matches")
    matched_service_id: Optional[str] = Field(None, description="Database ID of the matched service")
    intent_score: float = Field(..., ge=0, le=100, description="Purchase/engagement intent score (0-100)")
    reasoning_summary: str = Field(..., description="Summary explaining the analysis and intent score")
    recommended_next_action: str = Field(..., description="Actionable next step for user outreach")


# ---------------------------------------------------------------------------
# 2. Service Matching Schemas
# ---------------------------------------------------------------------------

class ServiceMatchRequest(BaseModel):
    lead_id: Optional[str] = None
    lead_description: str = Field(..., description="Inquiry description or project post")
    lead_need: Optional[str] = Field(None, description="Known requirements")


class ServiceMatchResponse(BaseModel):
    matched_service: Optional[str] = Field(None, description="Best matching service name")
    matched_service_id: Optional[str] = Field(None, description="Best matching service ID")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 - 1.0)")
    match_reasoning: str = Field(..., description="Why this service fits the lead requirements")


# ---------------------------------------------------------------------------
# 3. Intent Scoring Schemas
# ---------------------------------------------------------------------------

class IntentScoreRequest(BaseModel):
    lead_id: Optional[str] = None
    lead_description: str = Field(..., description="Inquiry text or communication")
    lead_need: Optional[str] = None
    source: Optional[str] = None


class IntentScoreResponse(BaseModel):
    intent_score: float = Field(..., ge=0, le=100, description="Intent score (0-100)")
    intent_level: str = Field(..., description="'Low', 'Medium', 'High', or 'Critical'")
    scoring_factors: List[str] = Field(default_factory=list, description="Key factors determining score")
    reasoning: str = Field(..., description="Explanation of intent estimation")


# ---------------------------------------------------------------------------
# 4. Social Caption Generation Schemas
# ---------------------------------------------------------------------------

class CaptionGenerateRequest(BaseModel):
    content_description: str = Field(..., description="Topic, key takeaway, or post idea")
    platform: str = Field("LinkedIn", description="Target platform (LinkedIn, Twitter/X, Instagram, Facebook, TikTok)")
    desired_tone: str = Field("Professional", description="Tone (Professional, Casual, Persuasive, Educational, Inspirational)")
    call_to_action: Optional[str] = Field(None, description="Specific CTA to include")
    target_service_id: Optional[str] = Field(None, description="Optional service ID to promote")


class CaptionGenerateResponse(BaseModel):
    caption: str = Field(..., description="The generated social media post body")
    hashtags: List[str] = Field(default_factory=list, description="Relevant hashtags")
    call_to_action: str = Field(..., description="Call to action included in the caption")


# ---------------------------------------------------------------------------
# 5. Personalized Email Draft Schemas
# ---------------------------------------------------------------------------

class EmailDraftRequest(BaseModel):
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    lead_company: Optional[str] = None
    lead_need: Optional[str] = None
    matched_service_id: Optional[str] = None
    desired_tone: str = Field("Professional", description="Tone (Professional, Warm & Consultative, Direct & Concise, Enthusiastic)")
    custom_instructions: Optional[str] = None


class EmailDraftResponse(BaseModel):
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email draft body")
    matched_service_name: Optional[str] = Field(None, description="Service referenced in the pitch")
    tone_used: str = Field(..., description="Tone applied")


# ---------------------------------------------------------------------------
# 6. Reply Suggestion Schemas
# ---------------------------------------------------------------------------

class ChatMessageItem(BaseModel):
    sender: str
    message: str
    timestamp: Optional[str] = None


class ReplySuggestionRequest(BaseModel):
    conversation_id: Optional[str] = None
    incoming_message: str = Field(..., description="The message requiring a response")
    conversation_history: Optional[List[ChatMessageItem]] = Field(
        default=None, description="Prior message history for context"
    )
    preferred_style: str = Field(
        "Professional & Helpful", description="Preferred response style"
    )


class ReplySuggestionResponse(BaseModel):
    suggested_reply: str = Field(..., description="Draft response ready for human review")
    reasoning_summary: str = Field(..., description="Why this response is appropriate")


# ---------------------------------------------------------------------------
# 7. Conversation Summarization Schemas
# ---------------------------------------------------------------------------

class ConversationSummaryRequest(BaseModel):
    conversation_id: Optional[str] = None
    messages: Optional[List[ChatMessageItem]] = None
    conversation_text: Optional[str] = Field(
        None, description="Raw conversation transcript if messages list is not structured"
    )


class ConversationSummaryResponse(BaseModel):
    summary: str = Field(..., description="Concise summary of conversation")
    client_needs: List[str] = Field(default_factory=list, description="Client requirements extracted")
    questions: List[str] = Field(default_factory=list, description="Unanswered questions or open points")
    next_action: str = Field(..., description="Suggested immediate next action")
    lead_status_suggestion: str = Field(
        ..., description="Recommended pipeline status (e.g. QUALIFIED, CONTACTED, REPLIED, INTERESTED, DISCOVERY, PROPOSAL, LOST)"
    )
