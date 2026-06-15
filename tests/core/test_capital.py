"""
Tests for WEALTH Core — Capital domain engines.

Capital computation must be correct and bounded.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_core.capital import (
    compute_conservation,
    compute_flow,
    compute_runway,
    compute_gradient,
    compute_energy,
    compute_inertia,
)


class TestConservation:
    """Capital conservation must compute net worth correctly."""

    def test_basic(self):
        result = compute_conservation(
            assets=[{"value": 1000}, {"value": 500}],
            liabilities=[{"value": 300}],
        )
        assert result["net_worth"] == 1200
        assert result["asset_total"] == 1500
        assert result["liability_total"] == 300

    def test_empty(self):
        result = compute_conservation()
        assert result["net_worth"] == 0

    def test_negative_net_worth(self):
        result = compute_conservation(
            assets=[{"value": 100}],
            liabilities=[{"value": 500}],
        )
        assert result["net_worth"] == -400


class TestFlow:
    """Cash flow must compute correctly."""

    def test_positive_flow(self):
        result = compute_flow(
            income=[{"amount": 5000}],
            expenses=[{"amount": 3000}],
        )
        assert result["net_cashflow"] == 2000
        assert result["is_positive"] is True

    def test_negative_flow(self):
        result = compute_flow(
            income=[{"amount": 2000}],
            expenses=[{"amount": 3000}],
        )
        assert result["net_cashflow"] == -1000
        assert result["is_positive"] is False


class TestRunway:
    """Financial runway must compute correctly."""

    def test_basic_runway(self):
        result = compute_runway(100000, 5000)
        assert result["runway_months"] == 16.0  # 100000*0.8/5000

    def test_infinite_runway(self):
        result = compute_runway(100000, 0)
        assert result["runway_months"] == "infinite"

    def test_conservative_factor(self):
        result = compute_runway(100000, 5000, conservative_factor=0.5)
        assert result["runway_months"] == 10.0


class TestGradient:
    """Price gradient must compute correctly."""

    def test_basic_spread(self):
        result = compute_gradient(bid=100, ask=102)
        assert result["spread"] == 2
        assert result["mid_price"] == 101

    def test_with_reference(self):
        result = compute_gradient(bid=100, ask=102, reference_price=99)
        assert result["mispricing"] == 2  # 101 - 99


class TestEnergy:
    """Energy/productivity must compute correctly."""

    def test_efficient(self):
        result = compute_energy(output_value=150, input_cost=100)
        assert result["profitability_index"] == 1.5
        assert result["roi"] == 0.5
        assert result["is_efficient"] is True

    def test_inefficient(self):
        result = compute_energy(output_value=80, input_cost=100)
        assert result["profitability_index"] == 0.8
        assert result["is_efficient"] is False

    def test_zero_cost(self):
        result = compute_energy(output_value=100, input_cost=0)
        assert result["profitability_index"] == float("inf")


class TestInertia:
    """Leverage/inertia must compute correctly."""

    def test_healthy(self):
        result = compute_inertia(ebitda=1000, principal=2000, interest=100)
        assert result["dscr"] > 1.0
        assert result["is_healthy"] is True

    def test_unhealthy(self):
        result = compute_inertia(ebitda=100, principal=5000, interest=500)
        assert result["dscr"] < 1.25
        assert result["is_healthy"] is False
