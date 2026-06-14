# WEALTH MCP — Five Seals and WAJIB Schema Helpers
# Phase 2: Canonical organs with sovereign envelope
# SPEAR: DITEMPA BUKAN DIBERI

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

# Advisory boundary (PR 5). Lazy-imported to avoid package-init order
# coupling with internal.engines.advisory during five_seals module load.
try:
    from internal.engines.advisory import compute_advisory_boundary
    _ADVISORY_LOADED = True
except ImportError:  # pragma: no cover — defensive only
    compute_advisory_boundary = None  # type: ignore[assignment]
    _ADVISORY_LOADED = False

# ─── EVIDENCE LEVELS ───────────────────────────────────────────────────
EVIDENCE_LEVELS: Dict[str, str] = {
    "E0": "assumption — no verification",
    "E1": "user-stated — claimed but not documented",
    "E2": "document-backed — supported by documents",
    "E3": "ledger-backed — confirmed by financial records",
    "E4": "externally verified — third-party confirmed",
    "E5": "audited — legally/ professionally confirmed",
}

# ─── REVERSIBILITY LEVELS ────────────────────────────────────────────────
REVERSIBILITY_LEVELS: Dict[str, str] = {
    "R1.0": "fully reversible — no residual cost or trace",
    "R0.7": "mostly reversible — minor cost or effort to undo",
    "R0.3": "costly to reverse — significant time, cost, or effort required",
    "R0.0": "irreversible — cannot be undone, permanent effect",
    "unknown": "reversibility cannot be determined",
}

# ─── VERDICTS ────────────────────────────────────────────────────────────
WEALTH_VERDICTS: List[str] = [
    "PROCEED",
    "PROCEED_WITH_GUARDS",
    "DEFER",
    "HOLD",
    "BLOCK",
    "UNKNOWN",
]

# ─── FIVE SEALS HELPERS ──────────────────────────────────────────────────


def _seal_value(metrics: Dict[str, Any], tool: str) -> str:
    """Compute VALUE_SEAL: Does this create, preserve, transfer, or destroy value?"""
    npv = metrics.get("npv", 0)
    irr = metrics.get("irr", 0)
    dscr = metrics.get("dscr", 0)
    networth = metrics.get("networth", 0)
    cashflow = metrics.get("cashflow", 0)

    # Positive value creation signals
    positive_signals = sum(1 for v in [npv, irr, dscr] if v > 0)
    negative_signals = sum(1 for v in [npv, irr] if v < 0)

    if negative_signals >= 2:
        return "DESTROY"
    elif positive_signals >= 2 and negative_signals == 0:
        return "CREATE"
    elif positive_signals >= 1 and negative_signals == 0:
        return "PRESERVE"
    elif cashflow < 0 and abs(cashflow) > abs(networth) * 0.2:
        return "DESTROY"
    return "UNKNOWN"


def _seal_risk(metrics: Dict[str, Any], tool: str) -> str:
    """Compute RISK_SEAL: What is the risk level?"""
    # Extract risk signals from metrics
    dscr = metrics.get("dscr", 999)
    leverage = metrics.get("leverage", 0)
    stress = metrics.get("stress_probability", 0)
    emv = metrics.get("emv", 0)

    if dscr < 1.0 or leverage > 5.0 or stress > 0.5:
        return "CRITICAL"
    elif dscr < 1.25 or leverage > 3.0 or stress > 0.2 or emv < 0:
        return "HIGH"
    elif dscr < 1.5 or leverage > 1.5 or stress > 0.05:
        return "MEDIUM"
    return "LOW"


def _seal_liquidity(metrics: Dict[str, Any], tool: str) -> str:
    """Compute LIQUIDITY_SEAL: Can the system survive the cash timing?"""
    runway = metrics.get("runway_months", 999)
    dscr = metrics.get("dscr", 999)
    cash = metrics.get("cash", 0)
    obligations = metrics.get("obligations", 0)

    if runway < 1 or dscr < 0.8:
        return "INSOLVENT_RISK"
    elif runway < 3 or dscr < 1.0:
        return "STRESSED"
    elif runway < 6 or dscr < 1.25:
        return "TIGHT"
    return "SAFE"


def _seal_legitimacy(metrics: Dict[str, Any], tool: str) -> str:
    """Compute LEGITIMACY_SEAL: Is the wealth clean and institutionally defensible?"""
    # Check for flags that indicate grey/dirty signals
    flags = metrics.get("flags", [])
    evidence_level = metrics.get("evidence_level", "E3")

    dirty_indicators = ["VOID", "INVALID", "FRAUD", "MANIPULATION", "COERCION"]
    if any(f in str(flags) for f in dirty_indicators):
        return "DIRTY"

    grey_indicators = ["UNKNOWN", "STALE", "UNVERIFIED", "UNCERTAINTY"]
    if any(f in str(flags) for f in grey_indicators):
        return "GREY"

    # Low evidence levels suggest grey
    if evidence_level in ("E0", "E1"):
        return "GREY"

    return "CLEAN"


