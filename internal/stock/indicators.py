"""
WEALTH Stock Analysis — Technical Indicators + Risk Metrics Engine
══════════════════════════════════════════════════════════════════

Computes indicators from yfinance OHLCV history (no manual input needed).
Closes the gap between TAC-9 judgment engine and live data.

Indicators:  RSI(14), MACD(12,26,9), SMA(20/50/200), EMA(12/26),
             Parabolic SAR, Bollinger Bands, ATR(14), OBV
Risk:        Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio,
             Annualized Return, Volatility, "Peace of Mind" Score

EUREKA: The TAC-9 engine was a judgment framework waiting for data.
        Now it has data. This is the bridge between raw prices and
        Arif's T1 swing trading strategy with peace-of-mind filtering.

DITEMPA BUKAN DIBERI — Indicators are forged on price, not hope.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════════════════


def compute_sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Simple Moving Average. Returns same-length list with None for pre-period."""
    result: List[Optional[float]] = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(prices[i - period + 1 : i + 1]) / period)
    return result


def compute_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """Exponential Moving Average."""
    if not prices:
        return []
    result: List[Optional[float]] = []
    multiplier = 2.0 / (period + 1)
    # Seed with SMA for first period
    sma = None
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            sma = sum(prices[:period]) / period
            result.append(sma)
        else:
            ema = (prices[i] - result[-1]) * multiplier + result[-1]  # type: ignore
            result.append(ema)
    return result


