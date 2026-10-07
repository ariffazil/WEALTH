"""Test suite for M7 — Survival and Path-Risk organ.

Covers:
    * 7.1 leverage_stress  — P(margin_breach) at given leverage
    * 7.2 stop_risk        — P(stop hit before target)
    * 7.3 expected_shortfall — CVaR at confidence level
    * 7.4 liquidation_cost — spread + market impact
    * 7.5 max_survivable_size — Kelly × survival
    * 7.6 thesis_half_life — autocorrelation decay
    * 7.7 abstention_gate — ACT/REDUCE/HOLD/BLOCK verdict
    * Disagreement preservation (F/T/D are NOT merged)
    * Safety gate regime-action table
    * End-to-end run_m7 with the real M5 forecast JSON
    * Honest fallback when data is missing

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, "/root/WEALTH")

from forecast.m7 import (  # noqa: E402
    M7_AUTHORITY,
    M7_SCHEMA,
    M7_STATUS,
    REGIME_ACTION_TABLE,
    VERDICTS,
    assess_disagreement,
    compute_cvar,
    compute_liquidation_cost,
    compute_margin_breach_probability,
    compute_max_survivable_size,
    compute_stop_risk,
    compute_thesis_half_life,
    decide_safety_gate,
    run_m7,
    widen_for_disagreement,
    write_honest_caveat_receipt,
    write_m7_receipt,
)
from forecast.m7.abstention_gate import SafetyGateVerdict  # noqa: E402
from forecast.m7.disagreement import DisagreementVector  # noqa: E402
from forecast.m7.expected_shortfall import CVaRResult  # noqa: E402
from forecast.m7.leverage_stress import LeverageStressResult  # noqa: E402
from forecast.m7.liquidation_cost import LiquidationCostResult  # noqa: E402
from forecast.m7.max_survivable_size import MaxSurvivableSizeResult  # noqa: E402
from forecast.m7.stop_risk import StopRiskResult  # noqa: E402
from forecast.m7.thesis_half_life import ThesisHalfLifeResult  # noqa: E402


# ── Shared fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def m5_forecast() -> dict:
    """Load the real M5 latest forecast JSON (sandbox yfinance cascade)."""
    path = Path("/root/WEALTH/forecast/m5/latest_forecast.json")
    if not path.exists():
        pytest.skip("M5 latest_forecast.json not on disk")
    with open(path) as f:
        return json.load(f)


def _synthetic_m5_horizon(*, sigma: float = 0.02, asymmetry: float = 0.0, regime: str = "RANGE") -> dict:
    """Build a synthetic M5 forecast dict with one horizon."""
    p50 = 1000.0
    # Add a small asymmetry: positive asymmetry ⇒ p90 further than p10.
    upper_mult = np.exp(sigma * 1.2816 + asymmetry)
    lower_mult = np.exp(-sigma * 1.2816 + asymmetry)
    p90 = p50 * upper_mult
    p10 = p50 * lower_mult
    return {
        "forecast_id": "test-m7",
        "origin_time": "2026-01-01T00:00:00+00:00",
        "issued_at": "2026-01-01T00:00:01+00:00",
        "asset": "XAUUSD",
        "data_source": "SYNTHETIC",
        "data_is_synthetic": True,
        "last_close": p50,
        "abstention": {"regime": regime, "abstain": False, "reasons": []},
        "horizons": [
            {
                "horizon_h": 24,
                "p10": float(p10),
                "p25": float(p50 * np.exp(-sigma * 0.6745)),
                "p50": float(p50),
                "p75": float(p50 * np.exp(sigma * 0.6745)),
                "p90": float(p90),
                "expected_high": float(p90),
                "expected_low": float(p10),
                "sigma_h": float(sigma),
                "p_vol_expansion": 0.3,
                "p_touch_upper_2sigma": 0.05,
                "p_touch_lower_2sigma": 0.05,
                "chosen_vol_model": "HAR",
            }
        ],
    }


# ── 7.1 leverage_stress ─────────────────────────────────────────────────


def test_71_leverage_stress_long_increases_with_leverage() -> None:
    """Higher leverage ⇒ higher P(margin breach) for the same buffer."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r1x = compute_margin_breach_probability(
        m5_horizon=h, side="LONG", leverage=1.0, margin_buffer=0.20, horizon_h=24
    )
    r5x = compute_margin_breach_probability(
        m5_horizon=h, side="LONG", leverage=5.0, margin_buffer=0.20, horizon_h=24
    )
    assert isinstance(r1x, LeverageStressResult)
    assert r1x.p_margin_breach < r5x.p_margin_breach
    assert 0 <= r5x.p_margin_breach <= 1
    assert r5x.breach_level > 0


