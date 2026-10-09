"""WEALTH forecast — chart pattern regime-conditioned scoring (patterns package).

Standalone importable. No dependency on the rest of ``forecast.orchestrator``.

This package hosts the meta-analysis layer that decides **whether any of the
chart patterns produced by sa-0's pattern module actually have positive edge
under the current APEX regime**. The honest rule is binding: if no pattern
shows walk-forward-validated edge in the current regime, the scorer must
return ``NO_RECOMMENDATION`` and explicitly recommend SHADOW. The module
never invents edge from thin samples.

Public surface (re-exported below for convenience):

    from forecast.patterns import (
        PatternStats,
        ApexStateSnapshot,
        PatternScore,
        RegimeRanking,
        RegimeScoringResult,
        score_patterns,
        NO_RECOMMENDATION,
        STATUS_SHADOW,
        DEFAULT_MIN_SAMPLE_SIZE,
        DEFAULT_MIN_CI_LOWER,
        DEFAULT_WILSON_Z,
    )

Laws binding this package
-------------------------
* NO FABRICATED EDGE. A pattern's edge must come from a walk-forward harness
  output (``walk_forward_validated=True``) with sufficient sample size; thin
  or backtested-only samples collapse to ``UNKNOWN`` confidence and are
  excluded from any ACT recommendation.
* If the regime is UNKNOWN, or no pattern passes the validation gate for the
  regime, the only admissible verdict is ``NO_RECOMMENDATION`` + SHADOW.
* Top-3 ranking per regime is honest about its CI — every score carries a
  Wilson lower bound on the edge, never a point estimate alone.
* Default status = SHADOW (matches ``forecast.orchestrator`` doctrine).
* This module is pure: it never mutates any global state and never imports
  the live API client.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from .regime_scoring import (
    # Constants — vocabulary
    NO_RECOMMENDATION,
    STATUS_SHADOW,
    VALID_REGIMES,
    DEFAULT_MIN_SAMPLE_SIZE,
    DEFAULT_MIN_CI_LOWER,
    DEFAULT_WILSON_Z,
    # Typed contracts
    PatternStats,
    ApexStateSnapshot,
    PatternScore,
    RegimeRanking,
    RegimeScoringResult,
    # Pure scorer
    score_patterns,
    # Lower-level helpers (exposed for tests)
    _wilson_lower_bound,
    _is_pattern_eligible,
)

__all__ = [
    "NO_RECOMMENDATION",
    "STATUS_SHADOW",
    "VALID_REGIMES",
    "DEFAULT_MIN_SAMPLE_SIZE",
    "DEFAULT_MIN_CI_LOWER",
    "DEFAULT_WILSON_Z",
    "PatternStats",
    "ApexStateSnapshot",
    "PatternScore",
    "RegimeRanking",
    "RegimeScoringResult",
    "score_patterns",
]
