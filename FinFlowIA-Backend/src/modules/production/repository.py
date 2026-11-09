import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.production.models import Product, ProductionEstimate, ProductionEstimateItem

logger = structlog.get_logger(__name__)


class ProductRepository:
    """Data access layer for Product entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[Product]:
        result = await self._session.execute(
            select(Product).where(Product.user_id == user_id).order_by(Product.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self._session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Product | None:
        """Case-insensitive lookup within this user's own catalog."""
        result = await self._session.execute(
            select(Product).where(
                Product.user_id == user_id, func.lower(Product.name) == name.strip().lower()
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        unit_insumos_cost: Decimal,
        unit_label: str | None = None,
        unit_sale_price: Decimal | None = None,
    ) -> Product:
        product = Product(
            user_id=user_id,
            name=name.strip().lower(),
            unit_label=unit_label,
            unit_insumos_cost=unit_insumos_cost,
            unit_sale_price=unit_sale_price,
            is_active=True,
        )
        self._session.add(product)
        await self._session.flush()
        logger.info("product_created", product_id=str(product.id), user_id=str(user_id))
        return product

    async def update(self, product: Product, **fields: object) -> Product:
        for key, value in fields.items():
            if value is not None:
                setattr(product, key, value)
        await self._session.flush()
        return product

    async def delete(self, product_id: uuid.UUID) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self._session.delete(product)
        await self._session.flush()
        return True


class ProductionEstimateRepository:
    """Data access layer for persisting a ProductionEstimate and its items."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_with_items(
        self,
        user_id: uuid.UUID,
        total_estimated_cost: Decimal,
        items: list[dict[str, Any]],
        llm_explanation: str | None = None,
    ) -> ProductionEstimate:
        estimate = ProductionEstimate(
            user_id=user_id,
            total_estimated_cost=total_estimated_cost,
            llm_explanation=llm_explanation,
        )
        self._session.add(estimate)
        await self._session.flush()

        for item in items:
            self._session.add(
                ProductionEstimateItem(
                    estimate_id=estimate.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_cost_snapshot=item["unit_cost"],
                    subtotal=item["subtotal"],
                )
            )
        await self._session.flush()

        logger.info(
            "production_estimate_created",
            estimate_id=str(estimate.id),
            user_id=str(user_id),
            total=str(total_estimated_cost),
        )
        return estimate

    async def latest_items_for_products(
        self, user_id: uuid.UUID, product_ids: list[uuid.UUID]
    ) -> list[ProductionEstimateItem]:
        """
        Items of the user's most recent estimate that includes any of
        `product_ids`, restricted to those products. Empty if none exists.
        """
        if not product_ids:
            return []
        latest = await self._session.execute(
            select(ProductionEstimate.id)
            .join(ProductionEstimateItem, ProductionEstimateItem.estimate_id == ProductionEstimate.id)
            .where(ProductionEstimate.user_id == user_id, ProductionEstimateItem.product_id.in_(product_ids))
            .order_by(ProductionEstimate.created_at.desc())
            .limit(1)
        )
        estimate_id = latest.scalar_one_or_none()
        if estimate_id is None:
            return []
        items = await self._session.execute(
            select(ProductionEstimateItem).where(
                ProductionEstimateItem.estimate_id == estimate_id,
                ProductionEstimateItem.product_id.in_(product_ids),
            )
        )
        return list(items.scalars().all())
