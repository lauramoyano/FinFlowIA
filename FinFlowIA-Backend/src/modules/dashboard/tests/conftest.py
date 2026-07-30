import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.dashboard.service import DashboardService
from src.modules.reports.repository import ReportRepository
from src.modules.transactions.models import Transaction
from src.modules.transactions.repository import TransactionRepository


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_transaction_repo() -> AsyncMock:
    return AsyncMock(spec=TransactionRepository)


@pytest.fixture
def mock_report_repo() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def dashboard_service(
    mock_transaction_repo: AsyncMock, mock_report_repo: AsyncMock
) -> DashboardService:
    return DashboardService(
        transaction_repo=mock_transaction_repo, report_repo=mock_report_repo
    )


@pytest.fixture
def sample_transaction(user_id: uuid.UUID) -> Transaction:
    t = Transaction()
    t.id = uuid.uuid4()
    t.user_id = user_id
    t.description = "Venta producto cliente A"
    t.amount = Decimal("1000.00")
    t.transaction_type = "income"
    t.category = "sales"
    t.ai_confidence = 0.9
    t.transaction_date = date.today()
    t.notes = None
    t.created_at = datetime.now(UTC)
    t.updated_at = datetime.now(UTC)
    return t
