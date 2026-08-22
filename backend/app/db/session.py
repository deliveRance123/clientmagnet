import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger("app.db")

db_url = settings.DATABASE_URL
engine_kwargs = {"pool_pre_ping": True}

if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
    })

try:
    engine = create_async_engine(db_url, **engine_kwargs)
except Exception as e:
    logger.warning(f"Could not initialize primary database engine: {e}. Using fallback in-memory test engine.")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

# Async session factory
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector yielding database sessions."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Utility function to test database connectivity at startup."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection verified successfully.")
            return True
    except Exception as e:
        logger.warning(
            "Could not connect to database. Make sure PostgreSQL is running. "
            f"Error details: {str(e)}"
        )
        return False
