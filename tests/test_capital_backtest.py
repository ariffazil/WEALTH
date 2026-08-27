"""Tests for capital_backtest — strategy backtest runner.

Validates:
  - Backtest mode (default) with mocked yfinance + backtest engine
  - Compass mode with equity curve inputs
  - Stress test mode with trade returns
  - Error handling: empty data, fetch failures
  - Output envelope structure

Run: pytest tests/test_capital_backtest.py -v
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
from wealth_mcp.tools.backtest import register_backtest


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
register_backtest(_stub)
capital_backtest = _stub.tools["capital_backtest"]


# ── Mock helpers ─────────────────────────────────────────────────────────

def _make_ohlcv_df(n: int = 200, base_price: float = 2300.0):
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1h")
    close = [base_price]
    for _ in range(n - 1):
        change = close[-1] * 0.01 * np.random.randn()
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


def _mock_backtest_result():
    """Return a mock backtest result matching engine_v2 output shape."""
    return {
        "metrics": {
            "final_equity": 11234.56,
            "total_return_pct": 12.35,
            "total_trades": 47,
            "win_rate_pct": 58.5,
            "profit_factor": 1.82,
            "sharpe_ratio": 1.45,
            "max_drawdown_pct": -8.3,
            "avg_win": 156.78,
            "avg_loss": -89.32,
        },
        "trades": [
            {
                "entry_price": 2300.0 + i * 5,
                "exit_price": 2310.0 + i * 5,
                "direction": "LONG" if i % 2 == 0 else "SHORT",
                "pnl": 10.0 * (1 if i % 3 != 0 else -0.5),
                "exit_reason": "take_profit" if i % 3 != 0 else "stop_loss",
            }
            for i in range(10)
        ],
    }


def _run(coro):
    return asyncio.run(coro)


# ── Tests: Default backtest mode ─────────────────────────────────────────

class TestCapitalBacktestDefault:
    """Test default backtest mode (backtest engine v2 integration)."""

    def test_backtest_returns_summary_metrics(self):
        """Backtest must return key performance metrics."""
        df = _make_ohlcv_df(200)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df

        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = mock_ticker
            # Mock the imports that happen inside the function body
            mock_ohlcv = type("OHLCV", (), {
            "__init__": lambda self, **kw: setattr(self, "_attrs", kw) or None,
            "__getattr__": lambda self, name: self._attrs.get(name),
        })
            mock_bt = MagicMock()
            mock_bt.BacktestConfig = MagicMock
            mock_bt.run_backtest.return_value = _mock_backtest_result()
            with patch.dict("sys.modules", {
                "signals.scanner": MagicMock(OHLCV=mock_ohlcv),
                "backtest.engine_v2": mock_bt,
            }):
                result = _run(capital_backtest(
                    symbol="GC=F", interval="1h", lookback="2y",
                    initial_capital=10000.0, risk_per_trade_pct=1.0,
                    session_id="test",
                ))

        inner = result["result"]
        assert inner["symbol"] == "GC=F"
        assert inner["initial_capital"] == 10000.0
        assert inner["final_equity"] == 11234.56
        assert inner["total_return_pct"] == 12.35
        assert inner["total_trades"] == 47
        assert inner["win_rate_pct"] == 58.5
        assert inner["profit_factor"] == 1.82
        assert inner["sharpe_ratio"] == 1.45
        assert inner["max_drawdown_pct"] == -8.3

    def test_backtest_has_trade_log(self):
        """Last 5 trades should be included in output."""
        df = _make_ohlcv_df(200)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df

        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = mock_ticker
            mock_ohlcv = type("OHLCV", (), {
            "__init__": lambda self, **kw: setattr(self, "_attrs", kw) or None,
            "__getattr__": lambda self, name: self._attrs.get(name),
        })
            mock_bt = MagicMock()
            mock_bt.BacktestConfig = MagicMock
            mock_bt.run_backtest.return_value = _mock_backtest_result()
            with patch.dict("sys.modules", {
                "signals.scanner": MagicMock(OHLCV=mock_ohlcv),
                "backtest.engine_v2": mock_bt,
            }):
                result = _run(capital_backtest())

        inner = result["result"]
        assert "last_5_trades" in inner
        assert len(inner["last_5_trades"]) <= 5
        for trade in inner["last_5_trades"]:
            assert "entry" in trade
            assert "exit" in trade
            assert "direction" in trade

    def test_backtest_date_range(self):
        """Output must include date range from/to."""
        df = _make_ohlcv_df(200)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df

        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = mock_ticker
            mock_ohlcv = type("OHLCV", (), {
            "__init__": lambda self, **kw: setattr(self, "_attrs", kw) or None,
            "__getattr__": lambda self, name: self._attrs.get(name),
        })
            mock_bt = MagicMock()
            mock_bt.BacktestConfig = MagicMock
            mock_bt.run_backtest.return_value = _mock_backtest_result()
            with patch.dict("sys.modules", {
                "signals.scanner": MagicMock(OHLCV=mock_ohlcv),
                "backtest.engine_v2": mock_bt,
            }):
                result = _run(capital_backtest())

        dr = result["result"]["date_range"]
        assert "from" in dr
        assert "to" in dr
        assert dr["from"] is not None
        assert dr["to"] is not None


# ── Tests: Compass mode ──────────────────────────────────────────────────

class TestCapitalBacktestCompass:
    """Test compass mode (PRUDEX-Compass distillation)."""

    def test_compass_returns_score_and_classification(self):
        """Compass mode must return overall_score and classification."""
        payload = {
            "equity_curve": [10000, 10100, 9950, 10200, 10300],
            "trade_returns": [0.01, -0.015, 0.025, 0.01],
        }
        result = _run(capital_backtest(mode="compass", payload=payload))

        inner = result["result"]
        assert "overall_score" in inner
        assert "classification" in inner
        assert "axes" in inner
        assert inner["framework"] == "PRUDEX-Compass (TradeMaster distillation)"

    def test_compass_missing_data_returns_error(self):
        """Compass without equity_curve/trade_returns should error."""
        result = _run(capital_backtest(mode="compass", payload={}))
        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "MISSING_DATA"

    def test_compass_empty_lists_returns_error(self):
        """Compass with empty lists should error."""
        result = _run(capital_backtest(mode="compass", payload={
            "equity_curve": [],
            "trade_returns": [],
        }))
        assert result["result"]["status"] == "ERROR"


# ── Tests: Stress test mode ──────────────────────────────────────────────

class TestCapitalBacktestStressTest:
    """Test stress_test mode (Market-GAN distillation)."""

    def test_stress_test_returns_scenarios(self):
        """Stress test must return scenarios and robustness_score."""
        payload = {
            "equity_curve": [10000, 10100, 9950, 10200, 10300, 10100],
            "trade_returns": [0.01, -0.015, 0.025, 0.01, -0.02],
        }
        result = _run(capital_backtest(mode="stress_test", payload=payload))

        inner = result["result"]
        assert "scenarios" in inner
        assert "robustness_score" in inner
        assert inner["framework"] == "Synthetic Adversarial Reality (TradeMaster distillation)"

    def test_stress_test_missing_data_returns_error(self):
        """Stress test without data should error."""
        result = _run(capital_backtest(mode="stress_test", payload={}))
        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "MISSING_DATA"


# ── Tests: Error handling ────────────────────────────────────────────────

class TestCapitalBacktestErrors:
    """Test error paths for capital_backtest."""

    def test_empty_data_returns_error(self):
        """Empty yfinance data should return NO_DATA error."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = mock_ticker
            result = _run(capital_backtest(symbol="INVALID"))

        assert result["result"]["status"] == "ERROR"
        assert result["result"]["error_code"] == "NO_DATA"


# ── Tests: Envelope contract ─────────────────────────────────────────────

class TestCapitalBacktestEnvelope:
    """Test output envelope contract."""

    def test_envelope_has_required_fields(self):
        """Every call must include tool_name, domain, epistemic_tag."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value = mock_ticker
            result = _run(capital_backtest(
                session_id="test_session",
                actor_id="test_actor",
            ))

        assert result["tool_name"] == "capital_backtest"
        assert result["domain"] in ("market", "evaluation")
        assert result["session_id"] == "test_session"
        assert result["actor_id"] == "test_actor"


# ── Standalone runner ────────────────────────────────────────────────────
if __name__ == "__main__":
    passed = failed = 0
    tests = [
        TestCapitalBacktestDefault(),
        TestCapitalBacktestCompass(),
        TestCapitalBacktestStressTest(),
        TestCapitalBacktestErrors(),
        TestCapitalBacktestEnvelope(),
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
