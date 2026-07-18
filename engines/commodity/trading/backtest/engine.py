#!/usr/bin/env python3
"""
XAUUSD Trading Backtester — 3-Regime Strategy Engine
=====================================================
Regimes:
  1. UPTREND:   EMA20 > EMA50 > EMA200  → Buy dips to support/EMA
  2. DOWNTREND: EMA20 < EMA50 < EMA200  → Sell rallies to resistance/EMA
  3. SIDEWAYS:  EMAs tangled            → Buy support, sell resistance

Rules:
  - Entry only at zone extremes (low zone for buys, high zone for sells)
  - Minimum RR 1:2
  - SL at structural level (below last swing low for buys, above last swing high)
  - Position size: 1% risk per trade
  - Max 3 concurrent positions
  - Trailing stop + partial TP management

Usage:
  python engine.py --data /root/trading/data/xauusd_1h.json \
                   --output /root/trading/backtest/results/h1_results.json
"""

import json
import math
import argparse
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_ohlcv(path: str) -> list[dict]:
    """Load OHLCV JSON. Supports both list-of-dicts and {data: [...]} formats."""
    with open(path, "r") as f:
        raw = json.load(f)
    if isinstance(raw, dict) and "data" in raw:
        raw = raw["data"]
    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError(f"No data found in {path}")

    bars = []
    for i, row in enumerate(raw):
        bar = {
            "ts":    row.get("timestamp", row.get("date", row.get("time", i))),
            "open":  float(row.get("open", row.get("o", 0))),
            "high":  float(row.get("high", row.get("h", 0))),
            "low":   float(row.get("low",  row.get("l", 0))),
            "close": float(row.get("close", row.get("c", 0))),
            "volume": float(row.get("volume", row.get("v", 0))),
        }
        bars.append(bar)
    return bars


# ---------------------------------------------------------------------------
# Indicators (numpy-free, pure Python)
# ---------------------------------------------------------------------------

def ema(values: list[float], period: int) -> list[float]:
    """Exponential moving average. Returns list same length as input (NaN-padded)."""
    out = [float("nan")] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1)
    # seed with SMA
    s = sum(values[:period]) / period
    out[period - 1] = s
    for i in range(period, len(values)):
        s = values[i] * k + s * (1 - k)
        out[i] = s
    return out


def find_swing_highs(highs: list[float], lookback: int = 10) -> list[int]:
    """Indices that are local maxima over ±lookback bars."""
    idxs = []
    n = len(highs)
    for i in range(lookback, n - lookback):
        is_high = True
        for j in range(i - lookback, i + lookback + 1):
            if j == i:
                continue
            if highs[j] >= highs[i]:
                is_high = False
                break
        if is_high:
            idxs.append(i)
    return idxs


def find_swing_lows(lows: list[float], lookback: int = 10) -> list[int]:
    """Indices that are local minima over ±lookback bars."""
    idxs = []
    n = len(lows)
    for i in range(lookback, n - lookback):
        is_low = True
        for j in range(i - lookback, i + lookback + 1):
            if j == i:
                continue
            if lows[j] <= lows[i]:
                is_low = False
                break
        if is_low:
            idxs.append(i)
    return idxs


# ---------------------------------------------------------------------------
# Regime detection
# ---------------------------------------------------------------------------

REGIME_UPTREND   = "UPTREND"
REGIME_DOWNTREND = "DOWNTREND"
REGIME_SIDEWAYS  = "SIDEWAYS"


def detect_regime(ema20: float, ema50: float, ema200: float) -> str:
    if ema20 > ema50 > ema200:
        return REGIME_UPTREND
    elif ema20 < ema50 < ema200:
        return REGIME_DOWNTREND
    else:
        return REGIME_SIDEWAYS


# ---------------------------------------------------------------------------
# S/R zone identification
# ---------------------------------------------------------------------------

