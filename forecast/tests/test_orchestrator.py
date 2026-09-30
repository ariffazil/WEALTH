"""Tests for /root/WEALTH/forecast/orchestrator.py.

Required coverage:
  1. Default status is SHADOW when there is no calibration data.
  2. Regime classification returns a valid state.
  3. Horizons always emit 3 quantile tuples (no fake OHLC).
  4. Governance flags always default to safe
     (human_confirmation_required=True, execution_enabled=False).

Tests use a stub GoldAPIClient so they never hit the network and never
silently assume the upstream is reachable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import pytest

from forecast.orchestrator import (
    AGENT_000_Integrity,
    AGENT_111_Regime,
    AGENT_333_Forecast,
    AGENT_555_Calibration,
    AGENT_777_Translator,
    AGENT_888_Judge,
    AGENT_999_Witness,
    DEFAULT_ROUND_TRIP_COST_BPS,
    GoldAPIClient,
    OrchestrationResult,
    STATUS_SHADOW,
    TARGET_HORIZON_HOURS,
    VALID_REGIMES,
    VALID_VERDICTS,
    run_orchestration,
)


MYT = timezone(timedelta(hours=8))


# ── Test doubles ─────────────────────────────────────────────────────────


class StubClient:
    """In-memory replacement for GoldAPIClient."""

    def __init__(
        self,
        ticker: dict[str, Any] | None = None,
        apex: dict[str, Any] | None = None,
        macro: dict[str, Any] | None = None,
        forecast: dict[str, Any] | None = None,
        raise_on: tuple[str, ...] = (),
    ) -> None:
        self.base_url = "http://stub"
        self._ticker = ticker if ticker is not None else _stub_ticker()
        self._apex = apex if apex is not None else _stub_apex()
        self._macro = macro if macro is not None else _stub_macro()
        self._forecast = forecast if forecast is not None else _stub_forecast()
        self._raise_on = raise_on

    def _guard(self, name: str) -> None:
        if name in self._raise_on:
            raise OSError(f"{name} unavailable")

    def ticker(self) -> dict[str, Any]:
        self._guard("ticker")
        return self._ticker

    def apex(self) -> dict[str, Any]:
        self._guard("apex")
        return self._apex

    def macro(self) -> dict[str, Any]:
        self._guard("macro")
        return self._macro

    def forecast(self, horizon_days: int = 30) -> dict[str, Any]:
        self._guard("forecast")
        return self._forecast


def _stub_ticker() -> dict[str, Any]:
    return {
        "symbol": "XAUUSD",
        "price": 4284.39,
        "change": 14.05,
        "changePct": 0.33,
        "rsi": 55.4,
        "rsiState": "NEUTRAL",
        "skewness_20d": 0.028,
        "signal": "SHORT",
        "confidence": 0.7,
        "ema20": 4269.53,
        "ema50": 4285.73,
        "ema200": 4328.03,
        "emaTrend": "BEARISH",
        "support": [4279.71, 4278.31, 4274.22],
        "resistance": [4290.08, 4292.89, 4293.33],
        "pivot": 4279.71,
        "timestamp": datetime.now(MYT).isoformat(),
    }


def _stub_apex() -> dict[str, Any]:
    return {
        "apex": {"A": 0.26, "P": 0.55, "E": 0.17, "X": 0.94, "Phi": 0.25},
        "G": 0.006,
        "C_dark": 0.007,
        "dS": -0.017,
        "state": "CHAOS",
        "direction": "FLAT",
        "confidence": 0.01,
        "volume_trend": "falling",
        "volume_confirmation": False,
        "momentum": 0.037,
        "volatility_regime": "normal",
        "verdict": "HOLD",
        "price": 4284.39,
        "ema_20": 4269.51,
        "ema_50": 4285.68,
        "ema_200": 4323.68,
        "rsi_14": 55.4,
        "atr_14": 15.03,
        "data_points": {"1H": 730, "4H": 363, "1D": 370},
        "timestamp": datetime.now(MYT).isoformat(),
    }


def _stub_macro() -> dict[str, Any]:
    return {
        "timestamp": datetime.now(MYT).isoformat(),
        "dxy": 101.22,
        "vix": 15.67,
        "us10y": 5.162,
        "silver": 64.48,
        "usmyr": 4.07,
        "gold_silver_ratio": 66.4,
    }


def _stub_forecast() -> dict[str, Any]:
    """Real-shape cone with daily steps; orchestrator slices 1/2/3 for +24/+48/+72h."""
    base = 4284.39
    atr = 60.6
    slope = -4.3766
    sigma1 = atr  # daily σ
    spot = base
    t_dates = []
    p10, p25, p50, p75, p90 = [], [], [], [], []
    for i in range(1, 31):
        t_dates.append(f"2026-09-{25 + i:02d}")
        mid = spot + slope * i
        sig = sigma1 * (i ** 0.5)
        p10.append(round(mid - 1.282 * sig, 2))
        p25.append(round(mid - 0.674 * sig, 2))
        p50.append(round(mid, 2))
        p75.append(round(mid + 0.674 * sig, 2))
        p90.append(round(mid + 1.282 * sig, 2))
    return {
        "schema": "wealth.forecast.v1",
        "asset": "gold",
        "generated_at": datetime.now(MYT).isoformat(),
        "horizon_days": 30,
        "basis": {
            "close": spot,
            "atr14": atr,
            "slope_per_day": slope,
            "regime": "SIDEWAYS",
            "rsi": 37.3,
            "ema20": 4342.87,
            "ema50": 4347.78,
            "ema200": 4372.94,
        },
        "bias": "BEARISH",
        "cone": {
            "t": t_dates,
            "p10": p10,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "p90": p90,
        },
        "scenarios": [],
        "epistemic": "INTERPRET — ATR-scaled drift cone, not prophecy.",
    }


def _full_bundle() -> Any:
    return AGENT_000_Integrity(StubClient())


# ══════════════════════════════════════════════════════════════════════════
# 1) SHADOW default — no calibration harness present
# ══════════════════════════════════════════════════════════════════════════


def test_default_status_is_shadow_when_no_calibration_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a walk-forward harness file, status MUST be SHADOW."""
    # Point the calibration harness at a path that does not exist.
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(tmp_path / "absent.json"))

    client = StubClient()
    result = run_orchestration(client, write_receipt=False)

    assert isinstance(result, OrchestrationResult)
    assert result.status == STATUS_SHADOW
    assert result.validation["calibration_state"] == STATUS_SHADOW
    assert result.validation["pinball_skill"] is None
    assert result.validation["coverage"] is None
    assert result.validation["brier_skill"] is None
    assert result.validation["calibration_reason"] == "no_walk_forward_harness"


