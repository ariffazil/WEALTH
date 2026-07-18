"""
Data Feed — market data ingestion.
Sources: yfinance (free), MT5 (if configured), or manual OHLCV input.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from ..core.models import OHLCV


def fetch_xauusd_yfinance(period: str = "5d", interval: str = "1h") -> list[OHLCV]:
    """
    Fetch XAUUSD from yfinance.
    Note: yfinance uses GC=F for gold futures.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker("GC=F")
        df = ticker.history(period=period, interval=interval)
        candles = []
        for idx, row in df.iterrows():
            candles.append(OHLCV(
                timestamp=idx.to_pydatetime().replace(tzinfo=timezone.utc),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=float(row["Volume"]),
                timeframe=interval,
            ))
        return candles
    except ImportError:
        return []
    except Exception:
        return []


def fetch_xauusd_from_file(path: str) -> list[OHLCV]:
    """Load OHLCV from JSON file."""
    with open(path) as f:
        data = json.load(f)
    candles = []
    for d in data:
        candles.append(OHLCV(
            timestamp=datetime.fromisoformat(d["timestamp"]),
            open=d["open"],
            high=d["high"],
            low=d["low"],
            close=d["close"],
            volume=d.get("volume", 0),
            timeframe=d.get("timeframe", "H1"),
        ))
    return candles


def fetch_xauusd_from_prices(prices: list[float], base_time: Optional[datetime] = None) -> list[OHLCV]:
    """
    Build synthetic OHLCV from a list of close prices.
    Useful for backtesting or when only close data available.
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc) - timedelta(hours=len(prices))

    candles = []
    for i, close in enumerate(prices):
        prev = prices[i - 1] if i > 0 else close
        spread = abs(close - prev) * 0.3 + 1.0
        o = prev
        h = max(o, close) + spread
        l = min(o, close) - spread * 0.7
        candles.append(OHLCV(
            timestamp=base_time + timedelta(hours=i),
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(close, 2),
            volume=500,
            timeframe="H1",
        ))
    return candles


def save_candles(candles: list[OHLCV], path: str) -> None:
    """Save candles to JSON for caching."""
    data = []
    for c in candles:
        data.append({
            "timestamp": c.timestamp.isoformat(),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
            "timeframe": c.timeframe,
        })
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
