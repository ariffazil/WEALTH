"""
WEALTH Core — Power Intelligence: Opacity Scorer.

How opaque is the valuation? Can the numbers be verified?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

OPAQUE_SIGNALS = [
    "black box",
    "proprietary model",
    "unaudited",
    "estimated",
    "management estimate",
    "board discretion",
    "fair value level 3",
    "unobservable input",
    "mark to model",
    "internal valuation",
    "adjusted ebitda",
    "pro forma",
    "non-gaap",
    "recurring revenue adjusted",
]

TRANSPARENT_SIGNALS = [
    "audited",
    "market price",
    "observable input",
    "fair value level 1",
    "mark to market",
    "third party valuation",
    "independent appraisal",
    "public data",
    "verifiable",
    "gaap compliant",
    "ifrs compliant",
    "disclosed methodology",
]


def score_opacity(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Score opacity of valuation in a capital scenario.

    Returns: {dimension, risk_level, evidence}
    Score: 0.0 (fully opaque) to 1.0 (fully transparent)
    """
    scenario_lower = scenario.lower()

    opaque_count = sum(
        1 for signal in OPAQUE_SIGNALS if signal in scenario_lower
    )
    transparent_count = sum(
        1 for signal in TRANSPARENT_SIGNALS if signal in scenario_lower
    )

    total = opaque_count + transparent_count
    if total == 0:
        risk_level = "LOW"
        opacity_score = 0.5
        evidence = "No opacity signals detected"
    else:
        opacity_score = transparent_count / total
        if opacity_score < 0.3:
            risk_level = "HIGH"
        elif opacity_score < 0.5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        evidence = (
            f"Opacity score: {opacity_score:.2f} "
            f"({transparent_count} transparent, {opaque_count} opaque signals)"
        )

    return {
        "dimension": "opacity",
        "risk_level": risk_level,
        "opacity_score": round(opacity_score, 3),
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "valuation setter" if opaque_count > 0 else "unknown",
        "who_carries_downside": "counterparty" if opaque_count > 0 else "unknown",
        "opaque_signals": opaque_count,
        "transparent_signals": transparent_count,
    }