def test_71_leverage_stress_short_close_to_long() -> None:
    """LONG and SHORT at the same leverage give similar breach probabilities
    for symmetric M5 quantiles. (Not perfectly equal because log is nonlinear
    around the breach level, but in the same order of magnitude.)"""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    rL = compute_margin_breach_probability(
        m5_horizon=h, side="LONG", leverage=3.0, margin_buffer=0.20, horizon_h=24
    )
    rS = compute_margin_breach_probability(
        m5_horizon=h, side="SHORT", leverage=3.0, margin_buffer=0.20, horizon_h=24
    )
    # Both should be tiny (deep tail), within 3x relative.
    assert rL.p_margin_breach < 0.01
    assert rS.p_margin_breach < 0.01
    assert abs(rL.p_margin_breach - rS.p_margin_breach) < 0.001


def test_71_leverage_stress_flat_no_risk() -> None:
    """FLAT position ⇒ p_margin_breach = 0."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r = compute_margin_breach_probability(
        m5_horizon=h, side="FLAT", leverage=3.0, margin_buffer=0.20, horizon_h=24
    )
    assert r.p_margin_breach == 0.0
    assert r.notes == "flat_or_no_leverage"


def test_71_leverage_stress_missing_quantiles_flag_insufficient() -> None:
    """Missing M5 quantiles ⇒ data_insufficient=True (honest fallback)."""
    bad = {"p10": None, "p50": 1000.0, "p90": 1100.0}
    r = compute_margin_breach_probability(
        m5_horizon=bad, side="LONG", leverage=3.0, margin_buffer=0.20, horizon_h=24
    )
    assert r.data_insufficient is True
    assert np.isnan(r.p_margin_breach)


# ── 7.2 stop_risk ───────────────────────────────────────────────────────


def test_72_stop_risk_long_wide_target_low_probability() -> None:
    """Wide target, tight stop ⇒ low P(stop before target)."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r = compute_stop_risk(
        side="LONG",
        entry=1000.0,
        stop=990.0,        # 1% stop
        target=1100.0,     # 10% target
        sigma_path=0.02,
    )
    assert isinstance(r, StopRiskResult)
    assert r.p_stop_before_target < r.p_stop_hit  # conditioning pulls prob toward 0
    assert r.p_target_hit > r.p_stop_hit
    assert 0 <= r.p_stop_before_target <= 1


def test_72_stop_risk_long_tight_stop_higher_marginal() -> None:
    """Tight stop + far target — verify the reflection-principle invariant
    p_stop_first = p_stop_hit / (p_stop_hit + p_target_hit) holds, and
    that with a 10% target the path is overwhelmingly likely to reach
    the target first (p_stop_first < 0.5)."""
    r = compute_stop_risk(
        side="LONG",
        entry=1000.0,
        stop=995.0,        # 0.5% stop
        target=1100.0,     # 10% target
        sigma_path=0.02,
    )
    # Reflection principle: P(stop first | one is hit)
    denom = r.p_stop_hit + r.p_target_hit
    if denom > 0:
        expected = r.p_stop_hit / denom
        assert abs(r.p_stop_before_target - expected) < 1e-9
    # With a far target, the target is more likely to be hit first.
    assert r.p_stop_before_target < 0.5
    assert r.p_target_hit > 0.9  # 10% target at 2% sigma is virtually certain


def test_72_stop_risk_invalid_inputs_flag_insufficient() -> None:
    """Stop on wrong side of entry ⇒ data_insufficient=True."""
    r = compute_stop_risk(
        side="LONG",
        entry=1000.0,
        stop=1010.0,    # ABOVE entry for a LONG ⇒ invalid
        target=1100.0,
        sigma_path=0.02,
    )
    assert r.data_insufficient is True
    assert np.isnan(r.p_stop_before_target)
    assert "stop_not_below_entry_for_long" in r.reasons


