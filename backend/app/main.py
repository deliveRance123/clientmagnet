import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import check_db_connection
from app.api.v1.api import api_router

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifespan events."""
    # 1. Initialize Logging
    setup_logging()
    logger.info("Initializing Client Magnet Backend Foundation...")

    # 2. Test Database Connection Configuration
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("PostgreSQL pre-flight check passed.")
    else:
        logger.warning(
            "PostgreSQL pre-flight check failed. Backend will start, "
            "but DB operations will fail until connection is resolved."
        )

    yield

    logger.info("Stopping Client Magnet Backend...")

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set CORS origins with wildcard regex for all Render subdomains and localhost ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else ["*"],
    allow_origin_regex=r"https://.*\.onrender\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for general errors
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact support."},
    )


# Health Check Endpoint
@app.get("/health", tags=["health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
async def health_check():
    """Performs a basic liveness/readiness health check."""
    db_connected = await check_db_connection()
    return {
        "status": "OK" if db_connected else "DEGRADED",
        "database": "connected" if db_connected else "disconnected",
        "environment": settings.ENVIRONMENT,
        "project": settings.PROJECT_NAME,
    }

# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
