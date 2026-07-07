"""
WEALTH Core — Governance Capacity Engine.

Pure computation: no I/O, no MCP, no side effects.

Monitors board governance capacity relative to institutional stress level.

Key insight: governance capacity must exceed stress level.
When capacity < stress, the institution cannot make quality decisions.
This is when external actors can exploit institutional weakness.

The governance-stress gap is the single most predictive indicator
of institutional collapse: it measures the ability to self-correct.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

_CONFIDENCE_CAP = 0.90


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _score_board_composition(
    board_members: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze board composition and return component scores."""
    if not board_members:
        return {
            "size_score": 0.0,
            "independence_score": 0.0,
            "tenure_score": 0.0,
            "diversity_score": 0.0,
            "total_members": 0,
            "independent_neds": 0,
            "executives": 0,
            "secretaries_as_directors": 0,
        }

    total = len(board_members)
    executives = sum(1 for m in board_members if m.get("type") == "executive")
    independent_neds = sum(
        1 for m in board_members if m.get("type") == "independent_ned"
    )
    non_independent_neds = sum(
        1 for m in board_members if m.get("type") == "non_independent_ned"
    )
    secretaries = sum(1 for m in board_members if m.get("type") == "secretary")

    # Size score: optimal 7-11 members
    if 7 <= total <= 11:
        size_score = 1.0
    elif 5 <= total < 7:
        size_score = 0.7
    elif 11 < total <= 15:
        size_score = 0.7
    elif total < 5:
        size_score = 0.3
    else:
        size_score = 0.4

    # Independence score: at least 1/3 should be independent NEDs
    if total > 0:
        independence_ratio = independent_neds / total
        independence_score = _clamp(independence_ratio / 0.33)
    else:
        independence_score = 0.0

    # Penalty if secretaries serve as directors
    secretary_penalty = 0.15 * secretaries if secretaries > 0 else 0.0
    independence_score = _clamp(independence_score - secretary_penalty)

    # Tenure score: diversity of tenure is healthy
    # But very short avg tenure is destabilizing, very long is capture risk
    now = datetime.now(timezone.utc)
    tenures = []
    for m in board_members:
        try:
            appointed = datetime.fromisoformat(
                m.get("appointed_date", "2020-01-01")
            )
            if appointed.tzinfo is None:
                appointed = appointed.replace(tzinfo=timezone.utc)
            years = (now - appointed).days / 365.25
            tenures.append(years)
        except (ValueError, TypeError):
            tenures.append(3.0)  # default assumption

    if tenures:
        avg_tenure = sum(tenures) / len(tenures)
        # Optimal: 3-7 years
        if 3 <= avg_tenure <= 7:
            tenure_score = 1.0
        elif avg_tenure < 3:
            tenure_score = _clamp(avg_tenure / 3.0)
        else:
            # Long tenure: mild penalty for capture risk
            tenure_score = _clamp(1.0 - (avg_tenure - 7) * 0.05)
    else:
        tenure_score = 0.5

    # Diversity: mix of types is healthy
    type_count = sum(
        1
        for t in [executives, independent_neds, non_independent_neds, secretaries]
        if t > 0
    )
    diversity_score = _clamp(type_count / 3.0)

    return {
        "size_score": round(size_score, 4),
        "independence_score": round(independence_score, 4),
        "tenure_score": round(tenure_score, 4),
        "diversity_score": round(diversity_score, 4),
        "total_members": total,
        "independent_neds": independent_neds,
        "executives": executives,
        "secretaries_as_directors": secretaries,
    }


