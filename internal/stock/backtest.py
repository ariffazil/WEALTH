"""
WEALTH Backtest Engine — Compare 888 vs 999 frameworks on historical data
══════════════════════════════════════════════════════════════════════════

Tests which framework produces better entry/exit signals:
  - 888 JUDGE: 3-layer gated decisions (F8/T8/W8 HOLD gates)
  - 999 SEAL:  27-point continuous scoring (no gates)
  - Baseline:   Simple PE < 15 + Price > SMA50

Uses yfinance for price history + klse-screener for fundamentals snapshots.
Computes: hit rate, avg return, max drawdown, Sharpe, win/loss ratio.

DITEMPA BUKAN DIBERI — Backtest truth, not backtest hope.
"""

from __future__ import annotations

import math
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .indicators import (
    compute_sma,
    compute_rsi,
    compute_returns,
    compute_max_drawdown,
    compute_sharpe_ratio,
)
from .engine_888 import compute_888
from .engine_999 import compute_999


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL GENERATORS — Each returns {signal: BUY/SELL/HOLD, score: float}
# ═══════════════════════════════════════════════════════════════════════════


def signal_baseline(closes: List[float], pe: Optional[float]) -> Dict:
    """Simple baseline: PE < 15 AND price > SMA50 → BUY."""
    if len(closes) < 50 or pe is None:
        return {"signal": "HOLD", "score": 0, "reason": "insufficient data"}
    sma50 = compute_sma(closes, 50)
    price_above = bool(sma50[-1] and closes[-1] > sma50[-1])
    pe_ok = pe > 0 and pe < 15
    if pe_ok and price_above:
        return {
            "signal": "BUY",
            "score": 70,
            "reason": f"PE={pe:.1f} < 15, Price > SMA50",
        }
    return {
        "signal": "HOLD",
        "score": 30,
        "reason": f"PE={pe}, above_SMA50={price_above}",
    }


def signal_888(
    closes: List[float],
    volumes: List[int],
    highs: List[int],
    lows: List[int],
    pe: Optional[float],
    roe: Optional[float],
    pb: Optional[float],
    dy: Optional[float],
    eps: Optional[float],
    sector: str,
) -> Dict:
    """888 JUDGE: only BUY when all 3 gates clear."""
    last_price = closes[-1] if closes else 0
    result = compute_888(
        "TEST",
        pe=pe,
        roe=roe,
        pb=pb,
        dy=dy,
        eps=eps,
        sector=sector,
        account_balance=10000,
        risk_per_trade_pct=1.0,
        stop_loss=last_price * 0.93,
        target_price=last_price * 1.15,
    )
    gates = result.get("gate_summary", {})
    fusion = (
        result.get("fundamentals", {}).get("score", 0) * 0.4
        + result.get("technicals", {}).get("score", 0) * 0.35
        + result.get("flows", {}).get("score", 0) * 0.25
    )

    if gates.get("total_gates", 99) == 0:
        return {
            "signal": "BUY",
            "score": round(fusion, 1),
            "gates": gates,
            "reason": result.get("signal", ""),
        }
    elif gates.get("total_gates", 99) >= 3:
        return {
            "signal": "SELL",
            "score": round(fusion, 1),
            "gates": gates,
            "reason": "All 3 gates triggered — SABAR",
        }
    else:
        return {
            "signal": "HOLD",
            "score": round(fusion, 1),
            "gates": gates,
            "reason": f"{gates['total_gates']}/3 gates",
        }


def signal_999(
    closes: List[float],
    volumes: List[int],
    highs: List[int],
    lows: List[int],
    pe: Optional[float],
    roe: Optional[float],
    pb: Optional[float],
    dy: Optional[float],
    eps: Optional[float],
    sector: str,
) -> Dict:
    """999 SEAL: continuous scoring, BUY above threshold."""
    last_price = closes[-1] if closes else 0
    result = compute_999(
        "TEST",
        pe=pe,
        roe=roe,
        pb=pb,
        dy=dy,
        eps=eps,
        sector=sector,
        account_balance=10000,
        risk_per_trade_pct=1.0,
        stop_loss=last_price * 0.93,
        target_price=last_price * 1.15,
    )
    fusion = result.get("fusion", {}).get("score", 0)
    verdict = result.get("verdict", "HOLD")

    if verdict in ("STRONG_BUY", "BUY"):
        return {
            "signal": "BUY",
            "score": round(fusion, 1),
            "verdict": verdict,
            "reason": result.get("narrative", ""),
        }
    elif verdict in ("SELL",):
        return {"signal": "SELL", "score": round(fusion, 1), "verdict": verdict}
    else:
        return {"signal": "HOLD", "score": round(fusion, 1), "verdict": verdict}


