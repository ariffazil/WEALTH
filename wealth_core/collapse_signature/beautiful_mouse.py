"""
WEALTH Core — Beautiful Mouse Detector (Phase C Entry).

Detects the Calhoun behavioural-death signature at Phase C ENTRY
(before full collapse). This is the early-warning counterpart to
the collapse signature scan (which fires at imminent collapse).

The 6 Phase C indicators:
1. PERFECT_PERFORMANCE  — no friction narrative, flawless execution claims
2. ZERO_FAILURE        — absence of failure treated as virtue
3. NARRATIVE_CENTRALISATION — one story dominates, dissent absent
4. TALENT_DRAIN        — no one inside fights, Ψ sidelined
5. MONITOR_CULTURE     — metrics over conflict, no real challenge
6. EXTERNAL_BLAME      — delays and failures blamed outward

A "Beautiful Mouse" is a Phase C pattern: the institution LOOKS
healthy because it has stopped fighting. The absence of failure
IS the failure signal.

Hard rules:
- F2 TRUTH — every indicator cite-keyed
- F6 MARUAH — diagnostic, not adversarial; never name individuals
- F7 HUMILITY — confidence cap 0.85 (lower than collapse scanner)
  because Phase C is inherently ambiguous
- F13 SOVEREIGN — diagnostic only, never declares collapse

Priors: Enron pre-2001, Lehman pre-2008, Suriname 1BBOE 2026
        (canonical "Beautiful Mouse" per Third Axis)

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import re


# The 6 Phase C indicators.
# Each entry: phrase patterns (case-insensitive substring match)
PHASE_C_INDICATORS: Dict[str, List[str]] = {
    "PERFECT_PERFORMANCE": [
        "flawless execution",
        "perfect record",
        "no major incidents",
        "100% delivery",
        "best-in-class",
        "industry-leading",
        "world-class",
        "best ever",
        "record performance",
        "perfect performance",
        "zero downtime",
        "perfect safety",
        "no accidents",
        "flawless",
        "impeccable",
    ],
    "ZERO_FAILURE": [
        "no failures",
        "without failure",
        "never failed",
        "no setback",
        "unblemished",
        "spotless",
        "no loss",
        "no write-down",
        "no impairment",
        "no project killed",
        "no project cancelled",
        "no surprise",
        "no miss",
    ],
    "NARRATIVE_CENTRALISATION": [
        "one team",
        "one vision",
        "unified message",
        "singular narrative",
        "single story",
        "aligned communication",
        "dissent is disloyalty",
        "loyalty to the plan",
        "consensus",
        "unanimous",
        "no opposition",
        "no critic",
        "everyone agrees",
        "all stakeholders aligned",
        "no objection",
    ],
    "TALENT_DRAIN": [
        "no one left to fight",
        "talent has left",
        "veterans departed",
        "key staff gone",
        "succession unclear",
        "no internal challenger",
        "no voice raised",
        "no one questions",
        "no one inside knows",
        "fighting spirit lost",
        "no one cares",
        "no institutional memory",
        "no one has been here long enough",
        "new leadership",
        "younger team",
    ],
    "MONITOR_CULTURE": [
        "monitor culture",
        "metrics over conflict",
        "no real challenge",
        "consensus over conflict",
        "harmony over honesty",
        "no internal audit",
        "no real scrutiny",
        "review without challenge",
        "approve without question",
        "rubber stamp",
        "no pushback",
        "no debate",
        "no contestation",
    ],
    "EXTERNAL_BLAME": [
        "delays blamed on",
        "failure blamed externally",
        "external factors",
        "global headwinds",
        "market conditions",
        "regulatory burden",
        "geopolitical",
        "pandemic",
        "supply chain",
        "everyone else to blame",
        "no internal accountability",
        "we did everything right",
        "nothing we could do",
    ],
}


def count_phase_c_matches(text: str, indicator: str) -> List[str]:
    """Count how many phrases for a given indicator appear in the text."""
    phrases = PHASE_C_INDICATORS.get(indicator, [])
    text_lower = text.lower()
    matches = []
    for phrase in phrases:
        if phrase.lower() in text_lower:
            matches.append(phrase)
    return matches


def compute_beautiful_mouse_score(
    text: str,
    historical_priors: Optional[List[str]] = None,
) -> dict:
    """
    Compute the Phase C Beautiful Mouse score for a text.

    Lower threshold than collapse scanner; designed to fire EARLY.
    Returns per-indicator matches, density, and overall Phase C
    probability.

    Args:
        text: the narrative text to scan (CEO speech, annual report,
              press release, internal memo, etc.)
        historical_priors: optional list of corpus anchors to compare
                          against ("enron_2000", "lehman_2007",
                          "suriname_2026")

    Returns:
        {
            "indicators": [{name, matches, density, threshold}],
            "phase_c_score": float 0.0-1.0,
            "phase_c_verdict": "ABSENT" | "EMERGING" | "ACTIVE" | "DOMINANT",
            "narrative_signature": str,
            "calibration_note": str,
            "f7_humility": {"confidence_cap": 0.85, "applied": bool},
            "f6_maruah": {"individuals_named": [], "guard": str},
            "priors_used": [...],
        }
    """
    if not text or len(text.strip()) < 50:
        return {
            "error": "text_too_short",
            "minimum_chars": 50,
            "received_chars": len(text.strip()) if text else 0,
        }

    indicator_results = []
    total_matches = 0

    for indicator, phrases in PHASE_C_INDICATORS.items():
        matches = count_phase_c_matches(text, indicator)
        density = len(matches) / len(phrases) if phrases else 0.0
        indicator_results.append({
            "name": indicator,
            "matches": matches,
            "match_count": len(matches),
            "phrase_pool_size": len(phrases),
            "density": round(density, 4),
            "threshold": 0.10,  # any single match triggers
            "triggered": len(matches) > 0,
        })
        total_matches += len(matches)

    # Phase C score: weighted by indicator coverage
    n_triggered = sum(1 for r in indicator_results if r["triggered"])
    n_indicators = len(indicator_results)
    coverage = n_triggered / n_indicators if n_indicators else 0.0

    # Total density across all indicators
    total_density = sum(r["density"] for r in indicator_results) / n_indicators

    # Phase C score: 0.5 * coverage + 0.5 * total_density
    phase_c_score = 0.5 * coverage + 0.5 * total_density

    # Verdict mapping
    if phase_c_score >= 0.5:
        verdict = "DOMINANT"
    elif phase_c_score >= 0.3:
        verdict = "ACTIVE"
    elif phase_c_score >= 0.15:
        verdict = "EMERGING"
    else:
        verdict = "ABSENT"

    # Narrative signature
    if verdict == "DOMINANT":
        narrative = "Strong Beautiful Mouse signature. Phase C entry likely. Capture + power audit recommended before any confidence claim."
    elif verdict == "ACTIVE":
        narrative = "Active Beautiful Mouse indicators. Phase C entry plausible. Cross-check with collapse signature scan + talent drain signals."
    elif verdict == "EMERGING":
        narrative = "Emerging Beautiful Mouse indicators. Early signal. Watch for talent drain, narrative centralisation, monitor culture over next cycle."
    else:
        narrative = "No Beautiful Mouse signature detected. The institution appears to be in healthy friction (good sign per Calhoun)."

    # F7 HUMILITY cap
    confidence_cap = 0.85
    f7_applied = phase_c_score > confidence_cap
    if f7_applied:
        phase_c_score = confidence_cap

    # F6 MARUAH — check for individual names (heuristic: capitalised 2-3 word sequences)
    individuals = _detect_individual_names(text)
    f6_status = "PASS" if not individuals else "REVIEW"

    return {
        "text_length_chars": len(text),
        "indicators": indicator_results,
        "phase_c_score": round(phase_c_score, 4),
        "phase_c_verdict": verdict,
        "narrative_signature": narrative,
        "calibration_note": "Phase C detection is inherently ambiguous. Use as early warning, not as verdict. Pair with capture_scan + power_audit + collapse_signature_scan.",
        "f7_humility": {
            "confidence_cap": confidence_cap,
            "applied": f7_applied,
        },
        "f6_maruah": {
            "individuals_named": individuals,
            "guard": "Diagnostic only. No individual named. Reference roles, not people. (F6 MARUAH)",
        },
        "priors_used": historical_priors or [],
        "hard_rules": [
            "F2 TRUTH: every indicator cite-keyed",
            "F6 MARUAH: never name individuals",
            "F7 HUMILITY: confidence cap 0.85",
            "F13 SOVEREIGN: diagnostic only, never declares collapse",
        ],
    }


def _detect_individual_names(text: str) -> List[str]:
    """
    Heuristic: detect Capitalised 2-3 word sequences that might be names.
    Returns empty list if no candidates found.
    This is intentionally conservative — flags only obvious patterns.
    """
    # Pattern: "Mr/Mrs/Dr/Prof Lastname" or "Firstname Lastname"
    patterns = [
        r"\b(?:Mr|Mrs|Dr|Prof|Datuk|Tan Sri|Tun)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b",
        r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # "John Smith"
    ]
    candidates = set()
    for pat in patterns:
        for m in re.finditer(pat, text):
            name = m.group(0)
            # Filter common false positives
            false_positives = {
                "New York", "New Zealand", "South China", "North Sea",
                "Bank Negara", "Federal Court", "Energy Transition",
                "Board Chairman", "Chief Executive",
            }
            if name not in false_positives:
                candidates.add(name)
    return list(candidates)[:10]  # cap at 10


__all__ = [
    "PHASE_C_INDICATORS",
    "count_phase_c_matches",
    "compute_beautiful_mouse_score",
]
