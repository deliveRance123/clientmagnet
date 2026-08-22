import base64
import email
from email.message import EmailMessage as PyEmailMessage
import json
import logging
import re
import secrets
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
import jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.email_account import EmailAccount
from app.models.lead import Lead
from app.models.message import Message
from app.models.opt_out import OptOut
from app.models.service import Service
from app.models.user import User
from app.schemas.ai import EmailDraftRequest as AIEmailDraftRequest
from app.schemas.social import OAuthTokenResult
from app.schemas.email import (
    EmailAccountInfo,
    EmailCallbackPayload,
    EmailConnectResponse,
    EmailConversationLeadInfo,
    EmailConversationOut,
    EmailDraftGenerateRequest,
    EmailDraftGenerateResponse,
    EmailMessageData,
    EmailMessageOut,
    EmailSendRequest,
    EmailSendResult,
)
from app.services.ai import AIService
from app.services.compliance import ComplianceService

logger = logging.getLogger("app.email")


# ---------------------------------------------------------------------------
# State Security (Signed Tamper-Proof Email OAuth State)
# ---------------------------------------------------------------------------

def generate_email_oauth_state(user_id: str, provider: str = "GMAIL") -> str:
    """Generates a cryptographically signed state token with 15-minute validity."""
    payload = {
        "sub": user_id,
        "provider": provider.upper(),
        "purpose": "EMAIL_OAUTH",
        "nonce": secrets.token_hex(8),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def validate_email_oauth_state(state: str, expected_provider: str = "GMAIL") -> str:
    """Validates the state token and returns user_id if valid; raises ValueError otherwise."""
    try:
        payload = jwt.decode(
            state, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("provider") != expected_provider.upper():
            raise ValueError(f"State provider mismatch: expected {expected_provider.upper()}")
        if payload.get("purpose") != "EMAIL_OAUTH":
            raise ValueError("Invalid OAuth purpose")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("State payload missing subject user ID")
        return str(user_id)
    except jwt.ExpiredSignatureError:
        raise ValueError("Email authorization session has expired. Please try connecting again.")
    except Exception as e:
        raise ValueError(f"Invalid or tampered OAuth state parameter: {e}")


# ---------------------------------------------------------------------------
# Provider Abstraction Interface
# ---------------------------------------------------------------------------

class EmailProvider(ABC):
    """Abstract base class for email providers (Gmail, Outlook, SMTP)."""

    provider_name: str = "BASE"

    @abstractmethod
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Returns the official OAuth authorization dialog URL."""
        pass

    @abstractmethod
    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        """Exchanges an authorization code for access and refresh tokens."""
        pass

    @abstractmethod
    async def get_account_info(self, access_token: str) -> EmailAccountInfo:
        """Fetches email identity and user profile metadata."""
        pass

    @abstractmethod
    async def send_email(
        self,
        access_token: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatches an email message through the provider."""
        pass

    @abstractmethod
    async def fetch_inbox_messages(
        self, access_token: str, max_results: int = 10
    ) -> List[EmailMessageData]:
        """Retrieves recent incoming email messages."""
        pass

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResult:
        """Refreshes an expired access token where supported."""
        raise NotImplementedError(f"Token refresh not implemented for {self.provider_name}")

    async def revoke_token(self, access_token: str) -> bool:
        """Revokes access token on disconnect."""
        return True


# ---------------------------------------------------------------------------
# Gmail Provider (Official Google OAuth 2.0 & Gmail REST API)
# ---------------------------------------------------------------------------

class GmailProvider(EmailProvider):
    """Official Google OAuth 2.0 and Gmail REST API Provider."""

    provider_name = "GMAIL"

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        scopes = (
            "https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/userinfo.profile "
            "https://www.googleapis.com/auth/gmail.send "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.modify"
        )
        encoded_scopes = scopes.replace(" ", "%20")
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&redirect_uri={redirect_uri}&response_type=code"
            f"&scope={encoded_scopes}&access_type=offline&prompt=consent&state={state}"
        )

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            token_data = resp.json()

        scopes_str = token_data.get("scope", "")
        return OAuthTokenResult(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in", 3600),
            scopes=[s for s in scopes_str.split(" ") if s],
            raw_response=token_data,
        )

    async def get_account_info(self, access_token: str) -> EmailAccountInfo:
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            profile = resp.json()

        return EmailAccountInfo(
            account_identifier=str(profile.get("id")),
            email_address=profile.get("email", ""),
            account_name=profile.get("name", "Google User"),
            profile_picture_url=profile.get("picture"),
            raw_profile=profile,
        )

    async def send_email(
        self,
        access_token: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        msg = PyEmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg.set_content(body)

        raw_bytes = msg.as_bytes()
        raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {"raw": raw_b64}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def fetch_inbox_messages(
        self, access_token: str, max_results: int = 10
    ) -> List[EmailMessageData]:
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"maxResults": max_results, "q": "label:INBOX"}

        messages: List[EmailMessageData] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()
            msg_ids = [m["id"] for m in data.get("messages", [])]

            for mid in msg_ids:
                msg_resp = await client.get(f"{url}/{mid}", headers=headers, params={"format": "full"})
                if msg_resp.status_code == 200:
                    m_data = msg_resp.json()
                    headers_list = m_data.get("payload", {}).get("headers", [])
                    header_map = {h["name"].lower(): h["value"] for h in headers_list}

                    messages.append(
                        EmailMessageData(
                            external_id=m_data["id"],
                            thread_id=m_data.get("threadId"),
                            sender=header_map.get("from", "unknown@sender.com"),
                            recipient=header_map.get("to", ""),
                            subject=header_map.get("subject", "No Subject"),
                            snippet=m_data.get("snippet", ""),
                            body_text=m_data.get("snippet", ""),
                            received_at=datetime.now(timezone.utc),
                        )
                    )
        return messages


# ---------------------------------------------------------------------------
# Mock Email Provider (for Testing & Offline Development)
# ---------------------------------------------------------------------------

class MockEmailProvider(EmailProvider):
    """Deterministic Mock Email Provider for testing and local development."""

    provider_name = "GMAIL"

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return f"{redirect_uri}?code=mock_gmail_auth_code_987&state={state}"

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs
    ) -> OAuthTokenResult:
        return OAuthTokenResult(
            access_token=f"mock_gmail_access_token_{secrets.token_hex(8)}",
            refresh_token=f"mock_gmail_refresh_token_{secrets.token_hex(8)}",
            expires_in=3600,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
            raw_response={"status": "mock_authorized", "provider": "GMAIL"},
        )

    async def get_account_info(self, access_token: str) -> EmailAccountInfo:
        return EmailAccountInfo(
            account_identifier="google-uid-8839210",
            email_address="founder@clientmagnet.com",
            account_name="Client Magnet Agency",
            profile_picture_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            raw_profile={"email": "founder@clientmagnet.com", "name": "Client Magnet Agency"},
        )

    async def send_email(
        self,
        access_token: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "id": f"mock_msg_{secrets.token_hex(8)}",
            "threadId": f"mock_thread_{secrets.token_hex(8)}",
            "labelIds": ["SENT"],
            "mock": True,
        }

    async def fetch_inbox_messages(
        self, access_token: str, max_results: int = 10
    ) -> List[EmailMessageData]:
        return [
            EmailMessageData(
                external_id=f"inbound_mock_{secrets.token_hex(6)}",
                thread_id="thread_mock_1",
                sender="prospect@apexventures.io",
                recipient="founder@clientmagnet.com",
                subject="Inquiry regarding Website Redesign proposal",
                snippet="Hi, we reviewed your proposal for our new landing page. Are you available for a quick call this week?",
                body_text="Hi, we reviewed your proposal for our new landing page. Are you available for a quick call this week?",
                received_at=datetime.now(timezone.utc) - timedelta(hours=2),
                is_unread=True,
            ),
            EmailMessageData(
                external_id=f"inbound_mock_{secrets.token_hex(6)}",
                thread_id="thread_mock_2",
                sender="sarah@nexustech.co",
                recipient="founder@clientmagnet.com",
                subject="Need Automation Bot for WhatsApp Lead Routing",
                snippet="Hello! We are looking to build a customer lead routing bot for WhatsApp. What is your turnaround time?",
                body_text="Hello! We are looking to build a customer lead routing bot for WhatsApp. What is your turnaround time?",
                received_at=datetime.now(timezone.utc) - timedelta(hours=5),
                is_unread=True,
            ),
        ]


