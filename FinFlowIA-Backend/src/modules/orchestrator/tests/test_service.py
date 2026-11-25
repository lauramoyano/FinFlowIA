import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.orchestrator.agents.classification_agent import ClassificationAgent
from src.modules.orchestrator.agents.financial_recommendation_agent import FinancialRecommendationAgent
from src.modules.orchestrator.agents.period_summary_agent import PeriodSummaryAgent
from src.modules.orchestrator.agents.production_estimate_agent import ProductionEstimateAgent
from src.modules.orchestrator.agents.types import AgentResult
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.orchestrator.openai_tool_client import OpenAIToolClient
from src.modules.orchestrator.service import OrchestratorService

USER_ID = uuid.uuid4()


@pytest.fixture
def mock_tool_client() -> AsyncMock:
    return AsyncMock(spec=OpenAIToolClient)


@pytest.fixture
def mock_store() -> AsyncMock:
    return AsyncMock(spec=ConversationStore)


@pytest.fixture
def mock_classification_agent() -> AsyncMock:
    return AsyncMock(spec=ClassificationAgent)


@pytest.fixture
def mock_production_estimate_agent() -> AsyncMock:
    return AsyncMock(spec=ProductionEstimateAgent)


@pytest.fixture
def mock_financial_recommendation_agent() -> AsyncMock:
    return AsyncMock(spec=FinancialRecommendationAgent)


@pytest.fixture
def mock_period_summary_agent() -> AsyncMock:
    return AsyncMock(spec=PeriodSummaryAgent)


@pytest.fixture
def service(
    mock_tool_client: AsyncMock,
    mock_store: AsyncMock,
    mock_classification_agent: AsyncMock,
    mock_production_estimate_agent: AsyncMock,
    mock_financial_recommendation_agent: AsyncMock,
    mock_period_summary_agent: AsyncMock,
) -> OrchestratorService:
    return OrchestratorService(
        tool_client=mock_tool_client,
        conversation_store=mock_store,
        classification_agent=mock_classification_agent,
        production_estimate_agent=mock_production_estimate_agent,
        financial_recommendation_agent=mock_financial_recommendation_agent,
        period_summary_agent=mock_period_summary_agent,
    )


class TestOrchestratorService:
    @pytest.mark.asyncio
    async def test_routes_to_classification_and_delegates(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_classification_agent: AsyncMock,
    ) -> None:
        mock_store.get.return_value = None
        mock_tool_client.route_intent.return_value = "classification"
        mock_classification_agent.handle.return_value = AgentResult(kind="confirm_transaction")

        conversation_id, result = await service.handle_message(
            text="gasté 500 en nafta", conversation_id=None, user_id=USER_ID
        )

        assert result.kind == "confirm_transaction"
        assert conversation_id
        mock_classification_agent.handle.assert_called_once_with(
            "gasté 500 en nafta", conversation_id, False
        )

    @pytest.mark.asyncio
    async def test_routes_to_production_estimate_and_delegates(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_production_estimate_agent: AsyncMock,
    ) -> None:
        mock_store.get.return_value = None
        mock_tool_client.route_intent.return_value = "production_estimate"
        mock_production_estimate_agent.handle.return_value = AgentResult(kind="estimate_result")

        conversation_id, result = await service.handle_message(
            text="cuánto me cuesta hacer 10 tortas", conversation_id=None, user_id=USER_ID
        )

        assert result.kind == "estimate_result"
        assert conversation_id
        mock_production_estimate_agent.handle.assert_called_once_with(
            "cuánto me cuesta hacer 10 tortas", conversation_id, False, USER_ID
        )

    @pytest.mark.asyncio
    async def test_routes_to_financial_recommendation_and_delegates(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_financial_recommendation_agent: AsyncMock,
    ) -> None:
        mock_store.get.return_value = None
        mock_tool_client.route_intent.return_value = "financial_recommendation"
        mock_financial_recommendation_agent.handle.return_value = AgentResult(
            kind="financial_recommendation_result"
        )

        conversation_id, result = await service.handle_message(
            text="cobré 5000, cómo lo reparto", conversation_id=None, user_id=USER_ID
        )

        assert result.kind == "financial_recommendation_result"
        assert conversation_id
        mock_financial_recommendation_agent.handle.assert_called_once_with(
            "cobré 5000, cómo lo reparto", conversation_id, False, USER_ID
        )

    @pytest.mark.asyncio
    async def test_routes_to_period_summary_and_delegates(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_period_summary_agent: AsyncMock,
    ) -> None:
        mock_store.get.return_value = None
        mock_tool_client.route_intent.return_value = "period_summary"
        mock_period_summary_agent.handle.return_value = AgentResult(kind="period_summary_result")

        conversation_id, result = await service.handle_message(
            text="cómo me fue este mes", conversation_id=None, user_id=USER_ID
        )

        assert result.kind == "period_summary_result"
        assert conversation_id
        mock_period_summary_agent.handle.assert_called_once_with(
            "cómo me fue este mes", conversation_id, False, USER_ID
        )

    @pytest.mark.asyncio
    async def test_routes_to_unrecognized_agent_returns_agent_unavailable(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_classification_agent: AsyncMock,
    ) -> None:
        # No current intent is unimplemented (all 4 agents exist) — this
        # exercises the fallback path for a hypothetical future/unrecognized
        # intent the router might one day return.
        mock_store.get.return_value = None
        mock_tool_client.route_intent.return_value = "some_future_agent"

        conversation_id, result = await service.handle_message(
            text="algo que todavía no sabemos rutear", conversation_id=None, user_id=USER_ID
        )

        assert result.kind == "agent_unavailable"
        assert result.agent == "some_future_agent"
        assert conversation_id
        mock_classification_agent.handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_existing_conversation_id_skips_rerouting(
        self,
        service: OrchestratorService,
        mock_tool_client: AsyncMock,
        mock_store: AsyncMock,
        mock_classification_agent: AsyncMock,
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="classification", turns=1, payload={"accumulated_text": "gasté en nafta"}
        )
        mock_classification_agent.handle.return_value = AgentResult(kind="confirm_transaction")

        conversation_id, result = await service.handle_message(
            text="500", conversation_id="conv-1", user_id=USER_ID
        )

        assert conversation_id == "conv-1"
        assert result.kind == "confirm_transaction"
        mock_tool_client.route_intent.assert_not_called()
        mock_classification_agent.handle.assert_called_once_with("500", "conv-1", True)
