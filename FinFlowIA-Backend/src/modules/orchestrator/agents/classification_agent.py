import structlog

from src.modules.orchestrator.agents.types import AgentResult
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.transactions.categorizer import TransactionTextParser

logger = structlog.get_logger(__name__)

MAX_FOLLOWUP_TURNS = 3


class ClassificationAgent:
    """
    Agent 1: conversational income/expense classification.

    Wraps the existing TransactionTextParser as-is — no changes to the
    extraction prompt or AIService. The only new behavior is the
    missing-data follow-up loop: if the parser can't find an amount, ask for
    it in the same thread instead of failing outright, accumulating the
    user's replies into one combined message before re-parsing.
    """

    def __init__(self, parser: TransactionTextParser, store: ConversationStore) -> None:
        self._parser = parser
        self._store = store

    async def handle(self, text: str, conversation_id: str, is_followup: bool) -> AgentResult:
        accumulated = text
        turns = 1

        if is_followup:
            state = await self._store.get(conversation_id)
            assert state is not None, "caller must only pass is_followup=True when state exists"
            accumulated = f"{state.payload['accumulated_text']}. {text}"
            turns = state.turns + 1

        result = await self._parser.parse(accumulated)

        if result.error == "no_amount" and turns < MAX_FOLLOWUP_TURNS:
            await self._store.set(
                conversation_id,
                ConversationState(
                    agent="classification", turns=turns, payload={"accumulated_text": accumulated}
                ),
            )
            return AgentResult(kind="question", message="ask_amount")

        await self._store.clear(conversation_id)

        if result.error:
            error_code = "follow_up_retry_limit" if result.error == "no_amount" else result.error
            logger.info("classification_agent_gave_up", error_code=error_code, turns=turns)
            return AgentResult(kind="error", error_code=error_code)

        return AgentResult(kind="confirm_transaction", draft=result)
