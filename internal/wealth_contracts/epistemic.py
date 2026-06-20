"""
Epistemic Labels for WEALTH outputs.

F2 TRUTH: Every claim must carry an epistemic label.
"""

from enum import Enum
from pydantic import BaseModel


class EpistemicLabel(str, Enum):
    """OBS (Observed) | DER (Derived) | INT (Interpreted) | SPEC (Speculative)."""

    OBS = "OBS"
    DER = "DER"
    INT = "INT"
    SPEC = "SPEC"


class EpistemicStatus(BaseModel):
    """Typed epistemic status attached to a WEALTH output."""

    label: EpistemicLabel
    confidence: float  # 0.0–0.90 (F7 cap)
    source: str  # free-form: "live_api", "cached_2026-06-15", "model_inference", etc.
    age_hours: float = 0.0
    notes: str = ""
