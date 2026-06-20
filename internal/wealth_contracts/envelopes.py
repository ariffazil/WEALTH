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
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

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

    class Config:
        json_encoders = {type(None): lambda v: None}