# ── 7.3 expected_shortfall ──────────────────────────────────────────────


def test_73_cvar_long_positive_in_standard_case() -> None:
    """LONG CVaR is a positive price-unit shortfall."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r = compute_cvar(m5_horizon=h, side="LONG", horizon_h=24, alpha=0.05)
    assert isinstance(r, CVaRResult)
    assert r.cvar_alpha > 0
    assert r.var_alpha > 0
    assert r.cvar_alpha >= r.var_alpha  # CVaR ≥ VaR by definition


def test_73_cvar_short_uses_upper_tail() -> None:
    """SHORT CVaR uses the upside tail — positive number."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r = compute_cvar(m5_horizon=h, side="SHORT", horizon_h=24, alpha=0.05)
    assert r.cvar_alpha > 0


def test_73_cvar_flat_zero() -> None:
    """FLAT ⇒ 0 shortfall (no exposure)."""
    h = _synthetic_m5_horizon(sigma=0.02)["horizons"][0]
    r = compute_cvar(m5_horizon=h, side="FLAT", horizon_h=24, alpha=0.05)
    assert r.cvar_alpha == 0.0


def test_73_cvar_invalid_quantiles_flag_insufficient() -> None:
    """Non-monotonic quantiles ⇒ data_insufficient=True."""
    bad = {"p10": 1100.0, "p50": 1000.0, "p90": 900.0}
    r = compute_cvar(m5_horizon=bad, side="LONG", horizon_h=24, alpha=0.05)
    assert r.data_insufficient is True
    assert np.isnan(r.cvar_alpha)


# ── 7.4 liquidation_cost ────────────────────────────────────────────────


def test_74_liquidation_cost_scales_with_notional() -> None:
    """Larger notional ⇒ larger absolute cost (USD), modest bps growth."""
    r_small = compute_liquidation_cost(notional_usd=10_000)
    r_large = compute_liquidation_cost(notional_usd=10_000_000)
    assert isinstance(r_small, LiquidationCostResult)
    assert r_large.total_cost_usd > r_small.total_cost_usd
    # Large order pays more bps because of market impact.
    assert r_large.total_cost_bps > r_small.total_cost_bps


def test_74_liquidation_cost_urgency_scales_impact() -> None:
    """Urgent orders pay more market impact than patient ones."""
    r_patient = compute_liquidation_cost(notional_usd=1_000_000, urgency="patient")
    r_urgent = compute_liquidation_cost(notional_usd=1_000_000, urgency="urgent")
    assert r_urgent.market_impact_bps > r_patient.market_impact_bps


def test_74_liquidation_cost_participation_flag() -> None:
    """Order > 50% of ADV ⇒ flagged in reasons."""
    r = compute_liquidation_cost(notional_usd=20_000_000_000, adv_usd=30_000_000_000)
    assert "participation_above_50pct" in r.reasons
    assert r.participation_pct > 50.0


def test_74_liquidation_cost_negative_notional_flag_insufficient() -> None:
    """Negative notional ⇒ data_insufficient=True (honest)."""
    r = compute_liquidation_cost(notional_usd=-1000)
    assert r.data_insufficient is True
    assert "non_positive_notional" in r.reasons


# ── 7.5 max_survivable_size ─────────────────────────────────────────────


def test_75_max_survivable_size_positive_edge_yields_positive_size() -> None:
    """Positive edge + survival ⇒ positive Kelly size."""
    r = compute_max_survivable_size(
        edge_log=0.01,
        sigma_log=0.10,
        survival_prob=0.95,
        equity_usd=100_000,
    )
    assert isinstance(r, MaxSurvivableSizeResult)
    assert r.kelly_fraction_raw > 0
    assert r.max_survivable_size_usd > 0
    # Quarter-Kelly applied.
    assert r.kelly_fraction_final < r.kelly_fraction_survival


def test_75_max_survivable_size_zero_survival_zero_size() -> None:
    """Zero survival probability ⇒ zero Kelly size (cannot survive)."""
    r = compute_max_survivable_size(
        edge_log=0.01,
        sigma_log=0.10,
        survival_prob=0.0,
        equity_usd=100_000,
    )
    assert r.max_survivable_size_usd == 0.0


