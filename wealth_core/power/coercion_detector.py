"""
WEALTH Core — Power Intelligence: Coercion Detector.

Is time-pressure being used to force action?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

COERCION_SIGNALS = [
    "limited time",
    "act now",
    "expires soon",
    "last chance",
    "urgency",
    "deadline",
    "hurry",
    "dont miss",
    "fomo",
    "fear of missing out",
    "opportunity of a lifetime",
    "once in a lifetime",
    "closing today",
    "final offer",
    "take it or leave it",
    "pressure",
    "countdown",
    "only.*left",
    "running out",
    "flash sale",
]

NO_PRESSURE_SIGNALS = [
    "no rush",
    "take your time",
    "consider carefully",
    "sleep on it",
    "compare options",
    "due diligence",
    "cooling off",
    "right of withdrawal",
    "no obligation",
    "open ended",
]


def detect_coercion(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect coercion signals in a capital scenario.

    Returns: {dimension, risk_level, evidence}
    """
    import re

    scenario_lower = scenario.lower()

    coercion_count = 0
    for signal in COERCION_SIGNALS:
        if signal.startswith("only") and ".*" in signal:
            if re.search(signal, scenario_lower):
                coercion_count += 1
        elif signal in scenario_lower:
            coercion_count += 1

    no_pressure_count = sum(
        1 for signal in NO_PRESSURE_SIGNALS if signal in scenario_lower
    )

    total = coercion_count + no_pressure_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No coercion signals detected"
    elif coercion_count > no_pressure_count * 2:
        risk_level = "CRITICAL"
        evidence = f"Strong coercion: {coercion_count} pressure vs {no_pressure_count} no-pressure signals"
    elif coercion_count > no_pressure_count:
        risk_level = "HIGH"
        evidence = f"Moderate coercion: {coercion_count} pressure vs {no_pressure_count} no-pressure signals"
    else:
        risk_level = "LOW"
        evidence = f"No pressure signals dominate: {no_pressure_count} vs {coercion_count}"

    return {
        "dimension": "coercion",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "pressure applicator" if coercion_count > 0 else "unknown",
        "who_carries_downside": "pressured party" if coercion_count > 0 else "unknown",
        "coercion_signals": coercion_count,
        "no_pressure_signals": no_pressure_count,
    }
