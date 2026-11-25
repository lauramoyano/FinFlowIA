import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.production.models import Product
from src.modules.production.schemas import CreateProductRequest, UpdateProductRequest
from src.modules.production.service import ProductService
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
def product_service(mock_repo: AsyncMock) -> ProductService:
    return ProductService(repo=mock_repo)


def make_product(
    *,
    user_id: uuid.UUID | None = None,
    name: str = "torta",
    unit_insumos_cost: Decimal = Decimal("150.00"),
    unit_sale_price: Decimal | None = Decimal("250.00"),
    unit_label: str | None = None,
    is_active: bool = True,
) -> Product:
    p = Product()
    p.id = uuid.uuid4()
    p.user_id = user_id
    p.name = name
    p.unit_label = unit_label
    p.unit_insumos_cost = unit_insumos_cost
    p.unit_sale_price = unit_sale_price
    p.is_active = is_active
    return p


class TestProductService:
    @pytest.mark.asyncio
    async def test_list_products_delegates_to_repository(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.list_for_user.return_value = [make_product(user_id=user_id)]

        result = await product_service.list_products(user_id=user_id)

        assert len(result) == 1
        mock_repo.list_for_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_create_product_persists_via_repository(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.get_by_name.return_value = None
        mock_repo.create.return_value = make_product(user_id=user_id, name="torta")

        request = CreateProductRequest(
            name="torta", unit_insumos_cost=Decimal("150.00"), unit_sale_price=Decimal("250.00")
        )
        await product_service.create_product(user_id=user_id, data=request)

        mock_repo.create.assert_called_once_with(
            user_id=user_id,
            name="torta",
            unit_insumos_cost=Decimal("150.00"),
            unit_label=None,
            unit_sale_price=Decimal("250.00"),
        )

    @pytest.mark.asyncio
    async def test_create_product_raises_conflict_on_duplicate(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.get_by_name.return_value = make_product(user_id=user_id, name="torta")

        request = CreateProductRequest(
            name="torta", unit_insumos_cost=Decimal("150.00"), unit_sale_price=Decimal("250.00")
        )

        with pytest.raises(AppException) as exc_info:
            await product_service.create_product(user_id=user_id, data=request)

        assert exc_info.value.code == "PRODUCT_ALREADY_EXISTS"
        assert exc_info.value.status_code == 409
        mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_product_raises_not_found_for_missing_product(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await product_service.update_product(
                user_id=user_id, product_id=uuid.uuid4(), data=UpdateProductRequest()
            )

    @pytest.mark.asyncio
    async def test_update_product_raises_forbidden_for_other_users_product(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        other_user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_product(user_id=other_user_id)

        with pytest.raises(ForbiddenException):
            await product_service.update_product(
                user_id=user_id, product_id=uuid.uuid4(), data=UpdateProductRequest()
            )

        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_product_succeeds_for_owned_product(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        product_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_product(user_id=user_id)

        await product_service.delete_product(user_id=user_id, product_id=product_id)

        mock_repo.delete.assert_called_once_with(product_id)

    @pytest.mark.asyncio
    async def test_delete_product_raises_forbidden_for_other_users_product(
        self, product_service: ProductService, mock_repo: AsyncMock, user_id: uuid.UUID
    ) -> None:
        other_user_id = uuid.uuid4()
        mock_repo.get_by_id.return_value = make_product(user_id=other_user_id)

        with pytest.raises(ForbiddenException):
            await product_service.delete_product(user_id=user_id, product_id=uuid.uuid4())

        mock_repo.delete.assert_not_called()
