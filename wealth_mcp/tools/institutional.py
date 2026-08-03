"""
WEALTH MCP — Institutional Stress Detection Tools.

Four tools detecting the "institutional collapse spiral":
  financial stress → rightsizing → governance erosion →
  intelligence compromise → external exploitation →
  more financial stress → spiral.

All outputs wrapped in WealthEnvelope with epistemic tags:
  - Financial signals = OBS (when from real data)
  - Governance signals = OBS (when from filings)
  - Exploitation score = DER (derived from behavioral pattern matching)
  - Cascade detection = INT (interpreted from temporal patterns)

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import sys
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Ensure parent in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from wealth_contracts.envelope import wrap_result, WEALTH_OUTPUT_SCHEMA
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_core.institutional.stress_index import compute_stress_index
from wealth_core.institutional.cascade import compute_cascade
from wealth_core.institutional.governance import compute_governance_capacity
from wealth_core.institutional.exploitation import compute_exploitation


def register_institutional_tools(mcp: FastMCP) -> None:
    """Zen Phase 1: shadow tools removed — all access via capital_diagnose(mode=...).

    The 5 tools below were shadow duplicates of capital_diagnose modes:
      - wealth_institutional_stress_index  → capital_diagnose(mode="stress_index")
      - wealth_cascade_model              → capital_diagnose(mode="cascade_model")
      - wealth_governance_capacity        → capital_diagnose(mode="governance_capacity")
      - wealth_external_exploitation_detect → capital_diagnose(mode="exploitation_detect")
      - wealth_bid_surface                → capital_diagnose(mode="bid_surface")

    Parity proven 2026-08-03: all 5 modes return identical result blocks from both paths.
    Engines preserved. Only the duplicate MCP registrations removed.

    DITEMPA BUKAN DIBERI — one capability, one door.
    """
    # No tools to register — all institutional access is through capital_diagnose.
