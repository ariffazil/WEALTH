"""
WEALTH Core — Power Intelligence: Rent Extraction.

Is hidden rent being extracted?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

RENT_SIGNALS = [
    "hidden fee",
    "opaque pricing",
    "spread markup",
    "payment for order flow",
    "kickback",
    "rebate",
    "soft dollar",
    "wrap fee",
    "trailing commission",
    "12b-1 fee",
    "load",
    "surrender charge",
    "early redemption fee",
    "switching fee",
    "platform fee",
]

TRANSPARENT_SIGNALS = [
    "all-in cost",
    "transparent pricing",
    "no hidden fee",
    "fee-only",
    "flat fee",
    "cost disclosure",
    "total expense ratio",
    "net of fees",
    "gross-to-net",
    "fee cap",
]


def detect_rent_extraction(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect hidden rent extraction in a capital scenario.

    Returns: {dimension, risk_level, evidence}
    """
    scenario_lower = scenario.lower()

    rent_count = sum(
        1 for signal in RENT_SIGNALS if signal in scenario_lower
    )
    transparent_count = sum(
        1 for signal in TRANSPARENT_SIGNALS if signal in scenario_lower
    )

    total = rent_count + transparent_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No rent extraction signals detected"
    elif rent_count > transparent_count * 2:
        risk_level = "HIGH"
        evidence = f"Strong rent signals: {rent_count} rent vs {transparent_count} transparency"
    elif rent_count > transparent_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate rent signals: {rent_count} rent vs {transparent_count} transparency"
    else:
        risk_level = "LOW"
        evidence = f"Transparency signals dominate: {transparent_count} vs {rent_count}"

    return {
        "dimension": "rent_extraction",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "intermediary" if rent_count > 0 else "unknown",
        "who_carries_downside": "end investor" if rent_count > 0 else "unknown",
        "rent_signals": rent_count,
        "transparent_signals": transparent_count,
    }
