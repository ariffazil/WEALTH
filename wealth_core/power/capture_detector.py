"""
WEALTH Core — Power Intelligence: Capture Detector.

Is this advice captured by interest?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

CAPTURE_SIGNALS = [
    "sponsored",
    "partner content",
    "affiliate",
    "paid promotion",
    "conflict of interest",
    "related party",
    "insider",
    "connected",
    "lobbying",
    "regulatory capture",
    "revolving door",
    "self-dealing",
    "tied selling",
    "bundled",
    "captive",
]

INDEPENDENCE_SIGNALS = [
    "independent",
    "fiduciary",
    "arm length",
    "disclosed conflict",
    "third party audit",
    "transparency",
    "open process",
    "competitive bid",
    "disinterested",
    "objective",
]


def detect_capture(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect capture risk in a capital scenario.

    Returns: {dimension, risk_level, evidence, who_benefits, who_carries_downside}
    """
    scenario_lower = scenario.lower()

    capture_count = sum(
        1 for signal in CAPTURE_SIGNALS if signal in scenario_lower
    )
    independence_count = sum(
        1 for signal in INDEPENDENCE_SIGNALS if signal in scenario_lower
    )

    total = capture_count + independence_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No capture signals detected"
    elif capture_count > independence_count * 2:
        risk_level = "CRITICAL"
        evidence = f"Strong capture signals: {capture_count} capture vs {independence_count} independence"
    elif capture_count > independence_count:
        risk_level = "HIGH"
        evidence = f"Moderate capture signals: {capture_count} capture vs {independence_count} independence"
    else:
        risk_level = "LOW"
        evidence = f"Independence signals dominate: {independence_count} vs {capture_count}"

    return {
        "dimension": "capture_risk",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "captured advisor" if capture_count > 0 else "unknown",
        "who_carries_downside": "client/investor" if capture_count > 0 else "unknown",
        "capture_signals": capture_count,
        "independence_signals": independence_count,
    }
