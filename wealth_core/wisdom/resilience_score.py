"""
WEALTH Core — Wisdom Economics: Resilience Score.

Does this survive shocks? How fragile is this allocation?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

from .signal_state import SignalState, derive_signal_state

FRAGILITY_SIGNALS = [
    "concentrated",
    "undiversified",
    "single point of failure",
    "leverage",
    "margin call",
    "short term",
    "maturity mismatch",
    "illiquid",
    "volatile",
    "correlated",
]

RESILIENCE_SIGNALS = [
    "diversified",
    "liquid reserve",
    "long term",
    "hedged",
    "buffer",
    "contingency",
    "stress tested",
    "multiple revenue streams",
    "low correlation",
    "adaptive capacity",
]


def evaluate_resilience(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate resilience of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (fragile) to 1.0 (resilient)
    """
    proposal_lower = proposal.lower()

    fragility_count = sum(
        1 for signal in FRAGILITY_SIGNALS if signal in proposal_lower
    )
    resilience_count = sum(
        1 for signal in RESILIENCE_SIGNALS if signal in proposal_lower
    )

    total = fragility_count + resilience_count
    if total == 0:
        score = 0.5
        evidence = "No resilience signals detected"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = resilience_count / total
        evidence = (
            f"Found {resilience_count} resilience signals "
            f"and {fragility_count} fragility signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    # Derive semantic signal state (Fix 3)
    signal_state, signal_confidence = derive_signal_state(
        score=score,
        pattern_count=fragility_count + resilience_count,
        has_positive_patterns=resilience_count > 0,
        has_negative_patterns=fragility_count > 0,
    )

    return {
        "dimension": "resilience",
        "score": round(score, 3),
        "signal_state": signal_state.value,
        "signal_confidence": round(signal_confidence, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "fragility_signals": fragility_count,
        "resilience_signals": resilience_count,
    }
