"""
Tests for WEALTH Intelligence Gates — Constitutional Enforcement Layer
═══════════════════════════════════════════════════════════════════════

10 architectural gaps tested against the two AI contrast failures:
- PETRONAS-EnQuest: capital structure math, confluence, materiality
- PCHEM: stale data, investment advice, regime change, probability

DITEMPA BUKAN DIBERI — Tests are forged, not given.
"""

import pytest
from datetime import datetime, timezone, timedelta

from internal.wealth_gates import (
    GateVerdict,
    DataPoint,
    Scenario,
    Signal,
    PreTradeCheck,
    gap1_investment_advice_filter,
    gap2_realtime_data_verification,
    gap3_ttm_completeness,
    gap4_false_confluence,
    gap5_single_catalyst_detector,
    gap6_regime_change_detector,
    gap7_probability_validation,
    gap8_negative_beta_check,
    gap9_capital_materiality,
    gap10_pre_trade_enforcement,
    run_all_gates,
    summarize_report,
)


# ─── GAP1: Investment Advice Filter ──────────────────────────────────────────

class TestGap1InvestmentAdviceFilter:
    def test_blocks_specific_price_target(self):
        text = "Target price: RM 5.40 with stop-loss at RM 4.20"
        result = gap1_investment_advice_filter(text)
        assert result.verdict == GateVerdict.BLOCK
        assert len(result.violations) > 0

    def test_blocks_buy_sell_rating(self):
        text = "Rating: BUY with accumulate on weakness recommendation"
        result = gap1_investment_advice_filter(text)
        assert result.verdict in (GateVerdict.BLOCK, GateVerdict.WARN)

    def test_blocks_entry_zone(self):
        text = "Entry zone at RM 4.30-4.50, look for bullish engulfing candlestick"
        result = gap1_investment_advice_filter(text)
        assert result.verdict == GateVerdict.BLOCK

    def test_blocks_risk_reward(self):
        text = "Risk:Reward ~1:2 if entering at RM 4.50"
        result = gap1_investment_advice_filter(text)
        assert result.verdict in (GateVerdict.BLOCK, GateVerdict.WARN)

    def test_allows_mechanism_explanation(self):
        text = "This is how PSCs work: the operator bears capex risk"
        result = gap1_investment_advice_filter(text)
        assert result.verdict == GateVerdict.PASS

    def test_allows_sector_analysis(self):
        text = "The petrochemical sector is cyclical with commodity pricing"
        result = gap1_investment_advice_filter(text)
        assert result.verdict == GateVerdict.PASS

    def test_pchem_report_would_be_blocked(self):
        """Test against the actual PCHEM report content."""
        text = """
        Rating: HOLD / ACCUMULATE ON WEAKNESS
        Entry Strategy: Look for bullish candlestick patterns near the RM 4.30 – RM 4.50 support zone
        Stop-loss: Below RM 4.20
        Target 1: RM 5.00 (psychological resistance)
        Target 2: RM 5.40 (analyst target)
        Risk:Reward: ~1:2 if entering at RM 4.50
        Wait for T1 confirmation, look for SAR to flip bullish before entering
        """
        result = gap1_investment_advice_filter(text)
        assert result.verdict == GateVerdict.BLOCK
        assert len(result.violations) >= 3


# ─── GAP2: Real-Time Data Verification ───────────────────────────────────────

class TestGap2RealTimeDataVerification:
    def test_passes_fresh_data(self):
        now = datetime.now(timezone.utc)
        points = [
            DataPoint(value=5.48, source="Yahoo Finance",
                      timestamp=now.isoformat(), freshness_hours=0.5),
        ]
        result = gap2_realtime_data_verification(points)
        assert result.verdict == GateVerdict.PASS

    def test_warns_stale_data(self):
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        points = [
            DataPoint(value=4.44, source="AI Report",
                      timestamp=old.isoformat(), freshness_hours=48),
        ]
        result = gap2_realtime_data_verification(points)
        assert result.verdict == GateVerdict.WARN

    def test_blocks_critically_stale(self):
        ancient = datetime.now(timezone.utc) - timedelta(hours=100)
        points = [
            DataPoint(value=4.44, source="AI Report",
                      timestamp=ancient.isoformat(), freshness_hours=100),
        ]
        result = gap2_realtime_data_verification(points)
        assert result.verdict == GateVerdict.BLOCK

    def test_needs_data_when_empty(self):
        result = gap2_realtime_data_verification([])
        assert result.verdict == GateVerdict.NEEDS_DATA


