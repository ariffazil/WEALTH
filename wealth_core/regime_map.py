"""
Regime Map Engine — Distribution-Aware Market Regime Classification

Eureka source: TradeMaster (NTU) market dynamics labeling + AlphaMix+ regime-aware MoE.
Distilled into WEALTH capital_diagnose.mode=regime_map.

Core insight: Regime is NOT a property of the current candle.
Regime IS a property of the distribution shift over a window.

Classification approach (no ML, pure numpy on existing OHLCV):
1. Rolling window statistics (mean, std, skew, kurtosis)
2. Volatility regime (ATR ratio to historical)
3. Trend strength (ADX-like directional movement)
4. Distribution shift detection (momentum consistency)

Output: Per-bar regime labels + current regime + regime transition probabilities.

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegimeBar:
    """Single bar's regime classification."""

    index: int
    regime: str  # BULL, BEAR, SIDEWAYS, VOLATILE, CRISIS
    confidence: float  # 0-1
    volatility_state: str  # LOW, NORMAL, HIGH, EXTREME
    trend_strength: float  # 0-1


@dataclass
class RegimeTransition:
    """Regime transition probability."""

    from_regime: str
    to_regime: str
    count: int
    probability: float


@dataclass
class RegimeMapResult:
    """Full regime map output."""

    current_regime: str
    current_confidence: float
    volatility_state: str
    trend_strength: float
    regime_distribution: dict[str, float]  # regime -> % of bars
    transitions: list[RegimeTransition]
    regime_bars: list[dict]  # last 20 bars with labels
    distribution_shift_detected: bool
    shift_severity: str  # NONE, MILD, SEVERE
    bars_analyzed: int
    window_size: int


def _rolling_stats(closes: list[float], window: int) -> dict[str, list[float]]:
    """Compute rolling statistics over a window."""
    n = len(closes)
    if n < window:
        return {"mean": [], "std": [], "returns": [], "skew": [], "kurtosis": []}

    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1] if closes[i - 1] != 0 else 0
        for i in range(1, n)
    ]

    means = []
    stds = []
    skews = []
    kurtoses = []

    for i in range(window - 1, len(returns)):
        w = returns[i - window + 1 : i + 1]
        m = sum(w) / len(w)
        v = sum((x - m) ** 2 for x in w) / len(w)
        s = v**0.5

        means.append(m)
        stds.append(s if s > 0 else 1e-10)

        # Skewness
        if s > 1e-10:
            sk = sum((x - m) ** 3 for x in w) / (len(w) * s**3)
        else:
            sk = 0.0
        skews.append(sk)

        # Kurtosis (excess)
        if s > 1e-10:
            ku = sum((x - m) ** 4 for x in w) / (len(w) * s**4) - 3.0
        else:
            ku = 0.0
        kurtoses.append(ku)

    return {
        "mean": means,
        "std": stds,
        "returns": returns,
        "skew": skews,
        "kurtosis": kurtoses,
    }


def _atr_series(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> list[float]:
    """Compute ATR series."""
    n = len(closes)
    if n < period + 1:
        return []

    trs = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)

    if len(trs) < period:
        return []

    # Wilder's smoothing (RMA)
    atrs = [sum(trs[:period]) / period]
    for i in range(period, len(trs)):
        atrs.append((atrs[-1] * (period - 1) + trs[i]) / period)

    return atrs


def _directional_movement(
    highs: list[float], lows: list[float], period: int = 14
) -> list[float]:
    """Compute ADX-like directional movement index (0-100 normalized to 0-1)."""
    n = len(highs)
    if n < period + 1:
        return []

    plus_dm = []
    minus_dm = []

    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]

        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

    if len(plus_dm) < period:
        return []

    # Smoothed DM
    sm_plus = [sum(plus_dm[:period])]
    sm_minus = [sum(minus_dm[:period])]

    for i in range(period, len(plus_dm)):
        sm_plus.append(sm_plus[-1] - sm_plus[-1] / period + plus_dm[i])
        sm_minus.append(sm_minus[-1] - sm_minus[-1] / period + minus_dm[i])

    # DX
    dxs = []
    for i in range(len(sm_plus)):
        total = sm_plus[i] + sm_minus[i]
        if total > 0:
            dx = abs(sm_plus[i] - sm_minus[i]) / total * 100
        else:
            dx = 0
        dxs.append(dx)

    return dxs


