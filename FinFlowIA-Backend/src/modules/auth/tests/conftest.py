import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.auth.models import User
from src.modules.auth.repository import UserRepository
from src.modules.auth.service import AuthService


@pytest.fixture
def mock_user() -> User:
    user = User()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.hashed_password = "$2b$04$test_hash"  # low rounds for tests
    user.full_name = "Test User"
    user.is_active = True
    return user


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def auth_service(mock_repo: AsyncMock) -> AuthService:
    return AuthService(repo=mock_repo)
