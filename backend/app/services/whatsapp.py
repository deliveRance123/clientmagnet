import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.notification import Notification
from app.models.opt_out import OptOut
from app.models.user import User
from app.models.whatsapp import WhatsAppAccount
from app.schemas.ai import ReplySuggestionRequest
from app.schemas.whatsapp import (
    WhatsAppAccountCreate,
    WhatsAppAccountOut,
    WhatsAppSendRequest,
    WhatsAppSendResult,
)
from app.services.ai import AIService
from app.services.compliance import ComplianceService

logger = logging.getLogger("app.services.whatsapp")


class WhatsAppService:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        compliance_service: Optional[ComplianceService] = None,
        use_mock: Optional[bool] = None,
    ):
        self.ai_service = ai_service or AIService()
        self.compliance_service = compliance_service or ComplianceService()
        self.use_mock = use_mock if use_mock is not None else settings.USE_MOCK_WHATSAPP

    # -----------------------------------------------------------------------
    # 1. Account Management
    # -----------------------------------------------------------------------

    async def connect_account(
        self, db: AsyncSession, user: User, data: WhatsAppAccountCreate
    ) -> WhatsAppAccount:
        # Check if phone number already connected for this user
        stmt = select(WhatsAppAccount).where(
            WhatsAppAccount.user_id == user.id,
            WhatsAppAccount.phone_number == data.phone_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.phone_number_id = data.phone_number_id
            existing.business_account_id = data.business_account_id
            existing.display_name = data.display_name
            existing.connection_status = "CONNECTED"
            existing.credentials = {"access_token": data.access_token}
            if data.webhook_verify_token:
                existing.webhook_verify_token = data.webhook_verify_token
            account = existing
        else:
            account = WhatsAppAccount(
                user_id=user.id,
                phone_number_id=data.phone_number_id,
                phone_number=data.phone_number,
                business_account_id=data.business_account_id,
                display_name=data.display_name,
                connection_status="CONNECTED",
                webhook_verify_token=data.webhook_verify_token or settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
            )
            account.credentials = {"access_token": data.access_token}
            db.add(account)

        await db.commit()
        await db.refresh(account)
        return account

    async def get_user_accounts(
        self, db: AsyncSession, user_id: str
    ) -> List[WhatsAppAccount]:
        stmt = (
            select(WhatsAppAccount)
            .where(WhatsAppAccount.user_id == user_id)
            .order_by(WhatsAppAccount.created_at.desc())
        )
        return (await db.execute(stmt)).scalars().all()

    async def disconnect_account(
        self, db: AsyncSession, user: User, account_id: str
    ) -> WhatsAppAccount:
        stmt = select(WhatsAppAccount).where(
            WhatsAppAccount.id == account_id, WhatsAppAccount.user_id == user.id
        )
        account = (await db.execute(stmt)).scalar_one_or_none()
        if not account:
            raise ValueError("WhatsApp account not found.")

        account.connection_status = "DISCONNECTED"
        account.credentials = None
        await db.commit()
        await db.refresh(account)
        return account

    # -----------------------------------------------------------------------
    # 2. Webhook Verification & Processing
    # -----------------------------------------------------------------------

    def verify_webhook_challenge(
        self, mode: Optional[str], token: Optional[str], challenge: Optional[str]
    ) -> str:
        """Verify Meta Webhook setup challenge (hub.verify_token)."""
        expected_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        if mode == "subscribe" and token == expected_token and challenge:
            return challenge
        raise ValueError("Invalid webhook verification token or mode.")

    def validate_webhook_signature(
        self, signature_header: Optional[str], payload_bytes: bytes
    ) -> bool:
        """Validate Meta X-Hub-Signature-256 HMAC header against WHATSAPP_APP_SECRET."""
        if not settings.WHATSAPP_APP_SECRET:
            # In mock/dev mode without app secret, allow signature pass
            return True
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        received_hash = signature_header[7:]
        expected_hash = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(received_hash, expected_hash)

    async def process_incoming_webhook(
        self, db: AsyncSession, payload: Dict[str, Any]
    ) -> int:
        """Parse incoming Meta WhatsApp webhook event and persist to unified conversations."""
        entries = payload.get("entry", [])
        ingested_count = 0

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id")

                # Find WhatsApp account
                stmt = select(WhatsAppAccount).where(
                    WhatsAppAccount.phone_number_id == phone_number_id,
                    WhatsAppAccount.connection_status == "CONNECTED",
                )
                account = (await db.execute(stmt)).scalar_one_or_none()
                if not account:
                    logger.info(f"Incoming WhatsApp message for unregistered phone ID: {phone_number_id}")
                    continue

                user_id = account.user_id
                messages = value.get("messages", [])
                contacts = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}

                for msg in messages:
                    sender_wa_id = msg.get("from")
                    sender_name = contacts.get(sender_wa_id, sender_wa_id)
                    external_msg_id = msg.get("id")
                    text_body = ""

                    if msg.get("type") == "text":
                        text_body = msg.get("text", {}).get("body", "")
                    elif msg.get("type") == "button":
                        text_body = msg.get("button", {}).get("text", "")
                    elif msg.get("type") == "interactive":
                        text_body = msg.get("interactive", {}).get("list_reply", {}).get("title", "")
                    else:
                        text_body = f"[{msg.get('type', 'media')} message received]"

                    if not text_body:
                        continue

                    # 1. Match sender phone to Lead
                    clean_phone = f"+{sender_wa_id.lstrip('+')}"
                    lead_stmt = select(Lead).where(
                        Lead.user_id == user_id,
                        (Lead.phone == clean_phone) | (Lead.phone == sender_wa_id),
                    )
                    lead = (await db.execute(lead_stmt)).scalar_one_or_none()

                    # 2. Find or create unified conversation
                    conv_stmt = (
                        select(Conversation)
                        .where(
                            Conversation.user_id == user_id,
                            Conversation.platform == "whatsapp",
                            Conversation.external_conversation_id == sender_wa_id,
                        )
                    )
                    conv = (await db.execute(conv_stmt)).scalar_one_or_none()

                    now = datetime.now(timezone.utc)
                    if not conv:
                        conv = Conversation(
                            user_id=user_id,
                            lead_id=lead.id if lead else None,
                            platform="whatsapp",
                            subject=f"WhatsApp chat with {sender_name or clean_phone}",
                            external_conversation_id=sender_wa_id,
                            unread_count=1,
                            last_message_at=now,
                            status="ACTIVE",
                        )
                        db.add(conv)
                        await db.flush()
                    else:
                        conv.unread_count += 1
                        conv.last_message_at = now
                        if lead and not conv.lead_id:
                            conv.lead_id = lead.id

                    # 3. Store message
                    new_msg = Message(
                        conversation_id=conv.id,
                        sender=sender_wa_id,
                        recipient=account.phone_number,
                        message_content=text_body,
                        platform="whatsapp",
                        direction="inbound",
                        status="RECEIVED",
                        external_message_id=external_msg_id,
                        sent_at=now,
                    )
                    db.add(new_msg)

                    # 4. Advance lead status if applicable
                    if lead and lead.status in ("NEW", "CONTACTED"):
                        lead.status = "REPLIED"

                    # 5. Create In-App Notification
                    notif = Notification(
                        user_id=user_id,
                        title=f"New WhatsApp message from {sender_name or clean_phone}",
                        message=text_body[:120],
                        notification_type="LEAD_REPLY",
                        link_url=f"/messages?platform=whatsapp&conv={conv.id}",
                    )
                    db.add(notif)
                    ingested_count += 1

        await db.commit()
        return ingested_count

    # -----------------------------------------------------------------------
    # 3. Sending Approved WhatsApp Messages
    # -----------------------------------------------------------------------

    async def send_approved_message(
        self, db: AsyncSession, user: User, req: WhatsAppSendRequest
    ) -> WhatsAppSendResult:
        """Send explicit, human-approved WhatsApp message with opt-out & duplicate protection."""
        clean_phone = req.recipient_phone.strip().replace(" ", "").replace("-", "")

        # 1. Opt-Out Registry Check
        opt_stmt = select(OptOut).where(
            OptOut.user_id == user.id,
            OptOut.contact_identifier == clean_phone,
            OptOut.platform.in_(["whatsapp", "all", "WHATSAPP"]),
        )
        opt_out = (await db.execute(opt_stmt)).scalar_one_or_none()
        if opt_out:
            raise ValueError(
                f"Contact {clean_phone} has opted out of WhatsApp communication ({opt_out.reason or 'DO NOT CONTACT'})."
            )

        # 2. Pre-flight compliance check
        comp_res = await self.compliance_service.check_action(
            user_id=user.id,
            action_type="send_whatsapp",
            payload={"recipient": clean_phone, "body": req.message_text},
        )
        if not comp_res.get("allowed", True):
            raise ValueError(f"Compliance check rejected send: {comp_res.get('reason')}")

        # 3. Duplicate send prevention within 60s cooldown
        now = datetime.now(timezone.utc)
        dup_stmt = select(Message).where(
            Message.recipient == clean_phone,
            Message.platform == "whatsapp",
            Message.direction == "outbound",
            Message.message_content == req.message_text.strip(),
        ).order_by(Message.sent_at.desc()).limit(1)
        recent_dup = (await db.execute(dup_stmt)).scalar_one_or_none()

        if recent_dup:
            sent_at = recent_dup.sent_at
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
            diff = (now - sent_at).total_seconds()
            if diff < 60:
                raise ValueError("Duplicate message detected: A very similar message was sent to this phone number within the last 60 seconds.")

        # 4. Get active WhatsApp account
        acc_stmt = select(WhatsAppAccount).where(
            WhatsAppAccount.user_id == user.id,
            WhatsAppAccount.connection_status == "CONNECTED",
        )
        account = (await db.execute(acc_stmt)).scalar_one_or_none()

        if not account and not self.use_mock:
            raise ValueError("No connected WhatsApp Business account. Please connect your phone number ID in WhatsApp settings.")

        # 5. Dispatch via Meta Cloud API
        external_id = f"wamid_mock_{int(now.timestamp())}"
        if not self.use_mock and account:
            creds = account.credentials or {}
            access_token = creds.get("access_token")
            api_url = f"{settings.WHATSAPP_API_URL}/{account.phone_number_id}/messages"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            body = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone.lstrip("+"),
                "type": "text",
                "text": {"preview_url": False, "body": req.message_text},
            }

            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(api_url, json=body, headers=headers)
                res.raise_for_status()
                res_data = res.json()
                external_id = res_data.get("messages", [{}])[0].get("id", external_id)

        # 6. Find or create unified conversation
        conv_id = req.conversation_id
        if conv_id:
            conv = (await db.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one_or_none()
        else:
            conv_stmt = select(Conversation).where(
                Conversation.user_id == user.id,
                Conversation.platform == "whatsapp",
                Conversation.external_conversation_id == clean_phone,
            )
            conv = (await db.execute(conv_stmt)).scalar_one_or_none()

        if not conv:
            conv = Conversation(
                user_id=user.id,
                lead_id=req.lead_id,
                platform="whatsapp",
                subject=f"WhatsApp: {clean_phone}",
                external_conversation_id=clean_phone,
                unread_count=0,
                last_message_at=now,
                status="ACTIVE",
            )
            db.add(conv)
            await db.flush()
        else:
            conv.last_message_at = now
            if req.lead_id and not conv.lead_id:
                conv.lead_id = req.lead_id

        # 7. Record outbound message
        msg = Message(
            conversation_id=conv.id,
            sender=account.phone_number if account else "WhatsAppBusiness",
            recipient=clean_phone,
            message_content=req.message_text,
            platform="whatsapp",
            direction="outbound",
            status="SENT",
            external_message_id=external_id,
            sent_at=now,
        )
        db.add(msg)

        # 8. Advance lead status if applicable
        if req.lead_id:
            lead = (await db.execute(select(Lead).where(Lead.id == req.lead_id))).scalar_one_or_none()
            if lead and lead.status == "NEW":
                lead.status = "CONTACTED"

        await db.commit()
        await db.refresh(msg)

        return WhatsAppSendResult(
            message_id=msg.id,
            conversation_id=conv.id,
            status="SENT",
            recipient_phone=clean_phone,
            external_message_id=external_id,
            sent_at=now,
            message="WhatsApp message successfully dispatched.",
        )

    # -----------------------------------------------------------------------
    # 4. AI Suggested Replies (Gemini)
    # -----------------------------------------------------------------------

    async def suggest_reply(
        self, db: AsyncSession, user: User, conversation_id: str
    ) -> str:
        """Generate a contextual suggested reply with Gemini based on thread history."""
        conv_stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages), selectinload(Conversation.lead))
            .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        )
        conv = (await db.execute(conv_stmt)).scalar_one_or_none()
        if not conv:
            raise ValueError("Conversation not found.")

        # Extract last few messages
        history_snippet = "\n".join(
            [f"{m.direction.upper()} ({m.sender}): {m.message_content}" for m in conv.messages[-5:]]
        )

        reply_res = await self.ai_service.suggest_reply(
            ReplySuggestionRequest(
                incoming_message=history_snippet or "Hello, I'd like more details on your services.",
                lead_context=conv.lead.detected_need if conv.lead else "Website and automation development inquiry",
                channel="whatsapp",
                desired_tone=user.preferred_tone or "Professional, concise, and helpful",
            ),
            user_id=user.id,
        )
        return reply_res.suggested_reply
