"""
Ensemble Engine — Regime-Aware Strategy Composition (AlphaMix+ Distillation)

Eureka source: TradeMaster (NTU) AlphaMix+ (KDD 2023) — Mixture-of-Experts for trading.
Distilled into WEALTH capital_backtest.mode=ensemble.

Core insight: No single strategy works in all regimes. The MoE architecture
means you don't pick the "best" strategy — you compose a portfolio of strategies,
each activated by regime.

Approach (no ML, pure numpy on existing backtest engine):
1. Run multiple strategy configs (different EMA/RSI/ATR parameters)
2. Label each trade's regime using regime_map
3. Compute per-regime performance for each strategy
4. Optimal regime-to-strategy mapping via greedy assignment
5. Compose ensemble returns by regime-switching

DITEMPA BUKAN DIBERI — forged from TradeMaster distillation, not imported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyConfig:
    """A strategy variant with its parameters."""

    name: str
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    rsi_period: int = 14
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0
    atr_mult_sl: float = 2.0
    atr_mult_tp: float = 2.0


@dataclass
class StrategyPerformance:
    """Per-strategy, per-regime performance."""

    strategy_name: str
    regime: str
    trade_count: int
    avg_return: float
    win_rate: float
    sharpe: float


@dataclass
class EnsembleResult:
    """Full ensemble composition result."""

    strategies_tested: int
    regimes_detected: list[str]
    regime_strategy_map: dict[str, dict]  # regime -> {strategy, reason}
    strategy_performances: list[dict]
    ensemble_metrics: dict[str, float]
    baseline_metrics: dict[str, float]  # best single strategy
    improvement: dict[str, float]  # ensemble vs best single
    recommendations: list[str]


def _compute_sharpe(returns: list[float], periods_per_year: float = 252) -> float:
    """Annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
    if std_r == 0:
        return 0.0
    return mean_r / std_r * (periods_per_year**0.5)


def _compute_max_drawdown_pct(equity_curve: list[float]) -> float:
    """Max drawdown as percentage (negative)."""
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
    return max_dd * 100


def _equity_from_returns(returns: list[float], initial: float = 10000) -> list[float]:
    """Build equity curve from returns."""
    equity = [initial]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    return equity


