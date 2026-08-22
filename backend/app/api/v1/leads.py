from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user, get_db_session
from app.models.client import Client
from app.models.lead import Lead
from app.models.service import Service
from app.models.user import User
from app.schemas.lead import (
    LeadCreate,
    LeadOut,
    LeadSource,
    LeadStatsSummary,
    LeadStatus,
    LeadUpdate,
)

router = APIRouter()


@router.get(
    "/stats/summary",
    response_model=LeadStatsSummary,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated statistics for the dashboard",
)
async def get_lead_stats_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Computes dashboard metrics via PostgreSQL queries for the authenticated user.
    """
    # Total Leads
    total_q = select(func.count(Lead.id)).where(Lead.user_id == current_user.id)
    total_leads = (await db.execute(total_q)).scalar() or 0

    # New Leads
    new_q = select(func.count(Lead.id)).where(
        Lead.user_id == current_user.id, Lead.status == LeadStatus.NEW.value
    )
    new_leads = (await db.execute(new_q)).scalar() or 0

    # Qualified Leads
    qualified_q = select(func.count(Lead.id)).where(
        Lead.user_id == current_user.id, Lead.status == LeadStatus.QUALIFIED.value
    )
    qualified_leads = (await db.execute(qualified_q)).scalar() or 0

    # Interested Leads
    interested_q = select(func.count(Lead.id)).where(
        Lead.user_id == current_user.id, Lead.status == LeadStatus.INTERESTED.value
    )
    interested_leads = (await db.execute(interested_q)).scalar() or 0

    # Won Clients (check clients table count or leads with WON status)
    clients_q = select(func.count(Client.id)).where(Client.user_id == current_user.id)
    won_clients_count = (await db.execute(clients_q)).scalar() or 0
    if won_clients_count == 0:
        won_leads_q = select(func.count(Lead.id)).where(
            Lead.user_id == current_user.id, Lead.status == LeadStatus.WON.value
        )
        won_clients_count = (await db.execute(won_leads_q)).scalar() or 0

    return LeadStatsSummary(
        total_leads=total_leads,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        interested_leads=interested_leads,
        won_clients=won_clients_count,
    )


@router.get(
    "/",
    response_model=List[LeadOut],
    status_code=status.HTTP_200_OK,
    summary="List, search, filter, and sort leads belonging to the authenticated user",
)
async def get_leads(
    search: Optional[str] = Query(None, description="Search by name, company, email, or need"),
    status_filter: Optional[LeadStatus] = Query(None, alias="status", description="Filter by status"),
    source_filter: Optional[LeadSource] = Query(None, alias="source", description="Filter by source"),
    matched_service_id: Optional[str] = Query(None, description="Filter by matched service ID"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, intent_score, name, status)"),
    sort_dir: str = Query("desc", description="Sort direction (asc, desc)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves all leads owned by the authenticated user with filtering, searching, and sorting.
    Enforces strict multi-tenant user isolation.
    """
    query = (
        select(Lead)
        .options(selectinload(Lead.matched_service))
        .where(Lead.user_id == current_user.id)
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Lead.name.ilike(term),
                Lead.company.ilike(term),
                Lead.email.ilike(term),
                Lead.detected_need.ilike(term),
                Lead.description.ilike(term),
            )
        )

    if status_filter:
        query = query.where(Lead.status == status_filter.value)

    if source_filter:
        query = query.where(Lead.source == source_filter.value)

    if matched_service_id:
        query = query.where(Lead.matched_service_id == matched_service_id)

    # Sorting
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_dir.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    result = await db.execute(query)
    leads = result.scalars().all()
    return [LeadOut.model_validate(lead) for lead in leads]


