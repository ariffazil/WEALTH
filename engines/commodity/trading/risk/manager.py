"""
Risk Manager — drawdown protection, daily limits, position limits.
The safety cage. No trade passes without this gate.
"""
from __future__ import annotations

from datetime import datetime, timezone, date
from typing import Optional

from ..core.config import get_config, TradingConfig
from ..core.models import RiskState, Position, Direction, Verdict


class RiskManager:
    """
    Stateful risk manager.
    Tracks equity, daily P&L, drawdown, and position limits.
    """

    def __init__(self, cfg: Optional[TradingConfig] = None):
        self.cfg = cfg or get_config()
        self._initial_equity: float = self.cfg.syed_balance_estimate
        self._peak_equity: float = self._initial_equity
        self._daily_pnl: float = 0.0
        self._daily_date: date = datetime.now(timezone.utc).date()
        self._positions: list[Position] = []
        self._trade_history: list[dict] = []

    def update_equity(self, equity: float) -> None:
        """Update current equity and peak tracking."""
        today = datetime.now(timezone.utc).date()
        if today != self._daily_date:
            # New day — reset daily P&L
            self._daily_pnl = 0.0
            self._daily_date = today

        if equity > self._peak_equity:
            self._peak_equity = equity

    def record_trade_pnl(self, pnl: float) -> None:
        """Record a closed trade's P&L."""
        self._daily_pnl += pnl
        self._trade_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pnl": pnl,
            "daily_pnl": self._daily_pnl,
        })

    def get_state(self, equity: Optional[float] = None) -> RiskState:
        """Get current risk state snapshot."""
        if equity is None:
            equity = self._initial_equity

        self.update_equity(equity)

        drawdown_pct = 0.0
        if self._peak_equity > 0:
            drawdown_pct = ((self._peak_equity - equity) / self._peak_equity) * 100

        daily_pnl_pct = 0.0
        if equity > 0:
            daily_pnl_pct = (self._daily_pnl / equity) * 100

        state = RiskState(
            equity=equity,
            balance=equity,
            open_positions=len(self._positions),
            daily_pnl=self._daily_pnl,
            daily_pnl_pct=round(daily_pnl_pct, 2),
            max_drawdown_pct=round(drawdown_pct, 2),
            current_drawdown_pct=round(drawdown_pct, 2),
            can_trade=True,
            block_reason="",
        )

        # Check all gates
        block = self._check_gates(state)
        if block:
            state.can_trade = False
            state.block_reason = block

        return state

    def _check_gates(self, state: RiskState) -> Optional[str]:
        """Check all risk gates. Returns block reason or None."""

        # Gate 1: Daily loss limit
        if state.daily_pnl_pct <= -self.cfg.max_daily_loss_pct:
            return f"DAILY_LOSS_LIMIT: {state.daily_pnl_pct:.1f}% <= -{self.cfg.max_daily_loss_pct}%"

        # Gate 2: Max drawdown
        if state.current_drawdown_pct >= self.cfg.max_drawdown_pct:
            return f"MAX_DRAWDOWN: {state.current_drawdown_pct:.1f}% >= {self.cfg.max_drawdown_pct}%"

        # Gate 3: Max open positions
        if state.open_positions >= self.cfg.max_open_positions:
            return f"MAX_POSITIONS: {state.open_positions} >= {self.cfg.max_open_positions}"

        return None

    def can_open_position(self, direction: Direction, equity: Optional[float] = None) -> tuple[bool, str]:
        """
        Check if a new position can be opened.
        Returns (allowed, reason).
        """
        state = self.get_state(equity)

        if not state.can_trade:
            return False, state.block_reason

        # Check for opposing positions
        opposing = [p for p in self._positions if p.direction != direction and p.direction != Direction.FLAT]
        if len(opposing) >= 2:
            return False, f"OPPOSING_POSITIONS: {len(opposing)} opposing positions open"

        return True, "OK"

    def register_position(self, position: Position) -> None:
        """Track an opened position."""
        self._positions.append(position)

    def close_position(self, ticket: int, pnl: float) -> None:
        """Remove a closed position and record P&L."""
        self._positions = [p for p in self._positions if p.ticket != ticket]
        self.record_trade_pnl(pnl)

    @property
    def position_count(self) -> int:
        return len(self._positions)

    @property
    def positions(self) -> list[Position]:
        return list(self._positions)
