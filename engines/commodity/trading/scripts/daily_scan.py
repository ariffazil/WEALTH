#!/usr/bin/env python3
"""
Daily XAUUSD scan — runs at 8am MYT (00:00 UTC).
Generates signal, logs to journal, outputs briefing.
"""
import sys
sys.path.insert(0, "/root/trading")

import json
from datetime import datetime
from signals.daily_briefing import generate_briefing, format_briefing_telegram, format_briefing_simple
from signals.journal import log_signal

def main():
    print(f"[{datetime.now().isoformat()}] Starting daily XAUUSD scan...")

    # Generate briefing
    briefing = generate_briefing()

    # Log signal if exists
    signal = briefing.get("signal", {})
    if signal.get("signal") != "NO_SIGNAL":
        logged = log_signal(signal)
        print(f"Signal logged: {logged.get('id')}")

    # Output briefing (telegram format for cron delivery)
    telegram = format_briefing_telegram(briefing)
    print(telegram)

    # Save to file for delivery
    output_file = f"/root/trading/logs/briefing_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(output_file, "w") as f:
        f.write(telegram)

    print(f"\nBriefing saved to: {output_file}")

    # Also save raw JSON for debugging
    json_file = f"/root/trading/logs/briefing_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_file, "w") as f:
        json.dump(briefing, f, indent=2, default=str)

    return briefing

if __name__ == "__main__":
    main()
