"""
WEALTH Core — Power Intelligence: Incentive Map.

Who benefits? Who carries downside?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

BENEFIT_SIGNALS = [
    "commission",
    "fee",
    "spread",
    "markup",
    "carried interest",
    "management fee",
    "performance fee",
    "finder fee",
    "referral bonus",
    "upfront payment",
]

DOWNSIDE_SIGNALS = [
    "loss",
    "risk",
    "liability",
    "guarantee",
    "collateral",
    "margin",
    "drawdown",
    "max loss",
    "unlimited risk",
    "personal guarantee",
]


def map_incentives(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Map incentive asymmetry in a capital scenario.

    Returns: {dimension, risk_level, evidence, who_benefits, who_carries_downside}
    """
    scenario_lower = scenario.lower()

    benefit_count = sum(
        1 for signal in BENEFIT_SIGNALS if signal in scenario_lower
    )
    downside_count = sum(
        1 for signal in DOWNSIDE_SIGNALS if signal in scenario_lower
    )

    total = benefit_count + downside_count
    if total == 0:
        risk_level = "LOW"
        evidence = "No incentive signals detected"
    elif benefit_count > downside_count * 2:
        risk_level = "HIGH"
        evidence = f"Strong benefit skew: {benefit_count} benefit vs {downside_count} downside signals"
    elif benefit_count > downside_count:
        risk_level = "MEDIUM"
        evidence = f"Moderate benefit skew: {benefit_count} benefit vs {downside_count} downside signals"
    else:
        risk_level = "LOW"
        evidence = f"Balanced signals: {benefit_count} benefit, {downside_count} downside"

    # Infer who benefits and who carries downside from actors
    who_benefits = actors[0] if actors else "unknown (no actors provided)"
    who_carries_downside = actors[-1] if len(actors) > 1 else "same party"

    return {
        "dimension": "incentive_asymmetry",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": who_benefits,
        "who_carries_downside": who_carries_downside,
        "benefit_signals": benefit_count,
        "downside_signals": downside_count,
    }
