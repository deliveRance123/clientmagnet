import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.follow_up import FollowUp
from app.models.lead import Lead
from app.models.message import Message
from app.models.notification import Notification
from app.models.opt_out import OptOut
from app.models.user import User
from app.schemas.ai import ConversationSummaryRequest, ReplySuggestionRequest
from app.schemas.unified_inbox import (
    FollowUpCreate,
    FollowUpOut,
    FollowUpUpdate,
    NotificationOut,
    NotificationSummary,
    SuggestedReplyResponse,
    UnifiedConversationLeadInfo,
    UnifiedConversationOut,
    UnifiedConversationSummaryResponse,
    UnifiedMessageOut,
    UserCommunicationPreferencesOut,
    UserCommunicationPreferencesUpdate,
)
from app.services.ai import AIService
from app.services.compliance import ComplianceService

logger = logging.getLogger("app.services.unified_inbox")


class UnifiedInboxService:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        compliance_service: Optional[ComplianceService] = None,
    ):
        self.ai_service = ai_service or AIService()
        self.compliance_service = compliance_service or ComplianceService()

    # -----------------------------------------------------------------------
    # 1. Unified Cross-Platform Inbox
    # -----------------------------------------------------------------------

    async def list_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        platform_filter: Optional[str] = None,
        lead_status_filter: Optional[str] = None,
        unread_only: bool = False,
        search_query: Optional[str] = None,
    ) -> List[UnifiedConversationOut]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.lead).selectinload(Lead.matched_service),
                selectinload(Conversation.messages),
            )
            .where(Conversation.user_id == user_id)
        )

        if platform_filter and platform_filter.lower() != "all":
            stmt = stmt.where(Conversation.platform == platform_filter.lower())

        if unread_only:
            stmt = stmt.where(Conversation.unread_count > 0)

        if search_query:
            q = f"%{search_query.strip()}%"
            stmt = stmt.where(
                (Conversation.subject.ilike(q))
                | (Conversation.external_conversation_id.ilike(q))
            )

        stmt = stmt.order_by(Conversation.last_message_at.desc().nullslast())
        convs = (await db.execute(stmt)).scalars().all()

        results: List[UnifiedConversationOut] = []
        for c in convs:
            if lead_status_filter and (not c.lead or c.lead.status != lead_status_filter):
                continue

            lead_info = None
            if c.lead:
                matched_svc_name = None
                try:
                    state = instance_state(c.lead)
                    if "matched_service" in state.dict and state.dict["matched_service"] is not None:
                        matched_svc_name = state.dict["matched_service"].name
                except Exception:
                    pass

                lead_info = UnifiedConversationLeadInfo(
                    id=c.lead.id,
                    name=c.lead.name,
                    company=c.lead.company,
                    email=c.lead.email,
                    phone=c.lead.phone,
                    status=c.lead.status,
                    detected_need=c.lead.detected_need,
                    matched_service_name=matched_svc_name,
                )

            msgs = [UnifiedMessageOut.from_orm_message(m) for m in c.messages]
            results.append(
                UnifiedConversationOut(
                    id=c.id,
                    user_id=c.user_id,
                    lead_id=c.lead_id,
                    platform=c.platform,
                    subject=c.subject,
                    external_conversation_id=c.external_conversation_id,
                    status=c.status,
                    unread_count=c.unread_count,
                    last_message_at=c.last_message_at,
                    lead=lead_info,
                    messages=msgs,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return results

    async def get_conversation_thread(
        self, db: AsyncSession, user_id: str, conversation_id: str
    ) -> Optional[UnifiedConversationOut]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.lead).selectinload(Lead.matched_service),
                selectinload(Conversation.messages),
            )
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        c = (await db.execute(stmt)).scalar_one_or_none()
        if not c:
            return None

        # Mark as read without expiring loaded relations
        if c.unread_count > 0:
            c.unread_count = 0
            await db.flush()

        lead_info = None
        if c.lead:
            matched_svc_name = None
            try:
                state = instance_state(c.lead)
                if "matched_service" in state.dict and state.dict["matched_service"] is not None:
                    matched_svc_name = state.dict["matched_service"].name
            except Exception:
                pass

            lead_info = UnifiedConversationLeadInfo(
                id=c.lead.id,
                name=c.lead.name,
                company=c.lead.company,
                email=c.lead.email,
                phone=c.lead.phone,
                status=c.lead.status,
                detected_need=c.lead.detected_need,
                matched_service_name=matched_svc_name,
            )

        return UnifiedConversationOut(
            id=c.id,
            user_id=c.user_id,
            lead_id=c.lead_id,
            platform=c.platform,
            subject=c.subject,
            external_conversation_id=c.external_conversation_id,
            status=c.status,
            unread_count=c.unread_count,
            last_message_at=c.last_message_at,
            lead=lead_info,
            messages=[UnifiedMessageOut.from_orm_message(m) for m in c.messages],
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    # -----------------------------------------------------------------------
    # 2. Conversation Intelligence (Gemini AI)
    # -----------------------------------------------------------------------

    async def summarize_conversation(
        self, db: AsyncSession, user: User, conversation_id: str
    ) -> UnifiedConversationSummaryResponse:
        thread = await self.get_conversation_thread(db, user.id, conversation_id)
        if not thread:
            raise ValueError("Conversation not found.")

        history_text = "\n".join(
            [f"{m.direction.upper()} ({m.sender}): {m.message_content}" for m in thread.messages]
        )

        ai_summary = await self.ai_service.summarize_conversation(
            db=db,
            user=user,
            request=ConversationSummaryRequest(
                conversation_id=conversation_id,
                conversation_text=history_text or "No messages recorded yet.",
            ),
        )

        return UnifiedConversationSummaryResponse(
            conversation_id=conversation_id,
            summary=ai_summary.summary,
            client_needs=ai_summary.client_needs,
            questions=ai_summary.questions,
            objections=[],
            next_action=ai_summary.next_action,
            lead_status_suggestion=ai_summary.lead_status_suggestion,
        )

    async def suggest_reply(
        self, db: AsyncSession, user: User, conversation_id: str
    ) -> SuggestedReplyResponse:
        thread = await self.get_conversation_thread(db, user.id, conversation_id)
        if not thread:
            raise ValueError("Conversation not found.")

        last_msg = thread.messages[-1].message_content if thread.messages else "Inquiry regarding your available services"

        ai_res = await self.ai_service.suggest_reply(
            db=db,
            user=user,
            request=ReplySuggestionRequest(
                conversation_id=conversation_id,
                incoming_message=last_msg,
                preferred_style=user.preferred_tone or "Professional & Consultative",
            ),
        )

        return SuggestedReplyResponse(
            conversation_id=conversation_id,
            suggested_reply=ai_res.suggested_reply,
            rationale=ai_res.reasoning_summary,
            platform=thread.platform,
        )

    # -----------------------------------------------------------------------
    # 3. Lead Communication Timeline
    # -----------------------------------------------------------------------

    async def get_lead_timeline(
        self, db: AsyncSession, user_id: str, lead_id: str
    ) -> List[Dict[str, Any]]:
        lead_stmt = select(Lead).where(Lead.id == lead_id, Lead.user_id == user_id)
        lead = (await db.execute(lead_stmt)).scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found.")

        events: List[Dict[str, Any]] = []

        # 1. Lead Created
        events.append(
            {
                "event_type": "LEAD_CREATED",
                "title": "Lead Discovered & Ingested",
                "description": f"Lead {lead.name} added to pipeline (Matched: {lead.matched_service_id or 'General'})",
                "timestamp": lead.created_at.isoformat(),
                "channel": "system",
            }
        )

        # 2. Conversations & Messages
        convs_stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.lead_id == lead_id, Conversation.user_id == user_id)
        )
        convs = (await db.execute(convs_stmt)).scalars().all()

        for c in convs:
            for m in c.messages:
                events.append(
                    {
                        "event_type": "MESSAGE_SENT" if m.direction == "outbound" else "MESSAGE_RECEIVED",
                        "title": f"{'Outbound' if m.direction == 'outbound' else 'Inbound'} {c.platform.title()} Message",
                        "description": m.message_content,
                        "timestamp": m.sent_at.isoformat(),
                        "channel": c.platform,
                        "status": m.status,
                        "sender": m.sender,
                        "recipient": m.recipient,
                    }
                )

        # 3. Follow-Ups
        fu_stmt = select(FollowUp).where(FollowUp.lead_id == lead_id, FollowUp.user_id == user_id)
        follow_ups = (await db.execute(fu_stmt)).scalars().all()
        for fu in follow_ups:
            events.append(
                {
                    "event_type": "FOLLOW_UP",
                    "title": f"Follow-Up ({fu.status}) on {fu.channel.title()}",
                    "description": fu.notes or fu.message_draft or "Scheduled touchpoint",
                    "timestamp": fu.scheduled_time.isoformat(),
                    "channel": fu.channel,
                    "status": fu.status,
                }
            )

        # Sort chronologically descending
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events

    # -----------------------------------------------------------------------
    # 4. Follow-Up Management System
    # -----------------------------------------------------------------------

    async def create_follow_up(
        self, db: AsyncSession, user: User, data: FollowUpCreate
    ) -> FollowUp:
        fu = FollowUp(
            user_id=user.id,
            lead_id=data.lead_id,
            conversation_id=data.conversation_id,
            channel=data.channel.lower(),
            scheduled_time=data.scheduled_time,
            status="Pending",
            notes=data.notes,
            message_draft=data.message_draft,
        )
        db.add(fu)
        await db.commit()
        await db.refresh(fu)
        return fu

    async def list_follow_ups(
        self,
        db: AsyncSession,
        user_id: str,
        status_filter: Optional[str] = None,
        due_filter: Optional[str] = None,
    ) -> List[FollowUpOut]:
        stmt = (
            select(FollowUp)
            .options(selectinload(FollowUp.lead))
            .where(FollowUp.user_id == user_id)
        )

        now = datetime.now(timezone.utc)
        if status_filter:
            stmt = stmt.where(FollowUp.status == status_filter)

        if due_filter == "due_today":
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            stmt = stmt.where(
                FollowUp.scheduled_time >= today_start,
                FollowUp.scheduled_time < today_end,
                FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
            )
        elif due_filter == "overdue":
            stmt = stmt.where(
                FollowUp.scheduled_time < now,
                FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
            )
        elif due_filter == "upcoming":
            stmt = stmt.where(
                FollowUp.scheduled_time >= now,
                FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
            )

        stmt = stmt.order_by(FollowUp.scheduled_time.asc())
        items = (await db.execute(stmt)).scalars().all()
        return [FollowUpOut.from_orm_followup(f) for f in items]

    async def update_follow_up(
        self, db: AsyncSession, user: User, follow_up_id: str, data: FollowUpUpdate
    ) -> FollowUpOut:
        stmt = (
            select(FollowUp)
            .options(selectinload(FollowUp.lead))
            .where(FollowUp.id == follow_up_id, FollowUp.user_id == user.id)
        )
        fu = (await db.execute(stmt)).scalar_one_or_none()
        if not fu:
            raise ValueError("Follow-up not found.")

        if data.scheduled_time is not None:
            fu.scheduled_time = data.scheduled_time
        if data.channel is not None:
            fu.channel = data.channel.lower()
        if data.notes is not None:
            fu.notes = data.notes
        if data.message_draft is not None:
            fu.message_draft = data.message_draft
        if data.status is not None:
            fu.status = data.status
            if data.status == "Sent":
                fu.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(fu)
        return FollowUpOut.from_orm_followup(fu)

    async def recommend_ai_follow_ups(self, db: AsyncSession, user: User) -> int:
        """Scan inactive leads without reply > 3 days and generate recommended follow-up drafts."""
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)

        # Inactive leads contacted but not replied
        stmt = (
            select(Lead)
            .where(
                Lead.user_id == user.id,
                Lead.status == "CONTACTED",
                Lead.updated_at < three_days_ago,
            )
        )
        inactive_leads = (await db.execute(stmt)).scalars().all()
        created_count = 0

        for lead in inactive_leads:
            # Check if pending follow-up already exists
            fu_check = select(FollowUp).where(
                FollowUp.lead_id == lead.id,
                FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
            )
            if (await db.execute(fu_check)).scalar_one_or_none():
                continue

            rec_fu = FollowUp(
                user_id=user.id,
                lead_id=lead.id,
                channel="email" if lead.email else "whatsapp",
                scheduled_time=now + timedelta(days=1),
                status="Pending",
                notes="Recommended follow-up: No response in 3+ days.",
                message_draft=f"Hi {lead.name}, following up on my previous message regarding {lead.detected_need or 'our services'}. Would you have 5 minutes to connect this week?",
                recommended_by_ai=True,
            )
            db.add(rec_fu)
            created_count += 1

        if created_count > 0:
            notif = Notification(
                user_id=user.id,
                title="Follow-Up Recommendations Ready",
                message=f"Gemini identified {created_count} leads ready for a timely follow-up check-in.",
                notification_type="FOLLOW_UP_DUE",
                link_url="/follow-ups",
            )
            db.add(notif)

        await db.commit()
        return created_count

    # -----------------------------------------------------------------------
    # 5. In-App Notifications
    # -----------------------------------------------------------------------

    async def get_notifications(
        self, db: AsyncSession, user_id: str, unread_only: bool = False
    ) -> NotificationSummary:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(50)
        items = (await db.execute(stmt)).scalars().all()

        unread_count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
        unread_count = (await db.execute(unread_count_stmt)).scalar() or 0

        return NotificationSummary(
            unread_count=unread_count,
            notifications=[NotificationOut.from_orm_notification(n) for n in items],
        )

    async def mark_notification_read(
        self, db: AsyncSession, user_id: str, notification_id: str
    ) -> bool:
        stmt = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        notif = (await db.execute(stmt)).scalar_one_or_none()
        if notif:
            notif.is_read = True
            await db.commit()
        return True

    async def mark_all_notifications_read(self, db: AsyncSession, user_id: str) -> bool:
        stmt = select(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
        items = (await db.execute(stmt)).scalars().all()
        for item in items:
            item.is_read = True
        await db.commit()
        return True

    # -----------------------------------------------------------------------
    # 6. User Communication Preferences
    # -----------------------------------------------------------------------

    async def get_preferences(self, user: User) -> UserCommunicationPreferencesOut:
        return UserCommunicationPreferencesOut(
            preferred_tone=user.preferred_tone,
            default_signature=user.default_signature,
            business_intro=user.business_intro,
            preferred_cta=user.preferred_cta,
        )

    async def update_preferences(
        self, db: AsyncSession, user: User, data: UserCommunicationPreferencesUpdate
    ) -> UserCommunicationPreferencesOut:
        if data.preferred_tone is not None:
            user.preferred_tone = data.preferred_tone
        if data.default_signature is not None:
            user.default_signature = data.default_signature
        if data.business_intro is not None:
            user.business_intro = data.business_intro
        if data.preferred_cta is not None:
            user.preferred_cta = data.preferred_cta

        await db.commit()
        await db.refresh(user)
        return await self.get_preferences(user)
