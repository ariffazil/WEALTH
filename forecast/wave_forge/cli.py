#!/usr/bin/env python3
"""GOLD_WAVE_FORGE — canonical verdict CLI.

Runs the full 8-agent challenger pipeline on the configured XAUUSD
history and prints the admission verdict to stdout. The exit code is:

* 0  — admission=PASS (verdict=USE)
* 2  — admission=FAIL but verdict is HOLD (the admission rule failed)
* 3  — verdict=QUARANTINE (some upstream gate failed)

The pipeline NEVER auto-promotes; an exit code of 0 only means the
admission rule passed the challenger through. Promotion out of
SHADOW_CHALLENGER still requires an explicit F13 authorization.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GOLD_WAVE_FORGE challenger verdict")
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--ensemble-size", type=int, default=50)
    parser.add_argument(
        "--no-receipt",
        action="store_true",
        help="skip writing the VAULT999 receipt (for offline replays)",
    )
    parser.add_argument(
        "--receipts-dir",
        default="/root/AAA/VAULT999/receipts",
        help="override the VAULT999 receipts directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the full forecast packet as JSON to stdout",
    )
    args = parser.parse_args(argv)

    # Import locally so that ``--help`` works without importing scipy/pywt.
    from wave_forge import run_wave_forge

    receipts_dir = Path(args.receipts_dir)
    if not args.no_receipt:
        receipts_dir.mkdir(parents=True, exist_ok=True)
    res = run_wave_forge(
        days=args.days,
        seed=args.seed,
        ensemble_size=args.ensemble_size,
        write_receipt=not args.no_receipt,
        receipts_dir=receipts_dir if not args.no_receipt else None,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2, default=str))
    else:
        # Compact verdict.
        verdict = res.verdict.verdict if res.verdict else "NONE"
        print(f"forecast_id: {res.forecast_id}")
        print(f"status:      {res.status}")
        print(f"admission:   {res.admission}")
        print(f"verdict:     {verdict}")
        print(f"reason:      {res.verdict.reason_codes if res.verdict else []}")
        print(f"skill M0:    {res.audit.skill_vs_M0:+.4f}" if res.audit else "  n/a")
        print(f"skill M2:    {res.audit.skill_vs_M2:+.4f}" if res.audit else "  n/a")
        print(f"skill M4T:   {res.audit.skill_vs_M4_TREND:+.4f}" if res.audit else "  n/a")
        print(f"stability:   {res.stability.endpoint_stability:.4f}" if res.stability else "  n/a")
        if res.receipt:
            print(f"receipt:     {res.receipt.receipt_uri}")
        if res.admission_failed_receipt:
            print(f"adm-failed:  {res.admission_failed_receipt['receipt_uri']}")

    if res.admission == "PASS":
        return 0
    if verdict == "QUARANTINE":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())