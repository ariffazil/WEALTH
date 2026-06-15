"""
WEALTH Contracts — Authority grammar and execution boundaries.

F1 AMANAH: Every action reversible or explicitly approved.
WEALTH computes. It never authorizes execution.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from enum import Enum


class ExecutionAuthority(str, Enum):
    """Can this output be acted upon?"""
    OBSERVATION = "OBSERVATION"        # Read-only, no action
    RECOMMENDATION = "RECOMMENDATION"  # Suggests action, requires human approval
    ADVISORY = "ADVISORY"              # Strong suggestion, needs 888_HOLD
    BLOCKED = "BLOCKED"                # Action explicitly forbidden


class ActionClass(str, Enum):
    """What class of action does this relate to?"""
    OBSERVE = "OBSERVE"                # Read-only observation
    COMPUTE = "COMPUTE"                # Pure computation
    MUTATE = "MUTATE"                  # Changes state
    ATOMIC = "ATOMIC"                  # Irreversible state change
    IRREVERSIBLE = "IRREVERSIBLE"      # Cannot be undone


class RiskTier(str, Enum):
    """Risk tier for the output."""
    T0_SAFE = "T0_SAFE"               # No risk
    T1_LOW = "T1_LOW"                 # Minor risk, reversible
    T2_MEDIUM = "T2_MEDIUM"           # Moderate risk, needs review
    T3_HIGH = "T3_HIGH"               # High risk, needs 888_HOLD
    T4_CRITICAL = "T4_CRITICAL"       # Critical risk, needs sovereign approval
    T5_FORBIDDEN = "T5_FORBIDDEN"     # Forbidden action


# Authority rules: what WEALTH can and cannot do
WEALTH_AUTHORITY_RULES = {
    "can_do": [
        "Compute financial metrics (NPV, IRR, EMV, DSCR)",
        "Analyze market data (FX, commodities, macro)",
        "Evaluate risk profiles (entropy, signal, correlation)",
        "Assess wisdom dimensions (dignity, sovereignty, resilience)",
        "Audit power dynamics (capture, rent, opacity)",
        "Screen stocks and portfolios",
        "Generate evidence contracts",
        "Report uncertainty bands",
    ],
    "cannot_do": [
        "Authorize capital execution",
        "Move money or assets",
        "Override human decisions",
        "Bypass arifOS governance",
        "Hide downside risk",
        "Fabricate precision",
        "Self-certify as SEALED",
    ],
    "must_do": [
        "Tag every output with epistemic strength",
        "Report evidence quality honestly",
        "List missing inputs that would strengthen output",
        "Mark execution_authorized=False always",
        "Escalate to arifOS for judgment",
        "Preserve human_final_authority='Arif'",
    ],
}


def validate_authority(output: dict) -> list[str]:
    """Validate that output respects WEALTH authority boundaries."""
    violations = []
    
    if output.get("execution_authorized") is True:
        violations.append(
            "VIOLATION: WEALTH cannot authorize execution. "
            "execution_authorized must be False."
        )
    
    if output.get("human_final_authority") != "Arif":
        violations.append(
            "VIOLATION: human_final_authority must be 'Arif' (F13 SOVEREIGN)."
        )
    
    if not output.get("epistemic_tag"):
        violations.append(
            "VIOLATION: Missing epistemic_tag. F2 TRUTH requires labeling."
        )
    
    return violations
