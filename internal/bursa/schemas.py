"""
WEALTH Bursa Malaysia — Canonical Schemas (Pydantic v2)
arifOS-aligned: every data point carries provenance, confidence, governance flags.
Free-first, provider-agnostic. Upgrade ports for Morningstar/ICE later.

EUREKA: WEALTH is a capital intelligence organ, not a broker app.
        The moat is judgment, normalization, and evidence discipline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ──────────────────────────────────────────────────────────────────


class SourceGrade(str, Enum):
    """Provenance grade for a data source."""

    LICENSED_REALTIME = "licensed_realtime"  # ICE/Bloomberg-grade
    LICENSED_DELAYED = "licensed_delayed"  # Morningstar, paid but delayed
    FREE_DELAYED = "free_delayed"  # klse-screener-py, ~15min delay
    SCRAPED = "scraped"  # unofficial scraper
    UNKNOWN = "unknown"  # source not verified


class EpistemicTag(str, Enum):
    """arifOS epistemic tag — F2 TRUTH compliance."""

    CLAIM = "CLAIM"
    PLAUSIBLE = "PLAUSIBLE"
    ESTIMATE = "ESTIMATE"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class ExecutionGrade(str, Enum):
    """Can this data be used for real-money decisions?"""

    EXECUTION_SAFE = "execution_safe"  # licensed + fresh + venue verified
    SCREENING_ONLY = "screening_only"  # delayed, good for research
    NON_EXECUTION = "non_execution"  # scraped, informational only
    UNVERIFIED = "unverified"  # not checked yet


class MarketPhase(str, Enum):
    """Bursa Malaysia market phases."""

    PRE_OPEN = "pre_open"
    OPEN = "open"
    LUNCH = "lunch"
    PRE_CLOSE = "pre_close"
    CLOSED = "closed"
    HALTED = "halted"
    UNKNOWN = "unknown"


class Board(str, Enum):
    """Bursa Malaysia listing boards."""

    MAIN = "main_market"
    ACE = "ace_market"
    LEAP = "leap_market"
    UNKNOWN = "unknown"


# ─── Provenance Block (included in every response) ─────────────────────────


class ProvenanceBlock(BaseModel):
    """Canonical provenance metadata — attached to every WEALTH data response."""

    source_provider: str = Field(
        default="klse_screener_py", description="Data provider name"
    )
    source_grade: SourceGrade = Field(default=SourceGrade.FREE_DELAYED)
    licensed: bool = Field(default=False)
    execution_grade: ExecutionGrade = Field(default=ExecutionGrade.SCREENING_ONLY)
    delay_minutes: int = Field(default=15, description="Estimated data delay")
    as_of_exchange: Optional[str] = Field(
        default=None, description="Exchange timestamp"
    )
    as_of_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    venue_code: str = Field(default="XKLS", description="Bursa Malaysia MIC code")
    schema_version: str = Field(default="2026.06.12")
    confidence_band: float = Field(
        default=0.85, ge=0.0, le=1.0, description="0.0-1.0 confidence"
    )
    epistemic_tag: EpistemicTag = Field(default=EpistemicTag.ESTIMATE)
    warnings: List[str] = Field(default_factory=list)
    hold_required: bool = Field(
        default=False, description="888_HOLD gate active if True"
    )


# ─── Instrument Master ─────────────────────────────────────────────────────


class InstrumentMaster(BaseModel):
    """Normalized Bursa instrument identity."""

    ticker: str = Field(..., description="Bursa numeric code or alphabetic ticker")
    name: str = Field(default="", description="Company name")
    isin: Optional[str] = Field(default=None)
    board: Board = Field(default=Board.UNKNOWN)
    sector: Optional[str] = Field(default=None)
    shariah_compliant: Optional[bool] = Field(default=None)
    aliases: List[str] = Field(default_factory=list)
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


# ─── Quote Snapshot ────────────────────────────────────────────────────────


class QuoteSnapshot(BaseModel):
    """Live-delayed Bursa quote snapshot."""

    ticker: str
    name: str = ""
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    value_rm: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_volume: Optional[int] = None
    ask_volume: Optional[int] = None
    market_phase: MarketPhase = MarketPhase.UNKNOWN
    board: Board = Board.UNKNOWN
    sector: Optional[str] = None
    currency: str = "MYR"
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)


# ─── Fundamentals ──────────────────────────────────────────────────────────


class FundamentalsSnapshot(BaseModel):
    """Normalized fundamentals snapshot."""

    ticker: str
    name: str = ""
    # Valuation
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    psr: Optional[float] = None
    eps: Optional[float] = None
    dps: Optional[float] = None
    nta: Optional[float] = None
    # Returns
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    # Size
    market_cap: Optional[float] = None  # in MYR
    shares_outstanding: Optional[float] = None  # in millions
    # Price range
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    # Classification
    sector: Optional[str] = None
    shariah_compliant: Optional[bool] = None
    # Metadata
    latest_quarter: Optional[str] = None
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)


# ─── Price History ─────────────────────────────────────────────────────────


class PriceBar(BaseModel):
    """Single OHLCV bar."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistory(BaseModel):
    """OHLCV price history for a ticker."""

    ticker: str
    period: str = "30d"
    bars: List[PriceBar] = Field(default_factory=list)
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)


