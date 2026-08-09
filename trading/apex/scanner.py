"""
Technical Analysis Scanner — pure computation, no I/O.
Computes indicators from OHLCV data. Epistemic label: DER (derived).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from ..core.models import OHLCV, Indicators, Direction


def ema(data: list[float], period: int) -> list[float]:
    """Exponential Moving Average."""
    if len(data) < period:
        return []
    k = 2 / (period + 1)
    result = [sum(data[:period]) / period]
    for val in data[period:]:
        result.append(val * k + result[-1] * (1 - k))
    return result


def sma(data: list[float], period: int) -> list[float]:
    """Simple Moving Average."""
    if len(data) < period:
        return []
    return [sum(data[i : i + period]) / period for i in range(len(data) - period + 1)]


def rsi(closes: list[float], period: int = 14) -> list[float]:
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return []
    deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    result = []
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))
    return result


def macd(
    closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[list[float], list[float], list[float]]:
    """MACD line, signal line, histogram."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    if not ema_fast or not ema_slow:
        return [], [], []
    # Align: ema_fast is longer
    offset = len(ema_fast) - len(ema_slow)
    macd_line = [ema_fast[offset + i] - ema_slow[i] for i in range(len(ema_slow))]
    signal_line = ema(macd_line, signal)
    if not signal_line:
        return macd_line, [], []
    offset2 = len(macd_line) - len(signal_line)
    histogram = [
        macd_line[offset2 + i] - signal_line[i] for i in range(len(signal_line))
    ]
    return macd_line, signal_line, histogram