@router.post(
    "/",
    response_model=LeadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead for the authenticated user",
)
async def create_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Creates a new lead associated strictly with the authenticated user.
    """
    # If a matched_service_id is provided, verify it belongs to the current user
    if lead_in.matched_service_id:
        svc_q = select(Service).where(
            Service.id == lead_in.matched_service_id,
            Service.user_id == current_user.id,
        )
        svc_res = await db.execute(svc_q)
        if not svc_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected matched service does not exist or belong to your account.",
            )

    new_lead = Lead(
        user_id=current_user.id,
        name=lead_in.name.strip(),
        company=lead_in.company.strip() if lead_in.company else None,
        email=lead_in.email.strip().lower() if lead_in.email else None,
        phone=lead_in.phone.strip() if lead_in.phone else None,
        website=lead_in.website.strip() if lead_in.website else None,
        platform=lead_in.platform.strip() if lead_in.platform else None,
        profile_url=lead_in.profile_url.strip() if lead_in.profile_url else None,
        location=lead_in.location.strip() if lead_in.location else None,
        source=lead_in.source.value if isinstance(lead_in.source, LeadSource) else str(lead_in.source),
        source_url=lead_in.source_url.strip() if lead_in.source_url else None,
        description=lead_in.description.strip() if lead_in.description else None,
        detected_need=lead_in.detected_need.strip() if lead_in.detected_need else None,
        matched_service_id=lead_in.matched_service_id,
        intent_score=lead_in.intent_score,
        status=lead_in.status.value if isinstance(lead_in.status, LeadStatus) else str(lead_in.status),
        notes=lead_in.notes.strip() if lead_in.notes else None,
    )
    db.add(new_lead)
    await db.commit()

    # Re-query with eager loading
    reloaded_q = (
        select(Lead)
        .options(selectinload(Lead.matched_service))
        .where(Lead.id == new_lead.id)
    )
    reloaded = (await db.execute(reloaded_q)).scalar_one()
    return LeadOut.model_validate(reloaded)


@router.get(
    "/{lead_id}",
    response_model=LeadOut,
    status_code=status.HTTP_200_OK,
    summary="Get lead details by ID (enforcing user isolation)",
)
async def get_lead_by_id(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a lead by ID only if it belongs to the authenticated user.
    Returns 404 if the lead does not exist or belongs to a different user.
    """
    query = (
        select(Lead)
        .options(selectinload(Lead.matched_service))
        .where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    result = await db.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied.",
        )

    return LeadOut.model_validate(lead)


@router.patch(
    "/{lead_id}",
    response_model=LeadOut,
    status_code=status.HTTP_200_OK,
    summary="Update a lead",
)
async def update_lead(
    lead_id: str,
    lead_in: LeadUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Updates a lead owned by the authenticated user.
    """
    query = (
        select(Lead)
        .options(selectinload(Lead.matched_service))
        .where(Lead.id == lead_id, Lead.user_id == current_user.id)
    )
    result = await db.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied.",
        )

    update_data = lead_in.model_dump(exclude_unset=True)

    # If matched_service_id is provided and changing, verify ownership
    if "matched_service_id" in update_data and update_data["matched_service_id"]:
        svc_q = select(Service).where(
            Service.id == update_data["matched_service_id"],
            Service.user_id == current_user.id,
        )
        svc_res = await db.execute(svc_q)
        if not svc_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected matched service does not exist or belong to your account.",
            )

    for field, value in update_data.items():
        if isinstance(value, (LeadStatus, LeadSource)):
            value = value.value
        elif isinstance(value, str):
            value = value.strip()
        setattr(lead, field, value)

    await db.commit()

    reloaded_q = (
        select(Lead)
        .options(selectinload(Lead.matched_service))
        .where(Lead.id == lead.id)
    )
    reloaded = (await db.execute(reloaded_q)).scalar_one()
    return LeadOut.model_validate(reloaded)


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lead",
)
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deletes a lead owned by the authenticated user.
    """
    query = select(Lead).where(
        Lead.id == lead_id, Lead.user_id == current_user.id
    )
    result = await db.execute(query)
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or access denied.",
        )

    await db.delete(lead)
    await db.commit()
    return None
