#!/usr/bin/env python3
"""
Trading Journal Engine for XAUUSD Gold Trading
-----------------------------------------------
Tracks signal outcomes, calculates performance metrics, generates reports.

Usage:
  python3 journal_engine.py --log --signal_id <id> --outcome <win|loss|breakeven|pending> --pnl <amount>
  python3 journal_engine.py --report [--period weekly|monthly]
  python3 journal_engine.py --stats
  python3 journal_engine.py --sync          # import new signals from signals.jsonl
  python3 journal_engine.py --list [--open]  # list all or only open trades
"""

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

JOURNAL_DIR = Path("/root/trading/journal")
SIGNALS_FILE = JOURNAL_DIR / "signals.jsonl"
TRADE_LOG = JOURNAL_DIR / "trade_log.json"
REPORTS_DIR = JOURNAL_DIR

VALID_OUTCOMES = ("win", "loss", "breakeven", "pending", "cancelled")


def load_trade_log() -> dict:
    if TRADE_LOG.exists():
        with open(TRADE_LOG) as f:
            return json.load(f)
    return {"trades": {}, "meta": {"created": datetime.now().isoformat(), "version": 1}}


def save_trade_log(log: dict):
    log["meta"]["updated"] = datetime.now().isoformat()
    with open(TRADE_LOG, "w") as f:
        json.dump(log, f, indent=2, default=str)


def generate_signal_id(signal: dict) -> str:
    """Generate a deterministic short ID from signal content."""
    raw = f"{signal['timestamp']}_{signal['entry']}_{signal['signal']}"
    return hashlib.sha256(raw.encode()).hexdigest()[:10]