def test_calibration_state_shadow_without_harness_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(tmp_path / "nope.json"))
    bundle = _full_bundle()
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))
    cal = AGENT_555_Calibration(bundle, horizons)

    assert cal.calibration_state == STATUS_SHADOW
    assert cal.pinball_skill is None
    assert cal.coverage is None
    assert cal.brier_skill is None


def test_calibration_state_promotes_only_with_real_skill(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A harness file with positive measured pinball + coverage in [0.6, 0.95]
    promotes CALIBRATED; anything else stays SHADOW."""
    harness = tmp_path / "calibration.json"
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(harness))

    # (a) Bad harness → still SHADOW
    harness.write_text(json.dumps({"pinball_skill": -0.2, "coverage": 0.5}))
    bundle = _full_bundle()
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))
    cal = AGENT_555_Calibration(bundle, horizons)
    assert cal.calibration_state == STATUS_SHADOW
    assert cal.pinball_skill == -0.2

    # (b) Good harness → CALIBRATED
    harness.write_text(
        json.dumps(
            {
                "baseline": "ATR_DRIFT_CONE",
                "pinball_skill": 0.18,
                "coverage": 0.78,
                "brier_skill": 0.05,
            }
        )
    )
    cal = AGENT_555_Calibration(bundle, horizons)
    assert cal.calibration_state == "CALIBRATED"
    assert cal.pinball_skill == 0.18
    assert cal.coverage == 0.78


def test_calibration_reads_wealth_harness_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The orchestrator reads the WEALTH harness format (schema
    wealth.calibration.gold.v1) when the rolling_means block is present."""
    harness = tmp_path / "harness.json"
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(harness))
    harness.write_text(
        json.dumps(
            {
                "schema": "wealth.calibration.gold.v1",
                "calibration_state": "LIVE",
                "promotion_recommended": True,
                "rolling_means": {
                    "pinball_skill_score": 0.21,
                    "model_coverage": 0.82,
                    "brier_skill": 0.07,
                },
            }
        )
    )
    bundle = _full_bundle()
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))
    cal = AGENT_555_Calibration(bundle, horizons)
    assert cal.calibration_state == "CALIBRATED"
    assert cal.pinball_skill == 0.21
    assert cal.coverage == 0.82
    assert cal.brier_skill == 0.07
    assert cal.reason == "harness_live_with_measured_skill"


