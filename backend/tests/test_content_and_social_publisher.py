import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.scheduled_post import ScheduledPost
from app.models.user import User
from app.schemas.content import (
    AICaptionGenerateRequest,
    ContentCreate,
)
from app.services.content_publisher import (
    ContentService,
    MockSocialPublisher,
)


async def create_user_and_headers(async_client: AsyncClient, email: str = "content_user@example.com"):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Content Creator",
            "company_name": "Creative Agency",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Unit Tests: MockSocialPublisher & Capability Checks
# ---------------------------------------------------------------------------

def test_platform_capability_checks():
    """Verify platform-specific capability rules."""
    pub = MockSocialPublisher()

    # X length check
    valid, _ = pub.check_capability("X", "Post", "Short tweet", None)
    assert valid is True
    valid, reason = pub.check_capability("X", "Post", "a" * 300, None)
    assert valid is False
    assert "280" in reason

    # TikTok requires media
    valid, reason = pub.check_capability("TIKTOK", "Post", "Text caption", None)
    assert valid is False
    assert "video" in reason.lower()

    # TikTok with media passes
    valid, _ = pub.check_capability("TIKTOK", "Post", "Text caption", "https://video.mp4")
    assert valid is True


# ---------------------------------------------------------------------------
# 2. Service Layer: Content CRUD, Scheduling & Publishing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_content_service_full_flow(db_session: AsyncSession):
    user = User(
        email="service_content_tester@example.com",
        hashed_password="dummy_password",
        is_active=True,
        full_name="Alex Content",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = ContentService(use_mock=True)

    # 1. Create content draft
    item = await service.create_content(
        db=db_session,
        user=user,
        data=ContentCreate(
            title="Website Redesign Promo",
            body="We craft high-converting modern web applications for founders.",
            hashtags="#NextJS #FastAPI",
            call_to_action="DM us for a free quote",
            target_platforms=["LINKEDIN", "X"],
        ),
    )
    assert item.id is not None
    assert item.status == "Draft"

    # 2. Generate AI Caption
    caption_res = await service.generate_caption(
        db=db_session,
        user=user,
        req=AICaptionGenerateRequest(
            topic="Next.js 14 Web Development",
            platform="LINKEDIN",
            tone="Professional",
        ),
    )
    assert len(caption_res.caption) > 0
    assert len(caption_res.call_to_action) > 0

    # 3. Publish Now
    pub_results = await service.publish_now(
        db=db_session,
        user=user,
        content_id=item.id,
        platforms=["LINKEDIN", "X"],
    )
    assert len(pub_results) == 2
    assert all(r.status == "PUBLISHED" for r in pub_results)

    # 4. Verify post status updated
    await db_session.refresh(item)
    assert item.status == "Published"


# ---------------------------------------------------------------------------
# 3. REST API End-to-End Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_content_api_endpoints(async_client: AsyncClient):
    token, headers = await create_user_and_headers(async_client, "api_content_user@example.com")

    # 1. Check Capabilities Matrix
    cap_res = await async_client.get("/api/v1/content/capabilities", headers=headers)
    assert cap_res.status_code == 200
    caps = cap_res.json()["capabilities"]
    assert len(caps) >= 5

    # 2. Create Content Draft via API
    create_res = await async_client.post(
        "/api/v1/content/",
        json={
            "title": "Agency Automation Showcase",
            "body": "Automate client acquisition and delivery seamlessly.",
            "hashtags": "#Automation #SaaS",
            "target_platforms": ["LINKEDIN", "X"],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    content_id = create_res.json()["id"]

    # 3. Generate AI Caption via API
    ai_res = await async_client.post(
        "/api/v1/content/generate-caption",
        json={"topic": "Freelancer CRM Systems", "platform": "LINKEDIN"},
        headers=headers,
    )
    assert ai_res.status_code == 200
    assert "caption" in ai_res.json()

    # 4. Schedule Post via API
    sched_res = await async_client.post(
        "/api/v1/social/schedule",
        json={
            "content_id": content_id,
            "platforms": ["LINKEDIN"],
            "scheduled_at": "2026-09-01T10:00:00Z",
        },
        headers=headers,
    )
    assert sched_res.status_code == 201
    scheduled_posts = sched_res.json()
    assert len(scheduled_posts) == 1
    post_id = scheduled_posts[0]["id"]

    # 5. List Scheduled Posts
    list_sched = await async_client.get("/api/v1/social/schedule", headers=headers)
    assert list_sched.status_code == 200
    assert len(list_sched.json()) >= 1

    # 6. Cancel Scheduled Post
    cancel_res = await async_client.post(
        f"/api/v1/social/schedule/{post_id}/cancel", headers=headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

    # 7. Publish Now via API
    pub_res = await async_client.post(
        "/api/v1/social/publish-now",
        json={"content_id": content_id, "platforms": ["LINKEDIN"]},
        headers=headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()[0]["status"] == "PUBLISHED"
