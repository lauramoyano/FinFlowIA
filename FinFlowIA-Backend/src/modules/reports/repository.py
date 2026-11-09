import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.transactions.models import Transaction


class ReportRepository:
    """Data access layer for report aggregation queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_totals_by_period(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get income, expense totals and transaction count for a period."""
        result = await self._session.execute(
            select(
                func.sum(
                    case((Transaction.transaction_type == "income", Transaction.amount), else_=0)
                ).label("total_income"),
                func.sum(
                    case((Transaction.transaction_type == "expense", Transaction.amount), else_=0)
                ).label("total_expenses"),
                func.count(Transaction.id).label("transaction_count"),
            ).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
            )
        )
        row = result.one()
        return {
            "total_income": row.total_income or Decimal("0"),
            "total_expenses": row.total_expenses or Decimal("0"),
            "transaction_count": row.transaction_count or 0,
        }

    async def get_totals_by_category(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get transaction totals grouped by category for a period."""
        result = await self._session.execute(
            select(
                Transaction.category,
                Transaction.transaction_type,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
            )
            .group_by(Transaction.category, Transaction.transaction_type)
            .order_by(func.sum(Transaction.amount).desc())
        )
        return [
            {
                "category": row.category or "uncategorized",
                "transaction_type": row.transaction_type,
                "total": row.total,
                "count": row.count,
            }
            for row in result.all()
        ]

    async def get_time_series(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        granularity: str,
    ) -> list[dict]:
        """
        Income/expense totals grouped into date_trunc buckets.
        Only non-empty buckets are returned — callers must backfill zero
        buckets themselves for a continuous chart.
        """
        bucket = func.date_trunc(granularity, Transaction.transaction_date).label("bucket")
        result = await self._session.execute(
            select(
                bucket,
                func.sum(
                    case((Transaction.transaction_type == "income", Transaction.amount), else_=0)
                ).label("income"),
                func.sum(
                    case((Transaction.transaction_type == "expense", Transaction.amount), else_=0)
                ).label("expense"),
            )
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                )
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        return [
            {
                "bucket": row.bucket.date(),
                "income": row.income or Decimal("0"),
                "expense": row.expense or Decimal("0"),
            }
            for row in result.all()
        ]
