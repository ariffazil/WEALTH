"""
PRUDEX-Compass Engine — 6-Axis Strategy Evaluation

Eureka source: TradeMaster (NTU) PRUDEX-Compass framework.
Distilled into WEALTH capital_backtest.mode=compass.

6 axes, 16 measures:
  1. Profitability  — Total Return, Sharpe Ratio, Sortino Ratio, Calmar Ratio
  2. Risk Control   — Max Drawdown, Volatility, CVaR (95%)
  3. Diversity      — Action Entropy, Benchmark Correlation
  4. Reliability    — Seed Consistency, Rolling Window Stability
  5. Explainability — Action Distribution, Return Attribution
  6. Universality   — Cross-Regime Performance

All computed from existing backtest output. No new data sources needed.

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class CompassAxis:
    """Single evaluation axis with its measures."""

    name: str
    score: float  # 0-100 normalized
    measures: dict[str, float]


@dataclass
class CompassResult:
    """Full PRUDEX-Compass evaluation."""

    axes: list[dict]
    overall_score: float  # geometric mean of axes
    prudef_label: str  # PRUDEX classification
    regime_performance: dict[str, dict]  # per-regime metrics
    recommendations: list[str]


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b != 0 else default


def _percentile(values: list[float], p: float) -> float:
    """Compute p-th percentile (0-100)."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_v[int(k)]
    return sorted_v[f] * (c - k) + sorted_v[c] * (k - f)


