"""
WEALTH Stock Analysis — TAC-9 Technical Engine
══════════════════════════════════════════════

Nine-layer technical analysis framework.
T1–T9: Regime → Sector → RS → Trend → Volume → Liquidity → Volatility → Structure → R.

RSI, MACD, and Parabolic SAR are SECONDARY confirmations only — never primary signals.

DITEMPA BUKAN DIBERI — Technicals are forged on fundamentals, not on hope.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def run_tac9_engine(
    ticker: str = "",
    # T1: Regime
    benchmark_trend: str = "neutral",  # "bullish", "neutral", "bearish"
    sector_trend: str = "neutral",
    market_breadth: str = "neutral",  # "broad", "narrow", "diverging"
    volatility_regime: str = "normal",  # "low", "normal", "elevated", "extreme"
    risk_state: str = "neutral",  # "risk_on", "neutral", "risk_off"
    # T2: Sector Differential
    stock_return_3m: Optional[float] = None,
    sector_return_3m: Optional[float] = None,
    # T3: Stock Relative Strength
    stock_vs_klci: Optional[float] = None,
    rs_3m: Optional[float] = None,
    rs_6m: Optional[float] = None,
    # T4: Trend Acceptance
    price_above_50ma: bool = False,
    ma50_above_ma200: bool = False,
    higher_highs: bool = False,
    higher_lows: bool = False,
    support_holding: bool = False,
    # T5: Volume-Price
    breakout_volume: str = "unknown",  # "strong", "normal", "weak", "unknown"
    up_volume_ratio: Optional[float] = None,  # up_vol / total_vol
    accumulation: str = "neutral",  # "accumulating", "distributing", "neutral"
    # T6: Liquidity Trap
    avg_daily_value_rm: Optional[float] = None,
    position_value_rm: Optional[float] = None,
    bid_ask_spread_pct: Optional[float] = None,
    gap_frequency: str = "low",  # "low", "moderate", "high"
    # T7: Volatility
    atr_pct: Optional[float] = None,
    bb_width: Optional[str] = None,  # "narrow", "normal", "wide"
    volume_dry_up: bool = False,
    # T8: Structure
    support_level: Optional[float] = None,
    resistance_level: Optional[float] = None,
    invalidation_level: Optional[float] = None,
    breakout_retest: bool = False,
    # T9: Risk-Reward
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    r_multiple: Optional[float] = None,
    # Secondary signals (demoted — confirm only, never primary)
    rsi_value: Optional[float] = None,
    macd_signal: str = "neutral",  # "bullish", "bearish", "neutral"
    sar_position: str = "neutral",  # "above", "below", "neutral"
) -> dict:
    """Run TAC-9 technical analysis on a stock.

    T1–T9 evaluation. Each tier gets a verdict. RSI/MACD/SAR are
    SECONDARY confirmations — never primary entry signals.
    """
    tiers: List[Dict[str, Any]] = []
    flags: List[str] = []
    tier_pass = 0
    tier_total = 9

    # ── T1: Regime ──
    t1_issues: List[str] = []
    if benchmark_trend == "bearish":
        t1_issues.append("Benchmark in bearish trend")
    if sector_trend == "bearish":
        t1_issues.append("Sector in bearish trend")
    if market_breadth == "narrow":
        t1_issues.append("Narrow market breadth — few stocks participating")
    if volatility_regime == "extreme":
        t1_issues.append("Extreme volatility regime — position sizing critical")
    if risk_state == "risk_off":
        t1_issues.append("Risk-off state — capital preservation mode")

    if benchmark_trend == "bearish" or risk_state == "risk_off":
        t1_verdict = "HOSTILE"
    elif t1_issues:
        t1_verdict = "CAUTION"
    elif benchmark_trend == "bullish" and risk_state == "risk_on":
        t1_verdict = "SUPPORTIVE"
    else:
        t1_verdict = "NEUTRAL"

    if t1_verdict != "HOSTILE":
        tier_pass += 1
    tiers.append(
        {
            "tier": "T1_REGIME",
            "verdict": t1_verdict,
            "description": "Market and sector regime",
            "issues": t1_issues,
        }
    )

    # ── T2: Sector Differential Strength ──
    t2_issues: List[str] = []
    sector_diff = None
    if stock_return_3m is not None and sector_return_3m is not None:
        sector_diff = stock_return_3m - sector_return_3m
        if sector_diff < -5:
            t2_issues.append(
                f"Stock lags sector by {abs(sector_diff):.1f}% over 3 months"
            )
            t2_verdict = "WEAK"
        elif sector_diff < 0:
            t2_verdict = "BELOW_AVERAGE"
        elif sector_diff > 5:
            t2_verdict = "LEADING"
        else:
            t2_verdict = "IN_LINE"
    else:
        t2_verdict = "INSUFFICIENT_DATA"

    if t2_verdict not in ("WEAK",):
        tier_pass += 1
    tiers.append(
        {
            "tier": "T2_SECTOR_DIFF",
            "verdict": t2_verdict,
            "description": "Stock vs sector strength",
            "diff_3m": sector_diff,
            "issues": t2_issues,
        }
    )

    # ── T3: Stock Relative Strength ──
    t3_issues: List[str] = []
    if rs_3m is not None and rs_3m < 0:
        t3_issues.append(f"Negative 3-month RS: {rs_3m}%")
    if rs_6m is not None and rs_6m < 0:
        t3_issues.append(f"Negative 6-month RS: {rs_6m}%")

    if t3_issues:
        t3_verdict = "WEAK"
    elif rs_3m is not None and rs_3m > 5:
        t3_verdict = "STRONG"
    elif rs_3m is not None:
        t3_verdict = "NEUTRAL"
    else:
        t3_verdict = "INSUFFICIENT_DATA"

    if t3_verdict != "WEAK":
        tier_pass += 1
    tiers.append(
        {
            "tier": "T3_RELATIVE_STRENGTH",
            "verdict": t3_verdict,
            "description": "Stock vs benchmark",
            "issues": t3_issues,
        }
    )

    # ── T4: Trend Acceptance ──
    t4_score = sum(
        [price_above_50ma, ma50_above_ma200, higher_highs, higher_lows, support_holding]
    )
    t4_issues: List[str] = []
    if not price_above_50ma:
        t4_issues.append("Price below 50MA")
    if not ma50_above_ma200:
        t4_issues.append("50MA below 200MA — death cross risk")
    if not higher_highs:
        t4_issues.append("No higher highs")
    if not higher_lows:
        t4_issues.append("No higher lows")

    if t4_score >= 4:
        t4_verdict = "STRONG_TREND"
    elif t4_score >= 2:
        t4_verdict = "NEUTRAL"
    else:
        t4_verdict = "WEAK"

    if t4_score >= 2:
        tier_pass += 1
    tiers.append(
        {
            "tier": "T4_TREND",
            "verdict": t4_verdict,
            "description": "Trend structure",
            "score": f"{t4_score}/5",
            "issues": t4_issues,
        }
    )

    # ── T5: Volume-Price Integrity ──
    t5_issues: List[str] = []
    if breakout_volume == "weak":
        t5_issues.append("Breakout on weak volume — unconvincing")
    if up_volume_ratio is not None and up_volume_ratio < 0.4:
        t5_issues.append(f"Only {up_volume_ratio:.0%} of volume on up days")
    if accumulation == "distributing":
        t5_issues.append("Distribution pattern — smart money exiting")

    if not t5_issues:
        t5_verdict = "HEALTHY"
        tier_pass += 1
    elif len(t5_issues) >= 2:
        t5_verdict = "DIVERGENCE"
    else:
        t5_verdict = "CAUTION"
        tier_pass += 1  # still passable
    tiers.append(
        {
            "tier": "T5_VOLUME",
            "verdict": t5_verdict,
            "description": "Volume-price integrity",
            "issues": t5_issues,
        }
    )

    # ── T6: Liquidity Trap Index ──
    t6_issues: List[str] = []
    if avg_daily_value_rm is not None and position_value_rm is not None:
        position_pct = (position_value_rm / avg_daily_value_rm) * 100.0
        if position_pct > 5.0:
            t6_issues.append(
                f"Position is {position_pct:.1f}% of avg daily value — may not exit cleanly"
            )
        elif position_pct > 2.0:
            t6_issues.append(
                f"Position is {position_pct:.1f}% of avg daily value — monitor"
            )
    if bid_ask_spread_pct is not None and bid_ask_spread_pct > 2.0:
        t6_issues.append(f"Wide spread: {bid_ask_spread_pct}%")
    if gap_frequency == "high":
        t6_issues.append("High gap frequency — gap-down risk")

    if not t6_issues:
        t6_verdict = "LIQUID"
        tier_pass += 1
    elif any("may not exit" in i for i in t6_issues):
        t6_verdict = "TRAP"
    else:
        t6_verdict = "CAUTION"
        tier_pass += 1
    tiers.append(
        {
            "tier": "T6_LIQUIDITY",
            "verdict": t6_verdict,
            "description": "Can you exit cleanly?",
            "issues": t6_issues,
        }
    )

    # ── T7: Volatility Compression/Expansion ──
    t7_issues: List[str] = []
    if atr_pct is not None and atr_pct > 10:
        t7_issues.append(f"ATR {atr_pct}% — high volatility, size down")
    if bb_width == "narrow":
        t7_issues.append("Bollinger Bands narrow — stored energy, expansion ahead")
    if volume_dry_up:
        t7_issues.append("Volume drying up — quiet before move")

    if not t7_issues:
        t7_verdict = "MANAGEABLE"
        tier_pass += 1
    elif atr_pct is not None and atr_pct > 10:
        t7_verdict = "HOSTILE"
    else:
        t7_verdict = "COMPRESSING"
        tier_pass += 1
    tiers.append(
        {
            "tier": "T7_VOLATILITY",
            "verdict": t7_verdict,
            "description": "Stored energy and survivable volatility",
            "issues": t7_issues,
        }
    )

    # ── T8: Structure + Invalidation ──
    t8_issues: List[str] = []
    if invalidation_level is None:
        t8_issues.append("No invalidation level defined — no clear exit")
    if support_level is not None and entry is not None and entry < support_level:
        t8_issues.append("Entry below support — weak structure")

    if not t8_issues and invalidation_level is not None:
        t8_verdict = "CLEAR"
        tier_pass += 1
    elif invalidation_level is not None:
        t8_verdict = "WEAK"
    else:
        t8_verdict = "NO_INVALIDATION"

    tiers.append(
        {
            "tier": "T8_STRUCTURE",
            "verdict": t8_verdict,
            "description": "Clear invalidation = tradeable",
            "issues": t8_issues,
        }
    )

    # ── T9: Risk-Reward Geometry ──
    t9_issues: List[str] = []
    if r_multiple is not None:
        if r_multiple < 2.0:
            t9_issues.append(f"R = {r_multiple} — unacceptable")
        elif r_multiple < 2.5:
            t9_issues.append(f"R = {r_multiple} — weak asymmetry")
    elif (
        entry is not None and stop is not None and target is not None and stop != entry
    ):
        calc_r = abs(target - entry) / abs(entry - stop)
        if calc_r < 2.0:
            t9_issues.append(f"R = {calc_r:.1f} — unacceptable")

    if not t9_issues and (r_multiple is not None and r_multiple >= 2.5):
        t9_verdict = "STRONG"
        tier_pass += 1
    elif not t9_issues:
        t9_verdict = "ACCEPTABLE"
        tier_pass += 1
    elif r_multiple is not None and r_multiple < 2.0:
        t9_verdict = "WEAK"
    else:
        t9_verdict = "INSUFFICIENT_DATA"

    tiers.append(
        {
            "tier": "T9_RISK_REWARD",
            "verdict": t9_verdict,
            "description": "Risk-reward geometry",
            "issues": t9_issues,
        }
    )

    # ── Secondary signal notes ──
    secondary_notes: List[str] = []
    if rsi_value is not None:
        if rsi_value > 70:
            secondary_notes.append(
                f"RSI {rsi_value} — short-term stretched (exhaustion possible, NOT a sell signal alone)"
            )
        elif rsi_value < 30:
            secondary_notes.append(
                f"RSI {rsi_value} — oversold (could be falling knife, NOT a buy signal alone)"
            )
    if macd_signal == "bullish":
        secondary_notes.append("MACD bullish — secondary momentum confirmation only")
    elif macd_signal == "bearish":
        secondary_notes.append("MACD bearish — secondary caution only")
    if sar_position == "above":
        secondary_notes.append(
            "SAR above price — trend may be down, NOT a sell signal alone"
        )
    elif sar_position == "below":
        secondary_notes.append(
            "SAR below price — trend may be up, NOT a buy signal alone"
        )

    # ── Overall TAC-9 verdict ──
    if tier_pass >= 8:
        tac9_verdict = "STRONG"
        overall_verdict = "SAFE_TO_STUDY"
    elif tier_pass >= 6:
        tac9_verdict = "ADEQUATE"
        overall_verdict = "SAFE_TO_STUDY"
    elif tier_pass >= 4:
        tac9_verdict = "WEAK"
        overall_verdict = "NEEDS_DATA"
    elif tier_pass >= 2:
        tac9_verdict = "VERY_WEAK"
        overall_verdict = "UNSAFE"
    else:
        tac9_verdict = "HOSTILE"
        overall_verdict = "UNSAFE"

    # ── False confluence warning ──
    bullish_count = sum(
        [
            1 if macd_signal == "bullish" else 0,
            1
            if rsi_value is not None and 30 < rsi_value < 70
            else 0,  # neutral RSI — not really a signal
            1 if sar_position == "below" else 0,
        ]
    )
    if bullish_count >= 2 and tac9_verdict in ("WEAK", "VERY_WEAK", "HOSTILE"):
        flags.append(
            f"FALSE_CONFLUENCE: {bullish_count} secondary signals bullish "
            f"but TAC-9 verdict = {tac9_verdict}. Secondary signals are one class "
            f"(price-momentum), not {bullish_count} independent confirmations."
        )

    # ── Hard gates ──
    if "HOSTILE" in [t1_verdict]:
        flags.append("REGIME_HOSTILE — all entries are higher risk")
    if "TRAP" in [t6_verdict]:
        flags.append("LIQUIDITY_TRAP — position may be un-exitable")
    if "NO_INVALIDATION" in [t8_verdict]:
        flags.append("NO_INVALIDATION — no clear exit means no trade")

    return {
        "status": "OK",
        "verdict": overall_verdict,
        "result": {
            "ticker": ticker.upper() if ticker else "?",
            "tac9_verdict": tac9_verdict,
            "tiers_passed": tier_pass,
            "tiers_total": tier_total,
            "tiers": tiers,
            "secondary_signals": {
                "rsi": rsi_value,
                "macd": macd_signal,
                "sar": sar_position,
                "notes": secondary_notes,
                "rule": "RSI/MACD/SAR are secondary. Use TAC-9 tiers for primary decisions.",
            },
            "flags": flags,
        },
        "warnings": flags,
        "recommendation_only": True,
        "final_authority": "Arif",
    }
