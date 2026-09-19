"""Trading instrument registry — per-instrument config for 5 markets.

Single SOT for scanner, regime, cron, and confluence scorer.
Per CHRON×WEALTH×HERMES synthesis 2026-09-18, KLCI + GAS were not in
scanner.py. This module adds them with instrument-specific config
(volatility class, ATR multiplier, trading session).

DITEMPA BUKAN DIBERI ⚒️
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InstrumentClass(str, Enum):
    METAL = "metal"
    ENERGY = "energy"
    EQUITY_INDEX = "equity_index"
    FX = "fx"


class VolatilityClass(str, Enum):
    """Atypical daily-range bucket — drives ATR multiplier + position size."""

    VERY_LOW = "very_low"  # < 0.3% daily range (e.g. USDMYR)
    LOW = "low"  # 0.3-0.8% daily range (e.g. KLCI, major FX)
    MEDIUM = "medium"  # 0.8-2% daily range (e.g. XAUUSD)
    HIGH = "high"  # > 2% daily range (e.g. NG=F, crypto)
    EXTREME = "extreme"  # > 5% daily range (very rare)


class TradingSession(str, Enum):
    """When the instrument is liquid. Drives scan-hours in cron."""

    ASIA = "asia"  # 00:00-08:00 UTC (08:00-16:00 MYT)
    LONDON = "london"  # 08:00-13:00 UTC
    NY = "ny"  # 13:00-20:00 UTC
    CONTINUOUS = "continuous"  # 24h (most futures, FX)


@dataclass(frozen=True)
class InstrumentConfig:
    """Single instrument config — what the scanner needs to know."""

    symbol: str  # Display symbol (XAUUSD, OIL, GAS, KLCI, USMYR)
    yfinance_ticker: str  # yfinance symbol (GC=F, CL=F, NG=F, ^KLSE, MYR=X)
    instrument_class: InstrumentClass
    volatility_class: VolatilityClass
    session: TradingSession
    decimal_places: int = 2  # Price display precision
    atr_stop_multiplier: float = 2.0  # Stop = entry ± ATR × this
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    atr_period: int = 14
    rsi_period: int = 14
    description: str = ""
    notes: str = ""


# ── Canonical registry ────────────────────────────────────────

INSTRUMENTS: dict[str, InstrumentConfig] = {
    "XAUUSD": InstrumentConfig(
        symbol="XAUUSD",
        yfinance_ticker="GC=F",
        instrument_class=InstrumentClass.METAL,
        volatility_class=VolatilityClass.MEDIUM,
        session=TradingSession.CONTINUOUS,
        decimal_places=2,
        atr_stop_multiplier=2.0,
        description="Gold Futures (USD/oz). Most developed instrument in federation.",
        notes="Continuous session; ~0.8-1.5% daily range; existing scanner tests in scanner.py.",
    ),
    "OIL": InstrumentConfig(
        symbol="OIL",
        yfinance_ticker="CL=F",
        instrument_class=InstrumentClass.ENERGY,
        volatility_class=VolatilityClass.MEDIUM,
        session=TradingSession.CONTINUOUS,
        decimal_places=2,
        atr_stop_multiplier=2.5,
        description="WTI Crude Futures (USD/bbl). Master signal for MYR + KLCI via Petronas.",
        notes="Continuous; ~1-2% daily range; macro-sensitive (OPEC, DXY).",
    ),
    "GAS": InstrumentConfig(
        symbol="GAS",
        yfinance_ticker="NG=F",
        instrument_class=InstrumentClass.ENERGY,
        volatility_class=VolatilityClass.HIGH,
        session=TradingSession.CONTINUOUS,
        decimal_places=3,
        atr_stop_multiplier=3.0,  # wider stop for high-vol
        description="Natural Gas Futures (USD/MMBtu). JCC-linked to Petronas LNG.",
        notes="Continuous but low-volume outside EIA storage Thu 10:30 ET; ~2-4% daily range; wider stops mandatory.",
    ),
    "KLCI": InstrumentConfig(
        symbol="KLCI",
        yfinance_ticker="^KLSE",
        instrument_class=InstrumentClass.EQUITY_INDEX,
        volatility_class=VolatilityClass.LOW,
        session=TradingSession.ASIA,
        decimal_places=2,
        atr_stop_multiplier=1.5,  # tighter stop, low-vol index
        description="FTSE Bursa Malaysia KLCI — Malaysian sovereign equity index.",
        notes="Asia session only (09:00-17:00 MYT); weekend gap risk; ~0.3-0.7% daily range; MYR-translation matters for foreign flows.",
    ),
    "USMYR": InstrumentConfig(
        symbol="USMYR",
        yfinance_ticker="MYR=X",
        instrument_class=InstrumentClass.FX,
        volatility_class=VolatilityClass.VERY_LOW,
        session=TradingSession.CONTINUOUS,
        decimal_places=4,
        atr_stop_multiplier=1.5,
        description="USD/MYR — Petronas-derivative FX pair.",
        notes="Continuous (24h FX); ~0.1-0.3% daily range; macro-driven (oil, OPR, Fed); expressed 4dp.",
    ),
}


def get(symbol: str) -> InstrumentConfig:
    """Lookup instrument config by symbol."""
    sym = symbol.upper()
    if sym not in INSTRUMENTS:
        raise ValueError(
            f"Unknown instrument: {symbol}. Known: {list(INSTRUMENTS.keys())}"
        )
    return INSTRUMENTS[sym]


def all_symbols() -> list[str]:
    return list(INSTRUMENTS.keys())


def is_valid(symbol: str) -> bool:
    return symbol.upper() in INSTRUMENTS


def by_class(instrument_class: InstrumentClass) -> list[str]:
    return [
        s for s, cfg in INSTRUMENTS.items() if cfg.instrument_class == instrument_class
    ]


# ── Mapping shared with chron_price_predictions.py ────────────
# Keep these in sync (chron uses different code path but same SOT).

INSTRUMENT_TICKERS_SHARED = {s: cfg.yfinance_ticker for s, cfg in INSTRUMENTS.items()}
