"""
WEALTH Core — Epistemic Intelligence: Zweig Incentive-Truth Alignment.

People do not defend what is true.
People defend what their incentives make survivable.

Jason Zweig's Three Rules:
1. Lie to people who want to be lied to, and you'll get rich.
2. Tell the truth to those who want the truth, and you'll make a living.
3. Tell the truth to those who want to be lied to, and you'll go broke.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Rule 1 signals: framing uncertainty into acceptable story
RULE_1_SIGNALS = [
    "acceptable story",
    "drillable",
    "defensible",
    "socialized",
    "approved",
    "passed",
    "endorsed",
    "supported",
    "viable",
    "promising",
    "positive",
    "upside",
    "potential",
    "opportunity",
    "encouraging",
    "favorable",
    "constructive",
    "optimistic",
    "bullish",
    "prospect",
    "lead",
    "play",
]

# Rule 2 signals: truth told when system is ready
RULE_2_SIGNALS = [
    "post-drill",
    "after wells",
    "learning",
    "updated",
    "revised",
    "corrected",
    "adjusted",
    "integrated",
    "new data",
    "new evidence",
    "reconsidered",
    "reevaluated",
    "post-mortem",
    "lessons learned",
    "retrospective",
]

# Rule 3 signals: truth that collapses incentives (suppressed)
RULE_3_SIGNALS = [
    "not a carbonate play",
    "volcanic primary",
    "model invalid",
    "play type wrong",
    "fundamentally different",
    "collapse ranking",
    "kill the prospect",
    "abandon the play",
    "no viable prospect",
    "dry hole",
    "failure",
    "not economic",
    "sub-commercial",
    "untenable",
    "unsustainable",
]

# Incentive mode indicators
INCENTIVE_MODES = {
    "identity_risk": {
        "description": "Operator/proposer defends model — skin in the game",
        "behavior": "Model defense, signal demotion, analog anchoring",
        "zweig_rule": 1,
    },
    "representation_risk": {
        "description": "Reviewer/partner hedges — governance constraint",
        "behavior": "Challenge without veto, post-fact correction",
        "zweig_rule": 2,
    },
    "governance_risk": {
        "description": "JV alignment pressure — harmony over truth",
        "behavior": "Dissent bounded by relationship preservation",
        "zweig_rule": 2,
    },
    "career_risk": {
        "description": "Decisiveness over correctness — career survival",
        "behavior": "Frame uncertainty as confidence, avoid visible indecision",
        "zweig_rule": 1,
    },
    "no_risk": {
        "description": "Earth has no incentives — wells vote independently",
        "behavior": "Contradiction as signal, truth from inconsistency",
        "zweig_rule": None,
    },
}


def map_zweig_alignment(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Map Zweig incentive-truth alignment.

    Returns: {dimension, risk_level, evidence, rule_1_active, rule_2_active,
              rule_3_suppressed, incentive_modes, truth_filter}
    """
    scenario_lower = scenario.lower()

    rule_1_count = sum(1 for signal in RULE_1_SIGNALS if signal in scenario_lower)
    rule_2_count = sum(1 for signal in RULE_2_SIGNALS if signal in scenario_lower)
    rule_3_count = sum(1 for signal in RULE_3_SIGNALS if signal in scenario_lower)

    # Detect incentive modes from context
    detected_modes = []
    for mode_name, mode_info in INCENTIVE_MODES.items():
        if mode_name in scenario_lower or mode_name.replace("_", " ") in scenario_lower:
            detected_modes.append(
                {
                    "mode": mode_name,
                    "description": mode_info["description"],
                    "behavior": mode_info["behavior"],
                    "zweig_rule": mode_info["zweig_rule"],
                }
            )

    # Also detect from actors
    for actor in actors:
        actor_lower = actor.lower()
        if any(s in actor_lower for s in ["operator", "proposer"]):
            if not any(m["mode"] == "identity_risk" for m in detected_modes):
                detected_modes.append(
                    {
                        "mode": "identity_risk",
                        "description": INCENTIVE_MODES["identity_risk"]["description"],
                        "behavior": INCENTIVE_MODES["identity_risk"]["behavior"],
                        "zweig_rule": 1,
                    }
                )
        elif any(s in actor_lower for s in ["partner", "reviewer", "jv"]):
            if not any(m["mode"] == "representation_risk" for m in detected_modes):
                detected_modes.append(
                    {
                        "mode": "representation_risk",
                        "description": INCENTIVE_MODES["representation_risk"][
                            "description"
                        ],
                        "behavior": INCENTIVE_MODES["representation_risk"]["behavior"],
                        "zweig_rule": 2,
                    }
                )

    # Determine which rules are active
    rule_1_active = rule_1_count > rule_3_count
    rule_2_active = rule_2_count > 0
    rule_3_suppressed = rule_3_count < rule_1_count and rule_3_count > 0

    # Determine truth filter
    truth_filter = "unknown"
    if rule_1_active and rule_3_suppressed:
        truth_filter = "incentive_filtered"  # Truth filtered by incentives
    elif rule_2_active and not rule_1_active:
        truth_filter = "delayed_acceptance"  # Truth accepted when system ready
    elif rule_3_count > rule_1_count:
        truth_filter = "unfiltered"  # Truth spoken despite incentives
    elif rule_1_count == 0 and rule_2_count == 0 and rule_3_count == 0:
        truth_filter = "no_signal"

    # Risk level
    if truth_filter == "incentive_filtered":
        risk_level = "CRITICAL"
        evidence = (
            f"Rule 1 active ({rule_1_count} signals): uncertainty framed as acceptable story. "
            f"Rule 3 suppressed ({rule_3_count} signals): truth that collapses incentives is filtered. "
            f"Detected modes: {[m['mode'] for m in detected_modes]}"
        )
    elif truth_filter == "delayed_acceptance":
        risk_level = "MEDIUM"
        evidence = (
            f"Rule 2 active ({rule_2_count} signals): truth accepted post-drill. "
            f"Rule 3 count: {rule_3_count}. System learns late but learns."
        )
    elif truth_filter == "unfiltered":
        risk_level = "LOW"
        evidence = f"Rule 3 dominant ({rule_3_count} signals): truth spoken despite incentive pressure."
    else:
        risk_level = "LOW"
        evidence = "No Zweig alignment signals detected"

    return {
        "dimension": "zweig_alignment",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "rule_1_active": rule_1_active,
        "rule_1_count": rule_1_count,
        "rule_2_active": rule_2_active,
        "rule_2_count": rule_2_count,
        "rule_3_suppressed": rule_3_suppressed,
        "rule_3_count": rule_3_count,
        "incentive_modes": detected_modes,
        "truth_filter": truth_filter,
    }
