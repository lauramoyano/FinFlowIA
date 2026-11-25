import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.schemas import CategoryResult
from src.modules.transactions.categorizer import TransactionCategorizer
from src.modules.transactions.category_repository import CategoryRepository
from src.modules.transactions.models import Transaction
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.service import TransactionService


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=TransactionRepository)


@pytest.fixture
def mock_categorizer() -> AsyncMock:
    mock = AsyncMock(spec=TransactionCategorizer)
    mock.categorize.return_value = CategoryResult(
        category="food", confidence=0.95, from_cache=False
    )
    return mock


@pytest.fixture
def mock_category_repo() -> AsyncMock:
    mock = AsyncMock(spec=CategoryRepository)
    # No category-linking by default; tests that care about category_id
    # resolution override this explicitly.
    mock.get_by_name.return_value = None
    return mock


@pytest.fixture
def transaction_service(
    mock_repo: AsyncMock,
    mock_categorizer: AsyncMock,
    mock_category_repo: AsyncMock,
) -> TransactionService:
    return TransactionService(
        repo=mock_repo, categorizer=mock_categorizer, category_repo=mock_category_repo
    )


@pytest.fixture
def sample_transaction(user_id: uuid.UUID) -> Transaction:
    t = Transaction()
    t.id = uuid.uuid4()
    t.user_id = user_id
    t.description = "Almuerzo restaurante"
    t.amount = Decimal("25.00")
    t.transaction_type = "expense"
    t.category = "food"
    t.category_id = None
    t.ai_confidence = 0.95
    t.transaction_date = date.today()
    t.notes = None
    t.created_at = datetime.now(UTC)
    t.updated_at = datetime.now(UTC)
    return t
