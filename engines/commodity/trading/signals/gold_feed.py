"""
Gold Price Feed — XAUUSD real-time via Yahoo Finance.
Free, no API key needed.

Usage:
    from signals.gold_feed import get_gold_price, get_gold_history, get_current_price
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json


# XAUUSD ticker on Yahoo Finance
GOLD_TICKER = "GC=F"  # Gold Futures (most liquid proxy for spot)
GOLD_SPOT_TICKER = "XAUUSD=X"  # Spot XAUUSD (sometimes unreliable)


def get_gold_price() -> Dict:
    """
    Get current gold price with metadata.
    Returns: {price, currency, timestamp, source, change, change_pct}
    """
    try:
        ticker = yf.Ticker(GOLD_TICKER)
        info = ticker.fast_info
        hist = ticker.history(period="2d")

        if hist.empty:
            # Fallback to spot ticker
            ticker = yf.Ticker(GOLD_SPOT_TICKER)
            hist = ticker.history(period="2d")
            if hist.empty:
                return {"error": "Cannot fetch gold price", "source": "yahoo"}

        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev else 0

        return {
            "price": round(current, 2),
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "source": "yahoo_finance",
            "ticker": GOLD_TICKER,
            "change": round(change, 2),
            "change_pct": round(change_pct, 3),
            "previous_close": round(prev, 2),
        }
    except Exception as e:
        return {"error": str(e), "source": "yahoo"}


def get_gold_history(
    period: str = "3mo",
    interval: str = "1h",
) -> Optional[List[Dict]]:
    """
    Get historical gold OHLCV data.
    Args:
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Returns: List of {date, open, high, low, close, volume}
    """
    try:
        ticker = yf.Ticker(GOLD_TICKER)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return None

        data = []
        for idx, row in hist.iterrows():
            data.append({
                "date": idx.isoformat(),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })
        return data
    except Exception as e:
        print(f"Error fetching gold history: {e}")
        return None


def get_gold_candles(timeframe: str = "1h", count: int = 100) -> Optional[List[Dict]]:
    """
    Get recent gold candles for technical analysis.
    Args:
        timeframe: 1h, 4h, 1d
        count: number of candles to return
    Returns: List of OHLCV dicts
    """
    period_map = {
        "1h": ("5d", "1h"),    # Yahoo max 1h = ~7 days
        "4h": ("1mo", "1h"),   # Get 1h and resample to 4h
        "1d": ("6mo", "1d"),
    }

    period, interval = period_map.get(timeframe, ("5d", "1h"))

    data = get_gold_history(period=period, interval=interval)
    if data:
        return data[-count:]
    return None


def get_gold_session_info() -> Dict:
    """
    Get current market session info for gold.
    Gold trades 23h/day (closed 5pm-6pm ET Sunday).
    """
    now = datetime.utcnow()
    hour = now.hour
    day = now.weekday()  # 0=Monday, 6=Sunday

    # Market closed: Sunday 5pm ET (21:00 UTC) to Sunday 6pm ET (22:00 UTC)
    # Simplified: closed Sunday 21:00-22:00 UTC
    if day == 6 and 21 <= hour <= 22:
        session = "CLOSED"
    elif day == 5 and hour >= 21:  # Friday after 9pm UTC
        session = "CLOSED"
    elif day == 6:  # Sunday before 9pm
        session = "CLOSED"
    elif 0 <= hour < 7:  # Asian session
        session = "ASIAN"
    elif 7 <= hour < 15:  # London session
        session = "LONDON"
    elif 13 <= hour < 21:  # NY session (overlap with London 13-15)
        session = "NEW_YORK"
    else:
        session = "OFF_HOURS"

    return {
        "session": session,
        "utc_hour": hour,
        "day": day,
        "is_trading": session != "CLOSED",
        "best_session": session in ["LONDON", "NEW_YORK"],
    }


# Quick test
if __name__ == "__main__":
    print("=== Gold Price Feed Test ===")
    price = get_gold_price()
    print(f"Price: {json.dumps(price, indent=2)}")

    session = get_gold_session_info()
    print(f"Session: {json.dumps(session, indent=2)}")

    history = get_gold_history(period="5d", interval="1h")
    if history:
        print(f"History: {len(history)} candles loaded")
        print(f"Latest: {history[-1]}")
