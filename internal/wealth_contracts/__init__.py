"""
WEALTH Contracts — Typed output envelopes for every WEALTH tool.

Per executive verdict Phase 1: "Add Pydantic output envelopes for all WEALTH tools."

Constitutional binding:
- F2 TRUTH: Every output carries epistemic label (OBS/DER/INT/SPEC)
- F11 AUDIT: Every output carries lineage_id + transform_hash
- F13 SOVEREIGN: verdict includes execution_authorized=False (WEALTH is EVIDENCE_ONLY)
"""

from .envelopes import WealthEnvelope, VerdictLabel, ExecutionAuthority
from .epistemic import EpistemicLabel, EpistemicStatus
from .lineage import WealthLineage
from .verdicts import WealthVerdict, StockVerdict, ConservationVerdict
from .units import Money, Unit, Currency, decimal_safe, format_myr, format_usd
from .money import round_money, myr_to_usd, usd_to_myr

__all__ = [
    "WealthEnvelope",
    "VerdictLabel",
    "ExecutionAuthority",
    "EpistemicLabel",
    "EpistemicStatus",
    "WealthLineage",
    "WealthVerdict",
    "StockVerdict",
    "ConservationVerdict",
    "Money",
    "Unit",
    "Currency",
    "decimal_safe",
    "format_myr",
    "format_usd",
    "round_money",
    "myr_to_usd",
    "usd_to_myr",
]
