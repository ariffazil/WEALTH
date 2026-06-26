"""
WEALTH — Sovereign Governance & Forge Laws
Codification of the 6 Forge Laws and Epistemic Metrics.
"""

from __future__ import annotations

import enum

class ForgeLaw(enum.Enum):
    F1_REVERSIBILITY = "Reversible by default; permanent only by SEAL."
    F2_TRUTH = "Truth over consensus; data origin over metadata."
    F3_WITNESS = "Tri-witness validation: Human, AI, Earth."
    F4_LEGIBILITY = "No hand-wavy math; shadow prices only."
    F5_MARUAH = "Maintain sovereign dignity (Maruah)."
    F6_HUMILITY = "Bound arrogance via kappa_r (Reasoning Coherence)."

def compute_kappa_r(
    rasa_score: float = 0.0,
    truth_consistency: float = 0.0,
    *,
    # Calibrated components (Fix 2: κ_r calibration coupling, 2026-06-21)
    internal_consistency_score: float | None = None,
    evidence_quality_score: float | None = None,
    witness_completeness: float | None = None,
    signal_density: float | None = None,
) -> float:
    """
    Computes Humility score (Reasoning coherence).

    [0.0, 1.0] where 1.0 is perfectly coherent and humble.

    Legacy path: (rasa_score * 0.4) + (truth_consistency * 0.6)

    Calibrated path (Fix 2): multi-component weighted sum:
      0.40 * internal_consistency_score
      0.30 * evidence_quality_score
      0.20 * witness_completeness
      0.10 * signal_density

    A WEAK-evidence + incomplete-witness result yields κ_r ≤ 0.5.
    """
    if internal_consistency_score is not None:
        # Calibrated path with explicit components
        _ics = max(0.0, min(1.0, internal_consistency_score))
        _eqs = max(0.0, min(1.0, evidence_quality_score or 0.1))
        _wc = max(0.0, min(1.0, witness_completeness or 0.1))
        _sd = max(0.0, min(1.0, signal_density or 0.1))
        return round(
            0.40 * _ics
            + 0.30 * _eqs
            + 0.20 * _wc
            + 0.10 * _sd,
            4,
        )
    # Legacy path
    return round((rasa_score * 0.4) + (truth_consistency * 0.6), 4)

def compute_psi_le(legibility_entropy: float, complexity: float) -> float:
    """
    Computes psi_le (Legibility entropy).
    Measures the gap between model complexity and human-auditable legibility.
    """
    return round(legibility_entropy / (1.0 + complexity), 4)

def get_qdf_version() -> str:
    """Returns the current Quantitative Decision Framework version."""
    return "QDF-v2.0-TRINITY"
