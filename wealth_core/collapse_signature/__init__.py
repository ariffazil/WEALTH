"""
WEALTH Core — Institutional Collapse Pattern Library + Scanner.

Public surface:
- patterns: SIGNAL lists and full_signature_profile + collapse_risk_score
- scanner: POWER_DIMENSION_INSTITUTIONAL_SIGNALS, WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS,
  enrich_dimension_with_institutional_signals, compute_collapse_risk

Calibration fix 2026-06-17: sovereign institutional collapse patterns
(1MDB, royalty, PETROS, SEARAH, etc.) cross-loaded into power_audit,
wisdom_evaluate, capture_scan dimension evaluators.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from .patterns import (
    NATIONAL_DESTINY_SIGNALS,
    TRIUMPHALISM_SIGNALS,
    COMPLEXITY_AS_VIRTUE,
    IDEOLOGICAL_CERTAINTY_SIGNALS,
    POLITICISATION_SIGNALS,
    PURGE_AND_CLEANSING_SIGNALS,
    EXTRACTION_NARRATIVE_SIGNALS,
    REINVESTMENT_SUPPRESSION_SIGNALS,
    EXTERNAL_BLAME_SIGNALS,
    DENIAL_OF_INTERNAL_FAILURE_SIGNALS,
    TIME_PRESSURE_PR_SIGNALS,
    BOILERPLATE_RISK_SIGNALS,
    GENERIC_GOVERNANCE_SIGNALS,
    OVER_PROMISE_SIGNALS,
    UNDER_DELIVERY_HEDGE_SIGNALS,
    QUARTERLY_BEAT_LANGUAGE_SIGNALS,
    RELATED_PARTY_SIGNALS,
    JURISDICTION_SHOPPING_SIGNALS,
    STRUCTURAL_GRIEVANCE_SIGNALS,
    count_matches,
    count_axis,
    full_signature_profile,
    collapse_risk_score,
)

from .scanner import (
    POWER_DIMENSION_INSTITUTIONAL_SIGNALS,
    WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS,
    enrich_dimension_with_institutional_signals,
    compute_collapse_risk,
)

__all__ = [
    # Signal lists
    "NATIONAL_DESTINY_SIGNALS",
    "TRIUMPHALISM_SIGNALS",
    "COMPLEXITY_AS_VIRTUE",
    "IDEOLOGICAL_CERTAINTY_SIGNALS",
    "POLITICISATION_SIGNALS",
    "PURGE_AND_CLEANSING_SIGNALS",
    "EXTRACTION_NARRATIVE_SIGNALS",
    "REINVESTMENT_SUPPRESSION_SIGNALS",
    "EXTERNAL_BLAME_SIGNALS",
    "DENIAL_OF_INTERNAL_FAILURE_SIGNALS",
    "TIME_PRESSURE_PR_SIGNALS",
    "BOILERPLATE_RISK_SIGNALS",
    "GENERIC_GOVERNANCE_SIGNALS",
    "OVER_PROMISE_SIGNALS",
    "UNDER_DELIVERY_HEDGE_SIGNALS",
    "QUARTERLY_BEAT_LANGUAGE_SIGNALS",
    "RELATED_PARTY_SIGNALS",
    "JURISDICTION_SHOPPING_SIGNALS",
    "STRUCTURAL_GRIEVANCE_SIGNALS",
    # Matcher primitives
    "count_matches",
    "count_axis",
    "full_signature_profile",
    "collapse_risk_score",
    # Cross-loaded dimension signals
    "POWER_DIMENSION_INSTITUTIONAL_SIGNALS",
    "WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS",
    "enrich_dimension_with_institutional_signals",
    "compute_collapse_risk",
]