def _score_committees(
    committees: List[Dict[str, Any]],
    board_members: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze committee structure and meeting frequency."""
    if not committees:
        return {
            "committee_score": 0.0,
            "key_committees_present": False,
            "meeting_frequency_score": 0.0,
            "total_committees": 0,
        }

    # Essential committees: audit, risk/remuneration, nomination
    essential = {"audit", "risk", "remuneration", "nomination"}
    present_names = set()
    for c in committees:
        name_lower = c.get("name", "").lower()
        for e in essential:
            if e in name_lower:
                present_names.add(e)

    key_present = len(present_names) >= 2  # At least 2 essential committees

    # Meeting frequency
    meeting_scores = []
    for c in committees:
        if c.get("meets_quarterly", False):
            meeting_scores.append(1.0)
        else:
            meeting_scores.append(0.5)

    avg_meeting = sum(meeting_scores) / len(meeting_scores) if meeting_scores else 0.0

    # Committee coverage: each committee should have members
    covered = sum(1 for c in committees if len(c.get("members", [])) > 0)
    coverage = covered / len(committees) if committees else 0.0

    committee_score = (
        (len(present_names) / len(essential)) * 0.4
        + avg_meeting * 0.3
        + coverage * 0.3
    )

    return {
        "committee_score": round(_clamp(committee_score), 4),
        "key_committees_present": key_present,
        "meeting_frequency_score": round(avg_meeting, 4),
        "total_committees": len(committees),
        "essential_committees_found": list(present_names),
    }


def _identify_gaps(
    composition: Dict[str, Any],
    committees: Dict[str, Any],
    stress_level: float,
) -> List[str]:
    """Identify governance gaps relative to stress level."""
    gaps = []

    if composition["total_members"] < 5:
        gaps.append("BOARD_SIZE: Below minimum effective board size (5)")

    if composition["independence_score"] < 0.5:
        gaps.append(
            "INDEPENDENCE: Insufficient independent NEDs for stress level. "
            "Need at least 1/3 independent."
        )

    if composition["secretaries_as_directors"] > 0:
        gaps.append(
            "DUAL_ROLE: Company secretaries serving as directors weakens "
            "governance oversight."
        )

    if not committees["key_committees_present"]:
        gaps.append(
            "COMMITTEES: Missing essential committees (audit/risk/remuneration/nomination)."
        )

    if committees["meeting_frequency_score"] < 0.7:
        gaps.append(
            "FREQUENCY: Committees not meeting quarterly. "
            "Stress periods require more frequent oversight."
        )

    if stress_level > 0.6 and composition["independent_neds"] < 3:
        gaps.append(
            "STRESS_CAPACITY: High stress requires more independent oversight. "
            "Recommend at least 3 independent NEDs."
        )

    if composition["tenure_score"] < 0.5:
        gaps.append(
            "TENURE: Board tenure outside optimal range (3-7 years). "
            "Risk of either instability or capture."
        )

    return gaps


def _generate_recommendations(
    capacity_score: float,
    stress_level: float,
    gaps: List[str],
    quorum_status: str,
) -> List[str]:
    """Generate governance recommendations."""
    recs = []

    stress_gap = stress_level - capacity_score

    if stress_gap > 0.3:
        recs.append(
            "CRITICAL GAP: Stress exceeds governance capacity by "
            f"{stress_gap:.2f}. Institution cannot self-correct. "
            "External governance intervention may be needed."
        )
    elif stress_gap > 0.1:
        recs.append(
            "CAPACITY GAP: Stress exceeds governance capacity by "
            f"{stress_gap:.2f}. Accelerate governance reforms."
        )

    if quorum_status == "INSUFFICIENT":
        recs.append(
            "QUORUM: Board cannot form effective quorum. "
            "Emergency appointment of independent NEDs required."
        )

    for gap in gaps[:3]:  # Top 3 gaps
        if "INDEPENDENCE" in gap:
            recs.append("Appoint additional independent NEDs immediately.")
        if "COMMITTEES" in gap:
            recs.append("Establish or reactivate essential governance committees.")
        if "DUAL_ROLE" in gap:
            recs.append("Separate company secretary and director roles.")

    return recs


def compute_governance_capacity(
    board_members: List[Dict[str, Any]],
    committees: List[Dict[str, Any]],
    stress_level: float,
) -> Dict[str, Any]:
    """
    Compute governance capacity score relative to stress level.

    Returns:
      - capacity_score: 0-1 governance capacity
      - quorum_status: ADEQUATE/TIGHT/INSUFFICIENT
      - key_gaps: list of identified governance gaps
      - stress_capacity_gap: stress_level - capacity_score (positive = dangerous)
      - recommendations: list of actionable strings
      - confidence: capped at 0.90
    """
    composition = _score_board_composition(board_members)
    committee_analysis = _score_committees(committees, board_members)

    # Composite capacity score
    capacity_score = (
        composition["size_score"] * 0.15
        + composition["independence_score"] * 0.30
        + composition["tenure_score"] * 0.15
        + composition["diversity_score"] * 0.10
        + committee_analysis["committee_score"] * 0.30
    )
    capacity_score = _clamp(capacity_score)

    # Quorum status
    total = composition["total_members"]
    independent = composition["independent_neds"]
    if total >= 5 and independent >= 2:
        quorum_status = "ADEQUATE"
    elif total >= 3 and independent >= 1:
        quorum_status = "TIGHT"
    else:
        quorum_status = "INSUFFICIENT"

    gaps = _identify_gaps(composition, committee_analysis, stress_level)
    stress_capacity_gap = round(stress_level - capacity_score, 4)
    recommendations = _generate_recommendations(
        capacity_score, stress_level, gaps, quorum_status
    )

    # Confidence
    data_richness = min(1.0, len(board_members) / 5.0)
    committee_richness = min(1.0, len(committees) / 3.0)
    confidence = min(_CONFIDENCE_CAP, (data_richness + committee_richness) / 2.0)

    return {
        "capacity_score": round(capacity_score, 4),
        "quorum_status": quorum_status,
        "key_gaps": gaps,
        "stress_capacity_gap": stress_capacity_gap,
        "recommendations": recommendations,
        "board_composition": composition,
        "committee_analysis": committee_analysis,
        "confidence": round(confidence, 4),
        "confidence_note": "Capped at 0.90 per F7 HUMILITY",
    }
