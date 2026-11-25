from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """
    Immutable value object representing a monetary amount with currency.
    Uses Decimal for precise financial calculations.
    """

    amount: Decimal
    currency: str = "ARS"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class DateRange:
    """
    Immutable value object representing a date range with start and end dates.
    """

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")

    def contains(self, d: date) -> bool:
        return self.start_date <= d <= self.end_date

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1
