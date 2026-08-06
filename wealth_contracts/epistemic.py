"""
WEALTH Contracts — Epistemic tagging and evidence quality.

CANONICAL ENUM SOURCE: /root/arifOS/arifosmcp/schemas/federation_enums.py
All new code SHOULD import from arifOS federation_enums.
This file exists for backward compatibility with existing WEALTH code.

F2 TRUTH: Never claim certainty without evidence.
Every output carries an epistemic tag and evidence quality label.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL ENUMS — Import from arifOS federation source
# ═══════════════════════════════════════════════════════════════════════════════

# Canonical enums for new code:
#   from arifosmcp.schemas.federation_enums import (
#       EvidenceQuality as CanonicalEvidenceQuality,
#       ConfidenceLevel,
#       EpistemicLabel,
#   )
# These match the values below exactly. The local definitions are
# kept for independent operation when arifOS is not importable.

# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL ENUMS — Match canonical values in federation_enums.py
# ═══════════════════════════════════════════════════════════════════════════════


class EpistemicTag(str, Enum):
    """Label every claim with its epistemic strength.
    Unified system: supports both OBSERVED/DERIVED (GEOX-style)
    and CLAIM/PLAUSIBLE (Bursa-style) via canonical mapping.

    VALUES MUST MATCH arifOS federation_enums.EpistemicLabel
    """

    OBSERVED = "OBSERVED"  # Direct measurement (price, rate, balance)
    DERIVED = "DERIVED"  # Computed from observed data (NPV, IRR)
    INTERPRETED = "INTERPRETED"  # Inferred from patterns (trend, regime)
    SPECULATED = "SPECULATED"  # Hypothesis without sufficient evidence
    ASSUMED = "ASSUMED"  # Input parameter, not verified

    # Aliases for Bursa/monolith compatibility
    CLAIM = "OBSERVED"  # CLAIM = OBSERVED (strongest)
    PLAUSIBLE = "DERIVED"  # PLAUSIBLE = DERIVED
    ESTIMATE = "INTERPRETED"  # ESTIMATE = INTERPRETED
    HYPOTHESIS = "SPECULATED"  # HYPOTHESIS = SPECULATED
    UNKNOWN = "ASSUMED"  # UNKNOWN = ASSUMED (weakest)


# Canonical ordering for comparison
EPISTEMIC_ORDER = ["ASSUMED", "SPECULATED", "INTERPRETED", "DERIVED", "OBSERVED"]

# Bursa-style aliases for compatibility
BURSA_TAG_MAP = {
    "CLAIM": "OBSERVED",
    "PLAUSIBLE": "DERIVED",
    "ESTIMATE": "INTERPRETED",
    "HYPOTHESIS": "SPECULATED",
    "UNKNOWN": "ASSUMED",
    "OBS": "OBSERVED",
    "DER": "DERIVED",
    "INT": "INTERPRETED",
    "SPEC": "SPECULATED",
}


def normalize_epistemic_tag(tag: str) -> EpistemicTag:
    """Normalize any epistemic tag variant to canonical form."""
    upper = tag.upper().strip()
    if upper in BURSA_TAG_MAP:
        upper = BURSA_TAG_MAP[upper]
    try:
        return EpistemicTag(upper)
    except ValueError:
        return EpistemicTag.ASSUMED  # Default to weakest


class ClaimState(str, Enum):
    """Where is this claim in the governance pipeline?"""

    DRAFT = "DRAFT"  # Initial computation
    QC_VERIFIED = "QC_VERIFIED"  # Passed data quality checks
    VALIDATED = "VALIDATED"  # Passed constitutional review
    SEALED = "SEALED"  # Irreversibly written to VAULT999
    CHALLENGED = "CHALLENGED"  # Competing claim exists
    VOID = "VOID"  # Rejected by governance


class EvidenceQuality(str, Enum):
    """How strong is the evidence behind this output?

    LEGACY VALUES (WEALTH v1): STRONG, MODERATE, WEAK, MISSING, CONFLICTED
    CANONICAL VALUES (federation_enums.py): OBSERVED, DERIVED, INTERPRETED, SPECULATED, ASSUMED

    LEGACY VALUES ARE DEPRECATED. New code should use canonical values.
    See: /root/arifOS/arifosmcp/schemas/federation_enums.py
    """

    STRONG = "STRONG"  # Multiple corroborating sources
    MODERATE = "MODERATE"  # Single reliable source
    WEAK = "WEAK"  # Inferred or analogical
    MISSING = "MISSING"  # No evidence provided
    CONFLICTED = "CONFLICTED"  # Evidence contradicts itself

    # Canonical aliases (same values as federation_enums.EvidenceQuality)
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INTERPRETED = "INTERPRETED"
    SPECULATED = "SPECULATED"
    ASSUMED = "ASSUMED"


# Canonical EvidenceQuality mapping (legacy → canonical)
EVIDENCE_QUALITY_CANONICAL_MAP = {
    EvidenceQuality.STRONG: EvidenceQuality.OBSERVED,
    EvidenceQuality.MODERATE: EvidenceQuality.DERIVED,
    EvidenceQuality.WEAK: EvidenceQuality.INTERPRETED,
    EvidenceQuality.MISSING: EvidenceQuality.SPECULATED,
    EvidenceQuality.CONFLICTED: EvidenceQuality.SPECULATED,
}


class UncertaintyBand:
    """Uncertainty range for numerical outputs."""

    def __init__(
        self,
        p10: Optional[float] = None,
        p50: Optional[float] = None,
        p90: Optional[float] = None,
        distribution: str = "unknown",
    ):
        self.p10 = p10
        self.p50 = p50
        self.p90 = p90
        self.distribution = distribution

    def to_dict(self) -> dict:
        return {
            "p10": self.p10,
            "p50": self.p50,
            "p90": self.p90,
            "distribution": self.distribution,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UncertaintyBand":
        return cls(
            p10=d.get("p10"),
            p50=d.get("p50"),
            p90=d.get("p90"),
            distribution=d.get("distribution", "unknown"),
        )


class MissingInput:
    """What evidence would strengthen this output?"""

    def __init__(self, name: str, description: str, impact_if_obtained: str):
        self.name = name
        self.description = description
        self.impact_if_obtained = impact_if_obtained

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "impact_if_obtained": self.impact_if_obtained,
        }


def upgrade_epistemic(current: EpistemicTag, new_evidence: str) -> EpistemicTag:
    """Upgrade epistemic tag when new evidence arrives."""
    hierarchy = [
        EpistemicTag.ASSUMED,
        EpistemicTag.SPECULATED,
        EpistemicTag.INTERPRETED,
        EpistemicTag.DERIVED,
        EpistemicTag.OBSERVED,
    ]
    current_idx = hierarchy.index(current)
    if current_idx < len(hierarchy) - 1:
        return hierarchy[current_idx + 1]
    return current


# ═══════════════════════════════════════════════════════════════════════════════
# W-004 — UNMEASURED Sentinel + Coverage Aggregation (2026-08-06)
# ═══════════════════════════════════════════════════════════════════════════════
# Mirrors arifOS kernel: /root/arifOS/arifosmcp/runtime/unmeasured.py
# Singleton. Identity-check `is UNMEASURED` is safe. Any coercion raises.
# ═══════════════════════════════════════════════════════════════════════════════

from typing import Any, NoReturn


class UnmeasuredError(TypeError):
    """Raised when UNMEASURED is coerced to a truth value or number."""


class _Unmeasured:
    """Sentinel for values that have not been measured.

    Singleton. Identity-check with `is UNMEASURED` (safe). Any attempt
    to coerce to bool, float, int, or compare numerically raises.
    """

    _instance: _Unmeasured | None = None

    def __new__(cls) -> _Unmeasured:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNMEASURED"

    def __str__(self) -> str:
        return "UNMEASURED"

    def __hash__(self) -> int:
        return hash("UNMEASURED")

    def __eq__(self, other: object) -> bool:
        return False

    def __ne__(self, other: object) -> bool:
        return True

    def __bool__(self) -> NoReturn:
        raise UnmeasuredError("UNMEASURED has no truth value")

    def __float__(self) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not a number")

    def __int__(self) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not a number")

    def __lt__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not ordered")

    def __gt__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not ordered")

    def __le__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not ordered")

    def __ge__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED is not ordered")

    def __add__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED cannot be used in arithmetic")

    def __mul__(self, other: object) -> NoReturn:
        raise UnmeasuredError("UNMEASURED cannot be used in arithmetic")

    def as_string_safe(self) -> str:
        return "UNMEASURED"


UNMEASURED = _Unmeasured()


def is_unmeasured(value: Any) -> bool:
    """Safe check: returns True ONLY if value IS the UNMEASURED sentinel."""
    return value is UNMEASURED


# ═══════════════════════════════════════════════════════════════════════════════
# Coverage Aggregation — geometric mean over KNOWN terms only
# ═══════════════════════════════════════════════════════════════════════════════


def geometric_mean_known(values: list[float | _Unmeasured]) -> float | _Unmeasured:
    """Geometric mean over KNOWN (non-UNMEASURED) terms only.

    Never impute 0 or 1 for UNMEASURED — that is the Enron/Holocaust defect.
    Returns UNMEASURED if ALL values are UNMEASURED.
    """
    import math

    known = [v for v in values if v is not UNMEASURED and isinstance(v, (int, float))]
    if not known:
        return UNMEASURED
    product = math.prod(max(v, 1e-10) for v in known)
    return float(product ** (1.0 / len(known)))


def coverage_ratio(known: int, total: int) -> float:
    """Coverage ratio: known / total. Returns -1.0 (UNMEASURED) if total <= 0."""
    if total <= 0:
        return -1.0  # UNMEASURED sentinel — cannot divide by zero
    return round(known / total, 2)


MIN_COVERAGE_THRESHOLD = 0.15  # Below this → INSUFFICIENT_EVIDENCE
