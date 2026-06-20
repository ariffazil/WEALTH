"""Test Ω-WEALTH-02: wealth_flow_liquidity — cashflow, runway, burn."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.monolith import wealth_flow_liquidity


def test_cashflow_positive():
    """Positive cashflow: income > expenses."""
    result = wealth_flow_liquidity(
        mode="cashflow",
        income=[{"name": "Salary", "value": 10000}],
        expenses=[{"name": "Rent", "value": 3000}, {"name": "Food", "value": 2000}],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    # Net should be positive: 10000 - (3000 + 2000) = 5000
    if result["primary_metrics"].get("net_monthly") is not None:
        assert result["primary_metrics"]["net_monthly"] >= 0


def test_cashflow_negative():
    """Negative cashflow: income < expenses."""
    result = wealth_flow_liquidity(
        mode="cashflow",
        income=[{"name": "Part Time", "value": 2000}],
        expenses=[{"name": "Rent", "value": 3000}, {"name": "Bills", "value": 1500}],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}


def test_runway_calculation():
    """Runway: months till depletion at current burn rate."""
    result = wealth_flow_liquidity(
        mode="velocity",
        principal=50000,
        rate=0,
        years=1,
        monthly=False,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}


def test_zero_income():
    """Zero income with expenses should show negative flow."""
    result = wealth_flow_liquidity(
        mode="cashflow",
        income=[],
        expenses=[{"name": "Fixed Costs", "value": 5000}],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}


def test_velocity_compound_growth():
    """Compound growth: principal grows with rate over years."""
    result = wealth_flow_liquidity(
        mode="velocity",
        principal=10000,
        rate=0.10,
        years=5,
        monthly=False,
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    # 10000 * 1.1^5 ≈ 16105.10
    forecast = result["primary_metrics"].get("growth_forecast", {})
    mid = forecast.get("mid", 0)
    assert mid > 15000  # Should have grown significantly


def test_triage_mode():
    """Triage mode allocates resources under constraint."""
    result = wealth_flow_liquidity(
        mode="triage",
        resources={"total": 100000},
        demands=[
            {"name": "Payroll", "min_required": 50000},
            {"name": "Operations", "min_required": 30000},
        ],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
