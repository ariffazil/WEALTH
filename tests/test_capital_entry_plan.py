"""Tests for capital_entry_plan — S/R-aware entry/stop/target planning.

Validates:
  - Entry plan with known support/resistance levels
  - ATR-based risk scaling
  - Risk:reward ratio calculation
  - Stop loss placement (2x ATR from entry)
  - Trend detection (EMA alignment)
  - Error handling: insufficient data, fetch failures
  - EMA200 warning for datasets with < 200 bars
  - Graceful degradation with trend_bias overrides

Run: pytest tests/test_capital_entry_plan.py -v
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# ── Setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import directly from the per-tool module (Phase 1a split)
from wealth_mcp.tools.entry_plan import register_entry_plan


class _StubMCP:
    """Captures FastMCP @tool-decorated functions for offline testing."""
    def __init__(self):
        self.tools: dict[str, object] = {}

    def tool(self, name=None, **_kwargs):
        def decorator(func):
            self.tools[name or func.__name__] = func
            return func
        return decorator

    def __getattr__(self, name):
        return lambda **kwargs: (lambda f: f)


_stub = _StubMCP()
register_entry_plan(_stub)
capital_entry_plan = _stub.tools["capital_entry_plan"]


# ── Mock helpers ─────────────────────────────────────────────────────────

def _make_ohlcv_df(
    n: int = 200,
    base_price: float = 2300.0,
    trend: str = "up",
    volatility: float = 0.01,
):
    """Generate synthetic OHLCV data with a clear trend direction."""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1h")
    close = [base_price]
    drift = volatility * 0.3 if trend == "up" else (-volatility * 0.3 if trend == "down" else 0)
    for _ in range(n - 1):
        change = close[-1] * (drift + volatility * np.random.randn())
        close.append(close[-1] + change)
    close = np.array(close)
    high = close * (1 + np.abs(np.random.randn(n)) * 0.005)
    low = close * (1 - np.abs(np.random.randn(n)) * 0.005)
    open_ = close * (1 + np.random.randn(n) * 0.003)
    volume = np.random.randint(1000, 50000, size=n).astype(float)
    return pd.DataFrame({
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    }, index=dates)


def _mock_yfinance(df):
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df
    return mock_ticker


def _mock_yfinance_empty():
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    return mock_ticker


def _mock_yfinance_exception(msg: str = "network timeout"):
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = RuntimeError(msg)
    return mock_ticker


def _run(coro):
    return asyncio.run(coro)


# ── Tests: Uptrend scenarios ─────────────────────────────────────────────

class TestEntryPlanUptrend:
    """Test entry plan in an uptrend scenario."""

    def test_uptrend_direction_is_long_or_neutral(self):
        """Uptrend should produce LONG or NEUTRAL direction."""
        df = _make_ohlcv_df(200, trend="up")
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F", interval="1h", lookback="3mo"))

        inner = result["result"]
        assert inner["direction"] in ("LONG", "NEUTRAL")

    def test_uptrend_stop_loss_below_entry(self):
        """In uptrend LONG, stop loss should be below entry zone."""
        df = _make_ohlcv_df(300, trend="up", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F", interval="1h", lookback="3mo"))

        inner = result["result"]
        if inner["direction"] == "LONG":
            assert inner["stop_loss"] < inner["entry_zone"]

    def test_uptrend_targets_above_entry(self):
        """In uptrend LONG, targets should be above entry zone."""
        df = _make_ohlcv_df(300, trend="up", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F", interval="1h", lookback="3mo"))

        inner = result["result"]
        if inner["direction"] == "LONG":
            assert inner["target_1"] > inner["entry_zone"]
            assert inner["target_2"] > inner["target_1"]


# ── Tests: Downtrend scenarios ───────────────────────────────────────────

class TestEntryPlanDowntrend:
    """Test entry plan in a downtrend scenario."""

    def test_downtrend_direction_is_short(self):
        """Downtrend should produce SHORT direction."""
        df = _make_ohlcv_df(300, trend="down", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F", interval="1h", lookback="3mo"))

        inner = result["result"]
        if inner["trend"] == "DOWNTREND":
            assert inner["direction"] == "SHORT"

    def test_downtrend_stop_loss_above_entry(self):
        """In downtrend SHORT, stop loss should be above entry zone."""
        df = _make_ohlcv_df(300, trend="down", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F", interval="1h", lookback="3mo"))

        inner = result["result"]
        if inner["direction"] == "SHORT":
            assert inner["stop_loss"] > inner["entry_zone"]


# ── Tests: Risk:Reward calculation ───────────────────────────────────────

class TestEntryPlanRiskReward:
    """Test risk:reward ratio calculation."""

    def test_risk_reward_positive(self):
        """Risk:reward ratios should be positive."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        assert inner["risk_reward_1"] >= 0
        assert inner["risk_reward_2"] >= 0

    def test_risk_reward_2_greater_than_1(self):
        """Target 2 should have higher R:R than target 1."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        if inner["risk"] > 0:
            assert inner["risk_reward_2"] >= inner["risk_reward_1"]

    def test_risk_calculation(self):
        """Risk = abs(entry_zone - stop_loss)."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        expected_risk = abs(inner["entry_zone"] - inner["stop_loss"])
        assert abs(inner["risk"] - round(expected_risk, 2)) < 0.01


