"""
WEALTH Calhoun Guard — Universe 25, Strange Loop, Gödel, Anti-Beautiful
══════════════════════════════════════════════════════════════════════════

Four philosophical locks forged into machine-enforceable gates:

  CALHOUN LOCK:    Perfect conditions breed extinction.
                   Detect complacency → tighten gates, not loosen.

  STRANGE LOOP:    Any widely-adopted edge arbitrages itself.
                   Track pattern decay → retire signals that stop working.

  GÖDEL LOCK:      The system cannot prove its own consistency.
                   Flag unverifiable assumptions → downgrade conviction.

  ANTI-BEAUTIFUL:  Elegant rules are fragile. Redundancy survives.
                   Enforce multi-pillar confirmation → fail closed.

These four locks enrich EVERY 888 JUDGE verdict with:
  - calhoun_flags[]       — utopia warning signs
  - strange_loop_flags[]  — self-arbitrage decay
  - godel_flags[]         — unprovable assumptions
  - anti_beautiful_flags[] — single-pillar fragility
  - survival_score         — 0-100 composite survival probability
  - extinction_risk        — LOW / ELEVATED / HIGH / CRITICAL

DITEMPA BUKAN DIBERI — Survival is the only alpha that doesn't decay.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# CALHOUN LOCK — Universe 25 Detector
# ═══════════════════════════════════════════════════════════════════════════


def detect_calhoun(
    closes: List[float],
    volumes: List[int],
    positions: int = 0,
    max_positions: int = 5,
) -> Dict[str, Any]:
    """Detect Universe 25 conditions: complacency → extinction.

    Calhoun's mice had EVERYTHING. No constraints. No struggle.
    They withdrew, became pathological, and went extinct.

    Market analogue:
      • Volatility abnormally low → complacency
      • Position count at max → overcrowding
      • Volume declining while prices rising → participation collapse
      • Tight range with no drawdowns → energy stored for explosion
    """
    flags: List[Dict] = []
    score = 50.0  # starts neutral

    if len(closes) < 60 or len(volumes) < 60:
        return {
            "calhoun_score": 50,
            "flags": [],
            "extinction_risk": "UNKNOWN",
            "verdict": "Insufficient data for Calhoun detection",
        }

    # ── Volatility Complacency ──
    returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    recent_vol = _std(returns[-20:]) if len(returns) >= 20 else 0
    historical_vol = _std(returns[-60:]) if len(returns) >= 60 else recent_vol

    if historical_vol > 0:
        vol_ratio = recent_vol / historical_vol
    else:
        vol_ratio = 1.0

    if vol_ratio < 0.5:
        flags.append(
            {
                "lock": "CALHOUN",
                "severity": "HIGH",
                "signal": "Volatility collapse — complacency extreme",
                "action": "Tighten stops, reduce position size",
            }
        )
        score -= 25
    elif vol_ratio < 0.7:
        flags.append(
            {
                "lock": "CALHOUN",
                "severity": "MEDIUM",
                "signal": "Volatility compressing — energy building",
                "action": "Monitor closely, don't add positions",
            }
        )
        score -= 10

    # ── Volume Decline (participation collapse) ──
    vol_10d = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else 0
    vol_60d = sum(volumes[-60:]) / 60 if len(volumes) >= 60 else vol_10d
    if vol_60d > 0 and vol_10d / vol_60d < 0.6:
        flags.append(
            {
                "lock": "CALHOUN",
                "severity": "MEDIUM",
                "signal": "Volume collapsing — participants withdrawing",
                "action": "Calhoun withdrawal pattern. Reduce exposure.",
            }
        )
        score -= 12

    # ── Drawdown Absence (utopia check) ──
    peak = max(closes[-60:]) if len(closes) >= 60 else closes[-1]
    current = closes[-1]
    dd_from_peak = (peak - current) / peak * 100 if peak > 0 else 0
    if dd_from_peak < 3 and vol_ratio < 0.7:
        flags.append(
            {
                "lock": "CALHOUN",
                "severity": "HIGH",
                "signal": "No drawdown + low vol = utopia. Calhoun extinction ahead.",
                "action": "This is the most dangerous market state. Tighten ALL gates.",
            }
        )
        score -= 15

    # ── Position Crowding ──
    if positions >= max_positions:
        flags.append(
            {
                "lock": "CALHOUN",
                "severity": "MEDIUM",
                "signal": f"Portfolio at capacity ({positions}/{max_positions}) — no room for new ideas",
                "action": "Must close a position before opening new one",
            }
        )
        score -= 8

    score = max(5, min(95, score))

    if score >= 70:
        risk = "LOW"
    elif score >= 45:
        risk = "ELEVATED"
    elif score >= 25:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    return {
        "calhoun_score": score,
        "extinction_risk": risk,
        "flags": flags,
        "metrics": {
            "vol_ratio": round(vol_ratio, 3),
            "vol_10d_pct": round(recent_vol * math.sqrt(252) * 100, 2),
            "drawdown_from_peak_pct": round(dd_from_peak, 2),
            "positions": f"{positions}/{max_positions}",
        },
        "verdict": f"Calhoun extinction risk: {risk}"
        + (f" ({len(flags)} warnings)" if flags else ""),
    }


# ═══════════════════════════════════════════════════════════════════════════
# STRANGE LOOP LOCK — Self-Arbitraging Alpha Detector
# ═══════════════════════════════════════════════════════════════════════════


def detect_strange_loop(
    pattern_usage_count: int = 0,
    pattern_recent_hit_rate: float = 0.5,
    pattern_age_days: int = 0,
    market_participants_estimate: str = "moderate",
) -> Dict[str, Any]:
    """Detect Strange Loop: signals that are eating themselves.

    "If this screener works, everyone uses it.
     If everyone uses it, the signal is arbitraged.
     If the signal is arbitraged, it stops working."

    This lock tracks signal decay and retires patterns before they hurt you.
    """
    flags: List[Dict] = []
    score = 50.0

    # ── Pattern Overuse ──
    if pattern_usage_count > 100:
        flags.append(
            {
                "lock": "STRANGE_LOOP",
                "severity": "HIGH",
                "signal": f"Pattern used {pattern_usage_count} times — highly visible",
                "action": "Consider retiring or rotating to alternative pattern",
            }
        )
        score -= 20
    elif pattern_usage_count > 50:
        flags.append(
            {
                "lock": "STRANGE_LOOP",
                "severity": "MEDIUM",
                "signal": f"Pattern used {pattern_usage_count} times — becoming crowded",
                "action": "Reduce position size, monitor for decay",
            }
        )
        score -= 10

    # ── Performance Decay ──
    if pattern_age_days > 180 and pattern_recent_hit_rate < 0.4:
        flags.append(
            {
                "lock": "STRANGE_LOOP",
                "severity": "HIGH",
                "signal": f"Pattern {pattern_age_days}d old, hit rate fallen to {pattern_recent_hit_rate:.0%}",
                "action": "RETIRE pattern. Strange loop has arbitraged the edge.",
            }
        )
        score -= 25
    elif pattern_age_days > 90 and pattern_recent_hit_rate < 0.45:
        flags.append(
            {
                "lock": "STRANGE_LOOP",
                "severity": "MEDIUM",
                "signal": f"Pattern aging ({pattern_age_days}d), hit rate declining",
                "action": "Start searching for replacement pattern",
            }
        )
        score -= 12

    # ── Market Crowding ──
    if market_participants_estimate == "crowded":
        flags.append(
            {
                "lock": "STRANGE_LOOP",
                "severity": "HIGH",
                "signal": "Market appears crowded — many participants likely using similar signals",
                "action": "All edges are duller in crowded markets. Reduce size.",
            }
        )
        score -= 15

    score = max(5, min(95, score))

    return {
        "strange_loop_score": score,
        "pattern_validity": "EMERGING"
        if score >= 70
        else ("MATURE" if score >= 45 else ("CROWDED" if score >= 25 else "RETIRED")),
        "flags": flags,
        "verdict": f"Strange Loop signal decay: pattern is {_loop_grade(score)}",
    }


# ═══════════════════════════════════════════════════════════════════════════
# GÖDEL LOCK — Unprovable Truths Detector
# ═══════════════════════════════════════════════════════════════════════════


def detect_godel(
    data_completeness: Dict[str, bool] = None,
    requires_narrative: List[str] = None,
    unverifiable_assumptions: List[str] = None,
) -> Dict[str, Any]:
    """Detect Gödel Incompleteness: what the system can't prove.

    "Any system complex enough to model the market
     contains truths it cannot prove about itself."

    This lock identifies and annotates unprovable claims,
    downgrading conviction when decisions rely on narrative.
    """
    if data_completeness is None:
        data_completeness = {}
    if requires_narrative is None:
        requires_narrative = []
    if unverifiable_assumptions is None:
        unverifiable_assumptions = []

    flags: List[Dict] = []
    score = 50.0
    unknowns: List[str] = []

    # ── Missing Data ──
    missing = [k for k, v in data_completeness.items() if not v]
    if missing:
        flags.append(
            {
                "lock": "GODEL",
                "severity": "HIGH",
                "signal": f"Missing data: {', '.join(missing)}",
                "action": "Downgrade conviction. Cannot prove thesis without these fields.",
            }
        )
        score -= 15 * len(missing)
        unknowns.extend(missing)

    # ── Narrative-Dependent Claims ──
    if requires_narrative:
        flags.append(
            {
                "lock": "GODEL",
                "severity": "MEDIUM",
                "signal": f"Decision relies on external narrative: {', '.join(requires_narrative)}",
                "action": "These claims cannot be verified from data alone. Size conservatively.",
            }
        )
        score -= 8 * len(requires_narrative)
        unknowns.extend([f"NARRATIVE:{n}" for n in requires_narrative])

    # ── Unverifiable Assumptions ──
    if unverifiable_assumptions:
        flags.append(
            {
                "lock": "GODEL",
                "severity": "CRITICAL",
                "signal": f"Unverifiable assumptions: {', '.join(unverifiable_assumptions)}",
                "action": "ESSENTIAL: assumptions cannot be falsified. Maximum caution.",
            }
        )
        score -= 20 * len(unverifiable_assumptions)
        unknowns.extend([f"ASSUMPTION:{a}" for a in unverifiable_assumptions])

    score = max(5, min(95, score))

    return {
        "godel_score": score,
        "provability": "PROVABLE"
        if score >= 70
        else ("PARTIALLY_PROVABLE" if score >= 40 else "UNPROVABLE"),
        "unknowns": unknowns,
        "flags": flags,
        "verdict": f"Gödel lock: {len(unknowns)} unprovable claims — conviction downgraded to {score}/100",
    }


# ═══════════════════════════════════════════════════════════════════════════
# ANTI-BEAUTIFUL LOCK — Redundancy Enforcer
# ═══════════════════════════════════════════════════════════════════════════


def detect_anti_beautiful(
    f_score: float = 0,
    t_score: float = 0,
    w_score: float = 0,
    f_pillars_passing: int = 0,
    t_pillars_passing: int = 0,
    w_pillars_passing: int = 0,
) -> Dict[str, Any]:
    """Detect Anti-Beautiful fragility: single-pillar dependence.

    "The most beautiful solution is the most fragile.
     Ugly, redundant, multi-layered systems survive."

    This lock ensures no single indicator carries the entire decision.
    If fundamentals are great but technicals are terrible = FAIL.
    """
    flags: List[Dict] = []
    score = 50.0

    # ── Single-Pillar Dominance ──
    if f_score > 70 and t_score < 30:
        flags.append(
            {
                "lock": "ANTI_BEAUTIFUL",
                "severity": "HIGH",
                "signal": f"Fundamentals strong ({f_score}) but technicals broken ({t_score})",
                "action": "Beautiful fundamentals in an ugly market = trap. HOLD.",
            }
        )
        score -= 20
    if t_score > 70 and f_score < 30:
        flags.append(
            {
                "lock": "ANTI_BEAUTIFUL",
                "severity": "HIGH",
                "signal": f"Technicals strong ({t_score}) but fundamentals broken ({f_score})",
                "action": "Beautiful chart, ugly business = speculation. HOLD.",
            }
        )
        score -= 20
    if f_score > 70 and t_score > 70 and w_score < 30:
        flags.append(
            {
                "lock": "ANTI_BEAUTIFUL",
                "severity": "CRITICAL",
                "signal": "Fundamentals and technicals strong but flows broken — sizing will kill you",
                "action": "Beautiful setup with broken execution. Fix flows before entry.",
            }
        )
        score -= 25

    # ── Pillar Count Check ──
    if f_pillars_passing > 0 and f_pillars_passing < 3:
        flags.append(
            {
                "lock": "ANTI_BEAUTIFUL",
                "severity": "MEDIUM",
                "signal": f"Only {f_pillars_passing} fundamental pillars passing — thin evidence",
                "action": "Need broader fundamental confirmation",
            }
        )
        score -= 8
    if t_pillars_passing > 0 and t_pillars_passing < 3:
        flags.append(
            {
                "lock": "ANTI_BEAUTIFUL",
                "severity": "MEDIUM",
                "signal": f"Only {t_pillars_passing} technical pillars passing — thin confirmation",
                "action": "Need broader technical confirmation",
            }
        )
        score -= 8

    # ── Correlation Trap ──
    if f_pillars_passing > 0 and t_pillars_passing > 0:
        overlap = min(f_pillars_passing, t_pillars_passing)
        if overlap >= 5:
            # Many pillars passing = good redundancy
            score += 10

    score = max(5, min(95, score))

    return {
        "anti_beautiful_score": score,
        "redundancy": "ROBUST"
        if score >= 70
        else (
            "ADEQUATE"
            if score >= 45
            else ("FRAGILE" if score >= 25 else "SINGLE_POINT_FAILURE")
        ),
        "flags": flags,
        "pillars": {
            "f_passing": f_pillars_passing,
            "t_passing": t_pillars_passing,
            "w_passing": w_pillars_passing,
        },
        "verdict": f"Anti-Beautiful redundancy: {_redundancy_grade(score)}",
    }


# ═══════════════════════════════════════════════════════════════════════════
# SURVIVAL SCORE — Composite extinction probability
# ═══════════════════════════════════════════════════════════════════════════


def compute_survival_score(
    closes: List[float],
    volumes: List[int],
    f_score: float = 50,
    t_score: float = 50,
    w_score: float = 50,
    positions: int = 0,
    max_positions: int = 5,
    data_completeness: Optional[Dict] = None,
    pattern_usage: int = 0,
    pattern_hit_rate: float = 0.5,
    pattern_age: int = 0,
) -> Dict[str, Any]:
    """Compute composite survival score from all four locks.

    Returns 0-100 score and extinction risk level.
    Used as a MODIFIER on 888 conviction and position sizing.
    """
    calhoun = detect_calhoun(closes, volumes, positions, max_positions)
    loop = detect_strange_loop(pattern_usage, pattern_hit_rate, pattern_age)
    godel = detect_godel(data_completeness or {}, [], [])
    anti = detect_anti_beautiful(
        f_score,
        t_score,
        w_score,
        sum(
            1
            for x in [
                f_score > 50,
                f_score > 40,
                t_score > 50,
                t_score > 40,
                w_score > 50,
            ]
        ),
        sum(1 for x in [t_score > 50, t_score > 40, w_score > 50]),
        sum(1 for x in [w_score > 50, w_score > 40]),
    )

    all_flags = []
    for lock in [calhoun, loop, godel, anti]:
        all_flags.extend(lock.get("flags", []))

    # Weighted fusion
    survival = (
        calhoun["calhoun_score"] * 0.30
        + loop["strange_loop_score"] * 0.25
        + godel["godel_score"] * 0.25
        + anti["anti_beautiful_score"] * 0.20
    )

    survival = round(max(5, min(95, survival)), 1)

    # Extinction risk
    critical_count = sum(1 for f in all_flags if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in all_flags if f.get("severity") == "HIGH")

    if critical_count >= 2 or survival < 25:
        extinction_risk = "CRITICAL"
        verdict = "888 SABAR: Extinction risk critical. Cease all new entries."
    elif high_count >= 3 or survival < 45:
        extinction_risk = "HIGH"
        verdict = "888 HOLD: High extinction risk. Reduce exposure, no new entries."
    elif high_count >= 1 or survival < 65:
        extinction_risk = "ELEVATED"
        verdict = "888 CAUTION: Elevated risk. Tighten stops, reduce size."
    else:
        extinction_risk = "LOW"
        verdict = "888 PROCEED: Acceptable survival probability. Within risk budget."

    return {
        "survival_score": survival,
        "extinction_risk": extinction_risk,
        "verdict": verdict,
        "locks": {
            "calhoun": {
                "score": calhoun["calhoun_score"],
                "risk": calhoun["extinction_risk"],
                "flags": calhoun["flags"],
            },
            "strange_loop": {
                "score": loop["strange_loop_score"],
                "validity": loop["pattern_validity"],
                "flags": loop["flags"],
            },
            "godel": {
                "score": godel["godel_score"],
                "provability": godel["provability"],
                "unknowns": godel["unknowns"],
            },
            "anti_beautiful": {
                "score": anti["anti_beautiful_score"],
                "redundancy": anti["redundancy"],
                "flags": anti["flags"],
            },
        },
        "all_flags": all_flags,
        "flag_summary": f"{critical_count}C/{high_count}H/{len(all_flags)} total flags",
        "feynman_note": "The first principle is that you must not fool yourself — and you are the easiest person to fool. These locks are your anti-self-deception system.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# ENRICHED 888 — JUDGE with Calhoun/Gödel/Strange Loop/Anti-Beautiful
# ═══════════════════════════════════════════════════════════════════════════


def enrich_888_verdict(
    ticker: str,
    closes: List[float],
    volumes: List[int],
    f_score: float = 50,
    t_score: float = 50,
    w_score: float = 50,
    f_hold: bool = False,
    t_hold: bool = False,
    w_hold: bool = False,
    positions: int = 0,
    max_positions: int = 5,
    data_completeness: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Enrich an 888 JUDGE verdict with all four philosophical locks.

    Call this AFTER compute_888() to add Calhoun/StrangeLoop/Gödel/AntiBeautiful
    annotations to the verdict.
    """
    survival = compute_survival_score(
        closes,
        volumes,
        f_score,
        t_score,
        w_score,
        positions,
        max_positions,
        data_completeness,
    )

    # Combine 888 gates with survival score
    base_888_proceed = not (f_hold or t_hold or w_hold)
    survival_ok = survival["extinction_risk"] == "LOW"

    if not base_888_proceed:
        verdict = "HOLD"
        reason = "888 gate triggered"
    elif not survival_ok:
        verdict = "HOLD"
        reason = f"Survival risk: {survival['extinction_risk']}"
    else:
        conviction = f_score * 0.40 + t_score * 0.35 + w_score * 0.25
        adjusted_conviction = conviction * (survival["survival_score"] / 100)

        if adjusted_conviction >= 65:
            verdict = "PROCEED"
            reason = (
                f"Conviction {adjusted_conviction:.0f}/100 after survival adjustment"
            )
        elif adjusted_conviction >= 45:
            verdict = "CAUTION"
            reason = (
                f"Reduced conviction {adjusted_conviction:.0f}/100 — size down by half"
            )
        else:
            verdict = "HOLD"
            reason = f"Conviction {adjusted_conviction:.0f}/100 too low after survival adjustment"

    return {
        "ticker": ticker,
        "verdict": verdict,
        "reason": reason,
        "base_888_proceed": base_888_proceed,
        "survival": survival,
        "adjusted_conviction": round(
            (f_score * 0.40 + t_score * 0.35 + w_score * 0.25)
            * (survival["survival_score"] / 100),
            1,
        )
        if base_888_proceed
        else 0,
        "narrative": _build_survival_narrative(
            ticker, verdict, survival, f_score, t_score, w_score
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    return math.sqrt(sum((x - avg) ** 2 for x in values) / (len(values) - 1))


def _loop_grade(score: float) -> str:
    if score >= 70:
        return "EMERGING — fresh edge, not yet arbitraged"
    if score >= 45:
        return "MATURE — still works but monitor for decay"
    if score >= 25:
        return "CROWDED — edge deteriorating, reduce reliance"
    return "RETIRED — strange loop has consumed this edge"


def _redundancy_grade(score: float) -> str:
    if score >= 70:
        return "ROBUST — multiple pillars confirm, no single point of failure"
    if score >= 45:
        return "ADEQUATE — reasonable redundancy, some gaps acceptable"
    if score >= 25:
        return "FRAGILE — thin confirmation, single break could collapse thesis"
    return "SINGLE_POINT_FAILURE — one broken pillar and the whole thesis falls"


def _build_survival_narrative(
    ticker: str, verdict: str, survival: Dict, f: float, t: float, w: float
) -> str:
    locks = survival.get("locks", {})
    c = locks.get("calhoun", {})
    s = locks.get("strange_loop", {})
    g = locks.get("godel", {})
    a = locks.get("anti_beautiful", {})

    parts = [
        f"═══ CALHOUN SURVIVAL: {ticker} ═══",
        f"888 Base:       F={f:.0f} T={t:.0f} W={w:.0f}",
        f"Survival Score: {survival['survival_score']}/100 — {survival['extinction_risk']}",
        f"Calhoun:        {c.get('score', 50)}/100 ({c.get('risk', '?')}) — {len(c.get('flags', []))} utopia warnings",
        f"Strange Loop:   {s.get('score', 50)}/100 ({s.get('validity', '?')}) — {len(s.get('flags', []))} decay flags",
        f"Gödel:          {g.get('score', 50)}/100 ({g.get('provability', '?')}) — {len(g.get('unknowns', []))} unknowns",
        f"Anti-Beautiful: {a.get('score', 50)}/100 ({a.get('redundancy', '?')}) — {len(a.get('flags', []))} fragility flags",
        f"═ VERDICT: {verdict}",
        survival.get("verdict", ""),
        f"═ {survival.get('feynman_note', '')}",
    ]
    return "\n".join(parts)
