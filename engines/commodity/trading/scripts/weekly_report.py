#!/usr/bin/env python3
"""
Weekly Trading Report Generator
--------------------------------
Generates a clean markdown report from the trading journal.
Suitable for Telegram delivery via Hermes cron.

Usage:
  python3 weekly_report.py                 # Generate and print report
  python3 weekly_report.py --save          # Save to file
  python3 weekly_report.py --telegram      # Telegram-optimized output (shorter)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

JOURNAL_DIR = Path("/root/trading/journal")
TRADE_LOG = JOURNAL_DIR / "trade_log.json"


def load_trades():
    if not TRADE_LOG.exists():
        return []
    with open(TRADE_LOG) as f:
        data = json.load(f)
    return list(data.get("trades", {}).values())


def generate_weekly_report(telegram_mode=False):
    """Generate weekly trading report."""
    now = datetime.now()
    cutoff = now - timedelta(days=7)
    cutoff_iso = cutoff.isoformat()

    all_trades = load_trades()
    trades = [t for t in all_trades if (t.get("closed_at") or t.get("timestamp", "")) >= cutoff_iso]

    closed = [t for t in trades if t["outcome"] in ("win", "loss", "breakeven")]
    wins = [t for t in closed if t["outcome"] == "win"]
    losses = [t for t in closed if t["outcome"] == "loss"]
    pending = [t for t in trades if t["outcome"] == "pending"]

    total = len(trades)
    total_closed = len(closed)
    total_wins = len(wins)
    total_losses = len(losses)
    total_pending = len(pending)

    win_rate = (total_wins / total_closed * 100) if total_closed > 0 else 0
    total_pnl = sum(t["pnl"] for t in closed)
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    rr_vals = [t.get("rr_ratio", 0) for t in closed if t.get("rr_ratio")]
    avg_rr = sum(rr_vals) / len(rr_vals) if rr_vals else 0

    # Drawdown
    max_dd = 0
    peak = 0
    running = 0
    for t in sorted(closed, key=lambda x: x.get("closed_at", "")):
        running += t["pnl"]
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    best = max(closed, key=lambda t: t["pnl"]) if closed else None
    worst = min(closed, key=lambda t: t["pnl"]) if closed else None

    # Setup analysis
    setup_wins = defaultdict(int)
    setup_losses = defaultdict(int)
    for t in closed:
        for sig in t.get("confluence_signals", ["UNKNOWN"]):
            if t["outcome"] == "win":
                setup_wins[sig] += 1
            else:
                setup_losses[sig] += 1

    # Hour analysis
    hour_wins = defaultdict(int)
    hour_losses = defaultdict(int)
    for t in closed:
        ts = t.get("timestamp", "")
        if ts:
            try:
                h = datetime.fromisoformat(ts).hour
                if t["outcome"] == "win":
                    hour_wins[h] += 1
                else:
                    hour_losses[h] += 1
            except (ValueError, TypeError):
                pass

    # Format
    wr_icon = "🟢" if win_rate >= 50 else "🔴"
    pnl_icon = "💰" if total_pnl >= 0 else "💸"
    pf_str = f"{profit_factor:.2f}" if profit_factor != float("inf") else "∞"

    if telegram_mode:
        # Shorter format for Telegram
        lines = [
            f"📊 **Weekly XAUUSD Report**",
            f"📅 {cutoff.strftime('%b %d')} - {now.strftime('%b %d, %Y')}",
            "",
            f"📈 Trades: {total} | Closed: {total_closed} | Pending: {total_pending}",
            f"{wr_icon} WR: {win_rate:.0f}% ({total_wins}W/{total_losses}L)",
            f"{pnl_icon} PnL: ${total_pnl:+.2f}",
            f"📊 PF: {pf_str} | Avg RR: {avg_rr:.1f}:1",
            f"⚠️ Max DD: ${max_dd:.2f}",
        ]

        if best:
            lines.append(f"🏆 Best: ${best['pnl']:+.2f} ({best['direction']} @ {best['entry_price']:.0f})")
        if worst:
            lines.append(f"💀 Worst: ${worst['pnl']:+.2f} ({worst['direction']} @ {worst['entry_price']:.0f})")

        lines.append("")
        lines.append("**💡 Recs:**")
        recs = build_recommendations(win_rate, profit_factor, avg_rr, max_dd, setup_wins, setup_losses)
        for r in recs:
            lines.append(f"• {r}")

        return "\n".join(lines)

    else:
        # Full format
        lines = [
            "📊 **XAUUSD Weekly Trading Report**",
            f"📅 Period: {cutoff.strftime('%b %d')} - {now.strftime('%b %d, %Y')}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📈 **Performance Summary**",
            f"   Total Signals: {total}",
            f"   🟢 Wins: {total_wins}  |  🔴 Losses: {total_losses}  |  ⏳ Open: {total_pending}",
            f"   {wr_icon} Win Rate: {win_rate:.1f}%",
            "",
            "💰 **Financials**",
            f"   {pnl_icon} Net PnL: ${total_pnl:+.2f}",
            f"   Profit Factor: {pf_str}",
            f"   Avg RR: {avg_rr:.2f}:1",
            f"   ⚠️ Max Drawdown: ${max_dd:.2f}",
            "",
        ]

        if best:
            lines.append(f"🏆 **Best Trade:** {best['direction']} @ {best['entry_price']:.2f} → ${best['pnl']:+.2f}")
        if worst:
            lines.append(f"💀 **Worst Trade:** {worst['direction']} @ {worst['entry_price']:.2f} → ${worst['pnl']:+.2f}")
        lines.append("")

        # Recommendations
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("💡 **Recommendations:**")
        recs = build_recommendations(win_rate, profit_factor, avg_rr, max_dd, setup_wins, setup_losses)
        for r in recs:
            lines.append(f"  • {r}")
        lines.append("")
        lines.append(f"_Generated: {now.strftime('%Y-%m-%d %H:%M UTC+8')}_")

        return "\n".join(lines)


def build_recommendations(win_rate, profit_factor, avg_rr, max_dd, setup_wins, setup_losses):
    """Build actionable recommendations."""
    recs = []

    if win_rate < 40:
        recs.append("Win rate critical — require 4+ confluence before entry")
    elif win_rate > 65:
        recs.append("Strong WR — consider scaling into A+ setups")

    pf = profit_factor if profit_factor != float("inf") else 999
    if pf < 1.2:
        recs.append("PF too low — extend TP targets, tighten SL")
    elif pf > 2.0:
        recs.append("Excellent PF — maintain current risk management")

    if avg_rr < 1.5:
        recs.append("Avg RR low — aim for minimum 1:2 setups")
    elif avg_rr > 2.5:
        recs.append("Great RR discipline — keep letting winners run")

    if max_dd > 500:
        recs.append(f"DD ${max_dd:.0f} — reduce position size to recover safely")

    # Worst setup
    all_setups = set(list(setup_wins.keys()) + list(setup_losses.keys()))
    for s in all_setups:
        w = setup_wins.get(s, 0)
        l = setup_losses.get(s, 0)
        if l > w and (w + l) >= 2:
            recs.append(f"'{s}' setup net negative ({w}W/{l}L) — review or avoid")

    if not recs:
        recs.append("Discipline on point — keep grinding, Abang Sado! 💪")

    return recs


def main():
    telegram = "--telegram" in sys.argv
    save = "--save" in sys.argv

    report = generate_weekly_report(telegram_mode=telegram)
    print(report)

    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = JOURNAL_DIR / f"weekly_report_{date_str}.md"
        with open(path, "w") as f:
            f.write(report)
        print(f"\nSaved to: {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
