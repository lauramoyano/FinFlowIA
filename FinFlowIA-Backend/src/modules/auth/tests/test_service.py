import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.auth.models import User
from src.modules.auth.schemas import LoginRequest, RegisterRequest
from src.modules.auth.service import AuthService
from src.shared.exceptions.base import AppException
from src.shared.exceptions.unauthorized import UnauthorizedException


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_creates_user_with_hashed_password(
        self, auth_service: AuthService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_email.return_value = None
        new_user = User()
        new_user.id = uuid.uuid4()
        new_user.email = "new@example.com"
        new_user.full_name = "New User"
        new_user.is_active = True
        new_user.hashed_password = "hashed"
        mock_repo.create.return_value = new_user

        request = RegisterRequest(
            email="new@example.com",
            password="securepassword123",
            full_name="New User",
        )
        result = await auth_service.register(request)

        mock_repo.create.assert_called_once()
        call_kwargs = mock_repo.create.call_args.kwargs
        # Password should be hashed, not stored plaintext
        assert call_kwargs["hashed_password"] != "securepassword123"
        assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_register_raises_if_email_already_exists(
        self, auth_service: AuthService, mock_repo: AsyncMock, mock_user: User
    ) -> None:
        mock_repo.get_by_email.return_value = mock_user

        request = RegisterRequest(
            email="test@example.com",
            password="password123",
            full_name="Test User",
        )

        with pytest.raises(AppException) as exc_info:
            await auth_service.register(request)

        assert exc_info.value.code == "EMAIL_ALREADY_EXISTS"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_login_raises_with_wrong_password(
        self, auth_service: AuthService, mock_repo: AsyncMock, mock_user: User
    ) -> None:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
        mock_user.hashed_password = ctx.hash("correct_password")
        mock_repo.get_by_email.return_value = mock_user

        request = LoginRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(UnauthorizedException):
            await auth_service.login(request)

    @pytest.mark.asyncio
    async def test_login_succeeds_with_correct_credentials(
        self, auth_service: AuthService, mock_repo: AsyncMock, mock_user: User
    ) -> None:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
        mock_user.hashed_password = ctx.hash("correct_password")
        mock_repo.get_by_email.return_value = mock_user

        request = LoginRequest(email="test@example.com", password="correct_password")
        result = await auth_service.login(request)

        assert result.access_token
        assert result.token_type == "bearer"
