"""
Technical Analysis Engine — XAUUSD.
EMA 20/50, Support/Resistance, RSI, Candle Patterns.

Usage:
    from signals.technical import analyze_gold, get_ema, get_support_resistance, get_rsi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def calc_ema(closes: List[float], period: int) -> List[float]:
    """Calculate EMA for given period."""
    if len(closes) < period:
        return []

    ema = [sum(closes[:period]) / period]  # SMA seed
    multiplier = 2 / (period + 1)

    for price in closes[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])

    return ema


def calc_sma(closes: List[float], period: int) -> List[float]:
    """Calculate SMA for given period."""
    if len(closes) < period:
        return []

    sma = []
    for i in range(period - 1, len(closes)):
        sma.append(sum(closes[i - period + 1: i + 1]) / period)
    return sma


def calc_rsi(closes: List[float], period: int = 14) -> List[float]:
    """Calculate RSI for given period."""
    if len(closes) < period + 1:
        return []

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))

    return rsi_values


def get_support_resistance(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    lookback: int = 50,
    sensitivity: int = 3,
) -> Dict:
    """
    Detect support and resistance levels using pivot points.
    Args:
        highs, lows, closes: price arrays
        lookback: how many candles to analyze
        sensitivity: min touches to confirm level
    Returns: {supports: [{level, strength, touches}], resistances: [...]}
    """
    if len(highs) < lookback:
        lookback = len(highs)

    highs = highs[-lookback:]
    lows = lows[-lookback:]
    closes = closes[-lookback:]

    # Find pivot highs and lows
    pivot_highs = []
    pivot_lows = []

    for i in range(2, len(highs) - 2):
        # Pivot high: higher than 2 neighbors on each side
        if (
            highs[i] > highs[i - 1]
            and highs[i] > highs[i - 2]
            and highs[i] > highs[i + 1]
            and highs[i] > highs[i + 2]
        ):
            pivot_highs.append(highs[i])

        # Pivot low: lower than 2 neighbors on each side
        if (
            lows[i] < lows[i - 1]
            and lows[i] < lows[i - 2]
            and lows[i] < lows[i + 1]
            and lows[i] < lows[i + 2]
        ):
            pivot_lows.append(lows[i])

    # Cluster levels (within 0.3% of each other)
    def cluster_levels(levels: List[float], threshold_pct: float = 0.3) -> List[Dict]:
        if not levels:
            return []

        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if (level - current_cluster[0]) / current_cluster[0] * 100 < threshold_pct:
                current_cluster.append(level)
            else:
                clusters.append({
                    "level": round(sum(current_cluster) / len(current_cluster), 2),
                    "touches": len(current_cluster),
                    "strength": min(len(current_cluster) / 5.0, 1.0),
                })
                current_cluster = [level]

        # Last cluster
        clusters.append({
            "level": round(sum(current_cluster) / len(current_cluster), 2),
            "touches": len(current_cluster),
            "strength": min(len(current_cluster) / 5.0, 1.0),
        })

        return [c for c in clusters if c["touches"] >= sensitivity]

    supports = cluster_levels(pivot_lows)
    resistances = cluster_levels(pivot_highs)

    return {
        "supports": sorted(supports, key=lambda x: x["level"], reverse=True),
        "resistances": sorted(resistances, key=lambda x: x["level"]),
    }


def detect_candle_patterns(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
) -> List[Dict]:
    """
    Detect candlestick patterns on recent candles.
    Returns: [{pattern, direction, confidence, description}]
    """
    patterns = []
    if len(opens) < 3:
        return patterns

    # Use last 3 candles for pattern detection
    o1, o2, o3 = opens[-3], opens[-2], opens[-1]
    h1, h2, h3 = highs[-3], highs[-2], highs[-1]
    l1, l2, l3 = lows[-3], lows[-2], lows[-1]
    c1, c2, c3 = closes[-3], closes[-2], closes[-1]

    body1 = abs(c1 - o1)
    body2 = abs(c2 - o2)
    body3 = abs(c3 - o3)
    range1 = h1 - l1
    range2 = h2 - l2
    range3 = h3 - l3

    # === SINGLE CANDLE PATTERNS ===

    # Doji (small body, long wicks)
    if range3 > 0 and body3 / range3 < 0.1:
        patterns.append({
            "pattern": "doji",
            "direction": "neutral",
            "confidence": 0.6,
            "description": "Indecision — wait for confirmation",
        })

    # Hammer (small body at top, long lower wick) — bullish
    if range3 > 0:
        lower_wick = min(o3, c3) - l3
        upper_wick = h3 - max(o3, c3)
        if lower_wick > 2 * body3 and upper_wick < body3 * 0.5:
            patterns.append({
                "pattern": "hammer",
                "direction": "bullish",
                "confidence": 0.7,
                "description": "Potential reversal — buyers stepping in",
            })

    # Shooting Star (small body at bottom, long upper wick) — bearish
    if range3 > 0:
        lower_wick = min(o3, c3) - l3
        upper_wick = h3 - max(o3, c3)
        if upper_wick > 2 * body3 and lower_wick < body3 * 0.5:
            patterns.append({
                "pattern": "shooting_star",
                "direction": "bearish",
                "confidence": 0.7,
                "description": "Potential reversal — sellers stepping in",
            })

    # === TWO CANDLE PATTERNS ===

    # Bullish Engulfing (bearish candle + larger bullish candle)
    if c2 < o2 and c3 > o3 and o3 <= c2 and c3 >= o2 and body3 > body2:
        patterns.append({
            "pattern": "bullish_engulfing",
            "direction": "bullish",
            "confidence": 0.8,
            "description": "Strong reversal — buyers overwhelmed sellers",
        })

    # Bearish Engulfing (bullish candle + larger bearish candle)
    if c2 > o2 and c3 < o3 and o3 >= c2 and c3 <= o2 and body3 > body2:
        patterns.append({
            "pattern": "bearish_engulfing",
            "direction": "bearish",
            "confidence": 0.8,
            "description": "Strong reversal — sellers overwhelmed buyers",
        })

    # === THREE CANDLE PATTERNS ===

    # Morning Star (bearish + doji/small + bullish)
    if c1 < o1 and body2 < body1 * 0.3 and c3 > o3 and c3 > (o1 + c1) / 2:
        patterns.append({
            "pattern": "morning_star",
            "direction": "bullish",
            "confidence": 0.85,
            "description": "Strong 3-candle reversal — bullish",
        })

    # Evening Star (bullish + doji/small + bearish)
    if c1 > o1 and body2 < body1 * 0.3 and c3 < o3 and c3 < (o1 + c1) / 2:
        patterns.append({
            "pattern": "evening_star",
            "direction": "bearish",
            "confidence": 0.85,
            "description": "Strong 3-candle reversal — bearish",
        })

    return patterns


def analyze_gold(
    candles: List[Dict],
    ema_fast: int = 20,
    ema_slow: int = 50,
    rsi_period: int = 14,
) -> Dict:
    """
    Full technical analysis on gold candles.
    Args:
        candles: list of {date, open, high, low, close, volume}
        ema_fast: fast EMA period (default 20)
        ema_slow: slow EMA period (default 50)
        rsi_period: RSI period (default 14)
    Returns: comprehensive analysis dict
    """
    if not candles or len(candles) < ema_slow + 5:
        return {"error": "Not enough candles for analysis", "required": ema_slow + 5}

    opens = [c["open"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    # Current price
    current_price = closes[-1]

    # EMA
    ema20 = calc_ema(closes, ema_fast)
    ema50 = calc_ema(closes, ema_slow)

    ema20_current = ema20[-1] if ema20 else None
    ema50_current = ema50[-1] if ema50 else None

    # EMA crossover detection
    ema_cross = "none"
    if len(ema20) >= 2 and len(ema50) >= 2:
        # Align arrays (ema50 is shorter)
        offset = len(ema20) - len(ema50)
        if offset >= 0:
            ema20_aligned = ema20[offset:]
            if len(ema20_aligned) >= 2 and len(ema50) >= 2:
                prev_diff = ema20_aligned[-2] - ema50[-2]
                curr_diff = ema20_aligned[-1] - ema50[-1]
                if prev_diff < 0 and curr_diff > 0:
                    ema_cross = "golden_cross"  # Bullish
                elif prev_diff > 0 and curr_diff < 0:
                    ema_cross = "death_cross"  # Bearish

    # EMA trend
    ema_trend = "neutral"
    if ema20_current and ema50_current:
        if current_price > ema20_current > ema50_current:
            ema_trend = "bullish"
        elif current_price < ema20_current < ema50_current:
            ema_trend = "bearish"
        elif current_price > ema20_current:
            ema_trend = "mild_bullish"
        elif current_price < ema20_current:
            ema_trend = "mild_bearish"

    # RSI
    rsi_values = calc_rsi(closes, rsi_period)
    rsi_current = rsi_values[-1] if rsi_values else None

    rsi_signal = "neutral"
    if rsi_current:
        if rsi_current < 30:
            rsi_signal = "oversold"
        elif rsi_current > 70:
            rsi_signal = "overbought"
        elif rsi_current < 40:
            rsi_signal = "weak"
        elif rsi_current > 60:
            rsi_signal = "strong"

    # RSI divergence (simple: compare price lows/highs with RSI lows/highs)
    rsi_divergence = "none"
    if len(rsi_values) >= 20 and len(closes) >= 20:
        # Check last 20 candles for divergence
        price_lows = lows[-20:]
        rsi_lows = rsi_values[-20:]
        price_highs = highs[-20:]
        rsi_highs = rsi_values[-20:]

        # Bullish divergence: price makes lower low, RSI makes higher low
        if (
            price_lows[-1] < price_lows[-10]
            and rsi_lows[-1] > rsi_lows[-10]
        ):
            rsi_divergence = "bullish"
        # Bearish divergence: price makes higher high, RSI makes lower high
        elif (
            price_highs[-1] > price_highs[-10]
            and rsi_highs[-1] < rsi_highs[-10]
        ):
            rsi_divergence = "bearish"

    # Support/Resistance
    sr = get_support_resistance(highs, lows, closes)

    # Find nearest support and resistance
    nearest_support = None
    nearest_resistance = None

    for s in sr["supports"]:
        if s["level"] < current_price:
            if nearest_support is None or s["level"] > nearest_support["level"]:
                nearest_support = s

    for r in sr["resistances"]:
        if r["level"] > current_price:
            if nearest_resistance is None or r["level"] < nearest_resistance["level"]:
                nearest_resistance = r

    # Candle patterns
    candle_patterns = detect_candle_patterns(opens, highs, lows, closes)

    # === CONFLUENCE SCORE ===
    # Count how many signals agree on direction
    bullish_signals = 0
    bearish_signals = 0

    # EMA trend
    if ema_trend in ["bullish", "mild_bullish"]:
        bullish_signals += 1
    elif ema_trend in ["bearish", "mild_bearish"]:
        bearish_signals += 1

    # EMA cross
    if ema_cross == "golden_cross":
        bullish_signals += 2
    elif ema_cross == "death_cross":
        bearish_signals += 2

    # RSI
    if rsi_signal == "oversold":
        bullish_signals += 1
    elif rsi_signal == "overbought":
        bearish_signals += 1

    # RSI divergence
    if rsi_divergence == "bullish":
        bullish_signals += 2
    elif rsi_divergence == "bearish":
        bearish_signals += 2

    # Candle patterns
    for p in candle_patterns:
        if p["direction"] == "bullish":
            bullish_signals += 1
        elif p["direction"] == "bearish":
            bearish_signals += 1

    # S/R proximity (within 0.5% of level)
    sr_bonus = 0
    if nearest_support:
        dist = (current_price - nearest_support["level"]) / current_price * 100
        if dist < 0.5:
            bullish_signals += 1
            sr_bonus = 1
    if nearest_resistance:
        dist = (nearest_resistance["level"] - current_price) / current_price * 100
        if dist < 0.5:
            bearish_signals += 1
            sr_bonus = 1

    total_signals = bullish_signals + bearish_signals
    if total_signals > 0:
        confluence = max(bullish_signals, bearish_signals) / total_signals
    else:
        confluence = 0

    # Direction
    if bullish_signals > bearish_signals + 1:
        direction = "bullish"
    elif bearish_signals > bullish_signals + 1:
        direction = "bearish"
    else:
        direction = "neutral"

    return {
        "timestamp": datetime.now().isoformat(),
        "price": current_price,
        "ema": {
            "fast": round(ema20_current, 2) if ema20_current else None,
            "slow": round(ema50_current, 2) if ema50_current else None,
            "trend": ema_trend,
            "crossover": ema_cross,
        },
        "rsi": {
            "value": round(rsi_current, 2) if rsi_current else None,
            "signal": rsi_signal,
            "divergence": rsi_divergence,
        },
        "support_resistance": {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "all_supports": sr["supports"],
            "all_resistances": sr["resistances"],
        },
        "candle_patterns": candle_patterns,
        "confluence": {
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "score": round(confluence, 2),
            "direction": direction,
            "total_signals": total_signals,
        },
    }


# Quick test
if __name__ == "__main__":
    from signals.gold_feed import get_gold_candles

    print("=== Technical Analysis Test ===")
    candles = get_gold_candles("1h", 100)
    if candles:
        analysis = analyze_gold(candles)
        import json
        print(json.dumps(analysis, indent=2, default=str))
    else:
        print("No candle data available")