def _classify_bar(
    returns_mean: float,
    returns_std: float,
    skew: float,
    kurtosis: float,
    atr_ratio: float,
    dx: float,
) -> tuple[str, float, str, float]:
    """Classify a single bar into regime.

    Returns (regime, confidence, volatility_state, trend_strength).
    """
    # Volatility state from ATR ratio
    if atr_ratio < 0.5:
        vol_state = "LOW"
    elif atr_ratio < 1.2:
        vol_state = "NORMAL"
    elif atr_ratio < 2.0:
        vol_state = "HIGH"
    else:
        vol_state = "EXTREME"

    # Trend strength from DX
    trend_str = min(1.0, dx / 100) if dx > 0 else 0.0

    # Crisis detection: extreme kurtosis + negative skew + high vol
    if kurtosis > 5.0 and skew < -1.0 and atr_ratio > 1.5:
        return "CRISIS", min(0.95, 0.5 + kurtosis * 0.05), vol_state, trend_str

    # Volatile: high vol but not crisis
    if atr_ratio > 1.5 and vol_state in ("HIGH", "EXTREME"):
        return "VOLATILE", min(0.90, 0.4 + atr_ratio * 0.2), vol_state, trend_str

    # Bull: positive returns + strong trend
    if returns_mean > 0 and trend_str > 0.3:
        conf = min(0.95, 0.3 + returns_mean * 50 + trend_str * 0.3)
        return "BULL", conf, vol_state, trend_str

    # Bear: negative returns + strong trend
    if returns_mean < 0 and trend_str > 0.3:
        conf = min(0.95, 0.3 + abs(returns_mean) * 50 + trend_str * 0.3)
        return "BEAR", conf, vol_state, trend_str

    # Sideways: weak trend
    return "SIDEWAYS", min(0.85, 0.4 + (1 - trend_str) * 0.3), vol_state, trend_str


def _detect_distribution_shift(
    regime_bars: list[RegimeBar], window: int = 20
) -> tuple[bool, str]:
    """Detect if a distribution shift has occurred in the recent window.

    Compares volatility and trend statistics of the last `window` bars
    against the preceding window.
    """
    if len(regime_bars) < window * 2:
        return False, "NONE"

    recent = regime_bars[-window:]
    prior = regime_bars[-window * 2 : -window]

    # Compare regime distributions
    recent_bull = sum(1 for b in recent if b.regime == "BULL") / len(recent)
    prior_bull = sum(1 for b in prior if b.regime == "BULL") / len(prior)

    recent_vol = sum(
        1 for b in recent if b.volatility_state in ("HIGH", "EXTREME")
    ) / len(recent)
    prior_vol = sum(
        1 for b in prior if b.volatility_state in ("HIGH", "EXTREME")
    ) / len(prior)

    # Shift = large change in regime composition or volatility
    regime_shift = abs(recent_bull - prior_bull)
    vol_shift = abs(recent_vol - prior_vol)

    severity_score = regime_shift * 0.5 + vol_shift * 0.5

    if severity_score > 0.4:
        return True, "SEVERE"
    elif severity_score > 0.2:
        return True, "MILD"
    return False, "NONE"


