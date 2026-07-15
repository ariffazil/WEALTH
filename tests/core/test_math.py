"""
Tests for WEALTH Core — Math primitives.
Updated 2026-07-07: NPV/IRR convention — CF[0] at t=0.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from wealth_core.math import npv, irr, profitability_index, payback_period, emv, dscr


class TestNPV:
    """Net Present Value — CF[0] at t=0, CF[i] at t=i."""

    def test_basic_npv(self):
        # $100 received in 1 year at 10% discount
        result = npv([0, 100], 0.10)
        assert result == 90.91

    def test_multi_period(self):
        # $0 at t=0, then $100, $200, $300 at t=1,2,3, 10%
        result = npv([0, 100, 200, 300], 0.10)
        expected = 0 + 100 / 1.1 + 200 / 1.21 + 300 / 1.331
        assert abs(result - round(expected, 2)) < 0.01

    def test_zero_discount(self):
        result = npv([100, 200], 0.0)
        assert result == 300.0

    def test_negative_cashflow(self):
        # $0 at t=0, -$50 at t=1, $100 at t=2 at 10%
        result = npv([0, -50, 100], 0.10)
        expected = 0 - 50 / 1.1 + 100 / 1.21
        assert abs(result - round(expected, 2)) < 0.01

    def test_investment_at_t0(self):
        # -100 at t=0, 30/year for 5 years (SVB backtest golden vector)
        result = npv([-100, 30, 30, 30, 30, 30], 0.10)
        assert result == 13.72

    def test_npv_zero_rate(self):
        result = npv([-100, 40, 40, 40], 0.0)
        assert result == 20.0


class TestIRR:
    """Internal Rate of Return — CF[0] at t=0."""

    def test_basic_irr(self):
        # Invest -100 at t=0, get 110 at t=1 → 10% IRR
        result = irr([-100, 110])
        assert result is not None
        assert abs(result - 0.10) < 0.01

    def test_five_period_irr(self):
        # SVB backtest golden vector
        result = irr([-100, 30, 40, 50, 60])
        assert result is not None
        assert 0.20 < result < 0.30

    def test_no_solution(self):
        # All positive → no sign change, no IRR
        result = irr([100, 200])
        assert result is None


class TestProfitabilityIndex:
    """PI — initial_investment separate, cash_flows at t=1+."""

    def test_basic_pi(self):
        result = profitability_index(100, [120], 0.0)
        assert abs(result - 1.2) < 0.01

    def test_pi_with_discount(self):
        result = profitability_index(100, [110], 0.10)
        assert abs(result - 1.0) < 0.01

    def test_zero_investment(self):
        result = profitability_index(0, [100], 0.10)
        assert result == float("inf")


class TestPaybackPeriod:
    """Payback period."""

    def test_exact_payback(self):
        result = payback_period(100, [50, 50])
        assert result == 2.0

    def test_fractional_payback(self):
        result = payback_period(100, [30, 30, 30, 30])
        assert result is not None
        assert abs(result - 3.33) < 0.1

    def test_never_pays_back(self):
        result = payback_period(1000, [10, 10, 10])
        assert result is None


class TestEMV:
    """Expected Monetary Value."""

    def test_basic_emv(self):
        result = emv([100, 0], [0.5, 0.5])
        assert result == 50.0

    def test_weighted(self):
        result = emv([100, -50], [0.7, 0.3])
        expected = 100 * 0.7 + (-50) * 0.3
        assert abs(result - expected) < 0.01

    def test_svb_golden(self):
        result = emv([-50, 10, 80], [0.3, 0.5, 0.2])
        assert result == 6.0


class TestDSCR:
    """Debt Service Coverage Ratio."""

    def test_basic_dscr(self):
        result = dscr(1000, 800)
        assert result == 1.25

    def test_zero_debt(self):
        result = dscr(1000, 0)
        assert result == float("inf")

    def test_underwater(self):
        result = dscr(500, 1000)
        assert result == 0.5
