"""Test Ω-WEALTH-06: wealth_time_discount — NPV, IRR, payback."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.monolith import wealth_time_discount, wealth_flow_liquidity


def test_npv_positive():
    """NPV = present value of cash flows minus investment."""
    result = wealth_time_discount(
        mode="npv",
        initial_investment=1000,
        cash_flows=[300, 400, 500, 600],
        discount_rate=0.10,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    # NPV should be positive: cash flows outweigh the investment
    npv = result["primary_metrics"]["npv"]
    assert npv is not None
    assert npv > 0


def test_npv_negative():
    """When costs exceed benefits, NPV is negative."""
    result = wealth_time_discount(
        mode="npv",
        initial_investment=10000,
        cash_flows=[100, 100, 100],
        discount_rate=0.10,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    npv = result["primary_metrics"]["npv"]
    assert npv is not None
    assert npv < 0


def test_npv_zero_discount():
    """NPV with zero discount rate = sum of cash flows minus investment."""
    result = wealth_time_discount(
        mode="npv",
        initial_investment=5000,
        cash_flows=[2000, 2000, 2000],
        discount_rate=0.0,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    npv = result["primary_metrics"]["npv"]
    # 2000 + 2000 + 2000 - 5000 = 1000
    assert npv is not None
    assert round(npv, 2) == 1000.0


def test_irr_calculation():
    """IRR is the discount rate that makes NPV = 0."""
    result = wealth_time_discount(
        mode="irr",
        initial_investment=1000,
        cash_flows=[300, 400, 500, 600],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    irr = result["primary_metrics"]["irr"]
    assert irr is not None


def test_irr_no_solution():
    """Flat cash flows may produce no IRR."""
    result = wealth_time_discount(
        mode="irr",
        initial_investment=100,
        cash_flows=[50, 50, 50],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}


def test_payback_period():
    """Payback: time to recover initial investment."""
    result = wealth_time_discount(
        mode="payback",
        initial_investment=1000,
        cash_flows=[250, 250, 250, 250, 250],
        discount_rate=0.0,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    # With zero discount, 1000 / 250 = 4 periods
    payback = result["primary_metrics"].get("payback_periods")
    if payback is not None:
        assert payback <= 5


def test_payback_never():
    """If cash flows never cover investment, payback is undefined."""
    result = wealth_time_discount(
        mode="payback",
        initial_investment=10000,
        cash_flows=[100, 100],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}


def test_compound_growth_flow():
    """Compound growth via wealth_flow_liquidity velocity mode."""
    result = wealth_flow_liquidity(
        mode="velocity",
        principal=10000,
        rate=0.10,
        years=10,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN"}
    forecast = result["primary_metrics"].get("growth_forecast", {})
    mid = forecast.get("mid", 0)
    assert mid > 20000  # 10000 * 1.1^10 ≈ 25937
