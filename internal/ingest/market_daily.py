"""
WEALTH Daily Market Ingestion — Gold + FX + Derived Signals

Fetches XAU/USD, USD/MYR, derives XAU/MYR per gram.
Stores in market_observation with full provenance.

Designed for systemd timer (daily at 08:00 MYT) or manual run.
No API keys required — uses yfinance + Frankfurter (free).

OBSERVE_ONLY — this script writes data, never recommends or trades.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("wealth.market_daily")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TROY_OZ_TO_GRAMS = 31.1035
MYT = timezone(timedelta(hours=8))
DB_CONTAINER = "postgres"
DB_USER = "arifos_admin"
DB_NAME = "vault999"


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_gold_usd() -> Optional[dict]:
    """Fetch XAU/USD from yfinance (gold futures front month)."""
    try:
        import yfinance as yf

        ticker = yf.Ticker("GC=F")
        price = ticker.info.get("regularMarketPrice")
        prev_close = ticker.info.get("regularMarketPreviousClose")
        if price is None:
            log.warning("yfinance GC=F returned no price")
            return None
        return {
            "instrument": "XAU_USD",
            "metric": "close",
            "value": float(price),
            "unit": "USD/oz",
            "currency": "USD",
            "source": "yfinance:GC=F",
            "confidence": 0.95,
            "extra": {
                "previous_close": prev_close,
                "change_pct": round((price - prev_close) / prev_close * 100, 2)
                if prev_close
                else None,
            },
        }
    except Exception as e:
        log.error("Failed to fetch XAU/USD: %s", e)
        return None


def fetch_usd_myr() -> Optional[dict]:
    """Fetch USD/MYR from yfinance, fallback to Frankfurter."""
    # Primary: yfinance
    try:
        import yfinance as yf

        ticker = yf.Ticker("MYR=X")
        price = ticker.info.get("regularMarketPrice")
        if price:
            return {
                "instrument": "USD_MYR",
                "metric": "close",
                "value": float(price),
                "unit": "MYR/USD",
                "currency": "MYR",
                "source": "yfinance:MYR=X",
                "confidence": 0.90,
            }
    except Exception as e:
        log.warning("yfinance USD/MYR failed: %s", e)

    # Fallback: Frankfurter API
    try:
        import httpx

        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://api.frankfurter.dev/v1/latest",
                params={"base": "USD", "symbols": "MYR"},
            )
            resp.raise_for_status()
            data = resp.json()
            rate = data["rates"]["MYR"]
            return {
                "instrument": "USD_MYR",
                "metric": "close",
                "value": float(rate),
                "unit": "MYR/USD",
                "currency": "MYR",
                "source": "frankfurter",
                "confidence": 0.95,
                "source_timestamp": data.get("date"),
            }
    except Exception as e:
        log.error("Frankfurter USD/MYR also failed: %s", e)
        return None


def derive_xau_myr_gram(gold_usd: float, usd_myr: float) -> dict:
    """Derive XAU/MYR per gram from XAU/USD and USD/MYR."""
    xau_myr_oz = gold_usd * usd_myr
    xau_myr_gram = xau_myr_oz / TROY_OZ_TO_GRAMS
    return {
        "instrument": "XAU_MYR_GRAM",
        "metric": "derived_price",
        "value": round(xau_myr_gram, 2),
        "unit": "MYR/gram",
        "currency": "MYR",
        "source": "derived:xau_usd*usd_myr/31.1035",
        "confidence": 0.90,
        "extra": {
            "xau_usd": gold_usd,
            "usd_myr": usd_myr,
            "xau_myr_oz": round(xau_myr_oz, 2),
        },
    }


# ---------------------------------------------------------------------------
# Database writer (via docker exec — no psql auth needed)
# ---------------------------------------------------------------------------

def _hash_payload(payload: dict) -> str:
    """SHA-256 of JSON payload for dedup."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def store_observation(obs: dict) -> bool:
    """Insert one observation into market_observation via docker exec."""
    now = datetime.now(MYT).isoformat()
    payload_hash = _hash_payload(obs)
    extra = obs.get("extra", {})

    # Build INSERT — use parameterized query via shell escaping
    value = obs["value"]
    if value is None:
        return False

    sql = f"""
    INSERT INTO market_observation
        (observed_at, instrument, metric, value, unit, currency,
         source, source_timestamp, confidence, payload_hash)
    VALUES (
        '{now}',
        '{obs["instrument"]}',
        '{obs["metric"]}',
        {value},
        '{obs.get("unit", "")}',
        '{obs.get("currency", "")}',
        '{obs["source"]}',
        '{obs.get("source_timestamp", now)}',
        {obs.get("confidence", 1.0)},
        '{payload_hash}'
    )
    ON CONFLICT DO NOTHING;
    """

    try:
        result = subprocess.run(
            ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            log.info("Stored: %s = %s %s", obs["instrument"], value, obs.get("unit", ""))
            return True
        else:
            log.error("DB insert failed: %s", result.stderr)
            return False
    except Exception as e:
        log.error("DB exec failed: %s", e)
        return False


def store_signal(signal: dict) -> bool:
    """Insert a derived signal into market_signal."""
    now = datetime.now(MYT).isoformat()
    value = signal.get("value")
    if value is None:
        return False

    evidence_json = json.dumps(signal.get("evidence_refs", []))

    sql = f"""
    INSERT INTO market_signal
        (calculated_at, instrument, signal_type, horizon, value,
         regime_label, severity, evidence_refs, model_version)
    VALUES (
        '{now}',
        '{signal["instrument"]}',
        '{signal["signal_type"]}',
        '{signal.get("horizon", "daily")}',
        {value},
        '{signal.get("regime_label", "")}',
        '{signal.get("severity", "info")}',
        '{evidence_json}',
        '{signal.get("model_version", "v1")}'
    );
    """

    try:
        result = subprocess.run(
            ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            log.info("Signal stored: %s/%s = %s", signal["instrument"], signal["signal_type"], value)
            return True
        else:
            log.error("Signal insert failed: %s", result.stderr)
            return False
    except Exception as e:
        log.error("Signal exec failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_daily_ingestion() -> dict:
    """Run the full daily market ingestion pipeline.

    Returns summary dict for logging / MCP response.
    """
    log.info("=== WEALTH Daily Market Ingestion ===")
    results = {"timestamp": datetime.now(MYT).isoformat(), "observations": [], "signals": []}

    # 1. Fetch XAU/USD
    gold = fetch_gold_usd()
    if gold:
        store_observation(gold)
        results["observations"].append(gold["instrument"])

    # 2. Fetch USD/MYR
    fx = fetch_usd_myr()
    if fx:
        store_observation(fx)
        results["observations"].append(fx["instrument"])

    # 3. Derive XAU/MYR per gram
    if gold and fx:
        derived = derive_xau_myr_gram(gold["value"], fx["value"])
        store_observation(derived)
        results["observations"].append(derived["instrument"])

        # Store as a signal too (the key Arif-specific metric)
        store_signal({
            "instrument": "XAU_MYR_GRAM",
            "signal_type": "decompose",
            "horizon": "daily",
            "value": derived["value"],
            "severity": "info",
            "evidence_refs": [
                {"instrument": "XAU_USD", "value": gold["value"]},
                {"instrument": "USD_MYR", "value": fx["value"]},
            ],
        })
        results["signals"].append("XAU_MYR_GRAM/decompose")

    # 4. Compute daily change if we have gold
    if gold and gold.get("extra", {}).get("change_pct") is not None:
        change = gold["extra"]["change_pct"]
        severity = "alert" if abs(change) > 3 else "caution" if abs(change) > 1.5 else "info"
        if severity != "info":
            store_signal({
                "instrument": "XAU_USD",
                "signal_type": "daily_move",
                "horizon": "daily",
                "value": change,
                "severity": severity,
                "regime_label": "volatile" if abs(change) > 3 else "active",
            })
            results["signals"].append(f"XAU_USD/daily_move ({change:+.1f}%)")

    log.info("Ingestion complete: %d observations, %d signals",
             len(results["observations"]), len(results["signals"]))
    return results


def get_latest_gold_snapshot() -> dict:
    """Query latest gold data from DB for MCP tool consumption."""
    sql = """
    SELECT instrument, value, unit, source, observed_at
    FROM market_observation
    WHERE instrument IN ('XAU_USD', 'USD_MYR', 'XAU_MYR_GRAM')
      AND observed_at > now() - interval '2 days'
    ORDER BY observed_at DESC
    LIMIT 6;
    """
    try:
        result = subprocess.run(
            ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME,
             "-t", "-A", "-F", "|", "-c", sql],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}

        rows = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 5:
                rows.append({
                    "instrument": parts[0],
                    "value": float(parts[1]),
                    "unit": parts[2],
                    "source": parts[3],
                    "observed_at": parts[4],
                })

        # Dedupe — keep latest per instrument
        latest = {}
        for row in rows:
            inst = row["instrument"]
            if inst not in latest:
                latest[inst] = row

        return {
            "mcp": "WEALTH",
            "tool": "wealth_market_data",
            "mode": "gold",
            "currency": "MYR",
            "snapshot": latest,
            "recommendation_only": True,
            "final_authority": "Arif",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--snapshot":
        snap = get_latest_gold_snapshot()
        print(json.dumps(snap, indent=2, default=str))
    else:
        results = run_daily_ingestion()
        print(json.dumps(results, indent=2, default=str))
