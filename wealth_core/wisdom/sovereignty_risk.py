"""
WEALTH Core — Wisdom Economics: Sovereignty Risk.

Does this create dependency, capture, or reduce autonomy?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

from .signal_state import SignalState, derive_signal_state

DEPENDENCY_SIGNALS = [
    "vendor lock-in",
    "single source",
    "no exit clause",
    "proprietary format",
    "data hostage",
    "switching cost",
    "platform dependency",
    "captive market",
    "exclusive contract",
    "monopoly",
]

AUTONOMY_SIGNALS = [
    "open standard",
    "multi-source",
    "exit clause",
    "portable data",
    "interoperable",
    "open source",
    "competitive market",
    "negotiating power",
    "alternative provider",
    "self-hosted",
]


def evaluate_sovereignty_risk(
    proposal: str,
    capital_type: str,
    context: dict,
) -> dict:
    """
    Evaluate sovereignty risk of a capital allocation proposal.

    Returns: {dimension, score, evidence, epistemic_tag}
    Score: 0.0 (high dependency) to 1.0 (high autonomy)
    """
    proposal_lower = proposal.lower()

    dependency_count = sum(
        1 for signal in DEPENDENCY_SIGNALS if signal in proposal_lower
    )
    autonomy_count = sum(
        1 for signal in AUTONOMY_SIGNALS if signal in proposal_lower
    )

    total = dependency_count + autonomy_count
    if total == 0:
        score = 0.5
        evidence = "No sovereignty signals detected"
        epistemic = EpistemicTag.ASSUMED
    else:
        score = autonomy_count / total
        evidence = (
            f"Found {autonomy_count} autonomy signals "
            f"and {dependency_count} dependency signals"
        )
        epistemic = EpistemicTag.INTERPRETED

    # Derive semantic signal state (Fix 3)
    signal_state, signal_confidence = derive_signal_state(
        score=score,
        pattern_count=dependency_count + autonomy_count,
        has_positive_patterns=autonomy_count > 0,
        has_negative_patterns=dependency_count > 0,
    )

    return {
        "dimension": "sovereignty",
        "score": round(score, 3),
        "signal_state": signal_state.value,
        "signal_confidence": round(signal_confidence, 3),
        "evidence": evidence,
        "epistemic_tag": epistemic.value,
        "dependency_signals": dependency_count,
        "autonomy_signals": autonomy_count,
    }
