import uuid
from decimal import Decimal
from typing import Any

import structlog

from src.modules.ai.schemas import ParsedRecommendationCosts
from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.types import (
    AgentResult,
    FinancialRecommendationResult,
    FinancialRecommendationResultItem,
)
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.orchestrator.product_memory import ProductMemory
from src.modules.planning.repository import DistributionTemplateRepository, FinancialRecommendationRepository
from src.modules.transactions.repository import TransactionRepository

logger = structlog.get_logger(__name__)

MAX_FOLLOWUP_TURNS = 3


class FinancialRecommendationAgent:
    """
    Agent 4: conversational reparto recommendation. Given the amount of a
    sale/cobro and its associated costs, computes the net amount and splits
    it across the user's distribution template (a fixed 40/20/40
    Reinversión/Ahorro/Utilidad default until a customization screen
    exists — see DistributionTemplateRepository). All math happens here,
    deterministically; the LLM only extracts the amount and cost breakdown,
    never computes a number itself.

    When the message names a preparation that already has an estimate
    (e.g. "vendí 200000 de tortas" after estimating tortas), the insumos
    cost is recalled from that estimate instead of being asked again, so
    the sale is tied to the cost it was planned with and the net amount is
    the real profit.
    """

    def __init__(
        self,
        ai_service: AIService,
        template_repo: DistributionTemplateRepository,
        recommendation_repo: FinancialRecommendationRepository,
        transaction_repo: TransactionRepository,
        memory: ProductMemory,
        store: ConversationStore,
    ) -> None:
        self._ai_service = ai_service
        self._template_repo = template_repo
        self._recommendation_repo = recommendation_repo
        self._transaction_repo = transaction_repo
        self._memory = memory
        self._store = store

    async def handle(
        self, text: str, conversation_id: str, is_followup: bool, user_id: uuid.UUID
    ) -> AgentResult:
        if is_followup:
            state = await self._store.get(conversation_id)
            assert state is not None, "caller must only pass is_followup=True when state exists"
            turns = state.turns + 1

            if state.payload.get("awaiting") == "costs":
                sale_amount = Decimal(state.payload["sale_amount"])
                costs = await self._ai_service.parse_recommendation_costs_text(text)
                linked = state.payload.get("linked_insumos")
                return await self._finalize(sale_amount, costs, conversation_id, user_id, linked)

            accumulated = f"{state.payload['accumulated_text']}. {text}"
            return await self._extract_amount_and_continue(accumulated, conversation_id, turns, user_id)

        return await self._extract_amount_and_continue(text, conversation_id, 1, user_id)

    async def _extract_amount_and_continue(
        self, text: str, conversation_id: str, turns: int, user_id: uuid.UUID
    ) -> AgentResult:
        parsed = await self._ai_service.parse_sale_amount_text(text)

        if parsed.error or parsed.amount is None:
            if turns < MAX_FOLLOWUP_TURNS:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="financial_recommendation",
                        turns=turns,
                        payload={"awaiting": "sale_amount", "accumulated_text": text},
                    ),
                )
                return AgentResult(kind="question", message="ask_sale_amount")
            await self._store.clear(conversation_id)
            logger.info("financial_recommendation_agent_gave_up", stage="sale_amount", turns=turns)
            return AgentResult(kind="error", error_code="follow_up_retry_limit")

        payload: dict[str, Any] = {"awaiting": "costs", "sale_amount": str(parsed.amount)}
        linked = await self._memory.linked_insumos(user_id, text)
        if linked is not None:
            payload["linked_insumos"] = {
                "products": linked.product_names,
                "insumos_cost": str(linked.insumos_cost),
            }
        await self._store.set(
            conversation_id,
            ConversationState(agent="financial_recommendation", turns=turns, payload=payload),
        )
        if linked is not None:
            return AgentResult(
                kind="question",
                message="ask_recommendation_costs_linked",
                message_params={
                    "product": ", ".join(linked.product_names),
                    "insumos": str(linked.insumos_cost),
                },
            )
        return AgentResult(kind="question", message="ask_recommendation_costs")

    async def _finalize(
        self,
        sale_amount: Decimal,
        costs: ParsedRecommendationCosts,
        conversation_id: str,
        user_id: uuid.UUID,
        linked: dict[str, Any] | None = None,
    ) -> AgentResult:
        insumos_linked_products: list[str] | None = None
        if linked is not None and costs.insumos_cost is None:
            costs.insumos_cost = Decimal(linked["insumos_cost"])
            insumos_linked_products = linked["products"]

        cost_fields: dict[str, Decimal | None] = {
            "insumos_cost": costs.insumos_cost,
            "transporte_cost": costs.transporte_cost,
            "ayudante_cost": costs.ayudante_cost,
            "gastos_adicionales": costs.gastos_adicionales,
            "servicios_publicos_cost": costs.servicios_publicos_cost,
        }
        total_costs = sum((v for v in cost_fields.values() if v is not None), Decimal("0"))
        net_amount = sale_amount - total_costs

        template, template_items = await self._template_repo.get_or_create_default(user_id)
        items: list[dict[str, Any]] = [
            {
                "label": item.label,
                "percentage": item.percentage,
                "amount": (net_amount * item.percentage / Decimal("100")).quantize(Decimal("0.01")),
            }
            for item in template_items
        ]
        estimated_savings = next(
            (i["amount"] for i in items if "ahorro" in i["label"].lower()), Decimal("0")
        )
        estimated_business_balance = net_amount - estimated_savings
        pending_debt_total = await self._transaction_repo.get_pending_debt_total(user_id)

        await self._recommendation_repo.create_with_items(
            user_id=user_id,
            distribution_template_id=template.id,
            sale_amount=sale_amount,
            estimated_savings=estimated_savings,
            estimated_business_balance=estimated_business_balance,
            items=items,
            **cost_fields,
        )
        await self._store.clear(conversation_id)

        return AgentResult(
            kind="financial_recommendation_result",
            financial_recommendation_result=FinancialRecommendationResult(
                items=[
                    FinancialRecommendationResultItem(
                        label=i["label"], amount=i["amount"], percentage=i["percentage"]
                    )
                    for i in items
                ],
                sale_amount=sale_amount,
                total_costs=total_costs,
                net_amount=net_amount,
                estimated_savings=estimated_savings,
                estimated_business_balance=estimated_business_balance,
                pending_debt_total=pending_debt_total,
                insumos_linked_products=insumos_linked_products,
            ),
        )
