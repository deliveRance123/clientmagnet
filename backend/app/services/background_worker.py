import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.follow_up import FollowUp
from app.models.notification import Notification
from app.models.scheduled_post import ScheduledPost
from app.models.user import User
from app.services.content_publisher import ContentService

logger = logging.getLogger("app.services.background_worker")


class BackgroundWorker:
    """
    Lightweight, resource-friendly background task worker.
    Runs periodically inside FastAPI lifespan or as a Render Background Worker.
    Executes due scheduled posts and sends notifications for due follow-ups.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        poll_interval_seconds: int = 60,
        content_service: Optional[ContentService] = None,
    ):
        self.session_factory = session_factory
        self.poll_interval_seconds = poll_interval_seconds
        self.content_service = content_service or ContentService(use_mock=True)
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the background worker loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Background worker started with poll interval of {self.poll_interval_seconds}s.")

    async def stop(self):
        """Stops the background worker loop gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Background worker stopped.")

    async def _run_loop(self):
        while self._running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Error during background worker execution: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.poll_interval_seconds)
            except asyncio.CancelledError:
                break

    async def run_once(self):
        """Executes one cycle of scheduled tasks."""
        async with self.session_factory() as db:
            await self._process_due_scheduled_posts(db)
            await self._process_due_follow_ups(db)

    async def _process_due_scheduled_posts(self, db: AsyncSession):
        """Finds ScheduledPosts whose scheduled_at <= now and publishes them."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(ScheduledPost)
            .where(
                ScheduledPost.status == "Scheduled",
                ScheduledPost.scheduled_at <= now,
            )
            .limit(10)
        )
        posts = (await db.execute(stmt)).scalars().all()
        for p in posts:
            user_stmt = select(User).where(User.id == p.user_id)
            user = (await db.execute(user_stmt)).scalar_one_or_none()
            if not user:
                continue

            try:
                logger.info(f"Executing scheduled post '{p.id}' for platform '{p.platform}'")
                await self.content_service.publish_now(
                    db=db,
                    user=user,
                    content_id=p.content_id,
                    platforms=[p.platform],
                )
            except Exception as e:
                logger.error(f"Failed to publish scheduled post {p.id}: {e}")
                p.status = "Failed"
                p.error_message = str(e)
                await db.commit()

    async def _process_due_follow_ups(self, db: AsyncSession):
        """Scans due follow-ups and generates internal notifications."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(FollowUp)
            .where(
                FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
                FollowUp.scheduled_time <= now,
            )
            .limit(20)
        )
        due_follow_ups = (await db.execute(stmt)).scalars().all()
        for fu in due_follow_ups:
            # Check if notification already created
            notif_stmt = select(Notification).where(
                Notification.user_id == fu.user_id,
                Notification.notification_type == "FOLLOW_UP_DUE",
                Notification.link_url == f"/follow-ups?id={fu.id}",
            )
            existing_notif = (await db.execute(notif_stmt)).scalar_one_or_none()
            if not existing_notif:
                db.add(
                    Notification(
                        user_id=fu.user_id,
                        title="⏰ Follow-Up Due Today",
                        message=f"Follow-up scheduled for lead is due: {fu.notes or 'Reach out to prospect'}",
                        notification_type="FOLLOW_UP_DUE",
                        link_url=f"/follow-ups?id={fu.id}",
                    )
                )
                await db.commit()
