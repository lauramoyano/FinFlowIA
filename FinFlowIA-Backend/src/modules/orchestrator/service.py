import uuid

import structlog

from src.modules.orchestrator.agents.classification_agent import ClassificationAgent
from src.modules.orchestrator.agents.financial_recommendation_agent import FinancialRecommendationAgent
from src.modules.orchestrator.agents.period_summary_agent import PeriodSummaryAgent
from src.modules.orchestrator.agents.production_estimate_agent import ProductionEstimateAgent
from src.modules.orchestrator.agents.types import AgentResult
from src.modules.orchestrator.conversation_store import ConversationStore
from src.modules.orchestrator.openai_tool_client import OpenAIToolClient

logger = structlog.get_logger(__name__)


class OrchestratorService:
    """
    Routes a chat message to the right agent by intent and manages the
    conversation_id lifecycle for multi-turn follow-ups. All 4 agents
    (classification, production estimate, financial recommendation, period
    summary) are implemented — "agent_unavailable" is kept as a fallback
    for any future unrecognized/unbuilt intent.
    """

    def __init__(
        self,
        tool_client: OpenAIToolClient,
        conversation_store: ConversationStore,
        classification_agent: ClassificationAgent,
        production_estimate_agent: ProductionEstimateAgent,
        financial_recommendation_agent: FinancialRecommendationAgent,
        period_summary_agent: PeriodSummaryAgent,
    ) -> None:
        self._tool_client = tool_client
        self._store = conversation_store
        self._classification_agent = classification_agent
        self._production_estimate_agent = production_estimate_agent
        self._financial_recommendation_agent = financial_recommendation_agent
        self._period_summary_agent = period_summary_agent

    async def handle_message(
        self, text: str, conversation_id: str | None, user_id: uuid.UUID
    ) -> tuple[str, AgentResult]:
        if conversation_id:
            state = await self._store.get(conversation_id)
            if state is not None:
                result = await self._dispatch(
                    state.agent, text, conversation_id, is_followup=True, user_id=user_id
                )
                return conversation_id, result

        new_conversation_id = conversation_id or str(uuid.uuid4())
        intent = await self._tool_client.route_intent(text)
        result = await self._dispatch(
            intent, text, new_conversation_id, is_followup=False, user_id=user_id
        )
        return new_conversation_id, result

    async def _dispatch(
        self, agent: str, text: str, conversation_id: str, is_followup: bool, user_id: uuid.UUID
    ) -> AgentResult:
        if agent == "classification":
            return await self._classification_agent.handle(text, conversation_id, is_followup)

        if agent == "production_estimate":
            return await self._production_estimate_agent.handle(
                text, conversation_id, is_followup, user_id
            )

        if agent == "financial_recommendation":
            return await self._financial_recommendation_agent.handle(
                text, conversation_id, is_followup, user_id
            )

        if agent == "period_summary":
            return await self._period_summary_agent.handle(text, conversation_id, is_followup, user_id)

        logger.info("orchestrator_agent_unavailable", agent=agent)
        return AgentResult(kind="agent_unavailable", agent=agent)
