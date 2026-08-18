"""
Enhanced backtest metrics — ported from chrisconlan/algorithmic-trading-with-python
plus additions for XAUUSD-specific analysis.

Source: https://github.com/chrisconlan/algorithmic-trading-with-python (MIT License)
Integrated: 2026-08-19 by 333-AGI for arifOS WEALTH organ

Adds to engine_v2._compute_metrics:
  - Sortino ratio (downside-only volatility)
  - Calmar ratio (CAGR / max drawdown)
  - Pure profit score (CAGR × R² smoothness)
  - Drawdown metadata (peak/trough dates + prices)
  - Rolling Sharpe (N-period window)
  - Log max drawdown ratio
  - Annualized volatility from trade returns
  - Expectancy per trade
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np


# ──────────────────────────── Core helpers ────────────────────────────


def _years_between(start: datetime, end: datetime) -> float:
    """Calculate years between two datetimes."""
    return (end - start).days / 365.25


def _annualization_factor(returns: list[float], years: float) -> float:
    """Calculate entries per year for annualization."""
    if years <= 0:
        return 252.0  # fallback to daily
    return len(returns) / years


# ──────────────────────────── Return metrics ────────────────────────────


def cagr(initial_equity: float, final_equity: float, years: float) -> float:
    """Compounded annual growth rate."""
    if years <= 0 or initial_equity <= 0:
        return 0.0
    return (final_equity / initial_equity) ** (1 / years) - 1


def annualized_volatility(returns: list[float], years: float) -> float:
    """Annualized volatility from a list of period returns."""
    if len(returns) < 2 or years <= 0:
        return 0.0
    entries_per_year = _annualization_factor(returns, years)
    return float(np.std(returns, ddof=1) * np.sqrt(entries_per_year))


# ──────────────────────────── Risk-adjusted ────────────────────────────


def sharpe_ratio(returns: list[float], years: float, risk_free: float = 0.0) -> float:
    """Annualized Sharpe ratio from trade returns."""
    vol = annualized_volatility(returns, years)
    if vol == 0:
        return 0.0
    mean_annual = float(np.mean(returns)) * _annualization_factor(returns, years)
    return (mean_annual - risk_free) / vol


def sortino_ratio(returns: list[float], years: float, risk_free: float = 0.0) -> float:
    """Sortino ratio — penalizes only downside volatility."""
    if len(returns) < 2 or years <= 0:
        return 0.0
    entries_per_year = _annualization_factor(returns, years)
    adjusted_benchmark = ((1 + risk_free) ** (1 / entries_per_year)) - 1
    downside = [min(0, r - adjusted_benchmark) for r in returns]
    downside_sq = sum(d**2 for d in downside)
    downside_dev = math.sqrt(downside_sq / (len(returns) - 1)) * math.sqrt(
        entries_per_year
    )
    if downside_dev == 0:
        return 0.0
    mean_annual = float(np.mean(returns)) * entries_per_year
    return (mean_annual - risk_free) / downside_dev


def calmar_ratio(equity_curve: list[float], years: float) -> float:
    """Calmar ratio = CAGR / max drawdown (percent)."""
    if len(equity_curve) < 2 or years <= 0:
        return 0.0
    initial = equity_curve[0]
    final = equity_curve[-1]
    c = cagr(initial, final, years)
    dd = max_drawdown_percent(equity_curve)
    if dd == 0:
        return float("inf") if c > 0 else 0.0
    return c / dd


def pure_profit_score(
    initial_equity: float, final_equity: float, equity_curve: list[float], years: float
) -> float:
    """CAGR × R² — measures smoothness of equity growth."""
    if len(equity_curve) < 3 or years <= 0:
        return 0.0
    c = cagr(initial_equity, final_equity, years)
    # R² of equity curve vs linear trend
    y = np.array(equity_curve)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return c * r_squared


# ──────────────────────────── Drawdown ────────────────────────────


def max_drawdown_percent(equity_curve: list[float]) -> float:
    """Max drawdown as a fraction (0.10 = 10%)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    return max_dd


@dataclass
class DrawdownMetadata:
    max_drawdown: float  # as fraction
    peak_index: int
    peak_value: float
    trough_index: int
    trough_value: float
    peak_date: Optional[datetime] = None
    trough_date: Optional[datetime] = None


def drawdown_metadata(
    equity_curve: list[float], dates: Optional[list[datetime]] = None
) -> DrawdownMetadata:
    """Max drawdown with peak/trough locations."""
    if len(equity_curve) < 2:
        return DrawdownMetadata(
            0,
            0,
            equity_curve[0] if equity_curve else 0,
            0,
            equity_curve[0] if equity_curve else 0,
        )
    peak_idx = 0
    peak_val = equity_curve[0]
    max_dd = 0.0
    best_peak_idx = 0
    best_trough_idx = 0

    for i, val in enumerate(equity_curve):
        if val > peak_val:
            peak_val = val
            peak_idx = i
        dd = (peak_val - val) / peak_val if peak_val > 0 else 0
        if dd > max_dd:
            max_dd = dd
            best_peak_idx = peak_idx
            best_trough_idx = i

    return DrawdownMetadata(
        max_drawdown=max_dd,
        peak_index=best_peak_idx,
        peak_value=equity_curve[best_peak_idx],
        trough_index=best_trough_idx,
        trough_value=equity_curve[best_trough_idx],
        peak_date=dates[best_peak_idx] if dates else None,
        trough_date=dates[best_trough_idx] if dates else None,
    )


