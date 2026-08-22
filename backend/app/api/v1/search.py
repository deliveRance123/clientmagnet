from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_global_search_service,
)
from app.models.user import User
from app.schemas.search import GlobalSearchResponse
from app.services.search import GlobalSearchService

router = APIRouter()


@router.get(
    "/",
    response_model=GlobalSearchResponse,
    summary="Global cross-entity search across leads, clients, conversations, and messages (user-isolated)",
)
async def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    search_service: GlobalSearchService = Depends(get_global_search_service),
):
    return await search_service.search(
        db=db, user_id=current_user.id, query=q, limit=limit
    )