def compute_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index (Wilder's smoothing)."""
    if len(prices) < period + 1:
        return [None] * len(prices)

    result: List[Optional[float]] = [None] * period
    gains: List[float] = []
    losses: List[float] = []

    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    # Initial average gain/loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        result.append(round(rsi, 2))

        # Wilder's smoothing
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    return result


def compute_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Dict[str, List[Optional[float]]]:
    """MACD: returns {macd_line, signal_line, histogram}."""
    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)

    macd_line: List[Optional[float]] = []
    for i in range(len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line.append(ema_fast[i] - ema_slow[i])  # type: ignore
        else:
            macd_line.append(None)

    # Signal = EMA of MACD line
    valid_macd = [v for v in macd_line if v is not None]
    signal_line_raw = compute_ema(valid_macd, signal)
    signal_line: List[Optional[float]] = [None] * (
        len(macd_line) - len(signal_line_raw)
    ) + signal_line_raw  # type: ignore

    histogram: List[Optional[float]] = []
    for i in range(len(macd_line)):
        if (
            macd_line[i] is not None
            and i < len(signal_line)
            and signal_line[i] is not None
        ):
            histogram.append(macd_line[i] - signal_line[i])  # type: ignore
        else:
            histogram.append(None)

    return {"macd_line": macd_line, "signal_line": signal_line, "histogram": histogram}


def compute_bollinger(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> Dict[str, List[Optional[float]]]:
    """Bollinger Bands: returns {middle, upper, lower, width_pct}."""
    sma = compute_sma(prices, period)

    upper: List[Optional[float]] = []
    lower: List[Optional[float]] = []
    width: List[Optional[float]] = []

    for i in range(len(prices)):
        if i < period - 1:
            upper.append(None)
            lower.append(None)
            width.append(None)
        else:
            window = prices[i - period + 1 : i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std = math.sqrt(variance)
            mid = sma[i] or mean
            upper.append(round(mid + std_dev * std, 4))
            lower.append(round(mid - std_dev * std, 4))
            width.append(round((2 * std_dev * std / mid) * 100, 2) if mid > 0 else None)

    return {"middle": sma, "upper": upper, "lower": lower, "width_pct": width}


def compute_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> List[Optional[float]]:
    """Average True Range."""
    if len(highs) < period + 1:
        return [None] * len(highs)

    true_ranges: List[float] = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)

    result: List[Optional[float]] = [None] * period
    atr_val = sum(true_ranges[:period]) / period
    result.append(round(atr_val, 4))

    for i in range(period, len(true_ranges)):
        atr_val = (atr_val * (period - 1) + true_ranges[i]) / period
        result.append(round(atr_val, 4))

    return result


def compute_parabolic_sar(
    highs: List[float],
    lows: List[float],
    acceleration: float = 0.02,
    maximum: float = 0.20,
) -> List[Optional[float]]:
    """Parabolic SAR — the indicator Arif uses for T1 entry.

    Returns SAR values and a direction signal.
    """
    if len(highs) < 2:
        return [None] * len(highs)

    sar_values: List[Optional[float]] = [None]  # first value is undefined
    direction: List[str] = ["none"]  # "long" or "short"

    # Start: if 2nd close > 1st close → long, else short
    long = highs[1] > highs[0]
    ep = highs[1] if long else lows[1]  # extreme point
    af = acceleration
    sar = lows[0] if long else highs[0]

    for i in range(1, len(highs)):
        # Calculate SAR
        sar = sar + af * (ep - sar)

        # Ensure SAR is below price in long, above in short
        if long:
            if i >= 2:
                sar = (
                    min(sar, lows[i - 1], lows[i - 2])
                    if i >= 2
                    else min(sar, lows[i - 1])
                )
        else:
            if i >= 2:
                sar = (
                    max(sar, highs[i - 1], highs[i - 2])
                    if i >= 2
                    else max(sar, highs[i - 1])
                )

        sar_values.append(round(sar, 4))

        # Check reversal
        if long and lows[i] < sar:
            long = False
            sar = ep  # switch SAR to high
            ep = lows[i]
            af = acceleration
        elif not long and highs[i] > sar:
            long = True
            sar = ep
            ep = highs[i]
            af = acceleration
        else:
            # Update extreme point
            if long and highs[i] > ep:
                ep = highs[i]
                af = min(af + acceleration, maximum)
            elif not long and lows[i] < ep:
                ep = lows[i]
                af = min(af + acceleration, maximum)

        direction.append("long" if long else "short")

    return sar_values


def compute_obv(closes: List[float], volumes: List[int]) -> List[Optional[int]]:
    """On-Balance Volume."""
    if len(closes) < 2 or len(volumes) < 2:
        return [None] * len(closes)

    obv: List[Optional[int]] = [0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv.append((obv[-1] or 0) + volumes[i])
        elif closes[i] < closes[i - 1]:
            obv.append((obv[-1] or 0) - volumes[i])
        else:
            obv.append(obv[-1])
    return obv


# ═══════════════════════════════════════════════════════════════════════════
# RISK METRICS — "Peace of Mind" Engine
# ═══════════════════════════════════════════════════════════════════════════


def compute_returns(prices: List[float]) -> List[float]:
    """Daily log returns from price series."""
    if len(prices) < 2:
        return []
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def compute_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.03) -> float:
    """Annualized Sharpe Ratio. risk_free_rate defaults to 3% (Malaysia OPR ~3%)."""
    if len(returns) < 2:
        return 0.0
    avg = sum(returns) / len(returns)
    variance = (
        sum((r - avg) ** 2 for r in returns) / (len(returns) - 1)
        if len(returns) > 1
        else 0
    )
    std = math.sqrt(variance) if variance > 0 else 0
    if std == 0:
        return 0.0
    # Annualize: daily returns * sqrt(252)
    return ((avg * 252) - risk_free_rate) / (std * math.sqrt(252))


def compute_sortino_ratio(returns: List[float], risk_free_rate: float = 0.03) -> float:
    """Annualized Sortino Ratio — only penalizes downside volatility."""
    if len(returns) < 2:
        return 0.0
    avg = sum(returns) / len(returns)
    downside = [min(r, 0) ** 2 for r in returns]
    downside_std = math.sqrt(sum(downside) / len(downside)) if downside else 0
    if downside_std == 0:
        return 0.0 if avg <= 0 else 999.0  # no downside = perfect
    return ((avg * 252) - risk_free_rate) / (downside_std * math.sqrt(252))


def compute_max_drawdown(prices: List[float]) -> Dict[str, Any]:
    """Calculate maximum drawdown and recovery metrics."""
    if len(prices) < 2:
        return {
            "max_drawdown_pct": 0,
            "peak": None,
            "trough": None,
            "recovery_days": None,
            "current_drawdown_pct": 0,
        }

    peak = prices[0]
    max_dd = 0.0
    peak_idx = 0
    trough_idx = 0
    current_peak_idx = 0
    recovery_days = None

    for i in range(1, len(prices)):
        if prices[i] > peak:
            peak = prices[i]
            current_peak_idx = i
        dd = (peak - prices[i]) / peak
        if dd > max_dd:
            max_dd = dd
            peak_idx = current_peak_idx
            trough_idx = i

    # Current drawdown
    current_dd = (max(prices) - prices[-1]) / max(prices) if max(prices) > 0 else 0

    return {
        "max_drawdown_pct": round(max_dd * 100, 2),
        "peak_value": round(prices[peak_idx], 4) if peak_idx < len(prices) else None,
        "trough_value": round(prices[trough_idx], 4)
        if trough_idx < len(prices)
        else None,
        "current_drawdown_pct": round(current_dd * 100, 2),
    }


def compute_risk_pack(
    prices: List[float],
    volumes: Optional[List[int]] = None,
    risk_free_rate: float = 0.03,
) -> Dict[str, Any]:
    """Complete risk metrics pack — the "Peace of Mind" score."""
    if len(prices) < 20:
        return {
            "error": "Need at least 20 price points for risk metrics",
            "peace_of_mind": "INSUFFICIENT_DATA",
        }

    returns = compute_returns(prices)
    sharpe = compute_sharpe_ratio(returns, risk_free_rate)
    sortino = compute_sortino_ratio(returns, risk_free_rate)
    dd = compute_max_drawdown(prices)

    # Annualized return and volatility
    total_return = (prices[-1] / prices[0] - 1) if prices[0] > 0 else 0
    days = len(prices)
    ann_return = ((1 + total_return) ** (252 / days) - 1) if days > 0 else 0
    ann_vol = (
        (
            math.sqrt(
                sum((r - sum(returns) / len(returns)) ** 2 for r in returns)
                / (len(returns) - 1)
            )
            * math.sqrt(252)
        )
        if len(returns) > 1
        else 0
    )

    # Calmar Ratio = annualized return / max drawdown
    calmar = (
        abs(ann_return / (dd["max_drawdown_pct"] / 100))
        if dd["max_drawdown_pct"] > 0
        else (999 if ann_return > 0 else 0)
    )

    # "Peace of Mind" Score (0-100)
    # Based on: low drawdown, high Sortino, positive returns
    peace_score = 50.0  # neutral
    if sortino > 1.0:
        peace_score += 20
    elif sortino > 0.5:
        peace_score += 10
    elif sortino < 0:
        peace_score -= 15

    max_dd_pct = dd["max_drawdown_pct"]
    if max_dd_pct < 10:
        peace_score += 20  # very low drawdown
    elif max_dd_pct < 20:
        peace_score += 10
    elif max_dd_pct > 40:
        peace_score -= 25  # scary drawdown

    if ann_return > 0.10:
        peace_score += 10
    elif ann_return < -0.05:
        peace_score -= 15

    peace_score = max(0, min(100, peace_score))

    # Peace grade
    if peace_score >= 75:
        peace_grade = "EXCELLENT"
    elif peace_score >= 60:
        peace_grade = "GOOD"
    elif peace_score >= 40:
        peace_grade = "MODERATE"
    elif peace_score >= 25:
        peace_grade = "STRESSFUL"
    else:
        peace_grade = "HOSTILE"

    return {
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "calmar_ratio": round(calmar, 3),
        "max_drawdown_pct": dd["max_drawdown_pct"],
        "current_drawdown_pct": dd["current_drawdown_pct"],
        "annualized_return_pct": round(ann_return * 100, 2),
        "annualized_volatility_pct": round(ann_vol * 100, 2),
        "peace_of_mind_score": round(peace_score, 1),
        "peace_of_mind_grade": peace_grade,
        "risk_free_rate_pct": risk_free_rate * 100,
        "data_points": len(prices),
        "verdict": "SAFE_TO_STUDY" if peace_score >= 40 else "NEEDS_DATA",
    }


# ═══════════════════════════════════════════════════════════════════════════
# FULL TECHNICAL PACK — Computes everything from yfinance history
# ═══════════════════════════════════════════════════════════════════════════


def compute_technical_pack(
    symbol: str,
    period: str = "6mo",
) -> Dict[str, Any]:
    """Compute full technical indicators + risk metrics from yfinance history.

    This is the bridge: yfinance OHLCV → computed indicators → TAC-9 ready inputs.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed", "status": "ERROR"}

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            return {
                "error": f"No history for {symbol} (period={period})",
                "status": "NEEDS_DATA",
            }

        closes = [float(x) for x in df["Close"].tolist()]
        highs = [float(x) for x in df["High"].tolist()]
        lows = [float(x) for x in df["Low"].tolist()]
        volumes = [int(x) for x in df["Volume"].tolist()]
        dates = [str(d.date()) for d in df.index]

        if len(closes) < 14:
            return {
                "error": f"Only {len(closes)} data points — need at least 14",
                "status": "NEEDS_DATA",
            }

        # Compute indicators
        rsi_vals = compute_rsi(closes, 14)
        macd_data = compute_macd(closes)
        sma20 = compute_sma(closes, 20)
        sma50 = compute_sma(closes, 50) if len(closes) >= 50 else [None] * len(closes)
        sma200 = (
            compute_sma(closes, 200) if len(closes) >= 200 else [None] * len(closes)
        )
        bb = compute_bollinger(closes)
        atr_vals = compute_atr(highs, lows, closes)
        sar_vals = compute_parabolic_sar(highs, lows)
        obv_vals = compute_obv(closes, volumes)

        # Latest values
        latest_rsi = rsi_vals[-1] if rsi_vals[-1] is not None else None
        latest_macd = (
            macd_data["macd_line"][-1]
            if macd_data["macd_line"][-1] is not None
            else None
        )
        latest_signal = (
            macd_data["signal_line"][-1] if len(macd_data["signal_line"]) > 0 else None
        )
        latest_hist = (
            macd_data["histogram"][-1] if len(macd_data["histogram"]) > 0 else None
        )
        latest_sar = sar_vals[-1] if sar_vals[-1] is not None else None

        # Direction signals
        macd_signal_str = (
            "bullish"
            if (latest_hist and latest_hist > 0)
            else "bearish"
            if latest_hist
            else "neutral"
        )
        sar_position_str = (
            "below"
            if (latest_sar and closes[-1] > latest_sar)
            else "above"
            if latest_sar
            else "neutral"
        )
        price_above_50ma = (
            bool(sma50[-1] and closes[-1] > sma50[-1]) if sma50[-1] else None
        )
        price_above_200ma = (
            bool(sma200[-1] and closes[-1] > sma200[-1])
            if len(sma200) > 0 and sma200[-1]
            else None
        )
        ma50_above_ma200 = bool(
            sma50[-1] and len(sma200) > 0 and sma200[-1] and sma50[-1] > sma200[-1]
        )

        # Risk pack
        risk = compute_risk_pack(closes, volumes)

        # Trend quality
        if latest_rsi:
            if latest_rsi > 70:
                rsi_zone = "overbought"
            elif latest_rsi < 30:
                rsi_zone = "oversold"
            else:
                rsi_zone = "neutral"
        else:
            rsi_zone = "unknown"

        bb_position = "middle"
        if bb["upper"][-1] and closes[-1] >= bb["upper"][-1]:
            bb_position = "upper_band"
        elif bb["lower"][-1] and closes[-1] <= bb["lower"][-1]:
            bb_position = "lower_band"

        atr_pct = (
            round((atr_vals[-1] / closes[-1]) * 100, 2)
            if (atr_vals[-1] and closes[-1])
            else None
        )

        return {
            "status": "OK",
            "verdict": "SAFE_TO_STUDY",
            "symbol": symbol,
            "period": period,
            "data_points": len(closes),
            "latest_price": round(closes[-1], 4),
            "latest_date": dates[-1] if dates else None,
            "indicators": {
                "rsi": {"value": latest_rsi, "zone": rsi_zone, "period": 14},
                "macd": {
                    "macd_line": round(latest_macd, 6) if latest_macd else None,
                    "signal_line": round(latest_signal, 6) if latest_signal else None,
                    "histogram": round(latest_hist, 6) if latest_hist else None,
                    "signal": macd_signal_str,
                },
                "sma": {
                    "sma20": round(sma20[-1], 4) if sma20[-1] else None,
                    "sma50": round(sma50[-1], 4) if sma50[-1] else None,
                    "sma200": round(sma200[-1], 4)
                    if (len(sma200) > 0 and sma200[-1])
                    else None,
                    "price_above_50ma": price_above_50ma,
                    "price_above_200ma": price_above_200ma,
                    "ma50_above_ma200": ma50_above_ma200,
                },
                "bollinger": {
                    "upper": round(bb["upper"][-1], 4) if bb["upper"][-1] else None,
                    "middle": round(bb["middle"][-1], 4) if bb["middle"][-1] else None,
                    "lower": round(bb["lower"][-1], 4) if bb["lower"][-1] else None,
                    "width_pct": bb["width_pct"][-1],
                    "position": bb_position,
                },
                "parabolic_sar": {
                    "value": latest_sar,
                    "position": sar_position_str,
                },
                "atr": {
                    "value": atr_vals[-1],
                    "pct": atr_pct,
                },
                "obv": {
                    "latest": obv_vals[-1] if obv_vals[-1] is not None else None,
                },
            },
            "risk_metrics": risk,
            "recommendation_only": True,
            "final_authority": "Arif",
            "note": "RSI/MACD/SAR are SECONDARY confirmations. Use TAC-9 tiers for primary decisions.",
        }

    except Exception as e:
        return {"error": str(e), "status": "ERROR", "symbol": symbol}
