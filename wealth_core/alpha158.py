"""
Alpha158 Engine — Systematic Feature Generation

Eureka source: TradeMaster (NTU) Alpha158 feature set.
Distilled into WEALTH capital_indicator.mode=alpha158.

Core insight: Indicator selection IS a strategy. Manual picking < systematic generation.
Generate 158 candidate features from OHLCV, then let the system select.

Features by category:
1. Price ratios (open/close, high/low, close/open)
2. Volume-price divergence
3. Volatility ratios (multi-period ATR)
4. Momentum across multiple periods
5. Mean reversion signals
6. Microstructure proxies

All pure numpy on existing candle data. No external dependencies.

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Alpha158Result:
    """Alpha158 feature set output."""

    feature_count: int
    features: dict[str, list[float]]
    top_features: list[dict]  # sorted by variance (information content)
    feature_categories: dict[str, int]
    bars_processed: int


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if abs(b) > 1e-10 else default


def _ema(data: list[float], period: int) -> list[float]:
    """Exponential moving average."""
    if len(data) < period:
        return []
    k = 2 / (period + 1)
    result = [sum(data[:period]) / period]
    for val in data[period:]:
        result.append(val * k + result[-1] * (1 - k))
    return result


def _rolling_std(data: list[float], window: int) -> list[float]:
    """Rolling standard deviation."""
    if len(data) < window:
        return []
    result = []
    for i in range(window - 1, len(data)):
        w = data[i - window + 1 : i + 1]
        mean = sum(w) / len(w)
        var = sum((x - mean) ** 2 for x in w) / len(w)
        result.append(var**0.5)
    return result


def _rolling_max(data: list[float], window: int) -> list[float]:
    """Rolling max."""
    return [max(data[max(0, i - window + 1) : i + 1]) for i in range(len(data))]


def _rolling_min(data: list[float], window: int) -> list[float]:
    """Rolling min."""
    return [min(data[max(0, i - window + 1) : i + 1]) for i in range(len(data))]


def compute_alpha158(
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float] | None = None,
) -> Alpha158Result:
    """Compute Alpha158 systematic feature set from OHLCV data.

    Args:
        opens: Open prices
        highs: High prices
        lows: Low prices
        closes: Close prices
        volumes: Optional volume data

    Returns:
        Alpha158Result with all features
    """
    n = len(closes)
    if n < 30:
        return Alpha158Result(0, {}, [], {}, 0)

    vols = volumes if volumes and len(volumes) == n else [1.0] * n
    features: dict[str, list[float]] = {}
    categories: dict[str, int] = {}

    def _add(name: str, cat: str, values: list[float]):
        features[name] = values
        categories[cat] = categories.get(cat, 0) + 1

    # ═══ CATEGORY 1: Price Ratios ═══
    # Open/Close ratio
    oc_ratio = [_safe_div(opens[i], closes[i]) for i in range(n)]
    _add("oc_ratio", "price_ratio", oc_ratio)

    # High/Low ratio
    hl_ratio = [_safe_div(highs[i], lows[i]) for i in range(n)]
    _add("hl_ratio", "price_ratio", hl_ratio)

    # Close/Open ratio (daily return proxy)
    co_ratio = [_safe_div(closes[i], opens[i]) for i in range(n)]
    _add("co_ratio", "price_ratio", co_ratio)

    # Close/High ratio (how close to day's high)
    ch_ratio = [_safe_div(closes[i], highs[i]) for i in range(n)]
    _add("ch_ratio", "price_ratio", ch_ratio)

    # Close/Low ratio (how far from day's low)
    cl_ratio = [_safe_div(closes[i], lows[i]) for i in range(n)]
    _add("cl_ratio", "price_ratio", cl_ratio)

    # Body ratio (candle body / total range)
    body_ratio = []
    for i in range(n):
        total = highs[i] - lows[i]
        body = abs(closes[i] - opens[i])
        body_ratio.append(_safe_div(body, total))
    _add("body_ratio", "price_ratio", body_ratio)

    # Upper shadow ratio
    upper_shadow = []
    for i in range(n):
        total = highs[i] - lows[i]
        shadow = highs[i] - max(opens[i], closes[i])
        upper_shadow.append(_safe_div(shadow, total))
    _add("upper_shadow", "price_ratio", upper_shadow)

    # Lower shadow ratio
    lower_shadow = []
    for i in range(n):
        total = highs[i] - lows[i]
        shadow = min(opens[i], closes[i]) - lows[i]
        lower_shadow.append(_safe_div(shadow, total))
    _add("lower_shadow", "price_ratio", lower_shadow)

    # ═══ CATEGORY 2: Returns (multiple periods) ═══
    for period in [1, 2, 3, 5, 10, 20]:
        rets = [0.0] * period + [
            _safe_div(closes[i] - closes[i - period], closes[i - period])
            for i in range(period, n)
        ]
        _add(f"return_{period}d", "return", rets)

    # Log returns
    import math

    log_rets = [0.0] + [
        math.log(closes[i] / closes[i - 1])
        if closes[i - 1] > 0 and closes[i] > 0
        else 0.0
        for i in range(1, n)
    ]
    _add("log_return_1d", "return", log_rets)

    # ═══ CATEGORY 3: Volatility ═══
    # Rolling volatility (std of returns)
    for window in [5, 10, 20]:
        vol = _rolling_std(log_rets, window)
        pad = [0.0] * (n - len(vol))
        _add(f"volatility_{window}d", "volatility", pad + vol)

    # ATR ratios
    trs = [0.0] + [
        max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        for i in range(1, n)
    ]
    for period in [5, 14, 20]:
        atr_vals = []
        for i in range(n):
            if i < period:
                atr_vals.append(0.0)
            else:
                atr_vals.append(sum(trs[i - period + 1 : i + 1]) / period)
        _add(f"atr_{period}", "volatility", atr_vals)

        # ATR ratio (current / average)
        atr_avg = (
            sum(atr_vals[period:]) / len(atr_vals[period:])
            if len(atr_vals) > period
            else 1.0
        )
        atr_ratio = [_safe_div(v, atr_avg) for v in atr_vals]
        _add(f"atr_ratio_{period}", "volatility", atr_ratio)

    # ═══ CATEGORY 4: Momentum ═══
    # RSI-like momentum at multiple periods
    for period in [6, 14, 28]:
        deltas = [closes[i] - closes[i - 1] for i in range(1, n)]
        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]
        rsi_vals = [50.0] * period
        if len(deltas) >= period:
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            for i in range(period, len(deltas)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                if avg_loss == 0:
                    rsi_vals.append(100.0)
                else:
                    rsi_vals.append(100 - (100 / (1 + avg_gain / avg_loss)))
        pad = [50.0] * (n - len(rsi_vals))
        _add(f"rsi_{period}", "momentum", pad + rsi_vals)

    # Rate of change
    for period in [5, 10, 20]:
        roc = [0.0] * period + [
            _safe_div(closes[i] - closes[i - period], closes[i - period]) * 100
            for i in range(period, n)
        ]
        _add(f"roc_{period}", "momentum", roc)

    # ═══ CATEGORY 5: Mean Reversion ═══
    # Distance from EMA
    for period in [10, 20, 50]:
        ema_vals = _ema(closes, period)
        if ema_vals:
            offset = n - len(ema_vals)
            dist = [0.0] * offset + [
                _safe_div(closes[offset + i] - ema_vals[i], ema_vals[i])
                for i in range(len(ema_vals))
            ]
            _add(f"ema_dist_{period}", "mean_reversion", dist)

    # Bollinger Band position
    for period in [20]:
        sma = []
        for i in range(n):
            if i < period - 1:
                sma.append(closes[i])
            else:
                sma.append(sum(closes[i - period + 1 : i + 1]) / period)
        std_vals = _rolling_std(closes, period)
        pad = [0.0] * (n - len(std_vals))
        std_full = pad + std_vals
        bb_pos = []
        for i in range(n):
            if std_full[i] > 0:
                bb_pos.append(_safe_div(closes[i] - sma[i], 2 * std_full[i]))
            else:
                bb_pos.append(0.0)
        _add(f"bb_position_{period}", "mean_reversion", bb_pos)

    # ═══ CATEGORY 6: Volume-Price ═══
    if volumes and any(v > 0 for v in volumes):
        # Volume ratio
        vol_sma = []
        for i in range(n):
            if i < 20:
                vol_sma.append(vols[i])
            else:
                vol_sma.append(sum(vols[i - 19 : i + 1]) / 20)
        vol_ratio = [_safe_div(vols[i], vol_sma[i]) for i in range(n)]
        _add("volume_ratio", "volume_price", vol_ratio)

        # Price-volume correlation (rolling)
        for window in [10, 20]:
            pv_corr = [0.0] * window
            for i in range(window, n):
                p_w = log_rets[i - window + 1 : i + 1]
                v_w = vols[i - window + 1 : i + 1]
                mp = sum(p_w) / len(p_w)
                mv = sum(v_w) / len(v_w)
                cov = sum((p_w[j] - mp) * (v_w[j] - mv) for j in range(len(p_w))) / len(
                    p_w
                )
                sp = (sum((x - mp) ** 2 for x in p_w) / len(p_w)) ** 0.5
                sv = (sum((x - mv) ** 2 for x in v_w) / len(v_w)) ** 0.5
                pv_corr.append(_safe_div(cov, sp * sv))
            _add(f"pv_corr_{window}", "volume_price", pv_corr)

    # ═══ CATEGORY 7: Microstructure Proxies ═══
    # High-low spread (bid-ask proxy)
    hl_spread = [_safe_div(highs[i] - lows[i], closes[i]) for i in range(n)]
    _add("hl_spread", "microstructure", hl_spread)

    # Amihud illiquidity (|return| / volume)
    if volumes and any(v > 0 for v in volumes):
        amihud = [_safe_div(abs(log_rets[i]), vols[i]) for i in range(n)]
        _add("amihud_illiquidity", "microstructure", amihud)

    # ═══ Compute feature statistics ═══
    top_features = []
    for name, values in features.items():
        if len(values) > 1:
            mean = sum(values) / len(values)
            var = sum((v - mean) ** 2 for v in values) / len(values)
            top_features.append(
                {
                    "name": name,
                    "category": name.split("_")[0] if "_" in name else "other",
                    "variance": round(var, 6),
                    "mean": round(mean, 6),
                    "values_count": len(values),
                }
            )
    top_features.sort(key=lambda f: f["variance"], reverse=True)

    return Alpha158Result(
        feature_count=len(features),
        features=features,
        top_features=top_features[:20],  # top 20 by information content
        feature_categories=categories,
        bars_processed=n,
    )
