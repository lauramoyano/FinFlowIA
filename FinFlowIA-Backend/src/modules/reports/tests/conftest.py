import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.reports.repository import ReportRepository
from src.modules.reports.service import ReportService


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_report_repo() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def report_service(mock_report_repo: AsyncMock) -> ReportService:
    return ReportService(repo=mock_report_repo)
