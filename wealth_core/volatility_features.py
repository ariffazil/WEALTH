"""
wealth_core/volatility_features.py — High-Fidelity Volatility Estimators
═══════════════════════════════════════════════════════════════════════

Extends alpha158 (which has basic ATR ratios) with professional-grade
volatility estimators used by quants and ML scalping systems.

Key difference: alpha158 uses ATR (high-low range, no intrabar shape).
These estimators use ALL four price points (OHLC) for better accuracy.

Features added:
1. Garman-Klass estimator — uses OHLC, more efficient than close-to-close
2. Parkinson estimator — uses High/Low, better for high-frequency
3. Yang-Zhang estimator — blends overnight + intraday + Rogers-Satchell
4. Rogers-Satchell — drift-independent volatility
5. Vol-of-vol — volatility of volatility (regime detection)
6. Range compression — Bollinger bandwidth contraction signal
7. Intraday range — (High-Low)/Close normalized
8. Close-to-Open gap — overnight volatility proxy

All pure numpy on existing candle data. No external dependencies.
DITEMPA BUKAN DIBERI — Forged from Garman-Klass (1980), Parkinson (1980),
Yang-Zhang (2000), Rogers-Satchell (1991).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class VolatilityFeatures:
    """Output from the volatility feature engine."""
    garman_klass: list[float] = field(default_factory=list)
    parkinson: list[float] = field(default_factory=list)
    yang_zhang: list[float] = field(default_factory=list)
    rogers_satchell: list[float] = field(default_factory=list)
    vol_of_vol: list[float] = field(default_factory=list)
    range_compression: list[float] = field(default_factory=list)
    intraday_range: list[float] = field(default_factory=list)
    close_open_gap: list[float] = field(default_factory=list)
    feature_count: int = 0
    bars_processed: int = 0
    feature_categories: dict[str, int] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE ESTIMATORS
# ═══════════════════════════════════════════════════════════════════════════════


def _safe_log(x: float, eps: float = 1e-10) -> float:
    """Natural log with floor to prevent log(0)."""
    return math.log(max(abs(x), eps))


def garman_klass(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 20,
) -> list[float]:
    """
    Garman-Klass (1980) volatility estimator.

    σ²_GK = 0.5 * ln(H/L)² - (2ln2 - 1) * ln(C/O)²

    Uses all four OHLC points. ~8x more efficient than close-to-close
    variance estimator. Assumes zero drift (valid for short windows).

    Returns: list of sqrt(GK) annualized per bar (NaN-padded for window-1 bars).
    """
    n = len(closes)
    if n < window:
        return [0.0] * n

    result = [0.0] * (window - 1)
    for i in range(window - 1, n):
        window_sq = 0.0
        for j in range(i - window + 1, i + 1):
            hl = _safe_log(highs[j] / lows[j])
            co = _safe_log(closes[j] / opens[j])
            window_sq += 0.5 * hl * hl - (2 * math.log(2) - 1) * co * co
        result.append(math.sqrt(max(window_sq / window, 0.0)))
    return result


def parkinson(
    highs: list[float],
    lows: list[float],
    window: int = 20,
) -> list[float]:
    """
    Parkinson (1980) volatility estimator.

    σ²_P = ln(H/L)² / (4ln2)

    Uses only high-low range. Better than close-to-close for high-frequency
    data because it captures intrabar price movement.

    Returns: list of sqrt(P) per bar.
    """
    n = len(highs)
    if n < window:
        return [0.0] * n

    result = [0.0] * (window - 1)
    coeff = 1.0 / (4.0 * math.log(2))
    for i in range(window - 1, n):
        window_sq = 0.0
        for j in range(i - window + 1, i + 1):
            hl = _safe_log(highs[j] / lows[j])
            window_sq += hl * hl * coeff
        result.append(math.sqrt(max(window_sq / window, 0.0)))
    return result


def rogers_satchell(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 20,
) -> list[float]:
    """
    Rogers-Satchell (1991) drift-independent volatility estimator.

    σ²_RS = ln(H/C) * ln(H/O) + ln(L/C) * ln(L/O)

    More accurate than Parkinson when there is drift (non-zero expected return).
    Used as a component in Yang-Zhang.
    """
    n = len(closes)
    if n < window:
        return [0.0] * n

    result = [0.0] * (window - 1)
    for i in range(window - 1, n):
        window_sq = 0.0
        for j in range(i - window + 1, i + 1):
            hc = _safe_log(highs[j] / closes[j])
            ho = _safe_log(highs[j] / opens[j])
            lc = _safe_log(lows[j] / closes[j])
            lo = _safe_log(lows[j] / opens[j])
            window_sq += hc * ho + lc * lo
        result.append(math.sqrt(max(window_sq / window, 0.0)))
    return result


def yang_zhang(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 20,
) -> list[float]:
    """
    Yang-Zhang (2000) volatility estimator.

    σ²_YZ = σ²_overnight + k * σ²_close + (1-k) * σ²_RS

    Blends overnight volatility (open-to-close), intraday range, and
    Rogers-Satchell. Most accurate single-bar estimator for OHLC data.
    k = 0.34 / (1.34 + (n+1)/(n-1))
    """
    n = len(closes)
    if n < window + 1:
        return [0.0] * n

    result = [0.0] * window
    k_denom = 1.34 + (n + 1) / max(n - 1, 1)
    k = 0.34 / k_denom

    for i in range(window, n):
        # Overnight volatility: log(C_prev / O_prev) — between-bar returns
        overnight_sq = 0.0
        for j in range(i - window + 1, i + 1):
            overnight_sq += _safe_log(closes[j] / opens[j]) ** 2
        overnight_var = overnight_sq / window

        # Close volatility: log(C_i / C_{i-1})
        close_sq = 0.0
        for j in range(i - window + 1, i + 1):
            close_sq += _safe_log(closes[j] / closes[j - 1]) ** 2
        close_var = close_sq / window

        # Rogers-Satchell (computed inline)
        rs_sq = 0.0
        for j in range(i - window + 1, i + 1):
            hc = _safe_log(highs[j] / closes[j])
            ho = _safe_log(highs[j] / opens[j])
            lc = _safe_log(lows[j] / closes[j])
            lo = _safe_log(lows[j] / opens[j])
            rs_sq += hc * ho + lc * lo
        rs_var = rs_sq / window

        yz = overnight_var + k * close_var + (1 - k) * rs_var
        result.append(math.sqrt(max(yz, 0.0)))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# DERIVED FEATURES
# ═══════════════════════════════════════════════════════════════════════════════


def _rolling_std(data: list[float], window: int) -> list[float]:
    """Rolling standard deviation. NaN-padded for window-1 bars."""
    n = len(data)
    if n < window:
        return [0.0] * n

    result = [0.0] * (window - 1)
    for i in range(window - 1, n):
        chunk = data[i - window + 1 : i + 1]
        mean = sum(chunk) / window
        var = sum((x - mean) ** 2 for x in chunk) / window
        result.append(math.sqrt(var))
    return result


def _rolling_mean(data: list[float], window: int) -> list[float]:
    """Rolling mean. NaN-padded for window-1 bars."""
    n = len(data)
    if n < window:
        return [0.0] * n

    result = [0.0] * (window - 1)
    for i in range(window - 1, n):
        chunk = data[i - window + 1 : i + 1]
        result.append(sum(chunk) / window)
    return result


def vol_of_vol(
    realized_vol: list[float],
    window: int = 20,
) -> list[float]:
    """
    Volatility of volatility — rolling std of realized volatility series.

    High vol-of-vol = regime uncertainty (transitional, not trending).
    Low vol-of-vol = stable regime (trending or range-bound, but stable).

    For ML scalping: regime detection. Trade when vol-of-vol is low
    (regime is stable), avoid when vol-of-vol is high (regime is uncertain).
    """
    return _rolling_std(realized_vol, window)


def range_compression(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 20,
    bollinger_window: int = 20,
    bollinger_std: float = 2.0,
) -> list[float]:
    """
    Bollinger Bandwidth contraction signal.

    bandwidth = (upper - lower) / middle
    compression = bandwidth / rolling_avg_bandwidth

    Compression < 0.8 = squeeze (breakout imminent).
    Used by Bollinger Bands Squeeze strategy.

    Returns: ratio of current bandwidth to average bandwidth.
    """
    n = len(closes)
    if n < window:
        return [1.0] * n

    # Compute Bollinger Bandwidth at each bar
    bbands = []
    for i in range(n):
        if i < bollinger_window - 1:
            bbands.append(0.0)
            continue
        chunk = closes[i - bollinger_window + 1 : i + 1]
        mean = sum(chunk) / bollinger_window
        var = sum((x - mean) ** 2 for x in chunk) / bollinger_window
        std = math.sqrt(var)
        upper = mean + bollinger_std * std
        lower = mean - bollinger_std * std
        bandwidth = (upper - lower) / mean if mean > 0 else 0.0
        bbands.append(bandwidth)

    # Compression ratio: current bandwidth / rolling average bandwidth
    result = [1.0] * (n - 1)
    for i in range(window - 1, n):
        chunk = bbands[i - window + 1 : i + 1]
        avg_bw = sum(chunk) / window
        result.append(
            bbands[i] / avg_bw if avg_bw > 1e-10 else 1.0
        )
    return result


def intraday_range(
    highs: list[float],
    lows: list[float],
    closes: list[float],
) -> list[float]:
    """
    Normalized intraday range: (High - Low) / Close.

    Used by ATR-percentage and range-based strategies.
    Scaled per-bar, no window needed.
    """
    return [
        (h - l) / c if abs(c) > 1e-10 else 0.0
        for h, l, c in zip(highs, lows, closes)
    ]


def close_open_gap(
    opens: list[float],
    closes: list[float],
) -> list[float]:
    """
    Overnight gap: (Close / Open) - 1 = log-return from open to close.

    Proxy for intraday volatility — how much the bar moved during
    the session (open to close, not including overnight gaps).
    """
    return [
        (c / o - 1.0) if abs(o) > 1e-10 else 0.0
        for o, c in zip(opens, closes)
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════


def compute_all_volatility_features(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    window: int = 20,
) -> VolatilityFeatures:
    """
    Compute all volatility features from OHLCV data.

    Args:
        opens, highs, lows, closes: Price arrays (same length, aligned)
        window: Rolling window for multi-period estimators (default 20)

    Returns:
        VolatilityFeatures with all features and metadata
    """
    n = len(closes)
    if n < 2:
        return VolatilityFeatures(bars_processed=n)

    # Core estimators
    gk = garman_klass(opens, highs, lows, closes, window)
    pk = parkinson(highs, lows, window)
    rs = rogers_satchell(opens, highs, lows, closes, window)
    yz = yang_zhang(opens, highs, lows, closes, window)

    # Derived features
    vov = vol_of_vol(gk, window)  # vol-of-vol based on Garman-Klass
    rc = range_compression(highs, lows, closes, window)
    ir = intraday_range(highs, lows, closes)
    cg = close_open_gap(opens, closes)

    # Count features
    all_features = [gk, pk, yz, rs, vov, rc, ir, cg]
    feature_count = sum(len(f) for f in all_features if f)

    return VolatilityFeatures(
        garman_klass=gk,
        parkinson=pk,
        yang_zhang=yz,
        rogers_satchell=rs,
        vol_of_vol=vov,
        range_compression=rc,
        intraday_range=ir,
        close_open_gap=cg,
        feature_count=feature_count,
        bars_processed=n,
        feature_categories={
            "garman_klass": len(gk),
            "parkinson": len(pk),
            "yang_zhang": len(yz),
            "rogers_satchell": len(rs),
            "vol_of_vol": len(vov),
            "range_compression": len(rc),
            "intraday_range": len(ir),
            "close_open_gap": len(cg),
        },
    )


def format_features_as_dict(
    result: VolatilityFeatures,
) -> dict[str, list[float]]:
    """Convert to dict format compatible with alpha158 output."""
    return {
        "vol_garman_klass": result.garman_klass,
        "vol_parkinson": result.parkinson,
        "vol_yang_zhang": result.yang_zhang,
        "vol_rogers_satchell": result.rogers_satchell,
        "vol_of_vol": result.vol_of_vol,
        "vol_range_compression": result.range_compression,
        "vol_intraday_range": result.intraday_range,
        "vol_close_open_gap": result.close_open_gap,
    }
