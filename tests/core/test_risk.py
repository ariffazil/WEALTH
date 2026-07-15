"""
Tests for WEALTH Core — Risk domain engines.

Risk computation must be correct and honest.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations


from wealth_core.risk import (
    compute_emv,
    monte_carlo_simulation,
    compute_evoi,
    detect_false_confluence,
    compute_asymmetry,
)


class TestEMV:
    """Expected Monetary Value must compute correctly."""

    def test_basic(self):
        result = compute_emv([100, 0], [0.5, 0.5])
        assert result["emv"] == 50.0
        assert result["variance"] == 2500.0

    def test_all_same(self):
        result = compute_emv([100, 100], [0.5, 0.5])
        assert result["emv"] == 100.0
        assert result["variance"] == 0.0
        assert result["std_dev"] == 0.0

    def test_bid_surface_metadata_passes_through(self):
        result = compute_emv(
            [120, 0],
            [0.25, 0.75],
            bid_surface={
                "competitive_intensity": 0.42,
                "winner": "bidder_C",
                "winning_price": 98.5,
            },
        )
        assert result["scoring_surface_missing"] is False
        assert result["bid_competitive_intensity"] == 0.42
        assert result["bid_winner"] == "bidder_C"
        assert result["bid_winning_price"] == 98.5


class TestMonteCarlo:
    """Monte Carlo simulation must produce valid distributions."""

    def test_basic(self):
        result = monte_carlo_simulation(
            initial_value=1000,
            growth_rate=0.05,
            volatility=0.2,
            periods=10,
            simulations=1000,
            seed=42,
        )
        assert result["simulations"] == 1000
        assert result["periods"] == 10
        assert result["p10"] < result["p50"] < result["p90"]
        assert result["mean"] > 0

    def test_percentiles_ordered(self):
        result = monte_carlo_simulation(
            initial_value=100,
            growth_rate=0.0,
            volatility=0.1,
            periods=5,
            simulations=500,
            seed=123,
        )
        assert result["p10"] <= result["p25"] <= result["p50"] <= result["p75"] <= result["p90"]


class TestEVOI:
    """Expected Value of Information must compute correctly."""

    def test_worth_drilling(self):
        result = compute_evoi(
            prior_pos=0.3,
            posterior_pos=0.7,
            well_cost_musd=50,
            p50_value_musd=200,
        )
        assert result["worth_drilling"] is True
        assert result["evoi"] > 0

    def test_not_worth_drilling(self):
        result = compute_evoi(
            prior_pos=0.8,
            posterior_pos=0.85,
            well_cost_musd=100,
            p50_value_musd=50,
        )
        # Small improvement doesn't justify cost
        assert result["evoi"] < 0


class TestFalseConfluence:
    """False confluence detection must find correlated indicators."""

    def test_independent_indicators(self):
        indicators = [
            {"name": "RSI", "signal_class": "momentum", "value": 70},
            {"name": "P/E", "signal_class": "valuation", "value": 15},
            {"name": "D/E", "signal_class": "leverage", "value": 0.5},
        ]
        result = detect_false_confluence(indicators)
        assert result["is_false_confluence"] is False
        assert result["unique_classes"] == 3

    def test_correlated_indicators(self):
        indicators = [
            {"name": "RSI", "signal_class": "momentum", "value": 70},
            {"name": "MACD", "signal_class": "momentum", "value": 0.5},
            {"name": "Stochastic", "signal_class": "momentum", "value": 80},
            {"name": "ADX", "signal_class": "momentum", "value": 25},
        ]
        result = detect_false_confluence(indicators)
        assert result["is_false_confluence"] is True
        assert result["concentration"] == 1.0


class TestAsymmetry:
    """Risk asymmetry must detect skewed distributions."""

    def test_favorable(self):
        result = compute_asymmetry(
            upside_scenarios=[100, 200, 300],
            downside_scenarios=[-10, -20],
        )
        assert result["favorable"] is True
        assert result["up_down_ratio"] > 1.0

    def test_unfavorable(self):
        result = compute_asymmetry(
            upside_scenarios=[10, 20],
            downside_scenarios=[-100, -200, -300],
        )
        assert result["favorable"] is False

    def test_symmetric(self):
        result = compute_asymmetry(
            upside_scenarios=[100],
            downside_scenarios=[-100],
        )
        assert result["is_asymmetric"] is False
