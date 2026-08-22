import logging
from typing import List
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.models.message import Message
from app.schemas.search import GlobalSearchResponse, GlobalSearchResultItem

logger = logging.getLogger("app.services.search")


class GlobalSearchService:
    """Multi-entity, user-isolated global search across leads, clients, conversations, and messages."""

    async def search(
        self, db: AsyncSession, user_id: str, query: str, limit: int = 20
    ) -> GlobalSearchResponse:
        q_clean = query.strip()
        if not q_clean:
            return GlobalSearchResponse(query=query, total_results=0, results=[])

        q_like = f"%{q_clean}%"
        results: List[GlobalSearchResultItem] = []

        # 1. Search Leads
        lead_stmt = (
            select(Lead)
            .where(
                Lead.user_id == user_id,
                or_(
                    Lead.name.ilike(q_like),
                    Lead.company.ilike(q_like),
                    Lead.email.ilike(q_like),
                    Lead.phone.ilike(q_like),
                    Lead.detected_need.ilike(q_like),
                    Lead.description.ilike(q_like),
                ),
            )
            .limit(limit)
        )
        leads = (await db.execute(lead_stmt)).scalars().all()
        for l in leads:
            results.append(
                GlobalSearchResultItem(
                    id=l.id,
                    entity_type="lead",
                    title=l.name,
                    subtitle=f"Lead ({l.company or 'Direct'}) - Status: {l.status}",
                    snippet=l.detected_need or l.description,
                    url=f"/leads?selected={l.id}",
                    metadata={"status": l.status, "email": l.email, "phone": l.phone},
                )
            )

        # 2. Search Clients
        client_stmt = (
            select(Client)
            .where(
                Client.user_id == user_id,
                or_(
                    Client.name.ilike(q_like),
                    Client.company.ilike(q_like),
                    Client.email.ilike(q_like),
                    Client.phone.ilike(q_like),
                    Client.service_purchased.ilike(q_like),
                    Client.notes.ilike(q_like),
                ),
            )
            .limit(limit)
        )
        clients = (await db.execute(client_stmt)).scalars().all()
        for c in clients:
            results.append(
                GlobalSearchResultItem(
                    id=c.id,
                    entity_type="client",
                    title=c.name,
                    subtitle=f"Client ({c.company or 'Direct'}) - Status: {c.status}",
                    snippet=c.service_purchased or c.notes,
                    url=f"/clients?selected={c.id}",
                    metadata={"status": c.status, "email": c.email, "phone": c.phone},
                )
            )

        # 3. Search Conversations
        conv_stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                or_(
                    Conversation.subject.ilike(q_like),
                    Conversation.external_conversation_id.ilike(q_like),
                ),
            )
            .limit(limit)
        )
        convs = (await db.execute(conv_stmt)).scalars().all()
        for cv in convs:
            results.append(
                GlobalSearchResultItem(
                    id=cv.id,
                    entity_type="conversation",
                    title=cv.subject or f"{cv.platform.title()} Conversation",
                    subtitle=f"Channel: {cv.platform.upper()}",
                    snippet=f"Unread: {cv.unread_count}, Status: {cv.status}",
                    url=f"/messages?conversation={cv.id}",
                    metadata={"platform": cv.platform, "unread": cv.unread_count},
                )
            )

        # 4. Search Messages
        msg_stmt = (
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == user_id,
                or_(
                    Message.message_content.ilike(q_like),
                    Message.sender.ilike(q_like),
                    Message.recipient.ilike(q_like),
                ),
            )
            .limit(limit)
        )
        msgs = (await db.execute(msg_stmt)).scalars().all()
        for m in msgs:
            results.append(
                GlobalSearchResultItem(
                    id=m.id,
                    entity_type="message",
                    title=f"Message ({m.platform.upper()})",
                    subtitle=f"From: {m.sender} → To: {m.recipient}",
                    snippet=m.message_content[:120] + "..." if len(m.message_content) > 120 else m.message_content,
                    url=f"/messages?conversation={m.conversation_id}",
                    metadata={"platform": m.platform, "direction": m.direction},
                )
            )

        return GlobalSearchResponse(
            query=query,
            total_results=len(results),
            results=results[:limit],
        )
