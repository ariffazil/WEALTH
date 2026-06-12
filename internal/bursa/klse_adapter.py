"""
WEALTH Bursa Malaysia — KLSE Screener Adapter (FREE TIER)
Wraps klse-screener-py (MIT license, v3.2.0) as a provider adapter.
All data tagged: source_grade=FREE_DELAYED, execution_grade=SCREENING_ONLY.
Swap to Morningstar/ICE adapter later by implementing the same interface.

EUREKA: Free data can produce useful intelligence if you aggressively
        mark delay, provenance, and confidence.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    Board,
    EpistemicTag,
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

logger = logging.getLogger("wealth.bursa.klse")

# ─── Adapter Interface (implement this for Morningstar/ICE later) ──────────


class BursaProvider:
    """Abstract Bursa Malaysia data provider interface.

    Implement this for each provider: KLSE Screener (free), Morningstar, ICE.
    """

    name: str = "base"
    grade: SourceGrade = SourceGrade.UNKNOWN

    def is_reachable(self) -> bool:
        raise NotImplementedError

    def get_quote(self, ticker: str) -> Optional[QuoteSnapshot]:
        raise NotImplementedError

    def get_fundamentals(self, ticker: str) -> Optional[FundamentalsSnapshot]:
        raise NotImplementedError

    def get_price_history(
        self, ticker: str, period: str = "30d"
    ) -> Optional[PriceHistory]:
        raise NotImplementedError

    def screen(self, criteria: ScreenCriteria) -> ScreenResult:
        raise NotImplementedError

    def health(self) -> ProviderStatus:
        raise NotImplementedError


# ─── KLSE Screener Adapter ─────────────────────────────────────────────────


class KLSEAdapter(BursaProvider):
    """klse-screener-py adapter — FREE, delayed ~15min, MIT license.

    This is the MISKIN-FIRST provider. Zero cost, good enough for screening.
    Upgrade to Morningstar/ICE when you have capital.
    """

    name: str = "klse_screener_py"
    grade: SourceGrade = SourceGrade.FREE_DELAYED

    def __init__(self):
        self._last_error: Optional[str] = None
        self._last_success: Optional[str] = None
        self._reachable: bool = False
        self._init_client()

    def _init_client(self):
        """Lazy-init the klse_screener client."""
        try:
            import klse_screener

            self._client = klse_screener
            self._reachable = True
        except ImportError:
            self._reachable = False
            self._last_error = (
                "klse-screener-py not installed (pip install klse-screener-py)"
            )
            logger.warning(self._last_error)

    def _provenance(self) -> ProvenanceBlock:
        """Build standard provenance block for this provider."""
        return ProvenanceBlock(
            source_provider=self.name,
            source_grade=self.grade,
            licensed=False,
            execution_grade=ExecutionGrade.SCREENING_ONLY,
            delay_minutes=15,
            venue_code="XKLS",
            confidence_band=0.85,
            epistemic_tag=EpistemicTag.ESTIMATE,
        )

    def _checked(self):
        """Mark successful call."""
        self._last_success = datetime.now(timezone.utc).isoformat()
        self._last_error = None

    def _errored(self, err: str):
        """Mark failed call."""
        self._last_error = err
        logger.warning(f"KLSE adapter error: {err}")

    def is_reachable(self) -> bool:
        return self._reachable

    # ─── Quote Snapshot ──────────────────────────────────────────────────

    def get_quote(self, ticker: str) -> Optional[QuoteSnapshot]:
        """Get live-delayed quote for a Bursa ticker.

        Uses get_klse_intraday_stats() for price/volume data
        plus get_klse_fundamentals() for name/sector enrichment.
        """
        ticker = str(ticker).strip().upper()
        if not self._reachable:
            return None

        try:
            # Intraday stats: open, high, low, bid, ask, volume
            stats = self._client.get_klse_intraday_stats(ticker)
            # Fundamentals: name, sector, pe, market_cap for enrichment
            fund = self._client.get_klse_fundamentals(ticker) or {}

            if not stats:
                self._errored(f"No intraday stats for {ticker}")
                return None

            # klse_screener intraday stats don't expose last_price.
            # Use best available: open price (during market) or high/low midpoint.
            last_price = None
            if stats.get("open"):
                last_price = float(stats["open"])
            elif stats.get("high") and stats.get("low"):
                last_price = round((float(stats["high"]) + float(stats["low"])) / 2, 3)

            change = None
            change_pct = None

            self._checked()
            prov = self._provenance()
            prov.as_of_exchange = str(stats.get("last_updated", "")) or None

            return QuoteSnapshot(
                ticker=ticker,
                name=str(fund.get("name", "")),
                last_price=last_price,
                change=change,
                change_pct=change_pct,
                open=float(stats.get("open", 0)) if stats.get("open") else None,
                high=float(stats.get("high", 0)) if stats.get("high") else None,
                low=float(stats.get("low", 0)) if stats.get("low") else None,
                volume=int(stats.get("volume", 0)) if stats.get("volume") else None,
                bid=float(stats.get("bid_price", 0))
                if stats.get("bid_price")
                else None,
                ask=float(stats.get("ask_price", 0))
                if stats.get("ask_price")
                else None,
                bid_volume=int(stats.get("bid_volume", 0))
                if stats.get("bid_volume")
                else None,
                ask_volume=int(stats.get("ask_volume", 0))
                if stats.get("ask_volume")
                else None,
                sector=str(fund.get("sector", "")),
                market_phase=MarketPhase.OPEN,  # if we got data, market is open
                provenance=prov,
            )

        except Exception as e:
            self._errored(str(e))
            return None

    # ─── Fundamentals ────────────────────────────────────────────────────

    def get_fundamentals(self, ticker: str) -> Optional[FundamentalsSnapshot]:
        """Get fundamentals snapshot for a Bursa ticker."""
        ticker = str(ticker).strip().upper()
        if not self._reachable:
            return None

        try:
            data = self._client.get_klse_fundamentals(ticker)
            if not data:
                self._errored(f"No fundamentals for {ticker}")
                return None

            self._checked()
            prov = self._provenance()
            prov.confidence_band = 0.80  # slightly lower for fundamentals

            # Parse 52-week range: "1.20 - 2.50"
            w52_high, w52_low = None, None
            w52_range = str(data.get("fifty_two_week_range", ""))
            if " - " in w52_range:
                parts = w52_range.split(" - ")
                try:
                    w52_low = float(parts[0].strip())
                    w52_high = float(parts[1].strip())
                except ValueError:
                    pass

            return FundamentalsSnapshot(
                ticker=ticker,
                name=str(data.get("name", "")),
                pe_ratio=_safe_float(data.get("pe_ratio")),
                pb_ratio=_safe_float(data.get("pb_ratio")),
                psr=_safe_float(data.get("psr")),
                eps=_safe_float(data.get("eps")),
                dps=_safe_float(data.get("dps")),
                nta=_safe_float(data.get("nta")),
                dividend_yield=_safe_float(data.get("dividend_yield")),
                roe=_safe_float(data.get("roe")),
                market_cap=_safe_float(data.get("market_cap")),
                week_52_high=w52_high,
                week_52_low=w52_low,
                sector=str(data.get("sector", "")),
                latest_quarter=str(data.get("latest_quarter", "")),
                provenance=prov,
            )

        except Exception as e:
            self._errored(str(e))
            return None

    # ─── Price History ───────────────────────────────────────────────────

    def get_price_history(
        self, ticker: str, period: str = "30d"
    ) -> Optional[PriceHistory]:
        """Get OHLCV price history.

        Valid periods: 30d, 3m, 6m, 1y, 3y, 5y, 10y
        """
        ticker = str(ticker).strip().upper()
        if not self._reachable:
            return None

        try:
            data = self._client.get_klse_price_history(ticker, period)
            if not data or not isinstance(data, dict):
                self._errored(f"No price history for {ticker} period={period}")
                return None

            self._checked()
            prov = self._provenance()

            bars: List[PriceBar] = []
            # Response format: {dates: [...], open: [...], high: [...], low: [...], close: [...], volume: [...]}
            dates = data.get("dates") or data.get("date") or []
            opens = data.get("open") or []
            highs = data.get("high") or []
            lows = data.get("low") or []
            closes = data.get("close") or []
            volumes = data.get("volume") or []

            for i in range(min(len(dates), len(opens))):
                try:
                    bars.append(
                        PriceBar(
                            date=str(dates[i]),
                            open=float(opens[i]),
                            high=float(highs[i]) if i < len(highs) else float(opens[i]),
                            low=float(lows[i]) if i < len(lows) else float(opens[i]),
                            close=float(closes[i])
                            if i < len(closes)
                            else float(opens[i]),
                            volume=int(volumes[i]) if i < len(volumes) else 0,
                        )
                    )
                except (ValueError, TypeError):
                    continue

            return PriceHistory(
                ticker=ticker,
                period=period,
                bars=bars,
                provenance=prov,
            )

        except Exception as e:
            self._errored(str(e))
            return None

    # ─── Screening ───────────────────────────────────────────────────────

    def screen(self, criteria: ScreenCriteria) -> ScreenResult:
        """Screen Bursa stocks by fundamentals criteria.

        Currently screens fundamentals for popular KLSE stocks.
        Full sector-wide screening requires iterating all stocks — SLOW.
        For now, screens a curated list of ~50 major Bursa counters.
        """
        if not self._reachable:
            return ScreenResult(
                criteria=criteria,
                provenance=self._provenance(),
            )

        # Curated list of major Bursa tickers — only verified-working tickers.
        # klse_screener times out ~30s on invalid tickers, so keep this tight.
        MAJOR_TICKERS = [
            "1155",
            "1295",
            "3182",
            "4197",  # banks: MAYBANK, PBBANK, GENTING, SIME
            "5183",
            "5681",
            "6033",  # oil/gas: PETRONAS, PETDAG, PENERGY
            "6947",
            "7113",
            "7277",  # tech: DIALOG, TOPGLOV, KOSSAN
        ]

        matches: List[ScreenMatch] = []
        total = 0

        for ticker in MAJOR_TICKERS:
            total += 1
            try:
                fund = self._client.get_klse_fundamentals(ticker)
                if not fund:
                    continue

                name = str(fund.get("name", ""))
                pe = _safe_float(fund.get("pe_ratio"))
                pb = _safe_float(fund.get("pb_ratio"))
                dy = _safe_float(fund.get("dividend_yield"))
                roe = _safe_float(fund.get("roe"))
                mcap = _safe_float(fund.get("market_cap"))
                sector = str(fund.get("sector", ""))

                # Apply filters
                if criteria.min_pe and (pe is None or pe < criteria.min_pe):
                    continue
                if criteria.max_pe and (pe is None or pe > criteria.max_pe):
                    continue
                if criteria.min_dividend_yield and (
                    dy is None or dy < criteria.min_dividend_yield
                ):
                    continue
                if criteria.min_roe and (roe is None or roe < criteria.min_roe):
                    continue
                if criteria.max_pb and (pb is None or pb > criteria.max_pb):
                    continue
                if criteria.min_market_cap_m and (
                    mcap is None or mcap < criteria.min_market_cap_m * 1_000_000
                ):
                    continue
                if criteria.max_market_cap_m and (
                    mcap is None or mcap > criteria.max_market_cap_m * 1_000_000
                ):
                    continue
                if criteria.board and criteria.board != Board.UNKNOWN:
                    continue  # klse-screener doesn't expose board cleanly
                if criteria.sector and criteria.sector.lower() not in sector.lower():
                    continue

                # Get last price from intraday (skip if slow — screen uses fundamentals)
                last_price = None
                try:
                    stats = self._client.get_klse_intraday_stats(ticker)
                    if stats:
                        last_price = (
                            float(stats.get("open", 0)) if stats.get("open") else None
                        )
                except Exception:
                    pass

                matches.append(
                    ScreenMatch(
                        ticker=ticker,
                        name=name,
                        last_price=last_price,
                        pe_ratio=pe,
                        pb_ratio=pb,
                        dividend_yield=dy,
                        roe=roe,
                        market_cap=mcap,
                        sector=sector,
                    )
                )

                # Early exit: stop if we have enough matches
                if len(matches) >= criteria.limit:
                    break

            except Exception:
                continue

        # Sort
        reverse = False  # Ascending by default (lower PE = better value)
        sort_key = criteria.sort_by
        matches.sort(
            key=lambda m: _sort_val(m, sort_key),
            reverse=reverse,
        )
        matches = matches[: criteria.limit]

        self._checked()
        prov = self._provenance()
        prov.warnings.append(
            f"Screen limited to {len(MAJOR_TICKERS)} major tickers. Full Bursa screening needs licensed data."
        )
        prov.hold_required = False

        return ScreenResult(
            criteria=criteria,
            matches=matches,
            total_screened=total,
            match_count=len(matches),
            provenance=prov,
        )

    # ─── Health ──────────────────────────────────────────────────────────

    def health(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            grade=self.grade,
            reachable=self._reachable,
            last_error=self._last_error,
            last_success_utc=self._last_success,
        )


# ─── Helpers ────────────────────────────────────────────────────────────────


def _safe_float(val: Any) -> Optional[float]:
    """Safely convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _sort_val(match: ScreenMatch, key: str) -> Any:
    """Get sort value, pushing None to the end."""
    val = getattr(match, key, None)
    if val is None:
        return float("inf")
    return val


# ─── Singleton ──────────────────────────────────────────────────────────────

_klse: Optional[KLSEAdapter] = None


def get_klse() -> KLSEAdapter:
    """Get or create the singleton KLSE adapter."""
    global _klse
    if _klse is None:
        _klse = KLSEAdapter()
    return _klse
