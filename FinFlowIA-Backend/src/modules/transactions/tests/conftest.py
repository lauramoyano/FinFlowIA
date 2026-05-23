import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.schemas import CategoryResult
from src.modules.transactions.categorizer import TransactionCategorizer
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
def transaction_service(mock_repo: AsyncMock, mock_categorizer: AsyncMock) -> TransactionService:
    return TransactionService(repo=mock_repo, categorizer=mock_categorizer)


@pytest.fixture
def sample_transaction(user_id: uuid.UUID) -> Transaction:
    t = Transaction()
    t.id = uuid.uuid4()
    t.user_id = user_id
    t.description = "Almuerzo restaurante"
    t.amount = Decimal("25.00")
    t.transaction_type = "expense"
    t.category = "food"
    t.ai_confidence = 0.95
    t.transaction_date = date.today()
    t.notes = None
    return t
