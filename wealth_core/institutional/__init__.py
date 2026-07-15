"""
WEALTH Core — Institutional Stress Detection.

Detects the "institutional collapse spiral" pattern:
  financial stress → rightsizing → governance erosion →
  intelligence compromise → external exploitation →
  more financial stress → spiral.

Four engines:
  - stress_index: composite 0-1 stress score
  - cascade: temporal feedback loop detector
  - governance: board capacity vs stress level
  - exploitation: counterparty behavior pattern matcher

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from .stress_index import compute_stress_index
from .cascade import compute_cascade
from .governance import compute_governance_capacity
from .exploitation import compute_exploitation

__all__ = [
    "compute_stress_index",
    "compute_cascade",
    "compute_governance_capacity",
    "compute_exploitation",
]
