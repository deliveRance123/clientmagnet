import asyncio
from typing import AsyncGenerator, Generator
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add backend app to python path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.api.deps import get_db_session
from app.core.security import hash_password, create_access_token
from app.db.base_class import Base
from app.models.user import User
from app.main import app

# In-memory async SQLite for lightning-fast, fully isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Creates all database tables before each test and drops after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override for test database sessions."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Synchronous test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP test client for testing async FastAPI routes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides direct database session for test assertions."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Fixture providing an active test user in the test database."""
    user = User(
        email="test_crm_user@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="CRM Test User",
        company_name="Test Agency",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Fixture providing authorization bearer headers for test_user."""
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}
