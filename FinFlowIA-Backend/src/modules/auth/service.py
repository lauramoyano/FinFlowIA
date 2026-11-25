import uuid

import structlog
from passlib.context import CryptContext

from src.config.settings import settings
from src.infrastructure.security.jwt import create_access_token
from src.modules.auth.models import User
from src.modules.auth.repository import UserRepository
from src.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.shared.exceptions.base import AppException
from src.shared.exceptions.not_found import NotFoundException
from src.shared.exceptions.unauthorized import UnauthorizedException

logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)


class AuthService:
    """Business logic for authentication and user management."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def register(self, request: RegisterRequest) -> UserResponse:
        """Register a new user. Raises AppException if email already exists."""
        existing = await self._repo.get_by_email(request.email)
        if existing:
            raise AppException(
                message=f"Email '{request.email}' is already registered",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
            )

        hashed = self._hash_password(request.password)
        user = await self._repo.create(
            email=request.email,
            hashed_password=hashed,
            full_name=request.full_name,
        )

        logger.info("user_registered", user_id=str(user.id))
        return UserResponse.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user and return a JWT token."""
        user = await self._repo.get_by_email(request.email)

        if not user or not self._verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        token = create_access_token(subject=str(user.id))

        logger.info("user_logged_in", user_id=str(user.id))
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_expire_minutes * 60,
        )

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        """Retrieve the currently authenticated user's profile."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User", user_id)
        return UserResponse.model_validate(user)
