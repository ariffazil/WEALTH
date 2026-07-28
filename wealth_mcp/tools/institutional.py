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
    """Register all 4 institutional stress detection tools."""

    # ── 1. wealth_institutional_stress_index ────────────────────────────
    @mcp.tool(
        name="wealth_institutional_stress_index",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_institutional_stress_index(
        org_name: str,
        financial_signals: dict,
        governance_signals: dict,
        workforce_signals: dict,
        legal_signals: dict,
        exploitation_signals: dict,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """
        Composite institutional stress index (0-1).

        Connects financial, governance, workforce, legal, and external
        exploitation signals into a single stress score. Detects feedback
        loops (the "institutional collapse spiral").

        Inputs:
          - org_name: organization name (e.g., "PETRONAS")
          - financial_signals: profit_change_pct, revenue_change_pct, cost_cutting_announced
          - governance_signals: board_size, board_resignations_12m, company_secretaries_as_directors, avg_tenure_years
          - workforce_signals: rightsizing_pct, voluntary_exits_pct, key_personnel_departures
          - legal_signals: active_litigation_count, injunction_value_musd, regulatory_uncertainty_score
          - exploitation_signals: counterparty_payment_freeze, interpleader_filed, competing_claims

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_stress_index(
            org_name=org_name,
            financial_signals=financial_signals,
            governance_signals=governance_signals,
            workforce_signals=workforce_signals,
            legal_signals=legal_signals,
            exploitation_signals=exploitation_signals,
        )

        return wrap_result(
            tool_name="wealth_institutional_stress_index",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "financial_signals_OBS",
                "governance_signals_OBS",
                "workforce_signals_OBS",
                "legal_signals_OBS",
                "exploitation_signals_DER",
            ],
        )

    # ── 2. wealth_cascade_model ─────────────────────────────────────────
    @mcp.tool(
        name="wealth_cascade_model",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_cascade_model(
        timeline: list,
        intervention_scenario: dict | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """
        Model feedback loops between institutional stress dimensions.

        Detects spiral vs linear decline vs recovery. Projects trajectory
        and optionally simulates intervention impact.

        Inputs:
          - timeline: list of dicts with {period, financial_stress, governance_capacity,
            workforce_stability, legal_exposure, external_exploitation}
          - intervention_scenario: optional dict (e.g., {"action": "rightsizing_pause", "period": 3})

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_cascade(
            timeline=timeline,
            intervention_scenario=intervention_scenario,
        )

        return wrap_result(
            tool_name="wealth_cascade_model",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["temporal_pattern_analysis_INT"],
        )

    # ── 3. wealth_governance_capacity ───────────────────────────────────
    @mcp.tool(
        name="wealth_governance_capacity",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_governance_capacity(
        board_members: list,
        committees: list,
        stress_level: float,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """
        Monitor board governance capacity relative to stress level.

        Analyzes board composition, committee structure, and identifies
        governance gaps that could enable institutional collapse.

        Inputs:
          - board_members: list of {name, role, appointed_date, type}
          - committees: list of {name, members, meets_quarterly}
          - stress_level: float 0-1 (from wealth_institutional_stress_index)

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_governance_capacity(
            board_members=board_members,
            committees=committees,
            stress_level=stress_level,
        )

        return wrap_result(
            tool_name="wealth_governance_capacity",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "board_filings_OBS",
                "committee_structure_OBS",
                "governance_analysis_DER",
            ],
        )

    # ── 4. wealth_external_exploitation_detect ──────────────────────────
    @mcp.tool(
        name="wealth_external_exploitation_detect",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "ΔG Governance",
        },
    )
    async def wealth_external_exploitation_detect(
        counterparty_actions: list,
        institution_state: dict,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """
        Detect "simulative neutral" counterparty behavior.

        Identifies rational exploitation of institutional weakness —
        where each action is individually defensible but the aggregate
        pattern reveals systematic extraction.

        Inputs:
          - counterparty_actions: list of {action, date, claimed_rationale, actual_benefit_musd}
          - institution_state: dict with stress_index, governance_capacity

        WEALTH computes. arifOS judges. Arif decides.
        """
        result = compute_exploitation(
            counterparty_actions=counterparty_actions,
            institution_state=institution_state,
        )

        return wrap_result(
            tool_name="wealth_external_exploitation_detect",
            domain="institutional",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                "counterparty_actions_OBS",
                "behavioral_pattern_DER",
                "institutional_state_DER",
            ],
        )

    # ── 5. wealth_bid_surface ────────────────────────────────────────────
    @mcp.tool(
        name="wealth_bid_surface",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "apex_primitive": "EMV Bid Surface",
        },
    )
    async def wealth_bid_surface(
        bids: list = None,
        reserve_price: float = 0.0,
        mode: str = "first_price",
        scoring_weights: dict | None = None,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """Score a competitive bid surface for resource allocation."""
        from wealth_mcp.tools.bid_surface import compute_bid_surface

        result = compute_bid_surface(
            bids=bids or [],
            reserve_price=reserve_price,
            mode=mode,
            scoring_weights=scoring_weights,
        )

        return wrap_result(
            tool_name="wealth_bid_surface",
            domain="risk",
            result=result,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["bid_surface_model"],
            session_id=session_id,
            actor_id=actor_id,
        )