def _seal_sovereignty(metrics: Dict[str, Any], tool: str) -> str:
    """Compute SOVEREIGNTY_SEAL: Does this increase or reduce Arif's freedom of action?"""
    runway = metrics.get("runway_months", 999)
    leverage = metrics.get("leverage", 0)
    dscr = metrics.get("dscr", 999)
    networth = metrics.get("networth", 0)
    obligations = metrics.get("obligations", 0)

    # High obligations relative to networth reduces sovereignty
    if obligations > networth * 0.8 and leverage > 2.0:
        return "CAPTURES"
    elif leverage > 3.0 or dscr < 1.0 or runway < 3:
        return "REDUCES"
    elif leverage < 1.0 and dscr > 1.5 and runway > 12:
        return "INCREASES"
    return "PRESERVES"


def compute_five_seals(
    metrics: Dict[str, Any],
    tool: str,
    capital_at_risk: Optional[Dict[str, Any]] = None,
    evidence_level: str = "E3",
) -> Dict[str, str]:
    """Compute all Five Seals for a WEALTH tool output.

    WAJIB: Every WEALTH output must carry the Five Seals.
    """
    return {
        "value_seal": _seal_value(metrics, tool),
        "risk_seal": _seal_risk(metrics, tool),
        "liquidity_seal": _seal_liquidity(metrics, tool),
        "legitimacy_seal": _seal_legitimacy(metrics, tool),
        "sovereignty_seal": _seal_sovereignty(metrics, tool),
    }


def compute_five_seals_legacy(envelope: Dict[str, Any]) -> Dict[str, str]:
    """Compute Five Seals from an existing envelope (legacy tool output).

    Handles both old-format and new-format envelopes.
    """
    primary = envelope.get("primary_metrics", envelope.get("primary_result", {}))
    tool = envelope.get("task", envelope.get("mcp", "unknown"))
    flags = envelope.get("failure_flags", [])

    metrics = {**primary, "flags": flags}
    evidence_level = (
        envelope.get("epistemic", {}).get("class", "E3")
        if isinstance(envelope.get("epistemic"), dict)
        else "E3"
    )

    return compute_five_seals(metrics, tool, evidence_level=evidence_level)


# ─── WAJIB ENVELOPE BUILDER ───────────────────────────────────────────────


