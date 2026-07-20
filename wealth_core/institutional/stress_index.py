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


def _normalize_departures(raw: Any) -> tuple[int, list[str]]:
    """Type-safe key_personnel_departures → (count, names).

    Accepts: int, list[str], comma-separated str. Never raises.
    P0 fix 2026-07-12 (#35 crash / #34 silent drop).
    """
    if raw is None:
        return 0, []
    if isinstance(raw, int):
        return max(0, raw), []
    if isinstance(raw, float):
        return max(0, int(raw)), []
    if isinstance(raw, str):
        names = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
        return len(names), names
    if isinstance(raw, (list, tuple, set)):
        names = [str(x) for x in raw]
        return len(names), names
    # Unknown type — treat as absent, caller records warning
    return 0, []


def _workforce_stress(sig: Dict[str, Any]) -> float:
    """Score workforce destabilization 0-1."""
    score = 0.0

    # Rightsizing percentage: 15%+ → 1.0
    rightsizing = sig.get("rightsizing_pct", 0.0)
    try:
        rightsizing = float(rightsizing or 0.0)
    except (TypeError, ValueError):
        rightsizing = 0.0
    score += _clamp(rightsizing / 15.0) * 0.35

    # Voluntary exits: 10%+ → 1.0
    exits = sig.get("voluntary_exits_pct", 0.0)
    try:
        exits = float(exits or 0.0)
    except (TypeError, ValueError):
        exits = 0.0
    score += _clamp(exits / 10.0) * 0.30

    # Key personnel departures — each one adds stress
    dep_count, _names = _normalize_departures(sig.get("key_personnel_departures"))
    if dep_count:
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


_EXPECTED_FIELDS: Dict[str, tuple[str, ...]] = {
    "financial": (
        "profit_change_pct",
        "revenue_change_pct",
        "cost_cutting_announced",
    ),
    "governance": (
        "board_size",
        "board_resignations_12m",
        "company_secretaries_as_directors",
        "avg_tenure_years",
    ),
    "workforce": (
        "rightsizing_pct",
        "voluntary_exits_pct",
        "key_personnel_departures",
    ),
    "legal": (
        "active_litigation_count",
        "injunction_value_musd",
        "regulatory_uncertainty_score",
    ),
    "exploitation": (
        "counterparty_payment_freeze",
        "interpleader_filed",
        "competing_claims",
    ),
}


def _audit_signal_fields(
    name: str, sig: Dict[str, Any] | None
) -> tuple[list[str], list[str], list[str]]:
    """Return (present, missing, type_warnings) for expected fields.

    P0 #34: silent field-drop must be visible — empty/missing keys are reported.
    """
    sig = sig or {}
    if not isinstance(sig, dict):
        return (
            [],
            list(_EXPECTED_FIELDS.get(name, ())),
            [f"{name}: expected dict, got {type(sig).__name__}"],
        )
    expected = _EXPECTED_FIELDS.get(name, ())
    present = [k for k in expected if k in sig and sig[k] is not None and sig[k] != ""]
    missing = [k for k in expected if k not in present]
    type_warnings: list[str] = []
    if "key_personnel_departures" in sig:
        raw = sig.get("key_personnel_departures")
        if raw is not None and not isinstance(raw, (int, float, list, tuple, set, str)):
            type_warnings.append(
                f"workforce.key_personnel_departures: unsupported type {type(raw).__name__}"
            )
    return present, missing, type_warnings


def compute_stress_index(
    org_name: str,
    financial_signals: Dict[str, Any] | None = None,
    governance_signals: Dict[str, Any] | None = None,
    workforce_signals: Dict[str, Any] | None = None,
    legal_signals: Dict[str, Any] | None = None,
    exploitation_signals: Dict[str, Any] | None = None,
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
      - fields_present / fields_missing / warnings: anti-silent-drop (P0 #34/#35)
    """
    financial_signals = financial_signals if isinstance(financial_signals, dict) else {}
    governance_signals = (
        governance_signals if isinstance(governance_signals, dict) else {}
    )
    workforce_signals = workforce_signals if isinstance(workforce_signals, dict) else {}
    legal_signals = legal_signals if isinstance(legal_signals, dict) else {}
    exploitation_signals = (
        exploitation_signals if isinstance(exploitation_signals, dict) else {}
    )

    audits = {
        "financial": _audit_signal_fields("financial", financial_signals),
        "governance": _audit_signal_fields("governance", governance_signals),
        "workforce": _audit_signal_fields("workforce", workforce_signals),
        "legal": _audit_signal_fields("legal", legal_signals),
        "exploitation": _audit_signal_fields("exploitation", exploitation_signals),
    }
    fields_present: list[str] = []
    fields_missing: list[str] = []
    warnings: list[str] = []
    for dim, (pres, miss, tw) in audits.items():
        fields_present.extend(f"{dim}.{k}" for k in pres)
        fields_missing.extend(f"{dim}.{k}" for k in miss)
        warnings.extend(tw)

    if fields_missing:
        warnings.append(
            f"SILENT_DEFAULT_RISK: {len(fields_missing)} expected fields absent — "
            "treated as zero/false; do not treat GREEN as 'no stress observed'"
        )

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

    # F7 HUMILITY: confidence from field coverage, not merely non-empty dicts
    expected_total = sum(len(v) for v in _EXPECTED_FIELDS.values())
    coverage = len(fields_present) / max(1, expected_total)
    confidence = min(_CONFIDENCE_CAP, coverage)

    # P0 #36 (2026-07-20): SILENT_DEFAULT_RISK hardening.
    # When coverage < 0.15 (fewer than 15% of expected fields present),
    # override risk_level to INSUFFICIENT_DATA regardless of computed score.
    # A 0.0 stress_index with zero data is NOT "GREEN" — it's "we have no data."
    if coverage < 0.15:
        original_level = risk_level
        risk_level = "INSUFFICIENT_DATA"
        warnings.append(
            f"RISK_LEVEL_OVERRIDE: coverage={coverage:.0%} < 15% threshold. "
            f"risk_level downgraded from '{original_level}' to "
            f"'INSUFFICIENT_DATA'. Provide at least 3 of {expected_total} expected "
            f"fields across any dimension for a meaningful stress assessment."
        )

    return {
        "org_name": org_name,
        "stress_index": round(stress_index, 4),
        "component_scores": component_scores,
        "risk_level": risk_level,
        "feedback_loop_detected": feedback_loop,
        "recommendations": recommendations,
        "confidence": round(confidence, 4),
        "confidence_note": "Capped at 0.90 per F7 HUMILITY; scales with field coverage",
        "fields_present": fields_present,
        "fields_missing": fields_missing,
        "warnings": warnings,
    }