def compute_sr_zones(highs: list[float], lows: list[float],
                     closes: list[float], idx: int,
                     lookback: int = 60, swing_lb: int = 8) -> dict:
    """
    Return support and resistance zones based on recent swing points.
    Zones are clusters within 0.5% of each other (typical gold spread).
    """
    start = max(0, idx - lookback)
    h_slice = highs[start:idx + 1]
    l_slice = lows[start:idx + 1]

    swing_h = find_swing_highs(h_slice, swing_lb)
    swing_l = find_swing_lows(l_slice, swing_lb)

    # Convert to absolute indices and get price levels
    res_levels = sorted(set(h_slice[i] for i in swing_h), reverse=True)
    sup_levels = sorted(set(l_slice[i] for i in swing_l))

    # Cluster nearby levels (within 0.5%)
    def cluster(levels: list[float], tol: float = 0.005) -> list[float]:
        if not levels:
            return []
        clusters = [[levels[0]]]
        for lv in levels[1:]:
            if abs(lv - clusters[-1][-1]) / clusters[-1][-1] < tol:
                clusters[-1].append(lv)
            else:
                clusters.append([lv])
        return [sum(c) / len(c) for c in clusters]

    supports = cluster(sup_levels)
    resistances = cluster(res_levels)

    return {"supports": supports, "resistances": resistances}


def nearest_support(supports: list[float], price: float) -> float | None:
    below = [s for s in supports if s < price]
    return max(below) if below else None


def nearest_resistance(resistances: list[float], price: float) -> float | None:
    above = [r for r in resistances if r > price]
    return min(above) if above else None


# ---------------------------------------------------------------------------
# Position management
# ---------------------------------------------------------------------------

class Position:
    _next_id = 1

    def __init__(self, side: str, entry: float, sl: float, tp: float,
                 lot_size: float, entry_bar: int, entry_ts,
                 regime: str, partial_closed: bool = False):
        self.id = Position._next_id
        Position._next_id += 1
        self.side = side          # "BUY" or "SELL"
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.lot_size = lot_size
        self.entry_bar = entry_bar
        self.entry_ts = entry_ts
        self.regime = regime
        self.partial_closed = partial_closed
        self.trailing_sl = sl
        self.max_favorable = 0.0  # best favorable excursion
        self.exit_price = None
        self.exit_bar = None
        self.exit_ts = None
        self.exit_reason = None
        self.pnl = 0.0
        self.rr_achieved = 0.0
        self.partial_pnl = 0.0  # from partial close


def risk_amount(equity: float, risk_pct: float = 0.01) -> float:
    return equity * risk_pct


def calc_lot_size(equity: float, sl_distance: float, risk_pct: float = 0.01,
                  contract_size: float = 100.0) -> float:
    """Position size in lots. 1 lot = 100 oz for XAUUSD."""
    if sl_distance <= 0:
        return 0.0
    risk = equity * risk_pct
    lots = risk / (sl_distance * contract_size)
    return round(lots, 2)


