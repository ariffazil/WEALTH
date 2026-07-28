"""
well_trust_compression — Detect narrowing trust patterns.

Detects: all-or-nothing trust, universal threat language, repeated loyalty tests,
reduced witness diversity, increasing control requests.
"""

import uuid
from datetime import datetime, timezone


TRUST_COMPRESSION_SIGNALS = {
    "all_or_nothing": {
        "patterns": ["completely trust", "totally reliable", "absolute confidence",
                      "never trust", "can't be relied on", "zero faith"],
        "weight": 0.7,
        "description": "Binary trust classification — no gradation",
    },
    "universal_threat": {
        "patterns": ["everyone is", "nobody can be", "all of them", "the whole system",
                      "every single", "no one is safe"],
        "weight": 0.8,
        "description": "Universal threat language — no exceptions acknowledged",
    },
    "loyalty_test": {
        "patterns": ["prove your loyalty", "are you with us", "whose side",
                      "show your commitment", "demonstrate allegiance"],
        "weight": 0.9,
        "description": "Repeated loyalty tests — trust conditional on compliance",
    },
    "witness_narrowing": {
        "patterns": ["only we understand", "outsiders don't", "they wouldn't get it",
                      "circle of trust", "inner circle"],
        "weight": 0.7,
        "description": "Reduced witness diversity — echo chamber formation",
    },
    "control_escalation": {
        "patterns": ["need to approve", "must be authorized", "require permission",
                      "check with me first", "don't do anything without"],
        "weight": 0.6,
        "description": "Increasing control requests — trust delegation narrowing",
    },
}


def well_trust_compression(
    text: str = "",
    events: list[dict] | None = None,
    baseline_trust_diversity: float | None = None,
) -> dict:
    """
    Detect narrowing trust patterns.

    Args:
        text: Text to analyze for trust compression signals
        events: Optional list of trust-related events with timestamps
        baseline_trust_diversity: Baseline diversity score (0-1)

    Returns:
        entropy_mirror format with trust compression signals
    """
    signals = []
    text_lower = text.lower()

    for signal_name, config in TRUST_COMPRESSION_SIGNALS.items():
        matches = [p for p in config["patterns"] if p in text_lower]
        if matches:
            signals.append({
                "signal": signal_name,
                "matches": matches,
                "weight": config["weight"],
                "description": config["description"],
            })

    # Compute compression score
    if signals:
        compression_score = sum(s["weight"] for s in signals) / len(signals)
    else:
        compression_score = 0.0

    # Trajectory from events
    recurrence = len(events) if events else len(signals)

    return {
        "mirror_id": f"tc-{uuid.uuid4().hex[:12]}",
        "status": "SIGNAL" if len(signals) <= 1 else "PATTERN",
        "organ": "WELL",
        "observed": [f"{s['signal']}: {s['description']}" for s in signals],
        "trajectory": {
            "recurrence": recurrence,
            "compression_score": round(compression_score, 4),
            "baseline_delta": round(
                abs(compression_score - (baseline_trust_diversity or 0.5)), 4
            ) if baseline_trust_diversity else None,
        },
        "alternative_explanations": [
            "Trust narrowing may reflect a specific breach, not general paranoia.",
            "Control requests may reflect genuine risk management.",
            "Witness narrowing may reflect privacy concerns, not echo chamber.",
            "Loyalty language may reflect team cohesion, not coercion.",
        ],
        "counterevidence": [],
        "reflection": [
            "Is the trust narrowing proportional to a specific event?",
            "Are new voices being welcomed or excluded?",
            "Has the circle of trust expanded or contracted over time?",
        ],
        "prohibited_conclusion": [
            "Do not infer hidden distrust from communication style.",
            "Do not classify trust patterns as permanent traits.",
        ],
        "metadata": {
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_trust_compression",
        },
    }
