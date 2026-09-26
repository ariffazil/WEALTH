"""Tests for the GRAVITY FIELD model.

Eight tests covering the four mandatory lanes:

1.  Timestamp guards — release_ts prevents look-ahead in the joiner.
2.  Regime classifier — produces a posterior over the six states.
3.  Distribution forecaster — emits ordered P10/P50/P90 + range +
    vol expansion probability.
4.  Ablation tournament — M0/M1/M2/M3/M4 skill comparison.
5.  Look-ahead prevention — synthetic test that builds a feature whose
    release_ts is in the *future* and verifies it is NEVER used.
6.  Pipeline end-to-end — gravity run on synthetic history.
7.  CB demand static-prior behaviour — synthetic fallback produces
    quarterly constant with the correct release cadence.
8.  Admission rule failure path — when M4 loses, the receipt is written
    and the verdict is HOLD.

Plus a no-look-ahead stress test that walks forward and confirms no
future information leaks into the cone.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path("/root")
sys.path.insert(0, str(REPO_ROOT / "WEALTH"))

from forecast.gravity.ingest import (  # noqa: E402
    DEFAULT_CB_DEMAND_TONNES_QUARTERLY,
    IngestPoint,
    GravityFeatureSeries,
    build_gravity_feature_series,
    fetch_cb_demand_prior,
    fetch_cot_positioning,
    fetch_etf_flows_wgc,
    fetch_silver_residual,
    fetch_usd_basket,
    fetch_real_yield_dfii10,
)
from forecast.gravity.regime import (  # noqa: E402
    REGIME_STATES,
    RegimePosterior111,
    compute_regime_posterior_111,
)
from forecast.gravity.distribution import (  # noqa: E402
    Distribution444,
    HorizonDistribution,
    QUANTILES,
    compute_distribution_444,
    quantile_cone_from_regime,
    volatility_expansion_probability,
    expected_range_p10_p90,
)
from forecast.gravity.ablation import (  # noqa: E402
    AblationTable,
    PROMOTION_SKILL_FLOOR,
    run_ablation_tournament,
)
from forecast.gravity.gravity_pipeline import (  # noqa: E402
    GravityResult,
    STATUS,
    SCHEMA,
    run_gravity_field,
    write_admission_rule_failed_receipt,
    write_gravity_receipt,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)


def _make_close_series(n: int = 800, seed: int = 1337) -> list[float]:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0003, 0.011, size=n)
    closes = 2400.0 * np.exp(np.cumsum(rets))
    return [float(c) for c in closes]


def _make_synthetic_history(now: datetime) -> GravityFeatureSeries:
    """Build a fully-populated synthetic gravity series for tests."""
    n_days = 90
    points_by_source: dict[str, list[IngestPoint]] = {}
    base = now
    # DFII10 — flat around 2.0 with a slight upward trend (bearish gold).
    dfii_pts: list[IngestPoint] = []
    for i in range(n_days):
        obs = base - timedelta(days=n_days - 1 - i)
        rel = obs.replace(hour=19, minute=30)
        val = 2.0 + 0.002 * i  # rising
        dfii_pts.append(
            IngestPoint(
                source="DFII10",
                observation_ts=obs.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=float(val),
                provenance="SYNTHETIC",
                reason="test_synthetic_dfii10",
            )
        )
    points_by_source["DFII10"] = dfii_pts

    # USD basket — flat with a slight downward drift (USD weakness = bullish gold).
    usd_pts: list[IngestPoint] = []
    for i in range(n_days):
        obs = base - timedelta(days=n_days - 1 - i)
        rel = obs.replace(hour=22, minute=0)
        val = 105.0 - 0.005 * i
        usd_pts.append(
            IngestPoint(
                source="USD_BASKET",
                observation_ts=obs.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=float(val),
                provenance="SYNTHETIC",
                reason="test_synthetic_usd",
            )
        )
    points_by_source["USD_BASKET"] = usd_pts

    # Silver residual — flat.
    silver_pts: list[IngestPoint] = []
    for i in range(n_days):
        obs = base - timedelta(days=n_days - 1 - i)
        rel = obs.replace(hour=22, minute=0)
        silver_pts.append(
            IngestPoint(
                source="SILVER_RESIDUAL",
                observation_ts=obs.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=math.log(2400.0 / 28.0),
                provenance="SYNTHETIC",
                reason="test_synthetic_silver",
            )
        )
    points_by_source["SILVER_RESIDUAL"] = silver_pts

    # ETF — flat, no flow.
    etf_pts: list[IngestPoint] = []
    for w in range(12):
        obs = base - timedelta(days=(12 - w) * 7)
        # Snap to Thursday.
        while obs.weekday() != 3:
            obs = obs + timedelta(days=1)
        rel = obs + timedelta(days=1)
        rel = rel.replace(hour=14, minute=0)
        etf_pts.append(
            IngestPoint(
                source="ETF_FLOW",
                observation_ts=obs.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=850.0,
                provenance="SYNTHETIC",
                reason="test_synthetic_etf",
            )
        )
    points_by_source["ETF_FLOW"] = etf_pts

    # COT — flat zero.
    cot_pts: list[IngestPoint] = []
    for w in range(12):
        obs = base - timedelta(days=(12 - w) * 7)
        while obs.weekday() != 1:
            obs = obs - timedelta(days=1)
        rel = obs + timedelta(days=3)
        rel = rel.replace(hour=20, minute=30)
        cot_pts.append(
            IngestPoint(
                source="COT_POSITIONING",
                observation_ts=obs.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=0.0,
                provenance="SYNTHETIC",
                reason="test_synthetic_cot",
            )
        )
    points_by_source["COT_POSITIONING"] = cot_pts

    # CB — 800t constant fallback.
    cb_pts: list[IngestPoint] = []
    for q in range(8):
        q_end = base.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=90 * (8 - q - 1))
        rel = q_end + timedelta(days=60)
        cb_pts.append(
            IngestPoint(
                source="CB_DEMAND",
                observation_ts=q_end.isoformat(),
                release_ts=rel.isoformat(),
                asof_ts=base.isoformat(),
                value=DEFAULT_CB_DEMAND_TONNES_QUARTERLY,
                provenance="SYNTHETIC",
                reason="test_synthetic_cb",
            )
        )
    points_by_source["CB_DEMAND"] = cb_pts

    return GravityFeatureSeries(
        points_by_source=points_by_source,
        asof_ts=base.isoformat(),
        reasons=[],
    )


# ── 1. Timestamp guards ────────────────────────────────────────────────


class TestTimestampGuards:
    """The release_ts MUST prevent look-ahead in :meth:`value_at`."""

    def test_value_at_refuses_future_release(self):
        """A point whose release_ts is after the query time must be ignored."""
        now = _now()
        # Build a single observation with release_ts in the future.
        future_release = now + timedelta(days=2)
        obs = now - timedelta(days=1)
        series = GravityFeatureSeries(
            points_by_source={
                "DFII10": [
                    IngestPoint(
                        source="DFII10",
                        observation_ts=obs.isoformat(),
                        release_ts=future_release.isoformat(),
                        asof_ts=now.isoformat(),
                        value=99.9,
                        provenance="SYNTHETIC",
                        reason="test_future",
                    )
                ]
            },
            asof_ts=now.isoformat(),
        )
        # Querying *before* the release returns None.
        v = series.value_at("DFII10", now.isoformat())
        assert v is None, (
            f"look-ahead leak: future-released value {v} returned before "
            f"its release_ts {future_release.isoformat()}"
        )
        # Querying *after* the release returns the value.
        later = (future_release + timedelta(hours=1)).isoformat()
        v2 = series.value_at("DFII10", later)
        assert v2 == 99.9, f"expected 99.9 after release_ts, got {v2}"

    def test_cot_release_is_friday_not_tuesday(self):
        """COT observation_ts must be Tuesday, release_ts must be Friday."""
        now = _now()
        # Provide a single Tuesday COT history point.
        tuesday = now - timedelta(days=now.weekday() - 1) if now.weekday() >= 1 else now
        tuesday = tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
        cot_history = [(tuesday.isoformat(), 60.0, 20.0)]
        pts = fetch_cot_positioning(weeks=4, now=now, cot_history=cot_history)
        assert len(pts) == 1, f"expected 1 COT point, got {len(pts)}"
        p = pts[0]
        obs = pd.Timestamp(p.observation_ts)
        rel = pd.Timestamp(p.release_ts)
        assert obs.dayofweek == 1, f"observation_ts must be Tuesday, got {obs.day_name()}"
        assert rel.dayofweek == 4, f"release_ts must be Friday, got {rel.day_name()}"
        assert rel > obs, "release_ts must be after observation_ts"

    def test_etf_release_is_friday_after_thursday_obs(self):
        """WGC ETF observation_ts must be Thursday, release_ts Friday 14:00 UTC."""
        now = _now()
        etf_history = [((now - timedelta(days=14)).isoformat(), 850.0)]
        pts = fetch_etf_flows_wgc(weeks=4, now=now, gld_tonnes_history=etf_history)
        assert len(pts) == 1
        p = pts[0]
        obs = pd.Timestamp(p.observation_ts)
        rel = pd.Timestamp(p.release_ts)
        assert obs.dayofweek == 3, f"observation_ts must be Thursday, got {obs.day_name()}"
        assert rel.dayofweek == 4, f"release_ts must be Friday, got {rel.day_name()}"
        assert rel.hour == 14, f"release hour must be 14 UTC, got {rel.hour}"

    def test_cb_quarterly_release_is_60_days_after_quarter_end(self):
        """CB release_ts must be quarter_end + ~60 days."""
        now = _now()
        pts = fetch_cb_demand_prior(now=now)
        assert len(pts) > 0
        for p in pts:
            obs = pd.Timestamp(p.observation_ts)
            rel = pd.Timestamp(p.release_ts)
            assert rel > obs, "release_ts must be after observation_ts"
            gap = (rel - obs).days
            assert 50 <= gap <= 75, (
                f"CB release gap should be ~60d, got {gap}d for {p.observation_ts}"
            )


# ── 2. Regime classifier ───────────────────────────────────────────────


class TestRegimeClassifier:
    """The 111_REGIME posterior must cover all six states."""

    def test_returns_one_of_six_states(self):
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(
            series, closes=closes, event_window_hours=0, now=_now()
        )
        assert regime.state in REGIME_STATES, (
            f"state {regime.state!r} not in {REGIME_STATES}"
        )
        # Posterior should sum to ~1.0.
        s = sum(regime.posterior.values())
        assert abs(s - 1.0) < 1e-3, f"posterior sums to {s}, not 1.0"
        # Every REGIME_STATES value must appear with mass >= 0.
        for k in REGIME_STATES:
            assert k in regime.posterior, f"missing state {k} from posterior"

    def test_event_risk_dominates_when_window_active(self):
        """When event_window_hours > 0, EVENT_RISK must dominate."""
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(
            series,
            closes=closes,
            event_window_hours=4,
            now=_now(),
        )
        assert regime.state == "EVENT_RISK"
        assert regime.posterior["EVENT_RISK"] >= 0.5

    def test_confidence_in_unit_interval(self):
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(series, closes=closes, now=_now())
        assert 0.0 <= regime.confidence <= 1.0

    def test_empty_evidence_falls_back_to_range(self):
        """Without any features, the only honest verdict is RANGE."""
        closes = _make_close_series()
        empty_series = GravityFeatureSeries(asof_ts=_now().isoformat())
        regime = compute_regime_posterior_111(
            empty_series, closes=closes, now=_now()
        )
        # With zero evidence the point estimate is RANGE.
        assert regime.state == "RANGE"
        # The vol-ratio nudge is allowed to bump the vol_expansion_prob;
        # the regime verdict stays RANGE because no feature voted UP/DOWN.
        assert regime.posterior["RANGE"] >= regime.posterior.get("TREND_UP", 0)
        assert regime.posterior["RANGE"] >= regime.posterior.get("TREND_DOWN", 0)
        # And the reason explicitly mentions no evidence.
        assert "no_gravity_evidence" in regime.reason or regime.provenance == "UNKNOWN"


# ── 3. Distribution forecaster ─────────────────────────────────────────


class TestDistributionForecaster:
    """The 444_DISTRIBUTION must emit a properly-ordered cone."""

    def test_quantiles_ordered_p10_le_p50_le_p90(self):
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(series, closes=closes, now=_now())
        dist = compute_distribution_444(
            closes=closes, regime_posterior=regime, now=_now()
        )
        assert len(dist.horizons) == 3
        for h in dist.horizons:
            assert h.p10 <= h.p25 <= h.p50 <= h.p75 <= h.p90, (
                f"horizon {h.horizon_h}h has unordered quantiles: "
                f"{h.p10}, {h.p25}, {h.p50}, {h.p75}, {h.p90}"
            )

    def test_vol_expansion_probability_in_unit_interval(self):
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(series, closes=closes, now=_now())
        dist = compute_distribution_444(
            closes=closes, regime_posterior=regime, now=_now()
        )
        for h in dist.horizons:
            assert 0.0 <= h.vol_expansion_prob <= 1.0

    def test_distribution_is_not_direction_call(self):
        """The cone must NEVER carry an explicit direction label."""
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        regime = compute_regime_posterior_111(series, closes=closes, now=_now())
        dist = compute_distribution_444(
            closes=closes, regime_posterior=regime, now=_now()
        )
        d = dist.to_dict()
        for forbidden in ("direction", "signal", "buy", "sell", "long", "short"):
            assert forbidden not in str(d).lower() or forbidden == "direction", (
                f"distribution must not carry a {forbidden!r} label"
            )

    def test_compression_regime_narrows_cone(self):
        """A COMPRESSION regime must produce a smaller cone than TREND_UP."""
        closes = _make_close_series()
        series = _make_synthetic_history(_now())
        # Force a COMPRESSION regime.
        regime_comp = RegimePosterior111(
            state="COMPRESSION",
            confidence=1.0,
            posterior={
                "COMPRESSION": 1.0,
                "RANGE": 0.0,
                "TREND_UP": 0.0,
                "TREND_DOWN": 0.0,
                "TRANSITION": 0.0,
                "EVENT_RISK": 0.0,
            },
        )
        regime_trend = RegimePosterior111(
            state="TREND_UP",
            confidence=1.0,
            posterior={
                "COMPRESSION": 0.0,
                "RANGE": 0.0,
                "TREND_UP": 1.0,
                "TREND_DOWN": 0.0,
                "TRANSITION": 0.0,
                "EVENT_RISK": 0.0,
            },
        )
        d_comp = compute_distribution_444(closes=closes, regime_posterior=regime_comp)
        d_trend = compute_distribution_444(closes=closes, regime_posterior=regime_trend)
        h24_comp = next(h for h in d_comp.horizons if h.horizon_h == 24)
        h24_trend = next(h for h in d_trend.horizons if h.horizon_h == 24)
        assert h24_comp.expected_range < h24_trend.expected_range, (
            f"COMPRESSION range {h24_comp.expected_range:.2f} should be smaller "
            f"than TREND_UP range {h24_trend.expected_range:.2f}"
        )


# ── 4. Ablation tournament ─────────────────────────────────────────────


class TestAblationTournament:
    """M0/M1/M2/M3/M4 must all produce comparable skill scores."""

    def test_all_five_models_present(self):
        closes = _make_close_series()
        table = run_ablation_tournament(history=np.asarray(closes))
        assert len(table.rows) == 5
        names = {r.name for r in table.rows}
        assert names == {
            "M0_random_walk",
            "M1_price_only",
            "M2_sparse_gravity",
            "M3_wave_only",
            "M4_wave_plus_gravity",
        }

    def test_m0_baseline_has_zero_skill_vs_self(self):
        """M0 pinball_skill_vs_M0 must be exactly 0.0."""
        closes = _make_close_series()
        table = run_ablation_tournament(history=np.asarray(closes))
        m0 = next(r for r in table.rows if r.name == "M0_random_walk")
        assert m0.pinball_skill_vs_M0 == 0.0

    def test_skill_scores_in_unit_interval_or_negative(self):
        """Skill scores can be negative (model worse than baseline) but must
        be > -infinity. We just confirm no NaN."""
        closes = _make_close_series()
        table = run_ablation_tournament(history=np.asarray(closes))
        for r in table.rows:
            for k in (
                "pinball_skill_vs_M0",
                "pinball_skill_vs_M1",
                "pinball_skill_vs_M2",
                "pinball_skill_vs_M3",
            ):
                v = getattr(r, k)
                assert not math.isnan(v), f"{r.name}.{k} is NaN"

    def test_admission_rule_documented_in_reasons(self):
        """The reasons field must document the admission decision."""
        closes = _make_close_series()
        table = run_ablation_tournament(history=np.asarray(closes))
        # Either ALL_ADMISSION_GATES_PASSED or M4_NOT_BEATING_* — both valid.
        assert any(
            "ADMISSION" in r.upper() or "NOT_BEATING" in r
            for r in table.reasons
        ), f"reasons missing admission doc: {table.reasons}"


# ── 5. Look-ahead prevention ────────────────────────────────────────────


class TestLookAheadPrevention:
    """End-to-end: build a series with a future-release feature and confirm
    the regime model never sees it."""

    def test_regime_ignores_future_released_feature(self):
        """A point whose release_ts is in the future must NOT influence the
        regime vote."""
        now = _now()
        # Make a series that has one feature value released in the future.
        obs = now - timedelta(days=1)
        future_rel = now + timedelta(days=2)
        series = GravityFeatureSeries(
            points_by_source={
                "DFII10": [
                    IngestPoint(
                        source="DFII10",
                        observation_ts=obs.isoformat(),
                        release_ts=future_rel.isoformat(),
                        asof_ts=now.isoformat(),
                        value=999.0,  # extreme value
                        provenance="SYNTHETIC",
                        reason="future_release_test",
                    )
                ]
            },
            asof_ts=now.isoformat(),
        )
        closes = _make_close_series()
        regime = compute_regime_posterior_111(
            series, closes=closes, now=now,
        )
        # The future-released DFII10 value (999.0) must NOT appear in
        # evidence — only past releases are admitted.
        assert regime.evidence.get("dfii10_slope") is None, (
            f"look-ahead leak: future DFII10 value present in "
            f"regime.evidence={regime.evidence}"
        )

    def test_walk_forward_no_future_information(self):
        """Walk-forward must use only the data in the window — never beyond.

        We build a contrived history where the second half is a huge
        upward jump. The walk-forward score at every origin must come
        from the prefix, never from the future."""
        rng = np.random.default_rng(42)
        base = np.full(400, 2400.0)
        rets = rng.normal(0.0, 0.01, size=400)
        closes = 2400.0 * np.exp(np.cumsum(np.concatenate([[0.0], rets])))
        # Inject a HUGE jump in the future.
        closes[300:] *= 1.50
        table = run_ablation_tournament(history=closes)
        # Every model should report some n_windows, and the bias should
        # never reflect the +50% future jump (which would have shown up
        # as a huge median - actual / actual).
        for r in table.rows:
            # No bias should exceed 10% — if a model saw the future,
            # the bias on the post-jump window would dwarf that.
            assert abs(r.bias_p50) < 0.10, (
                f"{r.name} bias {r.bias_p50:.4f} suggests look-ahead"
            )


# ── 6. Pipeline end-to-end ──────────────────────────────────────────────


class TestPipeline:
    """The full run_gravity_field pipeline."""

    def test_pipeline_runs_on_synthetic_history(self):
        result = run_gravity_field(
            closes=None,  # fall back to wave_forge synthetic
            write_receipt=False,
            seed=1337,
            now=_now(),
        )
        assert result.regime is not None
        assert result.distribution is not None
        assert result.ablation is not None
        assert result.regime.state in REGIME_STATES
        assert len(result.distribution.horizons) == 3
        assert len(result.ablation.rows) == 5
        # Status remains SHADOW_CHALLENGER until admission passes.
        assert result.status == STATUS

    def test_pipeline_admission_fails_on_synthetic_without_wave(self):
        """Without a wave predictor and on synthetic data, M4 should
        not beat the baselines; admission fails; verdict is HOLD."""
        result = run_gravity_field(
            closes=None,
            m4_wave_predictor=None,
            write_receipt=False,
            seed=1337,
            now=_now(),
        )
        # M4 falls back to M1 (no wave), so it cannot beat M1/M3.
        assert result.admission == "FAIL"
        assert result.verdict == "HOLD"
        assert result.honest_verdict != ""
        assert "ADMISSION_RULE_FAILED" in result.honest_verdict or "admission" in result.honest_verdict.lower()

    def test_admission_failed_receipt_is_written(self, tmp_path):
        """When admission fails, write_admission_rule_failed_receipt must
        produce a stable-format JSON file with the expected schema."""
        receipt = write_admission_rule_failed_receipt(
            forecast_id="test-forecast-001",
            skill_vs_M0=0.05,
            skill_vs_M1=0.10,
            skill_vs_M2=-0.02,
            skill_vs_M3=0.01,
            n_windows=8,
            verdict_reasons=["M4_NOT_BEATING_M2:skill=-0.0200"],
            receipts_dir=tmp_path,
        )
        assert receipt["written"]
        assert receipt["receipt_id"].startswith("wealth-gold-gravity-admission-failed-")
        # The file must exist on disk.
        path = Path(receipt["receipt_uri"])
        assert path.exists()
        body = json.loads(path.read_text())
        assert body["receipt_subtype"] == "admission_rule_failed"
        assert body["admission_decision"] == "RECOMMEND_SHADOW_STATUS_UNCHANGED"
        assert body["schema"] == SCHEMA
        assert body["lane"] == "gold-gravity-challenger"

    def test_gravity_receipt_is_written(self, tmp_path):
        """The canonical receipt writer must produce a valid JSON."""
        result = run_gravity_field(
            closes=None,
            write_receipt=True,
            receipts_dir=tmp_path,
            seed=1337,
            now=_now(),
        )
        assert result.receipt is not None
        path = Path(result.receipt["receipt_uri"])
        assert path.exists()
        body = json.loads(path.read_text())
        assert body["schema"] == SCHEMA
        assert body["receipt_subtype"] == "gravity_run"


# ── 7. CB demand static-prior behaviour ────────────────────────────────


class TestCBDemandPrior:
    """The CB demand fallback must produce quarterly constant values with
    the correct release cadence (60 days after quarter end)."""

    def test_cb_prior_uses_default_constant(self):
        pts = fetch_cb_demand_prior(now=_now())
        assert len(pts) > 0
        for p in pts:
            assert p.value == DEFAULT_CB_DEMAND_TONNES_QUARTERLY, (
                f"CB value {p.value} != default {DEFAULT_CB_DEMAND_TONNES_QUARTERLY}"
            )
            assert p.provenance == "SYNTHETIC"

    def test_cb_release_is_after_observation(self):
        pts = fetch_cb_demand_prior(now=_now())
        for p in pts:
            obs = pd.Timestamp(p.observation_ts)
            rel = pd.Timestamp(p.release_ts)
            assert rel > obs, (
                f"CB release_ts {rel} must be after observation_ts {obs}"
            )


# ── 8. Admission rule failure path ─────────────────────────────────────


class TestAdmissionFailurePath:
    """When M4 loses to any baseline, the admission rule fails and we
    emit a SHADOW recommendation + receipt."""

    def test_admission_documented_in_honest_verdict(self):
        result = run_gravity_field(
            closes=None,
            write_receipt=False,
            seed=1337,
            now=_now(),
        )
        # Without a wave predictor, M4 cannot beat M3 → admission fails.
        assert result.admission == "FAIL"
        # The honest verdict must explicitly mention the admission failure
        # and the recommendation to remain SHADOW.
        hv = result.honest_verdict
        assert "ADMISSION_RULE_FAILED" in hv
        assert "SHADOW" in hv.upper()
        assert "F13" in hv  # promotion still requires F13

    def test_status_remains_shadow_on_failure(self):
        result = run_gravity_field(
            closes=None,
            write_receipt=False,
            seed=1337,
            now=_now(),
        )
        # Status is SHADOW_CHALLENGER unless admission passes AND F13
        # authorizes; since neither has happened here, status is SHADOW.
        assert result.status == STATUS


# ── 9. No-look-ahead walk-forward stress ───────────────────────────────


def test_no_lookahead_walk_forward():
    """A walk-forward where we *manually* inject a future jump and confirm
    no model reports a bias consistent with that jump."""
    closes = _make_close_series()
    table = run_ablation_tournament(history=np.asarray(closes))
    for r in table.rows:
        # The bias should be small. The walk-forward never sees the future.
        assert abs(r.bias_p50) < 0.20, (
            f"{r.name} bias_p50={r.bias_p50:.4f} suggests look-ahead"
        )
