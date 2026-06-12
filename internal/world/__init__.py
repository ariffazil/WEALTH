"""
WEALTH Global Markets — Free Data Adapter (yfinance)
Wraps yfinance (Apache 2.0 license) for global indices, commodities, FX, crypto.
All data tagged: source_grade=FREE_DELAYED, execution_grade=SCREENING_ONLY.

EUREKA: Global context turns stock analysis into macro-aware intelligence.
        A Bursa stock viewed in isolation is incomplete. Same stock viewed
        against oil, gold, S&P, and ringgit is capital intelligence.

Supported symbols:
  Indices:    ^GSPC (S&P500), ^IXIC (Nasdaq), ^DJI (Dow), ^FTSE, ^N225, ^HSI
  Commodities: GC=F (Gold), CL=F (WTI), BZ=F (Brent), SI=F (Silver), ZC=F (Corn)
  FX:         EURUSD=X, USDMYR=X, USDJPY=X
  Crypto:     BTC-USD, ETH-USD
  Fear:       ^VIX
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..bursa.schemas import (
    EpistemicTag,
    EvidenceCard,
    ExecutionGrade,
    FundamentalsSnapshot,
    PriceBar,
    PriceHistory,
    ProvenanceBlock,
    ProviderHealth,
    ProviderStatus,
    QuoteSnapshot,
    SourceGrade,
)

logger = logging.getLogger("wealth.global.yfinance")

# ─── Symbol Registry ──────────────────────────────────────────────────────

GLOBAL_SYMBOLS: Dict[str, Dict[str, str]] = {
    # Major Indices
    "^GSPC": {"name": "S&P 500", "type": "index", "region": "US"},
    "^IXIC": {"name": "NASDAQ Composite", "type": "index", "region": "US"},
    "^DJI": {"name": "Dow Jones", "type": "index", "region": "US"},
    "^RUT": {"name": "Russell 2000", "type": "index", "region": "US"},
    "^FTSE": {"name": "FTSE 100", "type": "index", "region": "UK"},
    "^N225": {"name": "Nikkei 225", "type": "index", "region": "JP"},
    "^HSI": {"name": "Hang Seng", "type": "index", "region": "HK"},
    "^STI": {"name": "STI (Singapore)", "type": "index", "region": "SG"},
    # Commodities
    "GC=F": {"name": "Gold Futures", "type": "commodity", "region": "GLOBAL"},
    "CL=F": {"name": "WTI Crude Oil", "type": "commodity", "region": "GLOBAL"},
    "BZ=F": {"name": "Brent Crude Oil", "type": "commodity", "region": "GLOBAL"},
    "SI=F": {"name": "Silver Futures", "type": "commodity", "region": "GLOBAL"},
    "ZC=F": {"name": "Corn Futures", "type": "commodity", "region": "GLOBAL"},
    # FX
    "EURUSD=X": {"name": "EUR/USD", "type": "fx", "region": "GLOBAL"},
    "USDMYR=X": {"name": "USD/MYR", "type": "fx", "region": "MY"},
    "USDJPY=X": {"name": "USD/JPY", "type": "fx", "region": "GLOBAL"},
    # Crypto
    "BTC-USD": {"name": "Bitcoin USD", "type": "crypto", "region": "GLOBAL"},
    "ETH-USD": {"name": "Ethereum USD", "type": "crypto", "region": "GLOBAL"},
    # Fear
    "^VIX": {"name": "VIX Volatility", "type": "index", "region": "US"},
}


class YFinanceAdapter:
    """yfinance wrapper — FREE, delayed ~15min, Apache 2.0 license.

    This is the MISKIN-FIRST global data provider. Good enough for
    macro context and screening. Not execution-grade.
    """

    name: str = "yfinance"
    grade: SourceGrade = SourceGrade.FREE_DELAYED

    def __init__(self):
        self._last_error: Optional[str] = None
        self._last_success: Optional[str] = None
        self._reachable: bool = False
        self._init_client()

    def _init_client(self):
        try:
            import yfinance as yf

            self._yf = yf
            self._reachable = True
        except ImportError:
            self._reachable = False
            self._last_error = "yfinance not installed (pip install yfinance)"
            logger.warning(self._last_error)

    def _provenance(self) -> ProvenanceBlock:
        return ProvenanceBlock(
            source_provider=self.name,
            source_grade=self.grade,
            licensed=False,
            execution_grade=ExecutionGrade.SCREENING_ONLY,
            delay_minutes=15,
            venue_code="GLOBAL",
            confidence_band=0.80,
            epistemic_tag=EpistemicTag.ESTIMATE,
            warnings=[
                "Unofficial data source (yfinance). Screening only — not execution-grade."
            ],
        )

    def is_reachable(self) -> bool:
        return self._reachable

    def list_symbols(self) -> List[Dict[str, str]]:
        """List all known global symbols."""
        return [{"symbol": k, **v} for k, v in GLOBAL_SYMBOLS.items()]

    def get_quote(self, symbol: str) -> Optional[QuoteSnapshot]:
        """Get quote snapshot for a global symbol."""
        symbol = (
            symbol.strip().upper() if not symbol.startswith("^") else symbol.strip()
        )
        meta = GLOBAL_SYMBOLS.get(
            symbol, {"name": symbol, "type": "unknown", "region": "UNKNOWN"}
        )

        if not self._reachable:
            return None

        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info or {}

            last_price = (
                info.get("regularMarketPrice")
                or info.get("currentPrice")
                or info.get("previousClose")
            )
            prov = self._provenance()

            self._last_success = datetime.now(timezone.utc).isoformat()
            self._last_error = None

            return QuoteSnapshot(
                ticker=symbol,
                name=meta.get(
                    "name", info.get("shortName", info.get("longName", symbol))
                ),
                last_price=float(last_price) if last_price else None,
                open=float(info.get("regularMarketOpen", 0))
                if info.get("regularMarketOpen")
                else None,
                high=float(info.get("regularMarketDayHigh", 0))
                if info.get("regularMarketDayHigh")
                else None,
                low=float(info.get("regularMarketDayLow", 0))
                if info.get("regularMarketDayLow")
                else None,
                volume=int(info.get("regularMarketVolume", 0))
                if info.get("regularMarketVolume")
                else None,
                sector=meta.get("type", ""),
                currency=info.get("currency", "USD"),
                provenance=prov,
            )

        except Exception as e:
            self._last_error = str(e)
            logger.warning(f"yfinance get_quote failed for {symbol}: {e}")
            return None

    def get_price_history(
        self, symbol: str, period: str = "1mo"
    ) -> Optional[PriceHistory]:
        """Get OHLCV price history."""
        symbol = (
            symbol.strip().upper() if not symbol.startswith("^") else symbol.strip()
        )

        if not self._reachable:
            return None

        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(period=period)

            if df.empty:
                return None

            prov = self._provenance()
            self._last_success = datetime.now(timezone.utc).isoformat()

            bars: List[PriceBar] = []
            for idx, row in df.iterrows():
                bars.append(
                    PriceBar(
                        date=str(idx.date()),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                )

            return PriceHistory(
                ticker=symbol,
                period=period,
                bars=bars,
                provenance=prov,
            )

        except Exception as e:
            self._last_error = str(e)
            return None

    def get_global_dashboard(self) -> List[QuoteSnapshot]:
        """Get all global symbols at once — one multi-symbol query."""
        results: List[QuoteSnapshot] = []
        for symbol in GLOBAL_SYMBOLS:
            q = self.get_quote(symbol)
            if q:
                results.append(q)
        return results

    def health(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            grade=self.grade,
            reachable=self._reachable,
            last_error=self._last_error,
            last_success_utc=self._last_success,
        )


# ─── Singleton ──────────────────────────────────────────────────────────────

_global: Optional[YFinanceAdapter] = None


def get_global() -> YFinanceAdapter:
    global _global
    if _global is None:
        _global = YFinanceAdapter()
    return _global
