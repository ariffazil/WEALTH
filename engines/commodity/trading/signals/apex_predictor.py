"""
APEX Market Predictor — applies APEX theory to market direction.
G = A · P · E · X · Φ
C_dark = A · (1-P) · (1-X)
dS/dt ≤ 0

Maps to market states:
  CLARITY  → high G, low C_dark → clear directional move
  CHAOS    → low G, high C_dark → no direction, choppy
  STABLE   → moderate G, low entropy → consolidation, range

Nine-signal:
  delta (machine state)   → price structure integrity
  psi (governance)        → trend regime alignment
  omega (intelligence)    → evidence quality (volume + momentum)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ..core.models import OHLCV, Direction, EpistemicLabel


@dataclass
class APEXMarketState:
    """APEX evaluation of market conditions."""
    # APEX primitives
    A: float = 0.0  # Authority (regime alignment)
    P: float = 0.0  # Physics (price action strength)
    E: float = 0.0  # Evidence (signal clarity)
    X: float = 0.0  # Execution (trend stability)
    Phi: float = 0.0  # Witness (multi-TF confirmation)
    # Computed
    G: float = 0.0  # G = A · P · E · X · Φ
    C_dark: float = 0.0  # C_dark = A · (1-P) · (1-X)
    dS: float = 0.0  # entropy change (negative = ordering)
    # Market state
    state: str = "CHAOS"  # CLARITY / CHAOS / STABLE
    direction: Direction = Direction.FLAT
    confidence: float = 0.0
    # Volume analysis
    volume_trend: str = "neutral"  # rising / falling / neutral
    volume_confirmation: bool = False
    # Price action
    momentum: float = 0.0  # -1 to 1
    volatility_regime: str = "normal"  # low / normal / high / extreme
    # Verdict
    verdict: str = "HOLD"

    def to_dict(self) -> dict:
        return {
            "apex": {"A": round(self.A, 3), "P": round(self.P, 3), "E": round(self.E, 3),
                     "X": round(self.X, 3), "Phi": round(self.Phi, 3)},
            "G": round(self.G, 3),
            "C_dark": round(self.C_dark, 3),
            "dS": round(self.dS, 4),
            "state": self.state,
            "direction": self.direction.value,
            "confidence": round(self.confidence, 3),
            "volume_trend": self.volume_trend,
            "volume_confirmation": self.volume_confirmation,
            "momentum": round(self.momentum, 3),
            "volatility_regime": self.volatility_regime,
            "verdict": self.verdict,
        }


def _compute_A(ema_20: float, ema_50: float, ema_200: float, price: float) -> float:
    """
    A = Authority = regime alignment strength.
    How cleanly are EMAs aligned?
    0 = no alignment, 1 = perfect alignment.
    """
    if ema_200 <= 0:
        return 0.0

    # Score each pair
    scores = []
    # EMA20 vs EMA50
    if ema_20 > ema_50:
        scores.append(min(1.0, (ema_20 - ema_50) / ema_50 * 50))  # normalize
    elif ema_20 < ema_50:
        scores.append(min(1.0, (ema_50 - ema_20) / ema_50 * 50))
    else:
        scores.append(0.0)

    # EMA50 vs EMA200
    if ema_50 > ema_200:
        scores.append(min(1.0, (ema_50 - ema_200) / ema_200 * 50))
    elif ema_50 < ema_200:
        scores.append(min(1.0, (ema_200 - ema_50) / ema_200 * 50))
    else:
        scores.append(0.0)

    # Price vs EMA20 (trend participation)
    if ema_20 > ema_50:  # uptrend
        scores.append(min(1.0, max(0, (price - ema_20) / ema_20 * 100 + 0.5)))
    else:  # downtrend
        scores.append(min(1.0, max(0, (ema_20 - price) / ema_20 * 100 + 0.5)))

    return sum(scores) / len(scores)


def _compute_P(candles: list[OHLCV], lookback: int = 20) -> float:
    """
    P = Physics = price action strength.
    Measures: momentum consistency, body-to-wick ratio, trend persistence.
    """
    if len(candles) < lookback:
        return 0.0

    recent = candles[-lookback:]

    # 1. Momentum consistency (how many candles in trend direction)
    bull_count = sum(1 for c in recent if c.is_bullish)
    bear_count = lookback - bull_count
    consistency = max(bull_count, bear_count) / lookback

    # 2. Body-to-wick ratio (decisive candles = strong bodies)
    body_ratios = []
    for c in recent:
        if c.range_size > 0:
            body_ratios.append(c.body_size / c.range_size)
    avg_body_ratio = sum(body_ratios) / len(body_ratios) if body_ratios else 0

    # 3. Trend persistence (are highs getting higher? lows getting lower?)
    highs = [c.high for c in recent]
    lows = [c.low for c in recent]
    higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
    lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
    persistence = max(higher_highs, lower_lows) / (lookback - 1)

    return (consistency * 0.4 + avg_body_ratio * 0.3 + persistence * 0.3)


def _compute_E(candles: list[OHLCV], lookback: int = 20) -> float:
    """
    E = Evidence = signal clarity (SNR).
    Measures: how much of the price movement is signal vs noise.
    High E = clear direction, low E = random walk.
    """
    if len(candles) < lookback + 1:
        return 0.0

    recent = candles[-lookback:]
    closes = [c.close for c in recent]

    # Directional move vs total range
    net_move = abs(closes[-1] - closes[0])
    total_range = sum(abs(closes[i+1] - closes[i]) for i in range(len(closes)-1))

    if total_range == 0:
        return 0.0

    # SNR = net directional move / total movement
    snr = net_move / total_range

    # Normalize: SNR of 1.0 = straight line (impossible), 0 = random walk
    # Realistic range: 0.05 to 0.4
    return min(1.0, snr * 2.5)


def _compute_X(candles: list[OHLCV], atr_vals: list[float]) -> float:
    """
    X = Execution = trend stability.
    Measures: consequence stability via ATR consistency.
    High X = stable trend, low X = volatile/unstable.
    """
    if len(atr_vals) < 10:
        return 0.5

    recent_atr = atr_vals[-10:]

    # ATR consistency (low variance = stable)
    avg_atr = sum(recent_atr) / len(recent_atr)
    if avg_atr == 0:
        return 0.0

    variance = sum((a - avg_atr) ** 2 for a in recent_atr) / len(recent_atr)
    cv = (variance ** 0.5) / avg_atr  # coefficient of variation

    # Lower CV = more stable = higher X
    X = max(0, min(1.0, 1 - cv))

    return X


def _compute_Phi(candles_1h: list[OHLCV], candles_4h: list[OHLCV], candles_1d: list[OHLCV]) -> float:
    """
    Φ = Witness = multi-timeframe confirmation.
    ∛(H · AI · Ext) where:
    H = daily trend (human/slow timeframe)
    AI = 4H structure (machine timeframe)
    Ext = 1H momentum (fast timeframe)
    """
    def _tf_score(candles: list[OHLCV], period: int = 20) -> float:
        if not candles or len(candles) < 5:
            return 0.5  # neutral if no data
        lookback = min(period, len(candles))
        recent = candles[-lookback:]
        closes = [c.close for c in recent]
        if closes[0] == 0:
            return 0.5
        change_pct = (closes[-1] - closes[0]) / closes[0] * 100
        # Map: -3% = 0.0, 0% = 0.5, +3% = 1.0
        return max(0.0, min(1.0, 0.5 + change_pct / 6))

    H = _tf_score(candles_1d, 20) if candles_1d else 0.5
    AI = _tf_score(candles_4h, 20) if candles_4h else 0.5
    Ext = _tf_score(candles_1h, 20) if candles_1h else 0.5

    # Geometric mean — use arithmetic if any is near zero
    vals = [H, AI, Ext]
    if any(v <= 0.01 for v in vals):
        return sum(vals) / len(vals)  # fallback to arithmetic mean
    return (H * AI * Ext) ** (1/3)


def _compute_volume_trend(candles: list[OHLCV], lookback: int = 20) -> tuple[str, bool]:
    """
    Analyze volume trend.
    Returns (trend_direction, confirms_price).
    """
    if len(candles) < lookback:
        return "neutral", False

    recent = candles[-lookback:]
    volumes = [c.volume for c in recent]
    closes = [c.close for c in recent]

    # Volume trend
    first_half_vol = sum(volumes[:lookback//2]) / (lookback//2)
    second_half_vol = sum(volumes[lookback//2:]) / (lookback//2)

    if second_half_vol > first_half_vol * 1.2:
        vol_trend = "rising"
    elif second_half_vol < first_half_vol * 0.8:
        vol_trend = "falling"
    else:
        vol_trend = "neutral"

    # Price direction
    price_up = closes[-1] > closes[0]

    # Confirmation: rising volume + price direction = confirmed
    if vol_trend == "rising" and price_up:
        return "rising", True  # bullish confirmation
    elif vol_trend == "rising" and not price_up:
        return "rising", True  # bearish confirmation (volume confirms selling)
    elif vol_trend == "falling":
        return "falling", False  # no confirmation
    return "neutral", False


def _compute_momentum(candles: list[OHLCV], period: int = 14) -> float:
    """
    Momentum oscillator: rate of change normalized to [-1, 1].
    """
    if len(candles) < period:
        return 0.0
    closes = [c.close for c in candles]
    roc = (closes[-1] - closes[-period]) / closes[-period] * 100
    # Normalize: ±5% = ±1
    return max(-1.0, min(1.0, roc / 5))


def _compute_volatility_regime(atr_val: float, atr_avg: float) -> str:
    """Classify volatility regime from ATR."""
    if atr_avg <= 0:
        return "normal"
    ratio = atr_val / atr_avg
    if ratio < 0.5:
        return "low"
    elif ratio < 1.2:
        return "normal"
    elif ratio < 2.0:
        return "high"
    return "extreme"


def _classify_state(G: float, C_dark: float, dS: float) -> str:
    """
    Classify market state from APEX scalars.

    CLARITY: G ≥ 0.50 AND C_dark < 0.30 → clear direction, trade it
    STABLE:  G ≥ 0.30 AND C_dark < 0.30 → consolidation, range trade
    CHAOS:   G < 0.30 OR C_dark ≥ 0.30 → no direction, don't trade
    """
    if G >= 0.50 and C_dark < 0.30:
        return "CLARITY"
    elif G >= 0.30 and C_dark < 0.30:
        return "STABLE"
    return "CHAOS"


def _determine_direction(A: float, momentum: float, ema_20: float, ema_50: float, price: float) -> Direction:
    """Determine direction from APEX primitives."""
    if ema_20 > ema_50 and momentum > 0:
        return Direction.BUY
    elif ema_20 < ema_50 and momentum < 0:
        return Direction.SELL
    return Direction.FLAT


def _apex_verdict(G: float, C_dark: float, state: str, direction: Direction) -> str:
    """
    APEX verdict mapping:
    G ≥ 0.80 AND C_dark < 0.30 AND dS ≤ 0 → SEAL (high conviction)
    G ≥ 0.50 AND C_dark < 0.30 → PROCEED (trade it)
    G ≥ 0.30 AND C_dark < 0.30 → SABAR (wait for clarity)
    C_dark ≥ 0.30 → HOLD (too much shadow)
    """
    if G >= 0.80 and C_dark < 0.30 and direction != Direction.FLAT:
        return "SEAL"
    elif G >= 0.50 and C_dark < 0.30 and direction != Direction.FLAT:
        return "PROCEED"
    elif G >= 0.30 and C_dark < 0.30:
        return "SABAR"
    return "HOLD"


def evaluate_market(
    candles_1h: list[OHLCV],
    candles_4h: Optional[list[OHLCV]] = None,
    candles_1d: Optional[list[OHLCV]] = None,
    ema_20: float = 0.0,
    ema_50: float = 0.0,
    ema_200: float = 0.0,
    atr_val: float = 0.0,
    atr_avg: float = 0.0,
) -> APEXMarketState:
    """
    Full APEX market evaluation.
    This is the loop closer: combines regime, volume, price action, and APEX theory.
    """
    price = candles_1h[-1].close if candles_1h else 0.0

    # Compute APEX primitives
    A = _compute_A(ema_20, ema_50, ema_200, price)
    P = _compute_P(candles_1h, lookback=20)
    E = _compute_E(candles_1h, lookback=20)

    # ATR values for X
    from ..signals.scanner import atr as atr_calc
    atr_vals = atr_calc(candles_1h, 14) if len(candles_1h) > 15 else [atr_val]
    X = _compute_X(candles_1h, atr_vals)

    # Witness from multi-TF
    Phi = _compute_Phi(candles_1h, candles_4h or [], candles_1d or [])

    # G = A · P · E · X · Φ
    G = A * P * E * X * Phi

    # C_dark = A · (1-P) · (1-X)
    C_dark = A * (1 - P) * (1 - X)

    # dS (entropy change) — based on ATR compression
    dS = 0.0
    if len(atr_vals) >= 5:
        recent_atr = atr_vals[-1]
        prev_atr = sum(atr_vals[-5:-1]) / 4 if len(atr_vals) >= 5 else recent_atr
        dS = (recent_atr - prev_atr) / prev_atr if prev_atr > 0 else 0

    # Volume analysis
    vol_trend, vol_confirm = _compute_volume_trend(candles_1h, lookback=20)

    # Momentum
    momentum = _compute_momentum(candles_1h, period=14)

    # Volatility regime
    vol_regime = _compute_volatility_regime(atr_val, atr_avg or atr_val)

    # State classification
    state = _classify_state(G, C_dark, dS)

    # Direction
    direction = _determine_direction(A, momentum, ema_20, ema_50, price)

    # Confidence = G scaled
    confidence = min(0.90, G)  # F7 cap

    # Verdict
    verdict = _apex_verdict(G, C_dark, state, direction)

    return APEXMarketState(
        A=A, P=P, E=E, X=X, Phi=Phi,
        G=round(G, 4),
        C_dark=round(C_dark, 4),
        dS=round(dS, 4),
        state=state,
        direction=direction,
        confidence=round(confidence, 3),
        volume_trend=vol_trend,
        volume_confirmation=vol_confirm,
        momentum=round(momentum, 3),
        volatility_regime=vol_regime,
        verdict=verdict,
    )