# ─── GAP3: TTM-Completeness Gate ─────────────────────────────────────────────

class TestGap3TTMCompleteness:
    def test_passes_with_ttm(self):
        q = {"eps": 0.05, "margin": 5.7}
        ttm = {"eps_ttm": 0.10, "margin_ttm": 3.2}
        result = gap3_ttm_completeness(q, ttm)
        assert result.verdict == GateVerdict.PASS

    def test_blocks_hidden_negatives(self):
        q = {"eps": 0.05, "margin": 5.7}
        ttm = {"eps_ttm": -0.22, "margin_ttm": -6.42}
        result = gap3_ttm_completeness(q, ttm)
        assert result.verdict == GateVerdict.BLOCK
        assert any("negative hidden" in v.lower() for v in result.violations)

    def test_warns_missing_ttm(self):
        q = {"eps": 0.05, "margin": 5.7}
        ttm = {}  # No TTM data
        result = gap3_ttm_completeness(q, ttm)
        assert result.verdict == GateVerdict.WARN

    def test_pchem_scenario(self):
        """PCHEM Q1 profit + TTM loss = should be caught."""
        q = {"net_profit": 401_000_000}
        ttm = {"net_profit_ttm": -1_720_000_000}
        result = gap3_ttm_completeness(q, ttm)
        assert result.verdict == GateVerdict.BLOCK


# ─── GAP4: False Confluence Detector ─────────────────────────────────────────

class TestGap4FalseConfluence:
    def test_detects_single_factor_confluence(self):
        signals = [
            Signal(name="Hormuz disruption", underlying_factor="geopolitical_supply_shock"),
            Signal(name="Naphtha spike", underlying_factor="geopolitical_supply_shock"),
            Signal(name="Higher spreads", underlying_factor="geopolitical_supply_shock"),
            Signal(name="Competitor margins", underlying_factor="geopolitical_supply_shock"),
        ]
        result = gap4_false_confluence(signals)
        assert result.verdict == GateVerdict.BLOCK
        assert "false confluence" in result.violations[0].lower()

    def test_passes_independent_signals(self):
        signals = [
            Signal(name="Revenue growth", underlying_factor="fundamentals"),
            Signal(name="Sector rotation", underlying_factor="market_flow"),
            Signal(name="Technical breakout", underlying_factor="price_action"),
            Signal(name="Insider buying", underlying_factor="governance"),
        ]
        result = gap4_false_confluence(signals)
        assert result.verdict == GateVerdict.PASS

    def test_warns_partial_concentration(self):
        signals = [
            Signal(name="Signal A", underlying_factor="factor_1"),
            Signal(name="Signal B", underlying_factor="factor_1"),
            Signal(name="Signal C", underlying_factor="factor_2"),
            Signal(name="Signal D", underlying_factor="factor_3"),
        ]
        result = gap4_false_confluence(signals)
        # 3 unique factors / 4 signals = 0.75 ratio (>0.5, so no block)
        # But factor_1 has 2 signals — check for concentration warning
        assert result.verdict in (GateVerdict.PASS, GateVerdict.WARN)


# ─── GAP5: Single-Catalyst Detector ──────────────────────────────────────────

class TestGap5SingleCatalyst:
    def test_blocks_single_catalyst_no_contrarian(self):
        result = gap5_single_catalyst_detector(
            thesis="PCHEM bull case",
            catalysts=["Hormuz closure"],
            contrarian_scenarios=[],
        )
        assert result.verdict == GateVerdict.BLOCK

    def test_warns_single_catalyst_with_contrarian(self):
        result = gap5_single_catalyst_detector(
            thesis="PCHEM bull case",
            catalysts=["Hormuz closure"],
            contrarian_scenarios=["If Hormuz reopens, margins compress"],
        )
        assert result.verdict == GateVerdict.WARN

    def test_passes_multiple_catalysts(self):
        result = gap5_single_catalyst_detector(
            thesis="Growth thesis",
            catalysts=["Revenue growth", "Margin expansion", "New product"],
            contrarian_scenarios=[],
        )
        assert result.verdict == GateVerdict.PASS