def test_75_max_survivable_size_negative_survival_treated_as_zero() -> None:
    """Negative survival (over-blocked) clamped to zero — never INCREASES size."""
    r = compute_max_survivable_size(
        edge_log=0.01,
        sigma_log=0.10,
        survival_prob=-0.5,
        equity_usd=100_000,
    )
    assert r.max_survivable_size_usd == 0.0


def test_75_max_survivable_size_disagreement_penalty_shrinks() -> None:
    """Disagreement penalty (multiplier) shrinks the final Kelly."""
    r_full = compute_max_survivable_size(
        edge_log=0.01, sigma_log=0.10, survival_prob=0.95,
        equity_usd=100_000, disagreement_penalty=1.0,
    )
    r_penalty = compute_max_survivable_size(
        edge_log=0.01, sigma_log=0.10, survival_prob=0.95,
        equity_usd=100_000, disagreement_penalty=0.5,
    )
    assert r_penalty.max_survivable_size_usd < r_full.max_survivable_size_usd


# ── 7.6 thesis_half_life ────────────────────────────────────────────────


def test_76_thesis_half_life_constant_series_infinite() -> None:
    """A constant disagreement series is perfectly persistent."""
    r = compute_thesis_half_life(disagreement_series=[0.1] * 30)
    assert isinstance(r, ThesisHalfLifeResult)
    assert np.isinf(r.half_life_bars)
    assert r.persistence_score == 1.0
    assert r.autocorrelation_at_lag1 == 1.0


def test_76_thesis_half_life_random_series_short() -> None:
    """A zig-zag disagreement series decorrelates within ~1 bar."""
    series = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    r = compute_thesis_half_life(disagreement_series=series)
    # half_life=1 ⇒ persistence = 1/(1+1) = 0.5. Anything <= 0.5 is fragile.
    assert r.half_life_bars <= 2
    assert r.persistence_score <= 0.5


def test_76_thesis_half_life_short_series_flag_insufficient() -> None:
    """Series with < 4 bars ⇒ data_insufficient=True."""
    r = compute_thesis_half_life(disagreement_series=[0.1, 0.2, 0.15])
    assert r.data_insufficient is True
    assert np.isnan(r.half_life_bars)


# ── 7.7 abstention_gate ─────────────────────────────────────────────────


def test_77_safety_gate_regime_action_table_full() -> None:
    """The regime-action table must contain all 4 regimes × 3 tiers (12 entries)."""
    assert set(REGIME_ACTION_TABLE.keys()) == {"RANGE", "COMPRESSION", "TRENDING", "EVENT_RISK"}
    for regime, tiers in REGIME_ACTION_TABLE.items():
        assert len(tiers) == 3
        for verdict, mult in tiers:
            assert verdict in VERDICTS
            assert 0.0 <= mult <= 1.0


def test_77_safety_gate_act_high_survival_range() -> None:
    """High survival + RANGE ⇒ ACT with full size."""
    v = decide_safety_gate(regime="RANGE", p_margin_breach=0.02)
    assert isinstance(v, SafetyGateVerdict)
    assert v.verdict == "ACT"
    assert v.size_multiplier == 1.0


def test_77_safety_gate_reduce_mid_survival() -> None:
    """Mid survival + TRENDING ⇒ REDUCE.

    alpha is raised to 0.30 so the table's mid tier (survival 0.7-0.9,
    i.e. breach 0.10-0.30) governs the verdict rather than the
    constraint equation hard-block.
    """
    v = decide_safety_gate(regime="TRENDING", p_margin_breach=0.25, alpha=0.30)
    assert v.verdict == "REDUCE"
    assert 0 < v.size_multiplier < 1


def test_77_safety_gate_hold_low_survival() -> None:
    """Low survival + RANGE ⇒ HOLD.

    With alpha=0.30 the constraint is satisfied (breach 0.40 > alpha
    so still BLOCKs) — we use breach=0.35 with alpha=0.40 so survival
    drops into the table's bottom tier (HOLD) without violating alpha.
    """
    v = decide_safety_gate(regime="RANGE", p_margin_breach=0.35, alpha=0.40)
    assert v.verdict == "HOLD"
    assert v.size_multiplier == 0.0


