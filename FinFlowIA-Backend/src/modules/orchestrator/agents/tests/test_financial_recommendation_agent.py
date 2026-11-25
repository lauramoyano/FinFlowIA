import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.ai.schemas import ParsedRecommendationCosts, ParsedSaleAmountResult
from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.financial_recommendation_agent import FinancialRecommendationAgent
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.orchestrator.product_memory import ProductMemory
from src.modules.production.repository import ProductionEstimateRepository, ProductRepository
from src.modules.planning.repository import DistributionTemplateRepository, FinancialRecommendationRepository
from src.modules.transactions.repository import TransactionRepository

USER_ID = uuid.uuid4()


@pytest.fixture
def mock_ai_service() -> AsyncMock:
    return AsyncMock(spec=AIService)


@pytest.fixture
def mock_template_repo() -> AsyncMock:
    return AsyncMock(spec=DistributionTemplateRepository)


@pytest.fixture
def mock_recommendation_repo() -> AsyncMock:
    return AsyncMock(spec=FinancialRecommendationRepository)


@pytest.fixture
def mock_transaction_repo() -> AsyncMock:
    repo = AsyncMock(spec=TransactionRepository)
    repo.get_pending_debt_total.return_value = Decimal("0")
    return repo


@pytest.fixture
def mock_product_repo() -> AsyncMock:
    repo = AsyncMock(spec=ProductRepository)
    repo.list_for_user.return_value = []
    return repo


@pytest.fixture
def mock_estimate_repo() -> AsyncMock:
    return AsyncMock(spec=ProductionEstimateRepository)


@pytest.fixture
def mock_store() -> AsyncMock:
    return AsyncMock(spec=ConversationStore)


@pytest.fixture
def agent(
    mock_ai_service: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_recommendation_repo: AsyncMock,
    mock_transaction_repo: AsyncMock,
    mock_product_repo: AsyncMock,
    mock_estimate_repo: AsyncMock,
    mock_store: AsyncMock,
) -> FinancialRecommendationAgent:
    return FinancialRecommendationAgent(
        ai_service=mock_ai_service,
        template_repo=mock_template_repo,
        recommendation_repo=mock_recommendation_repo,
        transaction_repo=mock_transaction_repo,
        memory=ProductMemory(mock_product_repo, mock_estimate_repo, mock_transaction_repo),
        store=mock_store,
    )


def make_template_item(label: str, percentage: str) -> MagicMock:
    item = MagicMock()
    item.label = label
    item.percentage = Decimal(percentage)
    return item


def default_template_items() -> list[MagicMock]:
    return [
        make_template_item("Reinversión", "40"),
        make_template_item("Ahorro", "20"),
        make_template_item("Utilidad", "40"),
    ]


