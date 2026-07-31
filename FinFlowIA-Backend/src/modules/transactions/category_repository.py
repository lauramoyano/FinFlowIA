import uuid

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.transactions.models import Category

logger = structlog.get_logger(__name__)


class CategoryRepository:
    """Data access layer for Category entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        transaction_type: str | None = None,
    ) -> list[Category]:
        """Return system default categories plus this user's own custom ones."""
        conditions = [or_(Category.user_id.is_(None), Category.user_id == user_id)]
        if transaction_type:
            conditions.append(Category.transaction_type == transaction_type)

        result = await self._session.execute(
            select(Category)
            .where(and_(*conditions))
            .order_by(Category.transaction_type, Category.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self._session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        user_id: uuid.UUID,
        name: str,
        transaction_type: str,
    ) -> Category | None:
        """
        Resolve a category by name visible to this user. If the user has a
        custom category with the same name as a system default, the custom
        one wins.
        """
        result = await self._session.execute(
            select(Category).where(
                and_(
                    or_(Category.user_id.is_(None), Category.user_id == user_id),
                    Category.name == name,
                    Category.transaction_type == transaction_type,
                )
            )
        )
        matches = list(result.scalars().all())
        custom = next((c for c in matches if c.user_id == user_id), None)
        return custom or (matches[0] if matches else None)

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        transaction_type: str,
        icon: str | None = None,
    ) -> Category:
        category = Category(
            user_id=user_id,
            name=name,
            transaction_type=transaction_type,
            icon=icon,
            is_default=False,
        )
        self._session.add(category)
        await self._session.flush()
        logger.info(
            "category_created", category_id=str(category.id), user_id=str(user_id)
        )
        return category

    async def delete(self, category_id: uuid.UUID) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self._session.delete(category)
        await self._session.flush()
        return True
