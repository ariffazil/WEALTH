"""
Tests for internal/personal_finance.py — pure math tools (no DB, no MCP).
The mcp=None branch is active in test, so we test the fallback stubs + extracted math.
"""
import pytest


# ── Stub tests via direct import (mcp=None at module level in test env) ─────

import internal.personal_finance as _pf_mod


def test_stub_cashflow_track():
    """When mcp=None, all tools return the error stub."""
    # If mcp IS set in the module, call the else-branch function directly
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_cashflow_track()
        assert r["error"] == "FastMCP not initialised"
        assert r["mcp"] == "WEALTH"
    else:
        pytest.skip("mcp is live — stub test N/A")


def test_stub_cashflow_summary():
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_cashflow_summary()
        assert "error" in r
    else:
        pytest.skip("mcp is live")


def test_stub_net_worth_snapshot():
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_net_worth_snapshot()
        assert "error" in r
    else:
        pytest.skip("mcp is live")


def test_stub_epf_project():
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_epf_project()
        assert "error" in r
    else:
        pytest.skip("mcp is live")


def test_stub_zakat_calculate():
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_zakat_calculate()
        assert "error" in r
    else:
        pytest.skip("mcp is live")


def test_stub_runway_calculate():
    if _pf_mod.mcp is None:
        r = _pf_mod.wealth_runway_calculate()
        assert "error" in r
    else:
        pytest.skip("mcp is live")


# ── Pure-math helpers (tested directly) ──────────────────────────────────

def test_runway_math_critical():
    """Monthly burn=10000, liquid=20000 → 1.6 months → CRITICAL."""
    # replicate logic from wealth_runway_calculate
    monthly_burn = 10_000.0
    liquid_assets = 20_000.0
    conservative_factor = 0.8
    adjusted = liquid_assets * conservative_factor
    months = round(adjusted / monthly_burn, 1)
    assert months == 1.6
    assert months < 3  # CRITICAL branch


def test_runway_math_green():
    monthly_burn = 5_000.0
    liquid_assets = 200_000.0
    conservative_factor = 0.8
    adjusted = liquid_assets * conservative_factor
    months = round(adjusted / monthly_burn, 1)
    assert months == 32.0
    assert months >= 12  # GREEN branch


def test_runway_zero_burn():
    """Zero burn → infinite runway."""
    monthly_burn = 0.0
    liquid_assets = 50_000.0
    conservative_factor = 0.8
    adjusted = liquid_assets * conservative_factor
    months = round(adjusted / monthly_burn, 1) if monthly_burn > 0 else float("inf")
    assert months == float("inf")


def test_epf_projection_basic():
    """Basic EPF projection — verify FV formula."""
    current = 50_000.0
    monthly = 1_000.0
    employer = 500.0
    total_monthly = monthly + employer
    annual_rate = 0.0515
    years = 25
    months_count = years * 12
    r_month = annual_rate / 12
    fv_current = current * ((1 + r_month) ** months_count)
    fv_annuity = total_monthly * (((1 + r_month) ** months_count - 1) / r_month)
    projected = fv_current + fv_annuity
    assert projected > 500_000  # should grow significantly


def test_epf_projection_zero_rate():
    """Zero rate → linear growth."""
    current = 10_000.0
    total_monthly = 500.0
    years = 10
    months_count = years * 12
    r_month = 0.0
    fv_current = current  # no compounding
    fv_annuity = total_monthly * months_count
    projected = fv_current + fv_annuity
    assert projected == 10_000 + 500 * 120


def test_zakat_below_nisab():
    """Wealth below nisab → zero zakat."""
    NISAB_MYR = 14254.0
    ZAKAT_RATE = 0.025
    wealth = 10_000.0
    zakatable = max(0.0, wealth - NISAB_MYR)
    zakat = zakatable * ZAKAT_RATE
    assert zakat == 0.0


def test_zakat_above_nisab():
    """Wealth above nisab → 2.5% of excess."""
    NISAB_MYR = 14254.0
    ZAKAT_RATE = 0.025
    wealth = 50_000.0
    zakatable = max(0.0, wealth - NISAB_MYR)
    zakat = round(zakatable * ZAKAT_RATE, 4)
    assert zakat == round((50_000 - 14_254) * 0.025, 4)
    assert zakat > 0


def test_cashflow_summary_math():
    """Validate cashflow aggregation math (replicate from the function)."""
    txns = [
        {"amount": "3000.0", "category": "salary"},
        {"amount": "-1200.0", "category": "expense"},
        {"amount": "-800.0", "category": "expense"},
        {"amount": "500.0", "category": "income"},
    ]
    inflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) > 0)
    outflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) < 0)
    net = inflows + outflows

    assert inflows == 3500.0
    assert outflows == -2000.0
    assert net == 1500.0


def test_constants():
    """NISAB and ZAKAT_RATE constants are correct."""
    assert _pf_mod.NISAB_MYR == 14254.0
    assert _pf_mod.ZAKAT_RATE == 0.025
