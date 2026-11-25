import uuid

import structlog

from src.modules.transactions.category_repository import CategoryRepository
from src.modules.transactions.schemas import CategoryResponse, CreateCategoryRequest
from src.shared.exceptions.base import AppException
from src.shared.exceptions.not_found import NotFoundException
from src.shared.exceptions.unauthorized import ForbiddenException

logger = structlog.get_logger(__name__)


class CategoryService:
    """Business logic for managing transaction categories."""

    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def list_categories(
        self,
        user_id: uuid.UUID,
        transaction_type: str | None = None,
    ) -> list[CategoryResponse]:
        """List system default categories plus the user's own custom ones."""
        categories = await self._repo.list_for_user(user_id, transaction_type)
        return [CategoryResponse.model_validate(c) for c in categories]

    async def create_category(
        self,
        user_id: uuid.UUID,
        data: CreateCategoryRequest,
    ) -> CategoryResponse:
        """Create a custom category. Raises AppException on a name collision."""
        name = data.name.strip().lower()

        existing = await self._repo.get_by_name(
            user_id=user_id, name=name, transaction_type=data.transaction_type.value
        )
        if existing:
            raise AppException(
                message=f"Category '{name}' already exists for this transaction type",
                code="CATEGORY_ALREADY_EXISTS",
                status_code=409,
            )

        category = await self._repo.create(
            user_id=user_id,
            name=name,
            transaction_type=data.transaction_type.value,
            icon=data.icon,
        )
        logger.info("custom_category_created", user_id=str(user_id), category=name)
        return CategoryResponse.model_validate(category)

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        """Delete a user's custom category. System defaults can't be deleted."""
        category = await self._repo.get_by_id(category_id)
        if not category:
            raise NotFoundException("Category", category_id)
        if category.is_default:
            raise ForbiddenException("System default categories can't be deleted")
        if category.user_id != user_id:
            raise ForbiddenException("You don't have access to this category")

        await self._repo.delete(category_id)
        logger.info(
            "category_deleted", category_id=str(category_id), user_id=str(user_id)
        )