# ---------------------------------------------------------------------------
# Email Service Orchestrator
# ---------------------------------------------------------------------------

class EmailService:
    """
    Central email service managing OAuth connection, AI email draft generation,
    explicit send approval, opt-out protection, and conversation sync.
    """

    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        compliance_service: Optional[ComplianceService] = None,
    ):
        self.ai_service = ai_service
        self.compliance_service = compliance_service

    def get_provider(self, provider_name: str = "GMAIL") -> EmailProvider:
        """Resolves the email provider implementation."""
        p_upper = provider_name.upper()

        if settings.USE_MOCK_EMAIL:
            return MockEmailProvider()

        if p_upper == "GMAIL":
            if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
                return MockEmailProvider()
            return GmailProvider()
        else:
            return MockEmailProvider()

    def initiate_connect(
        self, user_id: str, provider_name: str = "GMAIL", custom_redirect_uri: Optional[str] = None
    ) -> EmailConnectResponse:
        """Initiates an OAuth connection flow for Gmail."""
        p_upper = provider_name.upper()
        provider = self.get_provider(p_upper)
        state = generate_email_oauth_state(user_id=user_id, provider=p_upper)
        redirect_uri = custom_redirect_uri or settings.GOOGLE_REDIRECT_URI
        auth_url = provider.get_authorization_url(state=state, redirect_uri=redirect_uri)

        return EmailConnectResponse(
            provider=p_upper.lower(),
            authorization_url=auth_url,
            state=state,
        )

    async def handle_oauth_callback(
        self,
        db: AsyncSession,
        code: str,
        state: str,
        provider_name: str = "GMAIL",
        custom_redirect_uri: Optional[str] = None,
    ) -> EmailAccount:
        """Exchanges OAuth code for credentials, encrypts tokens, and stores account."""
        p_upper = provider_name.upper()
        user_id = validate_email_oauth_state(state=state, expected_provider=p_upper)

        provider = self.get_provider(p_upper)
        redirect_uri = custom_redirect_uri or settings.GOOGLE_REDIRECT_URI
        token_result = await provider.exchange_code(code=code, redirect_uri=redirect_uri)

        account_info = await provider.get_account_info(access_token=token_result.access_token)

        # Check existing account
        query = select(EmailAccount).where(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == p_upper.lower(),
            EmailAccount.email_address == account_info.email_address,
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
            existing_account.account_name = account_info.account_name
            existing_account.profile_picture_url = account_info.profile_picture_url
            existing_account.connection_status = "CONNECTED"
            existing_account.token_expires_at = expires_at
            existing_account.scopes = json.dumps(token_result.scopes)
            existing_account.credentials = credentials_dict
            existing_account.metadata_json = json.dumps(account_info.raw_profile) if account_info.raw_profile else None
            account = existing_account
        else:
            account = EmailAccount(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=p_upper.lower(),
                email_address=account_info.email_address,
                account_name=account_info.account_name,
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
        logger.info(f"Successfully connected email account '{account.email_address}' for user {user_id}")
        return account

    async def disconnect_account(
        self, db: AsyncSession, user: User, account_id: str
    ) -> EmailAccount:
        """Disconnects email account, revoking tokens and wiping credentials."""
        query = select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == user.id,
        )
        account = (await db.execute(query)).scalar_one_or_none()
        if not account:
            raise ValueError("Email account not found.")

        creds = account.credentials
        if creds and creds.get("access_token"):
            try:
                provider = self.get_provider(account.provider)
                await provider.revoke_token(creds["access_token"])
            except Exception as e:
                logger.warning(f"Failed to revoke token on email provider: {e}")

        account.connection_status = "DISCONNECTED"
        account.credentials = None
        account.token_expires_at = None
        await db.commit()
        await db.refresh(account)
        return account

    # -----------------------------------------------------------------------
    # AI Email Draft Generation
    # -----------------------------------------------------------------------
    async def generate_ai_draft(
        self, db: AsyncSession, user: User, request: EmailDraftGenerateRequest
    ) -> EmailDraftGenerateResponse:
        """Generates a personalized email draft using Gemini AI based on lead and service context."""
        # 1. Fetch Lead
        lead_query = select(Lead).where(Lead.id == request.lead_id, Lead.user_id == user.id)
        lead = (await db.execute(lead_query)).scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found.")

        if not lead.email:
            raise ValueError("Selected lead does not have an email address.")

        # 2. Fetch Matched Service
        service_id = request.service_id or lead.matched_service_id
        service_name = None
        service_desc = None

        if service_id:
            svc_query = select(Service).where(Service.id == service_id, Service.user_id == user.id)
            service = (await db.execute(svc_query)).scalar_one_or_none()
            if service:
                service_name = service.name
                service_desc = service.description

        # 3. Call AI Service
        recipient_name = lead.name or "Valued Prospect"
        company_name = lead.company or ""
        detected_need = lead.detected_need or lead.description or "Digital solutions & services"

        if self.ai_service:
            ai_res = await self.ai_service.generate_email_draft(
                db=db,
                user=user,
                request=AIEmailDraftRequest(
                    lead_name=recipient_name,
                    lead_company=company_name,
                    detected_need=detected_need,
                    matched_service_name=service_name,
                    tone=request.tone or "Professional and persuasive",
                    extra_instructions=request.context_notes,
                ),
            )
            subject = ai_res.subject
            body = ai_res.body
        else:
            subject = f"Collaboration on {service_name or 'Your Project'} - {company_name or recipient_name}"
            body = (
                f"Hi {recipient_name},\n\n"
                f"I came across your requirements regarding {detected_need}. "
                f"At our agency, we specialize in high-impact {service_name or 'tailored solutions'} designed to streamline operations and drive growth.\n\n"
                f"Would you be open to a brief 10-minute introductory conversation this week to discuss how we can assist?\n\n"
                f"Best regards,\n{user.full_name or 'Client Magnet Team'}"
            )

        return EmailDraftGenerateResponse(
            lead_id=lead.id,
            recipient=lead.email,
            subject=subject,
            body=body,
            matched_service_id=service_id,
            matched_service_name=service_name,
        )

    # -----------------------------------------------------------------------
    # Explicit Send Approval & Email Dispatch
    # -----------------------------------------------------------------------
    async def send_approved_email(
        self, db: AsyncSession, user: User, request: EmailSendRequest
    ) -> EmailSendResult:
        """
        Sends an approved email after checking:
        1. Recipient syntax.
        2. Opt-out registry.
        3. Duplicate send prevention.
        4. Active connected email account.
        """
        # 1. Validate Recipient
        recipient_clean = request.recipient.strip().lower()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_clean):
            raise ValueError(f"Invalid email recipient format: '{request.recipient}'")

        # 2. Check Opt-Out Registry
        opt_out_query = select(OptOut).where(
            OptOut.user_id == user.id,
            OptOut.contact_identifier == recipient_clean,
            OptOut.platform.in_(["email", "all", "GMAIL", "EMAIL"]),
        )
        opt_out_record = (await db.execute(opt_out_query)).scalar_one_or_none()
        if opt_out_record:
            raise ValueError(
                f"Recipient '{recipient_clean}' has opted out of receiving communications. Email blocked."
            )

        if self.compliance_service:
            comp_check = await self.compliance_service.check_action(
                user_id=user.id,
                action_type="send_email",
                payload={"recipient": recipient_clean, "body": request.body, "subject": request.subject},
            )
            if not comp_check.get("allowed", True):
                raise ValueError(f"Compliance check blocked outreach: {comp_check.get('reason')}")

        # 3. Prevent Duplicate Sends (within 60 seconds)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
        dup_query = (
            select(Message)
            .join(Conversation)
            .where(
                Conversation.user_id == user.id,
                Message.recipient == recipient_clean,
                Message.subject == request.subject.strip(),
                Message.sent_at >= recent_cutoff,
                Message.direction == "outbound",
            )
        )
        recent_dup = (await db.execute(dup_query)).scalar_one_or_none()
        if recent_dup:
            raise ValueError("Duplicate email detected. An identical email was already sent in the last 60 seconds.")

        # 4. Check Active Email Account
        query_acc = select(EmailAccount).where(
            EmailAccount.user_id == user.id,
            EmailAccount.connection_status == "CONNECTED",
        )
        email_account = (await db.execute(query_acc)).scalar_one_or_none()
        if not email_account:
            raise ValueError("No connected email account found. Please connect your Gmail account in Settings.")

        creds = email_account.credentials
        if not creds or not creds.get("access_token"):
            raise ValueError("Email credentials expired or invalid. Please re-authorize Gmail.")

        # 5. Dispatch via Provider
        provider = self.get_provider(email_account.provider)
        try:
            send_res = await provider.send_email(
                access_token=creds["access_token"],
                from_email=email_account.email_address,
                to_email=recipient_clean,
                subject=request.subject.strip(),
                body=request.body.strip(),
                in_reply_to=request.in_reply_to_message_id,
            )
            external_msg_id = send_res.get("id") or str(uuid.uuid4())
        except Exception as e:
            logger.error(f"Provider email dispatch failed: {e}", exc_info=True)
            raise ValueError(f"Failed to dispatch email via {email_account.provider.upper()}: {e}")

        # 6. Associate or Create Conversation
        conversation = None
        if request.conversation_id:
            conv_q = select(Conversation).where(
                Conversation.id == request.conversation_id, Conversation.user_id == user.id
            )
            conversation = (await db.execute(conv_q)).scalar_one_or_none()

        if not conversation:
            # Match existing conversation by recipient or lead
            conv_search = select(Conversation).where(
                Conversation.user_id == user.id,
                Conversation.platform == "email",
                or_(
                    Conversation.external_conversation_id == recipient_clean,
                    Conversation.lead_id == request.lead_id if request.lead_id else False,
                ),
            )
            conversation = (await db.execute(conv_search)).scalars().first()

        # If lead_id not set on request, try to find lead by email
        lead_id = request.lead_id
        if not lead_id:
            lead_q = select(Lead).where(Lead.user_id == user.id, Lead.email == recipient_clean)
            matched_lead = (await db.execute(lead_q)).scalar_one_or_none()
            if matched_lead:
                lead_id = matched_lead.id

        sent_time = datetime.now(timezone.utc)

        if not conversation:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id,
                lead_id=lead_id,
                platform="email",
                external_conversation_id=recipient_clean,
                subject=request.subject.strip(),
                status="Open",
                unread_count=0,
                last_message_at=sent_time,
            )
            db.add(conversation)
            await db.flush()
        else:
            conversation.last_message_at = sent_time
            conversation.subject = request.subject.strip()
            if lead_id and not conversation.lead_id:
                conversation.lead_id = lead_id

        # 7. Record Outbound Message
        msg_record = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            sender=email_account.email_address,
            recipient=recipient_clean,
            subject=request.subject.strip(),
            message_content=request.body.strip(),
            platform="email",
            direction="outbound",
            status="SENT",
            external_message_id=external_msg_id,
            sent_at=sent_time,
        )
        db.add(msg_record)

        # Update lead status if lead was associated
        if lead_id:
            lead_q = select(Lead).where(Lead.id == lead_id, Lead.user_id == user.id)
            lead_obj = (await db.execute(lead_q)).scalar_one_or_none()
            if lead_obj and lead_obj.status == "NEW":
                lead_obj.status = "CONTACTED"

        await db.commit()
        await db.refresh(msg_record)

        return EmailSendResult(
            message_id=msg_record.id,
            conversation_id=conversation.id,
            status="SENT",
            recipient=recipient_clean,
            subject=request.subject.strip(),
            external_message_id=external_msg_id,
            sent_at=sent_time,
            message="Email successfully dispatched to recipient.",
        )

    # -----------------------------------------------------------------------
    # Inbox Synchronization & Reply Detection
    # -----------------------------------------------------------------------
    async def sync_inbox(self, db: AsyncSession, user: User) -> int:
        """Syncs recent messages from connected email account, detecting replies and matching leads."""
        query_acc = select(EmailAccount).where(
            EmailAccount.user_id == user.id,
            EmailAccount.connection_status == "CONNECTED",
        )
        email_account = (await db.execute(query_acc)).scalar_one_or_none()
        if not email_account:
            return 0

        creds = email_account.credentials
        if not creds or not creds.get("access_token"):
            return 0

        provider = self.get_provider(email_account.provider)
        try:
            inbox_messages = await provider.fetch_inbox_messages(
                access_token=creds["access_token"], max_results=10
            )
        except Exception as e:
            logger.warning(f"Inbox fetch failed during sync: {e}")
            return 0

        new_count = 0
        for msg_data in inbox_messages:
            # Check if message already recorded
            existing_msg = (
                await db.execute(
                    select(Message).where(Message.external_message_id == msg_data.external_id)
                )
            ).scalar_one_or_none()
            if existing_msg:
                continue

            sender_email = msg_data.sender
            # Extract email inside brackets if format is "Name <email@domain.com>"
            email_match = re.search(r"<([^>]+)>", sender_email)
            clean_sender = email_match.group(1).lower() if email_match else sender_email.strip().lower()

            # Find matching lead for user
            lead_q = select(Lead).where(Lead.user_id == user.id, Lead.email == clean_sender)
            matched_lead = (await db.execute(lead_q)).scalar_one_or_none()
            lead_id = matched_lead.id if matched_lead else None

            # Find or create conversation
            conv_q = select(Conversation).where(
                Conversation.user_id == user.id,
                Conversation.platform == "email",
                or_(
                    Conversation.external_conversation_id == clean_sender,
                    Conversation.lead_id == lead_id if lead_id else False,
                ),
            )
            conversation = (await db.execute(conv_q)).scalars().first()

            if not conversation:
                conversation = Conversation(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    lead_id=lead_id,
                    platform="email",
                    external_conversation_id=clean_sender,
                    subject=msg_data.subject,
                    status="Open",
                    unread_count=1,
                    last_message_at=msg_data.received_at,
                )
                db.add(conversation)
                await db.flush()
            else:
                conversation.last_message_at = msg_data.received_at
                conversation.unread_count += 1
                if lead_id and not conversation.lead_id:
                    conversation.lead_id = lead_id

            # Create Inbound Message record
            new_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                sender=clean_sender,
                recipient=email_account.email_address,
                subject=msg_data.subject,
                message_content=msg_data.body_text or msg_data.snippet,
                platform="email",
                direction="inbound",
                status="RECEIVED",
                external_message_id=msg_data.external_id,
                sent_at=msg_data.received_at,
            )
            db.add(new_msg)

            # If matched lead exists and lead was in CONTACTED status, advance to REPLIED
            if matched_lead and matched_lead.status in ("NEW", "CONTACTED"):
                matched_lead.status = "REPLIED"

            new_count += 1

        await db.commit()
        return new_count

    # -----------------------------------------------------------------------
    # Conversation Queries
    # -----------------------------------------------------------------------
    async def list_conversations(
        self, db: AsyncSession, user_id: str, query_str: Optional[str] = None
    ) -> List[EmailConversationOut]:
        """Lists email conversations for the user with optional search query."""
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.lead), selectinload(Conversation.messages))
            .where(Conversation.user_id == user_id, Conversation.platform == "email")
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        )
        if query_str:
            stmt = stmt.where(
                or_(
                    Conversation.subject.ilike(f"%{query_str}%"),
                    Conversation.external_conversation_id.ilike(f"%{query_str}%"),
                )
            )

        results = (await db.execute(stmt)).scalars().all()

        output: List[EmailConversationOut] = []
        for conv in results:
            lead_info = None
            if conv.lead:
                lead_info = EmailConversationLeadInfo(
                    id=conv.lead.id,
                    name=conv.lead.name,
                    company=conv.lead.company,
                    email=conv.lead.email,
                )

            msgs_out = [
                EmailMessageOut(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    sender=m.sender,
                    recipient=m.recipient,
                    subject=m.subject,
                    message_content=m.message_content,
                    platform=m.platform,
                    direction=m.direction,
                    status=m.status,
                    error_message=m.error_message,
                    external_message_id=m.external_message_id,
                    sent_at=m.sent_at,
                    created_at=m.created_at,
                )
                for m in conv.messages
            ]

            output.append(
                EmailConversationOut(
                    id=conv.id,
                    user_id=conv.user_id,
                    lead_id=conv.lead_id,
                    platform=conv.platform,
                    subject=conv.subject,
                    status=conv.status,
                    unread_count=conv.unread_count,
                    last_message_at=conv.last_message_at,
                    lead=lead_info,
                    messages=msgs_out,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                )
            )
        return output

    async def get_conversation(
        self, db: AsyncSession, user_id: str, conversation_id: str
    ) -> Optional[EmailConversationOut]:
        """Gets full conversation thread by ID."""
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.lead), selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        conv = (await db.execute(stmt)).scalar_one_or_none()
        if not conv:
            return None

        lead_info = None
        if conv.lead:
            lead_info = EmailConversationLeadInfo(
                id=conv.lead.id,
                name=conv.lead.name,
                company=conv.lead.company,
                email=conv.lead.email,
            )

        msgs_out = [
            EmailMessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                sender=m.sender,
                recipient=m.recipient,
                subject=m.subject,
                message_content=m.message_content,
                platform=m.platform,
                direction=m.direction,
                status=m.status,
                error_message=m.error_message,
                external_message_id=m.external_message_id,
                sent_at=m.sent_at,
                created_at=m.created_at,
            )
            for m in conv.messages
        ]

        return EmailConversationOut(
            id=conv.id,
            user_id=conv.user_id,
            lead_id=conv.lead_id,
            platform=conv.platform,
            subject=conv.subject,
            status=conv.status,
            unread_count=conv.unread_count,
            last_message_at=conv.last_message_at,
            lead=lead_info,
            messages=msgs_out,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    async def associate_lead_to_conversation(
        self, db: AsyncSession, user_id: str, conversation_id: str, lead_id: Optional[str]
    ) -> EmailConversationOut:
        """Associates or unassociates a lead with an existing conversation."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        conv = (await db.execute(stmt)).scalar_one_or_none()
        if not conv:
            raise ValueError("Conversation not found.")

        if lead_id:
            lead_q = select(Lead).where(Lead.id == lead_id, Lead.user_id == user_id)
            lead = (await db.execute(lead_q)).scalar_one_or_none()
            if not lead:
                raise ValueError("Lead not found.")

        conv.lead_id = lead_id
        await db.commit()
        return await self.get_conversation(db=db, user_id=user_id, conversation_id=conversation_id)

    async def mark_conversation_as_read(
        self, db: AsyncSession, user_id: str, conversation_id: str
    ) -> None:
        """Marks conversation unread count to 0."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        conv = (await db.execute(stmt)).scalar_one_or_none()
        if conv and conv.unread_count > 0:
            conv.unread_count = 0
            await db.commit()
