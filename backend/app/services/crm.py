import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.conversation import Conversation
from app.models.follow_up import FollowUp
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.service import Service
from app.models.user import User
from app.schemas.crm import (
    ClientCreate,
    ClientOut,
    ClientUpdate,
    ConversionFunnelMetrics,
    CRMAnalyticsResponse,
    CRMDashboardMetrics,
    LeadConvertToClientRequest,
    LeadStageUpdate,
    ServicePerformanceItem,
    SourcePerformanceItem,
    VALID_CLIENT_STATUSES,
    VALID_LEAD_STAGES,
)
from app.services.activity import ActivityService

logger = logging.getLogger("app.services.crm")


class CRMService:
    """Core CRM, Lead Pipeline, Client Management & PostgreSQL Business Analytics Service."""

    def __init__(self, activity_service: Optional[ActivityService] = None):
        self.activity_service = activity_service or ActivityService()

    # -----------------------------------------------------------------------
    # 1. Lead Pipeline Management
    # -----------------------------------------------------------------------

    async def update_lead_stage(
        self,
        db: AsyncSession,
        user: User,
        lead_id: str,
        stage_update: LeadStageUpdate,
    ) -> Lead:
        """Transitions a lead to a new pipeline stage and logs activity."""
        target_stage = stage_update.stage.upper().strip()
        if target_stage not in VALID_LEAD_STAGES:
            raise ValueError(
                f"Invalid pipeline stage '{target_stage}'. Must be one of: {', '.join(VALID_LEAD_STAGES)}"
            )

        stmt = select(Lead).where(Lead.id == lead_id, Lead.user_id == user.id)
        lead = (await db.execute(stmt)).scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found or does not belong to the current user.")

        old_stage = lead.status
        lead.status = target_stage
        lead.updated_at = datetime.now(timezone.utc)
        if stage_update.notes:
            existing_notes = lead.notes or ""
            lead.notes = f"{existing_notes}\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] Stage changed to {target_stage}: {stage_update.notes}".strip()

        # Log transition activity
        await self.activity_service.log_activity(
            db=db,
            user_id=user.id,
            lead_id=lead.id,
            event_type="STATUS_CHANGED",
            channel="crm",
            description=f"Lead stage transitioned from '{old_stage}' to '{target_stage}'",
            metadata={"old_stage": old_stage, "new_stage": target_stage, "notes": stage_update.notes},
        )

        # Notify if Won or Hot
        if target_stage == "WON":
            db.add(
                Notification(
                    user_id=user.id,
                    title="🎉 Deal Won!",
                    message=f"Lead '{lead.name}' ({lead.company or 'Direct'}) was marked as WON. Ready to convert to Client.",
                    notification_type="NEW_LEAD",
                    link_url=f"/clients",
                )
            )

        await db.commit()
        await db.refresh(lead)
        return lead

    async def convert_lead_to_client(
        self,
        db: AsyncSession,
        user: User,
        lead_id: str,
        req: LeadConvertToClientRequest,
    ) -> ClientOut:
        """
        Converts a won lead into a permanent Client record.
        Maintains Lead entity history and conversation linkages.
        """
        stmt = (
            select(Lead)
            .options(selectinload(Lead.matched_service))
            .where(Lead.id == lead_id, Lead.user_id == user.id)
        )
        lead = (await db.execute(stmt)).scalar_one_or_none()
        if not lead:
            raise ValueError("Lead not found or unauthorized.")

        # Check if already converted
        existing_client_stmt = select(Client).where(Client.lead_id == lead.id, Client.user_id == user.id)
        existing_client = (await db.execute(existing_client_stmt)).scalar_one_or_none()
        if existing_client:
            return ClientOut.from_orm_client(existing_client)

        # Validate status
        status_val = req.status.upper().strip()
        if status_val not in VALID_CLIENT_STATUSES:
            status_val = "ACTIVE"

        # Determine service
        service_id = req.service_id or lead.matched_service_id
        service_purchased = req.service_purchased or (lead.matched_service.name if lead.matched_service else None)

        client = Client(
            user_id=user.id,
            lead_id=lead.id,
            service_id=service_id,
            name=lead.name,
            company=lead.company,
            email=lead.email,
            phone=lead.phone,
            website=lead.website,
            service_purchased=service_purchased,
            status=status_val,
            notes=req.notes or f"Converted from lead on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(client)
        await db.flush()

        # Update lead status to WON if not already
        if lead.status != "WON":
            lead.status = "WON"
            lead.updated_at = datetime.now(timezone.utc)

        # Link existing conversations to this client
        conv_stmt = select(Conversation).where(Conversation.lead_id == lead.id, Conversation.user_id == user.id)
        convs = (await db.execute(conv_stmt)).scalars().all()
        for c in convs:
            c.client_id = client.id

        # Log Activity
        await self.activity_service.log_activity(
            db=db,
            user_id=user.id,
            lead_id=lead.id,
            client_id=client.id,
            event_type="CLIENT_WON",
            channel="crm",
            description=f"Converted lead '{lead.name}' into active Client with service: {service_purchased or 'General Services'}",
            metadata={"client_id": client.id, "service_purchased": service_purchased},
        )

        await db.commit()
        await db.refresh(client)
        return ClientOut.from_orm_client(client)

    # -----------------------------------------------------------------------
    # 2. Client Management (CRUD)
    # -----------------------------------------------------------------------

    async def list_clients(
        self,
        db: AsyncSession,
        user_id: str,
        status_filter: Optional[str] = None,
        service_id_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[ClientOut]:
        """Lists all clients belonging to the user."""
        stmt = (
            select(Client)
            .options(selectinload(Client.service))
            .where(Client.user_id == user_id)
        )

        if status_filter and status_filter.upper() != "ALL":
            stmt = stmt.where(Client.status == status_filter.upper())

        if service_id_filter:
            stmt = stmt.where(Client.service_id == service_id_filter)

        if search_query:
            q = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    Client.name.ilike(q),
                    Client.company.ilike(q),
                    Client.email.ilike(q),
                    Client.phone.ilike(q),
                )
            )

        stmt = stmt.order_by(Client.created_at.desc())
        clients = (await db.execute(stmt)).scalars().all()
        return [ClientOut.from_orm_client(c) for c in clients]

    async def get_client(
        self, db: AsyncSession, user_id: str, client_id: str
    ) -> Optional[ClientOut]:
        """Retrieves a single client by ID."""
        stmt = (
            select(Client)
            .options(selectinload(Client.service))
            .where(Client.id == client_id, Client.user_id == user_id)
        )
        client = (await db.execute(stmt)).scalar_one_or_none()
        if not client:
            return None
        return ClientOut.from_orm_client(client)

    async def create_client(
        self, db: AsyncSession, user: User, data: ClientCreate
    ) -> ClientOut:
        """Creates a new Client record directly."""
        status_val = data.status.upper().strip()
        if status_val not in VALID_CLIENT_STATUSES:
            status_val = "ACTIVE"

        client = Client(
            user_id=user.id,
            lead_id=data.lead_id,
            service_id=data.service_id,
            name=data.name.strip(),
            company=data.company.strip() if data.company else None,
            email=data.email.strip() if data.email else None,
            phone=data.phone.strip() if data.phone else None,
            website=data.website.strip() if data.website else None,
            service_purchased=data.service_purchased,
            status=status_val,
            notes=data.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

        await self.activity_service.log_activity(
            db=db,
            user_id=user.id,
            client_id=client.id,
            event_type="CLIENT_CREATED",
            channel="crm",
            description=f"Client '{client.name}' created manually.",
        )

        return ClientOut.from_orm_client(client)

    async def update_client(
        self, db: AsyncSession, user: User, client_id: str, data: ClientUpdate
    ) -> ClientOut:
        """Updates an existing Client."""
        stmt = select(Client).where(Client.id == client_id, Client.user_id == user.id)
        client = (await db.execute(stmt)).scalar_one_or_none()
        if not client:
            raise ValueError("Client not found or unauthorized.")

        if data.name is not None:
            client.name = data.name.strip()
        if data.company is not None:
            client.company = data.company.strip() or None
        if data.email is not None:
            client.email = data.email.strip() or None
        if data.phone is not None:
            client.phone = data.phone.strip() or None
        if data.website is not None:
            client.website = data.website.strip() or None
        if data.service_id is not None:
            client.service_id = data.service_id
        if data.service_purchased is not None:
            client.service_purchased = data.service_purchased
        if data.status is not None:
            status_val = data.status.upper().strip()
            if status_val in VALID_CLIENT_STATUSES:
                client.status = status_val
        if data.notes is not None:
            client.notes = data.notes

        client.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(client)
        return ClientOut.from_orm_client(client)

    # -----------------------------------------------------------------------
    # 3. CRM Dashboard & PostgreSQL Analytics
    # -----------------------------------------------------------------------

    async def get_dashboard_metrics(
        self, db: AsyncSession, user_id: str
    ) -> CRMDashboardMetrics:
        """Computes live CRM dashboard metrics directly via PostgreSQL."""
        # 1. Leads counts by status
        lead_status_stmt = (
            select(Lead.status, func.count(Lead.id))
            .where(Lead.user_id == user_id)
            .group_by(Lead.status)
        )
        status_rows = (await db.execute(lead_status_stmt)).all()
        leads_by_status = {r[0]: r[1] for r in status_rows}

        total_leads = sum(leads_by_status.values())
        qualified_leads = leads_by_status.get("QUALIFIED", 0)
        won_deals = leads_by_status.get("WON", 0)
        lost_deals = leads_by_status.get("LOST", 0)

        # 2. Active Conversations
        conv_stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id, Conversation.status.in_(["ACTIVE", "OPEN"])
        )
        active_conversations = (await db.execute(conv_stmt)).scalar() or 0

        # 3. Follow-ups Due
        now = datetime.now(timezone.utc)
        fu_stmt = select(func.count(FollowUp.id)).where(
            FollowUp.user_id == user_id,
            FollowUp.status.in_(["Pending", "Drafted", "Approved"]),
            FollowUp.scheduled_time <= now,
        )
        follow_ups_due = (await db.execute(fu_stmt)).scalar() or 0

        # 4. Active Clients
        client_stmt = select(func.count(Client.id)).where(
            Client.user_id == user_id, Client.status == "ACTIVE"
        )
        active_clients = (await db.execute(client_stmt)).scalar() or 0

        # 5. Leads by Service
        leads_svc_stmt = (
            select(Service.name, func.count(Lead.id))
            .join(Service, Lead.matched_service_id == Service.id)
            .where(Lead.user_id == user_id)
            .group_by(Service.name)
        )
        svc_rows = (await db.execute(leads_svc_stmt)).all()
        leads_by_service = {r[0]: r[1] for r in svc_rows}

        # 6. Leads by Source
        leads_src_stmt = (
            select(Lead.source, func.count(Lead.id))
            .where(Lead.user_id == user_id)
            .group_by(Lead.source)
        )
        src_rows = (await db.execute(leads_src_stmt)).all()
        leads_by_source = {r[0]: r[1] for r in src_rows}

        # 7. Clients by Service
        clients_svc_stmt = (
            select(
                func.coalesce(Service.name, Client.service_purchased, "General Services"),
                func.count(Client.id),
            )
            .outerjoin(Service, Client.service_id == Service.id)
            .where(Client.user_id == user_id)
            .group_by(Service.name, Client.service_purchased)
        )
        cl_svc_rows = (await db.execute(clients_svc_stmt)).all()
        clients_by_service = {r[0]: r[1] for r in cl_svc_rows}

        return CRMDashboardMetrics(
            total_leads=total_leads,
            qualified_leads=qualified_leads,
            active_conversations=active_conversations,
            follow_ups_due=follow_ups_due,
            active_clients=active_clients,
            won_deals=won_deals,
            lost_deals=lost_deals,
            leads_by_service=leads_by_service,
            leads_by_source=leads_by_source,
            leads_by_status=leads_by_status,
            clients_by_service=clients_by_service,
        )

    async def get_analytics(
        self, db: AsyncSession, user_id: str
    ) -> CRMAnalyticsResponse:
        """Computes comprehensive business conversion funnel and service/source ROI."""
        # 1. Total & Status Counts
        lead_status_stmt = (
            select(Lead.status, func.count(Lead.id))
            .where(Lead.user_id == user_id)
            .group_by(Lead.status)
        )
        status_rows = (await db.execute(lead_status_stmt)).all()
        st_map = {r[0]: r[1] for r in status_rows}

        total_leads = sum(st_map.values())
        new_leads = st_map.get("NEW", 0)
        qualified_leads = st_map.get("QUALIFIED", 0)
        contacted_leads = st_map.get("CONTACTED", 0)
        replied_leads = st_map.get("REPLIED", 0)
        won_leads = st_map.get("WON", 0)
        lost_leads = st_map.get("LOST", 0)

        # Hot leads count (intent_score >= 0.7)
        hot_stmt = select(func.count(Lead.id)).where(
            Lead.user_id == user_id, Lead.intent_score >= 0.7
        )
        hot_leads = (await db.execute(hot_stmt)).scalar() or 0

        # 2. Conversion Funnel (Safe division: never divide by zero)
        lead_to_qual = (qualified_leads / total_leads * 100.0) if total_leads > 0 else 0.0
        qual_to_contact = (contacted_leads / qualified_leads * 100.0) if qualified_leads > 0 else 0.0
        contact_to_reply = (replied_leads / contacted_leads * 100.0) if contacted_leads > 0 else 0.0
        reply_to_won = (won_leads / replied_leads * 100.0) if replied_leads > 0 else 0.0
        overall_to_won = (won_leads / total_leads * 100.0) if total_leads > 0 else 0.0

        funnel = ConversionFunnelMetrics(
            lead_to_qualified_pct=round(lead_to_qual, 1),
            qualified_to_contacted_pct=round(qual_to_contact, 1),
            contacted_to_replied_pct=round(contact_to_reply, 1),
            replied_to_won_pct=round(reply_to_won, 1),
            overall_lead_to_won_pct=round(overall_to_won, 1),
        )

        # 3. Service Performance
        services_stmt = select(Service).where(Service.user_id == user_id)
        services = (await db.execute(services_stmt)).scalars().all()

        service_performance: List[ServicePerformanceItem] = []
        for svc in services:
            # Count leads for this service
            s_leads_stmt = select(func.count(Lead.id)).where(
                Lead.user_id == user_id, Lead.matched_service_id == svc.id
            )
            s_total_leads = (await db.execute(s_leads_stmt)).scalar() or 0

            s_qual_stmt = select(func.count(Lead.id)).where(
                Lead.user_id == user_id,
                Lead.matched_service_id == svc.id,
                Lead.status == "QUALIFIED",
            )
            s_qual_leads = (await db.execute(s_qual_stmt)).scalar() or 0

            s_won_stmt = select(func.count(Lead.id)).where(
                Lead.user_id == user_id,
                Lead.matched_service_id == svc.id,
                Lead.status == "WON",
            )
            s_won_deals = (await db.execute(s_won_stmt)).scalar() or 0

            s_clients_stmt = select(func.count(Client.id)).where(
                Client.user_id == user_id, Client.service_id == svc.id
            )
            s_clients = (await db.execute(s_clients_stmt)).scalar() or 0

            service_performance.append(
                ServicePerformanceItem(
                    service_name=svc.name,
                    service_id=svc.id,
                    total_leads=s_total_leads,
                    qualified_leads=s_qual_leads,
                    clients_count=s_clients,
                    won_deals=s_won_deals,
                )
            )

        # 4. Source Performance
        sources_stmt = (
            select(Lead.source, func.count(Lead.id))
            .where(Lead.user_id == user_id)
            .group_by(Lead.source)
        )
        sources_rows = (await db.execute(sources_stmt)).all()

        source_performance: List[SourcePerformanceItem] = []
        for src_name, src_total in sources_rows:
            # Qualified for this source
            src_qual_stmt = select(func.count(Lead.id)).where(
                Lead.user_id == user_id,
                Lead.source == src_name,
                Lead.status == "QUALIFIED",
            )
            src_qual = (await db.execute(src_qual_stmt)).scalar() or 0

            # Clients from this source (via Lead linkage)
            src_clients_stmt = (
                select(func.count(Client.id))
                .join(Lead, Client.lead_id == Lead.id)
                .where(Client.user_id == user_id, Lead.source == src_name)
            )
            src_clients = (await db.execute(src_clients_stmt)).scalar() or 0

            source_performance.append(
                SourcePerformanceItem(
                    source_name=src_name,
                    total_leads=src_total,
                    qualified_leads=src_qual,
                    clients_count=src_clients,
                )
            )

        return CRMAnalyticsResponse(
            total_leads=total_leads,
            new_leads=new_leads,
            qualified_leads=qualified_leads,
            hot_leads=hot_leads,
            contacted_leads=contacted_leads,
            replied_leads=replied_leads,
            won_leads=won_leads,
            lost_leads=lost_leads,
            conversion_funnel=funnel,
            service_performance=service_performance,
            source_performance=source_performance,
        )
