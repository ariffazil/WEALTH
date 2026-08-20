"""
Stress Test Engine — Synthetic Adversarial Reality Generation

Eureka source: TradeMaster (NTU) Market-GAN concepts + extreme market evaluation.
Distilled into WEALTH capital_backtest.mode=stress_test.

Core insight: History is ONE sample path. To truly stress-test,
you need synthetic scenarios that preserve market physics
(volatility clustering, fat tails, regime transitions) but explore
paths that haven't happened yet.

Approach (no GAN, pure bootstrap + regime-aware perturbation):
1. Bootstrap resampling of historical returns
2. Volatility scaling (1.5x, 2x, 3x historical vol)
3. Regime injection (forced bear/crisis segments)
4. Fat tail amplification (kurtosis injection)
5. Flash crash insertion

All computed from existing OHLCV + backtest engine.

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any


@dataclass
class StressScenario:
    """Single stress test scenario."""

    name: str
    description: str
    modifier: str  # VOL_SCALE, REGIME_INJECT, TAIL_AMPLIFY, FLASH_CRASH
    multiplier: float  # severity multiplier
    returns: list[float]  # synthetic returns


@dataclass
class StressResult:
    """Full stress test output."""

    baseline: dict[str, float]  # original backtest metrics
    scenarios: list[dict]  # per-scenario results
    worst_case: dict[str, Any]  # worst scenario summary
    robustness_score: float  # 0-100, how many scenarios survive
    scenarios_tested: int
    scenarios_survived: int
    recommendations: list[str]


def _returns_from_prices(prices: list[float]) -> list[float]:
    """Convert prices to returns."""
    return [
        (prices[i] - prices[i - 1]) / prices[i - 1] if prices[i - 1] != 0 else 0
        for i in range(1, len(prices))
    ]


def _prices_from_returns(returns: list[float], start_price: float) -> list[float]:
    """Convert returns back to prices."""
    prices = [start_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    return prices


def _bootstrap_returns(returns: list[float], n: int) -> list[float]:
    """Bootstrap resample returns."""
    return [random.choice(returns) for _ in range(n)]


def _scale_volatility(returns: list[float], scale: float) -> list[float]:
    """Scale volatility while preserving mean."""
    if not returns:
        return returns
    mean_r = sum(returns) / len(returns)
    return [mean_r + (r - mean_r) * scale for r in returns]


def _inject_crisis(
    returns: list[float], crisis_len: int = 20, severity: float = -0.03
) -> list[float]:
    """Inject a crisis segment at a random position."""
    result = list(returns)
    if len(result) < crisis_len * 2:
        return result

    # Insert crisis at random position
    start = random.randint(crisis_len, len(result) - crisis_len * 2)
    for i in range(crisis_len):
        # Gradual decline then recovery
        progress = i / crisis_len
        if progress < 0.7:
            # Decline phase
            result[start + i] = (
                severity * (1 - progress / 0.7) * random.uniform(0.5, 1.5)
            )
        else:
            # Partial recovery
            result[start + i] = abs(severity) * 0.3 * random.uniform(0, 1)

    return result


def _amplify_tails(returns: list[float], amplification: float = 2.0) -> list[float]:
    """Amplify fat tails — make extreme returns more extreme."""
    if not returns:
        return returns
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
    if std_r == 0:
        return returns

    result = []
    for r in returns:
        z = (r - mean_r) / std_r
        # Amplify based on distance from mean
        if abs(z) > 1.5:
            # Extreme move — amplify
            amplified = mean_r + z * std_r * amplification
            result.append(amplified)
        else:
            result.append(r)
    return result


def _inject_flash_crash(
    returns: list[float], crash_size: float = -0.08, recovery_pct: float = 0.6
) -> list[float]:
    """Insert a single flash crash event."""
    result = list(returns)
    if len(result) < 10:
        return result

    pos = random.randint(5, len(result) - 5)
    # Crash
    result[pos] = crash_size
    # Partial recovery over next 3 bars
    for i in range(1, 4):
        if pos + i < len(result):
            result[pos + i] = (
                abs(crash_size) * recovery_pct / 3 * random.uniform(0.5, 1.5)
            )

    return result


def _compute_metrics_from_returns(
    returns: list[float], initial_equity: float = 10000.0
) -> dict[str, float]:
    """Compute key metrics from a return series."""
    if not returns:
        return {
            "total_return_pct": 0,
            "max_drawdown_pct": 0,
            "sharpe_ratio": 0,
            "final_equity": initial_equity,
            "volatility": 0,
        }

    # Build equity curve
    equity = [initial_equity]
    for r in returns:
        equity.append(equity[-1] * (1 + r))

    total_return = (equity[-1] - initial_equity) / initial_equity * 100

    # Max drawdown
    peak = equity[0]
    max_dd = 0.0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = (eq - peak) / peak if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd

    # Sharpe
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
    sharpe = (mean_r / std_r * (252**0.5)) if std_r > 0 else 0

    return {
        "total_return_pct": round(total_return, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "final_equity": round(equity[-1], 2),
        "volatility": round(std_r * (252**0.5) * 100, 2),
    }


def run_stress_test(
    equity_curve: list[float],
    trade_returns: list[float],
    scenarios_config: list[dict] | None = None,
    seed: int | None = None,
) -> StressResult:
    """Run stress test on backtest results.

    Args:
        equity_curve: Original backtest equity curve
        trade_returns: Per-trade returns (%)
        scenarios_config: Optional custom scenario configs
        seed: Random seed for reproducibility

    Returns:
        StressResult with scenario analysis
    """
    if seed is not None:
        random.seed(seed)

    # Baseline metrics
    baseline = _compute_metrics_from_returns(
        trade_returns, equity_curve[0] if equity_curve else 10000
    )
    initial_equity = equity_curve[0] if equity_curve else 10000

    # Default scenarios if none provided
    if scenarios_config is None:
        scenarios_config = [
            {
                "name": "Vol +50%",
                "modifier": "VOL_SCALE",
                "multiplier": 1.5,
                "description": "Volatility increases 50% (regime shift)",
            },
            {
                "name": "Vol +100%",
                "modifier": "VOL_SCALE",
                "multiplier": 2.0,
                "description": "Volatility doubles (stress regime)",
            },
            {
                "name": "Vol +200%",
                "modifier": "VOL_SCALE",
                "multiplier": 3.0,
                "description": "Volatility triples (extreme stress)",
            },
            {
                "name": "Bear Crisis",
                "modifier": "REGIME_INJECT",
                "multiplier": 1.0,
                "description": "20-bar sustained decline injected",
            },
            {
                "name": "Flash Crash -8%",
                "modifier": "FLASH_CRASH",
                "multiplier": 1.0,
                "description": "Single -8% flash crash with partial recovery",
            },
            {
                "name": "Fat Tail x2",
                "modifier": "TAIL_AMPLIFY",
                "multiplier": 2.0,
                "description": "Extreme returns amplified 2x",
            },
            {
                "name": "Fat Tail x3",
                "modifier": "TAIL_AMPLIFY",
                "multiplier": 3.0,
                "description": "Extreme returns amplified 3x",
            },
            {
                "name": "Combined Stress",
                "modifier": "COMBINED",
                "multiplier": 1.5,
                "description": "Vol +50% + flash crash + tail amplification",
            },
        ]

    scenarios = []
    survived = 0

    for cfg in scenarios_config:
        # Generate synthetic returns
        if cfg["modifier"] == "VOL_SCALE":
            syn_returns = _scale_volatility(trade_returns, cfg["multiplier"])
        elif cfg["modifier"] == "REGIME_INJECT":
            syn_returns = _inject_crisis(
                trade_returns,
                crisis_len=max(10, len(trade_returns) // 10),
                severity=-0.03 * cfg["multiplier"],
            )
        elif cfg["modifier"] == "TAIL_AMPLIFY":
            syn_returns = _amplify_tails(trade_returns, cfg["multiplier"])
        elif cfg["modifier"] == "FLASH_CRASH":
            syn_returns = _inject_flash_crash(trade_returns, crash_size=-0.08)
        elif cfg["modifier"] == "COMBINED":
            # Chain: vol scale → flash crash → tail amplify
            syn_returns = _scale_volatility(trade_returns, cfg["multiplier"])
            syn_returns = _inject_flash_crash(syn_returns, crash_size=-0.06)
            syn_returns = _amplify_tails(syn_returns, 1.5)
        else:
            syn_returns = trade_returns

        # Compute metrics on synthetic returns
        syn_metrics = _compute_metrics_from_returns(syn_returns, initial_equity)

        # Survived = still profitable AND drawdown < 30%
        is_survived = (
            syn_metrics["total_return_pct"] > 0
            and abs(syn_metrics["max_drawdown_pct"]) < 30
        )
        if is_survived:
            survived += 1

        scenarios.append(
            {
                "name": cfg["name"],
                "description": cfg["description"],
                "modifier": cfg["modifier"],
                "multiplier": cfg["multiplier"],
                "metrics": syn_metrics,
                "survived": is_survived,
                "delta_return": round(
                    syn_metrics["total_return_pct"] - baseline["total_return_pct"], 2
                ),
                "delta_drawdown": round(
                    syn_metrics["max_drawdown_pct"] - baseline["max_drawdown_pct"], 2
                ),
            }
        )

    # Worst case
    worst = (
        min(scenarios, key=lambda s: s["metrics"]["total_return_pct"])
        if scenarios
        else {}
    )

    # Robustness score
    total = len(scenarios) or 1
    robustness = survived / total * 100

    # Recommendations
    recommendations = []
    if robustness < 50:
        recommendations.append(
            "Strategy fragile — less than half of stress scenarios survive"
        )
    if worst and worst["metrics"]["max_drawdown_pct"] < -25:
        recommendations.append(
            f"Worst case drawdown: {worst['metrics']['max_drawdown_pct']}% — consider tighter risk limits"
        )
    if robustness >= 80:
        recommendations.append("Strategy robust — survives most stress scenarios")

    return StressResult(
        baseline=baseline,
        scenarios=scenarios,
        worst_case=worst,
        robustness_score=round(robustness, 1),
        scenarios_tested=len(scenarios),
        scenarios_survived=survived,
        recommendations=recommendations,
    )
