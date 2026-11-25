import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.ai.schemas import (
    ParsedProductionEstimateItem,
    ParsedProductionEstimateResult,
    ParsedSalesGoal,
)
from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.production_estimate_agent import ProductionEstimateAgent
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.orchestrator.product_memory import ProductMemory
from src.modules.production.repository import ProductionEstimateRepository, ProductRepository
from src.modules.transactions.repository import TransactionRepository

USER_ID = uuid.uuid4()


@pytest.fixture
def mock_ai_service() -> AsyncMock:
    return AsyncMock(spec=AIService)


@pytest.fixture
def mock_product_repo() -> AsyncMock:
    return AsyncMock(spec=ProductRepository)


@pytest.fixture
def mock_estimate_repo() -> AsyncMock:
    return AsyncMock(spec=ProductionEstimateRepository)


@pytest.fixture
def mock_transaction_repo() -> AsyncMock:
    repo = AsyncMock(spec=TransactionRepository)
    repo.search_expenses_by_description.return_value = []
    return repo


@pytest.fixture
def mock_store() -> AsyncMock:
    return AsyncMock(spec=ConversationStore)


@pytest.fixture
def agent(
    mock_ai_service: AsyncMock,
    mock_product_repo: AsyncMock,
    mock_estimate_repo: AsyncMock,
    mock_transaction_repo: AsyncMock,
    mock_store: AsyncMock,
) -> ProductionEstimateAgent:
    mock_product_repo.list_for_user.return_value = []
    return ProductionEstimateAgent(
        ai_service=mock_ai_service,
        product_repo=mock_product_repo,
        estimate_repo=mock_estimate_repo,
        memory=ProductMemory(mock_product_repo, mock_estimate_repo, mock_transaction_repo),
        store=mock_store,
    )


def make_product(
    name: str, unit_insumos_cost: Decimal, unit_sale_price: Decimal | None = None
) -> MagicMock:
    product = MagicMock()
    product.id = uuid.uuid4()
    product.name = name
    product.unit_insumos_cost = unit_insumos_cost
    product.unit_sale_price = unit_sale_price
    return product


