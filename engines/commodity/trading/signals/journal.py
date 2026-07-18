"""
Trading Journal & Tracking — XAUUSD.
Logs signals, tracks outcomes, generates reports.

Usage:
    from signals.journal import log_signal, update_outcome, get_stats, weekly_report
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


JOURNAL_DIR = Path("/root/trading/journal")
JOURNAL_FILE = JOURNAL_DIR / "signals.jsonl"
WEEKLY_DIR = JOURNAL_DIR / "weekly"

# Ensure dirs
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
WEEKLY_DIR.mkdir(parents=True, exist_ok=True)


def log_signal(signal: Dict) -> Dict:
    """
    Log a trading signal to journal.
    Args:
        signal: signal dict from engine.generate_signal()
    Returns: logged entry with ID
    """
    entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "logged_at": datetime.now().isoformat(),
        "signal": signal.get("signal"),
        "direction": signal.get("direction"),
        "entry": signal.get("entry"),
        "stop_loss": signal.get("stop_loss"),
        "take_profit": signal.get("take_profit"),
        "risk_pips": signal.get("risk_pips"),
        "reward_pips": signal.get("reward_pips"),
        "risk_reward": signal.get("risk_reward"),
        "confluence_score": signal.get("confluence_score"),
        "confidence": signal.get("confidence"),
        "reasoning": signal.get("reasoning"),
        "session": signal.get("session"),
        "technical": signal.get("technical"),
        "macro": signal.get("macro"),
        "status": "OPEN",  # OPEN → WIN / LOSS / BREAKEVEN / EXPIRED
        "outcome": None,
        "exit_price": None,
        "pnl_pips": None,
        "closed_at": None,
        "notes": None,
    }

    # Append to JSONL
    with open(JOURNAL_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def update_outcome(
    signal_id: str,
    outcome: str,
    exit_price: float,
    notes: Optional[str] = None,
) -> Dict:
    """
    Update signal outcome (WIN/LOSS/BREAKEVEN/EXPIRED).
    Args:
        signal_id: ID from log_signal
        outcome: WIN, LOSS, BREAKEVEN, EXPIRED
        exit_price: actual exit price
        notes: optional notes
    Returns: updated entry
    """
    if not JOURNAL_FILE.exists():
        return {"error": "No journal entries found"}

    # Read all entries
    entries = []
    with open(JOURNAL_FILE, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Find and update
    updated = None
    for entry in entries:
        if entry["id"] == signal_id:
            entry["status"] = outcome
            entry["outcome"] = outcome
            entry["exit_price"] = exit_price
            entry["closed_at"] = datetime.now().isoformat()
            entry["notes"] = notes

            # Calculate P&L
            if entry["direction"] == "long":
                entry["pnl_pips"] = round(exit_price - entry["entry"], 2)
            elif entry["direction"] == "short":
                entry["pnl_pips"] = round(entry["entry"] - exit_price, 2)

            updated = entry
            break

    if not updated:
        return {"error": f"Signal {signal_id} not found"}

    # Rewrite file
    with open(JOURNAL_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return updated


def get_signals(
    status: Optional[str] = None,
    days: Optional[int] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Get journal entries with optional filters.
    Args:
        status: filter by status (OPEN, WIN, LOSS, etc.)
        days: only last N days
        limit: max entries
    Returns: list of entries
    """
    if not JOURNAL_FILE.exists():
        return []

    entries = []
    with open(JOURNAL_FILE, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Filter by status
    if status:
        entries = [e for e in entries if e.get("status") == status]

    # Filter by days
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        entries = [e for e in entries if e.get("logged_at", "") >= cutoff]

    # Sort by date (newest first)
    entries.sort(key=lambda x: x.get("logged_at", ""), reverse=True)

    return entries[:limit]


def get_stats(days: Optional[int] = None) -> Dict:
    """
    Calculate trading statistics.
    Args:
        days: calculate for last N days only
    Returns: statistics dict
    """
    entries = get_signals(days=days, limit=1000)

    if not entries:
        return {"total_signals": 0, "message": "No signals logged yet"}

    # Filter completed trades
    completed = [e for e in entries if e.get("status") in ["WIN", "LOSS", "BREAKEVEN"]]
    open_signals = [e for e in entries if e.get("status") == "OPEN"]
    no_signals = [e for e in entries if e.get("signal") == "NO_SIGNAL"]

    total = len(completed)
    wins = len([e for e in completed if e["status"] == "WIN"])
    losses = len([e for e in completed if e["status"] == "LOSS"])
    breakevens = len([e for e in completed if e["status"] == "BREAKEVEN"])

    # Win rate
    win_rate = (wins / total * 100) if total > 0 else 0

    # Average RR
    rr_values = [e.get("risk_reward", 0) for e in completed if e.get("risk_reward")]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0

    # Average P&L
    pnl_values = [e.get("pnl_pips", 0) for e in completed if e.get("pnl_pips") is not None]
    avg_pnl = sum(pnl_values) / len(pnl_values) if pnl_values else 0
    total_pnl = sum(pnl_values)

    # Best/worst
    best_trade = max(pnl_values) if pnl_values else 0
    worst_trade = min(pnl_values) if pnl_values else 0

    # Best setup type
    setup_counts = {}
    for e in completed:
        patterns = e.get("technical", {}).get("patterns", [])
        for p in patterns:
            setup_counts[p] = setup_counts.get(p, 0) + 1
    best_setup = max(setup_counts, key=setup_counts.get) if setup_counts else "none"

    # Session performance
    session_stats = {}
    for e in completed:
        session = e.get("session", "unknown")
        if session not in session_stats:
            session_stats[session] = {"wins": 0, "losses": 0, "total": 0}
        session_stats[session]["total"] += 1
        if e["status"] == "WIN":
            session_stats[session]["wins"] += 1
        elif e["status"] == "LOSS":
            session_stats[session]["losses"] += 1

    return {
        "period": f"Last {days} days" if days else "All time",
        "total_signals": len(entries),
        "no_signal_days": len(no_signals),
        "open_signals": len(open_signals),
        "completed_trades": total,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "win_rate": round(win_rate, 1),
        "avg_rr": round(avg_rr, 2),
        "avg_pnl_pips": round(avg_pnl, 2),
        "total_pnl_pips": round(total_pnl, 2),
        "best_trade_pips": round(best_trade, 2),
        "worst_trade_pips": round(worst_trade, 2),
        "best_setup": best_setup,
        "session_performance": session_stats,
        "calibration_note": _calibration_note(win_rate, avg_rr),
    }


def _calibration_note(win_rate: float, avg_rr: float) -> str:
    """Generate calibration note based on performance."""
    if win_rate == 0:
        return "No completed trades yet. Track signal accuracy first."

    # Expected value per trade
    ev = (win_rate / 100 * avg_rr) - ((100 - win_rate) / 100)

    if ev > 0.5:
        return f"Excellent edge (EV: {ev:.2f}). Strategy is profitable."
    elif ev > 0:
        return f"Positive edge (EV: {ev:.2f}). Strategy works but can improve."
    elif ev > -0.2:
        return f"Marginal edge (EV: {ev:.2f}). Review strategy parameters."
    else:
        return f"Negative edge (EV: {ev:.2f}). Strategy needs rework."


def weekly_report(weeks_back: int = 1) -> str:
    """
    Generate weekly trading report.
    Args:
        weeks_back: how many weeks back to report
    Returns: formatted report string
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks_back)

    entries = get_signals(days=weeks_back * 7, limit=1000)

    if not entries:
        return "No signals in the past week."

    stats = get_stats(days=weeks_back * 7)

    # Build report
    lines = [
        f"# XAUUSD Weekly Report",
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        f"",
        f"## Summary",
        f"- Total Signals: {stats['total_signals']}",
        f"- No-Signal Days: {stats['no_signal_days']}",
        f"- Open Signals: {stats['open_signals']}",
        f"- Completed: {stats['completed_trades']}",
        f"",
        f"## Performance",
        f"- Win Rate: {stats['win_rate']}%",
        f"- Average RR: {stats['avg_rr']}",
        f"- Total P&L: {stats['total_pnl_pips']} pips",
        f"- Best Trade: {stats['best_trade_pips']} pips",
        f"- Worst Trade: {stats['worst_trade_pips']} pips",
        f"- Best Setup: {stats['best_setup']}",
        f"",
        f"## Calibration",
        f"{stats['calibration_note']}",
        f"",
    ]

    # Session breakdown
    if stats.get("session_performance"):
        lines.append("## Session Performance")
        for session, data in stats["session_performance"].items():
            wr = (data["wins"] / data["total"] * 100) if data["total"] > 0 else 0
            lines.append(f"- {session}: {data['wins']}W/{data['losses']}L ({wr:.0f}%)")
        lines.append("")

    # Individual trades
    completed = [e for e in entries if e.get("status") in ["WIN", "LOSS", "BREAKEVEN"]]
    if completed:
        lines.append("## Trades")
        for e in completed[:10]:  # Last 10 trades
            emoji = "✅" if e["status"] == "WIN" else "❌" if e["status"] == "LOSS" else "➖"
            pnl = e.get("pnl_pips", 0)
            lines.append(
                f"- {emoji} {e['logged_at'][:10]} | {e['signal']} | "
                f"Entry: {e['entry']} → Exit: {e.get('exit_price', '?')} | "
                f"P&L: {pnl:+.2f} pips"
            )

    report = "\n".join(lines)

    # Save to file
    report_file = WEEKLY_DIR / f"report_{end_date.strftime('%Y%m%d')}.md"
    with open(report_file, "w") as f:
        f.write(report)

    return report


# Quick test
if __name__ == "__main__":
    print("=== Journal Test ===")
    stats = get_stats()
    print(json.dumps(stats, indent=2))
