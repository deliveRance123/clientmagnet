import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.email_account import EmailAccount
from app.models.lead import Lead
from app.models.message import Message
from app.models.opt_out import OptOut
from app.models.service import Service
from app.models.user import User
from app.schemas.email import (
    EmailDraftGenerateRequest,
    EmailSendRequest,
)
from app.services.email import (
    EmailService,
    MockEmailProvider,
    generate_email_oauth_state,
    validate_email_oauth_state,
)


# Helper to register user and obtain bearer token
async def create_user_and_headers(async_client: AsyncClient, email: str = "email_tester@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Email Tester",
            "company_name": "Email Automation Labs",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. State Security & CSRF Validation Tests
# ---------------------------------------------------------------------------

def test_email_oauth_state_generation_and_validation():
    """Verify cryptographically signed state token roundtrip and provider checks."""
    user_id = "test-user-uuid-999"

    # Valid state
    state = generate_email_oauth_state(user_id=user_id, provider="GMAIL")
    recovered = validate_email_oauth_state(state=state, expected_provider="GMAIL")
    assert recovered == user_id

    # Provider mismatch
    with pytest.raises(ValueError, match="provider mismatch"):
        validate_email_oauth_state(state=state, expected_provider="OUTLOOK")

    # Tampered state
    with pytest.raises(ValueError, match="Invalid or tampered"):
        validate_email_oauth_state(state=state + "tampered", expected_provider="GMAIL")


# ---------------------------------------------------------------------------
# 2. Mock Email Provider Unit Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_email_provider():
    """Verify MockEmailProvider methods."""
    provider = MockEmailProvider()

    auth_url = provider.get_authorization_url("mock_state", "http://localhost/cb")
    assert "mock_state" in auth_url

    tokens = await provider.exchange_code("mock_code", "http://localhost/cb")
    assert tokens.access_token.startswith("mock_gmail_access_token_")
    assert len(tokens.scopes) > 0

    info = await provider.get_account_info(tokens.access_token)
    assert info.email_address == "founder@clientmagnet.com"

    send_res = await provider.send_email(
        access_token=tokens.access_token,
        from_email="founder@clientmagnet.com",
        to_email="client@acme.com",
        subject="Hello",
        body="World",
    )
    assert "id" in send_res

    inbox = await provider.fetch_inbox_messages(tokens.access_token)
    assert len(inbox) > 0


# ---------------------------------------------------------------------------
# 3. Email Service Lifecycle: Connect, AI Draft, Send, Opt-Out, Duplicate, Sync
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_email_service_full_flow(db_session: AsyncSession):
    """Test full EmailService lifecycle in PostgreSQL."""
    user = User(
        email="service_flow_user@example.com",
        hashed_password="hashed_dummy_password",
        is_active=True,
        full_name="Alex Founder",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create Lead & Service
    service = Service(
        user_id=user.id,
        name="Website Design",
        description="Custom responsive Next.js web applications",
        is_active=True,
    )
    db_session.add(service)
    await db_session.flush()

    lead = Lead(
        user_id=user.id,
        name="Jonathan Prospect",
        company="Apex Tech",
        email="prospect@apexventures.io",
        detected_need="Needs high-converting landing page",
        matched_service_id=service.id,
        status="NEW",
    )
    db_session.add(lead)
    await db_session.commit()

    email_service = EmailService()

    # 1. Connect Account
    init_res = email_service.initiate_connect(user_id=user.id, provider_name="GMAIL")
    account = await email_service.handle_oauth_callback(
        db=db_session, code="code123", state=init_res.state, provider_name="GMAIL"
    )
    assert account.connection_status == "CONNECTED"
    assert account.credentials is not None
    # Verify encrypted ciphertext
    assert "mock_gmail_access_token" not in account.encrypted_credentials

    # 2. Generate AI Draft
    draft = await email_service.generate_ai_draft(
        db=db_session,
        user=user,
        request=EmailDraftGenerateRequest(lead_id=lead.id, service_id=service.id),
    )
    assert draft.recipient == "prospect@apexventures.io"
    assert len(draft.subject) > 0
    assert len(draft.body) > 0

    # 3. Send Approved Email
    send_res = await email_service.send_approved_email(
        db=db_session,
        user=user,
        request=EmailSendRequest(
            recipient="prospect@apexventures.io",
            subject=draft.subject,
            body=draft.body,
            lead_id=lead.id,
        ),
    )
    assert send_res.status == "SENT"
    assert send_res.recipient == "prospect@apexventures.io"

    # Verify Lead status advanced to CONTACTED
    await db_session.refresh(lead)
    assert lead.status == "CONTACTED"

    # 4. Duplicate Send Prevention (within 60 seconds)
    with pytest.raises(ValueError, match="Duplicate email detected"):
        await email_service.send_approved_email(
            db=db_session,
            user=user,
            request=EmailSendRequest(
                recipient="prospect@apexventures.io",
                subject=draft.subject,
                body=draft.body,
                lead_id=lead.id,
            ),
        )

    # 5. Opt-Out Protection
    opt_out = OptOut(
        user_id=user.id,
        contact_identifier="unsub@domain.com",
        platform="email",
        reason="Requested no further emails",
    )
    db_session.add(opt_out)
    await db_session.commit()

    with pytest.raises(ValueError, match="opted out"):
        await email_service.send_approved_email(
            db=db_session,
            user=user,
            request=EmailSendRequest(
                recipient="unsub@domain.com",
                subject="Special offer",
                body="Hello",
            ),
        )

    # 6. Sync Inbox & Reply Detection
    synced = await email_service.sync_inbox(db=db_session, user=user)
    assert synced > 0

    # Verify lead advanced to REPLIED because prospect@apexventures.io sent inbound reply
    await db_session.refresh(lead)
    assert lead.status == "REPLIED"

    # 7. Disconnect Account
    disc = await email_service.disconnect_account(db=db_session, user=user, account_id=account.id)
    assert disc.connection_status == "DISCONNECTED"
    assert disc.encrypted_credentials is None


# ---------------------------------------------------------------------------
# 4. Authenticated REST API Endpoints Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticated_email_api_endpoints(async_client: AsyncClient):
    """Test /api/v1/email endpoints end-to-end."""
    token, headers = await create_user_and_headers(async_client, "email_api_user@example.com")

    # 1. Connect Gmail via API
    init_res = (await async_client.get("/api/v1/email/connect", headers=headers)).json()
    assert "state" in init_res
    state = init_res["state"]

    cb_res = await async_client.post(
        "/api/v1/email/callback",
        json={"code": "valid_mock_code", "state": state},
        headers=headers,
    )
    assert cb_res.status_code == 200
    account = cb_res.json()
    assert account["connection_status"] == "CONNECTED"
    assert "access_token" not in account  # Tokens never exposed

    # 2. List accounts
    accs_res = await async_client.get("/api/v1/email/accounts", headers=headers)
    assert accs_res.status_code == 200
    assert len(accs_res.json()) == 1

    # 3. Create a Lead to test drafting and sending
    lead_res = await async_client.post(
        "/api/v1/leads/",
        json={
            "name": "David Prospect",
            "company": "Cloud Corp",
            "email": "david@cloudcorp.com",
            "description": "Looking for graphics and UI/UX design",
        },
        headers=headers,
    )
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    # 4. Generate AI Draft
    draft_res = await async_client.post(
        "/api/v1/email/drafts/generate",
        json={"lead_id": lead_id, "tone": "Professional"},
        headers=headers,
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["recipient"] == "david@cloudcorp.com"

    # 5. Send Approved Email
    send_res = await async_client.post(
        "/api/v1/email/send",
        json={
            "recipient": draft_data["recipient"],
            "subject": draft_data["subject"],
            "body": draft_data["body"],
            "lead_id": lead_id,
        },
        headers=headers,
    )
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "SENT"
    conv_id = send_res.json()["conversation_id"]

    # 6. List Conversations
    convs_res = await async_client.get("/api/v1/email/conversations", headers=headers)
    assert convs_res.status_code == 200
    assert len(convs_res.json()) >= 1

    # 7. Get Conversation Thread
    thread_res = await async_client.get(f"/api/v1/email/conversations/{conv_id}", headers=headers)
    assert thread_res.status_code == 200
    assert len(thread_res.json()["messages"]) >= 1

    # 8. Sync Inbox
    sync_res = await async_client.post("/api/v1/email/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "success"

    # 9. Disconnect Account
    disc_res = await async_client.post(
        f"/api/v1/email/accounts/{account['id']}/disconnect", headers=headers
    )
    assert disc_res.status_code == 200
    assert disc_res.json()["connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_email_user_data_isolation(async_client: AsyncClient):
    """Verify User A cannot access or manipulate User B's email conversations."""
    _, headers_a = await create_user_and_headers(async_client, "email_user_a@example.com")
    _, headers_b = await create_user_and_headers(async_client, "email_user_b@example.com")

    # User B connects and sends an email
    init_b = (await async_client.get("/api/v1/email/connect", headers=headers_b)).json()
    await async_client.post(
        "/api/v1/email/callback",
        json={"code": "code_b", "state": init_b["state"]},
        headers=headers_b,
    )
    send_b = (
        await async_client.post(
            "/api/v1/email/send",
            json={"recipient": "test@b.com", "subject": "Priv", "body": "Secret info"},
            headers=headers_b,
        )
    ).json()
    conv_b_id = send_b["conversation_id"]

    # User A tries to view User B's conversation -> 404
    get_res = await async_client.get(
        f"/api/v1/email/conversations/{conv_b_id}", headers=headers_a
    )
    assert get_res.status_code == 404