class TestProductionEstimateAgent:
    @pytest.mark.asyncio
    async def test_no_items_parsed_asks_followup_and_saves_state(
        self, agent: ProductionEstimateAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[], error="no_items"
        )

        result = await agent.handle("no sé qué estimar", "conv-1", is_followup=False, user_id=USER_ID)

        assert result.kind == "question"
        assert result.message == "ask_product_quantity"
        mock_store.set.assert_called_once()
        saved_conversation_id, saved_state = mock_store.set.call_args.args
        assert saved_conversation_id == "conv-1"
        assert saved_state == ConversationState(
            agent="production_estimate",
            turns=1,
            payload={"awaiting": "items", "accumulated_text": "no sé qué estimar"},
        )

    @pytest.mark.asyncio
    async def test_all_items_found_computes_and_persists(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[ParsedProductionEstimateItem(product_name="torta", quantity=10)]
        )
        mock_product_repo.get_by_name.return_value = make_product("torta", Decimal("150.00"))

        result = await agent.handle(
            "cuánto me cuesta hacer 10 tortas", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "estimate_result"
        assert result.estimate is not None
        assert result.estimate.total_estimated_cost == Decimal("1500.00")
        assert len(result.estimate.items) == 1
        assert result.estimate.items[0].subtotal == Decimal("1500.00")
        mock_estimate_repo.create_with_items.assert_called_once()
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_missing_product_asks_for_unit_cost_with_params(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[ParsedProductionEstimateItem(product_name="torta", quantity=10)]
        )
        mock_product_repo.get_by_name.return_value = None

        result = await agent.handle(
            "cuánto me cuesta hacer 10 tortas", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_unit_cost"
        assert result.message_params == {"product": "torta"}
        mock_store.set.assert_called_once()
        _, saved_state = mock_store.set.call_args.args
        assert saved_state.payload["awaiting"] == "unit_cost"
        assert saved_state.payload["pending_item"] == {"product_name": "torta", "quantity": 10}
        assert saved_state.payload["remaining_items"] == []

    @pytest.mark.asyncio
    async def test_followup_with_valid_cost_creates_product_and_finalizes(
        self,
        agent: ProductionEstimateAgent,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=1,
            payload={
                "awaiting": "unit_cost",
                "pending_item": {"product_name": "torta", "quantity": 10},
                "resolved_items": [],
                "remaining_items": [],
            },
        )
        mock_product_repo.create.return_value = make_product("torta", Decimal("150.00"))

        result = await agent.handle("150", "conv-1", is_followup=True, user_id=USER_ID)

        mock_product_repo.create.assert_called_once_with(
            user_id=USER_ID, name="torta", unit_insumos_cost=Decimal("150")
        )
        assert result.kind == "estimate_result"
        assert result.estimate is not None
        assert result.estimate.total_estimated_cost == Decimal("1500")
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_followup_with_invalid_cost_reasks(
        self, agent: ProductionEstimateAgent, mock_product_repo: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=1,
            payload={
                "awaiting": "unit_cost",
                "pending_item": {"product_name": "torta", "quantity": 10},
                "resolved_items": [],
                "remaining_items": [],
            },
        )

        result = await agent.handle("no sé cuánto", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "question"
        assert result.message == "ask_unit_cost"
        assert result.message_params == {"product": "torta"}
        mock_product_repo.create.assert_not_called()
        mock_store.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_items_retry_limit_exceeded_returns_error(
        self, agent: ProductionEstimateAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=2,
            payload={"awaiting": "items", "accumulated_text": "no sé qué estimar. tampoco"},
        )
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[], error="no_items"
        )

        result = await agent.handle("sigo sin saber", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_store.set.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_unit_cost_retry_limit_exceeded_returns_error(
        self, agent: ProductionEstimateAgent, mock_product_repo: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=2,
            payload={
                "awaiting": "unit_cost",
                "pending_item": {"product_name": "torta", "quantity": 10},
                "resolved_items": [],
                "remaining_items": [],
            },
        )

        result = await agent.handle("ni idea", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_product_repo.create.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")


class TestSalesGoal:
    @pytest.mark.asyncio
    async def test_known_product_with_price_resolves_in_one_turn(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("2000000"), product_names=["torta"])
        )
        torta = make_product("torta", Decimal("150.00"), unit_sale_price=Decimal("250.00"))
        mock_product_repo.get_by_name.return_value = torta
        mock_product_repo.get_by_id.return_value = torta

        result = await agent.handle(
            "quiero vender 2000000 de tortas en la feria", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "sales_goal_result"
        assert result.sales_goal_result is not None
        sg = result.sales_goal_result
        assert sg.items[0].product_name == "torta"
        assert sg.items[0].quantity_needed == 8000  # ceil(2_000_000 / 250)
        assert sg.insumos_investment == Decimal("1200000.00")  # 8000 * 150
        assert sg.projected_revenue == Decimal("2000000.00")  # 8000 * 250
        assert sg.estimated_profit == Decimal("800000.00")
        mock_estimate_repo.create_with_items.assert_called_once()
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_no_product_named_asks_which_then_resolves(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("2000000"), product_names=[])
        )

        result = await agent.handle(
            "quiero vender 2000000 en la feria", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_which_product"
        mock_store.set.assert_called_once()
        _, saved_state = mock_store.set.call_args.args
        assert saved_state.payload == {"awaiting": "sales_goal_product", "goal_amount": "2000000"}

        mock_store.get.return_value = saved_state
        torta = make_product("torta", Decimal("150.00"), unit_sale_price=Decimal("250.00"))
        mock_product_repo.get_by_name.return_value = torta
        mock_product_repo.get_by_id.return_value = torta

        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("2000000"), product_names=["torta"])
        )

        follow_up = await agent.handle("torta", "conv-1", is_followup=True, user_id=USER_ID)

        assert follow_up.kind == "sales_goal_result"
        assert follow_up.sales_goal_result is not None
        assert follow_up.sales_goal_result.items[0].quantity_needed == 8000

    @pytest.mark.asyncio
    async def test_existing_product_missing_price_asks_only_price_and_updates(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("500000"), product_names=["pan"])
        )
        mock_product_repo.get_by_name.return_value = make_product(
            "pan", Decimal("30.00"), unit_sale_price=None
        )

        result = await agent.handle(
            "quiero vender 500000 de pan", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_sale_price"
        assert result.message_params == {"product": "pan"}
        _, saved_state = mock_store.set.call_args.args
        assert saved_state.payload["awaiting"] == "sales_goal_sale_price"
        assert saved_state.payload["current"] == {"name": "pan", "unit_cost": None}

        mock_store.get.return_value = saved_state
        updated_product = make_product("pan", Decimal("30.00"), unit_sale_price=Decimal("50.00"))
        mock_product_repo.update.return_value = updated_product
        mock_product_repo.get_by_id.return_value = updated_product

        follow_up = await agent.handle("50", "conv-1", is_followup=True, user_id=USER_ID)

        mock_product_repo.create.assert_not_called()
        mock_product_repo.update.assert_called_once()
        assert follow_up.kind == "sales_goal_result"
        assert follow_up.sales_goal_result is not None
        assert follow_up.sales_goal_result.items[0].quantity_needed == 10000  # ceil(500000 / 50)
        mock_estimate_repo.create_with_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_brand_new_product_asks_cost_then_price_and_creates(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("100000"), product_names=["alfajor"])
        )
        mock_product_repo.get_by_name.return_value = None

        result = await agent.handle(
            "quiero vender 100000 de alfajores", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_unit_cost"
        assert result.message_params == {"product": "alfajor"}
        _, state_after_ask_cost = mock_store.set.call_args.args
        assert state_after_ask_cost.payload["awaiting"] == "sales_goal_unit_cost"

        mock_store.get.return_value = state_after_ask_cost
        cost_reply = await agent.handle("20", "conv-1", is_followup=True, user_id=USER_ID)

        assert cost_reply.kind == "question"
        assert cost_reply.message == "ask_sale_price"
        mock_product_repo.create.assert_not_called()
        _, state_after_ask_price = mock_store.set.call_args.args
        assert state_after_ask_price.payload["awaiting"] == "sales_goal_sale_price"
        assert state_after_ask_price.payload["current"] == {"name": "alfajor", "unit_cost": "20"}

        mock_store.get.return_value = state_after_ask_price
        alfajor = make_product("alfajor", Decimal("20"), unit_sale_price=Decimal("40"))
        mock_product_repo.create.return_value = alfajor
        mock_product_repo.get_by_id.return_value = alfajor
        price_reply = await agent.handle("40", "conv-1", is_followup=True, user_id=USER_ID)

        mock_product_repo.create.assert_called_once_with(
            user_id=USER_ID, name="alfajor", unit_insumos_cost=Decimal("20"), unit_sale_price=Decimal("40")
        )
        assert price_reply.kind == "sales_goal_result"
        assert price_reply.sales_goal_result is not None
        assert price_reply.sales_goal_result.items[0].quantity_needed == 2500  # ceil(100000 / 40)
        mock_estimate_repo.create_with_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_sale_price_retry_limit_exceeded_returns_error(
        self, agent: ProductionEstimateAgent, mock_product_repo: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=2,
            payload={
                "awaiting": "sales_goal_sale_price",
                "goal_amount": "500000",
                "current": {"name": "pan", "unit_cost": None},
                "pending_names": [],
                "resolved_ids": [],
            },
        )

        result = await agent.handle("no sé", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_product_repo.create.assert_not_called()
        mock_product_repo.update.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")


class TestSharedMemoryAndMultiProduct:
    @pytest.mark.asyncio
    async def test_several_products_split_goal_and_ask_each_missing_one(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        # "alfajores y tortas" must never be looked up as a single product.
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("2000000"), product_names=["alfajor", "torta"])
        )
        torta = make_product("torta", Decimal("150"), unit_sale_price=Decimal("250"))
        mock_product_repo.get_by_name.side_effect = lambda _uid, name: torta if name == "torta" else None
        mock_product_repo.get_by_id.return_value = torta

        asked = await agent.handle(
            "quiero vender 2000000 en la feria", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert asked.message == "ask_unit_cost"
        assert asked.message_params == {"product": "alfajor"}
        _, state = mock_store.set.call_args.args
        assert state.payload["pending_names"] == ["torta"]

        mock_store.get.return_value = state
        priced = await agent.handle("20", "conv-1", is_followup=True, user_id=USER_ID)
        assert priced.message == "ask_sale_price"

        _, state = mock_store.set.call_args.args
        mock_store.get.return_value = state
        alfajor = make_product("alfajor", Decimal("20"), unit_sale_price=Decimal("40"))
        mock_product_repo.create.return_value = alfajor
        mock_product_repo.get_by_id.side_effect = lambda pid: alfajor if pid == alfajor.id else torta

        done = await agent.handle("40", "conv-1", is_followup=True, user_id=USER_ID)

        assert done.kind == "sales_goal_result"
        sg = done.sales_goal_result
        assert sg is not None
        by_name = {i.product_name: i for i in sg.items}
        assert by_name["alfajor"].quantity_needed == 25000  # ceil(1_000_000 / 40)
        assert by_name["torta"].quantity_needed == 4000  # ceil(1_000_000 / 250)
        assert sg.estimated_profit == sg.projected_revenue - sg.insumos_investment
        mock_estimate_repo.create_with_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_free_text_product_reply_is_parsed_into_names(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=1,
            payload={"awaiting": "sales_goal_product", "goal_amount": "300000"},
        )
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            sales_goal=ParsedSalesGoal(amount=Decimal("300000"), product_names=["torta", "alfajor"])
        )
        mock_product_repo.get_by_name.return_value = None

        result = await agent.handle(
            "me gustaría vender tortas y alfajores no más", "conv-1", is_followup=True, user_id=USER_ID
        )

        assert result.message == "ask_unit_cost"
        assert result.message_params == {"product": "torta"}
        _, state = mock_store.set.call_args.args
        assert state.payload["pending_names"] == ["alfajor"]

    @pytest.mark.asyncio
    async def test_unparseable_product_reply_reasks(
        self, agent: ProductionEstimateAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="production_estimate",
            turns=1,
            payload={"awaiting": "sales_goal_product", "goal_amount": "300000"},
        )
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            error="no_items"
        )

        result = await agent.handle("no sé", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.message == "ask_which_product"

    @pytest.mark.asyncio
    async def test_plural_name_matches_singular_catalog_product(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[ParsedProductionEstimateItem(product_name="tortas", quantity=2)]
        )
        torta = make_product("torta", Decimal("100"), unit_sale_price=Decimal("300"))
        mock_product_repo.get_by_name.side_effect = lambda _uid, name: torta if name == "torta" else None

        result = await agent.handle("cuánto cuestan 2 tortas", "conv-1", is_followup=False, user_id=USER_ID)

        assert result.kind == "estimate_result"
        assert result.estimate is not None
        assert result.estimate.items[0].product_name == "torta"
        # Cost is linked to profit because the sale price is known.
        assert result.estimate.projected_revenue == Decimal("600")
        assert result.estimate.estimated_profit == Decimal("400")

    @pytest.mark.asyncio
    async def test_unknown_product_mentions_past_expenses(
        self,
        agent: ProductionEstimateAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
    ) -> None:
        mock_ai_service.parse_production_estimate_text.return_value = ParsedProductionEstimateResult(
            items=[ParsedProductionEstimateItem(product_name="alfajor", quantity=10)]
        )
        mock_product_repo.get_by_name.return_value = None
        expense = MagicMock()
        expense.amount = Decimal("30000")
        mock_transaction_repo.search_expenses_by_description.return_value = [expense, expense]

        result = await agent.handle("cuánto cuestan 10 alfajores", "conv-1", is_followup=False, user_id=USER_ID)

        assert result.message == "ask_unit_cost_with_history"
        assert result.message_params == {"product": "alfajor", "count": "2", "total": "60000"}
