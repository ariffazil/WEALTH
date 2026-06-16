"""
WEALTH Lineage — Per-output lineage receipt (OpenLineage-style).

Every WEALTH computation carries:
- source dataset(s)
- as_of_date
- transform hash (the code that produced the output)
- lineage_id (unique per computation)
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel, Field


class WealthLineage(BaseModel):
    """OpenLineage-style lineage for a WEALTH computation."""

    lineage_id: str
    sources: list[str] = Field(default_factory=list)
    transform_path: str  # path to the transform code
    transform_hash: str  # b3: hash of transform source
    as_of_date: Optional[str] = None
    computed_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    license: str = "AGPL-3.0"
    quality_score: float = 1.0
    staleness_hours: float = 0.0
    notes: str = ""