def load_signals() -> list:
    """Load all signals from JSONL file."""
    signals = []
    if not SIGNALS_FILE.exists():
        return signals
    with open(SIGNALS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return signals


def sync_signals():
    """Import new signals from signals.jsonl into trade_log."""
    log = load_trade_log()
    signals = load_signals()
    added = 0
    for sig in signals:
        sid = generate_signal_id(sig)
        if sid not in log["trades"]:
            log["trades"][sid] = {
                "signal_id": sid,
                "timestamp": sig.get("timestamp"),
                "direction": sig.get("signal", "UNKNOWN"),
                "entry_price": sig.get("entry"),
                "sl_price": sig.get("sl"),
                "tp_price": sig.get("tp"),
                "rr_ratio": sig.get("rr_ratio"),
                "confidence": sig.get("confidence"),
                "confluence_count": sig.get("confluence_count"),
                "confluence_signals": sig.get("confluence_signals", []),
                "reasons": sig.get("reasons", []),
                "ema_trend": sig.get("ema_trend"),
                "rsi": sig.get("rsi"),
                "candle_pattern": sig.get("candle_pattern"),
                "current_price": sig.get("price"),
                "outcome": "pending",
                "pnl": 0.0,
                "notes": "",
                "closed_at": None,
                "outcome_logged_at": None,
            }
            added += 1
    save_trade_log(log)
    print(f"Synced {added} new signals (total: {len(log['trades'])})")
    return added


def log_outcome(signal_id: str, outcome: str, pnl: float, notes: str = ""):
    """Log outcome for a specific trade."""
    if outcome not in VALID_OUTCOMES:
        print(f"Error: outcome must be one of {VALID_OUTCOMES}")
        sys.exit(1)

    log = load_trade_log()

    # Try exact match first, then prefix match
    if signal_id in log["trades"]:
        trade = log["trades"][signal_id]
    else:
        matches = [k for k in log["trades"] if k.startswith(signal_id)]
        if len(matches) == 1:
            signal_id = matches[0]
            trade = log["trades"][signal_id]
        elif len(matches) > 1:
            print(f"Ambiguous signal_id '{signal_id}'. Matches: {matches}")
            sys.exit(1)
        else:
            # Create a manual entry
            print(f"Signal '{signal_id}' not found. Creating manual entry.")
            trade = {
                "signal_id": signal_id,
                "timestamp": datetime.now().isoformat(),
                "direction": "MANUAL",
                "entry_price": 0,
                "sl_price": 0,
                "tp_price": 0,
                "rr_ratio": 0,
                "confidence": 0,
                "confluence_count": 0,
                "confluence_signals": [],
                "reasons": ["manual_entry"],
                "ema_trend": "N/A",
                "rsi": 0,
                "candle_pattern": "N/A",
                "current_price": 0,
                "outcome": "pending",
                "pnl": 0.0,
                "notes": "",
                "closed_at": None,
                "outcome_logged_at": None,
            }
            log["trades"][signal_id] = trade

    trade["outcome"] = outcome
    trade["pnl"] = pnl
    trade["notes"] = notes
    trade["closed_at"] = datetime.now().isoformat()
    trade["outcome_logged_at"] = datetime.now().isoformat()

    save_trade_log(log)
    print(f"Logged: {signal_id[:10]}.. -> {outcome} (PnL: ${pnl:+.2f})")


def calc_statistics(log: dict) -> dict:
    """Calculate comprehensive trading statistics."""
    trades = list(log["trades"].values())
    if not trades:
        return {"error": "No trades in journal"}

    closed = [t for t in trades if t["outcome"] in ("win", "loss", "breakeven")]
    wins = [t for t in closed if t["outcome"] == "win"]
    losses = [t for t in closed if t["outcome"] == "loss"]
    breakeven = [t for t in closed if t["outcome"] == "breakeven"]
    pending = [t for t in trades if t["outcome"] == "pending"]

    total_closed = len(closed)
    total_wins = len(wins)
    total_losses = len(losses)
    total_pending = len(pending)

    # Win rate
    win_rate = (total_wins / total_closed * 100) if total_closed > 0 else 0

    # PnL stats
    total_pnl = sum(t["pnl"] for t in closed)
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
    avg_win = (gross_profit / total_wins) if total_wins > 0 else 0
    avg_loss = (gross_loss / total_losses) if total_losses > 0 else 0

    # Average RR of closed trades
    rr_values = [t.get("rr_ratio", 0) for t in closed if t.get("rr_ratio")]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0

    # Max drawdown (running PnL)
    max_dd = 0
    peak = 0
    running = 0
    sorted_closed = sorted(closed, key=lambda t: t.get("closed_at", ""))
    for t in sorted_closed:
        running += t["pnl"]
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    # Best & worst trade
    best_trade = max(closed, key=lambda t: t["pnl"]) if closed else None
    worst_trade = min(closed, key=lambda t: t["pnl"]) if closed else None

    # Best setup type (by confluence signals)
    setup_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0})
    for t in closed:
        for sig in t.get("confluence_signals", ["UNKNOWN"]):
            if t["outcome"] == "win":
                setup_stats[sig]["wins"] += 1
            elif t["outcome"] == "loss":
                setup_stats[sig]["losses"] += 1
            setup_stats[sig]["pnl"] += t["pnl"]

    best_setup = max(setup_stats.items(), key=lambda x: x[1]["pnl"]) if setup_stats else ("N/A", {})
    worst_setup = min(setup_stats.items(), key=lambda x: x[1]["pnl"]) if setup_stats else ("N/A", {})

    # Worst time of day
    hour_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0})
    for t in closed:
        ts = t.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                hour = dt.hour
                if t["outcome"] == "win":
                    hour_stats[hour]["wins"] += 1
                elif t["outcome"] == "loss":
                    hour_stats[hour]["losses"] += 1
                hour_stats[hour]["pnl"] += t["pnl"]
            except (ValueError, TypeError):
                pass

    best_hour = max(hour_stats.items(), key=lambda x: x[1]["pnl"]) if hour_stats else ("N/A", {})
    worst_hour = min(hour_stats.items(), key=lambda x: x[1]["pnl"]) if hour_stats else ("N/A", {})

    # Direction stats
    long_trades = [t for t in closed if t["direction"] == "LONG"]
    short_trades = [t for t in closed if t["direction"] == "SHORT"]

    return {
        "total_trades": len(trades),
        "total_closed": total_closed,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_breakeven": len(breakeven),
        "total_pending": total_pending,
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "∞",
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_rr": round(avg_rr, 2),
        "max_drawdown": round(max_dd, 2),
        "best_trade": {
            "signal_id": best_trade["signal_id"][:10],
            "pnl": round(best_trade["pnl"], 2),
            "direction": best_trade["direction"],
            "entry": best_trade["entry_price"],
        } if best_trade else None,
        "worst_trade": {
            "signal_id": worst_trade["signal_id"][:10],
            "pnl": round(worst_trade["pnl"], 2),
            "direction": worst_trade["direction"],
            "entry": worst_trade["entry_price"],
        } if worst_trade else None,
        "best_setup": {"name": best_setup[0], **best_setup[1]} if best_setup[1] else None,
        "worst_setup": {"name": worst_setup[0], **worst_setup[1]} if worst_setup[1] else None,
        "best_hour": {"hour": best_hour[0], **best_hour[1]} if best_hour[1] else None,
        "worst_hour": {"hour": worst_hour[0], **worst_hour[1]} if worst_hour[1] else None,
        "setup_stats": dict(setup_stats),
        "hour_stats": {str(k): v for k, v in hour_stats.items()},
        "long_stats": {
            "count": len(long_trades),
            "wins": sum(1 for t in long_trades if t["outcome"] == "win"),
            "pnl": round(sum(t["pnl"] for t in long_trades), 2),
        },
        "short_stats": {
            "count": len(short_trades),
            "wins": sum(1 for t in short_trades if t["outcome"] == "win"),
            "pnl": round(sum(t["pnl"] for t in short_trades), 2),
        },
    }


