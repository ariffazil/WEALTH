#!/usr/bin/env python3
"""
energy_market_grounding.py — WEALTH Energy & Petroleum Commodity Grounding
==========================================================================
STATUS: F13 RATIFIED (2026-09-24) — Bridges WEALTH to Alexandria Grounding.

Provides live, contracted commodity pricing & physical positioning data
for petroleum capital evaluations (EMV, Capex at risk, dry hole cost benchmarks).

Sources:
  - eia-gov (U.S. Energy Information Administration - Official spot prices)
  - cftc (Commodity Futures Trading Commission - Managed money positioning)
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Connect to Alexandria Grounding
sys.path.insert(0, "/root/scripts")
try:
    from alexandria_grounding import AlexandriaGrounding
except ImportError:
    from AAA.scripts.alexandria_grounding import AlexandriaGrounding


def get_brent_spot_price() -> dict:
    """Fetches official European Brent crude spot price FOB ($/bbl)."""
    options = {"route": "petroleum/pri/spt", "frequency": "daily", "page_size": 100}
    res = AlexandriaGrounding.fetch_evidence(
        provider="eia-gov",
        capability="energy-data/data",
        options=options,
        requested_by="WEALTH/PetroleumEconomics",
    )

    raw_data = res.get("data", {})
    if isinstance(raw_data, dict):
        records = raw_data.get("records", [])
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = []

    # Filter for Brent series
    brent_records = [
        r
        for r in records
        if isinstance(r, dict)
        and r.get("facets", {}).get("product", {}).get("code") == "EPCBRENT"
    ]

    latest = brent_records[0] if brent_records else (records[0] if records else {})
    val = latest.get("values", {}).get("value")
    period = latest.get("period")

    return {
        "commodity": "Brent Crude Oil (FOB)",
        "price_usd": float(val) if val else None,
        "unit": latest.get("units", {}).get("value", "$/BBL"),
        "date": period,
        "series": latest.get("facets", {})
        .get("series", {})
        .get("name", "Europe Brent Spot Price"),
        "trace_id": res["evidence_packet"]["trace_id"],
        "truth_class": "MEASURED",
    }


if __name__ == "__main__":
    print("Fetching live Brent Crude Spot Price via Alexandria...")
    data = get_brent_spot_price()
    print(
        f"  [SUCCESS] {data['commodity']}: ${data['price_usd']} {data['unit']} as of {data['date']}"
    )
    print(f"  Trace ID: {data['trace_id']} (Truth Class: {data['truth_class']})")


# ═══════════════════════════════════════════════════════════════════════════
# CFTC Commitment of Traders — managed-money positioning
# STATUS: added 2026-09-24 (EXEC-3). Grounding modal petroleum: bukan sekadar
# harga spot — tahu bila hedge fund over-leveraged long/short minyak mentah.
# Sumber: cftc/disaggregated/futures-only via Alexandria.
# truth_class: MEASURED (positioning), REPORTED (interpretation).
# ═══════════════════════════════════════════════════════════════════════════


def get_crude_positioning() -> dict:
    """Fetches CFTC Disaggregated Futures-Only — managed money net length in crude.

    Reads the positioning that sits BEHIND the spot price: when managed money is
    extremely net-long, the price is crowded; extremely net-short, it is fragile.
    This is the capital-reality half of a dry hole — not just the rock-reality half.
    """
    options = {
        "frequency": "weekly",
        "page_size": 104,  # ~2 years of weekly reports
    }
    res = AlexandriaGrounding.fetch_evidence(
        provider="cftc",
        capability="disaggregated/futures-only",
        options=options,
        requested_by="WEALTH/PetroleumEconomics",
    )

    raw_data = res.get("data", {})
    if isinstance(raw_data, dict):
        records = raw_data.get("records", [])
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = []

    # Crude Oil Only (futures-only disaggregated) — contract code WTI
    crude = [
        r
        for r in records
        if isinstance(r, dict)
        and (
            (r.get("facets", {}).get("contract", {}).get("code") in ("WTI", "067651"))
            or (
                "crude"
                in str(r.get("facets", {}).get("commodity", {}).get("name", "")).lower()
            )
        )
    ]

    if not crude:
        return {
            "commodity": "WTI Crude — Managed Money Positioning",
            "net_length": None,
            "records": 0,
            "trace_id": res["evidence_packet"]["trace_id"],
            "truth_class": "MEASURED",
            "note": "no crude records in response — verify provider facet mapping",
        }

    def _mv(rec, field):
        v = rec.get("values", {}).get(field)
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    latest = crude[0]
    longs = _mv(latest, "mm_long_all") or _mv(latest, "m_money_long_all")
    shorts = _mv(latest, "mm_short_all") or _mv(latest, "m_money_short_all")
    spread = _mv(latest, "mm_spread_all") or _mv(latest, "m_money_spread_all")
    net = (longs - shorts) if (longs is not None and shorts is not None) else None

    net_series = []
    for r in crude:
        l = _mv(r, "mm_long_all") or _mv(r, "m_money_long_all")
        s = _mv(r, "mm_short_all") or _mv(r, "m_money_short_all")
        p = r.get("period")
        if l is not None and s is not None:
            net_series.append({"period": p, "net": l - s, "long": l, "short": s})

    # Crowding read — INTERPRETATION, capped confidence (F7)
    crowd = "UNMEASURED"
    if net_series:
        vals = [x["net"] for x in net_series]
        lo, hi = min(vals), max(vals)
        cur = vals[0]
        span = (hi - lo) or 1
        pct = (cur - lo) / span
        if pct >= 0.90:
            crowd = "EXTREME_NET_LONG"
        elif pct >= 0.70:
            crowd = "CROWDED_LONG"
        elif pct <= 0.10:
            crowd = "EXTREME_NET_SHORT"
        elif pct <= 0.30:
            crowd = "CROWDED_SHORT"
        else:
            crowd = "NEUTRAL"

    return {
        "commodity": "WTI Crude — Managed Money Positioning",
        "as_of": latest.get("period"),
        "managed_money_long": longs,
        "managed_money_short": shorts,
        "managed_money_spread": spread,
        "net_length": net,
        "crowding": crowd,
        "crowding_truth_class": "INTERPRETATION",
        "history_weeks": len(net_series),
        "net_series_head": net_series[:6],
        "trace_id": res["evidence_packet"]["trace_id"],
        "truth_class": "MEASURED",
    }


def get_energy_grounding_summary() -> dict:
    """Combined grounding: spot price + managed-money positioning."""
    return {
        "brent_spot": get_brent_spot_price(),
        "wti_positioning": get_crude_positioning(),
    }
