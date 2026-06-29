"""
WEALTH Core — Epistemic Intelligence: Contradiction Density Scorer.

Truth emerges from wells disagreeing with models, not from institutional consensus.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

# Signals of contradiction / inconsistency
CONTRADICTION_SIGNALS = [
    "inconsistent",
    "contradicts",
    "disagrees",
    "conflicts",
    "at odds",
    "does not match",
    "incompatible",
    "divergent",
    "different outcome",
    "unexpected",
    "surprising",
    "anomalous",
    "outlier",
    "does not fit",
    "breaks the pattern",
    "against expectation",
    "counter to",
    "contrary to",
    "unlike",
    "different from",
    "variability",
    "heterogeneous",
    "mixed results",
    "three wells",
    "three outcomes",
    "each well different",
    "no consistent",
]

# Signals of false consensus / smoothing
CONSENSUS_SIGNALS = [
    "consistent",
    "agreement",
    "confirms",
    "supports",
    "validates",
    "corroborates",
    "in line with",
    "as expected",
    "predicted",
    "forecast",
    "model predicts",
    "theory says",
    "should be",
    "ought to be",
    "smooth",
    "uniform",
    "homogeneous",
    "coherent",
    "aligned",
]


def detect_contradiction_density(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect contradiction density — wells disagreeing with models.

    Returns: {dimension, risk_level, evidence, contradiction_count, consensus_count,
              contradiction_ratio, truth_source}
    """
    scenario_lower = scenario.lower()

    contradiction_count = sum(
        1 for signal in CONTRADICTION_SIGNALS if signal in scenario_lower
    )
    consensus_count = sum(1 for signal in CONSENSUS_SIGNALS if signal in scenario_lower)

    # Check context for explicit contradiction data
    outcomes = context.get("outcomes", [])
    if isinstance(outcomes, list) and len(outcomes) > 1:
        # Multiple different outcomes = contradiction
        unique_outcomes = len(set(str(o) for o in outcomes))
        if unique_outcomes > 1:
            contradiction_count += unique_outcomes

    total = contradiction_count + consensus_count
    contradiction_ratio = contradiction_count / max(1, total)

    # Determine truth source
    truth_source = "unknown"
    if contradiction_count > consensus_count:
        truth_source = "contradiction_pattern"
    elif consensus_count > contradiction_count:
        truth_source = "consensus"
    elif total == 0:
        truth_source = "no_signal"

    if total == 0:
        risk_level = "LOW"
        evidence = "No contradiction signals detected"
    elif contradiction_ratio > 0.7:
        risk_level = "HIGH"
        evidence = (
            f"High contradiction density: {contradiction_count} contradiction vs {consensus_count} consensus signals. "
            f"Truth likely emerging from pattern inconsistency, not institutional analysis."
        )
    elif contradiction_ratio > 0.5:
        risk_level = "MEDIUM"
        evidence = f"Moderate contradiction density: {contradiction_count} contradiction vs {consensus_count} consensus signals."
    else:
        risk_level = "LOW"
        evidence = f"Consensus signals dominate: {consensus_count} vs {contradiction_count} contradiction"

    return {
        "dimension": "contradiction_density",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "contradiction_count": contradiction_count,
        "consensus_count": consensus_count,
        "contradiction_ratio": round(contradiction_ratio, 3),
        "truth_source": truth_source,
        "outcomes_analyzed": len(outcomes) if isinstance(outcomes, list) else 0,
    }
