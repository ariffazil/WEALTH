"""Test Ω-WEALTH-03: wealth_gradient_price — spread, pressure, mispricing."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.monolith import wealth_gradient_price


def test_spread_calculation():
    """Spread = ask - bid when both provided."""
    result = wealth_gradient_price(
        mode="spread",
        bid=1.50,
        ask=1.55,
    )
    assert result["tool"] == "wealth_gradient_price"
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    spread = result["primary_metrics"]["spread"]
    assert round(spread, 4) == 0.05


def test_spread_ask_greater_than_bid():
    """Normal market: ask > bid, spread > 0."""
    result = wealth_gradient_price(
        mode="spread",
        bid=10.00,
        ask=10.05,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    spread = result["primary_metrics"]["spread"]
    assert round(spread, 4) == 0.05
    assert result["primary_metrics"]["ask"] > result["primary_metrics"]["bid"]


def test_spread_equal_bid_ask():
    """Zero spread means bid == ask (rare, possible in stablecoins or fixed prices)."""
    result = wealth_gradient_price(
        mode="spread",
        bid=25.00,
        ask=25.00,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    spread = result["primary_metrics"]["spread"]
    assert spread == 0.0


def test_spread_large():
    """Wide spread indicates low liquidity or high volatility."""
    result = wealth_gradient_price(
        mode="spread",
        bid=1.00,
        ask=1.50,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    spread = result["primary_metrics"]["spread"]
    assert spread == 0.50


def test_pressure_mode():
    """Pressure mode maps price direction signal."""
    result = wealth_gradient_price(
        mode="pressure",
        reference_price=100.0,
        pressure_direction="up",
    )
    assert result["tool"] == "wealth_gradient_price"
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    assert result["primary_metrics"]["pressure"] == "up"


def test_mispricing_mode():
    """Mispricing mode returns detection status."""
    result = wealth_gradient_price(
        mode="mispricing",
        reference_price=50.0,
    )
    assert result["tool"] == "wealth_gradient_price"
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
