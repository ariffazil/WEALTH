"""
WEALTH capital_entry_plan — S/R-aware entry/stop/target — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality


def register_entry_plan(mcp):
    """Register the entry_plan tool on the given FastMCP instance."""
    # 11. capital_entry_plan — S/R-aware entry/stop/target (FORGED 2026-08-09)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_entry_plan",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Compute S/R-aware entry zone, stop loss, and take profit targets "
            "for XAUUSD. Combines swing-point support/resistance clustering with "
            "ATR-based risk scaling. Returns structured trade plan: entry_zone, "
            "stop_loss, target_1, target_2, risk_reward_ratio. "
            "SIDE EFFECT: writes a vault receipt."
        ),
        tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_entry_plan(
        symbol: str = "GC=F",
        interval: str = "1h",
        lookback: str = "3mo",
        trend_bias: str = "auto",
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        import numpy as np
        import yfinance as yf

        sym = symbol.upper()
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=lookback, interval=interval)
        except Exception as e:
            return wrap_result(
                tool_name="capital_entry_plan",
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
                tool_name="capital_entry_plan",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "NO_DATA",
                    "message": f"No data for {sym}",
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

        # ── NaN filter: drop any row with NaN in OHLC ──
        hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
        n_raw_bars = len(hist)
        if n_raw_bars < 50:
            return wrap_result(
                tool_name="capital_entry_plan",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "INSUFFICIENT_DATA",
                    "message": (
                        f"Need >= 50 clean bars for analysis, got {n_raw_bars} "
                        f"(after NaN removal from raw data)"
                    ),
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )
        bars_before_nan = len(hist)
        has_enough_for_ema200 = bars_before_nan >= 200

        high = hist["High"].values.astype(np.float64)
        low = hist["Low"].values.astype(np.float64)
        close = hist["Close"].values.astype(np.float64)
        n = len(close)

        # ── Compute ATR(14) ──
        p = 14
        tr = np.zeros(n)
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        atr_vals = np.zeros(n)
        atr_vals[p] = np.mean(tr[1 : p + 1])
        for i in range(p + 1, n):
            atr_vals[i] = (atr_vals[i - 1] * (p - 1) + tr[i]) / p
        current_atr = float(atr_vals[-1])
        current_price = float(close[-1])

        # ── Compute EMA alignment for trend detection ──
        def _ema(series, span):
            alpha = 2.0 / (span + 1)
            out = np.zeros(len(series))
            out[0] = float(series[0])
            for i in range(1, len(series)):
                out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
            return out

        ema20 = _ema(close, 20)
        ema50 = _ema(close, 50)
        ema200 = _ema(
            np.concatenate([np.full(200 - n, close[0]), close]) if n < 200 else close,
            200,
        )
        if len(ema200) > n:
            ema200 = ema200[-n:]

        # EMA200 warning: when bars < 200, the EMA is seeded with padded values
        ema200_data_warning = None
        if not has_enough_for_ema200:
            ema200_data_warning = (
                f"EMA200 computed from {n} bars (< 200 required). "
                "Padded with leading values — EMA200 alignment is unreliable."
            )

        trend = "SIDEWAYS"
        if ema20[-1] > ema50[-1] > ema200[-1]:
            trend = "UPTREND"
        elif ema20[-1] < ema50[-1] < ema200[-1]:
            trend = "DOWNTREND"
        if trend_bias.lower() == "long" and trend == "DOWNTREND":
            trend = "SIDEWAYS"  # Don't fight trend
        elif trend_bias.lower() == "short" and trend == "UPTREND":
            trend = "SIDEWAYS"

        # ── Find swing S/R zones (local maxima/minima clustering) ──
        lookback_swing = 20
        swing_highs = []
        swing_lows = []
        if n < 50:
            # Insufficient bars for swing detection — use ATR-only zones
            swing_highs = []
            swing_lows = []
        else:
            for i in range(lookback_swing, n - lookback_swing):
                if all(
                    high[i] >= high[i - j] for j in range(1, lookback_swing + 1)
                ) and all(high[i] >= high[i + j] for j in range(1, lookback_swing + 1)):
                    swing_highs.append(float(high[i]))
                if all(low[i] <= low[i - j] for j in range(1, lookback_swing + 1)) and all(
                    low[i] <= low[i + j] for j in range(1, lookback_swing + 1)
                ):
                    swing_lows.append(float(low[i]))

        # Cluster nearby levels
        def _cluster(levels, tolerance_pct=0.5):
            if not levels:
                return []
            levels = sorted(set(levels))
            clusters = []
            current = [levels[0]]
            for lvl in levels[1:]:
                if (
                    abs(lvl - current[-1]) / max(current[-1], 1e-10) * 100
                    < tolerance_pct
                ):
                    current.append(lvl)
                else:
                    clusters.append((sum(current) / len(current), len(current)))
                    current = [lvl]
            clusters.append((sum(current) / len(current), len(current)))
            return [
                (round(price, 2), strength)
                for price, strength in clusters
                if strength >= 2
            ]

        resistance_zones = _cluster(swing_highs)
        support_zones = _cluster(swing_lows)

        # ── Build trade plan ──
        # Zone selection: filter to actionable bands around spot BEFORE ranking.
        # _cluster() orders zones by recency of formation (cluster scan order),
        # NOT by price proximity — index 0 was historically "oldest regime wins"
        # (9-touch zone from months back chosen while price traded 500+ above).
        max_zone_dist = 5 * current_atr

        def _nearest(levels, direction):
            candidates = [
                (lvl, strength)
                for lvl, strength in levels
                if direction == "below"
                and lvl <= current_price
                and (current_price - lvl) <= max_zone_dist
                or direction == "above"
                and lvl >= current_price
                and (lvl - current_price) <= max_zone_dist
            ]
            if not candidates:
                return None
            return min(candidates, key=lambda z: abs(current_price - z[0]))

        nearest_support = (
            _nearest(support_zones, "below")[0]
            if _nearest(support_zones, "below")
            else current_price * 0.98
        )
        nearest_resistance = (
            _nearest(resistance_zones, "above")[0]
            if _nearest(resistance_zones, "above")
            else current_price * 1.02
        )
        # next_resistance must clear the first, not merely be zones[1]
        further_res = [
            z
            for z in resistance_zones
            if z[0] > nearest_resistance + current_atr
            and (z[0] - current_price) <= max_zone_dist
        ]
        next_resistance = (
            further_res[0][0]
            if further_res
            else max(nearest_resistance + 2 * current_atr, current_price * 1.02)
        )

        if trend == "UPTREND":
            entry_zone = round(nearest_support, 2)
            stop_loss = round(nearest_support - 2 * current_atr, 2)
            target_1 = round(nearest_resistance, 2)
            target_2 = round(next_resistance, 2)
            direction = "LONG"
        elif trend == "DOWNTREND":
            entry_zone = round(nearest_resistance, 2)
            stop_loss = round(nearest_resistance + 2 * current_atr, 2)
            target_1 = round(nearest_support, 2)
            further_sup = [
                z
                for z in support_zones
                if z[0] < nearest_support - current_atr
                and (current_price - z[0]) <= max_zone_dist
            ]
            target_2 = round(
                further_sup[0][0]
                if further_sup
                else min(nearest_support - 2 * current_atr, current_price * 0.97),
                2,
            )
            direction = "SHORT"
        else:
            entry_zone = round(current_price, 2)
            stop_loss = round(current_price - 2 * current_atr, 2)
            target_1 = round(current_price + 2 * current_atr, 2)
            target_2 = round(current_price + 3 * current_atr, 2)
            direction = "NEUTRAL"

        risk = abs(entry_zone - stop_loss)
        reward_1 = abs(target_1 - entry_zone)
        reward_2 = abs(target_2 - entry_zone)
        rr_1 = round(reward_1 / risk, 2) if risk > 0 else 0.0
        rr_2 = round(reward_2 / risk, 2) if risk > 0 else 0.0

        return wrap_result(
            tool_name="capital_entry_plan",
            domain="market",
            result={
                "symbol": sym,
                "interval": interval,
                "current_price": round(current_price, 2),
                "trend": trend,
                "atr": round(current_atr, 2),
                "atr_pct": round(current_atr / current_price * 100, 2),
                "direction": direction,
                "entry_zone": entry_zone,
                "stop_loss": stop_loss,
                "target_1": target_1,
                "target_2": target_2,
                "risk": round(risk, 2),
                "risk_reward_1": rr_1,
                "risk_reward_2": rr_2,
                "support_zones": support_zones[:3],
                "resistance_zones": resistance_zones[:3],
                "ema200_data_warning": ema200_data_warning,
            },
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.OBSERVED,
            source_attribution=[f"yfinance:{sym}"],
            session_id=session_id,
            actor_id=actor_id,
        )