def test_77_safety_gate_block_extreme_breach() -> None:
    """p_margin_breach > alpha ⇒ BLOCK regardless of regime."""
    v = decide_safety_gate(regime="RANGE", p_margin_breach=0.50, alpha=0.10)
    assert v.verdict == "BLOCK"
    assert v.size_multiplier == 0.0
    assert v.hard_block is True
    assert "p_margin_breach_above_alpha" in v.reason_codes


def test_77_safety_gate_block_when_adv_participation_too_high() -> None:
    """Order > 50% ADV ⇒ BLOCK (cannot liquidate cleanly)."""
    v = decide_safety_gate(
        regime="RANGE", p_margin_breach=0.05, participation_above_50pct=True
    )
    assert v.verdict == "BLOCK"
    assert "participation_above_50pct_adv" in v.reason_codes


def test_77_safety_gate_block_when_cvar_exceeds_max_loss() -> None:
    """CVaR > max acceptable loss ⇒ BLOCK."""
    v = decide_safety_gate(
        regime="TRENDING", p_margin_breach=0.05, cvar_exceeds_max_loss=True
    )
    assert v.verdict == "BLOCK"
    assert "cvar_exceeds_max_acceptable_loss" in v.reason_codes


def test_77_safety_gate_hold_when_data_insufficient() -> None:
    """Any data_insufficient ⇒ HOLD (never BLOCK on missing data)."""
    v = decide_safety_gate(
        regime="RANGE", p_margin_breach=0.05, data_insufficient=True
    )
    assert v.verdict == "HOLD"
    assert "data_insufficient" in v.reason_codes


def test_77_safety_gate_flat_position_zero_size_act() -> None:
    """FLAT position ⇒ ACT with size 0 (no risk, nothing to do)."""
    v = decide_safety_gate(regime="RANGE", p_margin_breach=0.0, flat_position=True)
    assert v.verdict == "ACT"
    assert v.size_multiplier == 0.0


# ── Disagreement preservation ───────────────────────────────────────────


def test_disagreement_preserves_individual_signals() -> None:
    """F / T / D signals are preserved — never averaged into a single score."""
    dv = assess_disagreement(f_value=0.9, t_value=-0.5, d_value=0.2)
    assert isinstance(dv, DisagreementVector)
    assert dv.f_value == 0.9
    assert dv.t_value == -0.5
    assert dv.d_value == 0.2
    # The individual values must be exposed in to_dict().
    out = dv.to_dict()
    assert "f_value" in out and "t_value" in out and "d_value" in out
    # No merged score field.
    assert "consensus" not in out
    assert "merged_signal" not in out


def test_disagreement_lowers_confidence_and_size_and_widens_interval() -> None:
    """Disagreement ⇒ confidence DOWN, interval UP, size DOWN."""
    dv_agree = assess_disagreement(f_value=0.7, t_value=0.6, d_value=0.6)
    dv_disagree = assess_disagreement(f_value=0.7, t_value=-0.6, d_value=0.6)

    # Apply widening
    c1, i1, s1 = widen_for_disagreement(
        confidence=1.0, interval_width=10.0, position_size=1.0, disagreement=dv_agree
    )
    c2, i2, s2 = widen_for_disagreement(
        confidence=1.0, interval_width=10.0, position_size=1.0, disagreement=dv_disagree
    )
    assert c2 < c1, "confidence should go DOWN with disagreement"
    assert i2 > i1, "interval should WIDEN with disagreement"
    assert s2 < s1, "size should go DOWN with disagreement"


def test_disagreement_shortens_review_halflife() -> None:
    """Strong disagreement shortens the review half-life (review more often)."""
    dv_agree = assess_disagreement(f_value=0.7, t_value=0.6, d_value=0.6)
    dv_disagree = assess_disagreement(f_value=0.9, t_value=-0.9, d_value=0.9)
    assert dv_disagree.review_halflife_hours < dv_agree.review_halflife_hours


def test_disagreement_normalises_out_of_range_signals() -> None:
    """Signals outside [-1, 1] are clamped, not blown up."""
    dv = assess_disagreement(f_value=5.0, t_value=-5.0, d_value=0.0)
    assert -1.0 <= dv.f_value <= 1.0
    assert -1.0 <= dv.t_value <= 1.0


