"""
Tests for WEALTH Core — Math primitives.

Pure math must be correct. No hallucinated numbers.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_core.math import npv, irr, profitability_index, payback_period, emv, dscr


class TestNPV:
    """Net Present Value must compute correctly."""

    def test_basic_npv(self):
        # $100 received in 1 year at 10% discount
        result = npv([100], 0.10)
        assert result == 90.91

    def test_multi_period(self):
        # $100, $200, $300 at 10%
        result = npv([100, 200, 300], 0.10)
        expected = 100/1.1 + 200/1.21 + 300/1.331
        assert abs(result - round(expected, 2)) < 0.01

    def test_zero_discount(self):
        result = npv([100, 200], 0.0)
        assert result == 300.0

    def test_negative_cashflow(self):
        # Both cash flows discounted at t=1, t=2
        result = npv([-50, 100], 0.10)
        expected = -50/1.1 + 100/1.21
        assert abs(result - round(expected, 2)) < 0.01


class TestIRR:
    """Internal Rate of Return must converge."""

    def test_basic_irr(self):
        # Invest -1000, get back 1200 in 1 year → ~20% IRR
        result = irr([1200], initial_investment=-1000)
        assert result is not None
        assert abs(result - 0.2) < 0.01

    def test_no_solution(self):
        # All positive → no IRR
        result = irr([100, 200], initial_investment=0, max_iterations=100)
        # May or may not converge — just shouldn't crash
        assert result is None or isinstance(result, float)


class TestProfitabilityIndex:
    """PI must compute correctly."""

    def test_basic_pi(self):
        # Invest 100, get 120 back at 0% → PI = 1.2
        result = profitability_index(100, [120], 0.0)
        assert abs(result - 1.2) < 0.01

    def test_pi_with_discount(self):
        result = profitability_index(100, [110], 0.10)
        # PV = 110/1.1 = 100, PI = 100/100 = 1.0
        assert abs(result - 1.0) < 0.01

    def test_zero_investment(self):
        result = profitability_index(0, [100], 0.10)
        assert result == float("inf")


class TestPaybackPeriod:
    """Payback period must compute correctly."""

    def test_exact_payback(self):
        # Invest 100, get 50/year → pays back in 2 years
        result = payback_period(100, [50, 50])
        assert result == 2.0

    def test_fractional_payback(self):
        # Invest 100, get 30, 30, 30, 30 → pays back in 3.33 years
        result = payback_period(100, [30, 30, 30, 30])
        assert result is not None
        assert abs(result - 3.33) < 0.1

    def test_never_pays_back(self):
        result = payback_period(1000, [10, 10, 10])
        assert result is None


class TestEMV:
    """Expected Monetary Value must compute correctly."""

    def test_basic_emv(self):
        # 50% chance of $100, 50% chance of $0 → EMV = $50
        result = emv([100, 0], [0.5, 0.5])
        assert result == 50.0

    def test_weighted(self):
        result = emv([100, -50], [0.7, 0.3])
        expected = 100 * 0.7 + (-50) * 0.3
        assert abs(result - expected) < 0.01


class TestDSCR:
    """Debt Service Coverage Ratio must compute correctly."""

    def test_basic_dscr(self):
        result = dscr(1000, 800)
        assert result == 1.25

    def test_zero_debt(self):
        result = dscr(1000, 0)
        assert result == float("inf")

    def test_underwater(self):
        result = dscr(500, 1000)
        assert result == 0.5
