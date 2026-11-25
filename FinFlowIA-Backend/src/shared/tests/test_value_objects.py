from datetime import date
from decimal import Decimal

import pytest

from src.shared.domain.value_objects import DateRange, Money


class TestMoney:
    def test_add_and_subtract(self) -> None:
        a, b = Money(Decimal("10")), Money(Decimal("4"))
        assert a.add(b).amount == Decimal("14")
        assert a.subtract(b).amount == Decimal("6")

    def test_rejects_negative_and_bad_currency(self) -> None:
        with pytest.raises(ValueError):
            Money(Decimal("-1"))
        with pytest.raises(ValueError):
            Money(Decimal("1"), currency="PESOS")

    def test_currency_mismatch(self) -> None:
        with pytest.raises(ValueError):
            Money(Decimal("1"), "ARS").add(Money(Decimal("1"), "USD"))
        with pytest.raises(ValueError):
            Money(Decimal("1"), "ARS").subtract(Money(Decimal("1"), "USD"))

    def test_str(self) -> None:
        assert str(Money(Decimal("5"), "COP")) == "COP 5.00"


class TestDateRange:
    def test_contains_and_days(self) -> None:
        r = DateRange(date(2026, 11, 1), date(2026, 11, 30))
        assert r.contains(date(2026, 11, 15))
        assert not r.contains(date(2026, 12, 1))
        assert r.days == 30

    def test_invalid_order(self) -> None:
        with pytest.raises(ValueError):
            DateRange(date(2026, 11, 2), date(2026, 11, 1))