def generate_report(period: str = "weekly") -> str:
    """Generate markdown report."""
    log = load_trade_log()
    stats = calc_statistics(log)

    if "error" in stats:
        return f"# Trading Journal Report\n\n{stats['error']}\n"

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    # Filter to period
    if period == "weekly":
        cutoff = now - timedelta(days=7)
        period_label = f"Week of {cutoff.strftime('%b %d')} - {now.strftime('%b %d, %Y')}"
    elif period == "monthly":
        cutoff = now - timedelta(days=30)
        period_label = f"Month of {now.strftime('%B %Y')}"
    else:
        cutoff = None
        period_label = f"All Time ({date_str})"

    # Recalc with period filter if needed
    if cutoff:
        filtered_log = {"trades": {}}
        cutoff_iso = cutoff.isoformat()
        for tid, t in log["trades"].items():
            ts = t.get("closed_at") or t.get("timestamp", "")
            if ts >= cutoff_iso:
                filtered_log["trades"][tid] = t
        stats = calc_statistics(filtered_log)

    # Build report
    emoji_w = "🟢"
    emoji_l = "🔴"
    emoji_be = "🟡"
    emoji_p = "⏳"

    wr_emoji = emoji_w if stats["win_rate"] >= 50 else emoji_l

    lines = []
    lines.append(f"📊 **XAUUSD Trading Journal — {period_label}**")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # Summary
    lines.append(f"📈 **Total Trades:** {stats['total_trades']}")
    lines.append(f"   {emoji_w} Wins: {stats['total_wins']}  |  {emoji_l} Losses: {stats['total_losses']}  |  {emoji_be} BE: {stats['total_breakeven']}  |  {emoji_p} Open: {stats['total_pending']}")
    lines.append(f"   {wr_emoji} **Win Rate: {stats['win_rate']}%**")
    lines.append("")

    # Financials
    pnl_emoji = "💰" if stats["total_pnl"] >= 0 else "💸"
    lines.append(f"{pnl_emoji} **Net PnL: ${stats['total_pnl']:+.2f}**")
    lines.append(f"   Gross Profit: ${stats['gross_profit']:+.2f}  |  Gross Loss: ${stats['gross_loss']:.2f}")
    lines.append(f"   Profit Factor: {stats['profit_factor']}")
    lines.append(f"   Avg Win: ${stats['avg_win']:+.2f}  |  Avg Loss: ${stats['avg_loss']:.2f}")
    lines.append(f"   Avg RR: {stats['avg_rr']}:1")
    lines.append("")

    # Risk
    lines.append(f"⚠️ **Max Drawdown: ${stats['max_drawdown']:.2f}**")
    lines.append("")

    # Best & Worst
    if stats["best_trade"]:
        bt = stats["best_trade"]
        lines.append(f"🏆 Best Trade: {bt['signal_id']}.. {bt['direction']} @ {bt['entry']} → **${bt['pnl']:+.2f}**")
    if stats["worst_trade"]:
        wt = stats["worst_trade"]
        lines.append(f"💀 Worst Trade: {wt['signal_id']}.. {wt['direction']} @ {wt['entry']} → **${wt['pnl']:+.2f}**")
    lines.append("")

    # Direction breakdown
    ls = stats["long_stats"]
    ss = stats["short_stats"]
    lines.append(f"📊 **Direction Breakdown:**")
    if ls["count"]:
        lw = (ls["wins"] / ls["count"] * 100) if ls["count"] else 0
        lines.append(f"   🟢 LONG: {ls['count']} trades, {lw:.0f}% WR, ${ls['pnl']:+.2f}")
    if ss["count"]:
        sw = (ss["wins"] / ss["count"] * 100) if ss["count"] else 0
        lines.append(f"   🔴 SHORT: {ss['count']} trades, {sw:.0f}% WR, ${ss['pnl']:+.2f}")
    lines.append("")

    # Best/worst setup
    if stats["best_setup"]:
        bs = stats["best_setup"]
        lines.append(f"🎯 Best Setup: **{bs['name']}** (W:{bs.get('wins',0)} L:{bs.get('losses',0)} PnL:${bs.get('pnl',0):+.2f})")
    if stats["worst_setup"]:
        ws = stats["worst_setup"]
        lines.append(f"⛔ Worst Setup: **{ws['name']}** (W:{ws.get('wins',0)} L:{ws.get('losses',0)} PnL:${ws.get('pnl',0):+.2f})")
    lines.append("")

    # Best/worst hour
    if stats["best_hour"]:
        bh = stats["best_hour"]
        lines.append(f"⏰ Best Hour: **{bh['hour']:02d}:00 UTC+8** (W:{bh.get('wins',0)} L:{bh.get('losses',0)} PnL:${bh.get('pnl',0):+.2f})")
    if stats["worst_hour"]:
        wh = stats["worst_hour"]
        lines.append(f"🕐 Worst Hour: **{wh['hour']:02d}:00 UTC+8** (W:{wh.get('wins',0)} L:{wh.get('losses',0)} PnL:${wh.get('pnl',0):+.2f})")
    lines.append("")

    # Recommendations
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("💡 **Recommendations:**")

    recs = []
    if stats["win_rate"] < 40:
        recs.append("• Win rate below 40% — tighten entry criteria, wait for stronger confluence")
    if stats["win_rate"] > 65:
        recs.append("• Strong win rate — consider increasing position size gradually")
    pf = stats["profit_factor"]
    if isinstance(pf, (int, float)) and pf < 1.2:
        recs.append("• Profit factor too low — let winners run longer, cut losses faster")
    if isinstance(pf, (int, float)) and pf > 2.0:
        recs.append("• Excellent profit factor — maintain current risk/reward discipline")
    if stats["avg_rr"] < 1.5:
        recs.append("• Average RR below 1.5 — widen TP targets or trail stops more aggressively")
    if stats["max_drawdown"] > 500:
        recs.append(f"• High drawdown (${stats['max_drawdown']:.0f}) — reduce lot size until equity recovers")
    if stats["worst_setup"]:
        recs.append(f"• Review '{stats['worst_setup']['name']}' setup — consistently losing money")
    if stats["worst_hour"]:
        wh = stats["worst_hour"]
        if wh.get("losses", 0) > wh.get("wins", 0):
            recs.append(f"• Avoid trading at {wh['hour']:02d}:00 — losing hour historically")
    if not recs:
        recs.append("• Keep up the good work! Maintain discipline and stick to your system.")

    for r in recs:
        lines.append(f"  {r}")

    lines.append("")
    lines.append(f"_Generated: {now.strftime('%Y-%m-%d %H:%M UTC+8')}_")

    return "\n".join(lines)


