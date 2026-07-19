"""
Regime Detector — The only 3 patterns that exist.
Uptrend. Downtrend. Sideways. That's it.

Truth: Buy low, sell high.
The "low" and "high" change based on regime.
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from ..core.models import OHLCV, Direction


class Regime(str, Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"


@dataclass
class Zone:
    """A price zone — the 'low' or 'high' of the current regime."""
    price: float
    zone_type: str  # "support" or "resistance"
    strength: int  # how many times tested (1=weak, 3+=strong)
    regime: Regime


@dataclass
class MarketState:
    """What the market is doing RIGHT NOW."""
    regime: Regime
    regime_confidence: float  # 0-1
    price: float
    # The zones that matter
    buy_zone: Optional[Zone] = None  # where to buy (the "low")
    sell_zone: Optional[Zone] = None  # where to sell (the "high")
    # EMA state
    ema_20: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    # Structure
    last_swing_high: float = 0.0
    last_swing_low: float = 0.0
    # RSI
    rsi: float = 50.0

    @property
    def description(self) -> str:
        if self.regime == Regime.UPTREND:
            return f"📈 UPTREND — Buy the dips near {self.buy_zone.price:.2f}" if self.buy_zone else "📈 UPTREND"
        elif self.regime == Regime.DOWNTREND:
            return f"📉 DOWNTREND — Sell the rallies near {self.sell_zone.price:.2f}" if self.sell_zone else "📉 DOWNTREND"
        return f"📊 SIDEWAYS — Buy {self.buy_zone.price:.2f}, Sell {self.sell_zone.price:.2f}" if self.buy_zone and self.sell_zone else "📊 SIDEWAYS"


def detect_regime(ema_20: float, ema_50: float, ema_200: float) -> tuple[Regime, float]:
    """
    Classify market into one of 3 regimes using EMA alignment.

    Returns (regime, confidence).
    Confidence based on how cleanly EMAs are aligned.
    """
    # Perfect alignment
    if ema_20 > ema_50 > ema_200:
        # How clean is the alignment?
        spread_20_50 = (ema_20 - ema_50) / ema_50 * 100
        spread_50_200 = (ema_50 - ema_200) / ema_200 * 100
        confidence = min(0.95, 0.5 + (spread_20_50 + spread_50_200) * 0.5)
        return Regime.UPTREND, round(confidence, 2)

    elif ema_20 < ema_50 < ema_200:
        spread_50_20 = (ema_50 - ema_20) / ema_50 * 100
        spread_200_50 = (ema_200 - ema_50) / ema_200 * 100
        confidence = min(0.95, 0.5 + (spread_50_20 + spread_200_50) * 0.5)
        return Regime.DOWNTREND, round(confidence, 2)

    # EMAs tangled = sideways
    # Calculate how tangled
    spreads = [
        abs(ema_20 - ema_50) / ema_50 * 100,
        abs(ema_50 - ema_200) / ema_200 * 100,
        abs(ema_20 - ema_200) / ema_200 * 100,
    ]
    avg_spread = sum(spreads) / 3
    # Smaller spreads = more sideways
    confidence = min(0.95, 0.5 + (1 - min(avg_spread / 2, 1)) * 0.45)
    return Regime.SIDEWAYS, round(confidence, 2)


def find_swing_points(candles: list[OHLCV], lookback: int = 10) -> list[tuple[float, str]]:
    """
    Find swing highs and swing lows.
    Returns list of (price, "HIGH"|"LOW").
    """
    if len(candles) < lookback * 2 + 1:
        return []

    swings = []
    for i in range(lookback, len(candles) - lookback):
        # Swing high: highest point in window
        is_high = all(
            candles[i].high >= candles[j].high
            for j in range(i - lookback, i + lookback + 1)
            if j != i
        )
        if is_high:
            swings.append((candles[i].high, "HIGH"))

        # Swing low: lowest point in window
        is_low = all(
            candles[i].low <= candles[j].low
            for j in range(i - lookback, i + lookback + 1)
            if j != i
        )
        if is_low:
            swings.append((candles[i].low, "LOW"))

    return swings


def find_zones(candles: list[OHLCV], lookback: int = 20) -> tuple[list[Zone], list[Zone]]:
    """
    Find support zones (buy zones) and resistance zones (sell zones).
    Based on swing points clustering.
    """
    swings = find_swing_points(candles, lookback=max(5, lookback // 4))
    if not swings:
        return [], []

    supports = sorted([s for s in swings if s[1] == "LOW"], key=lambda x: x[0])
    resistances = sorted([s for s in swings if s[1] == "HIGH"], key=lambda x: x[0], reverse=True)

    # Cluster nearby levels (within 0.3% of each other)
    def cluster_levels(levels: list[float], threshold_pct: float = 0.3) -> list[Zone]:
        if not levels:
            return []
        clusters = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if abs(level - current_cluster[0]) / current_cluster[0] * 100 < threshold_pct:
                current_cluster.append(level)
            else:
                avg = sum(current_cluster) / len(current_cluster)
                clusters.append(Zone(
                    price=round(avg, 2),
                    zone_type="support" if avg < candles[-1].close else "resistance",
                    strength=len(current_cluster),
                    regime=Regime.SIDEWAYS,
                ))
                current_cluster = [level]
        # Last cluster
        if current_cluster:
            avg = sum(current_cluster) / len(current_cluster)
            clusters.append(Zone(
                price=round(avg, 2),
                zone_type="support" if avg < candles[-1].close else "resistance",
                strength=len(current_cluster),
                regime=Regime.SIDEWAYS,
            ))
        return clusters

    support_zones = cluster_levels([s[0] for s in supports])
    resistance_zones = cluster_levels([r[0] for r in resistances])

    return support_zones, resistance_zones


def compute_market_state(candles: list[OHLCV], ema_20: float, ema_50: float, ema_200: float, rsi: float) -> MarketState:
    """
    Full market state analysis.
    This is the SINGLE function that tells you: what is the market doing, and where are the zones.
    """
    price = candles[-1].close if candles else 0.0

    # 1. Detect regime
    regime, confidence = detect_regime(ema_20, ema_50, ema_200)

    # 2. Find zones
    support_zones, resistance_zones = find_zones(candles)

    # 3. Assign buy/sell zones based on regime
    buy_zone = None
    sell_zone = None

    if regime == Regime.UPTREND:
        # Buy zone = nearest support below price (the dip)
        below = [z for z in support_zones if z.price < price]
        if below:
            buy_zone = max(below, key=lambda z: z.price)  # nearest support
            buy_zone.zone_type = "buy_zone"
        # Sell zone = nearest resistance above (the high)
        above = [z for z in resistance_zones if z.price > price]
        if above:
            sell_zone = min(above, key=lambda z: z.price)
            sell_zone.zone_type = "sell_zone"

    elif regime == Regime.DOWNTREND:
        # Sell zone = nearest resistance above price (the rally)
        above = [z for z in resistance_zones if z.price > price]
        if above:
            sell_zone = min(above, key=lambda z: z.price)
            sell_zone.zone_type = "sell_zone"
        # Buy zone = next support way below (deep value)
        below = [z for z in support_zones if z.price < price]
        if below:
            buy_zone = max(below, key=lambda z: z.price)
            buy_zone.zone_type = "buy_zone"

    else:  # SIDEWAYS
        # Both zones matter — buy at bottom, sell at top
        below = [z for z in support_zones if z.price < price]
        above = [z for z in resistance_zones if z.price > price]
        if below:
            buy_zone = max(below, key=lambda z: z.price)
            buy_zone.zone_type = "buy_zone"
        if above:
            sell_zone = min(above, key=lambda z: z.price)
            sell_zone.zone_type = "sell_zone"

    # 4. Swing points
    swings = find_swing_points(candles)
    last_high = max((s[0] for s in swings if s[1] == "HIGH"), default=0.0)
    last_low = min((s[0] for s in swings if s[1] == "LOW"), default=0.0)

    return MarketState(
        regime=regime,
        regime_confidence=confidence,
        price=price,
        buy_zone=buy_zone,
        sell_zone=sell_zone,
        ema_20=ema_20,
        ema_50=ema_50,
        ema_200=ema_200,
        last_swing_high=round(last_high, 2),
        last_swing_low=round(last_low, 2),
        rsi=rsi,
    )