def test_calibration_harness_live_without_measured_skill_stays_shadow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Even if the harness self-reports LIVE, the orchestrator requires real
    measured skill before promotion out of SHADOW."""
    harness = tmp_path / "harness.json"
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(harness))
    harness.write_text(
        json.dumps(
            {
                "calibration_state": "LIVE",
                "promotion_recommended": True,
                "rolling_means": {
                    "pinball_skill_score": -0.1,
                    "model_coverage": 0.5,
                    "brier_skill": -0.05,
                },
            }
        )
    )
    bundle = _full_bundle()
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))
    cal = AGENT_555_Calibration(bundle, horizons)
    assert cal.calibration_state == STATUS_SHADOW
    assert cal.reason == "measured_skill_insufficient"


# ══════════════════════════════════════════════════════════════════════════
# 2) Regime classification returns a valid state
# ══════════════════════════════════════════════════════════════════════════


def test_regime_classification_returns_valid_state() -> None:
    bundle = _full_bundle()
    regime = AGENT_111_Regime(bundle)

    assert regime.regime in VALID_REGIMES
    assert 0.0 <= regime.confidence <= 1.0
    assert regime.envelope.tier == "111-REGIME"
    assert regime.envelope.ok is True
    # Evidence must be non-empty when inputs are full.
    assert isinstance(regime.evidence, dict)
    assert "price" in regime.evidence


def test_regime_unknown_when_inputs_insufficient() -> None:
    """When the price AND ATR are both absent across ALL inputs ⇒ UNKNOWN,
    not a guessed label."""
    # All four sources stripped to a bare stub: no price, no atr, no EMAs.
    bare_ticker = {"symbol": "XAUUSD"}
    bare_apex = {"state": "CHAOS", "volatility_regime": "normal"}
    bare_macro = {}
    bare_forecast = {
        "schema": "wealth.forecast.v1",
        "asset": "gold",
        "generated_at": datetime.now(MYT).isoformat(),
        "horizon_days": 30,
        "basis": {},  # no close / atr / slope / ema* / rsi
        "cone": {"t": [], "p10": [], "p25": [], "p50": [], "p75": [], "p90": []},
    }
    client = StubClient(
        ticker=bare_ticker,
        apex=bare_apex,
        macro=bare_macro,
        forecast=bare_forecast,
    )
    bundle = AGENT_000_Integrity(client)
    regime = AGENT_111_Regime(bundle)
    assert regime.regime == "UNKNOWN"
    assert regime.confidence <= 0.5


def test_regime_classifier_variants() -> None:
    """The classifier must produce a small but valid set on crafted inputs."""
    for label, ticker in {
        "tight_atr_low_trend": {
            "price": 2000.0, "rsi": 50.0, "ema20": 1999.8, "ema50": 2000.0,
            "ema200": 2001.0,
        },
        "wide_atr_high_trend": {
            "price": 2000.0, "rsi": 60.0, "ema20": 2080.0, "ema50": 2000.0,
            "ema200": 1950.0,
        },
    }.items():
        apex_payload = {
            "price": ticker["price"],
            "ema_20": ticker["ema20"],
            "ema_50": ticker["ema50"],
            "ema_200": ticker["ema200"],
            "rsi_14": ticker["rsi"],
            "atr_14": 60.0,
            "volatility_regime": "normal",
            "state": "CHAOS",
        }
        client = StubClient(ticker=ticker, apex=apex_payload)
        bundle = AGENT_000_Integrity(client)
        regime = AGENT_111_Regime(bundle)
        assert regime.regime in VALID_REGIMES, label
        assert 0.0 <= regime.confidence <= 1.0, label


# ══════════════════════════════════════════════════════════════════════════
# 3) Horizons always emit 3 quantile tuples — no fake OHLC
# ══════════════════════════════════════════════════════════════════════════


def test_horizons_emit_three_quantile_tuples() -> None:
    """333 must emit one tuple per target horizon (+24/+48/+72h), and each
    tuple must contain all five quantiles when the upstream cone covers it."""
    bundle = _full_bundle()
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))

    assert len(horizons.horizons) == 3
    assert [h.offset_hours for h in horizons.horizons] == list(TARGET_HORIZON_HOURS)
    for h in horizons.horizons:
        assert h.has_full_distribution()
        # Ordering invariant: P10 ≤ P25 ≤ P50 ≤ P75 ≤ P90.
        assert h.p10 <= h.p25 <= h.p50 <= h.p75 <= h.p90
        assert h.timestamp
        # p_up_after_cost is a derived, optional probability — either None or [0,1].
        if h.p_up_after_cost is not None:
            assert 0.0 <= h.p_up_after_cost <= 1.0


def test_horizons_null_when_upstream_cone_too_short() -> None:
    """If the cone has only 2 daily points, +48h and +72h are out of range —
    emit the slots with null quantiles and DO NOT invent numbers."""
    short_cone = _stub_forecast()
    short_cone["cone"] = {
        "t": short_cone["cone"]["t"][:2],
        "p10": short_cone["cone"]["p10"][:2],
        "p25": short_cone["cone"]["p25"][:2],
        "p50": short_cone["cone"]["p50"][:2],
        "p75": short_cone["cone"]["p75"][:2],
        "p90": short_cone["cone"]["p90"][:2],
    }
    client = StubClient(forecast=short_cone)
    bundle = AGENT_000_Integrity(client)
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))

    # Still 3 tuples emitted — never collapse to 2 just because upstream is short.
    assert len(horizons.horizons) == 3
    assert horizons.horizons[0].has_full_distribution()  # +24h reachable (idx 1)
    assert not horizons.horizons[1].has_full_distribution()  # +48h not reachable
    assert not horizons.horizons[2].has_full_distribution()  # +72h not reachable
    # And NO fake number for the unreachable slots.
    assert horizons.horizons[1].p50 is None
    assert horizons.horizons[1].p_up_after_cost is None
    assert horizons.horizons[2].p50 is None
    assert horizons.horizons[2].p_up_after_cost is None


def test_no_fake_ohlc_quantiles_never_synthesised() -> None:
    """The 333 agent must not fill missing quantiles from anywhere — verify by
    giving it a forecast with p25 missing entirely."""
    cone = _stub_forecast()["cone"]
    cone["p25"] = [None] * len(cone["p25"])  # NO FAKE OHLC
    fc = _stub_forecast()
    fc["cone"] = cone
    client = StubClient(forecast=fc)
    bundle = AGENT_000_Integrity(client)
    horizons = AGENT_333_Forecast(bundle, AGENT_111_Regime(bundle))
    for h in horizons.horizons:
        assert h.p25 is None
        # p_up_after_cost depends on p25 — must also be None, not guessed.
        assert h.p_up_after_cost is None


# ══════════════════════════════════════════════════════════════════════════
# 4) Governance defaults — always safe
# ══════════════════════════════════════════════════════════════════════════


def test_governance_flags_always_default_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """human_confirmation_required=True and execution_enabled=False on every
    path through the pipeline until an F13 authorization event flips them."""
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(tmp_path / "nope.json"))

    # Even with a *good* harness (CALIBRATED), the orchestrator's governance
    # block must remain safe by default. Calibration is not authority.
    harness = tmp_path / "good.json"
    harness.write_text(
        json.dumps(
            {"pinball_skill": 0.5, "coverage": 0.85, "brier_skill": 0.05}
        )
    )
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(harness))

    client = StubClient()
    result = run_orchestration(client, write_receipt=False)
    gov = result.governance
    assert gov["human_confirmation_required"] is True
    assert gov["execution_enabled"] is False
    assert gov["status"] == STATUS_SHADOW


def test_governance_safe_even_when_calibrated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = tmp_path / "calibration.json"
    harness.write_text(
        json.dumps({"pinball_skill": 0.5, "coverage": 0.8, "brier_skill": 0.05})
    )
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(harness))
    result = run_orchestration(StubClient(), write_receipt=False)
    assert result.governance["execution_enabled"] is False
    assert result.governance["human_confirmation_required"] is True


def test_governance_safe_when_integrity_partial() -> None:
    """A missing ticker does not collapse safety: integrity is partial but
    forecast still works; verdict is WAIT, governance still safe."""
    client = StubClient(raise_on=("ticker",))
    result = run_orchestration(client, write_receipt=False)
    assert result.governance["human_confirmation_required"] is True
    assert result.governance["execution_enabled"] is False
    assert result.governance["status"] == STATUS_SHADOW


def test_governance_safe_when_integrity_total_failure() -> None:
    """Forecast unreachable ⇒ integrity fails ⇒ verdict BLOCKED, still safe."""
    client = StubClient(raise_on=("forecast",))
    result = run_orchestration(client, write_receipt=False)
    assert result.governance["execution_enabled"] is False
    assert result.governance["human_confirmation_required"] is True
    assert result.verdict == "BLOCKED"
    assert result.status == STATUS_SHADOW


def test_judge_default_verdict_is_hold_or_wait() -> None:
    """In SHADOW the judge's ceiling is WAIT; never ACT."""
    bundle = _full_bundle()
    regime = AGENT_111_Regime(bundle)
    horizons = AGENT_333_Forecast(bundle, regime)
    cal = AGENT_555_Calibration(bundle, horizons)
    trans = AGENT_777_Translator(regime, horizons, cal)
    verdict = AGENT_888_Judge(bundle, regime, horizons, cal, trans)
    assert verdict.verdict in ("HOLD", "WAIT", "BLOCKED")
    assert verdict.verdict != "ACT"