def atr(candles: list[OHLCV], period: int = 14) -> list[float]:
    """Average True Range."""
    if len(candles) < period + 1:
        return []
    trs = []
    for i in range(1, len(candles)):
        high = candles[i].high
        low = candles[i].low
        prev_close = candles[i - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    # RMA (Wilder's smoothing)
    if len(trs) < period:
        return []
    result = [sum(trs[:period]) / period]
    for i in range(period, len(trs)):
        result.append((result[-1] * (period - 1) + trs[i]) / period)
    return result


def find_support_resistance(
    candles: list[OHLCV], lookback: int = 50
) -> tuple[float, float]:
    """Simple pivot-based S/R detection."""
    if len(candles) < lookback:
        lookback = len(candles)
    if lookback < 5:
        return 0.0, 0.0

    recent = candles[-lookback:]
    highs = [c.high for c in recent]
    lows = [c.low for c in recent]

    # Find local pivots
    pivot_highs = []
    pivot_lows = []
    for i in range(2, len(recent) - 2):
        if (
            recent[i].high > recent[i - 1].high
            and recent[i].high > recent[i - 2].high
            and recent[i].high > recent[i + 1].high
            and recent[i].high > recent[i + 2].high
        ):
            pivot_highs.append(recent[i].high)
        if (
            recent[i].low < recent[i - 1].low
            and recent[i].low < recent[i - 2].low
            and recent[i].low < recent[i + 1].low
            and recent[i].low < recent[i + 2].low
        ):
            pivot_lows.append(recent[i].low)

    resistance = max(pivot_highs) if pivot_highs else max(highs)
    support = min(pivot_lows) if pivot_lows else min(lows)
    return support, resistance


def detect_trend(
    ema_20: float, ema_50: float, ema_200: float, price: float
) -> Direction:
    """Trend detection from EMA alignment."""
    if ema_20 > ema_50 > ema_200 and price > ema_20:
        return Direction.BUY
    elif ema_20 < ema_50 < ema_200 and price < ema_20:
        return Direction.SELL
    return Direction.FLAT


def detect_candle_pattern(candles: list[OHLCV]) -> Optional[str]:
    """Detect common candlestick patterns. Returns pattern name or None."""
    if len(candles) < 3:
        return None

    c = candles[-1]
    p = candles[-2]

    # Doji (small body, long wicks)
    if c.body_size < c.range_size * 0.1 and c.range_size > 0:
        return "DOJI"

    # Hammer (small body at top, long lower wick)
    if c.lower_wick > c.body_size * 2 and c.upper_wick < c.body_size * 0.5:
        return "HAMMER" if c.is_bullish else "HANGING_MAN"

    # Engulfing
    if c.is_bullish and not p.is_bullish and c.open <= p.close and c.close >= p.open:
        return "BULLISH_ENGULFING"
    if not c.is_bullish and p.is_bullish and c.open >= p.close and c.close <= p.open:
        return "BEARISH_ENGULFING"

    # Pin bar
    if c.upper_wick > c.body_size * 2.5 and c.lower_wick < c.body_size:
        return "SHOOTING_STAR"
    if c.lower_wick > c.body_size * 2.5 and c.upper_wick < c.body_size:
        return "PIN_BAR_BULL"

    return None


def bollinger_bands(
    closes: list[float], period: int = 20, num_std: float = 2.0
) -> tuple[list[float], list[float], list[float]]:
    """Bollinger Bands: middle (SMA), upper, lower. FORGED 2026-08-09."""
    if len(closes) < period:
        return [], [], []
    sma_vals = sma(closes, period)
    rolling_std = []
    for i in range(len(closes) - period + 1):
        rolling_std.append(
            (sum((x - sma_vals[i]) ** 2 for x in closes[i : i + period]) / period)
            ** 0.5
        )
    upper = [sma_vals[i] + num_std * rolling_std[i] for i in range(len(sma_vals))]
    lower = [sma_vals[i] - num_std * rolling_std[i] for i in range(len(sma_vals))]
    return sma_vals, upper, lower


def parabolic_sar(
    candles: list[OHLCV],
    af_init: float = 0.02,
    af_max: float = 0.20,
    af_step: float = 0.02,
) -> tuple[list[float], list[bool]]:
    """Parabolic SAR. Returns (psar_values, trend_up). FORGED 2026-08-09."""
    n = len(candles)
    if n < 2:
        return [], []
    psar = [0.0] * n
    trend_up = [True] * n
    trend_up[0] = True
    ep = float(candles[0].high)
    af = af_init
    psar[0] = float(candles[0].low)

    for i in range(1, n):
        psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
        if trend_up[i - 1]:
            psar[i] = min(
                psar[i], float(candles[i - 1].low), float(candles[max(0, i - 2)].low)
            )
            if float(candles[i].high) > ep:
                ep = float(candles[i].high)
                af = min(af + af_step, af_max)
            if float(candles[i].low) < psar[i]:
                trend_up[i] = False
                psar[i] = ep
                ep = float(candles[i].low)
                af = af_init
            else:
                trend_up[i] = True
        else:
            psar[i] = max(
                psar[i], float(candles[i - 1].high), float(candles[max(0, i - 2)].high)
            )
            if float(candles[i].low) < ep:
                ep = float(candles[i].low)
                af = min(af + af_step, af_max)
            if float(candles[i].high) > psar[i]:
                trend_up[i] = True
                psar[i] = ep
                ep = float(candles[i].high)
                af = af_init
            else:
                trend_up[i] = False

    return psar, trend_up


def compute_indicators(candles: list[OHLCV], cfg) -> Indicators:
    """Compute all indicators from candle data. Returns latest snapshot."""
    closes = [c.close for c in candles]
    now = candles[-1].timestamp if candles else datetime.now(timezone.utc)

    ema_20_vals = ema(closes, cfg.ema_fast)
    ema_50_vals = ema(closes, cfg.ema_mid)
    ema_200_vals = ema(closes, cfg.ema_slow)
    rsi_vals = rsi(closes, cfg.rsi_period)
    macd_l, macd_s, macd_h = macd(closes, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal)
    atr_vals = atr(candles, cfg.atr_period)
    support, resistance = find_support_resistance(candles, cfg.sr_lookback)
    bb_mid, bb_upper, bb_lower = bollinger_bands(
        closes, cfg.bb_period if hasattr(cfg, "bb_period") else 20
    )
    psar_vals, psar_trend = parabolic_sar(candles)

    e20 = ema_20_vals[-1] if ema_20_vals else 0.0
    e50 = ema_50_vals[-1] if ema_50_vals else 0.0
    e200 = ema_200_vals[-1] if ema_200_vals else 0.0
    price = closes[-1] if closes else 0.0

    return Indicators(
        timestamp=now,
        ema_20=round(e20, 2),
        ema_50=round(e50, 2),
        ema_200=round(e200, 2),
        rsi_14=round(rsi_vals[-1], 1) if rsi_vals else 50.0,
        macd_line=round(macd_l[-1], 4) if macd_l else 0.0,
        macd_signal=round(macd_s[-1], 4) if macd_s else 0.0,
        macd_histogram=round(macd_h[-1], 4) if macd_h else 0.0,
        atr_14=round(atr_vals[-1], 2) if atr_vals else 0.0,
        support=round(support, 2),
        resistance=round(resistance, 2),
        bb_upper=round(bb_upper[-1], 2) if bb_upper else 0.0,
        bb_mid=round(bb_mid[-1], 2) if bb_mid else 0.0,
        bb_lower=round(bb_lower[-1], 2) if bb_lower else 0.0,
        psar=round(psar_vals[-1], 2) if psar_vals else 0.0,
        psar_trend="BULL"
        if (psar_trend and psar_trend[-1])
        else "BEAR"
        if psar_trend
        else "NONE",
        pivot=round((support + resistance) / 2, 2) if support and resistance else 0.0,
        trend=detect_trend(e20, e50, e200, price),
    )
