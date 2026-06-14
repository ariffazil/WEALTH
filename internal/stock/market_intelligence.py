"""
WEALTH Market Intelligence Engine — Thermodynamic State-Space Analysis
══════════════════════════════════════════════════════════════════════

EUREKA: A stock is a reservoir. Not of oil — of capital.
        Invariants   = reservoir quality (porosity, permeability — slow truth)
        Dynamics     = flow rate (pressure drawdown — fast changing)
        Entropy      = measurement uncertainty (how much is signal vs noise)
        Energy       = driving force (valuation gap × momentum)

This engine computes FOUR scores (0-100) and FUSES them into one intelligence
verdict. It does NOT use binary pass/fail. Every score is continuous.

LAYERS:
  1. INVARIANT — Business reality. Should change slowly. Sector-normalized.
  2. DYNAMIC   — Price/volume/momentum state. Can change daily.
  3. ENTROPY   — Disorder. Signal quality. Regime clarity. High entropy = chaos.
  4. ENERGY    — Driving force. Potential (valuation gap) + Kinetic (momentum).

FUSION:
  Total = 0.40·Invariant + 0.30·Dynamic + 0.15·Entropy + 0.15·Energy

VERDICT:
  ≥ 75 = COMPELLING  |  60-74 = INTERESTING  |  40-59 = NEUTRAL
  25-39 = WEAK       |  < 25  = AVOID

This is NOT a buy/sell signal. It is a MARKET STATE DIAGNOSIS — the same way
a petrophysicist diagnoses a reservoir from logs, not from one porosity number.

DITEMPA BUKAN DIBERI — Intelligence is forged from structure, not from hope.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1: INVARIANT SCORE — Business Reality (Sector-Normalized)
# ═══════════════════════════════════════════════════════════════════════════

# Sector norms for Bursa Malaysia (approximate, based on typical ranges)
# Format: {sector_keyword: {pe_median, pb_median, roe_median, dy_median}}
SECTOR_NORMS: Dict[str, Dict[str, float]] = {
    "bank": {"pe": 12, "pb": 1.2, "roe": 11, "dy": 4.0},
    "plantation": {"pe": 15, "pb": 1.8, "roe": 8, "dy": 2.5},
    "oil": {"pe": 10, "pb": 1.5, "roe": 12, "dy": 3.0},
    "utility": {"pe": 14, "pb": 1.3, "roe": 9, "dy": 3.5},
    "tech": {"pe": 25, "pb": 3.0, "roe": 15, "dy": 1.0},
    "glove": {"pe": 18, "pb": 2.5, "roe": 20, "dy": 1.5},
    "property": {"pe": 10, "pb": 0.8, "roe": 6, "dy": 3.0},
    "construction": {"pe": 12, "pb": 1.2, "roe": 8, "dy": 2.0},
    "telco": {"pe": 16, "pb": 2.0, "roe": 10, "dy": 3.5},
    "consumer": {"pe": 20, "pb": 3.0, "roe": 15, "dy": 2.0},
    "default": {"pe": 15, "pb": 1.8, "roe": 10, "dy": 2.5},
}


def _match_sector(sector_name: str) -> Dict[str, float]:
    """Match sector name to norms."""
    s = sector_name.lower()
    for keyword, norms in SECTOR_NORMS.items():
        if keyword in s:
            return norms
    return SECTOR_NORMS["default"]


def compute_invariant_score(
    pe: Optional[float],
    roe: Optional[float],
    pb: Optional[float],
    dy: Optional[float],
    eps: Optional[float],
    sector: str = "",
) -> Dict[str, Any]:
    """Compute invariant score (0-100) — sector-normalized business quality.

    Components (each 0-25):
      - Value (PE relative to sector)
      - Quality (ROE relative to sector)
      - Asset Efficiency (PB relative to sector)
      - Profitability (EPS > 0 + earnings power)

    Returns dict with score, component breakdown, and missing-data flags.
    """
    norms = _match_sector(sector)
    score = 0.0
    components: Dict[str, Any] = {}
    data_points = 0

    # 1. Value (0-25): PE vs sector median
    if pe is not None and pe > 0:
        data_points += 1
        sector_pe = norms["pe"]
        if pe < sector_pe * 0.7:
            val_score = 25  # deep value
        elif pe < sector_pe:
            val_score = 20  # undervalued
        elif pe < sector_pe * 1.3:
            val_score = 15  # fair
        elif pe < sector_pe * 2.0:
            val_score = 8  # expensive
        else:
            val_score = 3  # very expensive
    else:
        val_score = 0
    components["value"] = {"score": val_score, "pe": pe, "sector_pe": norms["pe"]}
    score += val_score

    # 2. Quality (0-25): ROE vs sector median
    if roe is not None:
        data_points += 1
        sector_roe = norms["roe"]
        if roe > sector_roe * 1.5:
            qual_score = 25  # exceptional
        elif roe > sector_roe:
            qual_score = 20  # above average
        elif roe > sector_roe * 0.7:
            qual_score = 15  # average
        elif roe > 0:
            qual_score = 8  # below average
        else:
            qual_score = 0  # negative ROE
    else:
        qual_score = 0
    components["quality"] = {
        "score": qual_score,
        "roe": roe,
        "sector_roe": norms["roe"],
    }
    score += qual_score

    # 3. Asset Efficiency (0-25): PB ratio
    if pb is not None and pb > 0:
        data_points += 1
        sector_pb = norms["pb"]
        if pb < sector_pb * 0.5:
            asset_score = 25  # deep asset value
        elif pb < sector_pb:
            asset_score = 20
        elif pb < sector_pb * 1.5:
            asset_score = 15
        elif pb < sector_pb * 3.0:
            asset_score = 8
        else:
            asset_score = 3
    else:
        asset_score = 0
    components["asset_efficiency"] = {
        "score": asset_score,
        "pb": pb,
        "sector_pb": norms["pb"],
    }
    score += asset_score

    # 4. Profitability (0-25): EPS + consistency
    if eps is not None and eps > 0:
        data_points += 1
        profit_score = 20  # positive earnings = baseline pass
        if eps > 50:
            profit_score = 25  # strong absolute earnings
        elif eps > 10:
            profit_score = 22
    elif eps is not None and eps <= 0:
        profit_score = 0  # losing money
    else:
        profit_score = 0
    components["profitability"] = {"score": profit_score, "eps": eps}
    score += profit_score

    # Missing data penalty
    if data_points < 3:
        score = score * 0.5  # heavy penalty for incomplete data

    return {
        "invariant_score": round(min(100, score), 1),
        "max_score": 100,
        "data_points": data_points,
        "sector": sector,
        "sector_norms": norms,
        "components": components,
    }


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2: DYNAMIC SCORE — Price/Volume/Momentum State
# ═══════════════════════════════════════════════════════════════════════════


def compute_dynamic_score(
    closes: List[float],
    volumes: List[int],
    highs: List[float],
    lows: List[float],
) -> Dict[str, Any]:
    """Compute dynamic score (0-100) — price, trend, momentum, liquidity.

    Components (each 0-33.3):
      - Trend (SMA alignment, slope)
      - Momentum (RSI zone, MACD)
      - Liquidity (volume quality, range)
    """
    if len(closes) < 50:
        return {"dynamic_score": 0, "error": "Need 50+ data points"}

    last_price = closes[-1]
    components: Dict[str, Any] = {}
    score = 0.0

    # ── Trend (0-33.3) ──
    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    sma_slope = (sma20 - sma50) / sma50 * 100 if sma50 > 0 else 0  # % spread

    trend_score = 16.5  # neutral
    if last_price > sma20 > sma50 and sma_slope > 0:
        trend_score = 30  # strong uptrend
    elif last_price > sma50:
        trend_score = 23  # above medium trend
    elif last_price < sma50 and last_price > sma20:
        trend_score = 13  # pullback in uptrend
    elif sma_slope < -3:
        trend_score = 5  # strong downtrend
    components["trend"] = {
        "score": round(trend_score, 1),
        "price_vs_sma50": round((last_price - sma50) / sma50 * 100, 2) if sma50 else 0,
        "sma_slope_pct": round(sma_slope, 2),
    }
    score += trend_score

    # ── Momentum (0-33.3) ──
    rsi = _compute_rsi(closes, 14)
    macd_bull = _macd_signal(closes)

    mom_score = 16.5  # neutral
    if rsi and 40 <= rsi <= 60:
        mom_score += 5  # healthy zone
    if macd_bull:
        mom_score += 5
    if rsi and 50 <= rsi <= 65:
        mom_score += 3  # upward momentum without overbought
    if rsi and rsi > 70:
        mom_score -= 8  # overbought risk
    if rsi and rsi < 30:
        mom_score -= 5  # oversold but could reverse

    mom_score = max(3, min(33, mom_score))
    components["momentum"] = {
        "score": round(mom_score, 1),
        "rsi": rsi,
        "macd_bullish": macd_bull,
    }
    score += mom_score

    # ── Liquidity (0-33.3) ──
    avg_vol = sum(volumes[-20:]) / min(20, len(volumes))
    vol_trend = (
        sum(volumes[-5:]) / max(1, sum(volumes[-20:-5]) / 15)
        if len(volumes) >= 20
        else 1.0
    )
    atr = _compute_atr_simple(highs[-14:], lows[-14:], closes[-14:])
    range_pct = (atr / last_price * 100) if (last_price and atr) else None

    liq_score = 16.5
    if avg_vol > 10_000_000:
        liq_score += 10  # very liquid
    elif avg_vol > 2_000_000:
        liq_score += 7
    elif avg_vol > 500_000:
        liq_score += 3
    if vol_trend > 1.2:
        liq_score += 3  # rising volume interest
    if range_pct and range_pct < 3:
        liq_score += 3  # tight range = efficient

    liq_score = max(3, min(33, liq_score))
    components["liquidity"] = {
        "score": round(liq_score, 1),
        "avg_volume": int(avg_vol),
        "volume_trend": round(vol_trend, 2),
        "atr_pct": round(range_pct, 2) if range_pct else None,
    }
    score += liq_score

    return {
        "dynamic_score": round(min(100, score), 1),
        "max_score": 100,
        "last_price": round(last_price, 4),
        "components": components,
    }


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3: ENTROPY SCORE — Disorder, Signal Quality, Regime Clarity
# ═══════════════════════════════════════════════════════════════════════════


def compute_entropy_score(returns: List[float], closes: List[float]) -> Dict[str, Any]:
    """Compute entropy score (0-100) — signal vs noise.

    High entropy = chaos, randomness, weak edge. (low score)
    Low entropy  = structure, persistence, strong signal. (high score)

    Components:
      - Autocorrelation (higher = more predictable, lower entropy)
      - Volatility Compression (contracting vol = energy building)
      - Trend Efficiency (ratio of net move to total path length)
    """
    if len(returns) < 20:
        return {"entropy_score": 50, "error": "Need 20+ returns"}

    score = 55.0  # slightly optimistic baseline (markets have structure)
    components: Dict[str, Any] = {}

    # ── Autocorrelation (lag-1) ──
    if len(returns) >= 21:
        r1 = returns[1:]
        r0 = returns[:-1]
        n = len(r0)
        mean_r0 = sum(r0) / n
        mean_r1 = sum(r1) / n
        cov = sum((r0[i] - mean_r0) * (r1[i] - mean_r1) for i in range(n)) / n
        var0 = sum((x - mean_r0) ** 2 for x in r0) / n
        var1 = sum((x - mean_r1) ** 2 for x in r1) / n
        if var0 > 0 and var1 > 0:
            autocorr = cov / math.sqrt(var0 * var1)
        else:
            autocorr = 0
        components["autocorrelation"] = round(autocorr, 4)
        if autocorr > 0.08:
            score += 12  # strong persistence
        elif autocorr > 0.03:
            score += 6
        elif autocorr < -0.15:
            score -= 8  # strong mean-reversion
        elif autocorr < -0.08:
            score -= 4
    else:
        components["autocorrelation"] = None

    # ── Volatility Compression ──
    if len(returns) >= 30:
        recent_vol = _std(returns[-10:])
        historical_vol = _std(returns[-30:])
        if historical_vol > 0:
            vol_ratio = recent_vol / historical_vol
            components["vol_compression"] = round(vol_ratio, 3)
            if vol_ratio < 0.7:
                score += 18  # strong compression — energy building
            elif vol_ratio < 0.9:
                score += 9
            elif vol_ratio > 1.5:
                score -= 15  # expanding chaos
            elif vol_ratio > 1.2:
                score -= 6
        else:
            components["vol_compression"] = None
    else:
        components["vol_compression"] = None

    # ── Trend Efficiency ──
    if len(closes) >= 20:
        net_move = closes[-1] - closes[0]
        total_path = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
        if total_path > 0:
            efficiency = abs(net_move) / total_path
            components["trend_efficiency"] = round(efficiency, 4)
            if efficiency > 0.35:
                score += 12
            elif efficiency > 0.20:
                score += 6
            elif efficiency < 0.05:
                score -= 10  # pure noise
            elif efficiency < 0.10:
                score -= 4
        else:
            components["trend_efficiency"] = None
    else:
        components["trend_efficiency"] = None

    score = max(5, min(95, score))
    components["entropy_score"] = round(score, 1)

    # Regime
    if score >= 70:
        regime = "ORDERED"
    elif score >= 50:
        regime = "STRUCTURED"
    elif score >= 30:
        regime = "NOISY"
    else:
        regime = "CHAOTIC"

    return {
        "entropy_score": round(score, 1),
        "max_score": 100,
        "regime": regime,
        "components": components,
    }


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 4: ENERGY PROFILE — Driving Force
# ═══════════════════════════════════════════════════════════════════════════


def compute_energy_profile(
    closes: List[float],
    volumes: List[int],
    pe: Optional[float],
    sector_pe: float,
) -> Dict[str, Any]:
    """Compute energy profile — reservoir of capital pressure.

    Potential Energy = valuation gap (distance from fair PE)
    Kinetic Energy   = price velocity × volume confirmation
    Friction         = spread proxy, liquidity drag
    Heat             = realized volatility

    Higher total energy = stronger driving force behind the stock.
    """
    if len(closes) < 20:
        return {"energy_score": 50, "error": "Need 20+ data points"}

    last_price = closes[-1]
    components: Dict[str, Any] = {}

    # ── Potential Energy (0-30): Valuation gap ──
    if pe is not None and pe > 0 and sector_pe > 0:
        pe_gap = (sector_pe - pe) / sector_pe  # positive = undervalued
        if pe_gap > 0.3:
            pot_score = 30  # deeply undervalued — large potential
        elif pe_gap > 0.1:
            pot_score = 22
        elif pe_gap > -0.1:
            pot_score = 15  # fair
        elif pe_gap > -0.3:
            pot_score = 8
        else:
            pot_score = 3  # very overvalued
    else:
        pot_score = 10
        pe_gap = None
    components["potential_energy"] = {
        "score": pot_score,
        "pe_gap": round(pe_gap, 3) if pe_gap else None,
    }

    # ── Kinetic Energy (0-35): Momentum × Volume ──
    returns_10 = (
        [(closes[i] / closes[i - 1] - 1) for i in range(-10, 0)]
        if len(closes) >= 11
        else []
    )
    momentum_10 = sum(returns_10) * 100 if returns_10 else 0  # 10-day return %
    avg_vol_10 = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else 0
    avg_vol_30 = sum(volumes[-30:]) / 30 if len(volumes) >= 30 else avg_vol_10

    # More volume + more momentum = more kinetic energy
    vol_ratio = avg_vol_10 / avg_vol_30 if avg_vol_30 > 0 else 1.0
    kin_raw = abs(momentum_10) * (0.5 + 0.5 * min(vol_ratio, 3.0))

    if momentum_10 > 3 and vol_ratio > 1.3:
        kin_score = 33  # strong upward thrust with volume
    elif momentum_10 > 0 and vol_ratio > 1.0:
        kin_score = 25
    elif momentum_10 > -3:
        kin_score = 15  # drifting
    elif momentum_10 < -5 and vol_ratio > 1.5:
        kin_score = 5  # strong downward thrust — dangerous energy
    else:
        kin_score = 10

    components["kinetic_energy"] = {
        "score": kin_score,
        "momentum_10d_pct": round(momentum_10, 2),
        "volume_ratio": round(vol_ratio, 2),
    }

    # ── Friction (0-20, inverted): Lower friction = better ──
    # Use ATR as volatility proxy for friction
    atr = (
        _compute_atr_simple(closes[-14:], closes[-14:], closes[-14:])
        if len(closes) >= 14
        else None
    )
    atr_pct = (atr / last_price * 100) if (last_price and atr) else None

    if atr_pct:
        if atr_pct < 1.5:
            fric_score = 18  # very low friction
        elif atr_pct < 2.5:
            fric_score = 14
        elif atr_pct < 4:
            fric_score = 10
        elif atr_pct < 6:
            fric_score = 6
        else:
            fric_score = 2  # high friction
    else:
        fric_score = 10
    components["friction"] = {
        "score": fric_score,
        "atr_pct": round(atr_pct, 2) if atr_pct else None,
    }

    # ── Heat (0-15): Realized volatility ──
    if len(returns_10) >= 5:
        vol_10d = _std(returns_10) * math.sqrt(252) * 100 if returns_10 else 0
        if vol_10d < 15:
            heat_score = 13  # cool — manageable
        elif vol_10d < 25:
            heat_score = 10
        elif vol_10d < 40:
            heat_score = 6
        else:
            heat_score = 2  # hot — unstable
    else:
        heat_score = 8
    components["heat"] = {
        "score": heat_score,
        "vol_annualized_pct": round(vol_10d, 1) if returns_10 else None,
    }

    total_energy = pot_score + kin_score + fric_score + heat_score
    energy_score = round(min(100, total_energy), 1)

    return {
        "energy_score": energy_score,
        "max_score": 100,
        "components": components,
    }


# ═══════════════════════════════════════════════════════════════════════════
# FUSION: Market Intelligence Verdict
# ═══════════════════════════════════════════════════════════════════════════


def compute_market_intelligence(
    ticker: str,
    pe: Optional[float] = None,
    roe: Optional[float] = None,
    pb: Optional[float] = None,
    dy: Optional[float] = None,
    eps: Optional[float] = None,
    sector: str = "",
) -> Dict[str, Any]:
    """Compute full market intelligence for a stock.

    This is the ENTRY POINT. Calls all four layers and fuses them.
    """
    result: Dict[str, Any] = {"ticker": ticker, "sector": sector}

    # ── Get price data from yfinance ──
    try:
        import yfinance as yf

        # Bursa tickers are digits-only; global have ^, =, - etc.
        yt_symbol = f"{ticker}.KL" if ticker.isdigit() else ticker
        yt = yf.Ticker(yt_symbol)
        hist = yt.history(period="6mo")
        if hist.empty:
            return {"error": f"No history for {ticker}", "status": "NEEDS_DATA"}

        closes = [float(x) for x in hist["Close"].tolist()]
        volumes = [int(x) for x in hist["Volume"].tolist()]
        highs = [float(x) for x in hist["High"].tolist()]
        lows = [float(x) for x in hist["Low"].tolist()]
        returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]

        result["last_price"] = round(closes[-1], 4)
        result["data_points"] = len(closes)
    except Exception:
        return {"error": "yfinance data unavailable", "status": "NEEDS_DATA"}

    norms = _match_sector(sector)

    # Layer 1: Invariant
    inv = compute_invariant_score(pe, roe, pb, dy, eps, sector)
    result["invariant"] = inv

    # Layer 2: Dynamic
    dyn = compute_dynamic_score(closes, volumes, highs, lows)
    result["dynamic"] = dyn

    # Layer 3: Entropy
    ent = compute_entropy_score(returns, closes)
    result["entropy"] = ent

    # Layer 4: Energy
    ene = compute_energy_profile(closes, volumes, pe, norms["pe"])
    result["energy"] = ene

    # ── FUSION ──
    weights = {"invariant": 0.40, "dynamic": 0.30, "entropy": 0.15, "energy": 0.15}
    total = (
        weights["invariant"] * inv.get("invariant_score", 50)
        + weights["dynamic"] * dyn.get("dynamic_score", 50)
        + weights["entropy"] * ent.get("entropy_score", 50)
        + weights["energy"] * ene.get("energy_score", 50)
    )
    result["fusion_score"] = round(total, 1)
    result["weights"] = weights

    # ── VERDICT ──
    if total >= 75:
        verdict = "COMPELLING"
    elif total >= 60:
        verdict = "INTERESTING"
    elif total >= 40:
        verdict = "NEUTRAL"
    elif total >= 25:
        verdict = "WEAK"
    else:
        verdict = "AVOID"

    result["verdict"] = verdict
    result["status"] = "OK"
    result["recommendation_only"] = True
    result["final_authority"] = "Arif"

    # ── Narrative ──
    result["narrative"] = _build_narrative(result, ticker)

    return result


def _build_narrative(result: Dict, ticker: str) -> str:
    """Build a human-readable narrative from the four-layer analysis."""
    inv = result.get("invariant", {})
    dyn = result.get("dynamic", {})
    ent = result.get("entropy", {})
    ene = result.get("energy", {})

    parts = [f"{ticker} Market Intelligence:"]

    # Invariant
    iscore = inv.get("invariant_score", 0)
    if iscore >= 75:
        parts.append(
            f"Strong fundamentals ({iscore}/100). Business quality above sector norms."
        )
    elif iscore >= 50:
        parts.append(
            f"Adequate fundamentals ({iscore}/100). Sector-average business quality."
        )
    else:
        parts.append(
            f"Weak fundamentals ({iscore}/100). Below sector norms — higher risk."
        )

    # Dynamic
    dscore = dyn.get("dynamic_score", 0)
    trend_info = dyn.get("components", {}).get("trend", {})
    if dscore >= 70:
        parts.append(f"Favorable technical state ({dscore}/100).")
    elif dscore >= 40:
        parts.append(f"Neutral technical state ({dscore}/100).")
    else:
        parts.append(
            f"Unfavorable technicals ({dscore}/100). Trend weak or liquidity thin."
        )

    # Entropy
    ent_score = ent.get("entropy_score", 50)
    regime = ent.get("regime", "UNKNOWN")
    if regime == "ORDERED":
        parts.append(
            f"Low entropy ({ent_score}/100) — {regime}. Signal clarity high. Market is predictable."
        )
    elif regime == "STRUCTURED":
        parts.append(
            f"Moderate entropy ({ent_score}/100) — {regime}. Some noise but structure visible."
        )
    elif regime == "NOISY":
        parts.append(
            f"High entropy ({ent_score}/100) — {regime}. Significant disorder. Edge is thin."
        )
    else:
        parts.append(
            f"Very high entropy ({ent_score}/100) — {regime}. Avoid. Market is a random walk."
        )

    # Energy
    escore = ene.get("energy_score", 50)
    pe_gap = ene.get("components", {}).get("potential_energy", {}).get("pe_gap")
    if pe_gap and pe_gap > 0.1:
        parts.append(
            f"Undervalued (PE gap {pe_gap * 100:.0f}%). Potential energy stored."
        )
    elif pe_gap and pe_gap < -0.1:
        parts.append(
            f"Overvalued (PE gap {pe_gap * 100:.0f}%). Potential energy depleted."
        )

    # Verdict
    parts.append(
        f"Fusion: {result.get('fusion_score', 0)}/100 — {result.get('verdict', '?')}."
    )
    parts.append("Recommendation only. NOT a trade signal. Arif decides.")

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# MINI MATH HELPERS — No heavy deps needed
# ═══════════════════════════════════════════════════════════════════════════


def _compute_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    for i in range(period + 1, len(prices)):
        d = prices[i] - prices[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(d, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-d, 0)) / period
    if avg_loss == 0:
        return 100.0
    return round(100.0 - 100.0 / (1.0 + avg_gain / avg_loss), 2)


def _macd_signal(prices: List[float]) -> bool:
    """True if MACD line > signal line."""
    if len(prices) < 35:
        return False

    def _ema(arr, p):
        mult = 2.0 / (p + 1)
        res = [sum(arr[:p]) / p]
        for i in range(p, len(arr)):
            res.append((arr[i] - res[-1]) * mult + res[-1])
        return res

    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    macd = [ema12[i] - ema26[i] for i in range(min(len(ema12), len(ema26)))]
    signal = _ema(macd, 9)
    return len(signal) > 1 and macd[-1] > signal[-1]


def _compute_atr_simple(
    highs: list, lows: list, closes: list, period: int = 14
) -> Optional[float]:
    if len(highs) < 2:
        return None
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sum(trs[-period:]) / min(period, len(trs)) if trs else None


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    return math.sqrt(sum((x - avg) ** 2 for x in values) / (len(values) - 1))


def _sample_entropy_approx(
    returns: List[float], m: int = 2, r_factor: float = 0.2
) -> Optional[float]:
    """Approximate sample entropy. Lower = more predictable."""
    if len(returns) < m + 2:
        return None
    r = _std(returns) * r_factor if _std(returns) > 0 else 0.01
    if r == 0:
        return None

    def _count_matches(template_len):
        count = 0
        for i in range(len(returns) - template_len):
            for j in range(i + 1, len(returns) - template_len):
                if (
                    max(
                        abs(returns[i + k] - returns[j + k])
                        for k in range(template_len)
                    )
                    < r
                ):
                    count += 1
        return max(count, 1)

    a = _count_matches(m + 1)
    b = _count_matches(m)
    return -math.log(a / b) if a > 0 and b > 0 else None
