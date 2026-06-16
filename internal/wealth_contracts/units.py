"""
WEALTH Units — Currency and unit normalization.

Anti-pattern: silently using float for money causes precision loss.
Solution: decimal-safe arithmetic + explicit currency tagging.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Union


class Currency(str, Enum):
    """Supported currencies (extend as needed)."""

    MYR = "MYR"
    USD = "USD"
    SGD = "SGD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    AUD = "AUD"


class Unit(str, Enum):
    """Capital/resource units."""

    MYR = "MYR"
    USD = "USD"
    BBL = "BBL"  # barrel
    MMSCFD = "MMSCFD"  # million std cubic feet per day
    STBD = "STBD"  # stock tank barrel per day
    MWH = "MWH"  # megawatt hour
    GT = "GT"  # gigatonne
    TWH = "TWH"  # terawatt hour


class Money:
    """Decimal-safe money wrapper. Use Decimal internally, expose float only at API edge."""

    def __init__(self, amount: Union[Decimal, float, int, str], currency: Union[Currency, str] = Currency.MYR):
        if isinstance(currency, str):
            currency = Currency(currency)
        self.currency = currency
        self.amount = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount

    def __add__(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: Union[Decimal, float, int]) -> "Money":
        return Money(self.amount * Decimal(str(scalar)), self.currency)

    def __truediv__(self, scalar: Union[Decimal, float, int]) -> "Money":
        return Money(self.amount / Decimal(str(scalar)), self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount >= other.amount

    def __eq__(self, other) -> bool:
        if not isinstance(other, Money):
            return False
        return self.currency == other.currency and self.amount == other.amount

    def __repr__(self) -> str:
        return f"Money({self.amount} {self.currency.value})"

    def _assert_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: {self.currency.value} vs {other.currency.value}. Convert first."
            )

    def to_float(self) -> float:
        """API-edge float exposure. Use only at display boundary."""
        return float(self.amount)

    def to_decimal(self) -> Decimal:
        return self.amount


def decimal_safe(value: Union[float, int, str, Decimal]) -> Decimal:
    """Convert any numeric to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def format_myr(amount: Union[float, int, Decimal, Money]) -> str:
    """Format amount in MYR with 2 decimal places."""
    if isinstance(amount, Money):
        amount = amount.amount
    return f"RM {decimal_safe(amount):,.2f}"


def format_usd(amount: Union[float, int, Decimal, Money]) -> str:
    """Format amount in USD with 2 decimal places."""
    if isinstance(amount, Money):
        if amount.currency != Currency.USD:
            raise ValueError(f"Expected USD, got {amount.currency.value}")
        amount = amount.amount
    return f"${decimal_safe(amount):,.2f}"
