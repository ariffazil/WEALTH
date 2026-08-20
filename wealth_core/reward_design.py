"""
Reward Design Engine — Multi-Task Reward Functions

Eureka source: TradeMaster (NTU) task-specific reward design.
Distilled into WEALTH capital_primitive.mode=reward_design.

Core insight: The reward function IS the strategy. Same market data,
different objective = completely different optimal policy.

Reward types:
1. SHARPE — risk-adjusted return (portfolio management)
2. SORTINO — downside-only risk (conservative)
3. CALMAR — return / max drawdown (drawdown-sensitive)
4. IMPLEMENTATION_SHORTFALL — execution quality (order execution)
5. RISK_ADJUSTED_PNL — asymmetric risk (algo trading)
6. MULTI_OBJECTIVE — weighted combination

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class RewardFunction:
    """A reward function specification."""

    name: str
    task_type: str  # portfolio, algo, execution, hft
    formula: str
    parameters: dict[str, float]
    description: str


@dataclass
class RewardDesignResult:
    """Reward design output."""

    recommended_reward: RewardFunction
    all_rewards: list[dict]
    task_type: str
    justification: str


def _compute_sharpe(returns: list[float], periods_per_year: float = 252) -> float:
    """Annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
    if std_r == 0:
        return 0.0
    return mean_r / std_r * (periods_per_year**0.5)


def _compute_sortino(returns: list[float], periods_per_year: float = 252) -> float:
    """Sortino ratio (downside deviation only)."""
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    downside = [r for r in returns if r < 0]
    if not downside:
        return 10.0  # cap
    downside_dev = (sum(r**2 for r in downside) / len(downside)) ** 0.5
    if downside_dev == 0:
        return 10.0
    return mean_r / downside_dev * (periods_per_year**0.5)


