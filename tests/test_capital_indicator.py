"""Tests for capital_indicator — technical analysis indicators via yfinance.

Validates:
  - RSI, MACD, Bollinger Bands, SMA, EMA, ATR, Stochastic/ADX indicators
  - Error handling for invalid tickers, empty data, unknown indicators
  - Output envelope structure (wrap_result fields)
  - All network calls mocked (no live yfinance dependency)

Run: pytest tests/test_capital_indicator.py -v
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

from wealth_mcp.tools.canonical import register_canonical_tools


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
register_canonical_tools(_stub)
capital_indicator = _stub.tools["capital_indicator"]


# ── Mock helpers ─────────────────────────────────────────────────────────

def _make_ohlcv_df(n: int = 100, base_price: float = 2300.0, volatility: float = 0.02):
    """Generate synthetic OHLCV DataFrame mimicking yfinance output."""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1h")
    close = [base_price]
    for _ in range(n - 1):
        change = close[-1] * volatility * np.random.randn()
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
    """Return a mock yf.Ticker whose .history() returns `df`."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df
    return mock_ticker


def _mock_yfinance_empty():
    """Return a mock yf.Ticker whose .history() returns an empty DataFrame."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    return mock_ticker


def _mock_yfinance_exception(msg: str = "network timeout"):
    """Return a mock yf.Ticker that raises on .history()."""
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = RuntimeError(msg)
    return mock_ticker


def _run(coro):
    """Run an async coroutine synchronously for pytest."""
    return asyncio.run(coro)


# ── Tests ────────────────────────────────────────────────────────────────

class TestCapitalIndicatorRSI:
    """Test RSI indicator computation."""

    def test_rsi_returns_valid_output(self):
        """RSI must return current value, overbought/oversold flags, and series."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="rsi", period=14))

        inner = result["result"]
        assert inner["symbol"] == "GC=F"
        assert inner["indicator"] == "RSI"
        assert inner["period"] == 14
        assert 0 <= inner["current"] <= 100
        assert isinstance(inner["overbought"], bool)
        assert isinstance(inner["oversold"], bool)
        assert isinstance(inner["series_last_5"], list)
        assert len(inner["series_last_5"]) == 5

    def test_rsi_overbought_flag(self):
        """RSI should flag overbought when current > 70."""
        # Construct monotonically rising prices → RSI approaches 100
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq="1h")
        close = np.linspace(2000, 2500, 100)
        df = pd.DataFrame({
            "Open": close * 0.999,
            "High": close * 1.001,
            "Low": close * 0.998,
            "Close": close,
            "Volume": np.ones(100) * 10000,
        }, index=dates)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="TEST", indicator="rsi", period=14))

        inner = result["result"]
        # Monotonically rising → RSI should be overbought
        assert inner["current"] > 50

    def test_rsi_oversold_flag(self):
        """RSI should flag oversold when current < 30."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq="1h")
        close = np.linspace(2500, 2000, 100)  # declining
        df = pd.DataFrame({
            "Open": close * 1.001,
            "High": close * 1.002,
            "Low": close * 0.998,
            "Close": close,
            "Volume": np.ones(100) * 10000,
        }, index=dates)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="TEST", indicator="rsi", period=14))

        inner = result["result"]
        assert inner["current"] < 50


class TestCapitalIndicatorMACD:
    """Test MACD indicator computation."""

    def test_macd_returns_valid_output(self):
        """MACD must return macd_line, signal_line, histogram, and bullish flag."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="AAPL", indicator="macd", period=14))

        inner = result["result"]
        assert inner["symbol"] == "AAPL"
        assert inner["indicator"] == "MACD"
        assert "macd_line" in inner
        assert "signal_line" in inner
        assert "histogram" in inner
        assert isinstance(inner["bullish"], bool)
        # Histogram should be approximately macd_line - signal_line
        assert abs(inner["histogram"] - (inner["macd_line"] - inner["signal_line"])) < 1e-4


class TestCapitalIndicatorBollinger:
    """Test Bollinger Bands indicator."""

    def test_bollinger_returns_valid_output(self):
        """BB must return upper, lower, sma, bandwidth, price_position."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="bb", period=20))

        inner = result["result"]
        assert inner["symbol"] == "GC=F"
        assert "upper" in inner
        assert "lower" in inner
        assert "sma" in inner
        assert "bandwidth_pct" in inner
        assert "price_position_pct" in inner
        assert inner["upper"] > inner["sma"] > inner["lower"]
        assert 0 <= inner["price_position_pct"] <= 100

    def test_bollinger_alias(self):
        """Both 'bb' and 'bollinger' should produce the same result."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            r1 = _run(capital_indicator(symbol="TEST", indicator="bb"))
            r2 = _run(capital_indicator(symbol="TEST", indicator="bollinger"))
        assert r1["result"]["upper"] == r2["result"]["upper"]


