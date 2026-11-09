import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.planning.models import (
    DistributionTemplate,
    DistributionTemplateItem,
    FinancialRecommendation,
    FinancialRecommendationItem,
)

logger = structlog.get_logger(__name__)

# Fixed default split until a dedicated management screen exists (see
# plan: "reparto fijo por ahora"). A real row in the user's own catalog,
# not a code constant, so a future customization UI needs zero migration.
DEFAULT_TEMPLATE_ITEMS: list[tuple[str, Decimal]] = [
    ("Reinversión", Decimal("40")),
    ("Ahorro", Decimal("20")),
    ("Utilidad", Decimal("40")),
]


class DistributionTemplateRepository:
    """Data access layer for a user's profit-distribution template."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _items_for(self, template_id: uuid.UUID) -> list[DistributionTemplateItem]:
        result = await self._session.execute(
            select(DistributionTemplateItem)
            .where(DistributionTemplateItem.template_id == template_id)
            .order_by(DistributionTemplateItem.order_index)
        )
        return list(result.scalars().all())

    async def get_or_create_default(
        self, user_id: uuid.UUID
    ) -> tuple[DistributionTemplate, list[DistributionTemplateItem]]:
        """
        Return the user's distribution template and its items, creating the
        default 40/20/40 Reinversión/Ahorro/Utilidad split on first use.
        No ORM relationship between the two (same convention as the rest of
        this codebase — relationships are resolved by the repository, not
        SQLAlchemy `relationship()`), so items are fetched separately.
        """
        result = await self._session.execute(
            select(DistributionTemplate)
            .where(DistributionTemplate.user_id == user_id)
            .order_by(DistributionTemplate.created_at)
            .limit(1)
        )
        template = result.scalar_one_or_none()
        if template is not None:
            return template, await self._items_for(template.id)

        template = DistributionTemplate(user_id=user_id, name="Mi reparto")
        self._session.add(template)
        await self._session.flush()

        for order_index, (label, percentage) in enumerate(DEFAULT_TEMPLATE_ITEMS):
            self._session.add(
                DistributionTemplateItem(
                    template_id=template.id,
                    label=label,
                    percentage=percentage,
                    order_index=order_index,
                )
            )
        await self._session.flush()

        logger.info("distribution_template_created", template_id=str(template.id), user_id=str(user_id))
        return template, await self._items_for(template.id)


class FinancialRecommendationRepository:
    """Data access layer for persisting a FinancialRecommendation and its items."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_with_items(
        self,
        user_id: uuid.UUID,
        distribution_template_id: uuid.UUID | None,
        sale_amount: Decimal,
        insumos_cost: Decimal | None,
        transporte_cost: Decimal | None,
        ayudante_cost: Decimal | None,
        gastos_adicionales: Decimal | None,
        servicios_publicos_cost: Decimal | None,
        estimated_savings: Decimal,
        estimated_business_balance: Decimal,
        items: list[dict[str, Any]],
    ) -> FinancialRecommendation:
        recommendation = FinancialRecommendation(
            user_id=user_id,
            distribution_template_id=distribution_template_id,
            sale_amount=sale_amount,
            insumos_cost=insumos_cost,
            transporte_cost=transporte_cost,
            ayudante_cost=ayudante_cost,
            gastos_adicionales=gastos_adicionales,
            servicios_publicos_cost=servicios_publicos_cost,
            estimated_savings=estimated_savings,
            estimated_business_balance=estimated_business_balance,
        )
        self._session.add(recommendation)
        await self._session.flush()

        for item in items:
            self._session.add(
                FinancialRecommendationItem(
                    recommendation_id=recommendation.id,
                    label=item["label"],
                    amount=item["amount"],
                    percentage=item["percentage"],
                )
            )
        await self._session.flush()

        logger.info(
            "financial_recommendation_created",
            recommendation_id=str(recommendation.id),
            user_id=str(user_id),
            sale_amount=str(sale_amount),
        )
        return recommendation
