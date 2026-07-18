"""
Position Sizing — Kelly Criterion + risk-based sizing.
Pure computation. WEALTH computes, arifOS judges.
"""
from __future__ import annotations

import math
from ..core.config import get_config, TradingConfig


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly fraction = (p * b - q) / b
    where p = win_rate, q = 1-p, b = avg_win/avg_loss

    Returns optimal fraction of capital to risk.
    Capped at 0.25 (quarter-Kelly) for safety.
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    q = 1 - win_rate
    b = avg_win / avg_loss
    kelly = (win_rate * b - q) / b

    # Negative Kelly = don't trade
    if kelly <= 0:
        return 0.0

    # Quarter-Kelly for conservatism
    return min(kelly, 0.25)


def position_size_risk(
    equity: float,
    risk_pct: float,
    entry: float,
    stop_loss: float,
    contract_multiplier: float = 1.0,
    point_value: float = 0.01,
) -> float:
    """
    Calculate position size based on fixed risk percentage.

    Formula: lots = (equity * risk_pct) / (SL_distance_in_pips * contract_multiplier_per_lot)

    For XAUUSD: 1 pip = $0.01 price movement, contract_multiplier = $1/pip/lot (standard)
    """
    risk_amount = equity * (risk_pct / 100)
    sl_distance = abs(entry - stop_loss)
    if sl_distance <= 0:
        return 0.0

    sl_pips = sl_distance / point_value
    if sl_pips <= 0:
        return 0.0

    lots = risk_amount / (sl_pips * contract_multiplier)

    # Round to 0.01 (micro lot)
    return max(0.01, round(lots, 2))


def position_size_kelly(
    equity: float,
    kelly_fraction: float,
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    entry: float,
    stop_loss: float,
    contract_multiplier: float = 1.0,
    point_value: float = 0.01,
) -> float:
    """
    Position size using Kelly Criterion.
    Kelly fraction tells us optimal bet size; we translate to lot size.
    """
    # Kelly amount = fraction * equity
    kelly_amount = kelly_fraction * equity

    # But cap at risk-based sizing as a safety net
    sl_distance = abs(entry - stop_loss)
    if sl_distance <= 0:
        return 0.0

    sl_pips = sl_distance / point_value
    lots = kelly_amount / (sl_pips * contract_multiplier) if sl_pips > 0 else 0.0

    return max(0.01, round(lots, 2))


def compute_position_size(
    signal,
    risk_state,
    cfg: TradingConfig | None = None,
) -> tuple[float, float]:
    """
    Compute final position size for a signal.
    Returns (lot_size, risk_amount).

    Uses the more conservative of:
    1. Fixed risk % of equity
    2. Kelly criterion (if history available)
    3. Max lot cap for Syed
    """
    if cfg is None:
        cfg = get_config()

    equity = risk_state.equity if risk_state.equity > 0 else cfg.syed_balance_estimate
    entry = signal.entry_price
    sl = signal.stop_loss

    # Method 1: Fixed risk %
    lots_risk = position_size_risk(
        equity=equity,
        risk_pct=cfg.max_risk_per_trade_pct,
        entry=entry,
        stop_loss=sl,
        contract_multiplier=cfg.contract_multiplier,
        point_value=cfg.point_value,
    )

    # Method 2: Kelly (default conservative if no history)
    lots_kelly = position_size_kelly(
        equity=equity,
        kelly_fraction=cfg.kelly_fraction,
        win_rate=0.45,  # conservative default
        avg_win=2.0,    # 1:2 RR default
        avg_loss=1.0,
        entry=entry,
        stop_loss=sl,
        contract_multiplier=cfg.contract_multiplier,
        point_value=cfg.point_value,
    )

    # Take the more conservative
    lots = min(lots_risk, lots_kelly)

    # Syed cap
    if cfg.syed_mode:
        lots = min(lots, cfg.syed_max_lot)

    # Floor at micro lot
    lots = max(0.01, round(lots, 2))

    risk_amount = round(lots * abs(entry - sl) / cfg.point_value * cfg.contract_multiplier, 2)

    return lots, risk_amount