def wajib_envelope(
    tool: str,
    mode: str,
    status: str,
    wealth_verdict: str,
    summary: str,
    metrics: Dict[str, Any],
    *,
    intent: str = "",
    entity_scope: str = "unknown",
    time_horizon: str = "unknown",
    decision_class: str = "W2",
    evidence_level: str = "E3",
    capital_at_risk: Optional[Dict[str, Any]] = None,
    risks: Optional[List[str]] = None,
    assumptions: Optional[List[str]] = None,
    sensitivity: Optional[List[str]] = None,
    liquidity_impact: str = "unknown",
    legitimacy_score: float = 0.5,
    reversibility_score: float = 0.5,
    confidence: float = 0.5,
    next_safe_action: str = "Consult arifOS 888_JUDGE",
    handoff_required: Optional[Dict[str, bool]] = None,
    five_seals: Optional[Dict[str, str]] = None,
    audit_trace: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a WAJIB-compliant output envelope with Five Seals.

    Every canonical WEALTH tool must use this envelope.
    Derived from create_envelope() but with explicit WAJIB fields.

    SPEAR: DITEMPA BUKAN DIBERI — Intelligence is forged, not given.
    """
    # Compute Five Seals if not provided
    if five_seals is None:
        five_seals = compute_five_seals(
            metrics,
            tool,
            capital_at_risk=capital_at_risk,
            evidence_level=evidence_level,
        )

    # Compute Advisory Boundary (PR 5) — every WEALTH output must label
    # its seal authority and surface input integrity. WEALTH advises;
    # arifOS authorizes. The label is the F2-honest disambiguation that
    # prevents a downstream agent from mistaking advisory for execution.
    if _ADVISORY_LOADED and compute_advisory_boundary is not None:
        advisory_boundary = compute_advisory_boundary(
            metrics,
            decision_class=decision_class,
            evidence_level=evidence_level,
        )
    else:  # pragma: no cover — defensive only, advisory.py must be present
        advisory_boundary = {
            "domain_seal_validity": "WEALTH|advisory_only",
            "judge_seal_authorization_required": decision_class in ("W4", "W5"),
            "synthetic_inputs_detected": False,
            "insufficient_input_detected": False,
            "seal_authority_disclaimer": (
                "WEALTH verdict is domain-valid advisory only. "
                "Execution requires arifOS JUDGE_SEAL_AUTHORIZATION."
            ),
        }

    # Default handoff matrix
    if handoff_required is None:
        handoff_required = {
            "WELL": False,
            "arifOS": decision_class in ("W4", "W5"),
            "GEOX": False,
            "human_professional": decision_class in ("W4", "W5"),
        }

    # Default audit trace
    if audit_trace is None:
        audit_trace = {
            "trace_id": f"wealth-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool": tool,
            "mode": mode,
            "canonical": True,
            "spear": "DITEMPA_BUKAN_DIBERI",
        }

    return {
        # ── Core identity ────────────────────────────────────────────────
        "mcp": "WEALTH",
        "task": f"{tool}:{mode}",
        "tool": tool,
        "mode": mode,
        # ── WAJIB mandatory fields ──────────────────────────────────────
        "status": status,
        "wealth_verdict": wealth_verdict,
        "summary": summary,
        "metrics": metrics,
        # ── Five Seals ─────────────────────────────────────────────────
        "value_seal": five_seals.get("value_seal", "UNKNOWN"),
        "risk_seal": five_seals.get("risk_seal", "UNKNOWN"),
        "liquidity_seal": five_seals.get("liquidity_seal", "UNKNOWN"),
        "legitimacy_seal": five_seals.get("legitimacy_seal", "UNKNOWN"),
        "sovereignty_seal": five_seals.get("sovereignty_seal", "UNKNOWN"),
        # ── Decision governance ──────────────────────────────────────────
        "decision_class": decision_class,
        "evidence_level": evidence_level,
        "entity_scope": entity_scope,
        "time_horizon": time_horizon,
        "capital_at_risk": capital_at_risk or {},
        "reversibility": reversibility_score,
        "counterparties": [],
        # ── Risk and assumptions ────────────────────────────────────────
        "risks": risks or [],
        "assumptions_used": assumptions or [],
        "sensitivity": sensitivity or [],
        "liquidity_impact": liquidity_impact,
        # ── Scores ────────────────────────────────────────────────────
        "legitimacy_score": legitimacy_score,
        "reversibility_score": reversibility_score,
        "confidence": confidence,
        # ── Action guidance ───────────────────────────────────────────
        "next_safe_action": next_safe_action,
        "handoff_required": handoff_required,
        "handoff_recommendation": _build_handoff_recommendation(
            decision_class, wealth_verdict
        ),
        # ── Advisory Boundary (PR 5) ────────────────────────────────
        # Every WEALTH output carries the seal-authority label and the
        # input-integrity flags. WEALTH|advisory_only ≠ arifOS|execution_authorized.
        "domain_seal_validity": advisory_boundary["domain_seal_validity"],
        "judge_seal_authorization_required": advisory_boundary[
            "judge_seal_authorization_required"
        ],
        "synthetic_inputs_detected": advisory_boundary["synthetic_inputs_detected"],
        "insufficient_input_detected": advisory_boundary["insufficient_input_detected"],
        "seal_authority_disclaimer": advisory_boundary["seal_authority_disclaimer"],
        # ── Audit ──────────────────────────────────────────────────────
        "audit_trace": audit_trace,
        # ── Legacy compatibility ──────────────────────────────────────
        "final_authority": "Arif",
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "epoch": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        # ── Intent tracking ────────────────────────────────────────────
        "intent": intent,
    }


def _build_handoff_recommendation(decision_class: str, verdict: str) -> List[str]:
    """Build handoff recommendations based on decision class and verdict."""
    recs = []

    if decision_class in ("W4", "W5"):
        recs.append(
            "Route to arifOS 888_JUDGE for constitutional verdict before action"
        )

    if verdict in ("HOLD", "BLOCK"):
        recs.append("Do not proceed — await human confirmation or input repair")

    if verdict == "PROCEED_WITH_GUARDS":
        recs.append("Proceed only after verifying all guard conditions are met")

    if decision_class in ("W3", "W4", "W5"):
        recs.append("Consider recording decision to WEALTH ledger for audit trail")

    return recs


# ─── HANDOVER POLICY ──────────────────────────────────────────────────────

HANDOVER_POLICY = {
    "WELL": "When biological readiness is low and decision is W4/W5.",
    "arifOS": "When constitutional/governance risk is high, ledger mutation is required, or action is W4/W5.",
    "GEOX": "When location, geospatial asset, or subsurface value is material to the decision.",
    "human_professional": "When legal, tax, audit, or licensed professional advice is required.",
}


def classify_decision_class(
    capital_amount: float = 0,
    legal_exposure: bool = False,
    tax_exposure: bool = False,
    irreversible: bool = False,
    entity_scope: str = "unknown",
) -> str:
    """Classify a decision into W0-W5 risk ladder.

    WAJIB: Every tool must classify its own decision class.
    """
    if legal_exposure or tax_exposure:
        return "W4"
    if irreversible:
        return "W5"
    if capital_amount <= 0:
        return "W0"
    if capital_amount < 1000:
        return "W1"
    if capital_amount < 50000:
        return "W2"
    return "W3"


print("[engines/five_seals] Five Seals helpers loaded — SPEAR: DITEMPA BUKAN DIBERI")
