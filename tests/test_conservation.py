"""Test Ω-WEALTH-01: wealth_conservation_capital — net worth, snapshot, ledger."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.monolith import wealth_conservation_capital


def test_net_worth_assets_minus_liabilities():
    """Net worth = total assets - total liabilities."""
    result = wealth_conservation_capital(
        mode="state",
        assets=[{"name": "Cash", "value": 100000}, {"name": "Stocks", "value": 50000}],
        liabilities=[{"name": "Mortgage", "outstanding": 80000}],
    )
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    assert result["primary_metrics"]["net_worth"] == 70000.0
    assert result["primary_metrics"]["assets"] == 150000.0
    assert result["primary_metrics"]["liabilities"] == 80000.0


def test_empty_portfolio():
    """Empty assets and liabilities should return zero or baseline."""
    result = wealth_conservation_capital(mode="state", assets=[], liabilities=[])
    assert result["status"] in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    # Empty portfolio — net worth should be 0
    assert result["primary_metrics"]["net_worth"] == 0.0
    assert result["primary_metrics"]["assets"] == 0.0
    assert result["primary_metrics"]["liabilities"] == 0.0


def test_single_asset_no_liabilities():
    """Single asset with no liabilities = net worth equals asset value."""
    result = wealth_conservation_capital(
        mode="state",
        assets=[{"name": "Emergency Fund", "value": 25000}],
        liabilities=[],
    )
    assert result["primary_metrics"]["net_worth"] == 25000.0
    assert result["primary_metrics"]["liabilities"] == 0.0


def test_negative_net_worth():
    """When liabilities exceed assets, net worth is negative."""
    result = wealth_conservation_capital(
        mode="state",
        assets=[{"name": "Car", "value": 30000}],
        liabilities=[{"name": "Car Loan", "outstanding": 45000}],
    )
    assert result["primary_metrics"]["net_worth"] == -15000.0
    assert result["primary_metrics"]["assets"] == 30000.0
    assert result["primary_metrics"]["liabilities"] == 45000.0


def test_multiple_liabilities_summed():
    """Multiple liabilities are summed correctly."""
    result = wealth_conservation_capital(
        mode="state",
        assets=[{"name": "House", "value": 500000}],
        liabilities=[
            {"name": "Mortgage", "outstanding": 350000},
            {"name": "Credit Card", "outstanding": 5000},
            {"name": "Car Loan", "principal": 20000},
        ],
    )
    # liabilities: 350000 + 5000 + 20000 = 375000
    # net worth: 500000 - 375000 = 125000
    assert result["primary_metrics"]["net_worth"] == 125000.0
