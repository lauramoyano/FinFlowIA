import uuid

import structlog

from src.modules.production.repository import ProductRepository
from src.modules.production.schemas import CreateProductRequest, ProductResponse, UpdateProductRequest
from src.shared.exceptions.base import AppException
from src.shared.exceptions.not_found import NotFoundException
from src.shared.exceptions.unauthorized import ForbiddenException

logger = structlog.get_logger(__name__)


class ProductService:
    """Business logic for managing a user's product catalog."""

    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    async def list_products(self, user_id: uuid.UUID) -> list[ProductResponse]:
        products = await self._repo.list_for_user(user_id)
        return [ProductResponse.model_validate(p) for p in products]

    async def create_product(
        self, user_id: uuid.UUID, data: CreateProductRequest
    ) -> ProductResponse:
        """Create a product. Raises AppException on a name collision for this user."""
        existing = await self._repo.get_by_name(user_id=user_id, name=data.name)
        if existing:
            raise AppException(
                message=f"Product '{data.name}' already exists",
                code="PRODUCT_ALREADY_EXISTS",
                status_code=409,
            )

        product = await self._repo.create(
            user_id=user_id,
            name=data.name,
            unit_insumos_cost=data.unit_insumos_cost,
            unit_label=data.unit_label,
            unit_sale_price=data.unit_sale_price,
        )
        logger.info("product_registered", user_id=str(user_id), product=data.name)
        return ProductResponse.model_validate(product)

    async def update_product(
        self, user_id: uuid.UUID, product_id: uuid.UUID, data: UpdateProductRequest
    ) -> ProductResponse:
        product = await self._repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Product", product_id)
        if product.user_id != user_id:
            raise ForbiddenException("You don't have access to this product")

        updated = await self._repo.update(
            product,
            name=data.name.strip().lower() if data.name else None,
            unit_label=data.unit_label,
            unit_insumos_cost=data.unit_insumos_cost,
            unit_sale_price=data.unit_sale_price,
            is_active=data.is_active,
        )
        return ProductResponse.model_validate(updated)

    async def delete_product(self, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
        product = await self._repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Product", product_id)
        if product.user_id != user_id:
            raise ForbiddenException("You don't have access to this product")

        await self._repo.delete(product_id)
        logger.info("product_deleted", product_id=str(product_id), user_id=str(user_id))
