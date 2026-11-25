import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.modules.transactions.enums import TransactionType


class CreateTransactionRequest(BaseModel):
    """Request schema for creating a new transaction."""

    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, decimal_places=2)
    transaction_type: TransactionType
    transaction_date: date
    # str, not CategoryType: a category can be one of the fixed defaults OR
    # a custom category name the user created (see CategoryService). Both
    # are resolved to a Category row by name in TransactionService._resolve_category_id.
    category: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v > Decimal("999999999.99"):
            raise ValueError("Amount exceeds maximum allowed value")
        return v


class ParseTransactionTextRequest(BaseModel):
    """Request schema for parsing a free-text chat message into transaction fields."""

    text: str = Field(min_length=1, max_length=500)


class ParsedTransactionResponse(BaseModel):
    """
    Response schema for a parsed (not yet created) transaction. Field names
    mirror CreateTransactionRequest so the frontend can reuse the same types
    when the user confirms and calls POST /transactions. When `error` is set,
    the other fields are not reliable and no transaction should be created.
    """

    description: str
    amount: Decimal | None
    transaction_type: TransactionType | None
    transaction_date: date
    category: str
    confidence: float
    error: str | None = None


class UpdateTransactionRequest(BaseModel):
    """Request schema for partially updating a transaction."""

    description: str | None = Field(default=None, min_length=1, max_length=500)
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    transaction_type: TransactionType | None = None
    transaction_date: date | None = None
    category: str | None = Field(default=None, max_length=50)
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