# ─── GAP6: Regime Change Detector ────────────────────────────────────────────

class TestGap6RegimeChange:
    def test_detects_regime_change(self):
        thesis = "PCHEM bullish due to US/Israel-Iran conflict and Strait of Hormuz closure"
        headlines = [
            "IMF chief hails US-Iran ceasefire in Washington",
            "Ringgit climbs as crude prices tumble on Hormuz hopes",
            "Bursa Malaysia ends higher on easing oil prices",
        ]
        result = gap6_regime_change_detector(thesis, headlines)
        assert result.verdict == GateVerdict.BLOCK

    def test_passes_no_regime_change(self):
        thesis = "PCHEM bullish due to long-term structural advantage in gas feedstock"
        headlines = [
            "Bursa Malaysia ends higher on technology buying",
            "Ringgit strengthens against dollar",
        ]
        result = gap6_regime_change_detector(thesis, headlines)
        assert result.verdict == GateVerdict.PASS


# ─── GAP7: Probability Validation Gate ───────────────────────────────────────

class TestGap7ProbabilityValidation:
    def test_blocks_no_evidence(self):
        scenarios = [
            Scenario(name="Bull", probability=0.30, evidence_basis=""),
            Scenario(name="Base", probability=0.50, evidence_basis=""),
            Scenario(name="Bear", probability=0.20, evidence_basis=""),
        ]
        result = gap7_probability_validation(scenarios)
        assert result.verdict == GateVerdict.BLOCK

    def test_blocks_inverted_probability(self):
        scenarios = [
            Scenario(name="Bull", probability=0.30, evidence_basis="conflict prolongs"),
            Scenario(name="Base", probability=0.50, evidence_basis="partial resolution"),
            Scenario(
                name="Bear", probability=0.20,
                evidence_basis="rapid ceasefire",
                is_currently_happening=True,  # This is happening NOW
            ),
        ]
        result = gap7_probability_validation(scenarios)
        assert result.verdict == GateVerdict.BLOCK
        assert any("inverted" in v.lower() for v in result.violations)

    def test_passes_well_evidenced(self):
        scenarios = [
            Scenario(name="Bull", probability=0.25, evidence_basis="strong Q1 + sustained demand"),
            Scenario(name="Base", probability=0.50, evidence_basis="moderation expected"),
            Scenario(name="Bear", probability=0.25, evidence_basis="recession risk"),
        ]
        result = gap7_probability_validation(scenarios)
        # May warn about round numbers but shouldn't block
        assert result.verdict in (GateVerdict.PASS, GateVerdict.WARN)


# ─── GAP8: Negative Beta Check ───────────────────────────────────────────────

class TestGap8NegativeBeta:
    def test_blocks_negative_beta_momentum(self):
        result = gap8_negative_beta_check("PCHEM", -0.78, "swing trading")
        assert result.verdict == GateVerdict.BLOCK
        assert any("inverse" in v.lower() for v in result.violations)

    def test_warns_negative_beta_other(self):
        result = gap8_negative_beta_check("PCHEM", -0.78, "long-term holding")
        assert result.verdict == GateVerdict.WARN

    def test_passes_positive_beta(self):
        result = gap8_negative_beta_check("MAYBANK", 1.2, "swing trading")
        assert result.verdict == GateVerdict.PASS


# ─── GAP9: Capital Materiality Check ─────────────────────────────────────────

class TestGap9CapitalMateriality:
    def test_warns_immaterial(self):
        result = gap9_capital_materiality(
            theoretical_correctness=True,
            economic_magnitude=500_000,  # Below RM 1M threshold
        )
        assert result.verdict == GateVerdict.WARN

    def test_passes_material(self):
        result = gap9_capital_materiality(
            theoretical_correctness=True,
            economic_magnitude=833_000_000,  # EnQuest deal
        )
        assert result.verdict == GateVerdict.PASS
        assert result.details["material"] is True

    def test_warns_unknown_magnitude(self):
        result = gap9_capital_materiality(
            theoretical_correctness=True,
            economic_magnitude=None,
        )
        assert result.verdict == GateVerdict.WARN


# ─── GAP10: Pre-Trade Gate Enforcement ───────────────────────────────────────

