import math
import uuid
from decimal import Decimal
from typing import Any

import structlog

from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.parsing import parse_decimal
from src.modules.orchestrator.agents.types import (
    AgentResult,
    ProductionEstimateResult,
    ProductionEstimateResultItem,
    SalesGoalItem,
    SalesGoalResult,
)
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.orchestrator.product_memory import ProductMemory
from src.modules.production.models import Product
from src.shared.utils.text_utils import split_product_names
from src.modules.production.repository import ProductionEstimateRepository, ProductRepository

logger = structlog.get_logger(__name__)

MAX_FOLLOWUP_TURNS = 3


class ProductionEstimateAgent:
    """
    Agent 3: conversational production planning. Two calculations, both
    backed by the same product catalog and both computed here
    deterministically (the LLM only extracts intent, never a number):

    - Cost-by-quantity: "cuánto me cuesta hacer 10 tortas" → resolves each
      item against the catalog, asking for a missing product's insumos
      cost on the fly if needed.
    - Sales goal: "quiero vender 2.000.000 en la feria" → minimum units to
      sell to hit a revenue target, the insumos investment needed, and the
      projected profit. Several products ("alfajores y tortas") split the
      target evenly. Needs each product's sale price — asked for
      conversationally only when this calculation needs it (new product,
      or an existing one without a price yet).

    Products are resolved through the shared ProductMemory, so plural /
    near-miss names match the catalog, and a genuinely new product's cost
    question mentions any past expenses already tied to it.
    """

    def __init__(
        self,
        ai_service: AIService,
        product_repo: ProductRepository,
        estimate_repo: ProductionEstimateRepository,
        memory: ProductMemory,
        store: ConversationStore,
    ) -> None:
        self._ai_service = ai_service
        self._product_repo = product_repo
        self._estimate_repo = estimate_repo
        self._memory = memory
        self._store = store

    async def handle(
        self, text: str, conversation_id: str, is_followup: bool, user_id: uuid.UUID
    ) -> AgentResult:
        if is_followup:
            state = await self._store.get(conversation_id)
            assert state is not None, "caller must only pass is_followup=True when state exists"
            turns = state.turns + 1
            awaiting = state.payload.get("awaiting")

            if awaiting == "unit_cost":
                return await self._handle_unit_cost_followup(
                    text, conversation_id, turns, state.payload, user_id
                )
            if awaiting == "sales_goal_product":
                goal_amount = Decimal(state.payload["goal_amount"])
                # The reply is free text ("me gustaría vender tortas y
                # alfajores no más"), so let the extractor pull the names
                # out instead of treating the whole sentence as one product.
                parsed = await self._ai_service.parse_production_estimate_text(
                    f"quiero vender {goal_amount}. {text}"
                )
                if parsed.sales_goal is not None:
                    names = parsed.sales_goal.product_names
                elif parsed.error == "provider_unavailable":
                    names = split_product_names(text)
                else:
                    names = []
                if not names:
                    return await self._retry_or_give_up(
                        conversation_id, state, turns, "ask_which_product", None, "sales_goal_product"
                    )
                return await self._advance_sales_goal(goal_amount, names, [], conversation_id, 1, user_id)
            if awaiting == "sales_goal_unit_cost":
                return await self._handle_sales_goal_unit_cost_followup(
                    text, conversation_id, turns, state.payload, user_id
                )
            if awaiting == "sales_goal_sale_price":
                return await self._handle_sales_goal_sale_price_followup(
                    text, conversation_id, turns, state.payload, user_id
                )

            accumulated = f"{state.payload['accumulated_text']}. {text}"
            return await self._extract_and_resolve(accumulated, conversation_id, turns, user_id)

        return await self._extract_and_resolve(text, conversation_id, 1, user_id)

    async def _extract_and_resolve(
        self, text: str, conversation_id: str, turns: int, user_id: uuid.UUID
    ) -> AgentResult:
        parsed = await self._ai_service.parse_production_estimate_text(text)

        if parsed.sales_goal is not None:
            goal = parsed.sales_goal
            if goal.product_names:
                return await self._advance_sales_goal(
                    goal.amount, goal.product_names, [], conversation_id, turns, user_id
                )
            await self._store.set(
                conversation_id,
                ConversationState(
                    agent="production_estimate",
                    turns=turns,
                    payload={"awaiting": "sales_goal_product", "goal_amount": str(goal.amount)},
                ),
            )
            return AgentResult(kind="question", message="ask_which_product")

        if parsed.error or not parsed.items:
            if turns < MAX_FOLLOWUP_TURNS:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="production_estimate",
                        turns=turns,
                        payload={"awaiting": "items", "accumulated_text": text},
                    ),
                )
                return AgentResult(kind="question", message="ask_product_quantity")
            await self._store.clear(conversation_id)
            logger.info("production_estimate_agent_gave_up", stage="items", turns=turns)
            return AgentResult(kind="error", error_code="follow_up_retry_limit")

        remaining_items = [{"product_name": item.product_name, "quantity": item.quantity} for item in parsed.items]
        return await self._resolve_items(
            resolved_items=[], remaining_items=remaining_items,
            conversation_id=conversation_id, turns=turns, user_id=user_id,
        )

    async def _resolve_items(
        self,
        resolved_items: list[dict[str, Any]],
        remaining_items: list[dict[str, Any]],
        conversation_id: str,
        turns: int,
        user_id: uuid.UUID,
    ) -> AgentResult:
        while remaining_items:
            item = remaining_items[0]
            product = await self._memory.find_product(user_id, item["product_name"])

            if product is None:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="production_estimate",
                        turns=turns,
                        payload={
                            "awaiting": "unit_cost",
                            "pending_item": item,
                            "resolved_items": resolved_items,
                            "remaining_items": remaining_items[1:],
                        },
                    ),
                )
                return await self._ask_unit_cost(item["product_name"], user_id)

            unit_cost = product.unit_insumos_cost
            subtotal = unit_cost * item["quantity"]
            resolved_items.append(
                {
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "quantity": item["quantity"],
                    "unit_cost": str(unit_cost),
                    "subtotal": str(subtotal),
                    "unit_sale_price": str(product.unit_sale_price) if product.unit_sale_price is not None else None,
                }
            )
            remaining_items = remaining_items[1:]

        return await self._finalize(resolved_items, conversation_id, user_id)

    async def _handle_unit_cost_followup(
        self, text: str, conversation_id: str, turns: int, payload: dict[str, Any], user_id: uuid.UUID
    ) -> AgentResult:
        pending = payload["pending_item"]
        cost = parse_decimal(text)

        if cost is None:
            if turns < MAX_FOLLOWUP_TURNS:
                await self._store.set(
                    conversation_id,
                    ConversationState(agent="production_estimate", turns=turns, payload=payload),
                )
                return AgentResult(
                    kind="question",
                    message="ask_unit_cost",
                    message_params={"product": pending["product_name"]},
                )
            await self._store.clear(conversation_id)
            logger.info("production_estimate_agent_gave_up", stage="unit_cost", turns=turns)
            return AgentResult(kind="error", error_code="follow_up_retry_limit")

        # Plain cost-by-quantity never needs a sale price, so this product
        # is created without one — it gets backfilled later only if a
        # sales-goal calculation ever needs it (see _handle_sales_goal_*).
        product = await self._product_repo.create(
            user_id=user_id, name=pending["product_name"], unit_insumos_cost=cost
        )
        subtotal = cost * pending["quantity"]
        resolved_items = payload["resolved_items"] + [
            {
                "product_id": str(product.id),
                "product_name": product.name,
                "quantity": pending["quantity"],
                "unit_cost": str(cost),
                "subtotal": str(subtotal),
                "unit_sale_price": None,
            }
        ]
        return await self._resolve_items(
            resolved_items=resolved_items,
            remaining_items=payload["remaining_items"],
            conversation_id=conversation_id,
            turns=turns,
            user_id=user_id,
        )

    async def _finalize(
        self, resolved_items: list[dict[str, Any]], conversation_id: str, user_id: uuid.UUID
    ) -> AgentResult:
        total = sum((Decimal(i["subtotal"]) for i in resolved_items), Decimal("0"))

        await self._estimate_repo.create_with_items(
            user_id=user_id,
            total_estimated_cost=total,
            items=[
                {
                    "product_id": uuid.UUID(i["product_id"]),
                    "quantity": i["quantity"],
                    "unit_cost": Decimal(i["unit_cost"]),
                    "subtotal": Decimal(i["subtotal"]),
                }
                for i in resolved_items
            ],
        )
        await self._store.clear(conversation_id)

        projected_revenue = None
        estimated_profit = None
        if all(i.get("unit_sale_price") for i in resolved_items):
            projected_revenue = sum(
                (Decimal(i["unit_sale_price"]) * i["quantity"] for i in resolved_items), Decimal("0")
            )
            estimated_profit = projected_revenue - total

        return AgentResult(
            kind="estimate_result",
            estimate=ProductionEstimateResult(
                items=[
                    ProductionEstimateResultItem(
                        product_name=i["product_name"],
                        quantity=i["quantity"],
                        unit_cost=Decimal(i["unit_cost"]),
                        subtotal=Decimal(i["subtotal"]),
                    )
                    for i in resolved_items
                ],
                total_estimated_cost=total,
                projected_revenue=projected_revenue,
                estimated_profit=estimated_profit,
            ),
        )

    async def _ask_unit_cost(self, product_name: str, user_id: uuid.UUID) -> AgentResult:
        """
        Ask for a new product's per-unit insumos cost. If past expenses
        already mention it, say so — the user can reuse that knowledge
        instead of starting from zero.
        """
        history = await self._memory.expense_history(user_id, product_name)
        if history is None:
            return AgentResult(
                kind="question", message="ask_unit_cost", message_params={"product": product_name}
            )
        return AgentResult(
            kind="question",
            message="ask_unit_cost_with_history",
            message_params={
                "product": product_name,
                "count": str(history.count),
                "total": str(history.total),
            },
        )

    async def _retry_or_give_up(
        self,
        conversation_id: str,
        state: ConversationState,
        turns: int,
        question_code: str,
        question_params: dict[str, str] | None,
        stage: str,
    ) -> AgentResult:
        if turns < MAX_FOLLOWUP_TURNS:
            await self._store.set(
                conversation_id,
                ConversationState(agent="production_estimate", turns=turns, payload=state.payload),
            )
            return AgentResult(kind="question", message=question_code, message_params=question_params)
        await self._store.clear(conversation_id)
        logger.info("production_estimate_agent_gave_up", stage=stage, turns=turns)
        return AgentResult(kind="error", error_code="follow_up_retry_limit")

    async def _advance_sales_goal(
        self,
        goal_amount: Decimal,
        names: list[str],
        resolved_ids: list[str],
        conversation_id: str,
        turns: int,
        user_id: uuid.UUID,
    ) -> AgentResult:
        """
        Walk the queue of named products, asking only for what each one is
        missing (cost if unknown, sale price if unset). Once every product
        is resolved, compute the goal.
        """
        while names:
            name, rest = names[0], names[1:]
            product = await self._memory.find_product(user_id, name)

            if product is None:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="production_estimate",
                        turns=turns,
                        payload={
                            "awaiting": "sales_goal_unit_cost",
                            "goal_amount": str(goal_amount),
                            "current": {"name": name, "unit_cost": None},
                            "pending_names": rest,
                            "resolved_ids": resolved_ids,
                        },
                    ),
                )
                return await self._ask_unit_cost(name, user_id)

            if product.unit_sale_price is None:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="production_estimate",
                        turns=turns,
                        payload={
                            "awaiting": "sales_goal_sale_price",
                            "goal_amount": str(goal_amount),
                            "current": {"name": product.name, "unit_cost": None},
                            "pending_names": rest,
                            "resolved_ids": resolved_ids,
                        },
                    ),
                )
                return AgentResult(
                    kind="question", message="ask_sale_price", message_params={"product": product.name}
                )

            if str(product.id) not in resolved_ids:
                resolved_ids = [*resolved_ids, str(product.id)]
            names = rest

        return await self._finalize_sales_goal(goal_amount, resolved_ids, conversation_id, user_id)

    async def _handle_sales_goal_unit_cost_followup(
        self, text: str, conversation_id: str, turns: int, payload: dict[str, Any], user_id: uuid.UUID
    ) -> AgentResult:
        name = payload["current"]["name"]
        cost = parse_decimal(text)

        if cost is None:
            return await self._retry_or_give_up(
                conversation_id,
                ConversationState(agent="production_estimate", turns=turns, payload=payload),
                turns,
                "ask_unit_cost",
                {"product": name},
                "sales_goal_unit_cost",
            )

        await self._store.set(
            conversation_id,
            ConversationState(
                agent="production_estimate",
                turns=1,
                payload={
                    **payload,
                    "awaiting": "sales_goal_sale_price",
                    "current": {"name": name, "unit_cost": str(cost)},
                },
            ),
        )
        return AgentResult(kind="question", message="ask_sale_price", message_params={"product": name})

    async def _handle_sales_goal_sale_price_followup(
        self, text: str, conversation_id: str, turns: int, payload: dict[str, Any], user_id: uuid.UUID
    ) -> AgentResult:
        name = payload["current"]["name"]
        price = parse_decimal(text)

        if price is None:
            return await self._retry_or_give_up(
                conversation_id,
                ConversationState(agent="production_estimate", turns=turns, payload=payload),
                turns,
                "ask_sale_price",
                {"product": name},
                "sales_goal_sale_price",
            )

        pending_unit_cost = payload["current"].get("unit_cost")
        product: Product
        if pending_unit_cost is not None:
            product = await self._product_repo.create(
                user_id=user_id,
                name=name,
                unit_insumos_cost=Decimal(pending_unit_cost),
                unit_sale_price=price,
            )
        else:
            existing = await self._memory.find_product(user_id, name)
            assert existing is not None, "product must still exist between asking for its price and the reply"
            product = await self._product_repo.update(existing, unit_sale_price=price)

        return await self._advance_sales_goal(
            Decimal(payload["goal_amount"]),
            payload["pending_names"],
            [*payload["resolved_ids"], str(product.id)],
            conversation_id,
            1,
            user_id,
        )

    async def _finalize_sales_goal(
        self, goal_amount: Decimal, product_ids: list[str], conversation_id: str, user_id: uuid.UUID
    ) -> AgentResult:
        # Target revenue is split evenly across the named products.
        share = goal_amount / len(product_ids)
        goal_items: list[SalesGoalItem] = []
        estimate_items: list[dict[str, Any]] = []

        for product_id in product_ids:
            product = await self._product_repo.get_by_id(uuid.UUID(product_id))
            assert product is not None and product.unit_sale_price is not None
            quantity = math.ceil(share / product.unit_sale_price)
            investment = quantity * product.unit_insumos_cost
            revenue = quantity * product.unit_sale_price
            goal_items.append(
                SalesGoalItem(
                    product_name=product.name,
                    quantity_needed=quantity,
                    unit_sale_price=product.unit_sale_price,
                    unit_insumos_cost=product.unit_insumos_cost,
                    insumos_investment=investment,
                    projected_revenue=revenue,
                    estimated_profit=revenue - investment,
                )
            )
            estimate_items.append(
                {
                    "product_id": product.id,
                    "quantity": quantity,
                    "unit_cost": product.unit_insumos_cost,
                    "subtotal": investment,
                }
            )

        total_investment = sum((i.insumos_investment for i in goal_items), Decimal("0"))
        total_revenue = sum((i.projected_revenue for i in goal_items), Decimal("0"))

        await self._estimate_repo.create_with_items(
            user_id=user_id, total_estimated_cost=total_investment, items=estimate_items
        )
        await self._store.clear(conversation_id)

        return AgentResult(
            kind="sales_goal_result",
            sales_goal_result=SalesGoalResult(
                goal_amount=goal_amount,
                items=goal_items,
                insumos_investment=total_investment,
                projected_revenue=total_revenue,
                estimated_profit=total_revenue - total_investment,
            ),
        )
