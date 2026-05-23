from decimal import Decimal

import structlog

from src.modules.ai.schemas import CategoryResult
from src.modules.ai.service import AIService

logger = structlog.get_logger(__name__)


class TransactionCategorizer:
    """
    Orchestrates the AI categorization flow for transactions.
    Acts as a bridge between the transactions module and the AI module.
    """

    def __init__(self, ai_service: AIService) -> None:
        self._ai_service = ai_service

    async def categorize(
        self,
        description: str,
        amount: Decimal,
    ) -> CategoryResult:
        """
        Categorize a transaction using the AI service.
        Returns CategoryResult with category and confidence score.
        Falls back to 'uncategorized' if AI service fails.
        """
        logger.debug("categorizing_transaction", description=description, amount=str(amount))
        try:
            result = await self._ai_service.categorize_transaction(
                description=description,
                amount=amount,
            )
            logger.info(
                "transaction_categorized",
                category=result.category,
                confidence=result.confidence,
                from_cache=result.from_cache,
            )
            return result
        except Exception as e:
            logger.error("categorization_failed", error=str(e), description=description)
            return CategoryResult(category="uncategorized", confidence=0.0, from_cache=False)
