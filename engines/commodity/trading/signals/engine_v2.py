"""
Signal Engine v2 — Simple truth.
3 patterns. Buy low, sell high. Risk/reward.

This replaces the old multi-factor engine with something that actually works.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from ..core.config import get_config, TradingConfig
from ..core.models import (
    OHLCV, Signal, SignalStrength, Direction,
    ConfluenceFactor, EpistemicLabel, Verdict,
)
from .scanner import ema, rsi as rsi_calc, atr as atr_calc, compute_indicators
from .regime import Regime, MarketState, compute_market_state


def _is_near_zone(price: float, zone_price: float, atr_val: float, tolerance: float = 1.0) -> bool:
    """Is price within tolerance*ATR of the zone?"""
    return abs(price - zone_price) <= atr_val * tolerance


def _has_confirmation(candles: list[OHLCV], direction: Direction, lookback: int = 3) -> bool:
    """
    Check for confirmation candle.
    BUY: bullish candle or rejection of low
    SELL: bearish candle or rejection of high
    """
    if len(candles) < lookback:
        return False

    recent = candles[-lookback:]

    if direction == Direction.BUY:
        # Last candle should be bullish (close > open) or show buying pressure
        last = recent[-1]
        if last.is_bullish:
            return True
        # Or: long lower wick (buyers stepping in)
        if last.lower_wick > last.body_size * 1.5:
            return True
        # Or: higher low pattern
        if len(recent) >= 2 and recent[-1].low > recent[-2].low:
            return True
        return False

    elif direction == Direction.SELL:
        last = recent[-1]
        if not last.is_bullish:
            return True
        if last.upper_wick > last.body_size * 1.5:
            return True
        if len(recent) >= 2 and recent[-1].high < recent[-2].high:
            return True
        return False

    return False


def generate_signal_v2(candles: list[OHLCV], cfg: Optional[TradingConfig] = None) -> Signal:
    """
    Generate signal based on the 3-pattern truth.

    Logic:
    1. What regime are we in? (UPTREND / DOWNTREND / SIDEWAYS)
    2. Where are the zones? (buy_zone / sell_zone)
    3. Is price near a zone? (within 1 ATR)
    4. Is there confirmation? (candle pattern)
    5. What's the risk/reward? (must be ≥ 1:2)
    """
    if cfg is None:
        cfg = get_config()

    if len(candles) < 200:
        return Signal(
            direction=Direction.FLAT,
            strength=SignalStrength.NONE,
            confidence=0.0,
            verdict=Verdict.SABAR,
            judge_reason=f"Need 200+ candles for EMA200, got {len(candles)}",
        )

    # Compute indicators
    ind = compute_indicators(candles, cfg)
    closes = [c.close for c in candles]
    atr_val = ind.atr_14 if ind.atr_14 > 0 else 10.0

    # Get market state
    state = compute_market_state(
        candles, ind.ema_20, ind.ema_50, ind.ema_200, ind.rsi_14
    )

    # No clear regime with low confidence = wait
    if state.regime_confidence < 0.5:
        return Signal(
            direction=Direction.FLAT,
            strength=SignalStrength.NONE,
            confidence=state.regime_confidence,
            verdict=Verdict.SABAR,
            judge_reason=f"Regime unclear (conf={state.regime_confidence:.2f}) — SABAR",
            indicators=ind,
        )

    price = state.price
    factors = []

    # ── UPTREND: Buy the dips ──
    if state.regime == Regime.UPTREND and state.buy_zone:
        zone = state.buy_zone
        if _is_near_zone(price, zone.price, atr_val, tolerance=1.2):
            if _has_confirmation(candles, Direction.BUY):
                # SL just below the support zone
                sl = round(zone.price - atr_val * 1.0, 2)
                risk = price - sl
                if risk > 0:
                    tp1 = round(price + risk * 2, 2)  # 1:2
                    tp2 = round(price + risk * 3, 2)  # 1:3

                    # Use resistance as TP if closer
                    if state.sell_zone and state.sell_zone.price < tp2:
                        tp2 = state.sell_zone.price

                    rr = round((tp1 - price) / risk, 1) if risk > 0 else 0.0

                    if rr >= cfg.min_rr_ratio:
                        factors = [
                            ConfluenceFactor("REGIME_UPTREND", Direction.BUY, 0.3, state.regime_confidence, EpistemicLabel.DER),
                            ConfluenceFactor(f"AT_ZONE_{zone.price:.2f}", Direction.BUY, 0.3, 0.8, EpistemicLabel.OBS),
                            ConfluenceFactor("CONFIRMATION", Direction.BUY, 0.2, 0.7, EpistemicLabel.INT),
                            ConfluenceFactor(f"RR_1:{rr}", Direction.BUY, 0.2, min(0.9, rr / 3), EpistemicLabel.DER),
                        ]
                        confidence = min(0.90, sum(f.weight * f.confidence for f in factors))
                        return Signal(
                            symbol=cfg.symbol,
                            direction=Direction.BUY,
                            strength=SignalStrength.STRONG if len(factors) >= 4 else SignalStrength.MODERATE,
                            confidence=round(confidence, 3),
                            entry_price=price,
                            stop_loss=sl,
                            take_profit_1=tp1,
                            take_profit_2=tp2,
                            rr_ratio=rr,
                            confluence_factors=factors,
                            confluence_score=round(sum(f.weight * f.confidence for f in factors), 3),
                            indicators=ind,
                            verdict=Verdict.HOLD,
                        )

    # ── DOWNTREND: Sell the rallies ──
    elif state.regime == Regime.DOWNTREND and state.sell_zone:
        zone = state.sell_zone
        if _is_near_zone(price, zone.price, atr_val, tolerance=1.2):
            if _has_confirmation(candles, Direction.SELL):
                # SL just above the resistance zone, not above absolute swing high
                sl = round(zone.price + atr_val * 1.0, 2)
                risk = sl - price
                if risk > 0:
                    tp1 = round(price - risk * 2, 2)  # 1:2
                    tp2 = round(price - risk * 3, 2)  # 1:3

                    # Use buy zone as TP if it gives better RR than default
                    if state.buy_zone and tp2 < state.buy_zone.price < tp1:
                        # Buy zone is between our targets — use it as realistic TP
                        tp2 = state.buy_zone.price

                    rr = round((price - tp1) / risk, 1) if risk > 0 else 0.0

                    if rr >= cfg.min_rr_ratio:
                        factors = [
                            ConfluenceFactor("REGIME_DOWNTREND", Direction.SELL, 0.3, state.regime_confidence, EpistemicLabel.DER),
                            ConfluenceFactor(f"AT_ZONE_{zone.price:.2f}", Direction.SELL, 0.3, 0.8, EpistemicLabel.OBS),
                            ConfluenceFactor("CONFIRMATION", Direction.SELL, 0.2, 0.7, EpistemicLabel.INT),
                            ConfluenceFactor(f"RR_1:{rr}", Direction.SELL, 0.2, min(0.9, rr / 3), EpistemicLabel.DER),
                        ]
                        confidence = min(0.90, sum(f.weight * f.confidence for f in factors))
                        return Signal(
                            symbol=cfg.symbol,
                            direction=Direction.SELL,
                            strength=SignalStrength.STRONG if len(factors) >= 4 else SignalStrength.MODERATE,
                            confidence=round(confidence, 3),
                            entry_price=price,
                            stop_loss=sl,
                            take_profit_1=tp1,
                            take_profit_2=tp2,
                            rr_ratio=rr,
                            confluence_factors=factors,
                            confluence_score=round(sum(f.weight * f.confidence for f in factors), 3),
                            indicators=ind,
                            verdict=Verdict.HOLD,
                        )

    # ── SIDEWAYS: Buy support, sell resistance ──
    elif state.regime == Regime.SIDEWAYS:
        # Buy at support
        if state.buy_zone and _is_near_zone(price, state.buy_zone.price, atr_val, 1.0):
            if _has_confirmation(candles, Direction.BUY):
                zone = state.buy_zone
                sl = round(zone.price - atr_val * 1.0, 2)
                risk = price - sl
                if risk > 0:
                    # TP at mid-range or resistance
                    tp = state.sell_zone.price if state.sell_zone else round(price + risk * 2, 2)
                    rr = round((tp - price) / risk, 1)
                    if rr >= cfg.min_rr_ratio:
                        factors = [
                            ConfluenceFactor("REGIME_SIDEWAYS", Direction.BUY, 0.25, state.regime_confidence, EpistemicLabel.DER),
                            ConfluenceFactor(f"SUPPORT_{zone.price:.2f}", Direction.BUY, 0.30, 0.8, EpistemicLabel.OBS),
                            ConfluenceFactor("CONFIRMATION", Direction.BUY, 0.25, 0.7, EpistemicLabel.INT),
                            ConfluenceFactor(f"RR_1:{rr}", Direction.BUY, 0.20, min(0.9, rr / 3), EpistemicLabel.DER),
                        ]
                        confidence = min(0.90, sum(f.weight * f.confidence for f in factors))
                        return Signal(
                            symbol=cfg.symbol,
                            direction=Direction.BUY,
                            strength=SignalStrength.MODERATE,
                            confidence=round(confidence, 3),
                            entry_price=price,
                            stop_loss=sl,
                            take_profit_1=tp,
                            take_profit_2=tp,
                            rr_ratio=rr,
                            confluence_factors=factors,
                            confluence_score=round(sum(f.weight * f.confidence for f in factors), 3),
                            indicators=ind,
                            verdict=Verdict.HOLD,
                        )

        # Sell at resistance
        if state.sell_zone and _is_near_zone(price, state.sell_zone.price, atr_val, 1.0):
            if _has_confirmation(candles, Direction.SELL):
                zone = state.sell_zone
                sl = round(zone.price + atr_val * 1.0, 2)
                risk = sl - price
                if risk > 0:
                    tp = state.buy_zone.price if state.buy_zone else round(price - risk * 2, 2)
                    rr = round((price - tp) / risk, 1)
                    if rr >= cfg.min_rr_ratio:
                        factors = [
                            ConfluenceFactor("REGIME_SIDEWAYS", Direction.SELL, 0.25, state.regime_confidence, EpistemicLabel.DER),
                            ConfluenceFactor(f"RESISTANCE_{zone.price:.2f}", Direction.SELL, 0.30, 0.8, EpistemicLabel.OBS),
                            ConfluenceFactor("CONFIRMATION", Direction.SELL, 0.25, 0.7, EpistemicLabel.INT),
                            ConfluenceFactor(f"RR_1:{rr}", Direction.SELL, 0.20, min(0.9, rr / 3), EpistemicLabel.DER),
                        ]
                        confidence = min(0.90, sum(f.weight * f.confidence for f in factors))
                        return Signal(
                            symbol=cfg.symbol,
                            direction=Direction.SELL,
                            strength=SignalStrength.MODERATE,
                            confidence=round(confidence, 3),
                            entry_price=price,
                            stop_loss=sl,
                            take_profit_1=tp,
                            take_profit_2=tp,
                            rr_ratio=rr,
                            confluence_factors=factors,
                            confluence_score=round(sum(f.weight * f.confidence for f in factors), 3),
                            indicators=ind,
                            verdict=Verdict.HOLD,
                        )

    # ── No signal — not at a zone, or no confirmation ──
    zone_info = ""
    if state.buy_zone:
        zone_info += f"Buy zone: {state.buy_zone.price:.2f} ({abs(price - state.buy_zone.price):.2f} away). "
    if state.sell_zone:
        zone_info += f"Sell zone: {state.sell_zone.price:.2f} ({abs(price - state.sell_zone.price):.2f} away). "

    return Signal(
        direction=Direction.FLAT,
        strength=SignalStrength.NONE,
        confidence=state.regime_confidence,
        verdict=Verdict.SABAR,
        judge_reason=f"{state.regime.value} but no setup. {zone_info}Wait for price to reach zone.",
        indicators=ind,
        confluence_score=0.0,
    )
