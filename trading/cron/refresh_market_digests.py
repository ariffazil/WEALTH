#!/usr/bin/env python3
"""
refresh_market_digests.py — Refresh all 5 market digests (gold, oil, gas, klci, usdmyr)
Writes to BOTH:
  - /root/arif-fazil.com/sites/arif-fazil.com/dist/data/markets/*.json  (source-of-truth)
  - /var/www/html/arif/data/markets/*.json                                  (Caddy-served public copy)

Forged 2026-08-11 by 333-AGI after discovering the trading digest was STALE.
Daily use by /etc/cron.d/trading-scan.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import yfinance as yf, json, math, hashlib, sys, traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

MYT = timezone(timedelta(hours=8))
OUT = Path("/root/arif-fazil.com/sites/arif-fazil.com/dist/data/markets")
WWW = Path("/var/www/html/arif/data/markets")
LOG = Path("/var/log/arifos/trading-scan-refresh.log")

# Ensure dirs exist
OUT.mkdir(parents=True, exist_ok=True)
WWW.mkdir(parents=True, exist_ok=True)


def safe_float(v):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:
        return None


def fetch(symbol, period="1y"):
    try:
        h = yf.Ticker(symbol).history(period=period, interval="1d")
        if len(h) < 1:
            return None, None
        closes = [
            safe_float(c) for c in h["Close"].tolist() if safe_float(c) is not None
        ]
        return closes, safe_float(h["Close"].iloc[-1])
    except Exception as e:
        LOG.write_text(
            LOG.read_text() + f"\n{fetch.__name__}({symbol}) err: {e}\n"
        ) if LOG.exists() else None
        return None, None


def ema(arr, p):
    if len(arr) < p:
        return None
    k = 2 / (p + 1)
    e = arr[0]
    for x in arr[1:]:
        e = x * k + e * (1 - k)
    return round(e, 4)


def rsi(arr, p=14):
    if len(arr) < p + 1:
        return None, None
    g, l = [], []
    for i in range(1, len(arr)):
        d = arr[i] - arr[i - 1]
        g.append(max(d, 0))
        l.append(max(-d, 0))
    ag = sum(g[-p:]) / p
    al = sum(l[-p:]) / p
    if al == 0:
        return 100.0, "OVERBOUGHT"
    rsi = 100 - 100 / (1 + ag / al)
    state = "OVERBOUGHT" if rsi >= 70 else ("OVERSOLD" if rsi <= 30 else "NEUTRAL")
    return round(rsi, 1), state


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()[:64]


def emit(name_ms, name_en, sym_disp, yf_sym, role_ms, role_en, fname):
    NOW = datetime.now(MYT)
    NOW_UTC = datetime.now(timezone.utc)
    closes, last = fetch(yf_sym)
    if not closes or last is None:
        return f"❌ {sym_disp}: no data from yfinance"
    prev = closes[-2] if len(closes) >= 2 else last
    chg = last - prev
    chg_pct = (chg / prev * 100) if prev else 0
    e20 = ema(closes[-30:], 20)
    e50 = ema(closes[-60:] if len(closes) >= 60 else closes, 50)
    r, rs = rsi(closes, 14)
    trend = "?"
    if e20 is not None and e50 is not None:
        trend = (
            "BULLISH"
            if e20 > e50 * 1.005
            else ("BEARISH" if e20 < e50 * 0.995 else "NEUTRAL")
        )
    else:
        trend = "?"
    if r and r >= 70:
        sig = "OVERBOUGHT"
    elif r and r <= 30:
        sig = "OVERSOLD"
    elif trend == "BULLISH":
        sig = "BUY"
    elif trend == "BEARISH":
        sig = "SELL"
    else:
        sig = "HOLD"
    COH = f"arif:trading:{NOW.date().isoformat()}:{NOW_UTC.isoformat()}:{sym_disp}"
    dig = {
        "schema": "market_digest.v1",
        "subject": {
            "type": "FinancialInstrument",
            "name_ms": name_ms,
            "name_en": name_en,
            "symbol": sym_disp,
            "exchange": "yfinance",
        },
        "seal": {
            "observed_at": NOW_UTC.isoformat().replace("+00:00", "Z"),
            "coherence_id": sha(f"{COH}:{last}"),
            "engine": "WEALTH institutional intelligence (yfinance)",
        },
        "one_liner": {
            "ms": f"{name_ms} pada {last:,.2f} · perubahan {chg:+.2f} ({chg_pct:+.2f}%)",
            "en": f"{name_en} at {last:,.2f} · {chg:+.2f} ({chg_pct:+.2f}%) change",
        },
        "role": {"ms": role_ms, "en": role_en},
        "obs_facts": {
            "price": round(last, 4),
            "change": round(chg, 4),
            "change_pct": round(chg_pct, 2),
            "rsi": r,
            "rsi_state": rs,
            "ema20": e20,
            "ema50": e50,
            "ema_trend": trend,
            "signal": sig,
            "epistemic_class": "OBS",
            "source": "yfinance via WEALTH refresh",
        },
        "interpretation_int": [
            f"RSI {r} is in {rs} zone",
            f"EMA trend is {trend} — price vs EMA50",
            f"Signal: {sig}",
        ],
        "refresh_chain": {
            "tick": "scheduled_refresh",
            "by": "refresh_market_digests.py",
            "freshness_minutes": 0,
        },
    }
    target = OUT / fname
    target.write_text(json.dumps(dig, indent=2, ensure_ascii=False))
    import shutil

    shutil.copy(target, WWW / fname)
    return f"✅ {name_en:18s} → {fname:32s} ({last}) RSI={r} [{sig}]"


def main():
    NOW_UTC = datetime.now(timezone.utc).isoformat()
    log_lines = [f"\n=== refresh @ {NOW_UTC} ==="]
    try:
        log_lines.append(
            emit(
                "Emas (XAU/USD)",
                "Gold",
                "GC=F",
                "GC=F",
                "Pelindung nilai · Lindung inflasi · Aset rizab",
                "Store of value · Inflation hedge · Reserve asset",
                "gold_digest.json",
            )
        )
        log_lines.append(
            emit(
                "Minyak Brent",
                "Brent Oil",
                "BZ=F",
                "BZ=F",
                "Penanda harga minyak global · Penanda chokepoint",
                "Global oil benchmark · Chokepoint indicator",
                "oil_digest.json",
            )
        )
        log_lines.append(
            emit(
                "Gas Asli (NG)",
                "Natural Gas",
                "NG=F",
                "NG=F",
                "Tenaga · Penanda geopolitik",
                "Energy · Geopolitical indicator",
                "gas_digest.json",
            )
        )
        log_lines.append(
            emit(
                "FBM KLCI",
                "FBM KLCI",
                "^KLSE",
                "^KLSE",
                "Indeks Bursa Malaysia · Penanda domestik",
                "Bursa Malaysia benchmark · Domestic indicator",
                "klci_digest.json",
            )
        )
        log_lines.append(
            emit(
                "USD/MYR",
                "USDMYR",
                "USDMYR=X",
                "USDMYR=X",
                "Pertukaran USD→MYR · Penanda tekanan mata wang",
                "USD→MYR exchange · Currency pressure indicator",
                "usdmyr_digest.json",
            )
        )
        log_lines.append("✅ all 5 refreshed")
    except Exception as e:
        log_lines.append(f"❌ {type(e).__name__}: {e}")
        log_lines.append(traceback.format_exc())
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()
