"""
WEALTH Verdicts — Typed verdict schemas for stock + conservation + game outputs.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StockVerdict(str, Enum):
    """Stock analysis verdicts (D4 mode)."""

    SAFE_TO_STUDY = "SAFE_TO_STUDY"
    NEEDS_DATA = "NEEDS_DATA"
    UNSAFE = "UNSAFE"
    HOLD_888 = "888_HOLD"
    MATH_ERROR = "MATH_ERROR"


class ConservationVerdict(str, Enum):
    """Conservation / flow / entropy verdicts."""

    SEAL = "SEAL"  # Mass/energy conserved
    SABAR = "SABAR"  # Within tolerance
    HOLD = "HOLD"  # Investigation needed
    VOID = "VOID"  # Conservation violated


class WealthVerdict(BaseModel):
    """Generic WEALTH verdict envelope."""

    verdict: str  # one of the enum values
    confidence: float = 0.0  # 0.0–0.90
    reason: str
    evidence: dict = Field(default_factory=dict)
    witness_id: str = "WEALTH"
    floor_compliance: list[str] = Field(default_factory=lambda: ["F2_TRUTH", "F11_AUDIT"])
    human_ack_required: bool = False
    timestamp: str = ""
