"""
WEALTH 999 — The Complete Investment Intelligence Framework
═══════════════════════════════════════════════════════════════

9 Fundamentals — WHAT to buy   (business quality, value, safety)
9 Technicals  — WHEN to buy    (timing, trend, momentum, structure)
9 Flows       — HOW MUCH + WHY (position, risk, conviction, exit)

999 = The complete loop:
  BUY  ← fundamentals find the asset
  WHEN ← technicals time the entry
  SIZE ← flows determine position
  SELL ← invert the thesis
  LOOP ← learn recursively, adjust to reality

Horizon: Long-term compounder. Adjusted to:
  • Risk/Reward ratio (F1 AMANAH — reversible first)
  • Reality (market truth, not hope)
  • Human physics (Arif's state from WELL)
  • Earth physics (macro context from GEOX/global data)

DITEMPA BUKAN DIBERI — The complete system forged from first principles.
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
from .market_intelligence import (
    _match_sector,
)


# ═══════════════════════════════════════════════════════════════════════════
# 9 FUNDAMENTALS — What To Buy
# ═══════════════════════════════════════════════════════════════════════════


FUNDAMENTAL_CHECKS = [
    {
        "id": "F1_VALUE",
        "name": "Value",
        "desc": "PE vs sector. Are you overpaying?",
        "weight": 0.15,
    },
    {
        "id": "F2_QUALITY",
        "name": "Quality",
        "desc": "ROE/ROIC. Does management create value?",
        "weight": 0.15,
    },
    {
        "id": "F3_GROWTH",
        "name": "Growth",
        "desc": "Revenue & earnings trend. Is the business expanding?",
        "weight": 0.10,
    },
    {
        "id": "F4_SOLVENCY",
        "name": "Solvency",
        "desc": "Debt/Equity, Current Ratio. Can it survive stress?",
        "weight": 0.12,
    },
    {
        "id": "F5_CASH",
        "name": "Cash Reality",
        "desc": "Free Cash Flow. Real money, not accounting profit.",
        "weight": 0.12,
    },
    {
        "id": "F6_MARGINS",
        "name": "Margin Health",
        "desc": "Gross/Op/Net margins. Pricing power.",
        "weight": 0.10,
    },
    {
        "id": "F7_DIVIDEND",
        "name": "Dividend Quality",
        "desc": "Payout ratio. Is the dividend sustainable?",
        "weight": 0.08,
    },
    {
        "id": "F8_GOVERNANCE",
        "name": "Governance",
        "desc": "Related party, audit, dilution. Who runs this?",
        "weight": 0.10,
    },
    {
        "id": "F9_POSITION",
        "name": "Sector Position",
        "desc": "Market position, moat, competitive advantage.",
        "weight": 0.08,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 9 TECHNICALS — When To Buy
# ═══════════════════════════════════════════════════════════════════════════

TECHNICAL_CHECKS = [
    {
        "id": "T1_TREND",
        "name": "Trend Structure",
        "desc": "SMA alignment, higher highs/lows. Is trend intact?",
        "weight": 0.15,
    },
    {
        "id": "T2_MOMENTUM",
        "name": "Momentum",
        "desc": "RSI zone + MACD. Is the move accelerating?",
        "weight": 0.12,
    },
    {
        "id": "T3_VOLUME",
        "name": "Volume Confirmation",
        "desc": "Volume trend, OBV. Are institutions participating?",
        "weight": 0.12,
    },
    {
        "id": "T4_VOLATILITY",
        "name": "Volatility State",
        "desc": "ATR, Bollinger. Compressing or exploding?",
        "weight": 0.10,
    },
    {
        "id": "T5_STRUCTURE",
        "name": "Support/Resistance",
        "desc": "Key levels, invalidation. Where is the battleground?",
        "weight": 0.10,
    },
    {
        "id": "T6_SAR",
        "name": "Parabolic SAR",
        "desc": "Arif's T1 entry signal. Trend flip confirmation.",
        "weight": 0.12,
    },
    {
        "id": "T7_RELATIVE",
        "name": "Relative Strength",
        "desc": "vs KLCI, vs sector. Leading or lagging?",
        "weight": 0.10,
    },
    {
        "id": "T8_LIQUIDITY",
        "name": "Liquidity Health",
        "desc": "Bid/ask spread, depth. Can you exit cleanly?",
        "weight": 0.10,
    },
    {
        "id": "T9_GAP",
        "name": "Gap/Risk Events",
        "desc": "Gap frequency, announcement risk. Hidden landmines?",
        "weight": 0.09,
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 9 FLOWS — How Much + Why
# ═══════════════════════════════════════════════════════════════════════════

FLOW_CHECKS = [
    {
        "id": "W1_SIZE",
        "name": "Position Size",
        "desc": "Kelly/risk-based. Never all-in.",
        "weight": 0.15,
    },
    {
        "id": "W2_RISK",
        "name": "Risk Per Trade",
        "desc": "Max 1% of portfolio at risk. Capital preservation.",
        "weight": 0.15,
    },
    {
        "id": "W3_RMULTIPLE",
        "name": "R-Multiple",
        "desc": "Risk/reward ratio. Is the asymmetry worth it?",
        "weight": 0.12,
    },
    {
        "id": "W4_STOP",
        "name": "Stop Loss",
        "desc": "Hard invalidation level. No stop = no trade.",
        "weight": 0.12,
    },
    {
        "id": "W5_TARGET",
        "name": "Target Price",
        "desc": "Realistic exit. Greed kills.",
        "weight": 0.08,
    },
    {
        "id": "W6_CORRELATION",
        "name": "Correlation Risk",
        "desc": "Portfolio overlap. Are you 3x the same bet?",
        "weight": 0.08,
    },
    {
        "id": "W7_CONVICTION",
        "name": "Conviction Score",
        "desc": "Fusion of fundamental + technical confidence.",
        "weight": 0.10,
    },
    {
        "id": "W8_LIQUIDITY",
        "name": "Liquidity Constraint",
        "desc": "Can you exit cleanly at size?",
        "weight": 0.10,
    },
    {
        "id": "W9_PEACE",
        "name": "Peace of Mind",
        "desc": "Max drawdown, sleep-well factor. F1 AMANAH.",
        "weight": 0.10,
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# THE 999 ENGINE
# ═══════════════════════════════════════════════════════════════════════════


def compute_999(
    ticker: str,
    pe: Optional[float] = None,
    roe: Optional[float] = None,
    pb: Optional[float] = None,
    dy: Optional[float] = None,
    eps: Optional[float] = None,
    sector: str = "",
    # ── Enrichment params (from klse-screener) ──
    dps: Optional[float] = None,
    market_cap_raw: Optional[str] = None,
    nta: Optional[float] = None,
    qoq: Optional[float] = None,
    yoy: Optional[float] = None,
    # Flow params (user-supplied)
    account_balance: float = 10000,
    risk_per_trade_pct: float = 1.0,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    target_price: Optional[float] = None,
    existing_positions: int = 0,
    max_positions: int = 5,
) -> Dict[str, Any]:
    """Compute the complete 999 framework for a stock.

    Returns:
      fundamentals: 9 checks scored 0-100
      technicals:   9 checks scored 0-100
      flows:        9 checks scored 0-100
      fusion:       weighted blend → BUY/HOLD/SELL signal
      narrative:    human-readable diagnosis
      loop:         recursive adjustment signals
    """
    result: Dict[str, Any] = {"ticker": ticker, "sector": sector}

    # ── Fetch price data from yfinance ──
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
        result["data_points"] = len(closes)
    except Exception as e:
        return {"error": str(e), "status": "NEEDS_DATA"}

    if not last_price or len(closes) < 50:
        return {"error": "Insufficient data (need 50+ points)", "status": "NEEDS_DATA"}

    norms = _match_sector(sector)

    # ═════════════════════════════════════════════════════════════════════
    # 9 FUNDAMENTALS
    # ═════════════════════════════════════════════════════════════════════
    f_scores: Dict[str, Any] = {}

    # F1: Value (PE vs sector)
    f1_score = _score_pe(pe, norms["pe"])
    f_scores["F1_VALUE"] = {
        "score": f1_score,
        "value": pe,
        "benchmark": norms["pe"],
        "pass": f1_score >= 60,
    }

    # F2: Quality (ROE vs sector)
    f2_score = _score_roe(roe, norms["roe"])
    f_scores["F2_QUALITY"] = {
        "score": f2_score,
        "value": roe,
        "benchmark": norms["roe"],
        "pass": f2_score >= 60,
    }

    # F3: Growth (revenue/earnings trend — proxy: price trend as earnings proxy)
    rev_growth = ((closes[-1] / closes[-63]) - 1) * 100 if len(closes) >= 63 else 0
    f3_score = _score_growth(rev_growth)
    f_scores["F3_GROWTH"] = {
        "score": f3_score,
        "value": round(rev_growth, 1),
        "note": "Price proxy for earnings trend",
        "pass": f3_score >= 50,
    }

    # F4: Solvency (PB proxy)
    f4_score = _score_pb(pb, norms["pb"])
    f_scores["F4_SOLVENCY"] = {
        "score": f4_score,
        "value": pb,
        "benchmark": norms["pb"],
        "pass": f4_score >= 60,
    }

    # F5: Cash Reality (EPS > 0 + magnitude)
    f5_score = _score_eps(eps)
    f_scores["F5_CASH"] = {"score": f5_score, "value": eps, "pass": f5_score >= 60}

    # F6: Margins (use EPS as margin proxy when no margin data)
    f6_score = 50 if (eps and eps > 5) else (30 if eps and eps > 0 else 10)
    f_scores["F6_MARGINS"] = {
        "score": f6_score,
        "note": "EPS-based proxy",
        "pass": f6_score >= 50,
    }

    # F7: Dividend Quality
    f7_score = _score_dividend(dy, eps)
    f_scores["F7_DIVIDEND"] = {"score": f7_score, "value": dy, "pass": f7_score >= 40}

    # F8: Governance — proxy scoring from available data
    f8_score = _score_governance(dps, dy, eps, market_cap_raw, qoq, yoy)
    f_scores["F8_GOVERNANCE"] = {
        "score": f8_score,
        "dps": dps,
        "dividend_yield": dy,
        "qoq": qoq,
        "yoy": yoy,
        "market_cap": market_cap_raw,
        "note": "Proxy — uses DPS, dividend consistency, market cap, earnings consistency",
        "data_quality": "PROXY" if (dps is not None or market_cap_raw) else "ESTIMATE",
        "pass": f8_score >= 50,
    }

    # F9: Sector Position — competitive moat proxy
    f9_score = _score_moat(roe, market_cap_raw, sector, eps, pb)
    f_scores["F9_POSITION"] = {
        "score": f9_score,
        "roe": roe,
        "market_cap": market_cap_raw,
        "sector": sector,
        "note": "Proxy — uses ROE level, market cap tier, sector characteristics",
        "data_quality": "PROXY" if (roe is not None and market_cap_raw) else "ESTIMATE",
        "pass": f9_score >= 50,
    }

    # Weighted fundamentals
    f_total = sum(
        FUNDAMENTAL_CHECKS[i]["weight"] * f_scores[c["id"]]["score"]
        for i, c in enumerate(FUNDAMENTAL_CHECKS)
    )
    f_total = round(f_total, 1)
    result["fundamentals"] = {"checks": f_scores, "score": f_total, "max": 100}

    # ═════════════════════════════════════════════════════════════════════
    # 9 TECHNICALS
    # ═════════════════════════════════════════════════════════════════════
    t_scores: Dict[str, Any] = {}

    # T1: Trend Structure
    sma20 = compute_sma(closes, 20)
    sma50 = compute_sma(closes, 50)
    price_above_20 = bool(sma20[-1] and last_price > sma20[-1])
    price_above_50 = bool(sma50[-1] and last_price > sma50[-1])
    ma_aligned = (
        bool(sma20[-1] and sma50[-1] and sma20[-1] > sma50[-1])
        if (sma20[-1] and sma50[-1])
        else False
    )
    t1_score = (
        90
        if (price_above_20 and price_above_50 and ma_aligned)
        else (70 if price_above_50 else (40 if price_above_20 else 20))
    )
    t_scores["T1_TREND"] = {
        "score": t1_score,
        "price_above_sma50": price_above_50,
        "sma_aligned": ma_aligned,
        "pass": t1_score >= 50,
    }

    # T2: Momentum
    rsi_val = compute_rsi(closes)
    rsi_last = rsi_val[-1] if rsi_val and rsi_val[-1] is not None else 50
    macd_bull = _macd_bullish(closes)
    t2_score = (
        80
        if (40 <= rsi_last <= 65 and macd_bull)
        else (65 if 30 <= rsi_last <= 70 else (40 if macd_bull else 25))
    )
    t_scores["T2_MOMENTUM"] = {
        "score": t2_score,
        "rsi": rsi_last,
        "macd_bullish": macd_bull,
        "pass": t2_score >= 50,
    }

    # T3: Volume
    avg_vol_10 = sum(volumes[-10:]) / min(10, len(volumes))
    avg_vol_50 = sum(volumes[-50:]) / min(50, len(volumes))
    vol_ratio = avg_vol_10 / avg_vol_50 if avg_vol_50 > 0 else 1.0
    t3_score = (
        85
        if vol_ratio > 1.3
        else (70 if vol_ratio > 1.0 else (50 if vol_ratio > 0.7 else 25))
    )
    t_scores["T3_VOLUME"] = {
        "score": t3_score,
        "vol_ratio": round(vol_ratio, 2),
        "avg_vol": int(avg_vol_10),
        "pass": t3_score >= 50,
    }

    # T4: Volatility
    atr_vals = compute_atr(highs, lows, closes)
    atr_last = atr_vals[-1] if atr_vals and atr_vals[-1] else None
    atr_pct = (atr_last / last_price * 100) if (atr_last and last_price) else None
    t4_score = (
        80
        if (atr_pct and atr_pct < 2)
        else (
            65 if atr_pct and atr_pct < 4 else (45 if atr_pct and atr_pct < 6 else 20)
        )
    )
    t_scores["T4_VOLATILITY"] = {
        "score": t4_score,
        "atr_pct": round(atr_pct, 1) if atr_pct else None,
        "pass": t4_score >= 50,
    }

    # T5: Structure (support/resistance — use BB)
    bb = compute_bollinger(closes)
    bb_lower = bb["lower"][-1]
    bb_upper = bb["upper"][-1]
    dist_from_support = (
        ((last_price - bb_lower) / last_price * 100)
        if (bb_lower and last_price)
        else None
    )
    t5_score = (
        75
        if (dist_from_support is not None and 0 < dist_from_support < 10)
        else (55 if dist_from_support and dist_from_support < 20 else 30)
    )
    t_scores["T5_STRUCTURE"] = {
        "score": t5_score,
        "bb_lower": round(bb_lower, 2) if bb_lower else None,
        "dist_from_support_pct": round(dist_from_support, 1)
        if dist_from_support
        else None,
        "pass": t5_score >= 50,
    }

    # T6: Parabolic SAR
    sar_vals = compute_parabolic_sar(highs, lows)
    sar_last = sar_vals[-1] if sar_vals and sar_vals[-1] else None
    sar_below = bool(sar_last and last_price > sar_last)
    t6_score = 90 if sar_below else 20
    t_scores["T6_SAR"] = {
        "score": t6_score,
        "sar_value": round(sar_last, 2) if sar_last else None,
        "sar_below_price": sar_below,
        "pass": t6_score >= 50,
    }

    # T7: Relative Strength (vs market — price vs SMA50 as proxy)
    rs = (
        round((last_price - sma50[-1]) / sma50[-1] * 100, 1)
        if (sma50[-1] and sma50[-1] > 0)
        else 0
    )
    t7_score = 85 if rs > 5 else (70 if rs > 0 else (45 if rs > -5 else 20))
    t_scores["T7_RELATIVE"] = {
        "score": t7_score,
        "vs_sma50_pct": rs,
        "pass": t7_score >= 50,
    }

    # T8: Liquidity
    t8_score = (
        90
        if avg_vol_10 > 5_000_000
        else (70 if avg_vol_10 > 1_000_000 else (50 if avg_vol_10 > 300_000 else 20))
    )
    t_scores["T8_LIQUIDITY"] = {
        "score": t8_score,
        "avg_volume_10d": int(avg_vol_10),
        "pass": t8_score >= 50,
    }

    # T9: Gap Risk
    t9_score = 50  # neutral — no gap data
    t_scores["T9_GAP"] = {
        "score": t9_score,
        "note": "UNKNOWN — no gap/announcement data",
        "pass": False,
    }

    # Weighted technicals
    t_total = sum(
        TECHNICAL_CHECKS[i]["weight"] * t_scores[c["id"]]["score"]
        for i, c in enumerate(TECHNICAL_CHECKS)
    )
    t_total = round(t_total, 1)
    result["technicals"] = {"checks": t_scores, "score": t_total, "max": 100}

    # ═════════════════════════════════════════════════════════════════════
    # 9 FLOWS
    # ═════════════════════════════════════════════════════════════════════
    w_scores: Dict[str, Any] = {}

    # W1: Position Size (Kelly-inspired: edge / odds)
    kelly_f = _kelly_fraction(f_total / 100, t_total / 100)
    position_value = account_balance * (risk_per_trade_pct / 100)
    quantity = int(position_value / last_price) if last_price and last_price > 0 else 0
    w1_score = 85 if 0 < quantity < 1000000 else (60 if quantity > 0 else 10)
    w_scores["W1_SIZE"] = {
        "score": w1_score,
        "quantity": quantity,
        "position_value_rm": round(position_value, 2),
        "pass": quantity > 0,
    }

    # W2: Risk Per Trade
    w2_score = (
        90
        if risk_per_trade_pct <= 1.0
        else (
            75
            if risk_per_trade_pct <= 2.0
            else (50 if risk_per_trade_pct <= 5.0 else 10)
        )
    )
    w_scores["W2_RISK"] = {
        "score": w2_score,
        "risk_pct": risk_per_trade_pct,
        "pass": risk_per_trade_pct <= 2.0,
    }

    # W3: R-Multiple
    r_mult = _calc_r(entry_price or last_price, stop_loss, target_price)
    w3_score = (
        90
        if r_mult and r_mult >= 3
        else (
            75 if r_mult and r_mult >= 2 else (50 if r_mult and r_mult >= 1.5 else 20)
        )
    )
    w_scores["W3_RMULTIPLE"] = {
        "score": w3_score,
        "r_multiple": r_mult,
        "pass": bool(r_mult and r_mult >= 2),
    }

    # W4: Stop Loss
    stop_pct = (
        abs((entry_price or last_price) - stop_loss) / (entry_price or last_price) * 100
        if (stop_loss and (entry_price or last_price))
        else None
    )
    w4_score = 85 if (stop_loss is not None and stop_loss > 0) else 10
    w_scores["W4_STOP"] = {
        "score": w4_score,
        "stop_loss": stop_loss,
        "stop_pct": round(stop_pct, 1) if stop_pct else None,
        "pass": bool(stop_loss and stop_loss > 0),
    }

    # W5: Target
    target_pct = (
        abs(target_price - (entry_price or last_price))
        / (entry_price or last_price)
        * 100
        if (target_price and (entry_price or last_price))
        else None
    )
    w5_score = 70 if (target_price is not None and target_price > 0) else 30
    w_scores["W5_TARGET"] = {
        "score": w5_score,
        "target_price": target_price,
        "target_pct": round(target_pct, 1) if target_pct else None,
        "pass": bool(target_price and target_price > 0),
    }

    # W6: Correlation
    w6_score = (
        80
        if existing_positions < max_positions
        else (50 if existing_positions == max_positions else 20)
    )
    w_scores["W6_CORRELATION"] = {
        "score": w6_score,
        "existing_positions": existing_positions,
        "max_positions": max_positions,
        "pass": existing_positions < max_positions,
    }

    # W7: Conviction (fundamental × technical fusion)
    conviction = (f_total * 0.55 + t_total * 0.45) / 100
    w7_score = round(conviction * 100)
    w_scores["W7_CONVICTION"] = {
        "score": w7_score,
        "f_score": f_total,
        "t_score": t_total,
        "pass": w7_score >= 60,
    }

    # W8: Liquidity Constraint (can exit at size?)
    position_pct_of_volume = (
        (position_value / (avg_vol_10 * last_price) * 100)
        if (avg_vol_10 > 0 and last_price > 0)
        else 100
    )
    w8_score = (
        90
        if position_pct_of_volume < 1
        else (
            70
            if position_pct_of_volume < 3
            else (45 if position_pct_of_volume < 10 else 15)
        )
    )
    w_scores["W8_LIQUIDITY"] = {
        "score": w8_score,
        "position_pct_of_daily_volume": round(position_pct_of_volume, 2),
        "pass": position_pct_of_volume < 5,
    }

    # W9: Peace of Mind
    max_dd = compute_max_drawdown(closes)
    dd_pct = max_dd.get("max_drawdown_pct", 30)
    sharpe = compute_sharpe_ratio(returns)
    w9_score = (
        90
        if dd_pct < 10
        else (
            75 if dd_pct < 20 else (55 if dd_pct < 30 else (35 if dd_pct < 40 else 15))
        )
    )
    if sharpe > 1.0:
        w9_score += 5
    if sharpe < 0:
        w9_score -= 15
    w9_score = max(10, min(95, w9_score))
    w_scores["W9_PEACE"] = {
        "score": w9_score,
        "max_drawdown_pct": dd_pct,
        "sharpe": round(sharpe, 2),
        "pass": w9_score >= 50,
    }

    # Weighted flows
    w_total = sum(
        FLOW_CHECKS[i]["weight"] * w_scores[c["id"]]["score"]
        for i, c in enumerate(FLOW_CHECKS)
    )
    w_total = round(w_total, 1)
    result["flows"] = {
        "checks": w_scores,
        "score": w_total,
        "max": 100,
        "quantity": quantity,
        "position_value_rm": round(position_value, 2),
    }

    # ═════════════════════════════════════════════════════════════════════
    # 999 FUSION — Weighted blend with macro + human readiness
    # ═════════════════════════════════════════════════════════════════════
    # Macro alignment: sector-based regime score (placeholder for GEOX integration)
    macro_score = _score_macro_alignment(sector, result.get("last_price"))
    # Human readiness: placeholder for WELL integration (default 70 = neutral)
    human_score = 70.0
    # Fusion: What(35%) + When(30%) + How(20%) + Macro(10%) + Human(5%)
    fusion = round(
        f_total * 0.35
        + t_total * 0.30
        + w_total * 0.20
        + macro_score * 0.10
        + human_score * 0.05,
        1,
    )
    result["fusion"] = {
        "score": fusion,
        "fundamentals": f_total,
        "technicals": t_total,
        "flows": w_total,
        "macro_alignment": round(macro_score, 1),
        "human_readiness": round(human_score, 1),
        "weights": "F:35% T:30% W:20% Macro:10% Human:5%",
        "note": "Macro=GEOX proxy, Human=WELL placeholder. Calibrate with live data.",
    }

    # Verdict
    if w_total < 30:
        verdict = "NO_TRADE"  # flows are broken — can't execute safely
    elif fusion >= 75 and w_total >= 60:
        verdict = "STRONG_BUY"
    elif fusion >= 65 and w_total >= 50:
        verdict = "BUY"
    elif fusion >= 50:
        verdict = "WATCH"
    elif fusion >= 35:
        verdict = "HOLD_OR_SELL"
    else:
        verdict = "SELL"

    result["verdict"] = verdict
    result["status"] = "OK"
    result["recommendation_only"] = True
    result["final_authority"] = "Arif"

    # ═════════════════════════════════════════════════════════════════════
    # RECURSIVE LOOP — Invert & Learn (EXECUTABLE)
    # ═════════════════════════════════════════════════════════════════════
    sell_triggers = _compute_sell_triggers(
        result,
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_price=target_price,
        last_price=last_price,
        position_size=quantity,
        account_balance=account_balance,
        risk_per_trade_pct=risk_per_trade_pct,
    )
    result["loop"] = {
        "buy_signal": verdict in ("STRONG_BUY", "BUY"),
        "watch_signal": verdict == "WATCH",
        "sell_signal": verdict in ("HOLD_OR_SELL", "SELL"),
        "sell_triggers": sell_triggers,
        "invert_check": {
            "if_bought": f"Monitor: stop={stop_loss}, target={target_price}, r={r_mult}",
            "exit_condition": "Stop hit OR target hit OR conviction drops below 50",
            "trail_stop": "Move stop to break-even at R=1, then trail by ATR",
        },
        "recursive_learn": {
            "log_trade": "Record entry price, exit price, reason, holding period, R outcome",
            "review_monthly": "What worked? What didn't? Adjust weights.",
            "adjust_to_reality": "If 3 consecutive stops hit, reduce position size 50%",
            "adjust_to_human": "If WELL reports fatigue, pause new entries",
            "adjust_to_earth": "If VIX > 30 or oil spikes >20%, tighten stops",
        },
    }

    # Narrative
    result["narrative"] = _build_999_narrative(result, ticker)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# SCORING HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _score_pe(pe, benchmark):
    if pe is None:
        return 0
    if pe <= 0:
        return 10
    gap = (benchmark - pe) / benchmark
    return min(100, max(5, 50 + gap * 80))


def _score_roe(roe, benchmark):
    if roe is None:
        return 0
    if roe <= 0:
        return 10
    gap = (roe - benchmark) / benchmark
    return min(100, max(5, 50 + gap * 50))


def _score_growth(growth):
    if growth > 20:
        return 90
    if growth > 10:
        return 75
    if growth > 5:
        return 60
    if growth > 0:
        return 50
    if growth > -10:
        return 30
    return 10


def _score_pb(pb, benchmark):
    if pb is None:
        return 0
    if pb <= 0:
        return 10
    gap = (benchmark - pb) / benchmark
    return min(100, max(5, 50 + gap * 60))


def _score_eps(eps):
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


def _score_dividend(dy, eps):
    if dy is None:
        return 0
    if eps is None or eps <= 0:
        return 20  # can't pay dividends without earnings
    if dy > 5:
        return 85
    if dy > 3:
        return 70
    if dy > 2:
        return 55
    if dy > 0:
        return 40
    return 20


def _kelly_fraction(f_score, t_score):
    """Kelly-inspired position sizing. More conservative than pure Kelly."""
    edge = (f_score * 0.5 + t_score * 0.5) - 0.5  # edge above 50% random
    if edge <= 0:
        return 0
    odds = 2.0  # assume 2:1 payoff (conservative)
    kelly = edge - (1 - edge) / odds
    return max(0, min(0.25, kelly * 0.5))  # half-kelly, max 25%


def _calc_r(entry, stop, target):
    if not entry or not stop or not target or entry == stop:
        return None
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return round(reward / risk, 2) if risk > 0 else None


def _score_governance(
    dps: Optional[float],
    dy: Optional[float],
    eps: Optional[float],
    market_cap_raw: Optional[str],
    qoq: Optional[float],
    yoy: Optional[float],
) -> int:
    """Score governance quality from proxy signals.

    Proxy signals (no direct governance data from free API):
      - DPS > 0 + dividend consistency → shareholder-friendly (40 pts)
      - Market cap tier → regulatory scrutiny proxy (20 pts)
      - QoQ/YoY earnings consistency → less likely manipulation (20 pts)
      - DPS/EPS payout ratio reasonable → balanced governance (20 pts)
    """
    score = 0
    evidence = 0

    # Signal 1: Dividend-paying = shareholder return discipline
    if dps is not None and dps > 0:
        score += 25
        evidence += 1
        # Strong payout consistency if yield > 2%
        if dy is not None and dy > 2:
            score += 15
            evidence += 1
    elif dy is not None and dy > 1:
        score += 15
        evidence += 1

    # Signal 2: Market cap tier — larger = more regulatory scrutiny
    mcap = _parse_market_cap(market_cap_raw)
    if mcap is not None:
        evidence += 1
        if mcap > 10:  # > RM10B = large cap, heavy scrutiny
            score += 20
        elif mcap > 2:  # > RM2B = mid cap, moderate scrutiny
            score += 12
        elif mcap > 0.5:  # > RM500M = small cap, less scrutiny
            score += 5

    # Signal 3: Earnings consistency (QoQ/YoY)
    if qoq is not None and yoy is not None:
        evidence += 1
        if qoq > 0 and yoy > 0:
            score += 20  # both growing — consistent
        elif qoq > 0 or yoy > 0:
            score += 10  # one direction growing
        elif qoq > -10 and yoy > -10:
            score += 5  # mild decline

    # Signal 4: Payout ratio sanity (DPS < EPS = sustainable)
    if dps is not None and eps is not None and eps > 0 and dps < eps:
        score += 15
        evidence += 1
    elif dps is not None and eps is not None and eps > 0 and dps <= eps * 1.5:
        score += 5

    # If no evidence at all, return honest neutral
    if evidence == 0:
        return 50  # "UNKNOWN — no governance signals available"

    return min(95, score + 5)


def _score_moat(
    roe: Optional[float],
    market_cap_raw: Optional[str],
    sector: str,
    eps: Optional[float],
    pb: Optional[float],
) -> int:
    """Score competitive moat / market position from proxy signals.

    Proxy signals:
      - ROE level and consistency → capital compounder or value destroyer
      - Market cap tier → dominant position
      - Sector characteristics → some sectors have natural moats
      - P/B premium → market pricing the moat
    """
    score = 0
    evidence = 0

    # Signal 1: ROE tier — the primary moat signal
    if roe is not None:
        evidence += 1
        if roe > 20:
            score += 40  # exceptional compounder
        elif roe > 15:
            score += 30  # strong moat
        elif roe > 10:
            score += 20  # adequate
        elif roe > 5:
            score += 10  # weak
        else:
            score += 0  # no moat

    # Signal 2: Market cap — absolute size = competitive position
    mcap = _parse_market_cap(market_cap_raw)
    if mcap is not None:
        evidence += 1
        if mcap > 50:  # > RM50B = dominant
            score += 30
        elif mcap > 10:  # > RM10B = large cap
            score += 20
        elif mcap > 2:
            score += 10
        elif mcap > 0.5:
            score += 5

    # Signal 3: Sector moat characteristics
    if sector:
        evidence += 1
        s = sector.lower()
        if any(k in s for k in ["bank", "finance", "insurance"]):
            score += 10  # regulatory moat + switching costs
        elif any(k in s for k in ["tele", "utility", "infra"]):
            score += 15  # natural monopoly / infrastructure moat
        elif any(k in s for k in ["consumer", "food", "beverage"]):
            score += 10  # brand moat
        elif any(k in s for k in ["oil", "gas", "energy"]):
            score += 8  # resource moat
        elif any(k in s for k in ["tech", "software"]):
            score += 5  # IP moat but competitive

    # Signal 4: P/B premium — market paying for intangibles/moat
    if pb is not None and pb > 0 and eps is not None and eps > 0:
        evidence += 1
        if pb > 3 and roe is not None and roe > 15:
            score += 10  # high P/B justified by high ROE = moat premium
        elif pb > 2:
            score += 5

    if evidence == 0:
        return 50

    return min(95, score + 5)


def _parse_market_cap(raw: Optional[str]) -> Optional[float]:
    """Parse market cap string like '129.7B' or '500M' to float in billions MYR."""
    if raw is None:
        return None
    try:
        raw = str(raw).strip().upper().replace(",", "")
        if raw.endswith("B"):
            return float(raw[:-1])
        elif raw.endswith("M"):
            return float(raw[:-1]) / 1000
        elif raw.endswith("K"):
            return float(raw[:-1]) / 1000000
        else:
            return float(raw) / 1e9
    except (ValueError, TypeError):
        return None


def _compute_sell_triggers(
    result: Dict[str, Any],
    entry_price: Optional[float],
    stop_loss: Optional[float],
    target_price: Optional[float],
    last_price: Optional[float],
    position_size: int,
    account_balance: float,
    risk_per_trade_pct: float,
) -> Dict[str, Any]:
    """Compute EXECUTABLE sell/exit triggers from 999 scores + position state.

    Returns structured sell rules, not just descriptive text.
    Each trigger has: condition (boolean), action (str), reason (str).
    """
    triggers = []
    active = 0

    # Trigger 1: Stop-loss hit
    stop_hit = (
        stop_loss is not None and last_price is not None and last_price <= stop_loss
    )
    triggers.append(
        {
            "id": "SELL_STOP",
            "active": stop_hit,
            "condition": f"price {last_price} <= stop {stop_loss}"
            if stop_hit
            else "not triggered",
            "action": "EXIT_FULL",
            "reason": "Hard invalidation — stop loss breached",
            "priority": 1,
        }
    )
    if stop_hit:
        active += 1

    # Trigger 2: Target hit
    target_hit = (
        target_price is not None
        and last_price is not None
        and last_price >= target_price
    )
    triggers.append(
        {
            "id": "SELL_TARGET",
            "active": target_hit,
            "condition": f"price {last_price} >= target {target_price}"
            if target_hit
            else "not triggered",
            "action": "EXIT_FULL_OR_TRAIL",
            "reason": "Target achieved — take profit or trail stop",
            "priority": 2,
        }
    )
    if target_hit:
        active += 1

    # Trigger 3: Conviction collapse (fusion < 35)
    fusion = result.get("fusion", {}).get("score", 50)
    conviction_collapse = fusion < 35
    triggers.append(
        {
            "id": "SELL_CONVICTION",
            "active": conviction_collapse,
            "condition": f"fusion {fusion} < 35"
            if conviction_collapse
            else f"fusion {fusion} >= 35",
            "action": "EXIT_FULL",
            "reason": "Conviction collapsed — thesis broken",
            "priority": 3,
        }
    )
    if conviction_collapse:
        active += 1

    # Trigger 4: Size exceeds risk budget
    position_value = (entry_price or last_price or 0) * position_size
    over_risk = (
        account_balance > 0
        and position_value > account_balance * (risk_per_trade_pct / 100) * 2
    )
    triggers.append(
        {
            "id": "REDUCE_SIZE",
            "active": over_risk,
            "condition": f"position RM{position_value:.0f} > {risk_per_trade_pct * 2:.1f}% of RM{account_balance:.0f}"
            if over_risk
            else "within risk budget",
            "action": "REDUCE_HALF",
            "reason": "Position exceeds risk budget — trim, don't exit",
            "priority": 4,
        }
    )
    if over_risk:
        active += 1

    # Trigger 5: Trend reversal (technical score < 30)
    t_score = result.get("technicals", {}).get("score", 50)
    trend_broken = t_score < 30
    triggers.append(
        {
            "id": "SELL_TREND",
            "active": trend_broken,
            "condition": f"technicals {t_score} < 30"
            if trend_broken
            else f"technicals {t_score} >= 30",
            "action": "EXIT_HALF",
            "reason": "Technical structure broken — reduce exposure",
            "priority": 5,
        }
    )
    if trend_broken:
        active += 1

    # Trigger 6: 3 consecutive stops (recursive learn)
    # This requires state tracking — hook for Calhoun guard integration
    triggers.append(
        {
            "id": "CALHOUN_HALT",
            "active": False,  # requires state tracking across trades
            "condition": "requires trade history — CalhounGuard integration point",
            "action": "PAUSE_ALL",
            "reason": "3 consecutive stops — reduce size 50%, pause new entries",
            "priority": 6,
        }
    )

    return {
        "triggers": triggers,
        "active_count": active,
        "any_critical": any(t["active"] and t["priority"] <= 2 for t in triggers),
        "recommended_action": (
            "EXIT"
            if any(t["active"] and t["priority"] <= 2 for t in triggers)
            else ("REDUCE" if active > 0 else "HOLD")
        ),
    }


def _score_macro_alignment(sector: str, last_price: Optional[float]) -> float:
    """Crude macro alignment score from sector + price (placeholder for GEOX integration).

    Different sectors benefit from different macro regimes:
      - Banking: higher rates = better NIM
      - Energy: oil price > $60 = favorable
      - Consumer: stable rates, low inflation
      - Tech: low rates, growth regime

    Currently returns sector-neutral baseline. Wire GEOX field_macro for real data.
    """
    if not sector:
        return 50.0  # neutral
    s = sector.lower()
    # Sector baseline scores (to be calibrated with real macro data)
    if any(k in s for k in ["bank", "finance"]):
        return 55.0  # banking — moderate macro sensitivity
    elif any(k in s for k in ["oil", "gas", "energy"]):
        return 55.0  # energy — oil-price dependent
    elif any(k in s for k in ["tele", "utility"]):
        return 60.0  # defensive — less macro sensitive
    elif any(k in s for k in ["consumer", "food"]):
        return 55.0  # consumer staples — defensive
    elif any(k in s for k in ["tech", "software"]):
        return 50.0  # tech — growth dependent, higher vol
    elif any(k in s for k in ["property", "construction"]):
        return 45.0  # cyclical — rate sensitive
    elif any(k in s for k in ["plant", "industrial"]):
        return 50.0
    else:
        return 50.0


def _macd_bullish(prices: List[float]) -> bool:
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


def _build_999_narrative(result: Dict, ticker: str) -> str:
    f = result.get("fundamentals", {})
    t = result.get("technicals", {})
    w = result.get("flows", {})
    fus = result.get("fusion", {})
    loop = result.get("loop", {})
    v = result.get("verdict", "?")

    parts = [f"═══ 999 ANALYSIS: {ticker} ═══"]
    parts.append(
        f"WHAT:  Fundamentals {f.get('score', 0)}/100 — {_grade(f.get('score', 0))}"
    )
    parts.append(
        f"WHEN:  Technicals  {t.get('score', 0)}/100 — {_grade(t.get('score', 0))}"
    )
    parts.append(
        f"HOW:   Flows       {w.get('score', 0)}/100 — {_grade(w.get('score', 0))}"
    )
    parts.append(f"SEAL:  {v} (Fusion {fus.get('score', 0)}/100)")
    qty = w.get("quantity", 0)
    if qty > 0:
        parts.append(
            f"SIZE:  {qty} shares @ RM{result.get('last_price', 0):.2f} = RM{w.get('position_value_rm', 0):.0f}"
        )
    if loop.get("buy_signal"):
        parts.append(
            f"→ BUY signal active. Stop: {w.get('checks', {}).get('W4_STOP', {}).get('stop_loss', 'SET')}"
        )
    parts.append("—" * 40)
    parts.append("LOOP: Trade → Monitor → Invert → Learn → Repeat")
    parts.append("Adjust to: Risk/Reality/Human physics/Earth physics")
    return "\n".join(parts)


def _grade(score):
    if score >= 75:
        return "STRONG"
    if score >= 60:
        return "GOOD"
    if score >= 45:
        return "FAIR"
    if score >= 30:
        return "WEAK"
    return "POOR"
