import uuid
from datetime import date
from decimal import Decimal

import structlog
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.transactions.models import Transaction

logger = structlog.get_logger(__name__)


class TransactionRepository:
    """Data access layer for Transaction entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        description: str,
        amount: Decimal,
        transaction_type: str,
        transaction_date: date,
        category: str | None = None,
        category_id: uuid.UUID | None = None,
        ai_confidence: float | None = None,
        notes: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            category=category,
            category_id=category_id,
            ai_confidence=ai_confidence,
            notes=notes,
        )
        self._session.add(transaction)
        await self._session.flush()
        logger.info("transaction_created", transaction_id=str(transaction.id))
        return transaction

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        result = await self._session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        transaction_type: str | None = None,
        category: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[list[Transaction], int]:
        """Return paginated transactions for a user along with total count."""
        conditions = [Transaction.user_id == user_id]

        if transaction_type:
            conditions.append(Transaction.transaction_type == transaction_type)
        if category:
            conditions.append(Transaction.category == category)
        if start_date:
            conditions.append(Transaction.transaction_date >= start_date)
        if end_date:
            conditions.append(Transaction.transaction_date <= end_date)

        where_clause = and_(*conditions)

        count_result = await self._session.execute(
            select(func.count()).select_from(Transaction).where(where_clause)
        )
        total = count_result.scalar_one()

        data_result = await self._session.execute(
            select(Transaction)
            .where(where_clause)
            .order_by(desc(Transaction.transaction_date), desc(Transaction.created_at))
            .offset(offset)
            .limit(limit)
        )
        transactions = list(data_result.scalars().all())

        return transactions, total

    async def update(
        self,
        transaction_id: uuid.UUID,
        **kwargs: object,
    ) -> Transaction | None:
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(transaction, key):
                setattr(transaction, key, value)
        await self._session.flush()
        return transaction

    async def delete(self, transaction_id: uuid.UUID) -> bool:
        transaction = await self.get_by_id(transaction_id)
        if not transaction:
            return False
        await self._session.delete(transaction)
        await self._session.flush()
        return True

    async def get_pending_debt_total(self, user_id: uuid.UUID) -> Decimal:
        """
        Sum of expense transactions representing an ongoing financial
        commitment: recurring expenses, or installment purchases not yet
        fully paid off. Used by the financial-recommendation agent to
        surface pending debts alongside a reparto suggestion.
        """
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                or_(
                    Transaction.is_recurring.is_(True),
                    and_(
                        Transaction.installments_total.is_not(None),
                        Transaction.installments_paid < Transaction.installments_total,
                    ),
                ),
            )
        )
        return Decimal(result.scalar_one())

    async def search_expenses_by_description(
        self, user_id: uuid.UUID, term: str, limit: int = 20
    ) -> list[Transaction]:
        """
        Past expenses whose description mentions `term` (case-insensitive).
        Lets agents recognise spending already tied to a preparation, e.g.
        "harina para las tortas" when the user later asks about "torta".
        """
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        result = await self._session.execute(
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.description.ilike(f"%{escaped}%", escape="\\"),
            )
            .order_by(desc(Transaction.transaction_date))
            .limit(limit)
        )
        return list(result.scalars().all())
