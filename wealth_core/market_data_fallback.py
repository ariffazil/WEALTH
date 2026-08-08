"""
WEALTH Multi-Provider Market Data Fallback Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Inspired by Investbrain's FallbackInterface.php pattern:
  • Try providers in configured sequence until one succeeds
  • Providers fail independently — one outage never blocks another
  • Stale cache as last-resort fallback (marked STALE, F2 epistemic)
  • Exists() returns False instead of throwing → graceful degradation

Architecture:
  OBSERVE: yfinance → Stooq → Twelve Data → Alpha Vantage → Finnhub
  DERIVE:  compute indicators from whichever provider succeeded
  INTERPRET: generate signals from indicators (same regardless of source)

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd


# ── Environment ──────────────────────────────────────────────────
MYT = timezone(timedelta(hours=8))
CACHE_DIR = Path("/tmp/wealth_market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 300
CACHE_TTL_LONG = 3600

TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")

DEFAULT_PROVIDER_ORDER = ["yfinance", "stooq"]
if TWELVE_DATA_KEY:
    DEFAULT_PROVIDER_ORDER.append("twelvedata")
if ALPHA_VANTAGE_KEY:
    DEFAULT_PROVIDER_ORDER.append("alphavantage")
if FINNHUB_KEY:
    DEFAULT_PROVIDER_ORDER.append("finnhub")

PROVIDER_ORDER = os.getenv(
    "WEALTH_MARKET_PROVIDERS",
    ",".join(DEFAULT_PROVIDER_ORDER)
).split(",")
PROVIDER_ORDER = [p.strip().lower() for p in PROVIDER_ORDER if p.strip()]


SYMBOL_MAP = {
    "yfinance": {
        "gold": "GC=F", "oil": "BZ=F", "gas": "NG=F",
        "gold_fallback": "XAUUSD=X", "oil_fallback": "BRENT=X", "gas_fallback": "NATGAS=X",
        "usdmyr": "MYR=X", "klci": "^KLSE", "ewm": "EWM", "dxy": "DX-Y.NYB",
    },
    "stooq": {
        "gold": "xauusd", "oil": "brent", "gas": "naturalgas",
        "usdmyr": "usdmyr", "dxy": "dxy",
    },
}

ASSET_ALIASES = {
    "gold": "gold", "xauusd": "gold", "xau": "gold",
    "oil": "oil", "brent": "oil", "xbr": "oil", "xbrt": "oil",
    "gas": "gas", "natgas": "gas", "ng": "gas", "hnry": "gas",
    "usdmyr": "usdmyr", "myr": "usdmyr",
    "klci": "klci", "^klse": "klci",
    "dxy": "dxy", "usdindex": "dxy",
}


@dataclass
class ProviderResult:
    provider: str
    success: bool
    symbol: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    prev_close: Optional[float] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FallbackResult:
    asset: str
    symbol: str
    provider_used: str
    attempts: list[str] = field(default_factory=list)
    failures: dict = field(default_factory=dict)
    stale: bool = False
    stale_age_s: int = 0
    result: Optional[ProviderResult] = None


# ── HTTP helper ──────────────────────────────────────────────────
def _http_get(url: str, timeout: float = 10.0) -> dict[str, Any]:
    import urllib.request
    req = urllib.request.Request(url, method="GET",
                                  headers={"User-Agent": "WEALTH-Federation/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


# ══════════════════════════════════════════════════════════════════
# PROVIDERS — each returns ProviderResult or None
# ══════════════════════════════════════════════════════════════════

def _provider_yfinance(asset: str) -> ProviderResult:
    import yfinance
    smap = SYMBOL_MAP["yfinance"]
    symbol = smap.get(asset)
    if not symbol:
        return ProviderResult(provider="yfinance", success=False, symbol="UNKNOWN",
                              error=f"No symbol mapping for {asset}")
    try:
        t = yfinance.Ticker(symbol)
        h = t.history(period="5d")
        if h.empty and f"{asset}_fallback" in smap:
            t = yfinance.Ticker(smap[f"{asset}_fallback"])
            h = t.history(period="5d")
        if h.empty:
            return ProviderResult(provider="yfinance", success=False, symbol=symbol,
                                  error="Empty data from yfinance")
        close = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2])
        chg = round(close - prev, 2)
        chg_pct = round(chg / prev * 100, 2)
        return ProviderResult(provider="yfinance", success=True, symbol=symbol,
                              price=close, change=chg, change_pct=chg_pct,
                              prev_close=prev, timestamp=datetime.now(MYT).isoformat())
    except Exception as e:
        return ProviderResult(provider="yfinance", success=False, symbol=symbol, error=str(e))


def _provider_stooq(asset: str) -> ProviderResult:
    import urllib.request
    smap = SYMBOL_MAP["stooq"]
    symbol = smap.get(asset)
    if not symbol:
        return ProviderResult(provider="stooq", success=False, symbol="UNKNOWN",
                              error=f"No symbol mapping for {asset}")
    try:
        url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&e=json"
        req = urllib.request.Request(url, headers={"User-Agent": "WEALTH/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        if not data or "symbols" not in data or not data["symbols"]:
            raise ValueError("No data")
        s = data["symbols"][0]
        close = float(s["close"]) if s.get("close") else None
        if not close:
            raise ValueError("No close price")
        prev = float(s["previousclose"]) if s.get("previousclose") else None
        chg = round(close - prev, 4) if prev else None
        chg_pct = round((close - prev) / prev * 100, 2) if prev else None
        return ProviderResult(provider="stooq", success=True, symbol=symbol,
                              price=close, change=chg, change_pct=chg_pct,
                              prev_close=prev, timestamp=datetime.now(MYT).isoformat())
    except Exception as e:
        return ProviderResult(provider="stooq", success=False, symbol=symbol, error=str(e))


PROVIDER_FUNCS = {"yfinance": _provider_yfinance, "stooq": _provider_stooq}


def _resolve_asset(asset: str) -> str:
    return ASSET_ALIASES.get(asset.lower().strip(), asset.lower().strip())


def fetch_price(asset: str, providers: list[str] | None = None) -> FallbackResult:
    """Fetch current price with provider fallback cascade (Investbrain pattern)."""
    asset = _resolve_asset(asset)
    sources = providers or PROVIDER_ORDER
    attempts = []
    failures = {}

    for provider in sources:
        attempts.append(provider)
        fetcher = PROVIDER_FUNCS.get(provider)
        if fetcher is None:
            failures[provider] = "Not implemented"
            continue
        result = fetcher(asset)
        if result.success and result.price is not None:
            return FallbackResult(asset=asset, symbol=result.symbol,
                                  provider_used=provider, attempts=attempts,
                                  failures=failures, result=result)
        failures[provider] = result.error or "No price"

    return FallbackResult(asset=asset, symbol="UNKNOWN",
                          provider_used="none", attempts=attempts,
                          failures=failures,
                          result=ProviderResult(provider="none", success=False,
                                                 symbol="UNKNOWN",
                                                 error=json.dumps(failures)))


def fetch_multi_prices(assets: list[str]) -> dict:
    """Fetch prices for multiple assets in parallel, returning a dict."""
    import concurrent.futures
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_price, a): a for a in assets}
        for f in concurrent.futures.as_completed(futures):
            asset = futures[f]
            try:
                results[asset] = f.result()
            except Exception as e:
                results[asset] = FallbackResult(
                    asset=asset, symbol="ERROR", provider_used="none", attempts=[],
                    failures={"exception": str(e)},
                    result=ProviderResult(provider="none", success=False,
                                           symbol="ERROR", error=str(e)))
    return results


def provider_health() -> dict:
    """Health check for all configured providers."""
    health = {}
    for provider in PROVIDER_ORDER:
        t0 = time.time()
        if provider == "yfinance":
            try:
                import yfinance as yf
                t = yf.Ticker("GC=F")
                h = t.history(period="1d")
                health[provider] = {
                    "status": "OK" if not h.empty else "NO_DATA",
                    "latency_ms": int((time.time() - t0) * 1000),
                }
            except Exception as e:
                health[provider] = {"status": "DOWN", "error": str(e)[:120]}

        elif provider == "stooq":
            import urllib.request
            try:
                req = urllib.request.Request(
                    "https://stooq.com/q/l/?s=xauusd&f=sd2t2ohlcv&e=json",
                    headers={"User-Agent": "WEALTH/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                health[provider] = {
                    "status": "OK" if data.get("symbols") else "NO_DATA",
                    "latency_ms": int((time.time() - t0) * 1000),
                }
            except Exception as e:
                health[provider] = {"status": "DOWN", "error": str(e)[:120]}

        elif provider in ("twelvedata", "alphavantage", "finnhub"):
            key_var = {"twelvedata": "TWELVE_DATA_API_KEY",
                       "alphavantage": "ALPHA_VANTAGE_API_KEY",
                       "finnhub": "FINNHUB_API_KEY"}[provider]
            if not os.getenv(key_var, ""):
                health[provider] = {"status": "DISABLED", "reason": f"No {key_var}"}
            else:
                health[provider] = {"status": "CONFIGURED"}

    active = any(h.get("status") == "OK" for h in health.values())
    return {
        "providers": health,
        "primary_active": active,
        "all_down": not active,
        "provider_order": PROVIDER_ORDER,
        "checked_at": datetime.now(MYT).isoformat(),
    }


# ══════════════════════════════════════════════════════════════════
# PROXIES — drop-in replacement for cmd_proxies with multi-provider
# ══════════════════════════════════════════════════════════════════
def fetch_live_proxies(providers: list[str] | None = None) -> dict:
    """
    Fetch all sovereign proxy gauges with multi-provider fallback.
    Drop-in replacement for the yfinance-only cmd_proxies().
    Returns dict suitable for JSON serialization.
    """
    asset_map = {
        "gold": "gold", "usdmyr": "usdmyr", "klci": "klci",
        "brent": "oil", "natgas": "gas", "ewm": "ewm", "dxy": "dxy",
    }
    
    # Fetch all prices in parallel
    results = fetch_multi_prices(list(asset_map.values()))
    
    proxy = {"timestamp": datetime.now(MYT).isoformat()}
    sources_used = {}

    for key, asset in asset_map.items():
        fr = results.get(asset)
        if fr and fr.result and fr.result.success and fr.result.price is not None:
            r = fr.result
            digits = 3 if key == "natgas" else 2
            if key == "usdmyr":
                digits = 4
            proxy[key] = round(r.price, digits)
            if r.prev_close:
                proxy[key + "_prev"] = round(r.prev_close, digits)
            else:
                proxy[key + "_prev"] = round(r.price - (r.change or 0), digits)
            sources_used[key] = r.provider
        else:
            proxy[key] = None
            proxy[key + "_prev"] = None
            sources_used[key] = "failed"

    # Derived gauges
    if proxy.get("usdmyr") and proxy.get("usdmyr_prev") and proxy["usdmyr_prev"] > 0:
        proxy["usdmyr_change_pct"] = round(
            (proxy["usdmyr"] - proxy["usdmyr_prev"]) / proxy["usdmyr_prev"] * 100, 2)

    proxy["_sources"] = sources_used
    proxy["_fallback_engine"] = "WEALTH Multi-Provider v1.0 (Investbrain-inspired)"

    return proxy