def manage_position(pos: Position, bar: dict, bar_idx: int,
                    partial_tp_pct: float = 0.5, trail_trigger_rr: float = 1.0,
                    trail_step_pct: float = 0.003) -> tuple[bool, str]:
    """
    Check SL, TP, trailing stop, and partial TP.
    Returns (closed, reason).
    """
    high = bar["high"]
    low = bar["low"]
    close = bar["close"]

    if pos.side == "BUY":
        # Track max favorable excursion
        exc = high - pos.entry
        if exc > pos.max_favorable:
            pos.max_favorable = exc

        # Check stop loss (use trailing SL)
        if low <= pos.trailing_sl:
            pos.exit_price = max(pos.trailing_sl, low)  # could gap through
            pos.exit_bar = bar_idx
            pos.exit_ts = bar.get("ts", bar_idx)
            pos.exit_reason = "TRAILING_SL" if pos.trailing_sl > pos.sl else "SL"
            pos.pnl = (pos.exit_price - pos.entry) * pos.lot_size * 100.0 + pos.partial_pnl
            rr_dist = abs(pos.entry - pos.sl)
            pos.rr_achieved = (pos.exit_price - pos.entry) / rr_dist if rr_dist > 0 else 0
            return True, pos.exit_reason

        # Check take profit
        if high >= pos.tp:
            pos.exit_price = pos.tp
            pos.exit_bar = bar_idx
            pos.exit_ts = bar.get("ts", bar_idx)
            pos.exit_reason = "TP"
            pos.pnl = (pos.tp - pos.entry) * pos.lot_size * 100.0 + pos.partial_pnl
            rr_dist = abs(pos.entry - pos.sl)
            pos.rr_achieved = (pos.tp - pos.entry) / rr_dist if rr_dist > 0 else 0
            return True, "TP"

        # Partial TP at 1R
        if not pos.partial_closed and exc >= abs(pos.entry - pos.sl):
            pos.partial_closed = True
            partial_lots = pos.lot_size * partial_tp_pct
            pos.partial_pnl = (pos.entry + abs(pos.entry - pos.sl) - pos.entry) * partial_lots * 100.0
            pos.lot_size -= partial_lots
            # Move SL to breakeven + small buffer
            pos.trailing_sl = max(pos.trailing_sl, pos.entry + 1.0)

        # Trailing stop after 1R favorable
        if pos.max_favorable >= abs(pos.entry - pos.sl) * trail_trigger_rr:
            new_sl = high - high * trail_step_pct
            if new_sl > pos.trailing_sl:
                pos.trailing_sl = new_sl

    elif pos.side == "SELL":
        exc = pos.entry - low
        if exc > pos.max_favorable:
            pos.max_favorable = exc

        if high >= pos.trailing_sl:
            pos.exit_price = min(pos.trailing_sl, high)
            pos.exit_bar = bar_idx
            pos.exit_ts = bar.get("ts", bar_idx)
            pos.exit_reason = "TRAILING_SL" if pos.trailing_sl < pos.sl else "SL"
            pos.pnl = (pos.entry - pos.exit_price) * pos.lot_size * 100.0 + pos.partial_pnl
            rr_dist = abs(pos.sl - pos.entry)
            pos.rr_achieved = (pos.entry - pos.exit_price) / rr_dist if rr_dist > 0 else 0
            return True, pos.exit_reason

        if low <= pos.tp:
            pos.exit_price = pos.tp
            pos.exit_bar = bar_idx
            pos.exit_ts = bar.get("ts", bar_idx)
            pos.exit_reason = "TP"
            pos.pnl = (pos.entry - pos.tp) * pos.lot_size * 100.0 + pos.partial_pnl
            rr_dist = abs(pos.sl - pos.entry)
            pos.rr_achieved = (pos.entry - pos.tp) / rr_dist if rr_dist > 0 else 0
            return True, "TP"

        if not pos.partial_closed and exc >= abs(pos.sl - pos.entry):
            pos.partial_closed = True
            partial_lots = pos.lot_size * partial_tp_pct
            pos.partial_pnl = (pos.entry - (pos.entry - abs(pos.sl - pos.entry)) - 0) * partial_lots * 100.0
            # Simplified: partial pnl = distance_to_1R * partial_lots * contract
            pos.partial_pnl = abs(pos.sl - pos.entry) * partial_lots * 100.0
            pos.lot_size -= partial_lots
            pos.trailing_sl = min(pos.trailing_sl, pos.entry - 1.0)

        if pos.max_favorable >= abs(pos.sl - pos.entry) * trail_trigger_rr:
            new_sl = low + low * trail_step_pct
            if new_sl < pos.trailing_sl:
                pos.trailing_sl = new_sl

    return False, ""


# ---------------------------------------------------------------------------
# Entry signal logic
# ---------------------------------------------------------------------------