class TestGap10PreTradeEnforcement:
    def test_blocks_majority_failure(self):
        checks = [
            PreTradeCheck("Stop Loss", False, "NO STOP LOSS"),
            PreTradeCheck("Position Size", False, "Not specified"),
            PreTradeCheck("Risk Under 1%", True),
            PreTradeCheck("R Multiple", False, "R not calculated"),
            PreTradeCheck("Liquidity", False, "Insufficient"),
            PreTradeCheck("Sector Exposure", False, "Concentrated"),
            PreTradeCheck("Market Regime", True),
            PreTradeCheck("No Emotional Trigger", True),
            PreTradeCheck("Reason Documented", False, "No reason"),
        ]
        result = gap10_pre_trade_enforcement(checks)
        assert result.verdict == GateVerdict.BLOCK

    def test_passes_all_gates(self):
        checks = [
            PreTradeCheck("Stop Loss", True),
            PreTradeCheck("Position Size", True),
            PreTradeCheck("Risk Under 1%", True),
        ]
        result = gap10_pre_trade_enforcement(checks)
        assert result.verdict == GateVerdict.PASS


# ─── Integration: Full Gate Runner ───────────────────────────────────────────

class TestFullGateRunner:
    def test_pchem_report_full_analysis(self):
        """Simulate running all gates against the PCHEM report."""
        report = run_all_gates(
            # GAP1: Investment advice
            text="Rating: HOLD / ACCUMULATE ON WEAKNESS. "
                 "Entry zone at RM 4.30-4.50. Stop-loss below RM 4.20. "
                 "Target 1: RM 5.00. Risk:Reward ~1:2.",
            # GAP3: TTM
            quarterly_metrics={"net_profit": 401_000_000},
            ttm_metrics={"net_profit_ttm": -1_720_000_000},
            # GAP4: Confluence
            signals=[
                Signal("Hormuz disruption", "geopolitical"),
                Signal("Naphtha spike", "geopolitical"),
                Signal("Higher spreads", "geopolitical"),
                Signal("Consensus upside", "geopolitical"),
            ],
            # GAP5: Single catalyst
            catalysts=["Hormuz closure"],
            contrarian_scenarios=[],
            # GAP6: Regime change
            thesis="PCHEM bullish due to Hormuz closure",
            current_headlines=[
                "IMF hails US-Iran ceasefire",
                "Crude prices tumble on peace deal",
            ],
            # GAP7: Probability
            scenarios=[
                Scenario("Bull", 0.30, "conflict prolongs"),
                Scenario("Base", 0.50, "partial resolution"),
                Scenario("Bear", 0.20, "rapid ceasefire", is_currently_happening=True),
            ],
            # GAP8: Beta
            ticker="PCHEM",
            beta=-0.78,
            recommended_strategy="swing trading",
        )

        assert report.overall_verdict == GateVerdict.BLOCK
        assert report.haram_violations >= 3
        assert len(report.floors_triggered) >= 3

    def test_enquest_report_analysis(self):
        """Simulate running gates against the PETRONAS-EnQuest analysis."""
        report = run_all_gates(
            # GAP4: Confluence — false confluence from the first AI
            signals=[
                Signal("PSC framework", "standard_industry_practice"),
                Signal("Risk sharing", "standard_industry_practice"),
                Signal("Resource ownership", "standard_industry_practice"),
                Signal("Portfolio optimization", "standard_industry_practice"),
            ],
            # GAP9: Materiality
            theoretical_correctness=True,
            economic_magnitude=833_000_000,  # $833M deal
            # GAP5: Single catalyst
            thesis="PETRONAS portfolio optimization",
            catalysts=["mature asset management"],
            contrarian_scenarios=[
                "EnQuest takes on excessive debt",
                "Revenue flows to UK shareholders over 15 years",
            ],
        )

        # Should pass investment advice (no specific recommendations)
        # Should flag false confluence
        # Should pass materiality
        gap4_result = next(r for r in report.results if r.gate_id == "GAP4")
        assert gap4_result.verdict == GateVerdict.BLOCK

    def test_summarize_report(self):
        """Test report summarization."""
        report = run_all_gates(
            text="Buy at RM 5.00 with stop-loss at RM 4.50",
        )
        summary = summarize_report(report)
        assert "WEALTH INTELLIGENCE GATE REPORT" in summary
        assert "GAP1" in summary