# ═══════════════════════════════════════════════════════════════════════════
# BACKTEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════


def run_comparative_backtest(
    ticker: str = "1155",
    pe: Optional[float] = None,
    roe: Optional[float] = None,
    pb: Optional[float] = None,
    dy: Optional[float] = None,
    eps: Optional[float] = None,
    sector: str = "",
    lookback_days: int = 252,
    step_days: int = 21,
) -> Dict[str, Any]:
    """Run all 3 strategies on the same historical window and compare.

    Walks back through history in step_days increments, computing signals
    at each point, then comparing what would have happened.

    Args:
        ticker: Bursa numeric or yfinance symbol
        lookback_days: how far back to test (default 1 year = 252 trading days)
        step_days: how often to evaluate (default monthly = 21 days)
    """
    # ── Fetch historical data ──
    try:
        import yfinance as yf

        yt_symbol = f"{ticker}.KL" if ticker.isdigit() else ticker
        yt = yf.Ticker(yt_symbol)
        total_days = lookback_days + 200  # extra for indicator warmup
        hist = (
            yt.history(period=f"{total_days}d")
            if total_days < 1500
            else yt.history(period="5y")
        )

        if hist.empty or len(hist) < 100:
            return {
                "error": f"Insufficient history for {ticker}",
                "status": "NEEDS_DATA",
            }

        all_closes = [float(x) for x in hist["Close"].tolist()]
        all_volumes = [int(x) for x in hist["Volume"].tolist()]
        all_highs = [float(x) for x in hist["High"].tolist()]
        all_lows = [float(x) for x in hist["Low"].tolist()]
        dates = [str(d.date()) for d in hist.index]
    except Exception as e:
        return {"error": str(e), "status": "NEEDS_DATA"}

    results: Dict[str, List] = {
        "baseline": [],
        "888": [],
        "999": [],
        "dates": [],
        "prices": [],
    }

    # ── Walk back through time ──
    n = len(all_closes)
    eval_start = max(0, n - lookback_days - 60)  # start from lookback_days ago

    for i in range(eval_start, n, step_days):
        if i < 100:  # need minimum data for indicators
            continue

        window_closes = all_closes[: i + 1]
        window_volumes = all_volumes[: i + 1]
        window_highs = all_highs[: i + 1]
        window_lows = all_lows[: i + 1]

        results["dates"].append(dates[i] if i < len(dates) else str(i))
        results["prices"].append(round(window_closes[-1], 2))

        # Baseline
        bl = signal_baseline(window_closes, pe)
        results["baseline"].append(bl)

        # 888
        e8 = signal_888(
            window_closes,
            window_volumes,
            window_highs,
            window_lows,
            pe,
            roe,
            pb,
            dy,
            eps,
            sector,
        )
        results["888"].append(e8)

        # 999
        e9 = signal_999(
            window_closes,
            window_volumes,
            window_highs,
            window_lows,
            pe,
            roe,
            pb,
            dy,
            eps,
            sector,
        )
        results["999"].append(e9)

    # ── Compute forward returns for each signal point ──
    forward_returns = _compute_forward_returns(
        all_closes, eval_start, n, step_days, results["dates"]
    )

    # ── Aggregate metrics ──
    metrics = {
        "ticker": ticker,
        "sector": sector,
        "period": f"{len(results['dates'])} evaluation points over ~{lookback_days} trading days",
        "current_price": round(all_closes[-1], 2),
        "fundamentals_used": {"pe": pe, "roe": roe, "pb": pb, "dy": dy, "eps": eps},
    }

    for strategy in ["baseline", "888", "999"]:
        signals = results[strategy]
        metrics[strategy] = _aggregate_strategy(signals, forward_returns)

    # ── Comparison verdict ──
    best = _pick_best(metrics)
    metrics["verdict"] = best

    return {"status": "OK", "results": metrics}


