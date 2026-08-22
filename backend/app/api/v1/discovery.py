import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_discovery_engine,
)
from app.models.discovery import LeadDiscoveryRun, LeadDiscoverySource
from app.models.user import User
from app.schemas.discovery import (
    CSVImportResult,
    DiscoveryRunOut,
    DiscoveryRunRequest,
    DiscoverySourceCreate,
    DiscoverySourceOut,
    DiscoverySourceUpdate,
    ManualLeadImportRequest,
)
from app.schemas.lead import LeadOut
from app.services.discovery import DiscoveryEngine

logger = logging.getLogger("app.api.discovery")

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Trigger Discovery Run
# ---------------------------------------------------------------------------
@router.post(
    "/run",
    response_model=List[DiscoveryRunOut],
    summary="Execute lead discovery across configured sources",
)
async def run_discovery(
    request: DiscoveryRunRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    engine: DiscoveryEngine = Depends(get_discovery_engine),
):
    """
    Triggers an opportunity scout run.
    Fetches raw postings, normalizes them, deduplicates against existing leads,
    enriches with Gemini AI analysis, and saves to PostgreSQL.
    """
    if request.source_id:
        query = select(LeadDiscoverySource).where(
            LeadDiscoverySource.id == request.source_id,
            LeadDiscoverySource.user_id == current_user.id,
        )
        source = (await db.execute(query)).scalar_one_or_none()
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discovery source not found.",
            )
        run = await engine.run_source(
            db=db,
            user=current_user,
            source=source,
            analyze_with_ai=request.analyze_with_ai,
        )
        return [run]
    else:
        runs = await engine.run_all_active_sources(
            db=db,
            user=current_user,
            analyze_with_ai=request.analyze_with_ai,
        )
        return runs


# ---------------------------------------------------------------------------
# 2. Source Management Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/sources",
    response_model=List[DiscoverySourceOut],
    summary="List user's configured discovery sources",
)
async def list_sources(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = (
        select(LeadDiscoverySource)
        .where(LeadDiscoverySource.user_id == current_user.id)
        .order_by(LeadDiscoverySource.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/sources",
    response_model=DiscoverySourceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new discovery source configuration",
)
async def create_source(
    data: DiscoverySourceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    source = LeadDiscoverySource(
        user_id=current_user.id,
        name=data.name.strip(),
        source_type=data.source_type.upper(),
        feed_url=data.feed_url.strip() if data.feed_url else None,
        config_json=data.config_json,
        frequency=data.frequency,
        is_active=data.is_active,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.get(
    "/sources/{source_id}",
    response_model=DiscoverySourceOut,
    summary="Get source details",
)
async def get_source(
    source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = select(LeadDiscoverySource).where(
        LeadDiscoverySource.id == source_id,
        LeadDiscoverySource.user_id == current_user.id,
    )
    source = (await db.execute(query)).scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery source not found.",
        )
    return source


@router.patch(
    "/sources/{source_id}",
    response_model=DiscoverySourceOut,
    summary="Update discovery source configuration",
)
async def update_source(
    source_id: str,
    data: DiscoverySourceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = select(LeadDiscoverySource).where(
        LeadDiscoverySource.id == source_id,
        LeadDiscoverySource.user_id == current_user.id,
    )
    source = (await db.execute(query)).scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery source not found.",
        )

    if data.name is not None:
        source.name = data.name.strip()
    if data.source_type is not None:
        source.source_type = data.source_type.upper()
    if data.feed_url is not None:
        source.feed_url = data.feed_url.strip() if data.feed_url else None
    if data.config_json is not None:
        source.config_json = data.config_json
    if data.frequency is not None:
        source.frequency = data.frequency
    if data.is_active is not None:
        source.is_active = data.is_active

    await db.commit()
    await db.refresh(source)
    return source


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a discovery source",
)
async def delete_source(
    source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = select(LeadDiscoverySource).where(
        LeadDiscoverySource.id == source_id,
        LeadDiscoverySource.user_id == current_user.id,
    )
    source = (await db.execute(query)).scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery source not found.",
        )
    await db.delete(source)
    await db.commit()


# ---------------------------------------------------------------------------
# 3. Discovery Run History
# ---------------------------------------------------------------------------
@router.get(
    "/runs",
    response_model=List[DiscoveryRunOut],
    summary="Retrieve discovery run history and metrics",
)
async def list_runs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    query = (
        select(LeadDiscoveryRun)
        .where(LeadDiscoveryRun.user_id == current_user.id)
        .order_by(LeadDiscoveryRun.started_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# 4. Manual & CSV Import Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/import",
    response_model=LeadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create a lead with optional AI enrichment",
)
async def import_manual_lead(
    data: ManualLeadImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    engine: DiscoveryEngine = Depends(get_discovery_engine),
):
    try:
        lead = await engine.import_manual_lead(
            db=db, user=current_user, request=data
        )
        return lead
    except ValueError as val_e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_e),
        )
    except Exception as e:
        logger.error(f"Error during manual lead import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import lead.",
        )


@router.post(
    "/import/csv",
    response_model=CSVImportResult,
    summary="Bulk import leads from a CSV file with duplicate and validation checking",
)
async def import_csv_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    engine: DiscoveryEngine = Depends(get_discovery_engine),
):
    try:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8-sig", errors="replace")
        result = await engine.import_csv_leads(
            db=db, user=current_user, csv_content=csv_text, analyze_with_ai=False
        )
        return result
    except Exception as e:
        logger.error(f"Error processing CSV file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file or formatting error: {str(e)}",
        )
