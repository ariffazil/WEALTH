"""
Asymmetric Risk Engine — Drawdown-Sensitive Sizing (DeepScalper Distillation)

Eureka source: TradeMaster (NTU) DeepScalper (CIKM 2022) — risk-aware RL framework.
Distilled into WEALTH capital_health.mode=asymmetric_risk.

Core insight: The pain of a loss is psychologically and mathematically greater
than the pleasure of an equivalent gain. The reward function should be asymmetric:
penalize drawdowns 2-3x more than equivalent gains.

Approach:
1. Asymmetric Kelly Criterion (loss aversion coefficient)
2. Omega Ratio (probability-weighted gains vs losses)
3. Pain-to-Gain ratio (max drawdown / max runup)
4. Risk-adjusted position sizing with drawdown scaling

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class AsymmetricRiskResult:
    """Full asymmetric risk assessment."""

    standard_kelly: float
    asymmetric_kelly: float
    loss_aversion_coefficient: float
    omega_ratio: float
    pain_to_gain_ratio: float
    recommended_risk_pct: float
    position_scaling: float  # multiplier on base position size
    drawdown_state: str  # NORMAL, CAUTION, DANGER, CRITICAL
    metrics: dict[str, float]
    recommendations: list[str]


def _compute_kelly(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Standard Kelly Criterion: f* = (p*b - q) / b

    Where p = win rate, q = 1-p, b = avg_win/avg_loss
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    b = avg_win / avg_loss  # win/loss ratio
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b

    # Cap at 0.25 (quarter Kelly for safety)
    return max(0, min(0.25, kelly))


def _compute_asymmetric_kelly(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    loss_aversion: float = 2.5,
) -> float:
    """Asymmetric Kelly with loss aversion.

    Adjusts the effective win/loss ratio to account for the fact that
    losses hurt more than equivalent gains help.

    loss_aversion: coefficient (>1 means losses hurt more)
    Effective b = avg_win / (avg_loss * loss_aversion)
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    # Effective loss is amplified by aversion coefficient
    effective_loss = avg_loss * loss_aversion
    b = avg_win / effective_loss
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b

    return max(0, min(0.25, kelly))


def _compute_omega_ratio(returns: list[float], threshold: float = 0.0) -> float:
    """Omega Ratio: sum of gains above threshold / sum of losses below threshold.

    Omega > 1 means gains dominate. Omega < 1 means losses dominate.
    """
    if not returns:
        return 0.0

    gains = sum(r - threshold for r in returns if r > threshold)
    losses = sum(threshold - r for r in returns if r < threshold)

    if losses == 0:
        return 10.0  # cap — no losses
    return gains / losses


def _compute_pain_to_gain(equity_curve: list[float]) -> tuple[float, float, float]:
    """Compute max drawdown (pain) and max runup (gain).

    Returns (max_drawdown_pct, max_runup_pct, pain_to_gain_ratio).
    """
    if len(equity_curve) < 2:
        return 0.0, 0.0, 0.0

    peak = equity_curve[0]
    trough = equity_curve[0]
    max_dd = 0.0
    max_runup = 0.0

    # Track from peak
    running_peak = equity_curve[0]
    for eq in equity_curve:
        if eq > running_peak:
            running_peak = eq
        dd = (eq - running_peak) / running_peak if running_peak > 0 else 0
        if dd < max_dd:
            max_dd = dd

    # Track max runup from trough
    running_trough = equity_curve[0]
    for eq in equity_curve:
        if eq < running_trough:
            running_trough = eq
        ru = (eq - running_trough) / running_trough if running_trough > 0 else 0
        if ru > max_runup:
            max_runup = ru

    pain = abs(max_dd) * 100
    gain = max_runup * 100
    p2g = pain / gain if gain > 0 else 10.0

    return pain, gain, p2g


def _classify_drawdown_state(max_dd_pct: float, omega: float, p2g: float) -> str:
    """Classify current drawdown state."""
    if max_dd_pct > 25 or omega < 0.5:
        return "CRITICAL"
    elif max_dd_pct > 15 or omega < 0.8:
        return "DANGER"
    elif max_dd_pct > 8 or omega < 1.0:
        return "CAUTION"
    return "NORMAL"


def _compute_position_scaling(drawdown_state: str, current_dd_pct: float) -> float:
    """Compute position scaling multiplier based on drawdown state.

    When in drawdown, reduce position size to preserve capital.
    """
    scaling = {
        "NORMAL": 1.0,
        "CAUTION": 0.7,
        "DANGER": 0.4,
        "CRITICAL": 0.2,
    }
    base = scaling.get(drawdown_state, 1.0)

    # Further reduce if actively in drawdown
    if current_dd_pct > 0:
        # Scale down linearly from base at 0% DD to 0.1 at 30% DD
        dd_factor = max(0.1, 1.0 - current_dd_pct / 30.0)
        base *= dd_factor

    return round(base, 3)


