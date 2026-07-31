import uuid
from datetime import date

import structlog

from src.modules.transactions.categorizer import TransactionCategorizer
from src.modules.transactions.category_repository import CategoryRepository
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.schemas import (
    CreateTransactionRequest,
    TransactionResponse,
    UpdateTransactionRequest,
)
from src.shared.exceptions.not_found import NotFoundException
from src.shared.exceptions.unauthorized import ForbiddenException

logger = structlog.get_logger(__name__)


class TransactionService:
    """Business logic for managing financial transactions."""

    def __init__(
        self,
        repo: TransactionRepository,
        categorizer: TransactionCategorizer,
        category_repo: CategoryRepository,
    ) -> None:
        self._repo = repo
        self._categorizer = categorizer
        self._category_repo = category_repo

    async def create(
        self,
        data: CreateTransactionRequest,
        user_id: uuid.UUID,
    ) -> TransactionResponse:
        """Create a new transaction and auto-categorize it via AI."""
        logger.info(
            "creating_transaction",
            user_id=str(user_id),
            amount=str(data.amount),
            type=data.transaction_type,
        )

        # Auto-categorize if no category was provided
        category = data.category
        ai_confidence: float | None = None

        if not category:
            result = await self._categorizer.categorize(
                description=data.description,
                amount=data.amount,
            )
            category = result.category
            ai_confidence = result.confidence

        category_id = await self._resolve_category_id(
            user_id, category, data.transaction_type.value
        )

        transaction = await self._repo.create(
            user_id=user_id,
            description=data.description,
            amount=data.amount,
            transaction_type=data.transaction_type.value,
            transaction_date=data.transaction_date,
            category=category,
            category_id=category_id,
            ai_confidence=ai_confidence,
            notes=data.notes,
        )

        return TransactionResponse.model_validate(transaction)

    async def _resolve_category_id(
        self,
        user_id: uuid.UUID,
        category: str | None,
        transaction_type: str,
    ) -> uuid.UUID | None:
        """Link a transaction to its Category row when the name matches one."""
        if not category:
            return None
        category_row = await self._category_repo.get_by_name(
            user_id=user_id, name=category, transaction_type=transaction_type
        )
        return category_row.id if category_row else None

    async def get_by_id(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> TransactionResponse:
        """Get a single transaction, ensuring it belongs to the requesting user."""
        transaction = await self._repo.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundException("Transaction", transaction_id)
        if transaction.user_id != user_id:
            raise ForbiddenException("You don't have access to this transaction")
        return TransactionResponse.model_validate(transaction)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        transaction_type: str | None = None,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[list[TransactionResponse], int]:
        """List transactions for a user with optional filters and pagination."""
        offset = (page - 1) * page_size
        transactions, total = await self._repo.list_by_user(
            user_id=user_id,
            limit=page_size,
            offset=offset,
            transaction_type=transaction_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )
        return [TransactionResponse.model_validate(t) for t in transactions], total

    async def update(
        self,
        transaction_id: uuid.UUID,
        data: UpdateTransactionRequest,
        user_id: uuid.UUID,
    ) -> TransactionResponse:
        """Update a transaction, ensuring ownership."""
        transaction = await self._repo.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundException("Transaction", transaction_id)
        if transaction.user_id != user_id:
            raise ForbiddenException("You don't have access to this transaction")

        update_data = data.model_dump(exclude_none=True)
        if "transaction_type" in update_data:
            update_data["transaction_type"] = update_data["transaction_type"].value

        if "category" in update_data:
            tx_type = update_data.get("transaction_type", transaction.transaction_type)
            category_id = await self._resolve_category_id(
                user_id, update_data["category"], tx_type
            )
            if category_id:
                update_data["category_id"] = category_id

        updated = await self._repo.update(transaction_id, **update_data)
        return TransactionResponse.model_validate(updated)

    async def delete(self, transaction_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a transaction, ensuring ownership."""
        transaction = await self._repo.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundException("Transaction", transaction_id)
        if transaction.user_id != user_id:
            raise ForbiddenException("You don't have access to this transaction")
        await self._repo.delete(transaction_id)
        logger.info("transaction_deleted", transaction_id=str(transaction_id))
