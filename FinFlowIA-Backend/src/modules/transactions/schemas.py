import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.modules.transactions.enums import CategoryType, TransactionType


class CreateTransactionRequest(BaseModel):
    """Request schema for creating a new transaction."""

    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, decimal_places=2)
    transaction_type: TransactionType
    transaction_date: date
    category: CategoryType | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v > Decimal("999999999.99"):
            raise ValueError("Amount exceeds maximum allowed value")
        return v


class UpdateTransactionRequest(BaseModel):
    """Request schema for partially updating a transaction."""

    description: str | None = Field(default=None, min_length=1, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    transaction_type: TransactionType | None = None
    transaction_date: date | None = None
    category: CategoryType | None = None
    notes: str | None = Field(default=None, max_length=1000)


class TransactionResponse(BaseModel):
    """Response schema for a single transaction."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    description: str
    amount: Decimal
    transaction_type: str
    category: str | None
    category_id: uuid.UUID | None
    ai_confidence: float | None
    transaction_date: date
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Response schema for a list of transactions with pagination metadata."""

    data: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreateCategoryRequest(BaseModel):
    """Request schema for creating a custom category."""

    name: str = Field(min_length=1, max_length=50)
    transaction_type: TransactionType
    icon: str | None = Field(default=None, max_length=50)


class CategoryResponse(BaseModel):
    """Response schema for a category — system default or user-defined."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    transaction_type: str
    icon: str | None
    is_default: bool