def log_max_drawdown_ratio(equity_curve: list[float]) -> float:
    """Log return minus log max drawdown. Higher = better risk-adjusted."""
    if len(equity_curve) < 2:
        return 0.0
    log_return = math.log(equity_curve[-1]) - math.log(equity_curve[0])
    # Log max drawdown
    peak = equity_curve[0]
    max_log_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        log_dd = math.log(peak) - math.log(val) if val > 0 and peak > 0 else 0
        max_log_dd = max(max_log_dd, log_dd)
    return log_return - max_log_dd


# ──────────────────────────── Rolling ────────────────────────────


def rolling_sharpe(returns: list[float], window: int = 20) -> list[Optional[float]]:
    """Rolling Sharpe approximation (mean/std × √window)."""
    result: list[Optional[float]] = []
    for i in range(len(returns)):
        if i < window - 1:
            result.append(None)
        else:
            window_returns = returns[i - window + 1 : i + 1]
            mean = float(np.mean(window_returns))
            std = float(np.std(window_returns, ddof=1))
            result.append(mean / std * math.sqrt(window) if std > 0 else None)
    return result


# ──────────────────────────── Trade-level ────────────────────────────


def expectancy(wins: list[float], losses: list[float]) -> float:
    """Expected value per trade: (win_rate × avg_win) + (loss_rate × avg_loss)."""
    total = len(wins) + len(losses)
    if total == 0:
        return 0.0
    win_rate = len(wins) / total
    loss_rate = len(losses) / total
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    return win_rate * avg_win + loss_rate * avg_loss


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Kelly criterion for optimal bet sizing. Returns fraction of capital."""
    if avg_loss == 0 or avg_win == 0:
        return 0.0
    b = avg_win / abs(avg_loss)
    kelly = win_rate - (1 - win_rate) / b
    return max(0, kelly)  # never negative (don't bet)


# ──────────────────────────── Composite ────────────────────────────


@dataclass
class EnhancedMetrics:
    """All enhanced metrics in one place."""

    # Risk-adjusted
    sharpe: float
    sortino: float
    calmar: float
    pure_profit_score: float
    # Drawdown
    max_dd_pct: float
    log_dd_ratio: float
    dd_peak_date: Optional[datetime]
    dd_trough_date: Optional[datetime]
    dd_peak_value: float
    dd_trough_value: float
    # Trade-level
    expectancy_per_trade: float
    kelly_fraction: float
    # Volatility
    annualized_vol: float
    # Rolling
    rolling_sharpe_latest: Optional[float]


def compute_enhanced(
    trade_pnls: list[float],
    equity_curve: list[float],
    dates: Optional[list[datetime]] = None,
    initial_equity: float = 10000.0,
    years: float = 1.0,
) -> EnhancedMetrics:
    """Compute all enhanced metrics from trade P&Ls and equity curve."""

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    final_equity = equity_curve[-1] if equity_curve else initial_equity

    # Return series (period-over-period)
    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            returns.append(equity_curve[i] / equity_curve[i - 1] - 1)

    dd_meta = drawdown_metadata(equity_curve, dates)
    rolling = rolling_sharpe(returns, window=20) if len(returns) > 20 else []

    return EnhancedMetrics(
        sharpe=sharpe_ratio(returns, years),
        sortino=sortino_ratio(returns, years),
        calmar=calmar_ratio(equity_curve, years),
        pure_profit_score=pure_profit_score(
            initial_equity, final_equity, equity_curve, years
        ),
        max_dd_pct=dd_meta.max_drawdown * 100,
        log_dd_ratio=log_max_drawdown_ratio(equity_curve),
        dd_peak_date=dd_meta.peak_date,
        dd_trough_date=dd_meta.trough_date,
        dd_peak_value=dd_meta.peak_value,
        dd_trough_value=dd_meta.trough_value,
        expectancy_per_trade=expectancy(wins, losses),
        kelly_fraction=kelly_criterion(
            len(wins) / len(trade_pnls) if trade_pnls else 0,
            float(np.mean(wins)) if wins else 0,
            float(np.mean(losses)) if losses else 0,
        ),
        annualized_vol=annualized_volatility(returns, years),
        rolling_sharpe_latest=rolling[-1] if rolling else None,
    )


def format_enhanced(m: EnhancedMetrics) -> str:
    """Format enhanced metrics for display."""
    lines = [
        f"  Sharpe:          {m.sharpe:.2f}",
        f"  Sortino:         {m.sortino:.2f}",
        f"  Calmar:          {m.calmar:.2f}",
        f"  Pure Profit:     {m.pure_profit_score:.4f}",
        f"  Annualized Vol:  {m.annualized_vol:.2%}",
        f"  ── Drawdown ──",
        f"  Max DD:          {m.max_dd_pct:.2f}%",
        f"  Log DD Ratio:    {m.log_dd_ratio:.4f}",
    ]
    if m.dd_peak_date:
        lines.append(
            f"  DD Peak:         {m.dd_peak_date.strftime('%Y-%m-%d')} @ ${m.dd_peak_value:,.2f}"
        )
        lines.append(
            f"  DD Trough:       {m.dd_trough_date.strftime('%Y-%m-%d')} @ ${m.dd_trough_value:,.2f}"
        )
    lines.extend(
        [
            f"  ── Trade ──",
            f"  Expectancy:      ${m.expectancy_per_trade:.2f}/trade",
            f"  Kelly Fraction:  {m.kelly_fraction:.2%}",
        ]
    )
    if m.rolling_sharpe_latest is not None:
        lines.append(f"  Rolling Sharpe:  {m.rolling_sharpe_latest:.2f} (last 20)")
    return "\n".join(lines)
