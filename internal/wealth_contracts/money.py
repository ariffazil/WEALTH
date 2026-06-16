"""
WEALTH Money — Decimal-safe money arithmetic helpers.

Anti-pattern in finance: float64 rounding errors.
Solution: round-half-even at the API edge, Decimal internally.
"""

from decimal import ROUND_HALF_EVEN, Decimal

TWOPLACES = Decimal("0.01")


def round_money(amount: Decimal, places: int = 2) -> Decimal:
    """Round Decimal to `places` decimals using bankers' rounding."""
    quant = Decimal(10) ** -places
    return amount.quantize(quant, rounding=ROUND_HALF_EVEN)


def myr_to_usd(myr: Decimal, rate: Decimal = Decimal("0.22")) -> Decimal:
    """Convert MYR to USD. Default rate is ~0.22 USD/MYR; pass live rate for accuracy."""
    return round_money(myr * rate)


def usd_to_myr(usd: Decimal, rate: Decimal = Decimal("4.55")) -> Decimal:
    """Convert USD to MYR. Default rate is ~4.55 MYR/USD; pass live rate for accuracy."""
    return round_money(usd * rate)
