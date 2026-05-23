"""Integration test configuration with real PostgreSQL database."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.database import get_db
from src.config.settings import settings
from src.shared.domain.base_entity import Base

# Use test database URL from .env.test
TEST_DATABASE_URL = settings.database_url.replace("/financeai", "/financeai_test")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine and initialize schema."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for each test, rolled back on cleanup."""
    TestSessionFactory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with database session override."""
    from src.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a test user and return authorization headers."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "integration@test.com",
            "password": "testpassword123",
            "full_name": "Integration Test User",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "integration@test.com", "password": "testpassword123"},
    )

    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
