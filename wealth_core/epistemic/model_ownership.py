"""
WEALTH Core — Epistemic Intelligence: Model Ownership Bias.

Who proposed it defends it. Identity risk → model defense.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals that someone is defending their own model/proposal
OWNERSHIP_DEFENSE_SIGNALS = [
    "our model",
    "our proposal",
    "our analysis",
    "our interpretation",
    "our framework",
    "we believe",
    "we proposed",
    "we recommend",
    "our assessment",
    "our view",
    "consistent with our",
    "supports our",
    "validates our",
    "confirms our",
    "aligned with our",
    "as we predicted",
    "as we expected",
    "as we proposed",
    "model was correct",
    "model was right",
    "execution unlucky",
    "reservoir development",
    "thickness variation",
    "charge variation",
    "not a model failure",
    "model remains valid",
]

# Signals of model detachment / independent evaluation
DETACHMENT_SIGNALS = [
    "alternative interpretation",
    "competing model",
    "independent assessment",
    "devil's advocate",
    "stress test",
    "falsification",
    "disconfirming evidence",
    "model fragility",
    "model uncertainty",
    "model limitations",
    "what if wrong",
    "could be wrong",
    "assumption challenged",
    "assumption questioned",
    "revisit the model",
    "rethink the approach",
]

# Role-based bias indicators
ROLE_BIAS_INDICATORS = {
    "operator": "identity_risk",  # Proposer defends model
    "proposer": "identity_risk",  # Same as operator
    "reviewer": "representation_risk",  # Reviewer hedges
    "partner": "representation_risk",  # JV partner hedges
    "governance": "governance_risk",  # Governance constrains dissent
    "approval": "pipeline_risk",  # Approval system creates inertia
}


def detect_model_ownership(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect model ownership bias — who proposed it defends it.

    Returns: {dimension, risk_level, evidence, bias_mode, defense_signals,
              detachment_signals, role_bias}
    """
    scenario_lower = scenario.lower()

    defense_count = sum(
        1 for signal in OWNERSHIP_DEFENSE_SIGNALS if signal in scenario_lower
    )
    detachment_count = sum(
        1 for signal in DETACHMENT_SIGNALS if signal in scenario_lower
    )

    # Detect role-based bias from actors
    role_bias = {}
    for actor in actors:
        actor_lower = actor.lower()
        for role_key, bias_mode in ROLE_BIAS_INDICATORS.items():
            if role_key in actor_lower:
                role_bias[actor] = bias_mode
                break

    total = defense_count + detachment_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No model ownership signals detected"
        bias_mode = "unknown"
    elif defense_count > detachment_count * 2:
        risk_level = "HIGH"
        evidence = (
            f"Strong model defense: {defense_count} defense vs {detachment_count} detachment signals. "
            f"Model owner appears to be protecting proposal."
        )
        bias_mode = "identity_risk"
    elif defense_count > detachment_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate model defense: {defense_count} defense vs {detachment_count} detachment signals."
        bias_mode = "identity_risk"
    else:
        risk_level = "LOW"
        evidence = f"Detachment signals dominate: {detachment_count} vs {defense_count} defense signals"
        bias_mode = "detached"

    # Upgrade risk if role bias matches defense pattern
    if role_bias and defense_count > detachment_count:
        risk_level = "HIGH"
        evidence += f" Role-based bias detected: {role_bias}"

    return {
        "dimension": "model_ownership",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "bias_mode": bias_mode,
        "defense_signals": defense_count,
        "detachment_signals": detachment_count,
        "role_bias": role_bias,
        "who_defends": actors[0]
        if actors and defense_count > detachment_count
        else "unknown",
        "who_detaches": actors[-1]
        if len(actors) > 1 and detachment_count > defense_count
        else "unknown",
    }