def _metrics_from_returns(
    returns: list[float], initial: float = 10000
) -> dict[str, float]:
    """Compute standard metrics from a return series."""
    if not returns:
        return {
            "total_return_pct": 0,
            "sharpe": 0,
            "max_dd_pct": 0,
            "win_rate": 0,
            "trade_count": 0,
            "profit_factor": 0,
        }

    equity = _equity_from_returns(returns, initial)
    total_return = (equity[-1] - initial) / initial * 100
    sharpe = _compute_sharpe(returns)
    max_dd = _compute_max_drawdown_pct(equity)
    win_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0

    wins = [r for r in returns if r > 0]
    losses = [abs(r) for r in returns if r < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 1e-10
    profit_factor = (sum(wins) / sum(losses)) if losses else float("inf")

    return {
        "total_return_pct": round(total_return, 2),
        "sharpe": round(sharpe, 3),
        "max_dd_pct": round(max_dd, 2),
        "win_rate": round(win_rate, 3),
        "trade_count": len(returns),
        "profit_factor": round(profit_factor, 3)
        if profit_factor != float("inf")
        else 999.0,
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
    }


def _generate_strategy_configs() -> list[StrategyConfig]:
    """Generate a diverse set of strategy configurations."""
    return [
        StrategyConfig(
            name="trend_fast",
            ema_fast=10,
            ema_mid=30,
            ema_slow=100,
            rsi_oversold=30,
            rsi_overbought=70,
            atr_mult_sl=1.5,
            atr_mult_tp=2.0,
        ),
        StrategyConfig(
            name="trend_standard",
            ema_fast=20,
            ema_mid=50,
            ema_slow=200,
            rsi_oversold=35,
            rsi_overbought=65,
            atr_mult_sl=2.0,
            atr_mult_tp=2.0,
        ),
        StrategyConfig(
            name="trend_slow",
            ema_fast=30,
            ema_mid=80,
            ema_slow=200,
            rsi_oversold=40,
            rsi_overbought=60,
            atr_mult_sl=2.5,
            atr_mult_tp=3.0,
        ),
        StrategyConfig(
            name="mean_revert",
            ema_fast=10,
            ema_mid=20,
            ema_slow=50,
            rsi_oversold=25,
            rsi_overbought=75,
            atr_mult_sl=1.0,
            atr_mult_tp=1.5,
        ),
        StrategyConfig(
            name="breakout",
            ema_fast=20,
            ema_mid=50,
            ema_slow=200,
            rsi_oversold=20,
            rsi_overbought=80,
            atr_mult_sl=3.0,
            atr_mult_tp=3.0,
        ),
        StrategyConfig(
            name="conservative",
            ema_fast=20,
            ema_mid=50,
            ema_slow=200,
            rsi_oversold=30,
            rsi_overbought=70,
            atr_mult_sl=1.5,
            atr_mult_tp=2.5,
        ),
    ]


def _label_regimes_simple(closes: list[float], window: int = 20) -> list[str]:
    """Simple regime labeling from price data (inline, no external dependency)."""
    labels = []
    for i in range(len(closes)):
        if i < window:
            labels.append("SIDEWAYS")
            continue

        # Compute returns over window
        w_returns = [
            (closes[j] - closes[j - 1]) / closes[j - 1]
            for j in range(max(1, i - window + 1), i + 1)
        ]
        mean_r = sum(w_returns) / len(w_returns)
        std_r = (sum((r - mean_r) ** 2 for r in w_returns) / len(w_returns)) ** 0.5

        # ATR-like volatility
        vol = std_r

        if vol > 0.03:
            labels.append("VOLATILE")
        elif mean_r > 0.001:
            labels.append("BULL")
        elif mean_r < -0.001:
            labels.append("BEAR")
        else:
            labels.append("SIDEWAYS")

    return labels


def compute_ensemble(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    volumes: list[float] | None = None,
    strategy_configs: list[dict] | None = None,
    initial_capital: float = 10000.0,
) -> EnsembleResult:
    """Compute regime-aware ensemble strategy composition.

    Args:
        closes: Close prices
        highs: High prices
        lows: Low prices
        volumes: Optional volume data
        strategy_configs: Optional custom strategy configs
        initial_capital: Starting capital

    Returns:
        EnsembleResult with regime-strategy mapping and ensemble metrics
    """
    if len(closes) < 210:  # need enough for EMA200 + warmup
        return EnsembleResult(
            strategies_tested=0,
            regimes_detected=[],
            regime_strategy_map={},
            strategy_performances=[],
            ensemble_metrics={},
            baseline_metrics={},
            improvement={},
            recommendations=["Insufficient data — need 210+ bars"],
        )

    # Generate configs
    if strategy_configs:
        configs = [StrategyConfig(**c) for c in strategy_configs]
    else:
        configs = _generate_strategy_configs()

    # Label regimes
    regime_labels = _label_regimes_simple(closes, window=20)
    unique_regimes = sorted(set(regime_labels))

    # For each strategy, simulate trades and compute per-regime performance
    strategy_regime_returns: dict[str, dict[str, list[float]]] = {}
    strategy_all_returns: dict[str, list[tuple[int, float]]] = {}

    for cfg in configs:
        # Simulate this strategy on the data
        trades = _simulate_strategy(closes, highs, lows, cfg)
        strategy_all_returns[cfg.name] = trades

        # Label each trade's regime (use the regime at trade entry)
        regime_returns: dict[str, list[float]] = {r: [] for r in unique_regimes}
        for i, (trade_idx, trade_return) in enumerate(trades):
            # Map trade index to regime
            if trade_idx < len(regime_labels):
                regime = regime_labels[trade_idx]
            else:
                regime = "SIDEWAYS"
            regime_returns[regime].append(trade_return)

        strategy_regime_returns[cfg.name] = regime_returns

    # Compute per-strategy, per-regime performance
    all_performances = []
    for cfg in configs:
        for regime in unique_regimes:
            rets = strategy_regime_returns.get(cfg.name, {}).get(regime, [])
            if not rets:
                continue
            sharpe = _compute_sharpe(rets)
            perf = StrategyPerformance(
                strategy_name=cfg.name,
                regime=regime,
                trade_count=len(rets),
                avg_return=round(sum(rets) / len(rets), 4),
                win_rate=round(sum(1 for r in rets if r > 0) / len(rets), 3),
                sharpe=round(sharpe, 3),
            )
            all_performances.append(perf)

    # Optimal regime-to-strategy mapping (greedy: best sharpe per regime)
    regime_strategy_map = {}
    for regime in unique_regimes:
        regime_perfs = [
            p for p in all_performances if p.regime == regime and p.trade_count >= 3
        ]
        if not regime_perfs:
            regime_strategy_map[regime] = {
                "strategy": "none",
                "reason": "No strategy has enough trades in this regime",
            }
            continue

        # Best by sharpe, fallback to avg_return
        best = max(
            regime_perfs, key=lambda p: p.sharpe if p.sharpe != 0 else p.avg_return
        )
        regime_strategy_map[regime] = {
            "strategy": best.strategy_name,
            "avg_return": best.avg_return,
            "win_rate": best.win_rate,
            "sharpe": best.sharpe,
            "trade_count": best.trade_count,
            "reason": f"Best Sharpe ({best.sharpe}) in {regime} regime",
        }

    # Compose ensemble returns by regime-switching
    ensemble_returns = []
    for i, (trade_idx, trade_return) in enumerate(
        _simulate_strategy(
            closes, highs, lows, configs[0]
        )  # use trade indices from first strategy
    ):
        regime = (
            regime_labels[trade_idx] if trade_idx < len(regime_labels) else "SIDEWAYS"
        )
        chosen = regime_strategy_map.get(regime, {})
        chosen_strategy = chosen.get("strategy", configs[0].name)

        # Find the return from the chosen strategy for this trade
        # (simplified: use the strategy's returns at same index)
        strat_returns = strategy_all_returns.get(chosen_strategy, [])
        if i < len(strat_returns):
            ensemble_returns.append(strat_returns[i][1])  # (idx, return) tuple

    # Compute metrics
    ensemble_metrics = _metrics_from_returns(ensemble_returns, initial_capital)

    # Baseline = best single strategy by sharpe
    best_single_name = ""
    best_single_sharpe = -999
    for name, rets in strategy_all_returns.items():
        s = _compute_sharpe([r[1] for r in rets])
        if s > best_single_sharpe:
            best_single_sharpe = s
            best_single_name = name

    baseline_returns = [r[1] for r in strategy_all_returns.get(best_single_name, [])]
    baseline_metrics = _metrics_from_returns(baseline_returns, initial_capital)
    baseline_info: dict[str, Any] = dict(baseline_metrics)
    baseline_info["strategy_name"] = best_single_name

    # Improvement
    improvement = {
        "sharpe_delta": round(
            ensemble_metrics["sharpe"] - baseline_metrics["sharpe"], 3
        ),
        "return_delta": round(
            ensemble_metrics["total_return_pct"] - baseline_metrics["total_return_pct"],
            2,
        ),
        "dd_delta": round(
            ensemble_metrics["max_dd_pct"] - baseline_metrics["max_dd_pct"], 2
        ),
    }

    # Recommendations
    recommendations = []
    if improvement["sharpe_delta"] > 0.1:
        recommendations.append(
            f"Ensemble improves Sharpe by {improvement['sharpe_delta']} over {best_single_name}"
        )
    if improvement["dd_delta"] < -1:
        recommendations.append(
            f"Ensemble reduces max drawdown by {abs(improvement['dd_delta'])}%"
        )
    if not recommendations:
        recommendations.append(
            "Ensemble shows marginal improvement — consider more diverse strategies"
        )

    return EnsembleResult(
        strategies_tested=len(configs),
        regimes_detected=unique_regimes,
        regime_strategy_map=regime_strategy_map,
        strategy_performances=[
            {
                "strategy": p.strategy_name,
                "regime": p.regime,
                "trades": p.trade_count,
                "avg_return": p.avg_return,
                "win_rate": p.win_rate,
                "sharpe": p.sharpe,
            }
            for p in all_performances
        ],
        ensemble_metrics=ensemble_metrics,
        baseline_metrics=baseline_info,
        improvement=improvement,
        recommendations=recommendations,
    )


def _simulate_strategy(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    cfg: StrategyConfig,
) -> list[tuple[int, float]]:
    """Simulate a strategy on OHLCV data. Returns list of (bar_index, return%).

    Simplified backtest: EMA crossover + RSI filter + ATR-based SL/TP.
    """
    n = len(closes)
    if n < cfg.ema_slow + 10:
        return []

    # Compute EMAs
    def _ema(data: list[float], period: int) -> list[float]:
        if len(data) < period:
            return []
        k = 2 / (period + 1)
        result = [sum(data[:period]) / period]
        for val in data[period:]:
            result.append(val * k + result[-1] * (1 - k))
        return result

    ema_fast = _ema(closes, cfg.ema_fast)
    ema_mid = _ema(closes, cfg.ema_mid)
    ema_slow = _ema(closes, cfg.ema_slow)

    # Compute RSI
    def _rsi(closes: list[float], period: int) -> list[float]:
        if len(closes) < period + 1:
            return []
        deltas = [closes[i + 1] - closes[i] for i in range(len(closes) - 1)]
        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        result = []
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                result.append(100 - (100 / (1 + avg_gain / avg_loss)))
        return result

    rsi_vals = _rsi(closes, cfg.rsi_period)

    # Compute ATR
    def _atr(highs, lows, closes, period=14):
        n = len(closes)
        if n < period + 1:
            return []
        trs = []
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            trs.append(tr)
        if len(trs) < period:
            return []
        result = [sum(trs[:period]) / period]
        for i in range(period, len(trs)):
            result.append((result[-1] * (period - 1) + trs[i]) / period)
        return result

    atr_vals = _atr(highs, lows, closes)

    # Align offsets
    ef_off = len(closes) - len(ema_fast)
    em_off = len(closes) - len(ema_mid)
    es_off = len(closes) - len(ema_slow)
    rsi_off = len(closes) - len(rsi_vals) - 1
    atr_off = len(closes) - len(atr_vals)

    trades = []
    in_trade = False
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0

    warmup = cfg.ema_slow + 10

    for i in range(warmup, n):
        # Get indicator values at this bar
        ef = (
            ema_fast[i - ef_off]
            if i - ef_off >= 0 and i - ef_off < len(ema_fast)
            else 0
        )
        em = ema_mid[i - em_off] if i - em_off >= 0 and i - em_off < len(ema_mid) else 0
        es = (
            ema_slow[i - es_off]
            if i - es_off >= 0 and i - es_off < len(ema_slow)
            else 0
        )
        rsi = (
            rsi_vals[i - rsi_off - 1]
            if i - rsi_off - 1 >= 0 and i - rsi_off - 1 < len(rsi_vals)
            else 50
        )
        atr = (
            atr_vals[i - atr_off]
            if i - atr_off >= 0 and i - atr_off < len(atr_vals)
            else 0
        )

        if ef == 0 or em == 0 or es == 0:
            continue

        price = closes[i]

        if in_trade:
            # Check SL/TP
            if price <= stop_loss or price >= take_profit:
                ret = (price - entry_price) / entry_price
                trades.append((i, ret))
                in_trade = False
        else:
            # Entry: EMA crossover + RSI filter
            if ef > em and em > es and rsi < cfg.rsi_overbought:
                # BUY signal
                in_trade = True
                entry_price = price
                stop_loss = price - cfg.atr_mult_sl * atr
                take_profit = price + cfg.atr_mult_tp * atr

    # Close any open trade at end
    if in_trade:
        ret = (closes[-1] - entry_price) / entry_price
        trades.append((n - 1, ret))

    return trades