def compute_asymmetric_risk(
    trade_returns: list[float],
    equity_curve: list[float],
    loss_aversion: float = 2.5,
    base_risk_pct: float = 1.0,
) -> AsymmetricRiskResult:
    """Compute asymmetric risk assessment.

    Args:
        trade_returns: Per-trade returns (%)
        equity_curve: Portfolio equity over time
        loss_aversion: Loss aversion coefficient (>1 = losses hurt more)
        base_risk_pct: Base risk per trade (%)

    Returns:
        AsymmetricRiskResult with sizing recommendations
    """
    if not trade_returns or not equity_curve:
        return AsymmetricRiskResult(
            standard_kelly=0,
            asymmetric_kelly=0,
            loss_aversion_coefficient=loss_aversion,
            omega_ratio=0,
            pain_to_gain_ratio=0,
            recommended_risk_pct=0,
            position_scaling=0,
            drawdown_state="UNKNOWN",
            metrics={},
            recommendations=["Insufficient data"],
        )

    # Basic stats
    win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns)
    wins = [r for r in trade_returns if r > 0]
    losses = [abs(r) for r in trade_returns if r < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    # Kelly
    std_kelly = _compute_kelly(win_rate, avg_win, avg_loss)
    asym_kelly = _compute_asymmetric_kelly(win_rate, avg_loss, avg_loss, loss_aversion)

    # Omega
    omega = _compute_omega_ratio(trade_returns)

    # Pain-to-Gain
    pain, gain, p2g = _compute_pain_to_gain(equity_curve)

    # Current drawdown
    peak = equity_curve[0]
    for eq in equity_curve:
        if eq > peak:
            peak = eq
    current_dd = (equity_curve[-1] - peak) / peak * 100 if peak > 0 else 0

    # Drawdown state
    dd_state = _classify_drawdown_state(pain, omega, p2g)

    # Position scaling
    pos_scaling = _compute_position_scaling(dd_state, abs(current_dd))

    # Recommended risk
    recommended_risk = base_risk_pct * pos_scaling

    # Metrics
    metrics = {
        "win_rate": round(win_rate, 3),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "win_loss_ratio": round(avg_win / avg_loss, 3) if avg_loss > 0 else 0,
        "trade_count": len(trade_returns),
        "current_drawdown_pct": round(current_dd, 2),
        "max_drawdown_pct": round(pain, 2),
        "max_runup_pct": round(gain, 2),
        "omega_ratio": round(omega, 3),
    }

    # Recommendations
    recommendations = []
    if dd_state == "CRITICAL":
        recommendations.append(
            "CRITICAL drawdown state — reduce position size to 20% of base"
        )
    elif dd_state == "DANGER":
        recommendations.append(
            "DANGER drawdown state — reduce position size to 40% of base"
        )
    elif dd_state == "CAUTION":
        recommendations.append(
            "CAUTION drawdown state — reduce position size to 70% of base"
        )

    if asym_kelly < std_kelly * 0.5 and asym_kelly > 0:
        recommendations.append(
            f"Asymmetric Kelly ({asym_kelly:.3f}) is {std_kelly / asym_kelly:.1f}x smaller than "
            f"standard Kelly ({std_kelly:.3f}) — loss aversion significantly reduces optimal sizing"
        )

    if omega < 1.0:
        recommendations.append(
            f"Omega ratio ({omega:.2f}) < 1.0 — losses dominate gains"
        )
    elif omega > 2.0:
        recommendations.append(
            f"Omega ratio ({omega:.2f}) > 2.0 — strong risk/reward profile"
        )

    if p2g > 1.0:
        recommendations.append(
            f"Pain-to-gain ratio ({p2g:.2f}) > 1.0 — drawdowns exceed runups"
        )

    return AsymmetricRiskResult(
        standard_kelly=round(std_kelly, 4),
        asymmetric_kelly=round(asym_kelly, 4),
        loss_aversion_coefficient=loss_aversion,
        omega_ratio=round(omega, 3),
        pain_to_gain_ratio=round(p2g, 3),
        recommended_risk_pct=round(recommended_risk, 3),
        position_scaling=pos_scaling,
        drawdown_state=dd_state,
        metrics=metrics,
        recommendations=recommendations,
    )