class TestFinancialRecommendationAgent:
    @pytest.mark.asyncio
    async def test_amount_given_upfront_asks_costs_directly(
        self, agent: FinancialRecommendationAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_ai_service.parse_sale_amount_text.return_value = ParsedSaleAmountResult(amount=Decimal("5000"))

        result = await agent.handle(
            "cobré 5000, cómo lo reparto", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_recommendation_costs"
        mock_store.set.assert_called_once()
        saved_conversation_id, saved_state = mock_store.set.call_args.args
        assert saved_conversation_id == "conv-1"
        assert saved_state == ConversationState(
            agent="financial_recommendation", turns=1, payload={"awaiting": "costs", "sale_amount": "5000"}
        )

    @pytest.mark.asyncio
    async def test_no_amount_asks_then_continues_to_costs(
        self, agent: FinancialRecommendationAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_ai_service.parse_sale_amount_text.return_value = ParsedSaleAmountResult(error="no_amount")

        result = await agent.handle(
            "quiero repartir una venta", "conv-1", is_followup=False, user_id=USER_ID
        )

        assert result.kind == "question"
        assert result.message == "ask_sale_amount"
        _, saved_state = mock_store.set.call_args.args
        assert saved_state == ConversationState(
            agent="financial_recommendation",
            turns=1,
            payload={"awaiting": "sale_amount", "accumulated_text": "quiero repartir una venta"},
        )

        mock_store.get.return_value = saved_state
        mock_ai_service.parse_sale_amount_text.return_value = ParsedSaleAmountResult(amount=Decimal("3000"))

        follow_up = await agent.handle("3000", "conv-1", is_followup=True, user_id=USER_ID)

        assert follow_up.kind == "question"
        assert follow_up.message == "ask_recommendation_costs"
        mock_ai_service.parse_sale_amount_text.assert_called_with(
            "quiero repartir una venta. 3000"
        )

    @pytest.mark.asyncio
    async def test_costs_none_mentioned_computes_full_net(
        self,
        agent: FinancialRecommendationAgent,
        mock_ai_service: AsyncMock,
        mock_template_repo: AsyncMock,
        mock_recommendation_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="financial_recommendation", turns=1, payload={"awaiting": "costs", "sale_amount": "3000"}
        )
        mock_ai_service.parse_recommendation_costs_text.return_value = ParsedRecommendationCosts()
        template = MagicMock()
        template.id = uuid.uuid4()
        mock_template_repo.get_or_create_default.return_value = (template, default_template_items())

        result = await agent.handle("ninguno", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "financial_recommendation_result"
        fr = result.financial_recommendation_result
        assert fr is not None
        assert fr.total_costs == Decimal("0")
        assert fr.net_amount == Decimal("3000")
        assert fr.sale_amount == Decimal("3000")
        assert {item.label: item.amount for item in fr.items} == {
            "Reinversión": Decimal("1200.00"),
            "Ahorro": Decimal("600.00"),
            "Utilidad": Decimal("1200.00"),
        }
        assert fr.estimated_savings == Decimal("600.00")
        assert fr.estimated_business_balance == Decimal("2400.00")
        assert fr.pending_debt_total == Decimal("0")
        mock_recommendation_repo.create_with_items.assert_called_once()
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_costs_partial_computes_correct_math(
        self,
        agent: FinancialRecommendationAgent,
        mock_ai_service: AsyncMock,
        mock_template_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="financial_recommendation", turns=1, payload={"awaiting": "costs", "sale_amount": "5000"}
        )
        mock_ai_service.parse_recommendation_costs_text.return_value = ParsedRecommendationCosts(
            insumos_cost=Decimal("1000"), transporte_cost=Decimal("200")
        )
        template = MagicMock()
        template.id = uuid.uuid4()
        mock_template_repo.get_or_create_default.return_value = (template, default_template_items())

        result = await agent.handle(
            "gasté 1000 en insumos y 200 en transporte", "conv-1", is_followup=True, user_id=USER_ID
        )

        fr = result.financial_recommendation_result
        assert fr is not None
        assert fr.total_costs == Decimal("1200")
        assert fr.net_amount == Decimal("3800")
        assert {item.label: item.amount for item in fr.items} == {
            "Reinversión": Decimal("1520.00"),
            "Ahorro": Decimal("760.00"),
            "Utilidad": Decimal("1520.00"),
        }

    @pytest.mark.asyncio
    async def test_includes_pending_debt_total(
        self,
        agent: FinancialRecommendationAgent,
        mock_ai_service: AsyncMock,
        mock_template_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="financial_recommendation", turns=1, payload={"awaiting": "costs", "sale_amount": "1000"}
        )
        mock_ai_service.parse_recommendation_costs_text.return_value = ParsedRecommendationCosts()
        template = MagicMock()
        template.id = uuid.uuid4()
        mock_template_repo.get_or_create_default.return_value = (template, default_template_items())
        mock_transaction_repo.get_pending_debt_total.return_value = Decimal("350.00")

        result = await agent.handle("ninguno", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.financial_recommendation_result is not None
        assert result.financial_recommendation_result.pending_debt_total == Decimal("350.00")

    @pytest.mark.asyncio
    async def test_retry_limit_on_amount_returns_error(
        self, agent: FinancialRecommendationAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="financial_recommendation",
            turns=2,
            payload={"awaiting": "sale_amount", "accumulated_text": "quiero repartir. no sé cuánto"},
        )
        mock_ai_service.parse_sale_amount_text.return_value = ParsedSaleAmountResult(error="no_amount")

        result = await agent.handle("sigo sin saber", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_store.set.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")


class TestLinkedInsumos:
    @pytest.mark.asyncio
    async def test_sale_of_estimated_product_recalls_insumos_and_nets_profit(
        self,
        agent: FinancialRecommendationAgent,
        mock_ai_service: AsyncMock,
        mock_product_repo: AsyncMock,
        mock_estimate_repo: AsyncMock,
        mock_template_repo: AsyncMock,
        mock_store: AsyncMock,
    ) -> None:
        torta = MagicMock()
        torta.id = uuid.uuid4()
        torta.name = "torta"
        mock_product_repo.list_for_user.return_value = [torta]
        item = MagicMock()
        item.product_id = torta.id
        item.subtotal = Decimal("1200")
        mock_estimate_repo.latest_items_for_products.return_value = [item]
        mock_ai_service.parse_sale_amount_text.return_value = ParsedSaleAmountResult(amount=Decimal("5000"))

        asked = await agent.handle("vendí 5000 de tortas", "conv-1", is_followup=False, user_id=USER_ID)

        assert asked.message == "ask_recommendation_costs_linked"
        assert asked.message_params == {"product": "torta", "insumos": "1200"}
        _, state = mock_store.set.call_args.args

        mock_store.get.return_value = state
        mock_ai_service.parse_recommendation_costs_text.return_value = ParsedRecommendationCosts()
        template = MagicMock()
        template_item = MagicMock()
        template_item.label = "Utilidad"
        template_item.percentage = Decimal("100")
        mock_template_repo.get_or_create_default.return_value = (template, [template_item])

        done = await agent.handle("nada más", "conv-1", is_followup=True, user_id=USER_ID)

        fr = done.financial_recommendation_result
        assert fr is not None
        assert fr.total_costs == Decimal("1200")
        assert fr.net_amount == Decimal("3800")
        assert fr.insumos_linked_products == ["torta"]