def _compute_calmar(returns: list[float]) -> float:
    """Calmar ratio (return / max drawdown)."""
    if len(returns) < 2:
        return 0.0
    equity = [1.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    peak = equity[0]
    max_dd = 0.0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = (eq - peak) / peak
        if dd < max_dd:
            max_dd = dd
    total_return = equity[-1] / equity[0] - 1
    if max_dd == 0:
        return 10.0
    return total_return / abs(max_dd)


def _compute_implementation_shortfall(
    actual_prices: list[float],
    decision_prices: list[float],
    volumes: list[float],
    direction: int = 1,  # 1 = buy, -1 = sell
) -> float:
    """Implementation shortfall: difference between decision and execution."""
    if not actual_prices or not decision_prices:
        return 0.0
    shortfall = sum(
        direction * (actual_prices[i] - decision_prices[i]) * volumes[i]
        for i in range(min(len(actual_prices), len(decision_prices)))
    ) / sum(volumes[: min(len(actual_prices), len(decision_prices))])
    return shortfall


def compute_reward_design(
    task_type: str = "portfolio",
    returns: list[float] | None = None,
    risk_aversion: float = 1.0,
    max_drawdown_tolerance: float = 0.15,
) -> RewardDesignResult:
    """Design optimal reward function for a trading task.

    Args:
        task_type: portfolio, algo, execution, hft
        returns: Historical returns for calibration
        risk_aversion: Loss aversion coefficient
        max_drawdown_tolerance: Maximum acceptable drawdown

    Returns:
        RewardDesignResult with recommended reward function
    """
    all_rewards = []
    task = task_type.lower()

    # ═══ PORTFOLIO MANAGEMENT ═══
    if task == "portfolio":
        all_rewards.append(
            {
                "name": "sharpe_reward",
                "formula": "mean(returns) / std(returns) * sqrt(252)",
                "description": "Risk-adjusted return. Standard for portfolio allocation.",
                "strengths": [
                    "Well-understood",
                    "Penalizes volatility",
                    "Industry standard",
                ],
                "weaknesses": [
                    "Treats upside and downside equally",
                    "Sensitive to normality assumption",
                ],
                "best_when": "Diversified portfolio, moderate risk tolerance",
            }
        )
        all_rewards.append(
            {
                "name": "sortino_reward",
                "formula": "mean(returns) / downside_deviation * sqrt(252)",
                "description": "Downside-only risk adjustment. Better for asymmetric preferences.",
                "strengths": [
                    "Only penalizes downside",
                    "More realistic for investors",
                ],
                "weaknesses": [
                    "Ignores upside volatility",
                    "May encourage concentrated bets",
                ],
                "best_when": "Capital preservation priority, asymmetric preferences",
            }
        )
        all_rewards.append(
            {
                "name": "calmar_reward",
                "formula": "total_return / max_drawdown",
                "description": "Return per unit of drawdown. Best for drawdown-sensitive mandates.",
                "strengths": ["Directly controls drawdown", "Simple to interpret"],
                "weaknesses": [
                    "Sensitive to drawdown measurement period",
                    "May be too conservative",
                ],
                "best_when": f"Max drawdown tolerance < {max_drawdown_tolerance * 100}%",
            }
        )

        # Recommended
        recommended = RewardFunction(
            name="sortino_reward",
            task_type="portfolio",
            formula="mean(returns) / downside_dev * sqrt(252) + risk_aversion * max(0, -drawdown - tolerance)",
            parameters={
                "risk_aversion": risk_aversion,
                "max_dd_tolerance": max_drawdown_tolerance,
            },
            description="Sortino with drawdown penalty. Optimal for capital preservation.",
        )

    # ═══ ALGORITHMIC TRADING ═══
    elif task == "algo":
        all_rewards.append(
            {
                "name": "risk_adjusted_pnl",
                "formula": "sum(pnl) - lambda * sum(max(0, -pnl))",
                "description": "Asymmetric PnL: losses penalized more than gains rewarded.",
                "strengths": ["Matches DeepScalper design", "Loss aversion built-in"],
                "weaknesses": [
                    "Requires tuning lambda",
                    "May be too conservative in trending markets",
                ],
                "best_when": "High-frequency, mean-reverting strategies",
            }
        )
        all_rewards.append(
            {
                "name": "sharpe_with_turnover_penalty",
                "formula": "sharpe - alpha * turnover",
                "description": "Sharpe adjusted for transaction costs and turnover.",
                "strengths": ["Controls costs", "Encourages holding"],
                "weaknesses": [
                    "Alpha parameter critical",
                    "May miss short-term opportunities",
                ],
                "best_when": "Medium-frequency, cost-sensitive strategies",
            }
        )

        recommended = RewardFunction(
            name="risk_adjusted_pnl",
            task_type="algo",
            formula="sum(pnl) - lambda * sum(max(0, -pnl))^2",
            parameters={"lambda": risk_aversion * 2.5},
            description="Asymmetric PnL with quadratic loss penalty. DeepScalper-inspired.",
        )

    # ═══ ORDER EXECUTION ═══
    elif task == "execution":
        all_rewards.append(
            {
                "name": "implementation_shortfall",
                "formula": "-|actual_price - decision_price| * volume",
                "description": "Minimize difference between decision and execution price.",
                "strengths": [
                    "Industry standard for execution quality",
                    "Directly measurable",
                ],
                "weaknesses": [
                    "Requires decision price benchmark",
                    "Ignores market impact",
                ],
                "best_when": "TWAP/VWAP execution, institutional orders",
            }
        )
        all_rewards.append(
            {
                "name": "arrival_price_benchmark",
                "formula": "-|execution_price - arrival_price| / arrival_price",
                "description": "Performance vs arrival price. Simpler benchmark.",
                "strengths": ["Easy to measure", "No decision price needed"],
                "weaknesses": ["May not capture full execution quality"],
                "best_when": "Single-shot execution, simple benchmarking",
            }
        )

        recommended = RewardFunction(
            name="implementation_shortfall",
            task_type="execution",
            formula="-sum(|actual - decision| * volume) / sum(volume)",
            parameters={"urgency_factor": 0.5},
            description="Implementation shortfall with urgency weighting.",
        )

    # ═══ HIGH-FREQUENCY TRADING ═══
    elif task == "hft":
        all_rewards.append(
            {
                "name": "pnl_per_trade",
                "formula": "sum(pnl) / trade_count",
                "description": "Average PnL per trade. Key for HFT profitability.",
                "strengths": ["Simple", "Directly measures per-trade edge"],
                "weaknesses": ["Ignores risk", "May encourage overtrading"],
                "best_when": "Very high frequency, many trades per day",
            }
        )

        recommended = RewardFunction(
            name="pnl_per_trade",
            task_type="hft",
            formula="sum(pnl) / trade_count - beta * std(pnl)",
            parameters={"beta": 0.5},
            description="PnL per trade with volatility penalty.",
        )

    else:
        # Default to portfolio
        recommended = RewardFunction(
            name="sharpe_reward",
            task_type="portfolio",
            formula="mean(returns) / std(returns) * sqrt(252)",
            parameters={},
            description="Default Sharpe ratio reward.",
        )

    # Calibration if returns provided
    justification = f"Task: {task}. "
    if returns:
        sharpe = _compute_sharpe(returns)
        sortino = _compute_sortino(returns)
        calmar = _compute_calmar(returns)
        justification += f"Historical Sharpe={sharpe:.2f}, Sortino={sortino:.2f}, Calmar={calmar:.2f}. "
        if sortino > sharpe * 1.5:
            justification += "Downside risk is well-controlled. Sortino recommended."
        elif calmar < 1.0:
            justification += (
                "Drawdowns are significant. Calmar-based reward recommended."
            )
        else:
            justification += "Balanced risk profile. Standard Sharpe appropriate."
    else:
        justification += "No historical returns provided. Using task-type default."

    return RewardDesignResult(
        recommended_reward=recommended,
        all_rewards=all_rewards,
        task_type=task,
        justification=justification,
    )
