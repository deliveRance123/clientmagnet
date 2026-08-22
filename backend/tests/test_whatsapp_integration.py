import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.opt_out import OptOut
from app.models.user import User
from app.models.whatsapp import WhatsAppAccount
from app.schemas.whatsapp import (
    WhatsAppAccountCreate,
    WhatsAppSendRequest,
)
from app.services.whatsapp import WhatsAppService


async def create_user_and_headers(async_client: AsyncClient, email: str = "wa_user@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "WhatsApp Manager",
            "company_name": "Messaging Pro",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. WhatsApp Webhook Verification & Processing Tests
# ---------------------------------------------------------------------------

def test_webhook_challenge_verification():
    service = WhatsAppService()
    challenge = service.verify_webhook_challenge(
        mode="subscribe",
        token="client_magnet_whatsapp_verify_token",
        challenge="CHALLENGE_STRING_123",
    )
    assert challenge == "CHALLENGE_STRING_123"

    with pytest.raises(ValueError):
        service.verify_webhook_challenge("subscribe", "wrong_token", "CHALLENGE_STRING_123")


@pytest.mark.asyncio
async def test_incoming_webhook_ingestion_and_lead_matching(db_session: AsyncSession):
    """Verify Meta incoming webhook ingests messages into unified conversations."""
    user = User(
        email="webhook_tester@example.com",
        hashed_password="dummy_password",
        is_active=True,
        full_name="Sam WhatsApp",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Add Lead with phone
    lead = Lead(
        user_id=user.id,
        name="Marcus Prospect",
        company="Nordic Ventures",
        phone="+14155552671",
        detected_need="Custom SaaS Web Development",
        status="CONTACTED",
    )
    db_session.add(lead)

    # Connect WhatsApp account
    account = WhatsAppAccount(
        user_id=user.id,
        phone_number_id="PHONE_ID_999",
        phone_number="+18005550199",
        display_name="Client Magnet Dev",
        connection_status="CONNECTED",
    )
    account.credentials = {"access_token": "mock_token"}
    db_session.add(account)
    await db_session.commit()

    service = WhatsAppService(use_mock=True)

    # Simulate Meta Incoming Webhook Payload
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "18005550199",
                                "phone_number_id": "PHONE_ID_999",
                            },
                            "contacts": [{"profile": {"name": "Marcus Prospect"}, "wa_id": "14155552671"}],
                            "messages": [
                                {
                                    "from": "14155552671",
                                    "id": "wamid.HBgLMTQxNTU1NTI2NzEVAgASGBQz",
                                    "timestamp": "1724330000",
                                    "text": {"body": "Hi! We are ready to proceed with the landing page redesign."},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    count = await service.process_incoming_webhook(db=db_session, payload=webhook_payload)
    assert count == 1

    # Verify conversation created & linked to lead
    conv_stmt = select(Conversation).where(
        Conversation.user_id == user.id, Conversation.platform == "whatsapp"
    )
    conv = (await db_session.execute(conv_stmt)).scalar_one_or_none()
    assert conv is not None
    assert conv.lead_id == lead.id
    assert conv.unread_count >= 1

    # Verify Lead status advanced to REPLIED
    await db_session.refresh(lead)
    assert lead.status == "REPLIED"


# ---------------------------------------------------------------------------
# 2. Approved WhatsApp Send, Opt-Out, and Duplicate Prevention Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_approved_whatsapp_message(db_session: AsyncSession):
    user = User(
        email="send_wa_user@example.com",
        hashed_password="dummy_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    account = WhatsAppAccount(
        user_id=user.id,
        phone_number_id="PHONE_ID_123",
        phone_number="+18005550199",
        connection_status="CONNECTED",
    )
    account.credentials = {"access_token": "valid_token"}
    db_session.add(account)
    await db_session.commit()

    service = WhatsAppService(use_mock=True)

    # 1. Send message successfully
    res = await service.send_approved_message(
        db=db_session,
        user=user,
        req=WhatsAppSendRequest(
            recipient_phone="+14155559999",
            message_text="Hello! Confirming our consultation for tomorrow at 2 PM.",
        ),
    )
    assert res.status == "SENT"
    assert res.recipient_phone == "+14155559999"

    # 2. Duplicate send blocked within 60 seconds
    with pytest.raises(ValueError, match="Duplicate message detected"):
        await service.send_approved_message(
            db=db_session,
            user=user,
            req=WhatsAppSendRequest(
                recipient_phone="+14155559999",
                message_text="Hello! Confirming our consultation for tomorrow at 2 PM.",
            ),
        )

    # 3. Opt-out blocked
    opt = OptOut(
        user_id=user.id,
        contact_identifier="+14155550000",
        platform="whatsapp",
        reason="Requested stop",
    )
    db_session.add(opt)
    await db_session.commit()

    with pytest.raises(ValueError, match="opted out"):
        await service.send_approved_message(
            db=db_session,
            user=user,
            req=WhatsAppSendRequest(
                recipient_phone="+14155550000",
                message_text="Hello! Special update for you.",
            ),
        )


# ---------------------------------------------------------------------------
# 3. REST API End-to-End Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_whatsapp_api_endpoints(async_client: AsyncClient):
    token, headers = await create_user_and_headers(async_client, "wa_api_user@example.com")

    # 1. Connect Account
    conn_res = await async_client.post(
        "/api/v1/whatsapp/connect",
        json={
            "phone_number_id": "100200300",
            "phone_number": "+14155550100",
            "display_name": "Support Line",
            "access_token": "EAABmocktoken...",
        },
        headers=headers,
    )
    assert conn_res.status_code == 201
    account = conn_res.json()
    assert account["connection_status"] == "CONNECTED"

    # 2. List Accounts
    accs_res = await async_client.get("/api/v1/whatsapp/accounts", headers=headers)
    assert accs_res.status_code == 200
    assert len(accs_res.json()) >= 1

    # 3. Webhook GET Verification Challenge
    challenge_res = await async_client.get(
        "/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=client_magnet_whatsapp_verify_token&hub.challenge=test_challenge_code"
    )
    assert challenge_res.status_code == 200
    assert challenge_res.text == "test_challenge_code"

    # 4. Send Message via API
    send_res = await async_client.post(
        "/api/v1/whatsapp/send",
        json={
            "recipient_phone": "+14155558888",
            "message_text": "Hi, thanks for reaching out!",
        },
        headers=headers,
    )
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "SENT"
