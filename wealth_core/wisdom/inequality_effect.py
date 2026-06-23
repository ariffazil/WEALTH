"""
WEALTH Core — Wisdom Economics: Inequality Effect.

Does this widen or narrow inequality?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

from .signal_state import SignalState, derive_signal_state

WIDEN_SIGNALS = [
    "wealth concentration",
    "rent seeking",
    "monopoly profit",
    "wage gap",
    "regressive tax",
    "financial exclusion",
    "information asymmetry",
    "power asymmetry",
    "barrier to entry",
    "extractive",
]

NARROW_SIGNALS = [
    "progressive",
    "inclusive",
    "universal access",
    "wealth distribution",
    "fair wage",
    "financial inclusion",
    "transparency",
    "empowerment",
    "capacity building",
    "shared prosperity",
]


def evaluate_inequality_effect(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate inequality effect of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (widens inequality) to 1.0 (narrows inequality)
    """
    proposal_lower = proposal.lower()

    widen_count = sum(
        1 for signal in WIDEN_SIGNALS if signal in proposal_lower
    )
    narrow_count = sum(
        1 for signal in NARROW_SIGNALS if signal in proposal_lower
    )

    total = widen_count + narrow_count
    if total == 0:
        score = 0.5
        evidence = "No inequality signals detected"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = narrow_count / total
        evidence = (
            f"Found {narrow_count} narrowing signals "
            f"and {widen_count} widening signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    # Derive semantic signal state (Fix 3)
    signal_state, signal_confidence = derive_signal_state(
        score=score,
        pattern_count=widen_count + narrow_count,
        has_positive_patterns=narrow_count > 0,
        has_negative_patterns=widen_count > 0,
    )

    return {
        "dimension": "inequality",
        "score": round(score, 3),
        "signal_state": signal_state.value,
        "signal_confidence": round(signal_confidence, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "widen_signals": widen_count,
        "narrow_signals": narrow_count,
    }
