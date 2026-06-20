"""
WEALTH 888 — The JUDGE Investment Framework
══════════════════════════════════════════════

8 Fundamentals — WHAT (7 to analyze, 8th = FUNDAMENTAL HOLD gate)
8 Technicals  — WHEN (7 to analyze, 8th = TECHNICAL HOLD gate)
8 Flows       — HOW   (7 to analyze, 8th = EXECUTION JUDGE gate)

888 = arifOS JUDGE number. Every layer ends with deliberation before action.
      999 is SEAL (complete). 888 is JUDGE (careful).

CONTRAST with 999:
  999 = 9×3 checks → fusion → verdict
  888 = (7 checks + 1 HOLD gate) × 3 → layered gating → final JUDGE

The 8th element in each layer is NOT a check — it's a DELIBERATION:
  F8: "Given F1-F7 scores, should I HOLD on fundamentals?"
  T8: "Given T1-T7 scores, should I HOLD on technicals?"
  W8: "Given F-HOLD + T-HOLD + W1-W7, is this trade EXECUTABLE?"

888 JUDGE verdict: PROCEED | HOLD | SABAR
  PROCEED = all 3 gates pass → execute within limits
  HOLD    = 1+ gates triggered → pause, gather more evidence
  SABAR   = critical gate → stop, await sovereign review

DITEMPA BUKAN DIBERI — The judge does not compute. The judge deliberates.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .indicators import (
    compute_rsi,
    compute_sma,
    compute_bollinger,
    compute_atr,
    compute_parabolic_sar,
    compute_returns,
    compute_max_drawdown,
    compute_sharpe_ratio,
)
from .market_intelligence import _match_sector


# ═══════════════════════════════════════════════════════════════════════════
# 8 FUNDAMENTALS — What To Buy (F1-F7 analyze, F8 = HOLD gate)
# ═══════════════════════════════════════════════════════════════════════════

F_CHECKS = [
    {
        "id": "F1",
        "name": "Value",
        "desc": "PE vs sector. Underpaying or overpaying?",
        "weight": 0.18,
    },
    {
        "id": "F2",
        "name": "Quality",
        "desc": "ROE. Does management compound capital?",
        "weight": 0.18,
    },
    {
        "id": "F3",
        "name": "Growth",
        "desc": "Revenue/EPS trend. Expanding or shrinking?",
        "weight": 0.15,
    },
    {
        "id": "F4",
        "name": "Solvency",
        "desc": "PB + debt structure. Can it survive stress?",
        "weight": 0.14,
    },
    {
        "id": "F5",
        "name": "Cash",
        "desc": "EPS reality. Accounting profit or real cash?",
        "weight": 0.14,
    },
    {
        "id": "F6",
        "name": "Margins",
        "desc": "Profit quality. Pricing power or commodity?",
        "weight": 0.10,
    },
    {
        "id": "F7",
        "name": "Dividend",
        "desc": "Payout sustainability. Paid to wait or trap?",
        "weight": 0.11,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 8 TECHNICALS — When To Buy (T1-T7 analyze, T8 = HOLD gate)
# ═══════════════════════════════════════════════════════════════════════════

T_CHECKS = [
    {
        "id": "T1",
        "name": "Trend",
        "desc": "SMA alignment. Is the structure intact?",
        "weight": 0.18,
    },
    {
        "id": "T2",
        "name": "Momentum",
        "desc": "RSI + MACD. Accelerating or fading?",
        "weight": 0.16,
    },
    {
        "id": "T3",
        "name": "Volume",
        "desc": "Volume confirmation. Smart money or noise?",
        "weight": 0.15,
    },
    {
        "id": "T4",
        "name": "Volatility",
        "desc": "ATR state. Compressing (energy) or exploding (chaos)?",
        "weight": 0.13,
    },
    {
        "id": "T5",
        "name": "Structure",
        "desc": "Support/Resistance. Where's the battleground?",
        "weight": 0.12,
    },
    {
        "id": "T6",
        "name": "SAR",
        "desc": "Parabolic SAR. Arif's T1 flip signal.",
        "weight": 0.14,
    },
    {
        "id": "T7",
        "name": "Strength",
        "desc": "RS vs market + liquidity. Leading and liquid?",
        "weight": 0.12,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 8 FLOWS — How Much + Why (W1-W7 analyze, W8 = EXECUTION JUDGE)
# ═══════════════════════════════════════════════════════════════════════════

W_CHECKS = [
    {
        "id": "W1",
        "name": "Position",
        "desc": "Kelly-inspired size. Never all-in.",
        "weight": 0.17,
    },
    {
        "id": "W2",
        "name": "Risk",
        "desc": "Max risk per trade. Capital preservation.",
        "weight": 0.17,
    },
    {
        "id": "W3",
        "name": "R-Multiple",
        "desc": "Risk/reward asymmetry. Worth the risk?",
        "weight": 0.14,
    },
    {
        "id": "W4",
        "name": "Stop",
        "desc": "Hard invalidation. No stop = no trade.",
        "weight": 0.14,
    },
    {
        "id": "W5",
        "name": "Target",
        "desc": "Realistic exit. Greed kills.",
        "weight": 0.10,
    },
    {
        "id": "W6",
        "name": "Correlation",
        "desc": "Portfolio overlap. Diversified or 3x same bet?",
        "weight": 0.10,
    },
    {
        "id": "W7",
        "name": "Peace",
        "desc": "Max drawdown. Can you sleep holding this?",
        "weight": 0.18,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# THE 888 JUDGE ENGINE
# ═══════════════════════════════════════════════════════════════════════════


def compute_888(
    ticker: str,
    pe: Optional[float] = None,
    roe: Optional[float] = None,
    pb: Optional[float] = None,
    dy: Optional[float] = None,
    eps: Optional[float] = None,
    sector: str = "",
    account_balance: float = 10000,
    risk_per_trade_pct: float = 1.0,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    target_price: Optional[float] = None,
    existing_positions: int = 0,
    max_positions: int = 5,
) -> Dict[str, Any]:
    """Compute the 888 JUDGE framework.

    Returns F1-F8 (fundamentals + HOLD), T1-T8 (technicals + HOLD),
    W1-W8 (flows + JUDGE), and final 888 verdict.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "sector": sector,
        "framework": "888_JUDGE",
    }

    # ── Fetch price data ──
    try:
        import yfinance as yf

        yt_symbol = f"{ticker}.KL" if ticker.isdigit() else ticker
        yt = yf.Ticker(yt_symbol)
        hist = yt.history(period="6mo")
        if hist.empty:
            return {"error": f"No history for {ticker}", "status": "NEEDS_DATA"}
        closes = [float(x) for x in hist["Close"].tolist()]
        volumes = [int(x) for x in hist["Volume"].tolist()]
        highs = [float(x) for x in hist["High"].tolist()]
        lows = [float(x) for x in hist["Low"].tolist()]
        returns = compute_returns(closes)
        last_price = closes[-1] if closes else None
        result["last_price"] = round(last_price, 4) if last_price else None
    except Exception as e:
        return {"error": str(e), "status": "NEEDS_DATA"}

    if not last_price or len(closes) < 50:
        return {"error": "Need 50+ data points", "status": "NEEDS_DATA"}

    norms = _match_sector(sector)

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 1: 8 FUNDAMENTALS
    # ═══════════════════════════════════════════════════════════════════
    f_scores: Dict[str, Any] = {}

    # F1: Value
    f1 = _f_score_pe(pe, norms["pe"])
    f_scores["F1"] = {"score": f1, "value": pe, "benchmark": norms["pe"]}

    # F2: Quality
    f2 = _f_score_roe(roe, norms["roe"])
    f_scores["F2"] = {"score": f2, "value": roe, "benchmark": norms["roe"]}

    # F3: Growth
    growth = ((closes[-1] / closes[-63]) - 1) * 100 if len(closes) >= 63 else 0
    f3 = _f_score_growth(growth)
    f_scores["F3"] = {"score": f3, "value": round(growth, 1), "note": "Price proxy"}

    # F4: Solvency
    f4 = _f_score_pb(pb, norms["pb"])
    f_scores["F4"] = {"score": f4, "value": pb, "benchmark": norms["pb"]}

    # F5: Cash
    f5 = _f_score_eps(eps)
    f_scores["F5"] = {"score": f5, "value": eps}

    # F6: Margins
    f6 = 50 if (eps and eps > 5) else (30 if eps and eps > 0 else 15)
    f_scores["F6"] = {"score": f6, "note": "EPS proxy"}

    # F7: Dividend
    f7 = _f_score_dy(dy, eps)
    f_scores["F7"] = {"score": f7, "value": dy}

    # Weighted F1-F7
    f_weighted = sum(
        F_CHECKS[i]["weight"] * f_scores[c["id"]]["score"]
        for i, c in enumerate(F_CHECKS)
    )
    f_weighted = round(f_weighted, 1)

    # ═══ F8: FUNDAMENTAL HOLD GATE ═══
    f_gate = _judge_gate(
        f_weighted, f_scores, threshold=45, critical_ids=["F1", "F2", "F4", "F5"]
    )
    f_scores["F8_HOLD"] = f_gate

    result["fundamentals"] = {
        "checks": f_scores,
        "score": f_weighted,
        "hold": f_gate["hold"],
    }

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 2: 8 TECHNICALS
    # ═══════════════════════════════════════════════════════════════════
    t_scores: Dict[str, Any] = {}

    # T1: Trend
    sma20 = compute_sma(closes, 20)
    sma50 = compute_sma(closes, 50)
    above_50 = bool(sma50[-1] and last_price > sma50[-1])
    aligned = bool(sma20[-1] and sma50[-1] and sma20[-1] > sma50[-1])
    t1 = 90 if (above_50 and aligned) else (65 if above_50 else 35)
    t_scores["T1"] = {"score": t1, "above_sma50": above_50, "aligned": aligned}

    # T2: Momentum
    rsi_vals = compute_rsi(closes)
    rsi_last = rsi_vals[-1] if rsi_vals and rsi_vals[-1] is not None else 50
    macd_bull = _macd_bullish(closes)
    t2 = (
        85
        if (40 <= rsi_last <= 65 and macd_bull)
        else (60 if 30 <= rsi_last <= 70 else 30)
    )
    t_scores["T2"] = {"score": t2, "rsi": rsi_last, "macd_bullish": macd_bull}

    # T3: Volume
    avg_vol_10 = sum(volumes[-10:]) / min(10, len(volumes))
    avg_vol_50 = sum(volumes[-50:]) / min(50, len(volumes))
    vol_ratio = avg_vol_10 / avg_vol_50 if avg_vol_50 > 0 else 1.0
    t3 = 85 if vol_ratio > 1.3 else (65 if vol_ratio > 1.0 else 40)
    t_scores["T3"] = {"score": t3, "vol_ratio": round(vol_ratio, 2)}

    # T4: Volatility
    atr_vals = compute_atr(highs, lows, closes)
    atr_last = atr_vals[-1] if atr_vals and atr_vals[-1] else None
    atr_pct = (atr_last / last_price * 100) if (atr_last and last_price) else None
    t4 = 85 if (atr_pct and atr_pct < 2) else (65 if atr_pct and atr_pct < 4 else 35)
    t_scores["T4"] = {"score": t4, "atr_pct": round(atr_pct, 1) if atr_pct else None}

    # T5: Structure
    bb = compute_bollinger(closes)
    bb_low = bb["lower"][-1]
    dist_support = (
        ((last_price - bb_low) / last_price * 100) if (bb_low and last_price) else None
    )
    t5 = (
        80
        if (dist_support and 0 < dist_support < 10)
        else (50 if dist_support and dist_support < 20 else 25)
    )
    t_scores["T5"] = {
        "score": t5,
        "dist_support_pct": round(dist_support, 1) if dist_support else None,
    }

    # T6: Parabolic SAR
    sar_vals = compute_parabolic_sar(highs, lows)
    sar_last = sar_vals[-1] if sar_vals and sar_vals[-1] else None
    sar_below = bool(sar_last and last_price > sar_last)
    t6 = 90 if sar_below else 20
    t_scores["T6"] = {"score": t6, "sar_below": sar_below}

    # T7: Relative Strength + Liquidity
    rs = (
        round((last_price - sma50[-1]) / sma50[-1] * 100, 1)
        if (sma50[-1] and sma50[-1] > 0)
        else 0
    )
    liq_score = 85 if avg_vol_10 > 5_000_000 else (65 if avg_vol_10 > 1_000_000 else 35)
    t7 = round(rs_score(rs) * 0.5 + liq_score * 0.5)
    t_scores["T7"] = {"score": t7, "rs_pct": rs, "avg_vol": int(avg_vol_10)}

    # Weighted T1-T7
    t_weighted = sum(
        T_CHECKS[i]["weight"] * t_scores[c["id"]]["score"]
        for i, c in enumerate(T_CHECKS)
    )
    t_weighted = round(t_weighted, 1)

    # ═══ T8: TECHNICAL HOLD GATE ═══
    t_gate = _judge_gate(
        t_weighted, t_scores, threshold=45, critical_ids=["T1", "T2", "T3", "T6"]
    )
    t_scores["T8_HOLD"] = t_gate

    result["technicals"] = {
        "checks": t_scores,
        "score": t_weighted,
        "hold": t_gate["hold"],
    }

    # ═══════════════════════════════════════════════════════════════════
    # LAYER 3: 8 FLOWS
    # ═══════════════════════════════════════════════════════════════════
    w_scores: Dict[str, Any] = {}

    # W1: Position Size (Kelly-inspired)
    edge = (f_weighted / 100 * 0.5 + t_weighted / 100 * 0.5) - 0.5
    kelly_f = max(0, min(0.25, edge * 0.5)) if edge > 0 else 0
    position_value = account_balance * (risk_per_trade_pct / 100)
    quantity = int(position_value / last_price) if last_price and last_price > 0 else 0
    w1 = 85 if 0 < quantity < 1000000 else (50 if quantity > 0 else 5)
    w_scores["W1"] = {
        "score": w1,
        "quantity": quantity,
        "value_rm": round(position_value, 2),
    }

    # W2: Risk Per Trade
    w2 = 90 if risk_per_trade_pct <= 1.0 else (70 if risk_per_trade_pct <= 2.0 else 40)
    w_scores["W2"] = {"score": w2, "risk_pct": risk_per_trade_pct}

    # W3: R-Multiple
    r_mult = _calc_r(entry_price or last_price, stop_loss, target_price)
    w3 = (
        90
        if (r_mult and r_mult >= 3)
        else (
            70 if r_mult and r_mult >= 2 else (40 if r_mult and r_mult >= 1.5 else 15)
        )
    )
    w_scores["W3"] = {"score": w3, "r_multiple": r_mult}

    # W4: Stop Loss
    w4 = 85 if (stop_loss is not None and stop_loss > 0) else 5
    w_scores["W4"] = {"score": w4, "stop": stop_loss}

    # W5: Target
    target_pct = (
        abs(target_price - (entry_price or last_price))
        / (entry_price or last_price)
        * 100
        if (target_price and (entry_price or last_price))
        else None
    )
    w5 = 75 if (target_price and target_price > 0) else 25
    w_scores["W5"] = {
        "score": w5,
        "target": target_price,
        "target_pct": round(target_pct, 1) if target_pct else None,
    }

    # W6: Correlation
    w6 = (
        80
        if existing_positions < max_positions
        else (45 if existing_positions == max_positions else 15)
    )
    w_scores["W6"] = {
        "score": w6,
        "positions": existing_positions,
        "max": max_positions,
    }

    # W7: Peace of Mind
    max_dd = compute_max_drawdown(closes)
    sharpe = compute_sharpe_ratio(returns)
    dd_pct = max_dd.get("max_drawdown_pct", 30)
    w7 = 90 if dd_pct < 10 else (70 if dd_pct < 20 else (50 if dd_pct < 30 else 25))
    if sharpe > 1.0:
        w7 += 5
    if sharpe < 0:
        w7 -= 10
    w7 = max(10, min(95, w7))
    w_scores["W7"] = {"score": w7, "max_dd_pct": dd_pct, "sharpe": round(sharpe, 2)}

    # Weighted W1-W7
    w_weighted = sum(
        W_CHECKS[i]["weight"] * w_scores[c["id"]]["score"]
        for i, c in enumerate(W_CHECKS)
    )
    w_weighted = round(w_weighted, 1)

    # ═══ W8: EXECUTION JUDGE GATE ═══
    # This is the FINAL gate. It considers:
    #   - Is F-HOLD triggered? (fundamentals broken)
    #   - Is T-HOLD triggered? (technicals invalid)
    #   - Are W1-W7 adequate? (flows insufficient)
    #   - Is liquidity constraint violated?
    position_pct_vol = (
        (position_value / (avg_vol_10 * last_price) * 100)
        if (avg_vol_10 > 0 and last_price > 0)
        else 100
    )
    liquidity_broken = position_pct_vol > 5
    r_broken = r_mult is not None and r_mult < 1.5
    peace_broken = dd_pct > 35

    hold_reasons = []
    if f_gate["hold"]:
        hold_reasons.append(f"F-HOLD: fundamentals ({f_weighted}/100) below threshold")
    if t_gate["hold"]:
        hold_reasons.append(f"T-HOLD: technicals ({t_weighted}/100) below threshold")
    if liquidity_broken:
        hold_reasons.append(
            f"LIQUIDITY: position is {position_pct_vol:.1f}% of daily volume"
        )
    if r_broken:
        hold_reasons.append(f"R-MULTIPLE: {r_mult} — insufficient asymmetry")
    if peace_broken:
        hold_reasons.append(f"PEACE: {dd_pct:.0f}% max drawdown — can you sleep?")
    if w_weighted < 40:
        hold_reasons.append(
            f"FLOWS: ({w_weighted}/100) — execution parameters inadequate"
        )

    w_gate = {
        "hold": len(hold_reasons) > 0,
        "hold_reasons": hold_reasons,
        "judge_verdict": "SABAR"
        if len(hold_reasons) >= 3
        else ("HOLD" if hold_reasons else "PROCEED"),
        "score": w_weighted,
    }
    w_scores["W8_JUDGE"] = w_gate

    result["flows"] = {
        "checks": w_scores,
        "score": w_weighted,
        "hold": w_gate["hold"],
        "quantity": quantity,
    }

    # ═══════════════════════════════════════════════════════════════════
    # 888 VERDICT
    # ═══════════════════════════════════════════════════════════════════
    f_hold = f_gate["hold"]
    t_hold = t_gate["hold"]
    w_hold = w_gate["hold"]
    gate_count = sum([f_hold, t_hold, w_hold])

    if gate_count == 0:
        verdict = "PROCEED"
        signal = "All 3 gates clear. Execute within position limits. F1 AMANAH: stop must be set."
    elif gate_count == 1:
        verdict = "HOLD"
        signal = f"1 gate triggered: {'F' if f_hold else ''}{'T' if t_hold else ''}{'W' if w_hold else ''}-HOLD. Review before action."
    elif gate_count == 2:
        verdict = "HOLD"
        signal = "2 gates triggered. Strong HOLD. Gather more evidence before reconsidering."
    else:
        verdict = "SABAR"
        signal = "3 gates triggered. SABAR — sovereign review required. Do NOT enter."

    result["verdict"] = verdict
    result["signal"] = signal
    result["gate_summary"] = {
        "F_HOLD": f_hold,
        "T_HOLD": t_hold,
        "W_HOLD": w_hold,
        "total_gates": gate_count,
    }
    result["status"] = "OK"
    result["recommendation_only"] = True
    result["final_authority"] = "Arif"

    # Narrative
    result["narrative"] = _build_888_narrative(
        result, ticker, f_weighted, t_weighted, w_weighted
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════
# THE JUDGE GATE — Common deliberation logic for each layer
# ═══════════════════════════════════════════════════════════════════════════


def _judge_gate(
    weighted_score: float,
    checks: Dict,
    threshold: float = 45,
    critical_ids: Optional[List[str]] = None,
) -> Dict:
    """Deliberate: should this layer HOLD?

    Returns {hold: bool, reason: str, confidence: float}

    HOLD triggers:
      1. Weighted score below threshold
      2. Any critical check scored < 30
      3. > 50% of checks scored < 40
    """
    reasons = []
    hold = False

    # Gate 1: overall score
    if weighted_score < threshold:
        hold = True
        reasons.append(f"Score {weighted_score} < {threshold}")

    # Gate 2: critical failures
    if critical_ids:
        for cid in critical_ids:
            if cid in checks and checks[cid]["score"] < 30:
                hold = True
                reasons.append(f"Critical {cid}={checks[cid]['score']}/100")

    # Gate 3: broad weakness
    poor_count = sum(
        1
        for k, v in checks.items()
        if not k.endswith("_HOLD") and v.get("score", 50) < 40
    )
    total_checks = sum(1 for k in checks if not k.endswith("_HOLD"))
    if total_checks > 0 and poor_count / total_checks > 0.5:
        hold = True
        reasons.append(f"Broad weakness: {poor_count}/{total_checks} checks below 40")

    return {
        "hold": hold,
        "reasons": reasons,
        "confidence": round(1.0 - (poor_count / max(total_checks, 1)), 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
# SCORING HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _f_score_pe(pe, bench):
    if pe is None:
        return 0
    if pe <= 0:
        return 10
    return min(100, max(5, 50 + (bench - pe) / bench * 80))


def _f_score_roe(roe, bench):
    if roe is None:
        return 0
    if roe <= 0:
        return 10
    return min(100, max(5, 50 + (roe - bench) / bench * 50))


def _f_score_growth(g):
    if g > 20:
        return 90
    if g > 10:
        return 75
    if g > 5:
        return 60
    if g > 0:
        return 45
    if g > -10:
        return 25
    return 10


def _f_score_pb(pb, bench):
    if pb is None:
        return 0
    if pb <= 0:
        return 10
    return min(100, max(5, 50 + (bench - pb) / bench * 60))


def _f_score_eps(eps):
    if eps is None:
        return 0
    if eps <= 0:
        return 10
    if eps > 50:
        return 95
    if eps > 20:
        return 80
    if eps > 5:
        return 60
    return 40


def _f_score_dy(dy, eps):
    if dy is None:
        return 0
    if eps is None or eps <= 0:
        return 15
    if dy > 5:
        return 85
    if dy > 3:
        return 70
    if dy > 2:
        return 55
    if dy > 0:
        return 40
    return 20


def rs_score(rs):
    if rs > 5:
        return 85
    if rs > 0:
        return 65
    if rs > -5:
        return 45
    return 20


def _calc_r(entry, stop, target):
    if not entry or not stop or not target or entry == stop:
        return None
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return round(reward / risk, 2) if risk > 0 else None


def _macd_bullish(prices):
    if len(prices) < 35:
        return False

    def _e(arr, p):
        m = 2.0 / (p + 1)
        r = [sum(arr[:p]) / p]
        for i in range(p, len(arr)):
            r.append((arr[i] - r[-1]) * m + r[-1])
        return r

    e12 = _e(prices, 12)
    e26 = _e(prices, 26)
    macd = [e12[i] - e26[i] for i in range(min(len(e12), len(e26)))]
    sig = _e(macd, 9)
    return len(sig) > 1 and macd[-1] > sig[-1]


def _build_888_narrative(result, ticker, f, t, w):
    v = result["verdict"]
    g = result["gate_summary"]
    parts = [
        f"═══ 888 JUDGE: {ticker} ═══",
        f"Fundamentals: {f}/100 {'⚠️ HOLD' if g['F_HOLD'] else '✅ CLEAR'}",
        f"Technicals:   {t}/100 {'⚠️ HOLD' if g['T_HOLD'] else '✅ CLEAR'}",
        f"Flows:        {w}/100 {'⚠️ HOLD' if g['W_HOLD'] else '✅ CLEAR'}",
        f"═ 888 VERDICT: {v} ({g['total_gates']}/3 gates triggered)",
        result["signal"],
        "═ DITEMPA BUKAN DIBERI — The judge deliberates before action.",
    ]
    return "\n".join(parts)