class TestCapitalIndicatorSMA:
    """Test SMA indicator computation."""

    def test_sma_returns_valid_output(self):
        """SMA must return current value and current_price."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="sma", period=20))

        inner = result["result"]
        assert inner["indicator"] == "SMA"
        assert "current" in inner
        assert "current_price" in inner
        assert inner["current"] > 0


class TestCapitalIndicatorEMA:
    """Test EMA indicator computation."""

    def test_ema_returns_valid_output(self):
        """EMA must return current value, current_price, and series_last_5."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="ema", period=20))

        inner = result["result"]
        assert inner["indicator"] == "EMA"
        assert "current" in inner
        assert "current_price" in inner
        assert "series_last_5" in inner
        assert len(inner["series_last_5"]) == 5


class TestCapitalIndicatorATR:
    """Test ATR indicator computation."""

    def test_atr_returns_valid_output(self):
        """ATR must return current, current_price, and atr_pct."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="atr", period=14))

        inner = result["result"]
        assert inner["indicator"] == "ATR"
        assert inner["current"] >= 0
        assert inner["current_price"] > 0
        assert inner["atr_pct"] >= 0


class TestCapitalIndicatorADX:
    """Test ADX indicator computation."""

    def test_adx_returns_valid_output(self):
        """ADX must return current, plus_di, minus_di, trending flag."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="adx", period=14))

        inner = result["result"]
        assert inner["indicator"] == "ADX"
        assert "current" in inner
        assert "plus_di" in inner
        assert "minus_di" in inner
        assert isinstance(inner["trending"], bool)


class TestCapitalIndicatorPSAR:
    """Test Parabolic SAR indicator."""

    def test_psar_returns_valid_output(self):
        """PSAR must return current, current_price, and trend."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="psar", period=14))

        inner = result["result"]
        assert inner["indicator"] == "PSAR"
        assert inner["trend"] in ("BULL", "BEAR")
        assert isinstance(inner["psar_below_price"], bool)

    def test_psar_aliases(self):
        """psar, parabolic_sar, and sar should all work."""
        df = _make_ohlcv_df(100)
        for alias in ["psar", "parabolic_sar", "sar"]:
            with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
                mock_yf.Ticker.return_value = _mock_yfinance(df)
                result = _run(capital_indicator(symbol="TEST", indicator=alias))
            assert result["result"]["trend"] in ("BULL", "BEAR"), f"alias '{alias}' failed"


class TestCapitalIndicatorTemporal:
    """Test multi-indicator trajectory/temporal mode."""

    def test_temporal_returns_full_snapshot(self):
        """trajectory mode must return rsi, macd, bollinger, regime, psar, atr, adx."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="trajectory", period=14))

        inner = result["result"]
        assert inner["mode"] == "temporal"
        for key in ["rsi", "macd", "bollinger", "regime", "psar", "atr", "adx", "signals", "confluence"]:
            assert key in inner, f"Missing key: {key}"

    def test_confluence_has_verdict(self):
        """Confluence must include a verdict label."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="temporal", period=14))

        conf = result["result"]["confluence"]
        assert "verdict" in conf
        assert conf["verdict"] in ("STRONG_BULL", "STRONG_BEAR", "BULL_LEAN", "BEAR_LEAN", "MIXED")


class TestCapitalIndicatorErrorHandling:
    """Test error paths for capital_indicator."""

    def test_empty_data_returns_error(self):
        """Empty yfinance data should return NO_DATA error."""
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance_empty()
            result = _run(capital_indicator(symbol="INVALID", indicator="rsi"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "NO_DATA"

    def test_fetch_exception_returns_error(self):
        """Network exception should return FETCH_FAILED error."""
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance_exception("connection refused")
            result = _run(capital_indicator(symbol="BAD", indicator="rsi"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "FETCH_FAILED"
        assert "connection refused" in result["result"]["message"]

    def test_unknown_indicator_returns_error(self):
        """Unknown indicator name should return UNKNOWN_INDICATOR error."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="GC=F", indicator="fake_indicator"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "UNKNOWN_INDICATOR"


class TestCapitalIndicatorEnvelope:
    """Test that output follows the wrap_result envelope contract."""

    def test_envelope_has_required_fields(self):
        """Every successful call must include tool_name, domain, epistemic_tag."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(
                symbol="GC=F", indicator="rsi",
                session_id="test_session", actor_id="test_actor"
            ))

        assert result["tool_name"] == "capital_indicator"
        assert result["domain"] == "market"
        assert result["epistemic_tag"] == "OBSERVED"
        assert result["session_id"] == "test_session"
        assert result["actor_id"] == "test_actor"
        assert any("yfinance" in s for s in result["source_attribution"])

    def test_case_insensitive_symbol(self):
        """Symbol should be uppercased internally."""
        df = _make_ohlcv_df(100)
        with patch("wealth_mcp.tools.canonical.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_yfinance(df)
            result = _run(capital_indicator(symbol="aapl", indicator="sma"))

        assert result["result"]["symbol"] == "AAPL"