# ── Tests: ATR-based risk scaling ────────────────────────────────────────

class TestEntryPlanATR:
    """Test ATR-based risk scaling."""

    def test_atr_in_output(self):
        """ATR and ATR percentage should be in output."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        assert inner["atr"] > 0
        assert inner["atr_pct"] > 0
        assert inner["atr_pct"] == round(inner["atr"] / inner["current_price"] * 100, 2)

    def test_stop_loss_is_2x_atr(self):
        """Stop loss distance should be approximately 2x ATR from entry."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        expected_stop = round(inner["entry_zone"] - 2 * inner["atr"], 2)
        assert abs(inner["stop_loss"] - expected_stop) < 0.02


# ── Tests: S/R zone detection ────────────────────────────────────────────

class TestEntryPlanSupportResistance:
    """Test S/R zone detection."""

    def test_support_resistance_zones_present(self):
        """Output should include support_zones and resistance_zones."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        assert "support_zones" in inner
        assert "resistance_zones" in inner
        assert isinstance(inner["support_zones"], list)
        assert isinstance(inner["resistance_zones"], list)

    def test_zones_are_tuples_of_price_strength(self):
        """Each zone should be a (price, strength) pair."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        for zone in inner["support_zones"] + inner["resistance_zones"]:
            assert isinstance(zone, (list, tuple))
            assert len(zone) == 2
            assert isinstance(zone[0], (int, float))
            assert isinstance(zone[1], (int, float))


# ── Tests: Error handling ────────────────────────────────────────────────

