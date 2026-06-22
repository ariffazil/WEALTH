"""
WEALTH Envelope — Standard output wrapper for every WEALTH tool result.

Every WEALTH tool returns an envelope of this shape:
{
    "verdict": "SAFE_TO_STUDY" | "NEEDS_DATA" | "UNSAFE" | "888_HOLD" | "MATH_ERROR",
    "execution_authorized": False,   # WEALTH computes; arifOS gates; Arif decides
    "recommendation_only": True,
    "epistemic_status": "OBS" | "DER" | "INT" | "SPEC",
    "data": <tool-specific payload>,
    "lineage_id": "<uuid>",
    "transform_hash": "b3:...",
    "session_id": "<seal-...>",
    "timestamp": "2026-06-15T16:50:00Z",
    "risk_floor": "F11_AUDIT",
    "blast_radius": "LOW" | "MEDIUM" | "HIGH",
    "human_ack_required": False,
}

F13 SOVEREIGN: WEALTH is EVIDENCE_ONLY. execution_authorized is always False.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class VerdictLabel(str, Enum):
    """WEALTH tool verdicts (mirror the existing `verdict` strings)."""

    SAFE_TO_STUDY = "SAFE_TO_STUDY"
    NEEDS_DATA = "NEEDS_DATA"
    UNSAFE = "UNSAFE"
    HOLD_888 = "888_HOLD"
    MATH_ERROR = "MATH_ERROR"
    SEAL = "SEAL"
    SABAR = "SABAR"


class ExecutionAuthority(str, Enum):
    """Who has execution authority. WEALTH is always NONE (evidence-only)."""

    NONE = "NONE"  # WEALTH itself — evidence only
    ARIFOS = "arifOS"  # Constitutional kernel
    ARIF = "arif"  # F13 SOVEREIGN


class ClaimState(str, Enum):
    """Fix 4: Witness completeness gate states."""

    SEAL = "SEAL"
    HOLD = "HOLD"
    BLOCKED = "BLOCKED"


# Fix 6: 888_HOLD trigger patterns
TRIGGER_888_HOLD_PATTERNS: set[str] = {
    "sovereignty_degradation",
    "petros_exclusion",
    "1mdb_governance_parallel",
    "royal_insulation",
    "venue_shopping",
    "asymmetric_state_participation",
    "mss_concurrent_major_jv",
    "structural_sovereignty_loss",
}


# Fix 7: Capital type calibration table
CAPITAL_TYPE_CALIBRATION: dict[str, dict[str, float]] = {
    "sovereign_capital": {
        "sovereignty_weight": 2.0,
        "capture_threshold": 0.30,
        "dignity_weight": 1.5,
    },
    "financial_capital": {
        "sovereignty_weight": 1.0,
        "capture_threshold": 0.50,
        "dignity_weight": 1.0,
    },
    "human_capital": {
        "sovereignty_weight": 1.5,
        "capture_threshold": 0.40,
        "dignity_weight": 2.0,
    },
    "natural_capital": {
        "sovereignty_weight": 1.5,
        "capture_threshold": 0.35,
        "dignity_weight": 1.5,
    },
    "social_capital": {
        "sovereignty_weight": 1.2,
        "capture_threshold": 0.45,
        "dignity_weight": 1.8,
    },
    "digital_capital": {
        "sovereignty_weight": 1.0,
        "capture_threshold": 0.55,
        "dignity_weight": 0.8,
    },
}


class WitnessState(BaseModel):
    """Witness completeness tracker (Fix 4)."""

    human_witness: bool = False
    ai_witness: bool = False
    earth_witness: bool = False

    @property
    def is_complete(self) -> bool:
        """All three witnesses present = complete."""
        return self.human_witness and self.ai_witness and self.earth_witness

    @property
    def missing_witnesses(self) -> list[str]:
        """Return list of missing witness types."""
        missing = []
        if not self.human_witness:
            missing.append("human")
        if not self.ai_witness:
            missing.append("ai")
        if not self.earth_witness:
            missing.append("earth")
        return missing


class WealthEnvelope(BaseModel, Generic[T]):
    """Standard output envelope for every WEALTH tool."""

    verdict: VerdictLabel
    execution_authorized: ExecutionAuthority = ExecutionAuthority.NONE
    recommendation_only: bool = True
    epistemic_status: str = "DER"  # OBS | DER | INT | SPEC
    data: Optional[T] = None
    lineage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transform_hash: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    risk_floor: str = "F11_AUDIT"
    blast_radius: str = "LOW"
    human_ack_required: bool = False
    notes: str = ""

    # Fix 4: Witness completeness
    witness: WitnessState = Field(default_factory=WitnessState)
    claim_state: ClaimState = ClaimState.SEAL
    requires_888_hold: bool = False

    # Fix 6: Triggered patterns
    triggered_hold_patterns: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _enforce_witness_completeness(self) -> "WealthEnvelope":
        """Fix 4: Incomplete witness → HOLD, never SEAL."""
        if not self.witness.is_complete:
            self.claim_state = ClaimState.HOLD
            self.execution_authorized = ExecutionAuthority.NONE
            self.requires_888_hold = True
            missing = self.witness.missing_witnesses
            self.warnings.append(
                f"Incomplete witness ({', '.join(missing)}) — claim_state set to HOLD"
            )
        return self

    @model_validator(mode="after")
    def _enforce_888_hold_triggers(self) -> "WealthEnvelope":
        """Fix 6: Matched hold patterns → requires_888_hold=True."""
        if self.triggered_hold_patterns:
            self.requires_888_hold = True
            self.claim_state = ClaimState.HOLD
            self.warnings.append(
                f"888_HOLD triggered by patterns: {', '.join(self.triggered_hold_patterns)}"
            )
        return self

    class Config:
        json_encoders = {type(None): lambda v: None}
