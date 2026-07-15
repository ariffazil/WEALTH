"""
WEALTH Core — Epistemic Intelligence: Governance Constraint Detector.

Challenge enough, but don't break system. JV harmony over truth.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals of governance-bounded dissent
CONSTRAINT_SIGNALS = [
    "alignment",
    "jv alignment",
    "partnership",
    "relationship",
    "harmony",
    "constructive",
    "collaborative",
    "supportive",
    "don't break",
    "don't rock",
    "work together",
    "maintain",
    "preserve relationship",
    "political",
    "diplomatic",
    "tactful",
    "careful",
    "measured",
    "balanced view",
    "both sides",
    "respectfully disagree",
    "see merit in",
    "valid concern",
    "worth considering",
]

# Signals of unbounded truth-seeking
TRUTH_SEEKING_SIGNALS = [
    "reject",
    "refuse",
    "veto",
    "block",
    "stop",
    "kill",
    "abandon",
    "this is wrong",
    "fundamentally flawed",
    "does not work",
    "cannot work",
    "will not work",
    "invalid",
    "incorrect",
    "false",
    "mistaken",
    "erroneous",
    "untenable",
    "unsustainable",
    "must change",
    "needs to change",
    "requires change",
]

# Governance structure indicators
GOVERNANCE_INDICATORS = [
    "jv",
    "joint venture",
    "partnership",
    "operator",
    "non-operator",
    "partner",
    "governance",
    "committee",
    "board",
    "steering",
    "oversight",
    "approval required",
    "consent",
    "unanimous",
]


def detect_governance_constraint(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect governance constraint — challenge without breaking system.

    Returns: {dimension, risk_level, evidence, constraint_count, truth_seeking_count,
              governance_structure, dissent_ceiling}
    """
    scenario_lower = scenario.lower()

    constraint_count = sum(
        1 for signal in CONSTRAINT_SIGNALS if signal in scenario_lower
    )
    truth_seeking_count = sum(
        1 for signal in TRUTH_SEEKING_SIGNALS if signal in scenario_lower
    )
    governance_count = sum(
        1 for signal in GOVERNANCE_INDICATORS if signal in scenario_lower
    )

    # Detect governance structure
    governance_structure = "unknown"
    if governance_count > 0:
        if any(s in scenario_lower for s in ["jv", "joint venture"]):
            governance_structure = "joint_venture"
        elif any(s in scenario_lower for s in ["operator", "non-operator"]):
            governance_structure = "operator_partner"
        elif any(s in scenario_lower for s in ["committee", "board"]):
            governance_structure = "committee"
        else:
            governance_structure = "governed"

    total = constraint_count + truth_seeking_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No governance constraint signals detected"
        dissent_ceiling = "unknown"
    elif constraint_count > truth_seeking_count * 2 and governance_count > 0:
        risk_level = "HIGH"
        evidence = (
            f"Strong governance constraint: {constraint_count} constraint vs {truth_seeking_count} truth-seeking signals. "
            f"Governance structure ({governance_structure}) appears to limit dissent."
        )
        dissent_ceiling = "bounded"
    elif constraint_count > truth_seeking_count and governance_count > 0:
        risk_level = "MEDIUM"
        evidence = f"Moderate governance constraint: {constraint_count} constraint vs {truth_seeking_count} truth-seeking signals."
        dissent_ceiling = "moderate"
    elif truth_seeking_count > constraint_count:
        risk_level = "LOW"
        evidence = f"Truth-seeking signals dominate: {truth_seeking_count} vs {constraint_count} constraint"
        dissent_ceiling = "unbounded"
    else:
        risk_level = "LOW"
        evidence = f"Balanced signals: {constraint_count} constraint, {truth_seeking_count} truth-seeking"
        dissent_ceiling = "balanced"

    return {
        "dimension": "governance_constraint",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "constraint_count": constraint_count,
        "truth_seeking_count": truth_seeking_count,
        "governance_count": governance_count,
        "governance_structure": governance_structure,
        "dissent_ceiling": dissent_ceiling,
    }