def save_report(report: str):
    """Save report to dated markdown file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"weekly_report_{date_str}.md"
    with open(path, "w") as f:
        f.write(report)
    print(f"Report saved to: {path}")
    return path


def print_stats():
    """Print formatted statistics to stdout."""
    log = load_trade_log()
    stats = calc_statistics(log)

    if "error" in stats:
        print(stats["error"])
        return

    print("\n" + "=" * 50)
    print("  XAUUSD TRADING JOURNAL — STATISTICS")
    print("=" * 50)
    print(f"  Total Trades:    {stats['total_trades']}")
    print(f"  Closed:          {stats['total_closed']}")
    print(f"  Wins / Losses:   {stats['total_wins']} / {stats['total_losses']}")
    print(f"  Breakeven:       {stats['total_breakeven']}")
    print(f"  Pending:         {stats['total_pending']}")
    print(f"  Win Rate:        {stats['win_rate']}%")
    print("-" * 50)
    print(f"  Net PnL:         ${stats['total_pnl']:+.2f}")
    print(f"  Gross Profit:    ${stats['gross_profit']:+.2f}")
    print(f"  Gross Loss:      ${stats['gross_loss']:.2f}")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Avg Win:         ${stats['avg_win']:+.2f}")
    print(f"  Avg Loss:        ${stats['avg_loss']:.2f}")
    print(f"  Avg RR:          {stats['avg_rr']}:1")
    print(f"  Max Drawdown:    ${stats['max_drawdown']:.2f}")
    print("-" * 50)

    if stats["best_trade"]:
        bt = stats["best_trade"]
        print(f"  Best Trade:      {bt['signal_id']}.. ${bt['pnl']:+.2f}")
    if stats["worst_trade"]:
        wt = stats["worst_trade"]
        print(f"  Worst Trade:     {wt['signal_id']}.. ${wt['pnl']:+.2f}")

    print("=" * 50 + "\n")


def list_trades(open_only=False):
    """List all trades."""
    log = load_trade_log()
    trades = sorted(log["trades"].values(), key=lambda t: t.get("timestamp", ""), reverse=True)

    if open_only:
        trades = [t for t in trades if t["outcome"] == "pending"]

    if not trades:
        print("No trades found.")
        return

    print(f"\n{'ID':<12} {'Dir':<6} {'Entry':>10} {'Outcome':<10} {'PnL':>10} {'Time':<20}")
    print("-" * 70)
    for t in trades[:30]:
        ts = t.get("timestamp", "")[:19] if t.get("timestamp") else "N/A"
        pnl = f"${t['pnl']:+.2f}" if t["outcome"] != "pending" else "—"
        print(f"{t['signal_id'][:10]:<12} {t['direction']:<6} {t['entry_price']:>10.2f} {t['outcome']:<10} {pnl:>10} {ts}")

    print(f"\nShowing {min(30, len(trades))} of {len(trades)} trades")


def main():
    parser = argparse.ArgumentParser(description="XAUUSD Trading Journal Engine")
    parser.add_argument("--log", action="store_true", help="Log trade outcome")
    parser.add_argument("--signal_id", type=str, help="Signal ID (full or prefix)")
    parser.add_argument("--outcome", type=str, choices=VALID_OUTCOMES, help="Trade outcome")
    parser.add_argument("--pnl", type=float, default=0.0, help="Profit/Loss amount")
    parser.add_argument("--notes", type=str, default="", help="Trade notes")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--period", type=str, default="all", choices=["weekly", "monthly", "all"])
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--sync", action="store_true", help="Sync signals from JSONL")
    parser.add_argument("--list", action="store_true", help="List trades")
    parser.add_argument("--open", action="store_true", help="Show only open trades (with --list)")

    args = parser.parse_args()

    # Ensure journal dir exists
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    if args.sync:
        sync_signals()
    elif args.log:
        if not args.signal_id or not args.outcome:
            print("Error: --log requires --signal_id and --outcome")
            sys.exit(1)
        log_outcome(args.signal_id, args.outcome, args.pnl, args.notes)
    elif args.report:
        report = generate_report(args.period)
        print(report)
        save_report(report)
    elif args.stats:
        print_stats()
    elif args.list:
        list_trades(open_only=args.open)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