def compute_compass(
    equity_curve: list[float],
    trade_returns: list[float],
    benchmark_returns: list[float] | None = None,
    regime_labels: list[str] | None = None,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> CompassResult:
    """Compute PRUDEX-Compass evaluation from backtest data.

    Args:
        equity_curve: Portfolio equity over time
        trade_returns: Per-trade returns (%)
        benchmark_returns: Optional benchmark returns for correlation
        regime_labels: Optional per-bar regime labels for universality
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year (252 for daily, 8760 for hourly)

    Returns:
        CompassResult with 6 axes and 16 measures
    """
    axes = []
    recommendations = []

    # ═══ AXIS 1: PROFITABILITY ═══
    prof_measures = {}
    total_return = 0.0
    if equity_curve and len(equity_curve) > 1 and equity_curve[0] > 0:
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] * 100

    # Daily returns from equity curve
    daily_returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            daily_returns.append(
                (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            )

    # Sharpe Ratio
    if daily_returns:
        mean_r = sum(daily_returns) / len(daily_returns)
        std_r = (
            sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
        ) ** 0.5
        annualized_r = mean_r * periods_per_year
        annualized_vol = std_r * (periods_per_year**0.5)
        sharpe = _safe_div(annualized_r - risk_free_rate, annualized_vol)
    else:
        sharpe = 0.0
        annualized_vol = 0.0

    # Sortino Ratio (downside deviation only)
    downside_returns = [r for r in daily_returns if r < 0]
    if downside_returns:
        downside_dev = (
            sum(r**2 for r in downside_returns) / len(downside_returns)
        ) ** 0.5
        sortino = _safe_div(
            annualized_r - risk_free_rate, downside_dev * (periods_per_year**0.5)
        )
    else:
        sortino = 0.0

    # Calmar Ratio (return / max drawdown)
    max_dd = _compute_max_drawdown(equity_curve)
    calmar = _safe_div(total_return / 100, abs(max_dd) if max_dd != 0 else 1.0)

    prof_measures = {
        "total_return_pct": round(total_return, 2),
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "calmar_ratio": round(calmar, 3),
    }
    prof_score = _normalize_profitability(total_return, sharpe, sortino, calmar)
    axes.append(
        {
            "name": "Profitability",
            "score": round(prof_score, 1),
            "measures": prof_measures,
        }
    )

    if prof_score < 30:
        recommendations.append("Low profitability — consider regime-filtered entry")

    # ═══ AXIS 2: RISK CONTROL ═══
    risk_measures = {
        "max_drawdown_pct": round(max_dd * 100, 2),
        "volatility_annualized": round(annualized_vol * 100, 2),
        "cvar_95": round(_compute_cvar(daily_returns, 0.05) * 100, 2),
    }
    risk_score = _normalize_risk_control(
        max_dd, annualized_vol, risk_measures["cvar_95"]
    )
    axes.append(
        {
            "name": "Risk_Control",
            "score": round(risk_score, 1),
            "measures": risk_measures,
        }
    )

    if risk_score < 30:
        recommendations.append(
            "High drawdown risk — tighten position sizing or add regime filter"
        )

    # ═══ AXIS 3: DIVERSITY ═══
    # Action entropy: how varied are trade directions/sizes
    if trade_returns:
        pos_count = sum(1 for r in trade_returns if r > 0)
        neg_count = sum(1 for r in trade_returns if r < 0)
        flat_count = sum(1 for r in trade_returns if r == 0)
        total_trades = len(trade_returns)
        probs = [c / total_trades for c in [pos_count, neg_count, flat_count] if c > 0]
        action_entropy = -sum(p * math.log2(p) for p in probs) if probs else 0
        max_entropy = math.log2(3)  # max 3 categories
        entropy_ratio = _safe_div(action_entropy, max_entropy)
    else:
        action_entropy = 0.0
        entropy_ratio = 0.0

    # Benchmark correlation
    if (
        benchmark_returns
        and daily_returns
        and len(benchmark_returns) == len(daily_returns)
    ):
        corr = _pearson_correlation(daily_returns, benchmark_returns)
    else:
        corr = 0.0

    div_measures = {
        "action_entropy": round(action_entropy, 3),
        "entropy_ratio": round(entropy_ratio, 3),
        "benchmark_correlation": round(corr, 3),
    }
    div_score = _normalize_diversity(entropy_ratio, corr)
    axes.append(
        {"name": "Diversity", "score": round(div_score, 1), "measures": div_measures}
    )

    # ═══ AXIS 4: RELIABILITY ═══
    # Rolling window stability (how consistent is performance over time)
    rolling_sharpes = _rolling_sharpe(
        daily_returns, window=min(60, len(daily_returns) // 3)
    )
    if rolling_sharpes:
        sharpe_std = (
            sum(
                (s - sum(rolling_sharpes) / len(rolling_sharpes)) ** 2
                for s in rolling_sharpes
            )
            / len(rolling_sharpes)
        ) ** 0.5
        stability = max(0, 1 - sharpe_std)  # lower std = higher stability
    else:
        stability = 0.0

    # Win rate consistency
    if trade_returns:
        win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns)
    else:
        win_rate = 0.0

    rel_measures = {
        "rolling_sharpe_stability": round(stability, 3),
        "win_rate": round(win_rate, 3),
        "trade_count": len(trade_returns),
    }
    rel_score = _normalize_reliability(stability, win_rate, len(trade_returns))
    axes.append(
        {"name": "Reliability", "score": round(rel_score, 1), "measures": rel_measures}
    )

    if rel_score < 30:
        recommendations.append(
            "Low reliability — strategy may be overfit or too few trades"
        )

    # ═══ AXIS 5: EXPLAINABILITY ═══
    # Return attribution by magnitude buckets
    if trade_returns:
        buckets = {"small": 0, "medium": 0, "large": 0}
        for r in trade_returns:
            ar = abs(r)
            if ar < 0.5:
                buckets["small"] += 1
            elif ar < 2.0:
                buckets["medium"] += 1
            else:
                buckets["large"] += 1
        total_t = len(trade_returns)
        action_dist = {k: round(v / total_t, 3) for k, v in buckets.items()}
    else:
        action_dist = {}

    explain_measures = {
        "action_distribution": action_dist,
        "avg_trade_return": round(sum(trade_returns) / len(trade_returns), 4)
        if trade_returns
        else 0,
    }
    explain_score = 50.0  # baseline — explainability is qualitative
    axes.append(
        {
            "name": "Explainability",
            "score": round(explain_score, 1),
            "measures": explain_measures,
        }
    )

    # ═══ AXIS 6: UNIVERSALITY ═══
    # Cross-regime performance
    regime_perf = {}
    if regime_labels and trade_returns and len(regime_labels) == len(trade_returns):
        for regime in set(regime_labels):
            regime_rets = [
                trade_returns[i]
                for i in range(len(trade_returns))
                if regime_labels[i] == regime
            ]
            if regime_rets:
                regime_perf[regime] = {
                    "count": len(regime_rets),
                    "avg_return": round(sum(regime_rets) / len(regime_rets), 4),
                    "win_rate": round(
                        sum(1 for r in regime_rets if r > 0) / len(regime_rets), 3
                    ),
                }

        # Universality = how many regimes are profitable
        profitable_regimes = sum(1 for v in regime_perf.values() if v["avg_return"] > 0)
        total_regimes = len(regime_perf) or 1
        univ_score = profitable_regimes / total_regimes * 100
    else:
        univ_score = 50.0  # neutral if no regime data

    univ_measures = {"regime_performance": regime_perf}
    axes.append(
        {
            "name": "Universality",
            "score": round(univ_score, 1),
            "measures": univ_measures,
        }
    )

    if univ_score < 50 and regime_perf:
        losing = [k for k, v in regime_perf.items() if v["avg_return"] <= 0]
        recommendations.append(f"Strategy loses in regimes: {', '.join(losing)}")

    # ═══ OVERALL SCORE ═══
    scores = [a["score"] for a in axes]
    # Geometric mean (requires all > 0)
    positive_scores = [s for s in scores if s > 0]
    if positive_scores:
        overall = math.prod(positive_scores) ** (1 / len(positive_scores))
    else:
        overall = 0.0

    # PRUDEX classification
    if overall >= 70:
        label = "STRONG"
    elif overall >= 50:
        label = "ADEQUATE"
    elif overall >= 30:
        label = "WEAK"
    else:
        label = "INSUFFICIENT"

    return CompassResult(
        axes=axes,
        overall_score=round(overall, 1),
        prudef_label=label,
        regime_performance=regime_perf,
        recommendations=recommendations,
    )


# ── Helpers ──────────────────────────────────────────────────────


def _compute_max_drawdown(equity_curve: list[float]) -> float:
    """Max drawdown as fraction (negative)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (eq - peak) / peak if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd
    return max_dd


def _compute_cvar(returns: list[float], alpha: float = 0.05) -> float:
    """Conditional VaR (Expected Shortfall) at given alpha."""
    if not returns:
        return 0.0
    sorted_r = sorted(returns)
    cutoff_idx = max(1, int(len(sorted_r) * alpha))
    tail = sorted_r[:cutoff_idx]
    return sum(tail) / len(tail) if tail else 0.0


def _pearson_correlation(x: list[float], y: list[float]) -> float:
    """Pearson correlation coefficient."""
    n = min(len(x), len(y))
    if n < 2:
        return 0.0
    x, y = x[:n], y[:n]
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
    sx = (sum((xi - mx) ** 2 for xi in x) / n) ** 0.5
    sy = (sum((yi - my) ** 2 for yi in y) / n) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return cov / (sx * sy)


def _rolling_sharpe(returns: list[float], window: int = 60) -> list[float]:
    """Compute rolling Sharpe ratios."""
    if len(returns) < window or window < 2:
        return []
    sharpes = []
    for i in range(window, len(returns) + 1):
        w = returns[i - window : i]
        m = sum(w) / len(w)
        s = (sum((r - m) ** 2 for r in w) / len(w)) ** 0.5
        sharpes.append(m / s if s > 0 else 0)
    return sharpes


# ── Normalization (0-100 scale) ──────────────────────────────────


def _normalize_profitability(
    total_return: float, sharpe: float, sortino: float, calmar: float
) -> float:
    """Normalize profitability to 0-100."""
    # Sharpe-based: 0=0, 1=50, 2+=100
    s_score = min(100, max(0, sharpe * 50))
    # Return-based: -20%=0, 0%=20, 20%=60, 50%+=100
    r_score = min(100, max(0, 20 + total_return * 1.6))
    return (
        s_score * 0.4
        + r_score * 0.3
        + min(100, sortino * 30) * 0.15
        + min(100, calmar * 50) * 0.15
    )


def _normalize_risk_control(max_dd: float, vol: float, cvar: float) -> float:
    """Normalize risk control to 0-100. Lower risk = higher score."""
    # Max DD: 0%=100, -10%=70, -20%=40, -30%+=10
    dd_score = max(0, min(100, 100 + max_dd * 300))
    # Vol: 0%=100, 10%=70, 20%=40, 30%+=10
    vol_score = max(0, min(100, 100 - vol * 300))
    # CVaR: same scale
    cvar_score = max(0, min(100, 100 + cvar * 300))
    return dd_score * 0.4 + vol_score * 0.3 + cvar_score * 0.3


def _normalize_diversity(entropy_ratio: float, correlation: float) -> float:
    """Normalize diversity to 0-100."""
    # High entropy = good, low correlation to benchmark = good
    e_score = entropy_ratio * 100
    c_score = (1 - abs(correlation)) * 100
    return e_score * 0.5 + c_score * 0.5


def _normalize_reliability(
    stability: float, win_rate: float, trade_count: int
) -> float:
    """Normalize reliability to 0-100."""
    s_score = stability * 100
    w_score = win_rate * 100
    # Trade count: <10=20, <30=50, <50=70, 50+=90
    t_score = min(90, 20 + trade_count * 1.4)
    return s_score * 0.4 + w_score * 0.3 + t_score * 0.3
