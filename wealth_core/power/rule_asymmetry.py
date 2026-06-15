"""
WEALTH Core — Power Intelligence: Rule Asymmetry.

Who can change the rules? Who cannot?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

RULE_CHANGE_SIGNALS = [
    "discretion",
    "sole discretion",
    "right to amend",
    "unilateral",
    "subject to change",
    "without notice",
    "reserved right",
    "regulatory change",
    "policy change",
    "terms may change",
    "at will",
    "forfeiture",
    "clawback",
    "retroactive",
]

PROTECTION_SIGNALS = [
    "bilateral",
    "mutual consent",
    "fixed terms",
    "locked in",
    "guaranteed",
    "irrevocable",
    "vested",
    "protected",
    "grandfathered",
    "contractual right",
    "statutory right",
    "due process",
    "appeal right",
    "arbitration",
]


def detect_rule_asymmetry(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect rule asymmetry in a capital scenario.

    Returns: {dimension, risk_level, evidence}
    """
    scenario_lower = scenario.lower()

    rule_change_count = sum(
        1 for signal in RULE_CHANGE_SIGNALS if signal in scenario_lower
    )
    protection_count = sum(
        1 for signal in PROTECTION_SIGNALS if signal in scenario_lower
    )

    total = rule_change_count + protection_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No rule asymmetry signals detected"
    elif rule_change_count > protection_count * 2:
        risk_level = "HIGH"
        evidence = f"Strong rule asymmetry: {rule_change_count} unilateral vs {protection_count} protected signals"
    elif rule_change_count > protection_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate rule asymmetry: {rule_change_count} unilateral vs {protection_count} protected signals"
    else:
        risk_level = "LOW"
        evidence = f"Protection signals dominate: {protection_count} vs {rule_change_count}"

    return {
        "dimension": "rule_asymmetry",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "rule setter" if rule_change_count > 0 else "unknown",
        "who_carries_downside": "rule taker" if rule_change_count > 0 else "unknown",
        "rule_change_signals": rule_change_count,
        "protection_signals": protection_count,
    }
