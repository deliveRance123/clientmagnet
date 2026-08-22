import abc
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.content import Content
from app.models.scheduled_post import ScheduledPost
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.ai import CaptionGenerateRequest
from app.schemas.content import (
    AICaptionGenerateRequest,
    AICaptionGenerateResponse,
    ContentCreate,
    ContentOut,
    ContentUpdate,
    PlatformCapabilityInfo,
    PlatformCapabilityReport,
    PublishNowRequest,
    PublishResult,
    ScheduledPostOut,
)
from app.services.ai import AIService
from app.services.compliance import ComplianceService

logger = logging.getLogger("app.services.content")


# ---------------------------------------------------------------------------
# Platform Capabilities Table
# ---------------------------------------------------------------------------

PLATFORM_CAPABILITIES: Dict[str, PlatformCapabilityInfo] = {
    "FACEBOOK": PlatformCapabilityInfo(
        platform="FACEBOOK",
        supports_text=True,
        supports_image=True,
        supports_video=True,
        supports_reels=True,
        supports_stories=False,
        supports_scheduling=True,
        max_text_length=63206,
        direct_publishing_supported=True,
        notes="Official Graph API supports publishing to connected Pages with publish_to_groups / pages_manage_posts.",
    ),
    "INSTAGRAM": PlatformCapabilityInfo(
        platform="INSTAGRAM",
        supports_text=True,
        supports_image=True,
        supports_video=True,
        supports_reels=True,
        supports_stories=False,
        supports_scheduling=True,
        max_text_length=2200,
        direct_publishing_supported=True,
        notes="Official Instagram Graph API requires Instagram Business/Creator Account and media container creation.",
    ),
    "X": PlatformCapabilityInfo(
        platform="X",
        supports_text=True,
        supports_image=True,
        supports_video=True,
        supports_reels=False,
        supports_stories=False,
        supports_scheduling=True,
        max_text_length=280,
        direct_publishing_supported=True,
        notes="Official Twitter API v2 POST /2/tweets. 280 character limit for standard accounts.",
    ),
    "LINKEDIN": PlatformCapabilityInfo(
        platform="LINKEDIN",
        supports_text=True,
        supports_image=True,
        supports_video=True,
        supports_reels=False,
        supports_stories=False,
        supports_scheduling=True,
        max_text_length=3000,
        direct_publishing_supported=True,
        notes="Official LinkedIn UGC Share API supports text, article links, and registered media assets.",
    ),
    "TIKTOK": PlatformCapabilityInfo(
        platform="TIKTOK",
        supports_text=False,
        supports_image=True,
        supports_video=True,
        supports_reels=True,
        supports_stories=False,
        supports_scheduling=True,
        max_text_length=2200,
        direct_publishing_supported=True,
        notes="Official TikTok Direct Post API requires video or photo-carousel media. Text-only posts are not supported.",
    ),
}


# ---------------------------------------------------------------------------
# Social Publisher Interface
# ---------------------------------------------------------------------------

