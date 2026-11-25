import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import User

logger = structlog.get_logger(__name__)


class UserRepository:
    """Data access layer for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address."""
        result = await self._session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their UUID."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()  # Get the generated ID without committing

        logger.info("user_created", user_id=str(user.id), email=email)
        return user

    async def update_active_status(self, user_id: uuid.UUID, is_active: bool) -> User | None:
        """Enable or disable a user account."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = is_active
            await self._session.flush()
        return user