def check_entry_signal(bar: dict, prev_bar: dict, regime: str,
                       sr: dict, ema20_val: float, ema50_val: float) -> dict | None:
    """
    Check if current bar produces an entry signal.
    Returns trade dict or None.
    No look-ahead: uses only data up to and including current bar.
    """
    price = bar["close"]
    low = bar["low"]
    high = bar["high"]
    opn = bar["open"]

    supports = sr["supports"]
    resistances = sr["resistances"]

    # --- BUY signals ---
    if regime in (REGIME_UPTREND, REGIME_SIDEWAYS):
        sup = nearest_support(supports, price)
        if sup is not None:
            # Price touched or came within 0.15% of support
            touch_dist = (price - sup) / sup if sup > 0 else 999
            touched_zone = (low <= sup * 1.0015) or (touch_dist < 0.0015)

            if touched_zone:
                # Confirmation: bullish close (close > open) or close above support
                bullish_candle = price > opn or price > sup
                # For uptrend: also accept if near EMA20
                near_ema = abs(low - ema20_val) / ema20_val < 0.002 if ema20_val > 0 else False

                if (bullish_candle and touched_zone) or (near_ema and regime == REGIME_UPTREND):
                    sl = sup * 0.998  # slightly below support
                    sl_dist = price - sl
                    if sl_dist <= 0:
                        return None
                    # TP at nearest resistance, minimum 2R
                    res = nearest_resistance(resistances, price)
                    min_tp = price + sl_dist * 2.0
                    if res is not None and res > min_tp:
                        tp = res
                    elif res is not None and res > price:
                        tp = max(res, min_tp)
                    else:
                        tp = min_tp

                    rr = (tp - price) / sl_dist
                    if rr < 2.0:
                        tp = min_tp  # enforce minimum 2R

                    return {
                        "side": "BUY",
                        "entry": price,
                        "sl": sl,
                        "tp": tp,
                        "regime": regime,
                        "reason": f"Buy at support {sup:.2f}",
                    }

    # --- SELL signals ---
    if regime in (REGIME_DOWNTREND, REGIME_SIDEWAYS):
        res = nearest_resistance(resistances, price)
        if res is not None:
            touch_dist = (res - price) / res if res > 0 else 999
            touched_zone = (high >= res * 0.9985) or (touch_dist < 0.0015)

            if touched_zone:
                bearish_candle = price < opn or price < res
                near_ema = abs(high - ema20_val) / ema20_val < 0.002 if ema20_val > 0 else False

                if (bearish_candle and touched_zone) or (near_ema and regime == REGIME_DOWNTREND):
                    sl = res * 1.002
                    sl_dist = sl - price
                    if sl_dist <= 0:
                        return None
                    sup = nearest_support(supports, price)
                    min_tp = price - sl_dist * 2.0
                    if sup is not None and sup < min_tp:
                        tp = sup
                    elif sup is not None and sup < price:
                        tp = min(sup, min_tp)
                    else:
                        tp = min_tp

                    rr = (price - tp) / sl_dist
                    if rr < 2.0:
                        tp = min_tp

                    return {
                        "side": "SELL",
                        "entry": price,
                        "sl": sl,
                        "tp": tp,
                        "regime": regime,
                        "reason": f"Sell at resistance {res:.2f}",
                    }

    return None


# ---------------------------------------------------------------------------
# Main backtester
# ---------------------------------------------------------------------------