# ── End-to-end: run_m7 with the real M5 forecast ────────────────────────


def test_run_m7_authority_explicit() -> None:
    """M7's authority tuple is fixed and never changes silently."""
    assert M7_AUTHORITY["may_reduce_size"] is True
    assert M7_AUTHORITY["may_block_trade"] is True
    assert M7_AUTHORITY["may_increase_size"] is False
    assert M7_AUTHORITY["may_override_human"] is False


def test_run_m7_schema_and_status() -> None:
    """M7 has a fixed schema and SHADOW_OPERATIONAL status by default."""
    assert M7_SCHEMA == "wealth.gold.m7.v1"
    assert M7_STATUS == "SHADOW_OPERATIONAL"


def test_run_m7_conservative_scenario_yields_act(m5_forecast: dict) -> None:
    """A conservative scenario with low leverage and large loss budget ⇒ ACT."""
    r = run_m7(
        m5_forecast=m5_forecast,
        side="LONG",
        entry=m5_forecast["last_close"],
        stop=m5_forecast["last_close"] * 0.95,
        target=m5_forecast["last_close"] * 1.10,
        leverage=1.0,
        margin_buffer=0.20,
        horizon_h=24,
        notional_usd=10_000,
        equity_usd=100_000,
        f_signal=0.7, t_signal=0.6, d_signal=0.6,
        disagreement_series=[0.05] * 30,
        edge_log=0.005, sigma_log=0.011,
        max_acceptable_loss_usd=100_000,
    )
    assert r.verdict == "ACT"
    assert r.size_multiplier > 0
    assert 0 <= r.probability_of_margin_breach <= 1
    assert 0 <= r.probability_of_stop_before_target <= 1
    assert r.expected_shortfall >= 0


def test_run_m7_risky_scenario_yields_block(m5_forecast: dict) -> None:
    """A risky scenario (high lev, high notional, low loss budget) ⇒ BLOCK."""
    r = run_m7(
        m5_forecast=m5_forecast,
        side="LONG",
        entry=m5_forecast["last_close"],
        stop=m5_forecast["last_close"] * 0.99,
        target=m5_forecast["last_close"] * 1.02,
        leverage=5.0,
        margin_buffer=0.10,
        horizon_h=24,
        notional_usd=500_000,
        equity_usd=100_000,
        f_signal=0.9, t_signal=-0.5, d_signal=0.3,
        disagreement_series=[0.1, 0.8, 0.2, 0.9, 0.1, 0.8, 0.2, 0.9, 0.1, 0.8],
        edge_log=0.005, sigma_log=0.011,
        max_acceptable_loss_usd=2_000,
    )
    assert r.verdict == "BLOCK"
    assert r.size_multiplier == 0.0


def test_run_m7_missing_m5_horizon_yields_hold() -> None:
    """No M5 horizon ⇒ HOLD (M7 refuses on missing data, never BLOCKs)."""
    fake = {
        "forecast_id": "empty",
        "asset": "XAUUSD",
        "data_source": "SYNTHETIC",
        "data_is_synthetic": True,
        "last_close": 1000.0,
        "horizons": [],
        "abstention": {"regime": "RANGE", "abstain": True, "reasons": []},
    }
    r = run_m7(
        m5_forecast=fake,
        side="LONG",
        entry=1000.0, stop=950.0, target=1100.0,
        leverage=1.0, margin_buffer=0.20,
        horizon_h=24,
        notional_usd=10_000, equity_usd=100_000,
    )
    assert r.verdict == "HOLD"
    assert "data_insufficient" in r.reason_codes or r.caveats


