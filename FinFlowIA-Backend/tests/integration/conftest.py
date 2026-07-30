"""Integration test configuration with real PostgreSQL database."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.database import get_db
from src.config.settings import settings
from src.shared.domain.base_entity import Base

# Derive the test database name from settings.database_url by replacing only
# the database component, not a blind string .replace() — the default user
# and database are both literally "financeai", so a naive substring replace
# also corrupts the username.
_test_url = make_url(settings.database_url)
TEST_DATABASE_URL = str(_test_url.set(database=f"{_test_url.database}_test"))


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test database engine and initialize schema, scoped per test function.

    Not session-scoped: pytest-asyncio 1.x gives each async test its own event
    loop by default, and an engine/connection pool created in one test's loop
    breaks ("another operation is in progress") when reused from another
    test's loop.
    """
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
