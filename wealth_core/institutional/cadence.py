"""
WEALTH Core — Institutional Breath: Cadence Monitor (Channel B).

Measures the institution's metabolic rhythm: approval cadence, payment cycles,
decision velocity, meeting-to-decision ratio, contract signature velocity.

The breath is the first thing that goes when an institution is under stress.
You can fake a balance sheet. You can't fake your breathing rhythm.

DITEMPA BUKAN DIBERI — Forged 2026-07-12.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def compute_cadence(
    approval_cycles: Optional[List[Dict[str, Any]]] = None,
    payment_cycles: Optional[List[Dict[str, Any]]] = None,
    meeting_logs: Optional[List[Dict[str, Any]]] = None,
    contract_signatures: Optional[List[Dict[str, Any]]] = None,
    budget_releases: Optional[List[Dict[str, Any]]] = None,
    org_name: str = "",
) -> Dict[str, Any]:
    """
    Compute institutional cadence health (0.0–1.0).

    Accepts optional time-series data for each dimension.
    Missing dimensions return UNKNOWN with a warning — never silently zero.

    Returns dict with:
      - cadence_health: composite score 0.0–1.0
      - band: RHYTHMIC | ARRHYTHMIC | STUTTERING | APNEIC | INSUFFICIENT_DATA
      - components: per-dimension scores
      - trend: improving | stable | declining | insufficient_data
      - warnings: list of data quality warnings
      - alternative_explanations: competing interpretations
      - falsification_test: what would disprove the reading
    """
    components: Dict[str, Any] = {}
    warnings: List[str] = []
    data_count = 0

    # ── 1. Approval Centralisation ────────────────────────────────────
    if approval_cycles and len(approval_cycles) >= 2:
        data_count += 1
        approval_score, approval_warning = _score_approval_centralisation(
            approval_cycles
        )
        components["approval_centralisation"] = {
            "score": approval_score,
            "description": "Are decisions moving upward? More approvals per decision = centralisation",
            "data_points": len(approval_cycles),
        }
        if approval_warning:
            warnings.append(approval_warning)
    else:
        components["approval_centralisation"] = {
            "score": None,
            "description": "Are decisions moving upward?",
            "data_points": 0,
            "status": "UNKNOWN",
        }
        warnings.append("APPROVAL_DATA: Insufficient approval cycle data")

    # ── 2. Payment Stretching ─────────────────────────────────────────
    if payment_cycles and len(payment_cycles) >= 2:
        data_count += 1
        payment_score, payment_warning = _score_payment_stretching(payment_cycles)
        components["payment_stretching"] = {
            "score": payment_score,
            "description": "Are payment cycles lengthening? Supplier payment days trend",
            "data_points": len(payment_cycles),
        }
        if payment_warning:
            warnings.append(payment_warning)
    else:
        components["payment_stretching"] = {
            "score": None,
            "description": "Are payment cycles lengthening?",
            "data_points": 0,
            "status": "UNKNOWN",
        }
        warnings.append("PAYMENT_DATA: Insufficient payment cycle data")

    # ── 3. Decision Backlog ───────────────────────────────────────────
    if meeting_logs and len(meeting_logs) >= 2:
        data_count += 1
        backlog_score, backlog_warning = _score_decision_backlog(meeting_logs)
        components["decision_backlog"] = {
            "score": backlog_score,
            "description": "Are decisions piling up? Meeting-to-decision ratio",
            "data_points": len(meeting_logs),
        }
        if backlog_warning:
            warnings.append(backlog_warning)
    else:
        components["decision_backlog"] = {
            "score": None,
            "description": "Are decisions piling up?",
            "data_points": 0,
            "status": "UNKNOWN",
        }
        warnings.append("MEETING_DATA: Insufficient meeting/decision data")

    # ── 4. Contract Velocity ──────────────────────────────────────────
    if contract_signatures and len(contract_signatures) >= 2:
        data_count += 1
        contract_score, contract_warning = _score_contract_velocity(contract_signatures)
        components["contract_velocity"] = {
            "score": contract_score,
            "description": "Are new commitments slowing? Contract signature rate",
            "data_points": len(contract_signatures),
        }
        if contract_warning:
            warnings.append(contract_warning)
    else:
        components["contract_velocity"] = {
            "score": None,
            "description": "Are new commitments slowing?",
            "data_points": 0,
            "status": "UNKNOWN",
        }
        warnings.append("CONTRACT_DATA: Insufficient contract signature data")

    # ── 5. Budget Release Timing ──────────────────────────────────────
    if budget_releases and len(budget_releases) >= 2:
        data_count += 1
        budget_score, budget_warning = _score_budget_release_timing(budget_releases)
        components["budget_release_timing"] = {
            "score": budget_score,
            "description": "Is budget being held or delayed? Q1 vs Q4 release ratio",
            "data_points": len(budget_releases),
        }
        if budget_warning:
            warnings.append(budget_warning)
    else:
        components["budget_release_timing"] = {
            "score": None,
            "description": "Is budget being held or delayed?",
            "data_points": 0,
            "status": "UNKNOWN",
        }
        warnings.append("BUDGET_DATA: Insufficient budget release data")

    # ── Composite ─────────────────────────────────────────────────────
    scores = [c["score"] for c in components.values() if c.get("score") is not None]

    if data_count == 0:
        return {
            "cadence_health": None,
            "band": "INSUFFICIENT_DATA",
            "components": components,
            "trend": "insufficient_data",
            "warnings": warnings + ["No data provided for any cadence dimension"],
            "alternative_explanations": [
                "No measurement possible without data",
                "Institution may be operating normally but no data was supplied",
            ],
            "falsification_test": "Provide data for at least one dimension to produce a reading",
            "data_dimensions_active": data_count,
            "data_dimensions_total": 5,
            "org_name": org_name,
        }

    composite = sum(scores) / len(scores)
    band = _classify_band(composite)
    trend = _infer_trend(components)

    alternative_explanations = _generate_alternatives(components, band, data_count)
    falsification_test = _generate_falsification(band, data_count)

    return {
        "cadence_health": round(composite, 4),
        "band": band,
        "components": components,
        "trend": trend,
        "warnings": warnings,
        "alternative_explanations": alternative_explanations,
        "falsification_test": falsification_test,
        "data_dimensions_active": data_count,
        "data_dimensions_total": 5,
        "org_name": org_name,
    }


def _score_approval_centralisation(
    cycles: List[Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    """
    Score approval centralisation (1.0 = healthy, 0.0 = fully centralised).

    Expects list of dicts with:
      - period: str (e.g. "2024-Q1")
      - approvals_required: int (avg approvals per decision)
      - decisions_made: int (total decisions in period)
      - approval_level: str (optional, "local" | "regional" | "executive" | "board")
    """
    period_count = len(cycles)

    # Trend: are approvals per decision rising?
    if period_count >= 2:
        first_approvals = cycles[0].get("approvals_required", 0)
        last_approvals = cycles[-1].get("approvals_required", 0)
        if first_approvals > 0 and last_approvals > 0:
            centralisation_trend = (last_approvals - first_approvals) / first_approvals
        else:
            centralisation_trend = 0.0
    else:
        centralisation_trend = 0.0

    # Score based on avg approvals per decision
    avg_approvals = sum(c.get("approvals_required", 1) for c in cycles) / max(
        len(cycles), 1
    )

    # 1-2 approvals = healthy, 3-4 = warning, 5+ = centralised
    if avg_approvals <= 2:
        base_score = 0.9
    elif avg_approvals <= 3:
        base_score = 0.7
    elif avg_approvals <= 5:
        base_score = 0.4
    else:
        base_score = 0.2

    # Penalise rising trend
    score = base_score - max(0, centralisation_trend * 0.5)
    score = max(0.0, min(1.0, score))

    warning = None
    if avg_approvals > 3:
        warning = (
            f"APPROVAL_CENTRALISATION: Avg {avg_approvals:.1f} approvals per "
            f"decision suggests bottleneck. Trend: {centralisation_trend:+.1%}"
        )

    return round(score, 4), warning


def _score_payment_stretching(
    cycles: List[Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    """
    Score payment cycle health (1.0 = healthy, 0.0 = severe stretching).

    Expects list of dicts with:
      - period: str
      - avg_payment_days: int (average days to pay suppliers)
      - previous_avg_days: int (optional, for trend)
    """
    period_count = len(cycles)
    current_days = cycles[-1].get("avg_payment_days", 30)

    if period_count >= 2 and cycles[0].get("avg_payment_days"):
        first_days = cycles[0]["avg_payment_days"]
        stretch_trend = (current_days - first_days) / max(first_days, 1)
    else:
        stretch_trend = 0.0

    # Score bands: <30 days = healthy, 30-60 = moderate, 60-90 = stretched, 90+ = severe
    if current_days < 30:
        base_score = 0.95
    elif current_days < 45:
        base_score = 0.8
    elif current_days < 60:
        base_score = 0.6
    elif current_days < 90:
        base_score = 0.3
    else:
        base_score = 0.1

    # Penalise worsening trend
    score = base_score - max(0, stretch_trend * 0.3)
    score = max(0.0, min(1.0, score))

    warning = None
    if current_days > 60:
        warning = (
            f"PAYMENT_STRETCHING: Avg {current_days}d payment cycle suggests "
            f"cashflow pressure. Trend: {stretch_trend:+.1%}"
        )

    return round(score, 4), warning


def _score_decision_backlog(
    logs: List[Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    """
    Score decision backlog (1.0 = healthy flow, 0.0 = complete gridlock).

    Expects list of dicts with:
      - period: str
      - meetings_held: int
      - decisions_reached: int
      - items_deferred: int (optional, backlog count)
    """
    period_count = len(logs)

    # Meeting-to-decision ratio
    ratios = []
    for log in logs:
        meetings = log.get("meetings_held", 0)
        decisions = log.get("decisions_reached", 0)
        if meetings > 0:
            ratios.append(decisions / meetings)
        else:
            ratios.append(0)

    avg_ratio = sum(ratios) / max(len(ratios), 1)

    # <0.5 decisions per meeting = talk shop, 0.5-1.0 = moderate, 1.0+ = efficient
    if avg_ratio >= 1.0:
        base_score = 0.9
    elif avg_ratio >= 0.7:
        base_score = 0.7
    elif avg_ratio >= 0.5:
        base_score = 0.5
    else:
        base_score = 0.3

    # Backlog penalty
    deferred = sum(log.get("items_deferred", 0) for log in logs)
    backlog_penalty = min(0.3, deferred * 0.01)
    score = base_score - backlog_penalty
    score = max(0.0, min(1.0, score))

    warning = None
    if avg_ratio < 0.5:
        warning = (
            f"DECISION_BACKLOG: {avg_ratio:.2f} decisions per meeting — "
            f"more talk than action. {deferred} items deferred."
        )

    return round(score, 4), warning


def _score_contract_velocity(
    signatures: List[Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    """
    Score contract signature velocity (1.0 = healthy, 0.0 = stalled).

    Expects list of dicts with:
      - period: str
      - contracts_signed: int
      - total_value: float (optional, for magnitude context)
      - days_to_sign_avg: int (optional, average days from negotiation to signature)
    """
    period_count = len(signatures)

    counts = [s.get("contracts_signed", 0) for s in signatures]
    trend = (
        (counts[-1] - counts[0]) / max(counts[0], 1)
        if period_count >= 2 and counts[0] > 0
        else 0.0
    )

    avg_count = sum(counts) / max(len(counts), 1)

    # Normalise: 10+ contracts/period = healthy, 5-10 = moderate, 1-5 = slow, 0 = stalled
    if avg_count >= 10:
        base_score = 0.9
    elif avg_count >= 5:
        base_score = 0.7
    elif avg_count >= 2:
        base_score = 0.5
    elif avg_count >= 1:
        base_score = 0.3
    else:
        base_score = 0.1

    # Penalise declining volume
    score = base_score - max(0, -trend * 0.3)
    score = max(0.0, min(1.0, score))

    # Days-to-sign bonus/penalty
    if signatures[-1].get("days_to_sign_avg"):
        dts = signatures[-1]["days_to_sign_avg"]
        if dts > 180:
            score -= 0.2
        elif dts < 30:
            score += 0.1
        score = max(0.0, min(1.0, score))

    warning = None
    if trend < -0.2:
        warning = (
            f"CONTRACT_SLOWDOWN: Signature volume declined {trend:+.1%}. "
            f"Avg {avg_count:.0f} contracts/period. "
            f"Days to sign: {signatures[-1].get('days_to_sign_avg', '?')}"
        )

    return round(score, 4), warning


def _score_budget_release_timing(
    releases: List[Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    """
    Score budget release timing (1.0 = even release, 0.0 = all held to Q4).

    Expects list of dicts with:
      - period: str (year)
      - q1_pct: float (% of annual budget released in Q1)
      - q2_pct: float
      - q3_pct: float
      - q4_pct: float
    """
    if not releases:
        return 0.5, None

    latest = releases[-1]
    q4 = latest.get("q4_pct", 25)
    q1 = latest.get("q1_pct", 25)

    # Healthy: <30% in Q4. Warning: >40% in Q4. Severe: >50% in Q4.
    if q4 <= 30:
        base_score = 0.9
    elif q4 <= 40:
        base_score = 0.6
    elif q4 <= 50:
        base_score = 0.3
    else:
        base_score = 0.1

    # Bonus for even distribution (Q1 close to Q4)
    if q1 > 0 and q4 > 0:
        evenness = 1.0 - min(abs(q4 - q1) / 100, 1.0)
        score = base_score * 0.7 + evenness * 0.3
    else:
        score = base_score

    score = max(0.0, min(1.0, score))

    warning = None
    if q4 > 40:
        warning = (
            f"BUDGET_HOLD: {q4:.0f}% of budget released in Q4 — "
            f"signs of financial uncertainty or approval gridlock."
        )

    return round(score, 4), warning


def _classify_band(score: float) -> str:
    if score >= 0.8:
        return "RHYTHMIC"
    elif score >= 0.5:
        return "ARRHYTHMIC"
    elif score >= 0.2:
        return "STUTTERING"
    else:
        return "APNEIC"


def _infer_trend(components: Dict[str, Any]) -> str:
    """Infer overall trend from available component data."""
    improving = 0
    declining = 0
    stable = 0

    for name, comp in components.items():
        score = comp.get("score")
        if score is None:
            continue
        if score >= 0.75:
            improving += 1
        elif score <= 0.3:
            declining += 1
        else:
            stable += 1

    total = improving + declining + stable
    if total == 0:
        return "insufficient_data"
    if declining > improving and declining >= total * 0.4:
        return "declining"
    if improving > declining and improving >= total * 0.4:
        return "improving"
    return "stable"


def _generate_alternatives(
    components: Dict[str, Any],
    band: str,
    data_count: int,
) -> List[Dict[str, str]]:
    """Generate competing explanations for the cadence reading."""
    alternatives = []

    # Structural alternative
    if band in ("STUTTERING", "APNEIC"):
        alternatives.append(
            {
                "hypothesis": "Institution is under real stress — cadence breakdown reflects genuine pressure",
                "evidence_for": "Multiple dimensions showing declining scores",
                "evidence_against": "Could be seasonal, restructuring transition, or new system implementation",
            }
        )
        alternatives.append(
            {
                "hypothesis": "Cadence change reflects process improvement, not stress",
                "evidence_for": "Fewer approvals may mean better delegation, not paralysis",
                "evidence_against": "Rising approval levels suggest centralisation, not delegation",
            }
        )

    # Data quality alternative
    if data_count < 3:
        alternatives.append(
            {
                "hypothesis": "Insufficient data dimensions — reading may be incomplete",
                "evidence_for": f"Only {data_count}/5 dimensions active",
                "evidence_against": "Available dimensions may still capture dominant signal",
            }
        )

    if not alternatives:
        alternatives.append(
            {
                "hypothesis": "Cadence is normal for this institution's stage and context",
                "evidence_for": "All measured dimensions within healthy range",
                "evidence_against": "Healthy cadence does not guarantee institutional health",
            }
        )

    return alternatives


def _generate_falsification(band: str, data_count: int) -> str:
    """Generate falsification test for current cadence reading."""
    if data_count < 2:
        return "Provide data for at least 2 dimensions across 2+ periods"

    if band in ("STUTTERING", "APNEIC"):
        return (
            "If within 2 periods, approval counts decrease, payment days shorten, "
            "and decisions-per-meeting rise without negative outcomes — "
            "the cadence breakdown was transitional, not structural."
        )
    return (
        "If within 2 periods, approval levels rise above 3, payment days extend "
        "beyond 60, or decisions-per-meeting fall below 0.5 — "
        "the current healthy reading was a lagging indicator."
    )