def test_run_m7_does_not_predict_gold() -> None:
    """M7 does not emit any directional price prediction.

    The output never contains a 'predicted_price' field, 'direction',
    or 'forecast_price'. Only safety outputs.
    """
    fake = _synthetic_m5_horizon(sigma=0.02)
    r = run_m7(
        m5_forecast=fake, side="LONG",
        entry=1000.0, stop=950.0, target=1100.0,
        leverage=2.0, margin_buffer=0.20, horizon_h=24,
        notional_usd=10_000, equity_usd=100_000,
        f_signal=0.5, t_signal=0.4, d_signal=0.4,
        disagreement_series=[0.1] * 20,
    )
    d = r.to_dict()
    forbidden = ["predicted_price", "direction", "forecast_price", "price_target"]
    for key in forbidden:
        assert key not in d, f"M7 must not emit a directional field: {key}"
    # M7 only emits survival / risk outputs.
    expected = {
        "probability_of_margin_breach",
        "probability_of_stop_before_target",
        "expected_shortfall",
        "liquidation_cost_bps",
        "liquidation_cost_usd",
        "maximum_survivable_size_usd",
        "thesis_half_life_bars",
        "size_multiplier",
        "verdict",
    }
    for key in expected:
        assert key in d, f"M7 missing required output: {key}"


def test_run_m7_reduce_under_high_leverage(m5_forecast: dict) -> None:
    """8x leverage in TRENDING regime with survival in 0.7-0.9 ⇒ REDUCE."""
    fake = dict(m5_forecast)
    fake["abstention"] = {"regime": "TRENDING", "abstain": False, "reasons": []}
    # Override the horizon to a known shape.
    fake["horizons"] = [{
        "horizon_h": 24, "p10": 970.0, "p25": 985.0, "p50": 1000.0,
        "p75": 1015.0, "p90": 1030.0, "expected_high": 1030.0,
        "expected_low": 970.0, "sigma_h": 0.025,
        "p_vol_expansion": 0.3, "p_touch_upper_2sigma": 0.05,
        "p_touch_lower_2sigma": 0.05, "chosen_vol_model": "HAR",
    }]
    r = run_m7(
        m5_forecast=fake, side="LONG",
        entry=1000.0, stop=970.0, target=1100.0,
        leverage=8.0, margin_buffer=0.20,
        horizon_h=24,
        notional_usd=10_000, equity_usd=100_000,
        f_signal=0.6, t_signal=0.5, d_signal=0.5,
        disagreement_series=[0.1] * 20,
        edge_log=0.005, sigma_log=0.025,
        max_acceptable_loss_usd=100_000,
        alpha=0.30,
    )
    assert r.verdict == "REDUCE"
    assert 0 < r.size_multiplier < 1


def test_run_m7_to_dict_round_trip() -> None:
    """to_dict() must be fully JSON-serialisable for the audit trail."""
    import json
    fake = _synthetic_m5_horizon(sigma=0.02)
    r = run_m7(
        m5_forecast=fake, side="LONG",
        entry=1000.0, stop=950.0, target=1100.0,
        leverage=2.0, margin_buffer=0.20, horizon_h=24,
        notional_usd=10_000, equity_usd=100_000,
    )
    text = json.dumps(r.to_dict())
    parsed = json.loads(text)
    assert parsed["schema"] == M7_SCHEMA
    assert parsed["verdict"] in VERDICTS


def test_run_m7_receipt_writes_to_vault() -> None:
    """write_m7_receipt drops a JSON file in VAULT999."""
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        fake = _synthetic_m5_horizon(sigma=0.02)
        r = run_m7(
            m5_forecast=fake, side="LONG",
            entry=1000.0, stop=950.0, target=1100.0,
            leverage=2.0, margin_buffer=0.20, horizon_h=24,
            notional_usd=10_000, equity_usd=100_000,
        )
        receipt = write_m7_receipt(r, receipts_dir=vault)
        assert receipt["written"] is True
        assert Path(receipt["receipt_uri"]).exists()
        with open(receipt["receipt_uri"]) as f:
            body = json.load(f)
        assert body["schema"] == M7_SCHEMA
        assert body["verdict"] in VERDICTS


def test_honest_caveat_receipt_records_synthetic_defaults() -> None:
    """write_honest_caveat_receipt is the canonical way to flag synthetic defaults."""
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        receipt = write_honest_caveat_receipt(
            caveat_codes=["spread_default_synthetic", "adv_default_synthetic"],
            description="M7 ran with synthetic default spread and ADV because no first-party live values were supplied.",
            forecast_id="m7-test-caveat",
            receipts_dir=vault,
        )
        assert receipt["written"] is True
        with open(receipt["receipt_uri"]) as f:
            body = json.load(f)
        assert body["receipt_subtype"] == "honest_caveat"
        assert "spread_default_synthetic" in body["caveat_codes"]
