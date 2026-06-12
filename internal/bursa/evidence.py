"""
WEALTH Bursa Malaysia — Evidence Card Generator
The EUREKA differentiator: every Bursa stock gets an evidence card
showing not just numbers, but provenance, freshness, confidence, and governance gates.

EUREKA: Free data can produce useful intelligence if you aggressively
        mark delay, provenance, and confidence, and refuse execution-grade claims.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .klse_adapter import KLSEAdapter, get_klse
from .schemas import (
    EpistemicTag,
    EvidenceCard,
    ExecutionGrade,
    ProvenanceBlock,
)


def generate_evidence_card(
    ticker: str,
    adapter: Optional[KLSEAdapter] = None,
) -> EvidenceCard:
    """Generate a full evidence card for a Bursa ticker.

    Gathers quote + fundamentals + intelligence signals into one
    governed evidence document. This is the arifOS moat.
    """
    if adapter is None:
        adapter = get_klse()

    ticker = str(ticker).strip().upper()
    prov = ProvenanceBlock(
        source_provider=adapter.name,
        source_grade=adapter.grade,
        licensed=False,
        execution_grade=ExecutionGrade.SCREENING_ONLY,
        delay_minutes=15,
        venue_code="XKLS",
        confidence_band=0.85,
        epistemic_tag=EpistemicTag.ESTIMATE,
    )

    # Gather data
    quote = adapter.get_quote(ticker)
    fundamentals = adapter.get_fundamentals(ticker)

    # Intelligence signals
    valuation_zone = _compute_valuation_zone(quote, fundamentals)
    quality_score = _compute_quality_score(fundamentals)
    momentum_signal = _compute_momentum(quote)
    liquidity_rating = _compute_liquidity(quote)
    dividend_grade = _compute_dividend_grade(fundamentals)

    # Freshness
    data_freshness_hours = None
    if quote and quote.provenance.as_of_utc:
        try:
            as_of = datetime.fromisoformat(
                quote.provenance.as_of_utc.replace("Z", "+00:00")
            )
            data_freshness_hours = (
                datetime.now(timezone.utc) - as_of
            ).total_seconds() / 3600
        except Exception:
            pass

    # Evidence count
    evidence_count = sum(
        [
            1 if quote else 0,
            1 if fundamentals else 0,
            1 if quote and quote.last_price else 0,
            1 if fundamentals and fundamentals.pe_ratio else 0,
        ]
    )

    # HOLD conditions
    hold_reasons = _check_hold_conditions(quote, fundamentals, data_freshness_hours)

    # Execution allowed?
    execution_allowed = (
        adapter.grade == SourceGrade.LICENSED_REALTIME
        and len(hold_reasons) == 0
        and data_freshness_hours is not None
        and data_freshness_hours < 1.0  # data must be <1h old
    )

    name = ""
    if fundamentals and fundamentals.name:
        name = fundamentals.name
    elif quote and quote.name:
        name = quote.name

    # Adjust confidence based on data completeness
    confidence = 0.85
    if quote and fundamentals:
        confidence = 0.88
    if quote and fundamentals and len(hold_reasons) == 0:
        confidence = 0.90
    prov.confidence_band = confidence
    prov.hold_required = len(hold_reasons) > 0
    prov.warnings = hold_reasons

    return EvidenceCard(
        ticker=ticker,
        name=name,
        quote=quote,
        fundamentals=fundamentals,
        valuation_zone=valuation_zone,
        quality_score=quality_score,
        momentum_signal=momentum_signal,
        liquidity_rating=liquidity_rating,
        dividend_grade=dividend_grade,
        evidence_count=evidence_count,
        data_freshness_hours=data_freshness_hours,
        execution_allowed=execution_allowed,
        hold_reasons=hold_reasons,
        provenance=prov,
    )


# ─── Intelligence Functions ─────────────────────────────────────────────────


def _compute_valuation_zone(quote, fundamentals):
    """Classify valuation: UNDERVALUED / FAIR / OVERVALUED / UNKNOWN."""
    if not fundamentals:
        return "UNKNOWN"
    pe = fundamentals.pe_ratio
    pb = fundamentals.pb_ratio
    roe = fundamentals.roe
    dy = fundamentals.dividend_yield

    # Simple heuristic (free tier logic):
    # - Low PE (<12) + high ROE (>12%) + decent dividend = UNDERVALUED
    # - High PE (>25) or negative earnings = OVERVALUED
    # - Everything else = FAIR
    if pe and pe > 0:
        if pe < 12 and (roe and roe > 12):
            return "UNDERVALUED"
        if pe > 25:
            return "OVERVALUED"
        if dy and dy > 5 and pe < 18:
            return "UNDERVALUED"
        return "FAIR"
    return "UNKNOWN"


def _compute_quality_score(fundamentals) -> Optional[float]:
    """Composite quality score 0-10.

    Components: ROE, margins stability, debt level, dividend consistency.
    Free tier: uses only available fundamentals data.
    """
    if not fundamentals:
        return None
    score = 5.0  # neutral baseline

    # ROE bonus: >15% = strong, >10% = decent, <5% = weak
    roe = fundamentals.roe
    if roe:
        if roe > 15:
            score += 2.0
        elif roe > 10:
            score += 1.0
        elif roe < 5:
            score -= 1.5

    # Dividend bonus: >4% = strong yield
    dy = fundamentals.dividend_yield
    if dy:
        if dy > 4:
            score += 1.5
        elif dy > 2:
            score += 0.5
        elif dy == 0:
            score -= 0.5  # no dividend = less quality for income investors

    # PE reasonability: PE<0 = loss-making, PE>30 = expensive
    pe = fundamentals.pe_ratio
    if pe is not None:
        if pe < 0:
            score -= 2.0
        elif pe > 30:
            score -= 0.5
        elif 10 <= pe <= 20:
            score += 1.0

    # PB for asset-heavy companies
    pb = fundamentals.pb_ratio
    if pb is not None:
        if pb < 0.5:
            score += 0.5  # possibly undervalued assets
        elif pb > 5:
            score -= 0.5  # expensive assets

    return round(max(0.0, min(10.0, score)), 1)


def _compute_momentum(quote) -> str:
    """Simple momentum signal from price change."""
    if not quote or quote.change_pct is None:
        return "NEUTRAL"
    chg = quote.change_pct
    if chg > 3:
        return "BULLISH"
    if chg > 1:
        return "SLIGHTLY_BULLISH"
    if chg < -3:
        return "BEARISH"
    if chg < -1:
        return "SLIGHTLY_BEARISH"
    return "NEUTRAL"


def _compute_liquidity(quote) -> str:
    """Liquidity rating from volume and spread."""
    if not quote:
        return "UNKNOWN"
    volume = quote.volume or 0
    if volume > 10_000_000:
        return "HIGH"
    if volume > 1_000_000:
        return "MEDIUM"
    if volume > 100_000:
        return "LOW"
    if volume > 0:
        return "VERY_LOW"
    return "UNKNOWN"


def _compute_dividend_grade(fundamentals) -> str:
    """Dividend grade from yield and DPS."""
    if not fundamentals:
        return "UNKNOWN"
    dy = fundamentals.dividend_yield
    dps = fundamentals.dps
    if dy is None and dps is None:
        return "UNKNOWN"
    if dy is None:
        return "NONE" if (dps is not None and dps == 0) else "UNKNOWN"
    if dy > 5:
        return "HIGH"
    if dy > 2.5:
        return "MEDIUM"
    if dy > 0:
        return "LOW"
    return "NONE"


def _check_hold_conditions(quote, fundamentals, freshness_hours) -> list:
    """Check 888_HOLD conditions. Returns list of hold reasons."""
    reasons = []

    if not quote and not fundamentals:
        reasons.append("NO_DATA: No quote or fundamentals available for this ticker")
        return reasons

    # Stale data
    if freshness_hours and freshness_hours > 24:
        reasons.append(
            f"STALE_DATA: Data is {freshness_hours:.1f}h old (>24h threshold)"
        )

    # Missing critical fields
    if fundamentals and fundamentals.pe_ratio is None and fundamentals.pb_ratio is None:
        reasons.append("LOW_EVIDENCE: No PE or PB ratio available")

    # Unusual price movement
    if quote and quote.change_pct and abs(quote.change_pct) > 15:
        reasons.append(
            f"EXTREME_MOVE: Price changed {quote.change_pct:.1f}% — verify before acting"
        )

    # Source is not execution-grade
    reasons.append(
        "SOURCE_GRADE: Free delayed data — screening only, not execution-grade"
    )

    return reasons


# Import SourceGrade for hold check
from .schemas import SourceGrade