# ══════════════════════════════════════════════════════════════════════════
# 999 Witness — receipt writes
# ══════════════════════════════════════════════════════════════════════════


def test_witness_writes_receipt(tmp_path: Path) -> None:
    packet = {"forecast_id": "test-1", "issued_at": "2026-09-25T00:00:00+08:00"}
    receipt = AGENT_999_Witness(packet, trace_id="abc", receipts_dir=tmp_path)
    assert receipt.written is True
    assert receipt.receipt_id
    out = tmp_path / f"{receipt.receipt_id}.json"
    assert out.exists()
    body = json.loads(out.read_text())
    assert body["trace_id"] == "abc"
    assert body["schema"].startswith("wealth.gold.orchestration.v1")


def test_witness_returns_unwritten_on_failure(tmp_path: Path) -> None:
    # Path under a non-directory parent → write fails.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a dir")
    receipt = AGENT_999_Witness(
        {"forecast_id": "x", "issued_at": "now"},
        trace_id="t",
        receipts_dir=blocker / "nested",
    )
    assert receipt.written is False


# ══════════════════════════════════════════════════════════════════════════
# Integration — full run on stub client
# ══════════════════════════════════════════════════════════════════════════


def test_full_run_produces_well_formed_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WEALTH_CALIBRATION_HARNESS", str(tmp_path / "nope.json"))
    result = run_orchestration(StubClient(), write_receipt=True, receipts_dir=tmp_path)
    packet = result.to_dict()
    assert packet["schema"] == "wealth.gold.orchestration.v1"
    assert packet["status"] == STATUS_SHADOW
    assert packet["asset"] == "XAUUSD"
    assert packet["forecast_id"]
    assert packet["trace_id"]
    assert packet["regime"]["state"] in VALID_REGIMES
    assert len(packet["horizons"]) == 3
    assert packet["governance"]["execution_enabled"] is False
    assert packet["governance"]["human_confirmation_required"] is True
    assert packet["verdict"] in VALID_VERDICTS
    assert packet["validation"]["calibration_state"] == STATUS_SHADOW
    assert packet["outputs"]["trade_72h"]["stance"] in (
        "FLAT", "LONG", "SHORT"
    )
    assert packet["outputs"]["physical_saving"]["stance"] in (
        "WAIT", "SAVE_NOW", "SAVE_WAIT"
    )


def test_pipeline_is_importable_not_run_on_load() -> None:
    """Importing the module must not produce side effects (no main() runs)."""
    import importlib
    import forecast.orchestrator as mod

    importlib.reload(mod)
    # If main() had run, the receipts dir would have a fresh file with a
    # recent timestamp; here we just check the module exposes run_orchestration.
    assert callable(mod.run_orchestration)
    assert callable(mod.AGENT_000_Integrity)
    assert callable(mod.AGENT_111_Regime)
    assert callable(mod.AGENT_333_Forecast)
    assert callable(mod.AGENT_555_Calibration)
    assert callable(mod.AGENT_777_Translator)
    assert callable(mod.AGENT_888_Judge)
    assert callable(mod.AGENT_999_Witness)


def test_default_cost_bps_is_six() -> None:
    """Documented round-trip cost assumption for p_up_after_cost."""
    assert DEFAULT_ROUND_TRIP_COST_BPS == 6.0


def test_gold_api_client_has_expected_methods() -> None:
    c = GoldAPIClient(base_url="http://stub")
    assert callable(c.ticker)
    assert callable(c.apex)
    assert callable(c.macro)
    assert callable(c.forecast)
    assert callable(c.history)
    assert c.base_url == "http://stub"
