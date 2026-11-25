import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.transactions.enums import CategoryType, TransactionType
from src.shared.domain.base_entity import BaseEntity


class Category(BaseEntity):
    """
    SQLAlchemy model for transaction categories.

    A row with user_id=None is a system default category (seeded once, shared by
    everyone). A row with user_id set is a category a specific user created for
    themselves. Both are looked up the same way, so custom categories don't need
    special-casing anywhere that already queries categories.
    """

    __tablename__ = "categories"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "name", "transaction_type", name="uq_categories_user_name_type"
        ),
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r} user_id={self.user_id}>"


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
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_confidence: Mapped[float | None] = mapped_column(Numeric(precision=4, scale=3), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_interval: Mapped[str | None] = mapped_column(String(20), nullable=True)
    installments_total: Mapped[int | None] = mapped_column(nullable=True)
    installments_paid: Mapped[int] = mapped_column(default=0, nullable=False)
    parent_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        # Dashboard/reports queries always filter by user + date range together.
        Index("ix_transactions_user_id_transaction_date", "user_id", "transaction_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.transaction_type} "
            f"amount={self.amount} category={self.category!r}>"
        )