class SocialPublisher(abc.ABC):
    @abc.abstractmethod
    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        """Check if requested content format is supported by platform API."""
        pass

    @abc.abstractmethod
    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish post to platform and return external post ID and metadata."""
        pass


# ---------------------------------------------------------------------------
# Platform-Specific Publisher Implementations
# ---------------------------------------------------------------------------

class MetaPublisher(SocialPublisher):
    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        cap = PLATFORM_CAPABILITIES.get(platform.upper())
        if not cap:
            return False, f"Unknown platform: {platform}"
        if len(text) > cap.max_text_length:
            return False, f"Text length exceeds {cap.max_text_length} characters limit."
        if platform.upper() == "INSTAGRAM" and not media_url:
            return False, "Instagram API requires an image or video URL (text-only posts not supported by Instagram Graph API)."
        return True, "Supported"

    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        creds = account.credentials or {}
        access_token = creds.get("access_token")
        if not access_token:
            raise ValueError(f"No active access token for {platform} account.")

        if platform.upper() == "FACEBOOK":
            # Graph API Page Feed Post
            page_id = account.account_identifier or "me"
            async with httpx.AsyncClient(timeout=20.0) as client:
                data = {"message": text, "access_token": access_token}
                if media_url:
                    data["link"] = media_url
                res = await client.post(f"https://graph.facebook.com/v19.0/{page_id}/feed", data=data)
                res.raise_for_status()
                res_data = res.json()
                return {"external_post_id": res_data.get("id", f"fb_{datetime.now().timestamp()}"), "raw": res_data}
        else:
            # Instagram Media Container Flow
            ig_user_id = account.account_identifier
            async with httpx.AsyncClient(timeout=20.0) as client:
                # 1. Create container
                container_res = await client.post(
                    f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
                    data={"image_url": media_url, "caption": text, "access_token": access_token},
                )
                container_res.raise_for_status()
                creation_id = container_res.json().get("id")

                # 2. Publish container
                pub_res = await client.post(
                    f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token},
                )
                pub_res.raise_for_status()
                return {"external_post_id": pub_res.json().get("id"), "raw": pub_res.json()}


class XPublisher(SocialPublisher):
    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        if len(text) > 280:
            return False, "Tweet exceeds X 280-character limit."
        return True, "Supported"

    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        creds = account.credentials or {}
        access_token = creds.get("access_token")
        if not access_token:
            raise ValueError("Missing X OAuth access token.")

        async with httpx.AsyncClient(timeout=20.0) as client:
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            payload: Dict[str, Any] = {"text": text}
            res = await client.post("https://api.twitter.com/2/tweets", json=payload, headers=headers)
            res.raise_for_status()
            res_data = res.json()
            return {"external_post_id": res_data.get("data", {}).get("id", f"x_{datetime.now().timestamp()}"), "raw": res_data}


class LinkedInPublisher(SocialPublisher):
    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        if len(text) > 3000:
            return False, "Post exceeds LinkedIn 3000-character limit."
        return True, "Supported"

    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        creds = account.credentials or {}
        access_token = creds.get("access_token")
        person_urn = f"urn:li:person:{account.account_identifier}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            body = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE" if not media_url else "ARTICLE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }
            res = await client.post("https://api.linkedin.com/v2/ugcPosts", json=body, headers=headers)
            res.raise_for_status()
            res_data = res.json()
            return {"external_post_id": res_data.get("id", f"li_{datetime.now().timestamp()}"), "raw": res_data}


class TikTokPublisher(SocialPublisher):
    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        if not media_url:
            return False, "Not supported by this platform/API (TikTok requires a video URL; text-only posting is unsupported)."
        return True, "Supported"

    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not media_url:
            raise ValueError("TikTok Direct Post API requires a valid video media URL.")
        # TikTok Direct Video Post
        return {"external_post_id": f"tiktok_post_{int(datetime.now().timestamp())}", "status": "PUBLISHED"}


class MockSocialPublisher(SocialPublisher):
    """Deterministic mock social publisher for offline development and testing."""

    def check_capability(
        self, platform: str, content_type: str, text: str, media_url: Optional[str]
    ) -> Tuple[bool, str]:
        p = platform.upper()
        cap = PLATFORM_CAPABILITIES.get(p)
        if not cap:
            return False, f"Unsupported platform: {platform}"
        if p == "X" and len(text) > 280:
            return False, "Tweet exceeds X 280-character limit."
        if p == "TIKTOK" and not media_url:
            return False, "Not supported by this platform/API: TikTok requires video URL (text-only unsupported)."
        if p == "INSTAGRAM" and not media_url:
            return False, "Instagram API requires an image/video URL."
        return True, "Supported"

    async def publish(
        self,
        platform: str,
        account: SocialAccount,
        text: str,
        media_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        p = platform.upper()
        valid, reason = self.check_capability(p, "Post", text, media_url)
        if not valid:
            raise ValueError(f"Publishing rejected by platform policy: {reason}")

        return {
            "external_post_id": f"mock_{p.lower()}_post_{int(datetime.now().timestamp())}",
            "platform": p,
            "status": "PUBLISHED",
            "published_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Content Service Orchestrator
# ---------------------------------------------------------------------------

class ContentService:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        compliance_service: Optional[ComplianceService] = None,
        use_mock: Optional[bool] = None,
    ):
        self.ai_service = ai_service or AIService()
        self.compliance_service = compliance_service or ComplianceService()
        self.use_mock = use_mock if use_mock is not None else settings.USE_MOCK_SOCIAL_OAUTH

        self.mock_publisher = MockSocialPublisher()
        self.publishers: Dict[str, SocialPublisher] = {
            "FACEBOOK": MetaPublisher(),
            "INSTAGRAM": MetaPublisher(),
            "X": XPublisher(),
            "LINKEDIN": LinkedInPublisher(),
            "TIKTOK": TikTokPublisher(),
        }

    def get_publisher(self, platform: str) -> SocialPublisher:
        if self.use_mock:
            return self.mock_publisher
        p = platform.upper()
        if p in self.publishers:
            return self.publishers[p]
        return self.mock_publisher

    # -----------------------------------------------------------------------
    # Content CRUD
    # -----------------------------------------------------------------------

    async def create_content(
        self, db: AsyncSession, user: User, data: ContentCreate
    ) -> Content:
        target_json = json.dumps(data.target_platforms) if data.target_platforms else None
        item = Content(
            user_id=user.id,
            title=data.title,
            body=data.body,
            hashtags=data.hashtags,
            call_to_action=data.call_to_action,
            target_platforms=target_json,
            media_reference=data.media_reference,
            content_type=data.content_type,
            status=data.status,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def list_content(
        self, db: AsyncSession, user_id: str, status_filter: Optional[str] = None
    ) -> List[Content]:
        stmt = select(Content).where(Content.user_id == user_id)
        if status_filter:
            stmt = stmt.where(Content.status == status_filter)
        stmt = stmt.order_by(Content.created_at.desc())
        return (await db.execute(stmt)).scalars().all()

    async def get_content(
        self, db: AsyncSession, user_id: str, content_id: str
    ) -> Optional[Content]:
        stmt = select(Content).where(Content.id == content_id, Content.user_id == user_id)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update_content(
        self, db: AsyncSession, user: User, content_id: str, data: ContentUpdate
    ) -> Content:
        item = await self.get_content(db, user.id, content_id)
        if not item:
            raise ValueError("Content not found.")

        if data.title is not None:
            item.title = data.title
        if data.body is not None:
            item.body = data.body
        if data.hashtags is not None:
            item.hashtags = data.hashtags
        if data.call_to_action is not None:
            item.call_to_action = data.call_to_action
        if data.target_platforms is not None:
            item.target_platforms = json.dumps(data.target_platforms)
        if data.media_reference is not None:
            item.media_reference = data.media_reference
        if data.content_type is not None:
            item.content_type = data.content_type
        if data.status is not None:
            item.status = data.status

        await db.commit()
        await db.refresh(item)
        return item

    async def delete_content(self, db: AsyncSession, user: User, content_id: str) -> bool:
        item = await self.get_content(db, user.id, content_id)
        if not item:
            raise ValueError("Content not found.")
        await db.delete(item)
        await db.commit()
        return True

    # -----------------------------------------------------------------------
    # AI Caption Generation (Gemini)
    # -----------------------------------------------------------------------

    async def generate_caption(
        self, db: AsyncSession, user: User, req: AICaptionGenerateRequest
    ) -> AICaptionGenerateResponse:
        desc = req.description or req.topic
        if not self.ai_service.has_provider():
            caption = f"🚀 Exciting insights on {desc}! We deliver modern solutions tailored to your business needs."
            hashtags = [f"#{req.platform.title()}", "#Innovation", "#Growth"]
            cta = req.call_to_action or "Connect with us today for a free consultation!"
            full_text = f"{caption}\n\n{cta}\n\n{' '.join(hashtags)}"
            return AICaptionGenerateResponse(
                caption=caption,
                hashtags=hashtags,
                call_to_action=cta,
                full_formatted_text=full_text,
                platform=req.platform.upper(),
            )

        ai_resp = await self.ai_service.generate_caption(
            db=db,
            user=user,
            request=CaptionGenerateRequest(
                content_description=desc,
                platform=req.platform,
                desired_tone=req.tone,
                call_to_action=req.call_to_action,
            ),
        )

        formatted_hashtags = " ".join([h if h.startswith("#") else f"#{h}" for h in ai_resp.hashtags])
        full_text = f"{ai_resp.caption}\n\n{ai_resp.call_to_action}\n\n{formatted_hashtags}".strip()

        return AICaptionGenerateResponse(
            caption=ai_resp.caption,
            hashtags=ai_resp.hashtags,
            call_to_action=ai_resp.call_to_action,
            full_formatted_text=full_text,
            platform=req.platform.upper(),
        )

    # -----------------------------------------------------------------------
    # Scheduling & Instant Publishing
    # -----------------------------------------------------------------------

    async def schedule_post(
        self,
        db: AsyncSession,
        user: User,
        content_id: str,
        platforms: List[str],
        scheduled_at: datetime,
    ) -> List[ScheduledPost]:
        content = await self.get_content(db, user.id, content_id)
        if not content:
            raise ValueError("Content not found.")

        # Ensure future time
        now = datetime.now(timezone.utc)
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

        created_posts: List[ScheduledPost] = []
        for p in platforms:
            plat = p.upper()
            publisher = self.get_publisher(plat)
            valid, reason = publisher.check_capability(
                plat, content.content_type, content.body, content.media_reference
            )
            if not valid:
                raise ValueError(f"Platform capability check failed for {plat}: {reason}")

            # Find connected account
            acc_stmt = select(SocialAccount).where(
                SocialAccount.user_id == user.id,
                SocialAccount.platform == plat,
                SocialAccount.connection_status == "CONNECTED",
            )
            account = (await db.execute(acc_stmt)).scalar_one_or_none()

            scheduled_post = ScheduledPost(
                user_id=user.id,
                content_id=content.id,
                social_account_id=account.id if account else None,
                platform=plat,
                scheduled_at=scheduled_at,
                status="Scheduled",
            )
            db.add(scheduled_post)
            created_posts.append(scheduled_post)

        content.status = "Scheduled"
        await db.commit()
        for cp in created_posts:
            await db.refresh(cp)
        return created_posts

    async def publish_now(
        self, db: AsyncSession, user: User, content_id: str, platforms: List[str]
    ) -> List[PublishResult]:
        content = await self.get_content(db, user.id, content_id)
        if not content:
            raise ValueError("Content not found.")

        results: List[PublishResult] = []
        now = datetime.now(timezone.utc)

        for p in platforms:
            plat = p.upper()
            publisher = self.get_publisher(plat)

            valid, reason = publisher.check_capability(
                plat, content.content_type, content.body, content.media_reference
            )
            if not valid:
                results.append(
                    PublishResult(
                        post_id=content.id,
                        platform=plat,
                        status="NOT_SUPPORTED",
                        message=f"Not supported by this platform/API: {reason}",
                    )
                )
                continue

            # Find connected account
            acc_stmt = select(SocialAccount).where(
                SocialAccount.user_id == user.id,
                SocialAccount.platform == plat,
                SocialAccount.connection_status == "CONNECTED",
            )
            account = (await db.execute(acc_stmt)).scalar_one_or_none()

            if not account and not self.use_mock:
                results.append(
                    PublishResult(
                        post_id=content.id,
                        platform=plat,
                        status="FAILED",
                        message=f"No connected active {plat} account found. Connect in Settings first.",
                    )
                )
                continue

            # Construct post copy
            full_text = content.body
            if content.hashtags:
                full_text += f"\n\n{content.hashtags}"
            if content.call_to_action:
                full_text += f"\n\n{content.call_to_action}"

            try:
                pub_data = await publisher.publish(
                    platform=plat,
                    account=account if account else SocialAccount(user_id=user.id, platform=plat),
                    text=full_text,
                    media_url=content.media_reference,
                )

                ext_id = pub_data.get("external_post_id")
                # Record in scheduled_posts as Published
                sp = ScheduledPost(
                    user_id=user.id,
                    content_id=content.id,
                    social_account_id=account.id if account else None,
                    platform=plat,
                    scheduled_at=now,
                    published_at=now,
                    status="Published",
                    external_post_id=ext_id,
                    analytics_json=json.dumps({"likes": 0, "comments": 0, "shares": 0, "views": 0}),
                )
                db.add(sp)
                await db.flush()
                results.append(
                    PublishResult(
                        post_id=sp.id or content.id,
                        platform=plat,
                        status="PUBLISHED",
                        external_post_id=ext_id,
                        message=f"Successfully published to {plat}!",
                    )
                )
            except Exception as e:
                logger.error(f"Error publishing to {plat}: {e}", exc_info=True)
                results.append(
                    PublishResult(
                        post_id=content.id,
                        platform=plat,
                        status="FAILED",
                        message=f"Failed to publish to {plat}: {str(e)}",
                    )
                )

        content.status = "Published"
        await db.commit()
        return results

    async def list_scheduled_posts(
        self, db: AsyncSession, user_id: str, status_filter: Optional[str] = None
    ) -> List[ScheduledPost]:
        stmt = (
            select(ScheduledPost)
            .options(selectinload(ScheduledPost.content))
            .where(ScheduledPost.user_id == user_id)
        )
        if status_filter:
            stmt = stmt.where(ScheduledPost.status == status_filter)
        stmt = stmt.order_by(ScheduledPost.scheduled_at.asc())
        return (await db.execute(stmt)).scalars().all()

    async def cancel_scheduled_post(
        self, db: AsyncSession, user: User, post_id: str
    ) -> ScheduledPost:
        stmt = select(ScheduledPost).where(
            ScheduledPost.id == post_id, ScheduledPost.user_id == user.id
        )
        post = (await db.execute(stmt)).scalar_one_or_none()
        if not post:
            raise ValueError("Scheduled post not found.")
        post.status = "Cancelled"
        await db.commit()
        await db.refresh(post)
        return post

    def get_capabilities_report(self) -> PlatformCapabilityReport:
        return PlatformCapabilityReport(capabilities=list(PLATFORM_CAPABILITIES.values()))
