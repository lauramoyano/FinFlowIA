import json
from dataclasses import asdict, dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

CONVERSATION_TTL_SECONDS = 15 * 60


@dataclass
class ConversationState:
    """
    Ephemeral multi-turn state for one orchestrator conversation. `payload`
    is agent-specific (e.g. the classification agent stores
    {"accumulated_text": ...}, the production estimate agent stores a
    richer shape with pending/resolved items) — kept generic here so any
    agent can persist its own follow-up state through the same store.
    """

    agent: str
    turns: int
    payload: dict[str, Any]


class ConversationStore:
    """
    Redis-backed store for in-progress orchestrator conversations (e.g. the
    classification agent waiting on a missing amount). No Postgres table is
    needed: this state only matters for the next few minutes of a chat, not
    after it resolves.
    """

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    def _key(self, conversation_id: str) -> str:
        return f"orchestrator:conversation:{conversation_id}"

    async def get(self, conversation_id: str) -> ConversationState | None:
        if self._redis is None:
            return None
        try:
            raw = await self._redis.get(self._key(conversation_id))
            if not raw:
                return None
            return ConversationState(**json.loads(raw))
        except Exception as e:
            logger.warning("conversation_store_get_error", error=str(e))
            return None

    async def set(self, conversation_id: str, state: ConversationState) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(
                self._key(conversation_id), CONVERSATION_TTL_SECONDS, json.dumps(asdict(state))
            )
        except Exception as e:
            logger.warning("conversation_store_set_error", error=str(e))

    async def clear(self, conversation_id: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(self._key(conversation_id))
        except Exception as e:
            logger.warning("conversation_store_clear_error", error=str(e))
