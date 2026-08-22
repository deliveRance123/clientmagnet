import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.schemas.activity import ActivityLogOut, ActivityTimelineResponse

logger = logging.getLogger("app.services.activity")


class ActivityService:
    """Service to track, record, and query timeline activities across leads and clients."""

    async def log_activity(
        self,
        db: AsyncSession,
        user_id: str,
        event_type: str,
        description: str,
        lead_id: Optional[str] = None,
        client_id: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ActivityLog:
        """Records an activity event into PostgreSQL."""
        meta_str = json.dumps(metadata) if metadata else None
        log_entry = ActivityLog(
            user_id=user_id,
            lead_id=lead_id,
            client_id=client_id,
            event_type=event_type,
            channel=channel,
            description=description,
            metadata_json=meta_str,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        await db.flush()
        return log_entry

    async def get_lead_timeline(
        self, db: AsyncSession, user_id: str, lead_id: str
    ) -> ActivityTimelineResponse:
        """Retrieves chronological activity audit trail for a specific lead."""
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.lead_id == lead_id)
            .order_by(ActivityLog.created_at.desc())
        )
        logs = (await db.execute(stmt)).scalars().all()
        return ActivityTimelineResponse(
            entity_id=lead_id,
            entity_type="lead",
            activities=[ActivityLogOut.from_orm_log(a) for a in logs],
        )

    async def get_client_timeline(
        self, db: AsyncSession, user_id: str, client_id: str
    ) -> ActivityTimelineResponse:
        """Retrieves chronological activity audit trail for a specific client."""
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.client_id == client_id)
            .order_by(ActivityLog.created_at.desc())
        )
        logs = (await db.execute(stmt)).scalars().all()
        return ActivityTimelineResponse(
            entity_id=client_id,
            entity_type="client",
            activities=[ActivityLogOut.from_orm_log(a) for a in logs],
        )
