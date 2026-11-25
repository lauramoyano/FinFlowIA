import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.transactions.category_service import CategoryService
from src.modules.transactions.enums import TransactionType
from src.modules.transactions.models import Category
from src.modules.transactions.schemas import CreateCategoryRequest
from src.shared.exceptions.base import AppException
from src.shared.exceptions.not_found import NotFoundException
from src.shared.exceptions.unauthorized import ForbiddenException


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def category_service(mock_repo: AsyncMock) -> CategoryService:
    return CategoryService(repo=mock_repo)


def make_category(
    *,
    user_id: uuid.UUID | None = None,
    name: str = "food",
    transaction_type: str = "expense",
    is_default: bool = False,
) -> Category:
    c = Category()
    c.id = uuid.uuid4()
    c.user_id = user_id
    c.name = name
    c.transaction_type = transaction_type
    c.icon = None
    c.is_default = is_default
    return c


class TestCategoryService:
    @pytest.mark.asyncio
    async def test_list_categories_delegates_to_repository(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.list_for_user.return_value = [
            make_category(name="food", is_default=True),
            make_category(user_id=user_id, name="suscripciones"),
        ]

        result = await category_service.list_categories(user_id=user_id)

        assert len(result) == 2
        mock_repo.list_for_user.assert_called_once_with(user_id, None)

    @pytest.mark.asyncio
    async def test_create_category_normalizes_name_before_persisting(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.get_by_name.return_value = None
        mock_repo.create.return_value = make_category(
            user_id=user_id, name="suscripciones", transaction_type="expense"
        )

        request = CreateCategoryRequest(
            name="  Suscripciones  ", transaction_type=TransactionType.EXPENSE
        )
        await category_service.create_category(user_id=user_id, data=request)

        mock_repo.create.assert_called_once_with(
            user_id=user_id, name="suscripciones", transaction_type="expense", icon=None
        )

    @pytest.mark.asyncio
    async def test_create_category_raises_conflict_on_duplicate(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.get_by_name.return_value = make_category(name="food", is_default=True)

        request = CreateCategoryRequest(
            name="food", transaction_type=TransactionType.EXPENSE
        )

        with pytest.raises(AppException) as exc_info:
            await category_service.create_category(user_id=user_id, data=request)

        assert exc_info.value.code == "CATEGORY_ALREADY_EXISTS"
        assert exc_info.value.status_code == 409
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_category_raises_not_found_for_missing_category(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await category_service.delete_category(
                user_id=user_id, category_id=uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_delete_category_raises_forbidden_for_default_category(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.get_by_id.return_value = make_category(name="food", is_default=True)

        with pytest.raises(ForbiddenException):
            await category_service.delete_category(
                user_id=user_id, category_id=uuid.uuid4()
            )

        mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_category_raises_forbidden_for_other_users_category(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        other_user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_category(
            user_id=other_user_id, name="suscripciones"
        )

        with pytest.raises(ForbiddenException):
            await category_service.delete_category(
                user_id=user_id, category_id=uuid.uuid4()
            )

        mock_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_category_succeeds_for_owned_custom_category(
        self,
        category_service: CategoryService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        category_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_category(
            user_id=user_id, name="suscripciones"
        )

        await category_service.delete_category(user_id=user_id, category_id=category_id)

        mock_repo.delete.assert_called_once_with(category_id)