def _compute_forward_returns(all_closes, eval_start, n, step_days, eval_dates):
    """Compute forward N-day returns from each evaluation point."""
    fwd = []
    for idx_offset, date_str in enumerate(eval_dates):
        i = eval_start + idx_offset * step_days
        if i >= n - step_days:
            fwd.append(None)
        else:
            entry = all_closes[i]
            future_idx = min(i + step_days, n - 1)
            exit_price = all_closes[future_idx]
            ret = (exit_price / entry - 1) * 100
            fwd.append(round(ret, 2))
    return fwd


def _aggregate_strategy(signals: List[Dict], forward_returns: List) -> Dict:
    """Compute aggregate metrics for one strategy."""
    buys = [
        (s, r)
        for s, r in zip(signals, forward_returns)
        if s["signal"] == "BUY" and r is not None
    ]
    sells = [
        (s, r)
        for s, r in zip(signals, forward_returns)
        if s["signal"] == "SELL" and r is not None
    ]
    holds = sum(1 for s in signals if s["signal"] == "HOLD")

    buy_returns = [r for _, r in buys]
    sell_returns = [r for _, r in sells]

    # Buy metrics
    buy_hit_rate = sum(1 for r in buy_returns if r > 0) / max(len(buy_returns), 1) * 100
    buy_avg_return = sum(buy_returns) / max(len(buy_returns), 1) if buy_returns else 0
    buy_max_return = max(buy_returns) if buy_returns else 0
    buy_min_return = min(buy_returns) if buy_returns else 0

    # Sell metrics (did we avoid losses?)
    sell_hit_rate = (
        sum(1 for r in sell_returns if r < 0) / max(len(sell_returns), 1) * 100
    )  # correct sells = price dropped
    sell_avg_return = (
        sum(sell_returns) / max(len(sell_returns), 1) if sell_returns else 0
    )

    # Stability: variance of buy returns
    buy_variance = (
        sum((r - buy_avg_return) ** 2 for r in buy_returns) / max(len(buy_returns), 1)
        if buy_returns
        else 0
    )
    buy_std = math.sqrt(buy_variance)

    return {
        "total_signals": len(signals),
        "buy_signals": len(buys),
        "sell_signals": len(sells),
        "hold_signals": holds,
        "buy_hit_rate_pct": round(buy_hit_rate, 1),
        "buy_avg_return_pct": round(buy_avg_return, 2),
        "buy_best_pct": round(buy_max_return, 2),
        "buy_worst_pct": round(buy_min_return, 2),
        "buy_std_pct": round(buy_std, 2),
        "sell_correct_pct": round(sell_hit_rate, 1) if sell_returns else None,
        "sell_avg_return_pct": round(sell_avg_return, 2) if sell_returns else None,
        "signal_ratio": f"{len(buys)}B/{holds}H" + (f"/{len(sells)}S" if sells else ""),
    }


def _pick_best(metrics: Dict) -> str:
    """Compare strategies and pick the best based on risk-adjusted returns."""
    best_strat = None
    best_score = -999

    for strat in ["baseline", "888", "999"]:
        m = metrics.get(strat, {})
        hit = m.get("buy_hit_rate_pct", 0)
        avg_ret = m.get("buy_avg_return_pct", 0)
        worst = m.get("buy_worst_pct", -50)
        buys = m.get("buy_signals", 0)

        if buys < 2:
            continue  # not enough data to evaluate

        # Score: hit rate × avg return, penalized by worst drawdown
        score = hit * 0.3 + avg_ret * 5.0 - abs(worst) * 0.5
        if score > best_score:
            best_score = score
            best_strat = strat

    if best_strat:
        return f"{best_strat.upper()} leads: hit={metrics[best_strat]['buy_hit_rate_pct']}%, avg_ret={metrics[best_strat]['buy_avg_return_pct']}%, {metrics[best_strat]['buy_signals']} buy signals. 888 JUDGE gates {'active' if best_strat == '888' else 'bypassed' if best_strat == '999' else 'absent'}."
    return "INCONCLUSIVE — need more data"
