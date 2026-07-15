"""
WEALTH Core — Epistemic Intelligence: Pipeline Inertia Detector.

Approval system makes pivot hard. Proposal → AFE → approval → hard to change.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals of pipeline/approval inertia
INERTIA_SIGNALS = [
    "afe",
    "approval",
    "approved",
    "budget",
    "committed",
    "sunk cost",
    "already decided",
    "already approved",
    "in the pipeline",
    "in progress",
    "underway",
    "mobilized",
    "contracted",
    "rig committed",
    "drilling contract",
    "capital committed",
    "expenditure approved",
    "board approved",
    "management approved",
    "sanctioned",
    "final investment decision",
    "fid",
    "moved to execution",
    "execution phase",
    "implementation phase",
]

# Signals of pivot flexibility
FLEXIBILITY_SIGNALS = [
    "revisit",
    "reconsider",
    "pivot",
    "change course",
    "update model",
    "revise",
    "amend",
    "adjust",
    "flexibility",
    "contingency",
    "alternative",
    "option",
    "stage gate",
    "decision gate",
    "checkpoint",
    "review point",
    "off-ramp",
    "kill criteria",
    "walk away",
    "abandon",
]


def detect_pipeline_inertia(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect pipeline inertia — approval system makes pivot hard.

    Returns: {dimension, risk_level, evidence, inertia_count, flexibility_count,
              commitment_level}
    """
    scenario_lower = scenario.lower()

    inertia_count = sum(1 for signal in INERTIA_SIGNALS if signal in scenario_lower)
    flexibility_count = sum(
        1 for signal in FLEXIBILITY_SIGNALS if signal in scenario_lower
    )

    total = inertia_count + flexibility_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No pipeline inertia signals detected"
        commitment_level = "unknown"
    elif inertia_count > flexibility_count * 3:
        risk_level = "CRITICAL"
        evidence = (
            f"Extreme pipeline inertia: {inertia_count} inertia vs {flexibility_count} flexibility signals. "
            f"System appears locked into course of action."
        )
        commitment_level = "locked"
    elif inertia_count > flexibility_count * 2:
        risk_level = "HIGH"
        evidence = (
            f"Strong pipeline inertia: {inertia_count} inertia vs {flexibility_count} flexibility signals. "
            f"Pivot would require significant organizational energy."
        )
        commitment_level = "heavy"
    elif inertia_count > flexibility_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate pipeline inertia: {inertia_count} inertia vs {flexibility_count} flexibility signals."
        commitment_level = "moderate"
    else:
        risk_level = "LOW"
        evidence = f"Flexibility signals dominate: {flexibility_count} vs {inertia_count} inertia"
        commitment_level = "flexible"

    return {
        "dimension": "pipeline_inertia",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "inertia_count": inertia_count,
        "flexibility_count": flexibility_count,
        "commitment_level": commitment_level,
    }
