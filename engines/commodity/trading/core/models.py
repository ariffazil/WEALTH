"""
Data models for the trading system.
Pure dataclasses — no business logic, no I/O.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    FLAT = "FLAT"


class SignalStrength(str, Enum):
    STRONG = "STRONG"      # ≥3 confluence factors
    MODERATE = "MODERATE"  # 2 confluence factors
    WEAK = "WEAK"          # 1 factor, needs confirmation
    NONE = "NONE"


class Verdict(str, Enum):
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    BLOCK = "BLOCK"
    SABAR = "SABAR"


class EpistemicLabel(str, Enum):
    OBS = "OBS"       # observed (price, indicator value)
    DER = "DER"       # derived (computed from observations)
    INT = "INT"       # interpreted (pattern recognition)
    SPEC = "SPEC"     # speculative (prediction)


@dataclass
class OHLCV:
    """Single candlestick."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str = "H1"

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def range_size(self) -> float:
        return self.high - self.low

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass
class Indicators:
    """Snapshot of all technical indicators at a point in time."""
    timestamp: datetime
    # EMAs
    ema_20: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    # Momentum
    rsi_14: float = 50.0
    macd_line: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    # Volatility
    atr_14: float = 0.0
    # Structure
    support: float = 0.0
    resistance: float = 0.0
    pivot: float = 0.0
    # Trend
    trend: Direction = Direction.FLAT
    # Epistemic label
    epistemic: EpistemicLabel = EpistemicLabel.DER


@dataclass
class ConfluenceFactor:
    """A single factor contributing to a signal."""
    name: str
    direction: Direction
    weight: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    epistemic: EpistemicLabel = EpistemicLabel.INT
    detail: str = ""


@dataclass
class Signal:
    """A trading signal with full provenance."""
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str = "XAUUSD"
    direction: Direction = Direction.FLAT
    strength: SignalStrength = SignalStrength.NONE
    confidence: float = 0.0
    # Entry / SL / TP
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    # Risk:Reward
    rr_ratio: float = 0.0
    # Confluence
    confluence_factors: list[ConfluenceFactor] = field(default_factory=list)
    confluence_score: float = 0.0
    # Indicators snapshot
    indicators: Optional[Indicators] = None
    # Governance
    verdict: Verdict = Verdict.HOLD
    judge_reason: str = ""
    # Sizing
    suggested_lot: float = 0.0
    risk_amount: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        if self.indicators:
            d["indicators"]["timestamp"] = self.indicators.timestamp.isoformat()
        return d

    def to_alert_text(self, syed_mode: bool = True) -> str:
        """Human-readable alert text. BM if syed_mode."""
        if syed_mode:
            return self._format_syed()
        return self._format_full()

    def _format_syed(self) -> str:
        emoji = "🟢" if self.direction == Direction.BUY else "🔴" if self.direction == Direction.SELL else "⚪"
        conf_pct = int(self.confidence * 100)
        lines = [
            f"{emoji} **XAUUSD {self.direction.value}** — {self.strength.value}",
            f"Entry: **{self.entry_price:.2f}** | SL: **{self.stop_loss:.2f}**",
            f"TP1: **{self.take_profit_1:.2f}** | TP2: **{self.take_profit_2:.2f}**",
            f"RR: **1:{self.rr_ratio:.1f}** | Conf: **{conf_pct}%**",
            f"Lot: **{self.suggested_lot:.2f}** | Risk: **${self.risk_amount:.0f}**",
        ]
        if self.confluence_factors:
            lines.append("Factors:")
            for f in self.confluence_factors[:5]:
                lines.append(f"  • {f.name} ({f.direction.value}, {f.confidence:.0%})")
        if self.verdict != Verdict.PROCEED:
            lines.append(f"⚠️ {self.verdict.value}: {self.judge_reason}")
        return "\n".join(lines)

    def _format_full(self) -> str:
        d = self.to_dict()
        return json.dumps(d, indent=2, default=str)


@dataclass
class Position:
    """An open position."""
    ticket: int = 0
    symbol: str = "XAUUSD"
    direction: Direction = Direction.FLAT
    lot_size: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    open_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pnl: float = 0.0
    signal_id: str = ""  # links back to originating signal


@dataclass
class TradeRecord:
    """Closed trade for journaling and learning."""
    signal_id: str = ""
    symbol: str = "XAUUSD"
    direction: Direction = Direction.FLAT
    lot_size: float = 0.0
    entry_price: float = 0.0
    exit_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    open_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    close_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pnl: float = 0.0
    pnl_pct: float = 0.0
    outcome: str = ""  # "TP_HIT", "SL_HIT", "MANUAL_CLOSE"
    notes: str = ""


@dataclass
class RiskState:
    """Current risk exposure snapshot."""
    equity: float = 0.0
    balance: float = 0.0
    open_positions: int = 0
    daily_pnl: float = 0.0
    daily_pnl_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    can_trade: bool = True
    block_reason: str = ""

    @property
    def daily_loss_remaining(self) -> float:
        """How much more can be lost today before halt."""
        from .config import get_config
        cfg = get_config()
        return max(0, (cfg.max_daily_loss_pct / 100 * self.equity) + self.daily_pnl)
