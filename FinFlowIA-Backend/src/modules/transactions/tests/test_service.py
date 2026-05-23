import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.schemas import CategoryResult
from src.modules.transactions.models import Transaction
from src.modules.transactions.schemas import CreateTransactionRequest
from src.modules.transactions.service import TransactionService
from src.modules.transactions.enums import TransactionType
from src.shared.exceptions.not_found import NotFoundException


class TestTransactionService:
    @pytest.mark.asyncio
    async def test_create_transaction_calls_categorizer(
        self,
        transaction_service: TransactionService,
        mock_categorizer: AsyncMock,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
        sample_transaction: Transaction,
    ) -> None:
        mock_repo.create.return_value = sample_transaction

        data = CreateTransactionRequest(
            description="Almuerzo restaurante",
            amount=Decimal("25.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date.today(),
        )

        await transaction_service.create(data, user_id=user_id)

        mock_categorizer.categorize.assert_called_once_with(
            description="Almuerzo restaurante",
            amount=Decimal("25.00"),
        )

    @pytest.mark.asyncio
    async def test_create_transaction_skips_categorizer_if_category_provided(
        self,
        transaction_service: TransactionService,
        mock_categorizer: AsyncMock,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
        sample_transaction: Transaction,
    ) -> None:
        mock_repo.create.return_value = sample_transaction

        data = CreateTransactionRequest(
            description="Almuerzo",
            amount=Decimal("25.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date.today(),
            category="food",  # type: ignore
        )

        await transaction_service.create(data, user_id=user_id)
        mock_categorizer.categorize.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found_for_missing_transaction(
        self,
        transaction_service: TransactionService,
        mock_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await transaction_service.get_by_id(uuid.uuid4(), user_id)

    @pytest.mark.parametrize(
        "amount,expected_valid",
        [
            (Decimal("0.01"), True),
            (Decimal("999999999.99"), True),
        ],
    )
    def test_transaction_amount_validation(
        self, amount: Decimal, expected_valid: bool
    ) -> None:
        from pydantic import ValidationError
        if expected_valid:
            req = CreateTransactionRequest(
                description="Test",
                amount=amount,
                transaction_type=TransactionType.INCOME,
                transaction_date=date.today(),
            )
            assert req.amount == amount
        else:
            with pytest.raises(ValidationError):
                CreateTransactionRequest(
                    description="Test",
                    amount=amount,
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date.today(),
                )

    @pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1")])
    def test_invalid_amounts_fail_validation(self, amount: Decimal) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CreateTransactionRequest(
                description="Test",
                amount=amount,
                transaction_type=TransactionType.INCOME,
                transaction_date=date.today(),
            )
