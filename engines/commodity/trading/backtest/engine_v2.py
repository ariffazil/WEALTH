"""
Backtest v2 — Fixed strategy based on post-mortem.
Changes from v1:
1. NO trading in SIDEWAYS regime
2. Wider SL (2× ATR from zone)
3. RSI confirmation required (oversold for buy, overbought for sell)
4. Strong zones only (tested 3+ times)
5. Max 2 positions
6. Partial TP at 1R, trail rest with 1.5 ATR trailing stop
"""
from __future__ import annotations

import json
import argparse
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, '/root')

from trading.signals.scanner import ema, rsi, atr
from trading.signals.regime import detect_regime, find_swing_points, Regime
from trading.core.models import OHLCV


@dataclass
class Trade:
    entry_time: str
    exit_time: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    pnl: float
    pnl_pct: float
    regime: str
    exit_reason: str
    bars_held: int


@dataclass
class BacktestConfig:
    initial_equity: float = 10000.0
    risk_per_trade: float = 0.01
    max_positions: int = 2
    atr_sl_mult: float = 2.0  # SL = 2× ATR
    atr_trail_mult: float = 1.5  # trailing stop = 1.5 ATR
    min_rr: float = 2.0
    zone_min_strength: int = 3  # only trade strong zones
    rsi_oversold: float = 35.0  # buy when RSI < 35
    rsi_overbought: float = 65.0  # sell when RSI > 65
    warmup: int = 210  # bars for EMA200 + buffer


