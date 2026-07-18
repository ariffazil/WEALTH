"""
Signal Engine — generates trading signals from scanner output.
Multi-factor confluence scoring with epistemic honesty.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..core.config import get_config, TradingConfig
from ..core.models import (
    OHLCV, Indicators, Signal, SignalStrength, Direction,
    ConfluenceFactor, EpistemicLabel, Verdict,
)
from .scanner import compute_indicators, detect_candle_pattern


def _score_ema_trend(ind: Indicators, price: float) -> ConfluenceFactor:
    """Score EMA alignment trend."""
    if ind.ema_20 > ind.ema_50 > ind.ema_200:
        return ConfluenceFactor(
            name="EMA_BULL_ALIGN",
            direction=Direction.BUY,
            weight=0.25,
            confidence=0.7 if price > ind.ema_20 else 0.4,
            detail=f"EMA20>{ind.ema_20:.2f} > EMA50>{ind.ema_50:.2f} > EMA200>{ind.ema_200:.2f}",
        )
    elif ind.ema_20 < ind.ema_50 < ind.ema_200:
        return ConfluenceFactor(
            name="EMA_BEAR_ALIGN",
            direction=Direction.SELL,
            weight=0.25,
            confidence=0.7 if price < ind.ema_20 else 0.4,
            detail=f"EMA20<{ind.ema_20:.2f} < EMA50<{ind.ema_50:.2f} < EMA200<{ind.ema_200:.2f}",
        )
    return ConfluenceFactor(
        name="EMA_NEUTRAL",
        direction=Direction.FLAT,
        weight=0.1,
        confidence=0.3,
        detail="No clear EMA alignment",
    )


def _score_rsi(ind: Indicators, cfg: TradingConfig) -> ConfluenceFactor:
    """Score RSI conditions."""
    rsi_val = ind.rsi_14
    if rsi_val <= cfg.rsi_oversold:
        return ConfluenceFactor(
            name="RSI_OVERSOLD",
            direction=Direction.BUY,
            weight=0.20,
            confidence=min(0.8, (cfg.rsi_oversold - rsi_val) / 20 + 0.5),
            detail=f"RSI={rsi_val:.1f} < {cfg.rsi_oversold}",
        )
    elif rsi_val >= cfg.rsi_overbought:
        return ConfluenceFactor(
            name="RSI_OVERBOUGHT",
            direction=Direction.SELL,
            weight=0.20,
            confidence=min(0.8, (rsi_val - cfg.rsi_overbought) / 20 + 0.5),
            detail=f"RSI={rsi_val:.1f} > {cfg.rsi_overbought}",
        )
    elif rsi_val < 40:
        return ConfluenceFactor(
            name="RSI_BELOW_MID",
            direction=Direction.BUY,
            weight=0.10,
            confidence=0.4,
            detail=f"RSI={rsi_val:.1f} below midpoint",
        )
    elif rsi_val > 60:
        return ConfluenceFactor(
            name="RSI_ABOVE_MID",
            direction=Direction.SELL,
            weight=0.10,
            confidence=0.4,
            detail=f"RSI={rsi_val:.1f} above midpoint",
        )
    return ConfluenceFactor(
        name="RSI_NEUTRAL",
        direction=Direction.FLAT,
        weight=0.05,
        confidence=0.3,
        detail=f"RSI={rsi_val:.1f} neutral",
    )


def _score_macd(ind: Indicators) -> ConfluenceFactor:
    """Score MACD histogram direction."""
    hist = ind.macd_histogram
    if hist > 0 and ind.macd_line > ind.macd_signal:
        return ConfluenceFactor(
            name="MACD_BULL",
            direction=Direction.BUY,
            weight=0.15,
            confidence=min(0.7, abs(hist) / 5 + 0.4),
            detail=f"MACD hist={hist:.4f} positive crossover",
        )
    elif hist < 0 and ind.macd_line < ind.macd_signal:
        return ConfluenceFactor(
            name="MACD_BEAR",
            direction=Direction.SELL,
            weight=0.15,
            confidence=min(0.7, abs(hist) / 5 + 0.4),
            detail=f"MACD hist={hist:.4f} negative crossover",
        )
    return ConfluenceFactor(
        name="MACD_NEUTRAL",
        direction=Direction.FLAT,
        weight=0.05,
        confidence=0.3,
        detail=f"MACD hist={hist:.4f}",
    )


def _score_sr_proximity(ind: Indicators, price: float, atr_val: float) -> ConfluenceFactor:
    """Score proximity to support/resistance."""
    if ind.support <= 0:
        return ConfluenceFactor(name="SR_NA", direction=Direction.FLAT, weight=0, confidence=0)

    dist_to_support = abs(price - ind.support)
    dist_to_resistance = abs(ind.resistance - price)

    # Near support = bullish bounce potential
    if dist_to_support < atr_val * 0.5:
        return ConfluenceFactor(
            name="NEAR_SUPPORT",
            direction=Direction.BUY,
            weight=0.20,
            confidence=min(0.7, (1 - dist_to_support / atr_val) + 0.3),
            detail=f"Price {price:.2f} near support {ind.support:.2f} (dist={dist_to_support:.2f})",
        )
    # Near resistance = bearish rejection potential
    elif dist_to_resistance < atr_val * 0.5:
        return ConfluenceFactor(
            name="NEAR_RESISTANCE",
            direction=Direction.SELL,
            weight=0.20,
            confidence=min(0.7, (1 - dist_to_resistance / atr_val) + 0.3),
            detail=f"Price {price:.2f} near resistance {ind.resistance:.2f} (dist={dist_to_resistance:.2f})",
        )
    return ConfluenceFactor(
        name="SR_MID_RANGE",
        direction=Direction.FLAT,
        weight=0.05,
        confidence=0.3,
        detail=f"Between S={ind.support:.2f} and R={ind.resistance:.2f}",
    )


def _score_candle_pattern(candles: list[OHLCV]) -> ConfluenceFactor:
    """Score candlestick pattern."""
    pattern = detect_candle_pattern(candles)
    if pattern is None:
        return ConfluenceFactor(name="NO_PATTERN", direction=Direction.FLAT, weight=0.05, confidence=0.2)

    bull_patterns = {"HAMMER", "BULLISH_ENGULFING", "PIN_BAR_BULL", "DOJI"}
    bear_patterns = {"SHOOTING_STAR", "BEARISH_ENGULFING", "HANGING_MAN"}

    if pattern in bull_patterns:
        return ConfluenceFactor(
            name=f"CANDLE_{pattern}",
            direction=Direction.BUY,
            weight=0.15,
            confidence=0.6,
            detail=f"{pattern} detected",
        )
    elif pattern in bear_patterns:
        return ConfluenceFactor(
            name=f"CANDLE_{pattern}",
            direction=Direction.SELL,
            weight=0.15,
            confidence=0.6,
            detail=f"{pattern} detected",
        )
    return ConfluenceFactor(name="CANDLE_NEUTRAL", direction=Direction.FLAT, weight=0.05, confidence=0.3)


def _compute_stops(entry: float, direction: Direction, atr_val: float, ind: Indicators, cfg: TradingConfig) -> tuple[float, float, float]:
    """Compute SL, TP1, TP2 from ATR and structure."""
    if direction == Direction.BUY:
        sl = round(entry - atr_val * 1.5, 2)
        # SL below nearest support if available
        if ind.support > 0 and ind.support < entry:
            sl = round(min(sl, ind.support - atr_val * 0.3), 2)
        risk = entry - sl
        tp1 = round(entry + risk * cfg.min_rr_ratio, 2)
        tp2 = round(entry + risk * cfg.min_rr_ratio * 1.5, 2)
    else:  # SELL
        sl = round(entry + atr_val * 1.5, 2)
        if ind.resistance > 0 and ind.resistance > entry:
            sl = round(max(sl, ind.resistance + atr_val * 0.3), 2)
        risk = sl - entry
        tp1 = round(entry - risk * cfg.min_rr_ratio, 2)
        tp2 = round(entry - risk * cfg.min_rr_ratio * 1.5, 2)
    return sl, tp1, tp2


def generate_signal(candles: list[OHLCV], cfg: Optional[TradingConfig] = None) -> Signal:
    """
    Generate a trading signal from OHLCV data.
    This is the main entry point for the signal engine.
    """
    if cfg is None:
        cfg = get_config()

    if len(candles) < cfg.lookback_bars:
        return Signal(
            direction=Direction.FLAT,
            strength=SignalStrength.NONE,
            confidence=0.0,
            judge_reason=f"Insufficient data: {len(candles)} bars < {cfg.lookback_bars} required",
        )

    # Compute indicators
    ind = compute_indicators(candles, cfg)
    price = candles[-1].close
    atr_val = ind.atr_14 if ind.atr_14 > 0 else 10.0  # fallback

    # Score all confluence factors
    factors = [
        _score_ema_trend(ind, price),
        _score_rsi(ind, cfg),
        _score_macd(ind),
        _score_sr_proximity(ind, price, atr_val),
        _score_candle_pattern(candles),
    ]

    # Aggregate by direction
    buy_score = sum(f.weight * f.confidence for f in factors if f.direction == Direction.BUY)
    sell_score = sum(f.weight * f.confidence for f in factors if f.direction == Direction.SELL)
    total_weight = sum(f.weight for f in factors)

    # Determine direction
    if buy_score > sell_score and buy_score > cfg.min_confluence_score * total_weight:
        direction = Direction.BUY
        score = buy_score
        active_factors = [f for f in factors if f.direction == Direction.BUY]
    elif sell_score > buy_score and sell_score > cfg.min_confluence_score * total_weight:
        direction = Direction.SELL
        score = sell_score
        active_factors = [f for f in factors if f.direction == Direction.SELL]
    else:
        return Signal(
            direction=Direction.FLAT,
            strength=SignalStrength.NONE,
            confidence=max(buy_score, sell_score),
            indicators=ind,
            confluence_factors=factors,
            confluence_score=max(buy_score, sell_score),
            verdict=Verdict.SABAR,
            judge_reason=f"No clear direction: BUY={buy_score:.3f} SELL={sell_score:.3f}",
        )

    # Normalize confidence
    confidence = min(0.90, score / total_weight)  # cap at 0.90 per F7

    # Signal strength from factor count
    n_factors = len(active_factors)
    if n_factors >= 4:
        strength = SignalStrength.STRONG
    elif n_factors >= 3:
        strength = SignalStrength.MODERATE
    else:
        strength = SignalStrength.WEAK

    # Compute stops
    sl, tp1, tp2 = _compute_stops(price, direction, atr_val, ind, cfg)

    # RR ratio
    risk = abs(price - sl)
    reward = abs(tp1 - price)
    rr = round(reward / risk, 1) if risk > 0 else 0.0

    return Signal(
        timestamp=candles[-1].timestamp,
        symbol=cfg.symbol,
        direction=direction,
        strength=strength,
        confidence=round(confidence, 3),
        entry_price=price,
        stop_loss=sl,
        take_profit_1=tp1,
        take_profit_2=tp2,
        rr_ratio=rr,
        confluence_factors=active_factors,
        confluence_score=round(score, 3),
        indicators=ind,
        verdict=Verdict.HOLD,  # governance decides final verdict
    )
