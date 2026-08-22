import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.models.user import User
from app.schemas.unified_inbox import FollowUpCreate
from app.services.unified_inbox import UnifiedInboxService


async def create_user_and_headers(async_client: AsyncClient, email: str = "inbox_user@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Inbox Manager",
            "company_name": "Unified Operations",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Service Layer Tests: Timeline, AI Summary, Follow-Ups, Notifications
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unified_inbox_service_full_flow(db_session: AsyncSession):
    user = User(
        email="unified_flow_user@example.com",
        hashed_password="dummy_password",
        is_active=True,
        full_name="Sarah Inbox",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    lead = Lead(
        user_id=user.id,
        name="TechCorp Founder",
        company="TechCorp",
        email="founder@techcorp.io",
        phone="+14155553333",
        detected_need="Full-stack Next.js and FastAPI platform",
        status="CONTACTED",
    )
    db_session.add(lead)
    await db_session.flush()

    # Create Conversation & Messages
    conv = Conversation(
        user_id=user.id,
        lead_id=lead.id,
        platform="email",
        subject="Project Scoping: Next.js + FastAPI",
        unread_count=1,
    )
    db_session.add(conv)
    await db_session.flush()

    msg1 = Message(
        conversation_id=conv.id,
        sender="founder@techcorp.io",
        recipient="sarah@agency.com",
        message_content="We are looking for a senior developer to build our backend and frontend.",
        platform="email",
        direction="inbound",
        status="RECEIVED",
    )
    db_session.add(msg1)
    await db_session.commit()

    from app.services.ai import get_ai_service
    service = UnifiedInboxService(ai_service=get_ai_service(api_key="", use_mock=True))

    # 1. List conversations with platform filter
    convs = await service.list_conversations(db=db_session, user_id=user.id, platform_filter="email")
    assert len(convs) == 1
    assert convs[0].lead is not None
    assert convs[0].lead.name == "TechCorp Founder"

    # 2. Summarize conversation with Gemini AI
    summary_res = await service.summarize_conversation(db=db_session, user=user, conversation_id=conv.id)
    assert len(summary_res.summary) > 0
    assert len(summary_res.next_action) > 0

    # 3. Suggest Reply with Gemini AI
    reply_res = await service.suggest_reply(db=db_session, user=user, conversation_id=conv.id)
    assert len(reply_res.suggested_reply) > 0

    # 4. Lead Timeline
    timeline = await service.get_lead_timeline(db=db_session, user_id=user.id, lead_id=lead.id)
    assert len(timeline) >= 2  # LEAD_CREATED + MESSAGE_RECEIVED

    # 5. Follow-Up Creation
    fu = await service.create_follow_up(
        db=db_session,
        user=user,
        data=FollowUpCreate(
            lead_id=lead.id,
            conversation_id=conv.id,
            channel="email",
            scheduled_time="2026-09-01T10:00:00Z",
            notes="Follow-up regarding proposal review",
        ),
    )
    assert fu.id is not None
    assert fu.status == "Pending"

    # 6. In-App Notifications
    notifs = await service.get_notifications(db=db_session, user_id=user.id)
    assert isinstance(notifs.unread_count, int)


# ---------------------------------------------------------------------------
# 2. REST API End-to-End Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unified_inbox_and_followups_api(async_client: AsyncClient):
    token, headers = await create_user_and_headers(async_client, "api_inbox_user@example.com")

    # 1. Create Lead
    lead_res = await async_client.post(
        "/api/v1/leads/",
        json={"name": "Alex Investor", "email": "alex@invest.co"},
        headers=headers,
    )
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    # 2. Create Follow-Up via API
    fu_res = await async_client.post(
        "/api/v1/follow-ups/",
        json={
            "lead_id": lead_id,
            "channel": "email",
            "scheduled_time": "2026-09-05T14:00:00Z",
            "notes": "Follow up on product roadmap feedback",
        },
        headers=headers,
    )
    assert fu_res.status_code == 201
    fu_id = fu_res.json()["id"]

    # 3. List Follow-ups
    list_fu = await async_client.get("/api/v1/follow-ups/", headers=headers)
    assert list_fu.status_code == 200
    assert len(list_fu.json()) >= 1

    # 4. Trigger AI Follow-Up Recommendations Scan
    rec_res = await async_client.post("/api/v1/follow-ups/recommend", headers=headers)
    assert rec_res.status_code == 200
    assert "recommended_count" in rec_res.json()

    # 5. List Notifications
    notif_res = await async_client.get("/api/v1/notifications/", headers=headers)
    assert notif_res.status_code == 200
    assert "unread_count" in notif_res.json()

    # 6. Mark All Notifications Read
    mark_all = await async_client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark_all.status_code == 200

    # 7. Get & Update Communication Preferences
    pref_get = await async_client.get("/api/v1/settings/communication-preferences", headers=headers)
    assert pref_get.status_code == 200

    pref_update = await async_client.patch(
        "/api/v1/settings/communication-preferences",
        json={
            "preferred_tone": "Direct & Bold",
            "default_signature": "Best,\nAlex | Founder",
            "preferred_cta": "Book a 15-min call",
        },
        headers=headers,
    )
    assert pref_update.status_code == 200
    assert pref_update.json()["preferred_tone"] == "Direct & Bold"