def run_backtest(bars: list[dict], config: dict) -> dict:
    """Walk-forward backtest engine."""
    ema20_vals = ema([b["close"] for b in bars], 20)
    ema50_vals = ema([b["close"] for b in bars], 50)
    ema200_vals = ema([b["close"] for b in bars], 200)

    highs = [b["high"] for b in bars]
    lows  = [b["low"]  for b in bars]

    initial_equity = config.get("initial_equity", 10000.0)
    equity = initial_equity
    risk_pct = config.get("risk_pct", 0.01)
    max_positions = config.get("max_positions", 3)
    contract_size = config.get("contract_size", 100.0)
    min_bars = config.get("warmup", 210)  # need 200 for EMA200 + some buffer

    positions: list[Position] = []
    closed_trades: list[dict] = []
    equity_curve: list[dict] = []
    regime_log: list[dict] = []

    peak_equity = equity
    max_dd = 0.0
    max_dd_pct = 0.0

    sr_cache = {}  # cache SR zones every 20 bars to save compute
    sr_update_freq = 20

    for i in range(min_bars, len(bars)):
        bar = bars[i]
        prev_bar = bars[i - 1]

        # --- Check existing positions ---
        still_open = []
        for pos in positions:
            closed, reason = manage_position(pos, bar, i)
            if closed:
                trade = {
                    "id": pos.id,
                    "side": pos.side,
                    "entry": pos.entry,
                    "exit": pos.exit_price,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "lot_size": pos.lot_size + (pos.partial_pnl / abs(pos.entry - pos.sl) / 100.0 if pos.partial_pnl != 0 and abs(pos.entry - pos.sl) > 0 else 0),
                    "entry_bar": pos.entry_bar,
                    "exit_bar": pos.exit_bar,
                    "entry_ts": pos.entry_ts,
                    "exit_ts": pos.exit_ts,
                    "regime": pos.regime,
                    "reason": reason,
                    "pnl": pos.pnl,
                    "rr_achieved": pos.rr_achieved,
                    "partial_closed": pos.partial_closed,
                    "equity_after": equity + pos.pnl,
                }
                closed_trades.append(trade)
                equity += pos.pnl
            else:
                still_open.append(pos)
        positions = still_open

        # Update peak / drawdown
        # Include open position PnL for mark-to-market
        open_pnl = 0.0
        for pos in positions:
            if pos.side == "BUY":
                open_pnl += (bar["close"] - pos.entry) * pos.lot_size * 100.0
            else:
                open_pnl += (pos.entry - bar["close"]) * pos.lot_size * 100.0

        total_equity = equity + open_pnl
        if total_equity > peak_equity:
            peak_equity = total_equity
        dd = peak_equity - total_equity
        dd_pct = dd / peak_equity if peak_equity > 0 else 0
        if dd > max_dd:
            max_dd = dd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

        equity_curve.append({
            "bar": i,
            "ts": bar.get("ts", i),
            "equity": round(equity, 2),
            "total_equity": round(total_equity, 2),
            "open_positions": len(positions),
            "drawdown": round(dd, 2),
        })

        # --- Regime detection ---
        e20 = ema20_vals[i]
        e50 = ema50_vals[i]
        e200 = ema200_vals[i]
        if math.isnan(e20) or math.isnan(e50) or math.isnan(e200):
            continue

        regime = detect_regime(e20, e50, e200)

        # Log regime changes
        if not regime_log or regime_log[-1]["regime"] != regime:
            regime_log.append({"bar": i, "ts": bar.get("ts", i), "regime": regime})

        # --- S/R zones (cached, refreshed periodically) ---
        cache_key = (i // sr_update_freq) * sr_update_freq
        if cache_key not in sr_cache:
            sr_cache[cache_key] = compute_sr_zones(highs, lows, [b["close"] for b in bars], i)
        sr = sr_cache[cache_key]

        # --- Check for new entry ---
        if len(positions) < max_positions and equity > 0:
            signal = check_entry_signal(bar, prev_bar, regime, sr, e20, e50)
            if signal is not None:
                sl_dist = abs(signal["entry"] - signal["sl"])
                if sl_dist > 0:
                    lots = calc_lot_size(equity, sl_dist, risk_pct, contract_size)
                    if lots >= 0.01:
                        pos = Position(
                            side=signal["side"],
                            entry=signal["entry"],
                            sl=signal["sl"],
                            tp=signal["tp"],
                            lot_size=lots,
                            entry_bar=i,
                            entry_ts=bar.get("ts", i),
                            regime=signal["regime"],
                        )
                        positions.append(pos)

    # Force-close any remaining positions at last bar
    last_bar = bars[-1]
    last_idx = len(bars) - 1
    for pos in positions:
        if pos.side == "BUY":
            pos.exit_price = last_bar["close"]
            pos.pnl = (pos.exit_price - pos.entry) * pos.lot_size * 100.0 + pos.partial_pnl
        else:
            pos.exit_price = last_bar["close"]
            pos.pnl = (pos.entry - pos.exit_price) * pos.lot_size * 100.0 + pos.partial_pnl
        pos.exit_bar = last_idx
        pos.exit_ts = last_bar.get("ts", last_idx)
        pos.exit_reason = "END_OF_DATA"
        rr_dist = abs(pos.entry - pos.sl)
        if pos.side == "BUY":
            pos.rr_achieved = (pos.exit_price - pos.entry) / rr_dist if rr_dist > 0 else 0
        else:
            pos.rr_achieved = (pos.entry - pos.exit_price) / rr_dist if rr_dist > 0 else 0
        equity += pos.pnl
        closed_trades.append({
            "id": pos.id,
            "side": pos.side,
            "entry": pos.entry,
            "exit": pos.exit_price,
            "sl": pos.sl,
            "tp": pos.tp,
            "lot_size": pos.lot_size,
            "entry_bar": pos.entry_bar,
            "exit_bar": pos.exit_bar,
            "entry_ts": pos.entry_ts,
            "exit_ts": pos.exit_ts,
            "regime": pos.regime,
            "reason": pos.exit_reason,
            "pnl": pos.pnl,
            "rr_achieved": pos.rr_achieved,
            "partial_closed": pos.partial_closed,
            "equity_after": equity,
        })

    # --- Compute performance metrics ---
    metrics = compute_metrics(closed_trades, equity_curve, initial_equity, equity, max_dd, max_dd_pct)

    return {
        "metrics": metrics,
        "trades": closed_trades,
        "equity_curve": equity_curve[-200:],  # last 200 points for compactness
        "regime_changes": regime_log,
        "config": config,
        "total_bars": len(bars),
        "warmup_bars": min_bars,
    }


def compute_metrics(trades: list[dict], eq_curve: list[dict],
                    initial_eq: float, final_eq: float,
                    max_dd: float, max_dd_pct: float) -> dict:
    """Compute all required performance metrics."""
    n = len(trades)
    if n == 0:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_rr": 0,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "total_return": 0,
            "total_return_pct": 0,
            "sharpe_ratio": 0,
            "profit_factor": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "avg_bars_held": 0,
            "wins": 0,
            "losses": 0,
            "breakeven": 0,
            "by_regime": {},
            "by_exit_reason": {},
        }

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    be = [t for t in trades if t["pnl"] == 0]

    total_pnl = sum(t["pnl"] for t in trades)
    gross_profit = sum(t["pnl"] for t in wins) if wins else 0
    gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0

    pnls = [t["pnl"] for t in trades]
    avg_pnl = total_pnl / n
    if n > 1:
        var = sum((p - avg_pnl) ** 2 for p in pnls) / (n - 1)
        std_pnl = math.sqrt(var)
    else:
        std_pnl = 0.0

    # Annualized Sharpe (assume ~252 trading days, 24 bars/day for 1H)
    bars_per_year = 252 * 24
    total_bars_held = sum(t["exit_bar"] - t["entry_bar"] for t in trades)
    avg_bars = total_bars_held / n if n > 0 else 0

    # Daily returns approximation from equity curve
    daily_returns = []
    if len(eq_curve) > 24:
        step = 24  # approx 1 day for hourly data
        for j in range(step, len(eq_curve)):
            prev = eq_curve[j - step]["total_equity"]
            curr = eq_curve[j]["total_equity"]
            if prev > 0:
                daily_returns.append((curr - prev) / prev)
    if len(daily_returns) > 1:
        avg_ret = sum(daily_returns) / len(daily_returns)
        var_ret = sum((r - avg_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_ret = math.sqrt(var_ret)
        sharpe = (avg_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0
    else:
        sharpe = 0

    # By regime
    by_regime = {}
    for t in trades:
        r = t["regime"]
        if r not in by_regime:
            by_regime[r] = {"count": 0, "wins": 0, "pnl": 0.0}
        by_regime[r]["count"] += 1
        if t["pnl"] > 0:
            by_regime[r]["wins"] += 1
        by_regime[r]["pnl"] += t["pnl"]
    for r in by_regime:
        c = by_regime[r]["count"]
        by_regime[r]["win_rate"] = round(by_regime[r]["wins"] / c * 100, 1) if c > 0 else 0
        by_regime[r]["pnl"] = round(by_regime[r]["pnl"], 2)

    # By exit reason
    by_reason = {}
    for t in trades:
        reason = t["reason"]
        if reason not in by_reason:
            by_reason[reason] = {"count": 0, "pnl": 0.0}
        by_reason[reason]["count"] += 1
        by_reason[reason]["pnl"] += t["pnl"]
    for reason in by_reason:
        by_reason[reason]["pnl"] = round(by_reason[reason]["pnl"], 2)

    return {
        "total_trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(be),
        "win_rate": round(len(wins) / n * 100, 1) if n > 0 else 0,
        "avg_rr": round(sum(abs(t["rr_achieved"]) for t in trades) / n, 2) if n > 0 else 0,
        "avg_pnl": round(avg_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_win": round(gross_profit / len(wins), 2) if wins else 0,
        "avg_loss": round(-gross_loss / len(losses), 2) if losses else 0,
        "best_trade": round(max(pnls), 2),
        "worst_trade": round(min(pnls), 2),
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd_pct * 100, 2),
        "total_return": round(final_eq - initial_eq, 2),
        "total_return_pct": round((final_eq - initial_eq) / initial_eq * 100, 2),
        "initial_equity": initial_eq,
        "final_equity": round(final_eq, 2),
        "sharpe_ratio": round(sharpe, 2),
        "avg_bars_held": round(avg_bars, 1),
        "by_regime": by_regime,
        "by_exit_reason": by_reason,
    }


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(result: dict):
    m = result["metrics"]
    print("\n" + "=" * 60)
    print("  XAUUSD BACKTESTER — RESULTS SUMMARY")
    print("=" * 60)
    print(f"  Data bars:     {result['total_bars']}  (warmup: {result['warmup_bars']})")
    print(f"  Initial eq:    ${m['initial_equity']:,.2f}")
    print(f"  Final eq:      ${m['final_equity']:,.2f}")
    print("-" * 60)
    print(f"  Total trades:  {m['total_trades']}")
    print(f"  Wins / Losses: {m['wins']} / {m['losses']}  (BE: {m['breakeven']})")
    print(f"  Win rate:      {m['win_rate']}%")
    print(f"  Avg RR:        {m['avg_rr']}")
    print("-" * 60)
    print(f"  Total return:  ${m['total_return']:,.2f}  ({m['total_return_pct']:.2f}%)")
    print(f"  Profit factor: {m['profit_factor']}")
    print(f"  Sharpe ratio:  {m['sharpe_ratio']}")
    print(f"  Max drawdown:  ${m['max_drawdown']:,.2f}  ({m['max_drawdown_pct']:.2f}%)")
    print("-" * 60)
    print(f"  Avg win:       ${m['avg_win']:,.2f}")
    print(f"  Avg loss:      ${m['avg_loss']:,.2f}")
    print(f"  Best trade:    ${m['best_trade']:,.2f}")
    print(f"  Worst trade:   ${m['worst_trade']:,.2f}")
    print(f"  Avg bars held: {m['avg_bars_held']}")
    print("-" * 60)

    if m.get("by_regime"):
        print("\n  BY REGIME:")
        print(f"  {'Regime':<12} {'Count':>6} {'Win%':>6} {'PnL':>12}")
        print("  " + "-" * 40)
        for regime, data in sorted(m["by_regime"].items()):
            print(f"  {regime:<12} {data['count']:>6} {data['win_rate']:>5.1f}% ${data['pnl']:>10,.2f}")

    if m.get("by_exit_reason"):
        print("\n  BY EXIT REASON:")
        print(f"  {'Reason':<16} {'Count':>6} {'PnL':>12}")
        print("  " + "-" * 38)
        for reason, data in sorted(m["by_exit_reason"].items()):
            print(f"  {reason:<16} {data['count']:>6} ${data['pnl']:>10,.2f}")

    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="XAUUSD 3-Regime Backtester")
    parser.add_argument("--data", required=True, help="Path to OHLCV JSON file")
    parser.add_argument("--output", required=True, help="Output results JSON path")
    parser.add_argument("--equity", type=float, default=10000.0, help="Initial equity")
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade (default 0.01 = 1%%)")
    parser.add_argument("--max-pos", type=int, default=3, help="Max concurrent positions")
    parser.add_argument("--warmup", type=int, default=210, help="Warmup bars before trading")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"ERROR: Data file not found: {args.data}")
        sys.exit(1)

    print(f"Loading data from {args.data} ...")
    bars = load_ohlcv(args.data)
    print(f"Loaded {len(bars)} bars.")

    config = {
        "initial_equity": args.equity,
        "risk_pct": args.risk,
        "max_positions": args.max_pos,
        "contract_size": 100.0,
        "warmup": args.warmup,
    }

    print("Running backtest ...")
    result = run_backtest(bars, config)

    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Results saved to {args.output}")

    print_summary(result)


if __name__ == "__main__":
    main()
