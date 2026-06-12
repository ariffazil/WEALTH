"""
WEALTH Bursa Malaysia — Capital Intelligence Package
Free-first, arifOS-aligned. klse-screener-py (MIT license) as default provider.
Upgrade ports for Morningstar MCP / ICE Bursa when capital allows.

EUREKA: WEALTH is not a broker app. It is a capital intelligence organ.
        The moat is judgment, normalization, and evidence discipline.

3 public functions exposed for the MCP tool layer:
  - bursa_snapshot(symbol)         → QuoteSnapshot
  - bursa_screen(criteria)         → ScreenResult
  - bursa_evidence(symbol)         → EvidenceCard
"""

from .klse_adapter import KLSEAdapter, get_klse
from .evidence import generate_evidence_card
from .schemas import (
    Board,
    EpistemicTag,
    EvidenceCard,
    ExecutionGrade,
    FundamentalsSnapshot,
    MarketPhase,
    PriceBar,
    PriceHistory,
    ProvenanceBlock,
    ProviderHealth,
    ProviderStatus,
    QuoteSnapshot,
    ScreenCriteria,
    ScreenMatch,
    ScreenResult,
    SourceGrade,
)

__all__ = [
    # Adapter
    "KLSEAdapter",
    "get_klse",
    # Evidence
    "generate_evidence_card",
    # Schemas
    "Board",
    "EpistemicTag",
    "EvidenceCard",
    "ExecutionGrade",
    "FundamentalsSnapshot",
    "MarketPhase",
    "PriceBar",
    "PriceHistory",
    "ProvenanceBlock",
    "ProviderHealth",
    "ProviderStatus",
    "QuoteSnapshot",
    "ScreenCriteria",
    "ScreenMatch",
    "ScreenResult",
    "SourceGrade",
]
