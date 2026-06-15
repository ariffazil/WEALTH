"""
WEALTH Core — Wisdom Economics: Optionality Preservation.

Does this preserve future choices? Or does it close doors?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

CLOSE_DOOR_SIGNALS = [
    "irreversible",
    "permanent",
    "sunk cost",
    "lock-in",
    "burning bridges",
    "no return",
    "terminal",
    "one-way",
    "exclusive commitment",
    "cannibalize",
]

OPEN_DOOR_SIGNALS = [
    "reversible",
    "flexible",
    "option value",
    "staged",
    "modular",
    "pilot",
    "experiment",
    "pivot capable",
    "real option",
    "optionality preserved",
]


def evaluate_optionality(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate optionality preservation of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (closes all doors) to 1.0 (preserves maximum optionality)
    """
    proposal_lower = proposal.lower()

    close_count = sum(
        1 for signal in CLOSE_DOOR_SIGNALS if signal in proposal_lower
    )
    open_count = sum(
        1 for signal in OPEN_DOOR_SIGNALS if signal in proposal_lower
    )

    total = close_count + open_count
    if total == 0:
        score = 0.5
        evidence = "No optionality signals detected"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = open_count / total
        evidence = (
            f"Found {open_count} option-preserving signals "
            f"and {close_count} door-closing signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    return {
        "dimension": "optionality",
        "score": round(score, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "door_closing_signals": close_count,
        "option_preserving_signals": open_count,
    }