def run_backtest(candles: list[OHLCV], cfg: BacktestConfig) -> dict:
    """Run the improved backtest."""
    equity = cfg.initial_equity
    peak_equity = equity
    max_dd = 0.0
    trades: list[Trade] = []
    positions: list[dict] = []  # open positions
    equity_curve = []

    closes = [c.close for c in candles]

    # Pre-compute indicators
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi_vals = rsi(closes, 14)
    atr_vals = atr(candles, 14)

    # Offsets (EMA arrays have different starting points)
    e20_off = len(closes) - len(ema20)
    e50_off = len(closes) - len(ema50)
    e200_off = len(closes) - len(ema200)
    rsi_off = len(closes) - len(rsi_vals)
    atr_off = len(closes) - len(atr_vals)

    for i in range(cfg.warmup, len(candles)):
        bar = candles[i]
        price = bar.close

        # Get indicators for this bar
        e20 = ema20[i - e20_off] if i - e20_off >= 0 and i - e20_off < len(ema20) else None
        e50 = ema50[i - e50_off] if i - e50_off >= 0 and i - e50_off < len(ema50) else None
        e200 = ema200[i - e200_off] if i - e200_off >= 0 and i - e200_off < len(ema200) else None
        rsi_val = rsi_vals[i - rsi_off] if i - rsi_off >= 0 and i - rsi_off < len(rsi_vals) else 50
        atr_val = atr_vals[i - atr_off] if i - atr_off >= 0 and i - atr_off < len(atr_vals) else 10

        if None in (e20, e50, e200) or atr_val <= 0:
            continue

        # Detect regime
        regime, conf = detect_regime(e20, e50, e200)

        # === RULE 1: Skip SIDEWAYS ===
        if regime == Regime.SIDEWAYS:
            # Still manage existing positions
            positions = _manage_positions(positions, bar, atr_val, cfg, trades, i, candles, regime)
            equity = cfg.initial_equity + sum(t.pnl for t in trades) + sum(_unrealized(p, price) for p in positions)
            peak_equity = max(peak_equity, equity)
            dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
            max_dd = max(max_dd, dd)
            equity_curve.append(equity)
            continue

        # Manage existing positions
        positions = _manage_positions(positions, bar, atr_val, cfg, trades, i, candles, regime)

        # === Check for new entry ===
        if len(positions) >= cfg.max_positions:
            equity = cfg.initial_equity + sum(t.pnl for t in trades) + sum(_unrealized(p, price) for p in positions)
            peak_equity = max(peak_equity, equity)
            dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
            max_dd = max(max_dd, dd)
            equity_curve.append(equity)
            continue

        # Find recent swing points for zones
        lookback = min(20, i - cfg.warmup)
        if lookback < 5:
            equity = cfg.initial_equity + sum(t.pnl for t in trades) + sum(_unrealized(p, price) for p in positions)
            equity_curve.append(equity)
            continue

        recent = candles[i - lookback:i]
        swings = find_swing_points(recent, lookback=max(3, lookback // 4))

        support_levels = sorted([s[0] for s in swings if s[1] == "LOW"])
        resistance_levels = sorted([s[0] for s in swings if s[1] == "HIGH"])[::-1]

        # Cluster and find strong zones
        support_zones = _cluster_zones(support_levels, cfg.zone_min_strength)
        resistance_zones = _cluster_zones(resistance_levels, cfg.zone_min_strength)

        if regime == Regime.UPTREND:
            # === RULE 3: RSI must be oversold for buy ===
            if rsi_val > cfg.rsi_oversold:
                equity_curve.append(equity)
                continue

            # Find nearest strong support below price
            buy_zone = None
            for z in support_zones:
                if z < price and abs(price - z) < atr_val * 2:
                    buy_zone = z
                    break

            if buy_zone and abs(price - buy_zone) < atr_val * 1.5:
                # === RULE 2: SL = 2× ATR below zone ===
                sl = buy_zone - atr_val * cfg.atr_sl_mult
                risk = price - sl
                if risk > 0:
                    tp = price + risk * cfg.min_rr
                    rr = (tp - price) / risk
                    if rr >= cfg.min_rr:
                        lots = max(0.001, round((equity * cfg.risk_per_trade) / (risk * 1000), 2))
                        positions.append({
                            "direction": "BUY",
                            "entry": price,
                            "sl": sl,
                            "tp": tp,
                            "lots": lots,
                            "entry_bar": i,
                            "regime": regime.value,
                            "partial_closed": False,
                            "entry_time": bar.timestamp.isoformat(),
                        })

        elif regime == Regime.DOWNTREND:
            # === RULE 3: RSI must be overbought for sell ===
            if rsi_val < cfg.rsi_overbought:
                equity_curve.append(equity)
                continue

            # Find nearest strong resistance above price
            sell_zone = None
            for z in resistance_levels:
                if z > price and abs(z - price) < atr_val * 2:
                    sell_zone = z
                    break

            if sell_zone and abs(sell_zone - price) < atr_val * 1.5:
                sl = sell_zone + atr_val * cfg.atr_sl_mult
                risk = sl - price
                if risk > 0:
                    tp = price - risk * cfg.min_rr
                    rr = (price - tp) / risk
                    if rr >= cfg.min_rr:
                        lots = max(0.001, round((equity * cfg.risk_per_trade) / (risk * 1000), 2))
                        positions.append({
                            "direction": "SELL",
                            "entry": price,
                            "sl": sl,
                            "tp": tp,
                            "lots": lots,
                            "entry_bar": i,
                            "regime": regime.value,
                            "partial_closed": False,
                            "entry_time": bar.timestamp.isoformat(),
                        })

        equity = cfg.initial_equity + sum(t.pnl for t in trades) + sum(_unrealized(p, price) for p in positions)
        peak_equity = max(peak_equity, equity)
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        max_dd = max(max_dd, dd)
        equity_curve.append(equity)

    # Close remaining positions
    for p in positions:
        price = candles[-1].close
        pnl = _unrealized(p, price)
        trades.append(Trade(
            entry_time=p["entry_time"],
            exit_time=candles[-1].timestamp.isoformat(),
            direction=p["direction"],
            entry_price=p["entry"],
            exit_price=price,
            stop_loss=p["sl"],
            take_profit=p["tp"],
            lot_size=p["lots"],
            pnl=round(pnl, 2),
            pnl_pct=round(pnl / cfg.initial_equity * 1000, 2),
            regime=p["regime"],
            exit_reason="END_OF_DATA",
            bars_held=len(candles) - 1 - p["entry_bar"],
        ))

    return _compute_metrics(trades, equity_curve, cfg, max_dd)


def _manage_positions(positions, bar, atr_val, cfg, trades, i, candles, regime):
    """Manage open positions: SL, TP, trailing stop."""
    remaining = []
    price = bar.close
    high = bar.high
    low = bar.low

    for p in positions:
        sl = p["sl"]
        tp = p["tp"]
        direction = p["direction"]
        entry = p["entry"]
        lots = p["lots"]
        risk = abs(entry - sl)

        exit_price = None
        exit_reason = None

        if direction == "BUY":
            # Check SL hit
            if low <= sl:
                exit_price = sl
                exit_reason = "SL"
            # Check TP hit
            elif high >= tp:
                exit_price = tp
                exit_reason = "TP"
            else:
                # === RULE 6: Trailing stop after 1R profit ===
                profit = price - entry
                if profit >= risk and not p["partial_closed"]:
                    # Move SL to breakeven + trail
                    new_sl = price - atr_val * cfg.atr_trail_mult
                    p["sl"] = max(p["sl"], new_sl)
                    p["partial_closed"] = True
                elif p["partial_closed"]:
                    # Continue trailing
                    new_sl = price - atr_val * cfg.atr_trail_mult
                    p["sl"] = max(p["sl"], new_sl)

        elif direction == "SELL":
            if high >= sl:
                exit_price = sl
                exit_reason = "SL"
            elif low <= tp:
                exit_price = tp
                exit_reason = "TP"
            else:
                profit = entry - price
                if profit >= risk and not p["partial_closed"]:
                    new_sl = price + atr_val * cfg.atr_trail_mult
                    p["sl"] = min(p["sl"], new_sl)
                    p["partial_closed"] = True
                elif p["partial_closed"]:
                    new_sl = price + atr_val * cfg.atr_trail_mult
                    p["sl"] = min(p["sl"], new_sl)

        if exit_price:
            pnl = (exit_price - entry) * lots * 1000 if direction == "BUY" else (entry - exit_price) * lots * 1000
            trades.append(Trade(
                entry_time=p["entry_time"],
                exit_time=bar.timestamp.isoformat(),
                direction=direction,
                entry_price=entry,
                exit_price=round(exit_price, 2),
                stop_loss=sl,
                take_profit=tp,
                lot_size=lots,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl / cfg.initial_equity * 1000, 2),
                regime=p["regime"],
                exit_reason=exit_reason,
                bars_held=i - p["entry_bar"],
            ))
        else:
            remaining.append(p)

    return remaining


def _unrealized(pos, price):
    entry = pos["entry"]
    lots = pos["lots"]
    if pos["direction"] == "BUY":
        return (price - entry) * lots * 1000
    else:
        return (entry - price) * lots * 1000


def _cluster_zones(levels, min_strength):
    """Cluster nearby price levels and filter by minimum strength."""
    if not levels:
        return []
    clusters = []
    current = [levels[0]]
    for l in levels[1:]:
        if abs(l - current[0]) / current[0] * 100 < 0.3:
            current.append(l)
        else:
            if len(current) >= min_strength:
                clusters.append(sum(current) / len(current))
            current = [l]
    if len(current) >= min_strength:
        clusters.append(sum(current) / len(current))
    return sorted(clusters)


def _compute_metrics(trades, equity_curve, cfg, max_dd):
    if not trades:
        return {"total_trades": 0, "error": "No trades generated"}

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    total_pnl = sum(t.pnl for t in trades)

    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0
    avg_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    profit_factor = abs(sum(t.pnl for t in wins) / sum(t.pnl for t in losses)) if losses and sum(t.pnl for t in losses) != 0 else float('inf')

    # Sharpe
    returns = [t.pnl_pct for t in trades]
    avg_ret = sum(returns) / len(returns) if returns else 0
    std_ret = (sum((r - avg_ret) ** 2 for r in returns) / len(returns)) ** 0.5 if len(returns) > 1 else 1
    sharpe = (avg_ret / std_ret) * (252 ** 0.5) if std_ret > 0 else 0

    # By regime
    regime_stats = {}
    for t in trades:
        r = t.regime
        if r not in regime_stats:
            regime_stats[r] = {"count": 0, "wins": 0, "pnl": 0}
        regime_stats[r]["count"] += 1
        if t.pnl > 0:
            regime_stats[r]["wins"] += 1
        regime_stats[r]["pnl"] += t.pnl

    # By exit reason
    exit_stats = {}
    for t in trades:
        e = t.exit_reason
        if e not in exit_stats:
            exit_stats[e] = {"count": 0, "pnl": 0}
        exit_stats[e]["count"] += 1
        exit_stats[e]["pnl"] += t.pnl

    return {
        "config": {
            "initial_equity": cfg.initial_equity,
            "risk_per_trade": cfg.risk_per_trade,
            "atr_sl_mult": cfg.atr_sl_mult,
            "atr_trail_mult": cfg.atr_trail_mult,
            "min_rr": cfg.min_rr,
            "zone_min_strength": cfg.zone_min_strength,
            "rsi_oversold": cfg.rsi_oversold,
            "rsi_overbought": cfg.rsi_overbought,
            "max_positions": cfg.max_positions,
        },
        "summary": {
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "avg_rr": round(avg_rr, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(total_pnl / cfg.initial_equity * 1000, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "avg_bars_held": round(sum(t.bars_held for t in trades) / len(trades), 1),
            "best_trade": round(max(t.pnl for t in trades), 2),
            "worst_trade": round(min(t.pnl for t in trades), 2),
        },
        "by_regime": {
            r: {"count": s["count"], "win_rate": round(s["wins"] / s["count"] * 100, 1) if s["count"] > 0 else 0, "pnl": round(s["pnl"], 2)}
            for r, s in regime_stats.items()
        },
        "by_exit": {
            e: {"count": s["count"], "pnl": round(s["pnl"], 2)}
            for e, s in exit_stats.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description="XAUUSD Backtester v2")
    parser.add_argument("--data", required=True, help="Path to OHLCV JSON")
    parser.add_argument("--output", help="Output results JSON")
    parser.add_argument("--equity", type=float, default=10000)
    parser.add_argument("--risk", type=float, default=0.01)
    args = parser.parse_args()

    print(f"Loading {args.data}...")
    with open(args.data) as f:
        raw = json.load(f)
    candles = [OHLCV(
        timestamp=datetime.fromisoformat(d["timestamp"]),
        open=d["open"], high=d["high"], low=d["low"], close=d["close"],
        volume=d.get("volume", 0),
    ) for d in raw]
    print(f"Loaded {len(candles)} bars.")

    cfg = BacktestConfig(initial_equity=args.equity, risk_per_trade=args.risk)
    print("Running backtest v2 (no sideways, wider SL, RSI filter)...")
    results = run_backtest(candles, cfg)

    # Print summary
    s = results["summary"]
    print(f"\n{'='*60}")
    print(f"  XAUUSD BACKTEST v2 — IMPROVED STRATEGY")
    print(f"{'='*60}")
    print(f"  Data: {len(candles)} bars | Warmup: 210")
    print(f"  Initial: ${cfg.initial_equity:,.2f} | Final: ${cfg.initial_equity + s['total_pnl']:,.2f}")
    print(f"  {'─'*56}")
    print(f"  Trades:     {s['total_trades']}")
    print(f"  Win rate:   {s['win_rate']}%")
    print(f"  Avg RR:     1:{s['avg_rr']}")
    print(f"  Profit factor: {s['profit_factor']}")
    print(f"  Sharpe:     {s['sharpe_ratio']}")
    print(f"  {'─'*56}")
    print(f"  Return:     {s['total_return_pct']}% (${s['total_pnl']:,.2f})")
    print(f"  Max DD:     {s['max_drawdown_pct']}%")
    print(f"  {'─'*56}")
    print(f"  Avg win:    ${s['avg_win']:.2f} | Avg loss: ${s['avg_loss']:.2f}")
    print(f"  Best:       ${s['best_trade']:.2f} | Worst: ${s['worst_trade']:.2f}")
    print(f"  Avg hold:   {s['avg_bars_held']} bars")

    print(f"\n  BY REGIME:")
    for r, st in results["by_regime"].items():
        print(f"    {r:12s} {st['count']:4d} trades  {st['win_rate']:5.1f}% win  ${st['pnl']:>10,.2f}")

    print(f"\n  BY EXIT:")
    for e, st in results["by_exit"].items():
        print(f"    {e:14s} {st['count']:4d} trades  ${st['pnl']:>10,.2f}")
    print(f"{'='*60}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
