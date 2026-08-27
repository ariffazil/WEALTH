"""
WEALTH capital_indicator — Technical analysis indicators — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality



def register_indicator(mcp):
    """Register the indicator tool on the given FastMCP instance."""
# 9. capital_indicator — Technical analysis indicators (FORGED 2026-08-09)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="capital_indicator",
    output_schema=WEALTH_OUTPUT_SCHEMA,
    description=(
        "Compute technical analysis indicators for any yfinance symbol. "
        "Indicators: ema, sma, rsi, macd, bb (Bollinger Bands), psar (Parabolic SAR), "
        "atr, adx. Pure numpy computation — no external TA library needed. "
        "SIDE EFFECT: writes a vault receipt."
    ),
    tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
)
async def capital_indicator(
    symbol: str = "GC=F",
    indicator: str = "rsi",
    period: int = 14,
    interval: str = "1d",
    lookback: str = "6mo",
    session_id: str | None = None,
    trace_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    import numpy as np
    import yfinance as yf

    sym = symbol.upper()
    ind = indicator.lower().strip()

    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period=lookback, interval=interval)
    except Exception as e:
        return wrap_result(
            tool_name="capital_indicator",
            domain="market",
            result={
                "status": "ERROR",
                "error_code": "FETCH_FAILED",
                "message": str(e)[:200],
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            session_id=session_id,
            actor_id=actor_id,
        )
    if hist.empty:
        return wrap_result(
            tool_name="capital_indicator",
            domain="market",
            result={
                "status": "ERROR",
                "error_code": "NO_DATA",
                "message": f"No price data for {sym}",
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            session_id=session_id,
            actor_id=actor_id,
        )

    close = hist["Close"].values.astype(np.float64)
    high = hist["High"].values.astype(np.float64) if "High" in hist else close
    low = hist["Low"].values.astype(np.float64) if "Low" in hist else close
    n = len(close)
    p = int(period)

    result: dict = {
        "symbol": sym,
        "indicator": indicator.upper(),
        "period": p,
        "interval": interval,
        "data_points": n,
    }

    # ── EMA ──
    if ind == "ema":
        alpha = 2.0 / (p + 1)
        ema_vals = np.zeros(n)
        ema_vals[0] = float(close[0])
        for i in range(1, n):
            ema_vals[i] = alpha * close[i] + (1 - alpha) * ema_vals[i - 1]
        result["current"] = round(float(ema_vals[-1]), 4)
        result["current_price"] = round(float(close[-1]), 4)
        result["series_last_5"] = [round(float(v), 4) for v in ema_vals[-5:]]

    # ── SMA ──
    elif ind == "sma":
        sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
        result["current"] = round(float(sma_vals[-1]), 4)
        result["current_price"] = round(float(close[-1]), 4)
        if len(sma_vals) >= 5:
            result["series_last_5"] = [round(float(v), 4) for v in sma_vals[-5:]]

    # ── RSI ──
    elif ind == "rsi":
        deltas = np.diff(close)
        gain = np.where(deltas > 0, deltas, 0.0)
        loss = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)
        avg_gain[p] = np.mean(gain[:p])
        avg_loss[p] = np.mean(loss[:p])
        for i in range(p + 1, n):
            avg_gain[i] = (avg_gain[i - 1] * (p - 1) + gain[i - 1]) / p
            avg_loss[i] = (avg_loss[i - 1] * (p - 1) + loss[i - 1]) / p
        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi_vals = 100.0 - (100.0 / (1.0 + rs))
        result["current"] = round(float(rsi_vals[-1]), 2)
        result["overbought"] = result["current"] > 70
        result["oversold"] = result["current"] < 30
        result["series_last_5"] = [round(float(v), 2) for v in rsi_vals[-5:]]

    # ── MACD ──
    elif ind == "macd":
        # EMA of close: fast=12, slow=26, signal=9 by default
        fast_p, slow_p, sig_p = 12, 26, 9
        if p != 14:  # user override via period param
            fast_p = p
            slow_p = p * 2
            sig_p = max(5, p // 2)

        def _ema(series, span):
            alpha = 2.0 / (span + 1)
            out = np.zeros(len(series))
            out[0] = float(series[0])
            for i in range(1, len(series)):
                out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
            return out

        ema_fast = _ema(close, fast_p)
        ema_slow = _ema(close, slow_p)
        macd_line = ema_fast - ema_slow
        signal_line = _ema(macd_line, sig_p)
        histogram = macd_line - signal_line
        result["macd_line"] = round(float(macd_line[-1]), 6)
        result["signal_line"] = round(float(signal_line[-1]), 6)
        result["histogram"] = round(float(histogram[-1]), 6)
        result["bullish"] = bool(macd_line[-1] > signal_line[-1])

    # ── Bollinger Bands ──
    elif ind in ("bb", "bollinger"):
        sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
        rolling_std = np.array(
            [np.std(close[i : i + p], ddof=0) for i in range(n - p + 1)]
        )
        upper = sma_vals + 2 * rolling_std
        lower = sma_vals - 2 * rolling_std
        result["sma"] = round(float(sma_vals[-1]), 4)
        result["upper"] = round(float(upper[-1]), 4)
        result["lower"] = round(float(lower[-1]), 4)
        result["current_price"] = round(float(close[-1]), 4)
        result["bandwidth_pct"] = round(
            float((upper[-1] - lower[-1]) / sma_vals[-1] * 100), 2
        )
        result["price_position_pct"] = round(
            float((close[-1] - lower[-1]) / (upper[-1] - lower[-1]) * 100), 1
        )

    # ── Parabolic SAR ──
    elif ind in ("psar", "parabolic_sar", "sar"):
        af_init = 0.02
        af_max = 0.20
        af_step = 0.02
        psar = np.zeros(n)
        # Start: first bar determines trend
        trend_up = True
        ep = float(high[0])  # extreme point
        af = af_init
        psar[0] = float(low[0])
        for i in range(1, n):
            psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
            if trend_up:
                psar[i] = min(psar[i], float(low[i - 1]), float(low[max(0, i - 2)]))
                if float(high[i]) > ep:
                    ep = float(high[i])
                    af = min(af + af_step, af_max)
                if float(low[i]) < psar[i]:
                    trend_up = False
                    psar[i] = ep
                    ep = float(low[i])
                    af = af_init
            else:
                psar[i] = max(
                    psar[i], float(high[i - 1]), float(high[max(0, i - 2)])
                )
                if float(low[i]) < ep:
                    ep = float(low[i])
                    af = min(af + af_step, af_max)
                if float(high[i]) > psar[i]:
                    trend_up = True
                    psar[i] = ep
                    ep = float(high[i])
                    af = af_init
        result["current"] = round(float(psar[-1]), 4)
        result["current_price"] = round(float(close[-1]), 4)
        result["trend"] = "BULL" if close[-1] > psar[-1] else "BEAR"
        result["psar_below_price"] = bool(close[-1] > psar[-1])

    # ── ATR ──
    elif ind == "atr":
        tr = np.zeros(n)
        for i in range(1, n):
            tr[i] = max(
                float(high[i]) - float(low[i]),
                abs(float(high[i]) - float(close[i - 1])),
                abs(float(low[i]) - float(close[i - 1])),
            )
        atr_vals = np.zeros(n)
        atr_vals[p] = np.mean(tr[1 : p + 1])
        for i in range(p + 1, n):
            atr_vals[i] = (atr_vals[i - 1] * (p - 1) + tr[i]) / p
        result["current"] = round(float(atr_vals[-1]), 4)
        result["current_price"] = round(float(close[-1]), 4)
        result["atr_pct"] = round(float(atr_vals[-1] / close[-1] * 100), 2)

    # ── ADX ──
    elif ind == "adx":
        tr = np.zeros(n)
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        for i in range(1, n):
            h_diff = float(high[i]) - float(high[i - 1])
            l_diff = float(low[i - 1]) - float(low[i])
            plus_dm[i] = h_diff if h_diff > l_diff and h_diff > 0 else 0.0
            minus_dm[i] = l_diff if l_diff > h_diff and l_diff > 0 else 0.0
            tr[i] = max(
                float(high[i]) - float(low[i]),
                abs(float(high[i]) - float(close[i - 1])),
                abs(float(low[i]) - float(close[i - 1])),
            )
        atr_smooth = np.zeros(n)
        atr_smooth[p] = np.mean(tr[1 : p + 1])
        plus_di_smooth = np.zeros(n)
        plus_di_smooth[p] = (
            100 * np.mean(plus_dm[1 : p + 1]) / max(atr_smooth[p], 1e-10)
        )
        minus_di_smooth = np.zeros(n)
        minus_di_smooth[p] = (
            100 * np.mean(minus_dm[1 : p + 1]) / max(atr_smooth[p], 1e-10)
        )
        for i in range(p + 1, n):
            atr_smooth[i] = (atr_smooth[i - 1] * (p - 1) + tr[i]) / p
            plus_di_smooth[i] = (
                plus_di_smooth[i - 1] * (p - 1)
                + 100 * plus_dm[i] / max(atr_smooth[i], 1e-10)
            ) / p
            minus_di_smooth[i] = (
                minus_di_smooth[i - 1] * (p - 1)
                + 100 * minus_dm[i] / max(atr_smooth[i], 1e-10)
            ) / p
        dx = (
            100
            * np.abs(plus_di_smooth - minus_di_smooth)
            / np.maximum(plus_di_smooth + minus_di_smooth, 1e-10)
        )
        adx_vals = np.zeros(n)
        adx_vals[2 * p] = np.mean(dx[p : 2 * p])
        for i in range(2 * p + 1, n):
            adx_vals[i] = (adx_vals[i - 1] * (p - 1) + dx[i]) / p
        result["current"] = round(float(adx_vals[-1]), 2)
        result["plus_di"] = round(float(plus_di_smooth[-1]), 2)
        result["minus_di"] = round(float(minus_di_smooth[-1]), 2)
        result["trending"] = bool(adx_vals[-1] > 25)

    # ── TRAJECTORY / TEMPORAL — multi-indicator state snapshot ──
    elif ind in ("trajectory", "temporal", "state", "full"):
        # Compute all key indicators for temporal awareness
        out: dict = {
            "symbol": sym,
            "mode": "temporal",
            "interval": interval,
            "data_points": n,
            "current_price": round(float(close[-1]), 2),
        }

        # --- RSI ---
        deltas = np.diff(close)
        gain = np.where(deltas > 0, deltas, 0.0)
        loss = np.where(deltas < 0, -deltas, 0.0)
        avg_g = np.zeros(n)
        avg_l = np.zeros(n)
        avg_g[p] = np.mean(gain[:p])
        avg_l[p] = np.mean(loss[:p])
        for i in range(p + 1, n):
            avg_g[i] = (avg_g[i - 1] * (p - 1) + gain[i - 1]) / p
            avg_l[i] = (avg_l[i - 1] * (p - 1) + loss[i - 1]) / p
        rs_vals = avg_g / np.where(avg_l == 0, 1e-10, avg_l)
        rsi_all = 100.0 - (100.0 / (1.0 + rs_vals))
        out["rsi"] = {
            "current": round(float(rsi_all[-1]), 1),
            "signal": "overbought"
            if rsi_all[-1] > 70
            else ("oversold" if rsi_all[-1] < 30 else "neutral"),
            "trend_5": "rising" if rsi_all[-1] > rsi_all[-6] else "falling",
            "roc_5": round(float(rsi_all[-1] - rsi_all[-6]), 1),
        }

        # --- MACD ---
        def _e(series, span):
            a = 2.0 / (span + 1)
            o = np.zeros(len(series))
            o[0] = float(series[0])
            for i in range(1, len(series)):
                o[i] = a * series[i] + (1 - a) * o[i - 1]
            return o

        macd_line = _e(close, 12) - _e(close, 26)
        signal_l = _e(macd_line, 9)
        hist = macd_line - signal_l
        out["macd"] = {
            "line": round(float(macd_line[-1]), 4),
            "signal": round(float(signal_l[-1]), 4),
            "histogram": round(float(hist[-1]), 4),
            "bullish": bool(macd_line[-1] > signal_l[-1]),
            "cross_5": "bullish_cross"
            if macd_line[-1] > signal_l[-1] and macd_line[-6] <= signal_l[-6]
            else (
                "bearish_cross"
                if macd_line[-1] < signal_l[-1] and macd_line[-6] >= signal_l[-6]
                else "none"
            ),
        }

        # --- Bollinger Bands ---
        sma_vals = np.convolve(close, np.ones(p) / p, mode="valid")
        rstd = np.array(
            [np.std(close[i : i + p], ddof=0) for i in range(n - p + 1)]
        )
        bb_upper = sma_vals + 2 * rstd
        bb_lower = sma_vals - 2 * rstd
        bb_pos = (close[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]) * 100
        bb_width = (bb_upper[-1] - bb_lower[-1]) / sma_vals[-1] * 100
        out["bollinger"] = {
            "position_pct": round(float(bb_pos), 0),
            "bandwidth": round(float(bb_width), 1),
            "signal": "breakout_above"
            if bb_pos > 100
            else ("breakout_below" if bb_pos < 0 else "inside"),
            "squeeze": bool(bb_width < 5),
        }

        # --- EMA alignment (regime) ---
        e20 = _e(close, 20)
        e50 = _e(close, 50)
        e200_long = _e(
            np.concatenate([np.full(max(0, 200 - n), close[0]), close]), 200
        )
        if len(e200_long) > n:
            e200_long = e200_long[-n:]
        trend = "SIDEWAYS"
        if e20[-1] > e50[-1] > e200_long[-1]:
            trend = "UPTREND"
        elif e20[-1] < e50[-1] < e200_long[-1]:
            trend = "DOWNTREND"
        out["regime"] = {
            "trend": trend,
            "ema20": round(float(e20[-1]), 2),
            "ema50": round(float(e50[-1]), 2),
            "ema200": round(float(e200_long[-1]), 2),
            "strength_pct": round(
                float(abs(e20[-1] - e200_long[-1]) / e200_long[-1] * 100), 2
            ),
        }

        # --- PSAR ---
        af_i = 0.02
        af_m = 0.20
        af_s = 0.02
        psar = np.zeros(n)
        t_up = True
        ep_v = float(high[0])
        af_v = af_i
        psar[0] = float(low[0])
        for i in range(1, n):
            psar[i] = psar[i - 1] + af_v * (ep_v - psar[i - 1])
            if t_up:
                psar[i] = min(psar[i], float(low[i - 1]), float(low[max(0, i - 2)]))
                if float(high[i]) > ep_v:
                    ep_v = float(high[i])
                    af_v = min(af_v + af_s, af_m)
                if float(low[i]) < psar[i]:
                    t_up = False
                    psar[i] = ep_v
                    ep_v = float(low[i])
                    af_v = af_i
            else:
                psar[i] = max(
                    psar[i], float(high[i - 1]), float(high[max(0, i - 2)])
                )
                if float(low[i]) < ep_v:
                    ep_v = float(low[i])
                    af_v = min(af_v + af_s, af_m)
                if float(high[i]) > psar[i]:
                    t_up = True
                    psar[i] = ep_v
                    ep_v = float(high[i])
                    af_v = af_i
        out["psar"] = {
            "value": round(float(psar[-1]), 2),
            "trend": "BULL" if close[-1] > psar[-1] else "BEAR",
            "distance_pct": round(
                float(abs(close[-1] - psar[-1]) / close[-1] * 100), 2
            ),
        }

        # --- ATR ---
        tr_arr = np.zeros(n)
        for i in range(1, n):
            tr_arr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        atr_s = np.zeros(n)
        atr_s[p] = np.mean(tr_arr[1 : p + 1])
        for i in range(p + 1, n):
            atr_s[i] = (atr_s[i - 1] * (p - 1) + tr_arr[i]) / p
        atr_now = float(atr_s[-1])
        atr_5_ago = float(atr_s[max(0, n - 6)])
        out["atr"] = {
            "current": round(atr_now, 2),
            "pct_of_price": round(atr_now / close[-1] * 100, 2),
            "expanding": bool(atr_now > atr_5_ago * 1.1),
            "contracting": bool(atr_now < atr_5_ago * 0.9),
        }

        # --- ADX ---
        px_dm = np.zeros(n)
        nx_dm = np.zeros(n)
        for i in range(1, n):
            hd = float(high[i]) - float(high[i - 1])
            ld = float(low[i - 1]) - float(low[i])
            px_dm[i] = hd if hd > ld and hd > 0 else 0.0
            nx_dm[i] = ld if ld > hd and ld > 0 else 0.0
        atr_adx = np.zeros(n)
        atr_adx[p] = np.mean(tr_arr[1 : p + 1])
        pdi = np.zeros(n)
        pdi[p] = 100 * np.mean(px_dm[1 : p + 1]) / max(atr_adx[p], 1e-10)
        ndi = np.zeros(n)
        ndi[p] = 100 * np.mean(nx_dm[1 : p + 1]) / max(atr_adx[p], 1e-10)
        for i in range(p + 1, n):
            atr_adx[i] = (atr_adx[i - 1] * (p - 1) + tr_arr[i]) / p
            pdi[i] = (
                pdi[i - 1] * (p - 1) + 100 * px_dm[i] / max(atr_adx[i], 1e-10)
            ) / p
            ndi[i] = (
                ndi[i - 1] * (p - 1) + 100 * nx_dm[i] / max(atr_adx[i], 1e-10)
            ) / p
        dx_v = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-10)
        adx_all = np.zeros(n)
        adx_all[2 * p] = np.mean(dx_v[p : 2 * p])
        for i in range(2 * p + 1, n):
            adx_all[i] = (adx_all[i - 1] * (p - 1) + dx_v[i]) / p
        out["adx"] = {
            "current": round(float(adx_all[-1]), 1),
            "plus_di": round(float(pdi[-1]), 1),
            "minus_di": round(float(ndi[-1]), 1),
            "trending": bool(adx_all[-1] > 25),
            "strong_trend": bool(adx_all[-1] > 40),
        }

        # --- Signal summary ---
        signals = []
        if out["regime"]["trend"] == "UPTREND" and out["adx"]["trending"]:
            signals.append("BULL_TREND")
        elif out["regime"]["trend"] == "DOWNTREND" and out["adx"]["trending"]:
            signals.append("BEAR_TREND")
        if out["rsi"]["signal"] == "overbought":
            signals.append("RSI_OVERBOUGHT")
        elif out["rsi"]["signal"] == "oversold":
            signals.append("RSI_OVERSOLD")
        if out["bollinger"]["signal"] == "breakout_above":
            signals.append("BB_BREAKOUT_UP")
        elif out["bollinger"]["signal"] == "breakout_below":
            signals.append("BB_BREAKOUT_DOWN")
        if out["bollinger"]["squeeze"]:
            signals.append("BB_SQUEEZE")
        if out["macd"]["bullish"]:
            signals.append("MACD_BULLISH")
        else:
            signals.append("MACD_BEARISH")
        if out["psar"]["trend"] == "BULL":
            signals.append("PSAR_BULL")
        else:
            signals.append("PSAR_BEAR")
        if out["atr"]["expanding"]:
            signals.append("VOL_EXPANDING")
        elif out["atr"]["contracting"]:
            signals.append("VOL_CONTRACTING")

        # Confluence score: count how many agree with trend direction
        bull_align = sum(
            1
            for s in signals
            if "BULL" in s
            or s in ("RSI_OVERSOLD", "BB_BREAKOUT_UP", "MACD_BULLISH", "PSAR_BULL")
        )
        bear_align = sum(
            1
            for s in signals
            if "BEAR" in s
            or s
            in ("RSI_OVERBOUGHT", "BB_BREAKOUT_DOWN", "MACD_BEARISH", "PSAR_BEAR")
        )
        total = max(len(signals), 1)
        out["confluence"] = {
            "bull_signals": bull_align,
            "bear_signals": bear_align,
            "total": total,
            "bull_pct": round(bull_align / total * 100),
            "verdict": "STRONG_BULL"
            if bull_align >= total * 0.7
            else (
                "STRONG_BEAR"
                if bear_align >= total * 0.7
                else (
                    "BULL_LEAN"
                    if bull_align > bear_align
                    else ("BEAR_LEAN" if bear_align > bull_align else "MIXED")
                )
            ),
        }
        out["signals"] = signals

        result = out

    # ── ALPHA158 — TradeMaster distillation (2026-08-18) ──
    elif ind == "alpha158":
        import sys as _sys

        _wealth_root = "/root/WEALTH"
        if _wealth_root not in _sys.path:
            _sys.path.insert(0, _wealth_root)

        from wealth_core.alpha158 import compute_alpha158

        opens = hist["Open"].values.astype(np.float64) if "Open" in hist else close
        volumes = (
            hist["Volume"].values.astype(np.float64) if "Volume" in hist else None
        )

        alpha = compute_alpha158(
            opens.tolist(),
            high.tolist(),
            low.tolist(),
            close.tolist(),
            volumes.tolist() if volumes is not None else None,
        )
        result = {
            "symbol": sym,
            "indicator": "ALPHA158",
            "feature_count": alpha.feature_count,
            "categories": alpha.feature_categories,
            "top_features": alpha.top_features[:10],
            "bars_processed": alpha.bars_processed,
            "framework": "Alpha158 (TradeMaster distillation)",
        }

    else:
        valid = "ema, sma, rsi, macd, bb, psar, atr, adx"
        return wrap_result(
            tool_name="capital_indicator",
            domain="market",
            result={
                "status": "ERROR",
                "error_code": "UNKNOWN_INDICATOR",
                "message": f"Unknown '{indicator}'. Valid: {valid}",
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            session_id=session_id,
            actor_id=actor_id,
        )

    return wrap_result(
        tool_name="capital_indicator",
        domain="market",
        result=result,
        epistemic_tag=EpistemicTag.DERIVED,
        evidence_quality=EvidenceQuality.OBSERVED,
        source_attribution=[f"yfinance:{sym}"],
        session_id=session_id,
        actor_id=actor_id,
    )


