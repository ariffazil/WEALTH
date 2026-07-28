"""
well_dark_geometry_mirror — Mirror dark-geometry signals without judgment.

Input: text or conversation events, baseline reference, time window, optional vitality signals.
Output: signals only, alternative explanations, counterevidence, trajectory, reflection questions.

Modes: language, behavioral, relational, combined
"""

import uuid
from datetime import datetime, timezone


LANGUAGE_SIGNALS = {
    "responsibility_shift": {
        "patterns": ["the system decided", "it was determined", "process requires",
                      "we have no choice", "it's out of my hands", "the algorithm"],
        "weight": 0.7,
        "benign": "May be accurately describing institutional process",
    },
    "certainty_creep": {
        "patterns": ["obviously", "clearly", "everyone knows", "undeniable",
                      "no reasonable person", "it's simply a fact"],
        "weight": 0.5,
        "benign": "May reflect genuine confidence from evidence; check if challenged",
    },
    "niat_substitution": {
        "patterns": ["our intention was", "we meant to", "the goal was always",
                      "what we wanted was", "our purpose was"],
        "weight": 0.6,
        "benign": "May be providing context before discussing impact",
    },
    "scale_empathy_collapse": {
        "patterns": ["numbers show", "statistics indicate", "the data says",
                      "quantitatively", "in terms of volume"],
        "weight": 0.4,
        "benign": "Statistical reporting is appropriate in many contexts",
    },
    "witness_delegitimization": {
        "patterns": ["they don't understand", "they weren't there", "they have an agenda",
                      "that's not what happened", "they're being emotional"],
        "weight": 0.8,
        "benign": "May be providing missing context; check if substance is addressed",
    },
}


def _analyze_language(text: str) -> list[dict]:
    """Detect language signals in text."""
    signals = []
    text_lower = text.lower()
    for signal_name, config in LANGUAGE_SIGNALS.items():
        matches = [p for p in config["patterns"] if p in text_lower]
        if matches:
            signals.append({
                "signal": signal_name,
                "matches": matches,
                "weight": config["weight"],
                "benign_alternative": config["benign"],
            })
    return signals


def well_dark_geometry_mirror(
    text: str = "",
    mode: str = "language",
    baseline_ref: str | None = None,
    time_window: str | None = None,
    vitality_signals: dict | None = None,
) -> dict:
    """
    Mirror dark-geometry signals without judgment.

    Args:
        text: Text or conversation to analyze
        mode: language | behavioral | relational | combined
        baseline_ref: Baseline reference for comparison
        time_window: Time window for observation
        vitality_signals: Optional vitality data from WELL sensors

    Returns:
        entropy_mirror format with signals, alternatives, counterevidence, reflection
    """
    signals = []
    trajectory = {}

    if mode in ("language", "combined"):
        lang_signals = _analyze_language(text)
        signals.extend(lang_signals)

    if mode in ("behavioral", "combined") and vitality_signals:
        # Analyze behavioral patterns from vitality data
        flux = vitality_signals.get("metabolic_flux", 0.5)
        if flux > 0.7:
            signals.append({
                "signal": "elevated_metabolic_flux",
                "value": flux,
                "weight": 0.6,
                "benign_alternative": "May reflect high workload or external stress, not internal dysfunction",
            })

    # Trajectory
    trajectory = {
        "recurrence": len(signals),
        "baseline_delta": round(sum(s["weight"] for s in signals) / max(len(signals), 1), 4),
        "time_window": time_window or "current",
    }

    return {
        "mirror_id": f"dm-{uuid.uuid4().hex[:12]}",
        "status": "SIGNAL" if len(signals) <= 1 else "PATTERN",
        "organ": "WELL",
        "mode": mode,
        "observed": [f"Signal: {s['signal']} ({len(s.get('matches', []))} matches)" for s in signals],
        "trajectory": trajectory,
        "alternative_explanations": [s["benign_alternative"] for s in signals],
        "counterevidence": [],
        "reflection": [
            "Who had the power to stop this action?",
            "Who carries the cost if the decision is wrong?",
            "Has the stated good intention displaced discussion of repair?",
        ],
        "prohibited_conclusion": [
            "Do not infer hidden niat.",
            "Do not classify the actor as evil.",
        ],
        "metadata": {
            "mirrored_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_dark_geometry_mirror",
            "schema_version": "v1",
        },
    }
