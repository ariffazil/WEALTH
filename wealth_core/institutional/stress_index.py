"""
WEALTH Core — Institutional Stress Index Engine.

Pure computation: no I/O, no MCP, no side effects.

Composite 0-1 stress score connecting:
  - financial signals (profit decline, cost cutting)
  - governance signals (board erosion, resignations)
  - workforce signals (rightsizing, key departures)
  - legal signals (litigation, injunctions, regulatory uncertainty)
  - exploitation signals (payment freezes, interpleaders, competing claims)

APEX framework: G = A·P·E·X·Φ (multiplicative — zero in any collapses G)
F7 HUMILITY: confidence cap 0.90
F9 ANTI-HANTU: declare unknowns explicitly

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Confidence cap per F7 HUMILITY
_CONFIDENCE_CAP = 0.90


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _financial_stress(sig: Dict[str, Any]) -> float:
    """Score financial stress 0-1 from signals."""
    score = 0.0

    # Profit change: -50% or worse → 1.0, 0% → 0.0
    profit_chg = sig.get("profit_change_pct", 0.0)
    if profit_chg < 0:
        score += _clamp(abs(profit_chg) / 50.0) * 0.45

    # Revenue change: -30% or worse → 1.0, 0% → 0.0
    rev_chg = sig.get("revenue_change_pct", 0.0)
    if rev_chg < 0:
        score += _clamp(abs(rev_chg) / 30.0) * 0.35

    # Cost cutting announced → binary flag
    if sig.get("cost_cutting_announced", False):
        score += 0.20

    return _clamp(score)


def _governance_stress(sig: Dict[str, Any]) -> float:
    """Score governance erosion 0-1 from signals."""
    score = 0.0

    # Board resignations in 12m relative to board size
    resignations = sig.get("board_resignations_12m", 0)
    board_size = sig.get("board_size", 7)
    if board_size > 0:
        resign_ratio = resignations / board_size
        # 30%+ resignations → 1.0
        score += _clamp(resign_ratio / 0.30) * 0.35

    # Company secretaries serving as directors (governance weakness)
    if sig.get("company_secretaries_as_directors", False):
        score += 0.20

    # Low average tenure (instability) — below 3 years is concerning
    tenure = sig.get("avg_tenure_years", 5.0)
    if tenure < 5.0:
        score += _clamp((5.0 - tenure) / 5.0) * 0.20

    # Board size too small (below 5) or too large (above 15) is a signal
    if board_size < 5:
        score += 0.15
    elif board_size < 7:
        score += 0.10

    # High resignation count absolute
    if resignations >= 3:
        score += 0.10

    return _clamp(score)


def _workforce_stress(sig: Dict[str, Any]) -> float:
    """Score workforce destabilization 0-1."""
    score = 0.0

    # Rightsizing percentage: 15%+ → 1.0
    rightsizing = sig.get("rightsizing_pct", 0.0)
    score += _clamp(rightsizing / 15.0) * 0.35

    # Voluntary exits: 10%+ → 1.0
    exits = sig.get("voluntary_exits_pct", 0.0)
    score += _clamp(exits / 10.0) * 0.30

    # Key personnel departures — each one adds stress
    departures = sig.get("key_personnel_departures", [])
    if departures:
        # Accept both int (count) and list (names) — F12 INJECTION: type-safe
        dep_count = departures if isinstance(departures, int) else len(departures)
        # 5+ key departures → max
        score += _clamp(dep_count / 5.0) * 0.35

    return _clamp(score)


def _legal_stress(sig: Dict[str, Any]) -> float:
    """Score legal exposure 0-1."""
    score = 0.0

    # Active litigation count: 5+ → 1.0
    lit_count = sig.get("active_litigation_count", 0)
    score += _clamp(lit_count / 5.0) * 0.30

    # Injunction value: $500M+ → 1.0
    inj_value = sig.get("injunction_value_musd", 0.0)
    score += _clamp(inj_value / 500.0) * 0.35

    # Regulatory uncertainty: direct 0-1
    reg_unc = sig.get("regulatory_uncertainty_score", 0.0)
    score += _clamp(reg_unc) * 0.35

    return _clamp(score)


def _exploitation_stress(sig: Dict[str, Any]) -> float:
    """Score external exploitation signals 0-1."""
    score = 0.0

    if sig.get("counterparty_payment_freeze", False):
        score += 0.35

    if sig.get("interpleader_filed", False):
        score += 0.35

    if sig.get("competing_claims", False):
        score += 0.30

    return _clamp(score)


def _detect_feedback_loop(
    financial: float,
    governance: float,
    workforce: float,
    legal: float,
    exploitation: float,
) -> bool:
    """
    Detect whether the stress pattern suggests a feedback loop.

    A feedback loop exists when:
    - At least 3 of 5 stress dimensions are above 0.5 (multi-dimensional)
    - AND exploitation signals are present (external actors acting on weakness)
    - AND financial stress is present (the loop's fuel)

    This is the "institutional collapse spiral":
      financial stress → rightsizing → governance erosion →
      intelligence compromise → external exploitation → more financial stress
    """
    high_count = sum(
        1 for s in [financial, governance, workforce, legal, exploitation] if s > 0.5
    )
    return high_count >= 3 and exploitation > 0.3 and financial > 0.3


def _risk_level(stress_index: float) -> str:
    """Map stress index to risk level."""
    if stress_index >= 0.80:
        return "CRITICAL"
    elif stress_index >= 0.60:
        return "RED"
    elif stress_index >= 0.35:
        return "YELLOW"
    else:
        return "GREEN"


def _generate_recommendations(
    component_scores: Dict[str, float],
    feedback_loop: bool,
    risk_level: str,
) -> List[str]:
    """Generate actionable recommendations based on component scores."""
    recs = []

    if component_scores.get("financial", 0) > 0.5:
        recs.append(
            "FINANCIAL: Review cost structure and revenue diversification. "
            "Rightsizing alone creates feedback loop risk."
        )

    if component_scores.get("governance", 0) > 0.5:
        recs.append(
            "GOVERNANCE: Board stability compromised. Accelerate independent NED "
            "appointments. Review company secretary dual-role policy."
        )

    if component_scores.get("workforce", 0) > 0.5:
        recs.append(
            "WORKFORCE: Key personnel departures signal intelligence compromise risk. "
            "Implement retention packages for mission-critical roles."
        )

    if component_scores.get("legal", 0) > 0.5:
        recs.append(
            "LEGAL: High litigation exposure. Consolidate legal strategy. "
            "Assess counterparty exploitation vectors through legal channels."
        )

    if component_scores.get("exploitation", 0) > 0.5:
        recs.append(
            "EXPLOITATION: Counterparty behavior suggests rational exploitation "
            "of institutional weakness. Map all affected contracts and obligations."
        )

    if feedback_loop:
        recs.append(
            "⚠ FEEDBACK LOOP DETECTED: Multi-dimensional stress with external "
            "exploitation. Break the cycle at the weakest link — likely governance "
            "or workforce. Do NOT focus solely on financial metrics."
        )

    if risk_level == "CRITICAL":
        recs.append(
            "CRITICAL: Institutional stress at crisis level. Consider arifOS "
            "judge handoff for constitutional assessment."
        )

    return recs


def compute_stress_index(
    org_name: str,
    financial_signals: Dict[str, Any],
    governance_signals: Dict[str, Any],
    workforce_signals: Dict[str, Any],
    legal_signals: Dict[str, Any],
    exploitation_signals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute composite institutional stress index.

    Returns:
      - stress_index: 0-1 composite score
      - component_scores: per-dimension scores
      - risk_level: GREEN/YELLOW/RED/CRITICAL
      - feedback_loop_detected: bool
      - recommendations: list of actionable strings
      - confidence: capped at 0.90 (F7 HUMILITY)
    """
    financial = _financial_stress(financial_signals)
    governance = _governance_stress(governance_signals)
    workforce = _workforce_stress(workforce_signals)
    legal = _legal_stress(legal_signals)
    exploitation = _exploitation_stress(exploitation_signals)

    # Composite: weighted average (not multiplicative — stress is additive)
    # Weights: financial 0.30, governance 0.25, workforce 0.20, legal 0.15, exploitation 0.10
    stress_index = (
        financial * 0.30
        + governance * 0.25
        + workforce * 0.20
        + legal * 0.15
        + exploitation * 0.10
    )
    stress_index = _clamp(stress_index)

    component_scores = {
        "financial": round(financial, 4),
        "governance": round(governance, 4),
        "workforce": round(workforce, 4),
        "legal": round(legal, 4),
        "exploitation": round(exploitation, 4),
    }

    feedback_loop = _detect_feedback_loop(
        financial, governance, workforce, legal, exploitation
    )
    risk_level = _risk_level(stress_index)
    recommendations = _generate_recommendations(
        component_scores, feedback_loop, risk_level
    )

    # F7 HUMILITY: confidence cap
    # Confidence is lower when we have fewer signals
    signal_count = sum(
        1
        for sig in [
            financial_signals,
            governance_signals,
            workforce_signals,
            legal_signals,
            exploitation_signals,
        ]
        if sig
    )
    confidence = min(_CONFIDENCE_CAP, signal_count / 5.0)

    return {
        "org_name": org_name,
        "stress_index": round(stress_index, 4),
        "component_scores": component_scores,
        "risk_level": risk_level,
        "feedback_loop_detected": feedback_loop,
        "recommendations": recommendations,
        "confidence": round(confidence, 4),
        "confidence_note": "Capped at 0.90 per F7 HUMILITY",
    }