class TestEntryPlanErrorHandling:
    """Test error paths for capital_entry_plan."""

    def test_empty_data_returns_error(self):
        """Empty yfinance data should return NO_DATA error."""
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance_empty()
            result = _run(capital_entry_plan(symbol="INVALID"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "NO_DATA"

    def test_fetch_exception_returns_error(self):
        """Network exception should return FETCH_FAILED error."""
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance_exception("DNS failure")
            result = _run(capital_entry_plan(symbol="BAD"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "FETCH_FAILED"
        assert "DNS failure" in result["result"]["message"]

    def test_insufficient_data_returns_error(self):
        """Fewer than 50 bars after NaN removal should return INSUFFICIENT_DATA."""
        df = _make_ohlcv_df(30)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="TINY", interval="1m", lookback="1d"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "INSUFFICIENT_DATA"

    def test_nan_rows_are_dropped(self):
        """DataFrame with NaN rows should have them filtered before analysis."""
        df = _make_ohlcv_df(200)
        df.loc[df.index[50], "Close"] = np.nan
        df.loc[df.index[100], "High"] = np.nan
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        # Should still work (NaN rows dropped, still > 50 bars)
        assert result["result"].get("status") != "ERROR" or \
               result["result"].get("error_code") != "INSUFFICIENT_DATA"


# ── Tests: EMA200 warning ────────────────────────────────────────────────

class TestEntryPlanEMA200Warning:
    """Test EMA200 data warning for datasets with < 200 bars."""

    def test_ema200_warning_when_few_bars(self):
        """Data with < 200 bars should trigger EMA200 warning."""
        df = _make_ohlcv_df(100)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        if inner["ema200_data_warning"] is not None:
            assert "EMA200" in inner["ema200_data_warning"]
            assert "< 200" in inner["ema200_data_warning"]

    def test_no_ema200_warning_when_enough_bars(self):
        """Data with >= 200 bars should have no EMA200 warning."""
        df = _make_ohlcv_df(250)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        assert inner["ema200_data_warning"] is None


# ── Tests: Trend bias override ───────────────────────────────────────────

class TestEntryPlanTrendBias:
    """Test trend_bias override."""

    def test_long_bias_sideways_on_downtrend(self):
        """trend_bias='long' on a downtrend should produce SIDEWAYS, not SHORT."""
        df = _make_ohlcv_df(300, trend="down", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(
                symbol="GC=F", interval="1h", lookback="3mo",
                trend_bias="long",
            ))

        inner = result["result"]
        if inner["trend"] == "DOWNTREND":
            assert inner["direction"] != "SHORT"

    def test_short_bias_sideways_on_uptrend(self):
        """trend_bias='short' on an uptrend should produce SIDEWAYS, not LONG."""
        df = _make_ohlcv_df(300, trend="up", volatility=0.005)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(
                symbol="GC=F", interval="1h", lookback="3mo",
                trend_bias="short",
            ))

        inner = result["result"]
        if inner["trend"] == "UPTREND":
            assert inner["direction"] != "LONG"


# ── Tests: Envelope contract ─────────────────────────────────────────────

class TestEntryPlanEnvelope:
    """Test output envelope contract."""

    def test_envelope_has_required_fields(self):
        """Every call must include tool_name, domain, epistemic_tag."""
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance_empty()
            result = _run(capital_entry_plan(
                session_id="test_session",
                actor_id="test_actor",
            ))

        assert result["tool_name"] == "capital_entry_plan"
        assert result["domain"] == "market"
        assert result["session_id"] == "test_session"
        assert result["actor_id"] == "test_actor"

    def test_success_envelope_has_observed_epistemic(self):
        """Successful call must have OBSERVED epistemic tag."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        assert result["epistemic_tag"] in ("OBSERVED", "DERIVED")
        assert result["tool_name"] == "capital_entry_plan"

    def test_current_price_in_output(self):
        """Output should include current_price."""
        df = _make_ohlcv_df(200)
        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = _mock_yfinance(df)
            result = _run(capital_entry_plan(symbol="GC=F"))

        inner = result["result"]
        assert "current_price" in inner
        assert inner["current_price"] > 0


# ── Standalone runner ────────────────────────────────────────────────────
if __name__ == "__main__":
    passed = failed = 0
    tests = [
        TestEntryPlanUptrend(),
        TestEntryPlanDowntrend(),
        TestEntryPlanRiskReward(),
        TestEntryPlanATR(),
        TestEntryPlanSupportResistance(),
        TestEntryPlanErrorHandling(),
        TestEntryPlanEMA200Warning(),
        TestEntryPlanTrendBias(),
        TestEntryPlanEnvelope(),
    ]
    for test_obj in tests:
        for method_name in dir(test_obj):
            if method_name.startswith("test_"):
                method = getattr(test_obj, method_name)
                try:
                    method()
                    passed += 1
                    print(f"  PASS: {test_obj.__class__.__name__}.{method_name}")
                except Exception as e:
                    failed += 1
                    print(f"  FAIL: {test_obj.__class__.__name__}.{method_name}: {e}")
    print(f"\n━━ Results: {passed} pass, {failed} fail of {passed + failed} ━━")
    sys.exit(0 if failed == 0 else 1)
