import logging
from typing import Dict
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session

logger = logging.getLogger("app.api.health")

router = APIRouter()


@router.get(
    "/health",
    summary="Production Health Check Endpoint",
    response_description="System and database connection health status",
)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, str]:
    """
    Public Health Check Endpoint for Render / Load Balancers.
    Checks PostgreSQL connectivity and returns a simple healthy payload without leaking internals.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check database failure: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
            },
        )