def compute_regime_map(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    window: int = 20,
    atr_period: int = 14,
) -> RegimeMapResult:
    """Compute full regime map from OHLCV data.

    Args:
        closes: Close prices
        highs: High prices
        lows: Low prices
        window: Rolling window for statistics
        atr_period: ATR period for volatility

    Returns:
        RegimeMapResult with full regime classification
    """
    if len(closes) < max(window, atr_period) + 20:
        return RegimeMapResult(
            current_regime="UNKNOWN",
            current_confidence=0.0,
            volatility_state="UNKNOWN",
            trend_strength=0.0,
            regime_distribution={},
            transitions=[],
            regime_bars=[],
            distribution_shift_detected=False,
            shift_severity="NONE",
            bars_analyzed=0,
            window_size=window,
        )

    # Compute rolling stats
    stats = _rolling_stats(closes, window)
    atrs = _atr_series(highs, lows, closes, atr_period)
    dxs = _directional_movement(highs, lows, atr_period)

    # Compute historical ATR average for ratio
    atr_avg = sum(atrs) / len(atrs) if atrs else 1.0

    # Classify each bar
    regime_bars = []
    regime_counts = {"BULL": 0, "BEAR": 0, "SIDEWAYS": 0, "VOLATILE": 0, "CRISIS": 0}

    min_len = min(len(stats["mean"]), len(atrs), len(dxs))
    offset = max(window - 1, atr_period)  # align indices

    for i in range(min_len):
        atr_ratio = atrs[i] / atr_avg if atr_avg > 0 else 1.0
        dx = dxs[i] if i < len(dxs) else 0.0

        regime, conf, vol_state, trend_str = _classify_bar(
            stats["mean"][i],
            stats["std"][i],
            stats["skew"][i],
            stats["kurtosis"][i],
            atr_ratio,
            dx,
        )

        bar = RegimeBar(
            index=offset + i,
            regime=regime,
            confidence=round(conf, 3),
            volatility_state=vol_state,
            trend_strength=round(trend_str, 3),
        )
        regime_bars.append(bar)
        regime_counts[regime] = regime_counts.get(regime, 0) + 1

    # Current regime = last bar
    current = (
        regime_bars[-1] if regime_bars else RegimeBar(0, "UNKNOWN", 0, "UNKNOWN", 0)
    )

    # Regime distribution (% of bars)
    total = len(regime_bars) or 1
    distribution = {k: round(v / total * 100, 1) for k, v in regime_counts.items()}

    # Transition matrix
    transitions = _compute_transitions(regime_bars)

    # Distribution shift detection
    shift_detected, shift_severity = _detect_distribution_shift(regime_bars, window)

    return RegimeMapResult(
        current_regime=current.regime,
        current_confidence=current.confidence,
        volatility_state=current.volatility_state,
        trend_strength=current.trend_strength,
        regime_distribution=distribution,
        transitions=transitions,
        regime_bars=[
            {
                "index": b.index,
                "regime": b.regime,
                "confidence": b.confidence,
                "volatility": b.volatility_state,
                "trend": b.trend_strength,
            }
            for b in regime_bars[-20:]  # last 20 bars
        ],
        distribution_shift_detected=shift_detected,
        shift_severity=shift_severity,
        bars_analyzed=len(regime_bars),
        window_size=window,
    )


def _compute_transitions(regime_bars: list[RegimeBar]) -> list[RegimeTransition]:
    """Compute regime transition probabilities."""
    if len(regime_bars) < 2:
        return []

    counts: dict[tuple[str, str], int] = {}
    regime_totals: dict[str, int] = {}

    for i in range(1, len(regime_bars)):
        from_r = regime_bars[i - 1].regime
        to_r = regime_bars[i].regime
        key = (from_r, to_r)
        counts[key] = counts.get(key, 0) + 1
        regime_totals[from_r] = regime_totals.get(from_r, 0) + 1

    transitions = []
    for (from_r, to_r), count in sorted(counts.items()):
        total = regime_totals.get(from_r, 1)
        transitions.append(
            RegimeTransition(
                from_regime=from_r,
                to_regime=to_r,
                count=count,
                probability=round(count / total, 3),
            )
        )

    return transitions