# ─── Screen Result ─────────────────────────────────────────────────────────


class ScreenCriteria(BaseModel):
    """Screening filter criteria."""

    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    min_dividend_yield: Optional[float] = None
    min_roe: Optional[float] = None
    max_pb: Optional[float] = None
    min_market_cap_m: Optional[float] = None
    max_market_cap_m: Optional[float] = None
    board: Optional[Board] = None
    sector: Optional[str] = None
    shariah_only: bool = False
    sort_by: str = "pe_ratio"
    limit: int = Field(default=20, ge=1, le=100)


class ScreenMatch(BaseModel):
    """Single screening match."""

    ticker: str
    name: str
    last_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    market_cap: Optional[float] = None
    sector: Optional[str] = None


class ScreenResult(BaseModel):
    """Complete screening result."""

    criteria: ScreenCriteria
    matches: List[ScreenMatch] = Field(default_factory=list)
    total_screened: int = 0
    match_count: int = 0
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)


# ─── Evidence Card — EUREKA differentiation ────────────────────────────────


class EvidenceCard(BaseModel):
    """Evidence card — the EUREKA differentiator.

    Every Bursa stock gets an evidence card that shows not just numbers,
    but where they came from, how fresh they are, and what level of
    trust they warrant. This is the arifOS moat.
    """

    ticker: str
    name: str = ""
    # Snapshot
    quote: Optional[QuoteSnapshot] = None
    fundamentals: Optional[FundamentalsSnapshot] = None
    # Intelligence
    valuation_zone: str = "UNKNOWN"  # UNDERVALUED / FAIR / OVERVALUED / UNKNOWN
    quality_score: Optional[float] = None  # 0-10 composite
    momentum_signal: str = "NEUTRAL"  # BULLISH / BEARISH / NEUTRAL
    liquidity_rating: str = "UNKNOWN"  # HIGH / MEDIUM / LOW / UNKNOWN
    dividend_grade: str = "UNKNOWN"  # HIGH / MEDIUM / LOW / NONE / UNKNOWN
    # Governance
    evidence_count: int = 0  # how many data points back this card
    data_freshness_hours: Optional[float] = None  # hours since last update
    execution_allowed: bool = False  # 888_HOLD gate
    hold_reasons: List[str] = Field(default_factory=list)
    # Metadata
    provenance: ProvenanceBlock = Field(default_factory=ProvenanceBlock)


# ─── Provider Health ───────────────────────────────────────────────────────


class ProviderStatus(BaseModel):
    """Health status of a single data provider."""

    name: str
    grade: SourceGrade
    reachable: bool = False
    last_error: Optional[str] = None
    last_success_utc: Optional[str] = None
    rate_limit_remaining: Optional[int] = None


class ProviderHealth(BaseModel):
    """Aggregate provider health dashboard."""

    providers: List[ProviderStatus] = Field(default_factory=list)
    checked_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    all_reachable: bool = False
