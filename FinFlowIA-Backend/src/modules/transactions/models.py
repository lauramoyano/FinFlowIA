import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.transactions.enums import CategoryType, TransactionType
from src.shared.domain.base_entity import BaseEntity


class Transaction(BaseEntity):
    """SQLAlchemy model for financial transactions (income and expenses)."""

    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    ai_confidence: Mapped[float | None] = mapped_column(Numeric(precision=4, scale=3), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.transaction_type} "
            f"amount={self.amount} category={self.category!r}>"
        )
