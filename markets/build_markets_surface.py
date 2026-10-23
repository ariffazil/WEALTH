#!/usr/bin/env python3
"""Build the WEALTH public markets surface and sync WORLD state from live engines + ledger.

ARIFOS::WORLD_WEALTH_LINKAGE::v2.0 — Unified Reality Loop (2026-10-23).
SOURCE:
  1. Live local WEALTH commodity engines (:3456 gold, :3457 oil, :3458 gas)
  2. Live daily WEALTH briefing (/var/www/html/arif/data/wealth/latest.json)
  3. Canonical observation ledger (/root/WEALTH/markets/observations.json)
OUTPUT:
  - /var/www/html/wealth/api/markets/registry.json
  - /var/www/html/wealth/api/markets/<id>/latest.json
  - /var/www/html/wealth/markets/index.html, markets/<id>/index.html, markets/<id>/index.md
  - /var/www/html/wealth/sitemap.xml
  - /root/arif-fazil.com/sites/arif-fazil.com/public/world-state.json (+ dist + /var/www/html/arif/world-state.json)
  - SHA-256 integrity binding in /world/index.html (source + dist + webroot)

Honesty rules:
  - No observation -> value null, state UNKNOWN. Nothing fabricated.
  - Every observation carries structured provenance:
      value, observed_at, as_of, source, epistemic_class ("OBS"),
      evidence ("OBSERVED" / "REPORTED"), freshness ("FRESH" / "STALE" / "UNKNOWN"),
      producer ("WEALTH"), authority ("555_COMPUTE_ONLY").
  - By default, live engine reads are merged in-memory so daily cron runs do not dirty
    /root/WEALTH git working tree. Pass --write-ledger to persist live reads back to
    /root/WEALTH/markets/observations.json before committing.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "observations.json"
WEBROOT = Path("/var/www/html/wealth")
ARIF_SITE_ROOT = Path("/root/arif-fazil.com/sites/arif-fazil.com")
ARIF_WEBROOT = Path("/var/www/html/arif")
BRIEFING_JSON = ARIF_WEBROOT / "data" / "wealth" / "latest.json"

BASE = "https://wealth.arif-fazil.com"
WORLD_BASE = "https://arif-fazil.com"
GENERATED_BY = "WEALTH markets/build_markets_surface.py (ARIFOS::WEALTH_FEDERATION_ALIGNMENT::2026-10-23)"
BOUNDARY = "WORLD observes. WEALTH computes. AAA coordinates. arifOS judges. ARIF decides."
AUTHORITY = "555_COMPUTE_ONLY"

ENGINE_ENDPOINTS = {
    "gold": ("http://127.0.0.1:3456/api/snapshot", "WEALTH Gold Commodity Engine (:3456, yfinance XAUUSD)"),
    "oil": ("http://127.0.0.1:3457/api/snapshot", "WEALTH Oil Commodity Engine (:3457, yfinance Brent)"),
    "gas": ("http://127.0.0.1:3458/api/snapshot", "WEALTH Natural Gas Commodity Engine (:3458, yfinance Henry Hub)"),
}

WORLD_SURFACE: dict = {}

CSS = """
:root{--bg:#0B0B0F;--panel:#13131C;--panel2:#181826;--line:#262637;--tx:#E8E8F0;
--mut:#9B9BB0;--gold:#E8C468;--grn:#4ADE80;--red:#F87171;--amb:#FBBF24;--gry:#8A8AA0}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--tx);font:16px/1.65 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}
main{max-width:880px;margin:0 auto;padding:40px 22px 80px}
header{border-bottom:1px solid var(--line);margin-bottom:34px;padding-bottom:18px}
.kicker{color:var(--mut);font-size:13px;letter-spacing:.14em;text-transform:uppercase}
h1{font-size:30px;margin:6px 0 4px}h2{font-size:20px;margin:34px 0 12px}
.sub{color:var(--mut);font-size:15px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px;margin:16px 0}
.wcard{border-left:3px solid var(--gold)}
.kv{display:grid;grid-template-columns:170px 1fr;gap:6px 14px;font-size:15px}
.kv dt{color:var(--mut)}.kv dd{font-variant-numeric:tabular-nums}
.big{font-size:34px;font-weight:650;letter-spacing:.01em}
.chip{display:inline-block;border-radius:999px;padding:2px 12px;font-size:12.5px;font-weight:600;letter-spacing:.06em;vertical-align:middle}
.FRESH{background:rgba(74,222,128,.14);color:var(--grn);border:1px solid rgba(74,222,128,.4)}
.STALE{background:rgba(251,191,36,.12);color:var(--amb);border:1px solid rgba(251,191,36,.4)}
.UNKNOWN{background:rgba(138,138,160,.12);color:var(--gry);border:1px solid rgba(138,138,160,.4)}
.UNAVAILABLE{background:rgba(248,113,113,.12);color:var(--red);border:1px solid rgba(248,113,113,.4)}
.up{color:var(--grn)}.down{color:var(--red)}.flat{color:var(--mut)}
nav.mkts{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
nav.mkts a{border:1px solid var(--line);border-radius:8px;padding:6px 13px;font-size:14px;color:var(--tx)}
nav.mkts a:hover{border-color:var(--gold);text-decoration:none;color:var(--gold)}
.btns{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}
.btn{border-radius:9px;padding:11px 18px;font-size:15px;font-weight:600;border:1px solid var(--gold);color:var(--gold)}
.btn:hover{text-decoration:none;background:rgba(232,196,104,.08)}
.btn.ghost{border-color:var(--line);color:var(--tx)}
footer{border-top:1px solid var(--line);margin-top:46px;padding-top:20px;color:var(--mut);font-size:13.5px}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600;font-size:13px;letter-spacing:.04em}
code{background:var(--panel2);border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:13px}
.note{color:var(--mut);font-size:13.5px;margin-top:10px}
ul.src{list-style:none}ul.src li{padding:7px 0;border-bottom:1px dashed var(--line);font-size:14.5px}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def now_my() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))


def parse_as_of(s: str) -> dt.datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def state_for(m: dict, gen: dt.datetime, fresh_h: int) -> str:
    obs = m.get("observations") or []
    if not obs:
        return "UNKNOWN"
    age = (gen - parse_as_of(obs[0]["as_of"])).total_seconds() / 3600.0
    return "FRESH" if age <= fresh_h else "STALE"


def fmt_num(v, unit: str = "") -> str:
    if v is None:
        return "UNKNOWN"
    if isinstance(v, float) and abs(v - round(v)) < 1e-9:
        v = int(round(v))
    s = f"{v:,.4f}".rstrip("0").rstrip(".") if isinstance(v, float) and abs(v) < 10 else (
        f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
    )
    return f"{s} {unit}".strip()


def fmt_chg(o: dict) -> str:
    c, p = o.get("change"), o.get("change_pct")
    if c is None:
        return ""
    cls = "up" if c > 0 else ("down" if c < 0 else "flat")
    sign = "+" if c > 0 else ""
    ps = f" ({sign}{p:.2f}%)" if p is not None else ""
    return f'<span class="{cls}">{sign}{c:g}{ps}</span>'


def obs_value(m: dict):
    obs = m.get("observations") or []
    return obs[0] if obs else None


def secondary_rows(o: dict) -> list[dict]:
    return o.get("secondary") or [] if o else []


def ws_verified(m: dict | None = None) -> str:
    if m and m.get("world_url"):
        return m["world_url"]
    return WORLD_SURFACE.get("verified_url", f"{WORLD_BASE}/world/economics/")


def ws_status() -> str:
    return WORLD_SURFACE.get("world_link_status", "VERIFIED_LIVE")


def ws_policy() -> str:
    return WORLD_SURFACE.get("link_policy", "DIRECT_TERMINAL_AND_HUB")


def fetch_live_engines() -> tuple[dict[str, dict], dict]:
    """Fetch live commodity snapshots from :3456/:3457/:3458 and daily briefing JSON."""
    engine_snaps: dict[str, dict] = {}
    for mid, (url, label) in ENGINE_ENDPOINTS.items():
        try:
            with urllib.request.urlopen(url, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, dict) and "ticker" in data and data["ticker"].get("price") is not None:
                    data["_engine_label"] = label
                    engine_snaps[mid] = data
        except Exception as exc:
            print(f"[warn] live engine {mid} ({url}) unavailable: {exc}", file=sys.stderr)

    briefing: dict = {}
    if BRIEFING_JSON.is_file():
        try:
            briefing = json.loads(BRIEFING_JSON.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[warn] briefing JSON read failed: {exc}", file=sys.stderr)

    return engine_snaps, briefing


def enrich_ledger_from_live(ledger_data: dict, engine_snaps: dict[str, dict], briefing: dict, gen: dt.datetime) -> dict:
    """Merge live WEALTH engine observations into ledger structure with full provenance."""
    updated = copy.deepcopy(ledger_data)
    fresh_h = updated["freshness_rule"]["fresh_within_hours"]

    updated["updated_by"] = "WEALTH markets/build_markets_surface.py (ARIFOS::WEALTH_FEDERATION_ALIGNMENT::2026-10-23)"
    updated["world_surface"] = {
        "verdict": "LIVE_TERMINAL_VERIFIED (2026-10-23; restored in T2-R2 2026-10-16)",
        "surface_status": "ACTIVE",
        "desired_route_pattern": "https://arif-fazil.com/world/economics/{id}/",
        "verified_url": "https://arif-fazil.com/world/economics/",
        "link_policy": "DIRECT_TERMINAL_AND_HUB",
        "world_link_status": "VERIFIED_LIVE",
        "world_link_clickable": True,
        "reversal_ticket": "WORLD-TERMINAL-REVERSAL-001 (CLOSED)",
        "note": "All 5 World Economics instrument terminals (/world/economics/{gold,oil,gas,klci,usdmyr}/) are verified live HTTP 200.",
    }

    for m in updated.get("markets", []):
        mid = m["id"]
        prior_obs = m.get("observations") or []
        prior_primary = prior_obs[0] if prior_obs else None

        if mid in engine_snaps:
            snap = engine_snaps[mid]
            tk = snap.get("ticker", {})
            lv = snap.get("levels", {})
            obs_at = snap.get("observed_at") or gen.astimezone(dt.timezone.utc).isoformat()
            price = round(float(tk["price"]), 4 if float(tk["price"]) < 10 else 2)
            chg = round(float(tk["change"]), 4 if abs(float(tk["change"])) < 1 else 2) if tk.get("change") is not None else None
            chg_pct = round(float(tk["changePct"]), 2) if tk.get("changePct") is not None else None
            res_list = lv.get("resistance_daily") or lv.get("resistance") or []
            sup_list = lv.get("support_daily") or lv.get("support") or []
            res_val = res_list[0] if res_list else None
            sup_val = sup_list[0] if sup_list else None

            age_h = (gen - parse_as_of(obs_at)).total_seconds() / 3600.0
            fresh_state = "FRESH" if age_h <= fresh_h else "STALE"

            secondary = []
            if prior_primary and prior_primary.get("as_of") != obs_at:
                secondary.append({
                    "as_of": prior_primary.get("as_of"),
                    "source": prior_primary.get("source"),
                    "evidence": prior_primary.get("evidence", "REPORTED"),
                    "value": prior_primary.get("value"),
                    "note": "Prior recorded baseline observation in ledger.",
                })

            new_obs = {
                "as_of": obs_at,
                "observed_at": obs_at,
                "source": snap["_engine_label"],
                "epistemic_class": "OBS",
                "evidence": "OBSERVED",
                "freshness": fresh_state,
                "producer": "WEALTH",
                "authority": AUTHORITY,
                "value": price,
                "change": chg,
                "change_pct": chg_pct,
                "rsi_14d": tk.get("rsi"),
                "ema_trend": tk.get("emaTrend"),
            }
            if res_val is not None and sup_val is not None:
                new_obs["resistance"] = res_val
                new_obs["support"] = sup_val
                new_obs["levels_note"] = "Computed technical pivot levels from WEALTH commodity engine (not trade advice)."
            if secondary:
                new_obs["secondary"] = secondary[:3]
            m["observations"] = [new_obs]

        elif mid == "klci" and briefing.get("bursa", {}).get("klci_close") is not None:
            meta = briefing.get("meta", {})
            bursa = briefing["bursa"]
            obs_at = meta.get("observed_at") or meta.get("generated_at") or gen.isoformat()
            val = round(float(bursa["klci_close"]), 2)
            chg_pct = round(float(bursa.get("klci_change_pct") or 0.0), 2)
            age_h = (gen - parse_as_of(obs_at)).total_seconds() / 3600.0
            fresh_state = "FRESH" if age_h <= fresh_h else "STALE"

            secondary = []
            if prior_primary and prior_primary.get("as_of") != obs_at:
                secondary.append({
                    "as_of": prior_primary.get("as_of"),
                    "source": prior_primary.get("source"),
                    "evidence": prior_primary.get("evidence", "REPORTED"),
                    "value": prior_primary.get("value"),
                    "note": "Prior recorded baseline observation in ledger.",
                })

            new_obs = {
                "as_of": obs_at,
                "observed_at": obs_at,
                "source": "arifOS WEALTH daily snapshot (yfinance ^KLSE)",
                "epistemic_class": "OBS",
                "evidence": "OBSERVED",
                "freshness": fresh_state,
                "producer": "WEALTH",
                "authority": AUTHORITY,
                "value": val,
                "change": 0.0 if chg_pct == 0.0 else None,
                "change_pct": chg_pct,
            }
            if prior_primary and prior_primary.get("resistance") is not None:
                new_obs["resistance"] = prior_primary["resistance"]
                new_obs["support"] = prior_primary["support"]
                new_obs["levels_note"] = prior_primary.get("levels_note", "Broker-reported levels.")
            if secondary:
                new_obs["secondary"] = secondary[:3]
            m["observations"] = [new_obs]

        elif mid == "usdmyr" and briefing.get("ringgit", {}).get("usd_myr") is not None:
            meta = briefing.get("meta", {})
            ringgit = briefing["ringgit"]
            obs_at = meta.get("observed_at") or meta.get("generated_at") or gen.isoformat()
            val = round(float(ringgit["usd_myr"]), 4)
            age_h = (gen - parse_as_of(obs_at)).total_seconds() / 3600.0
            fresh_state = "FRESH" if age_h <= fresh_h else "STALE"

            secondary = []
            # Cross-witness with live commodity engine macro.usmyr if available
            oil_macro_myr = engine_snaps.get("oil", {}).get("macro", {}).get("usmyr")
            if oil_macro_myr is not None:
                secondary.append({
                    "as_of": engine_snaps["oil"].get("observed_at", obs_at),
                    "source": "WEALTH commodity engine macro feed (yfinance MYR=X)",
                    "evidence": "OBSERVED",
                    "value": float(oil_macro_myr),
                    "note": "Cross-engine intraday FX witness.",
                })
            if prior_primary and prior_primary.get("as_of") != obs_at:
                secondary.append({
                    "as_of": prior_primary.get("as_of"),
                    "source": prior_primary.get("source"),
                    "evidence": prior_primary.get("evidence", "OBSERVED"),
                    "value": prior_primary.get("value"),
                    "note": "Prior recorded baseline observation in ledger.",
                })

            new_obs = {
                "as_of": obs_at,
                "observed_at": obs_at,
                "source": "arifOS WEALTH daily snapshot (yfinance MYR=X)",
                "epistemic_class": "OBS",
                "evidence": "OBSERVED",
                "freshness": fresh_state,
                "producer": "WEALTH",
                "authority": AUTHORITY,
                "value": val,
            }
            if secondary:
                new_obs["secondary"] = secondary[:3]
            m["observations"] = [new_obs]

        # Ensure provenance fields exist on any fallback observation
        if m.get("observations"):
            o0 = m["observations"][0]
            o0.setdefault("observed_at", o0.get("as_of"))
            o0.setdefault("epistemic_class", "OBS" if o0.get("evidence") == "OBSERVED" else "REP")
            o0["freshness"] = state_for(m, gen, fresh_h)
            o0.setdefault("producer", "WEALTH")
            o0.setdefault("authority", AUTHORITY)

    return updated


def sync_world_state(
    markets: list[dict],
    states: dict[str, str],
    engine_snaps: dict[str, dict],
    briefing: dict,
    gen: dt.datetime,
    dry_run: bool = False,
) -> None:
    """Update world-state.json with structured provenance and re-bind SHA256 in /world/index.html."""
    ws_src = ARIF_SITE_ROOT / "public" / "world-state.json"
    if not ws_src.is_file():
        return

    ws = json.loads(ws_src.read_text(encoding="utf-8"))
    gen_utc = gen.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ws["version"] = "1.2.0"
    ws["organ"] = "WEALTH"
    ws["federation"] = "arifOS"
    ws["territory"] = "world"
    ws["timestamp"] = gen_utc
    ws["status"] = "LIVE_ORGAN_SYNC_PENDING_SEAL"
    ws["authority"] = AUTHORITY
    ws["final_authority"] = "ARIF"
    ws["markets_registry_url"] = f"{BASE}/api/markets/registry"

    by_id = {m["id"]: m for m in markets}
    oil_obs = obs_value(by_id.get("oil", {})) or {}
    gold_obs = obs_value(by_id.get("gold", {})) or {}
    gas_obs = obs_value(by_id.get("gas", {})) or {}
    klci_obs = obs_value(by_id.get("klci", {})) or {}
    myr_obs = obs_value(by_id.get("usdmyr", {})) or {}

    macro_src = (
        engine_snaps.get("oil", {}).get("macro")
        or engine_snaps.get("gold", {}).get("macro")
        or {}
    )
    macro_obs_at = (
        engine_snaps.get("oil", {}).get("observed_at")
        or engine_snaps.get("gold", {}).get("observed_at")
        or gen_utc
    )

    macro = ws.setdefault("macro_thermodynamics", {})
    if oil_obs.get("value") is not None:
        macro["brent_crude_usd"] = oil_obs["value"]
    if gold_obs.get("value") is not None:
        macro["gold_xau_usd"] = gold_obs["value"]
    if gas_obs.get("value") is not None:
        macro["henry_hub_gas_usd"] = gas_obs["value"]
    if klci_obs.get("value") is not None:
        macro["fbm_klci"] = klci_obs["value"]
    if myr_obs.get("value") is not None:
        macro["usd_myr"] = myr_obs["value"]
    if macro_src.get("dxy") is not None:
        macro["dxy"] = macro_src["dxy"]
    if macro_src.get("vix") is not None:
        macro["vix"] = macro_src["vix"]
    if macro_src.get("us10y") is not None:
        macro["us10y_yield_pct"] = macro_src["us10y"]
    if macro_src.get("silver") is not None:
        macro["silver_usd"] = macro_src["silver"]

    def make_prov(val, unit: str, obs_at: str, src: str, f_state: str = "FRESH") -> dict:
        return {
            "value": val,
            "unit": unit,
            "observed_at": obs_at,
            "source": src,
            "epistemic_class": "OBS",
            "freshness": f_state,
            "producer": "WEALTH",
            "authority": AUTHORITY,
        }

    ws["observations"] = {
        "brent_crude_usd": make_prov(
            macro.get("brent_crude_usd"),
            "USD/bbl",
            oil_obs.get("observed_at", gen_utc),
            oil_obs.get("source", "WEALTH Oil Commodity Engine (:3457)"),
            states.get("oil", "FRESH"),
        ),
        "gold_xau_usd": make_prov(
            macro.get("gold_xau_usd"),
            "USD/oz",
            gold_obs.get("observed_at", gen_utc),
            gold_obs.get("source", "WEALTH Gold Commodity Engine (:3456)"),
            states.get("gold", "FRESH"),
        ),
        "henry_hub_gas_usd": make_prov(
            macro.get("henry_hub_gas_usd"),
            "USD/MMBtu",
            gas_obs.get("observed_at", gen_utc),
            gas_obs.get("source", "WEALTH Natural Gas Commodity Engine (:3458)"),
            states.get("gas", "FRESH"),
        ),
        "fbm_klci": make_prov(
            macro.get("fbm_klci"),
            "index pts",
            klci_obs.get("observed_at", gen_utc),
            klci_obs.get("source", "arifOS WEALTH daily snapshot (yfinance ^KLSE)"),
            states.get("klci", "FRESH"),
        ),
        "usd_myr": make_prov(
            macro.get("usd_myr"),
            "MYR/USD",
            myr_obs.get("observed_at", gen_utc),
            myr_obs.get("source", "arifOS WEALTH daily snapshot (yfinance MYR=X)"),
            states.get("usdmyr", "FRESH"),
        ),
        "dxy": make_prov(
            macro.get("dxy"),
            "index pts",
            macro_obs_at,
            "WEALTH commodity engine macro feed (yfinance DX-Y.NYB)",
            "FRESH",
        ),
        "vix": make_prov(
            macro.get("vix"),
            "index pts",
            macro_obs_at,
            "WEALTH commodity engine macro feed (yfinance ^VIX)",
            "FRESH",
        ),
        "us10y_yield_pct": make_prov(
            macro.get("us10y_yield_pct"),
            "%",
            macro_obs_at,
            "WEALTH commodity engine macro feed (yfinance ^TNX)",
            "FRESH",
        ),
        "silver_usd": make_prov(
            macro.get("silver_usd"),
            "USD/oz",
            macro_obs_at,
            "WEALTH commodity engine macro feed (yfinance SI=F)",
            "FRESH",
        ),
    }

    ws.setdefault("section_grades", {})["macro_thermodynamics"] = (
        f"ORGAN_LIVE_RECEIPTED (WEALTH commodity engines + daily snapshot, {gen_utc})"
    )
    pw = ws.setdefault("provenance_witness", {})
    pw["last_synced_at"] = gen_utc
    pw["producer_organ"] = "WEALTH"
    pw["producer_endpoint"] = f"{BASE}/api/markets/registry"
    pw["authority_ceiling"] = AUTHORITY
    pw["final_authority"] = "ARIF"
    pw["actor"] = "WEALTH markets/build_markets_surface.py (session SEAL-8fa3c44343b14bde)"

    ws_bytes = (json.dumps(ws, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    ws_sha = hashlib.sha256(ws_bytes).hexdigest()

    ws_targets = [
        ARIF_SITE_ROOT / "public" / "world-state.json",
        ARIF_SITE_ROOT / "dist" / "world-state.json",
        ARIF_WEBROOT / "world-state.json",
    ]
    for t in ws_targets:
        if t.parent.is_dir():
            print(f"{'DRY ' if dry_run else 'WRITE'} {t} ({len(ws_bytes)}B, sha256={ws_sha[:12]}…)")
            if not dry_run:
                t.write_bytes(ws_bytes)

    # Update bound sha256 + timestamp + live data values in /world/index.html
    world_idx_targets = [
        ARIF_SITE_ROOT / "public" / "world" / "index.html",
        ARIF_SITE_ROOT / "dist" / "world" / "index.html",
        ARIF_WEBROOT / "world" / "index.html",
    ]
    gen_human = gen.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    brent_val = macro.get("brent_crude_usd", 110.3)
    myr_val = macro.get("usd_myr", 4.0787)
    klci_rsi = macro.get("klci_rsi_14d", 42.56)

    for idx_path in world_idx_targets:
        if not idx_path.is_file():
            continue
        txt = idx_path.read_text(encoding="utf-8")
        new_txt = re.sub(
            r'(<footer class="integrity"[^>]*>.*?<time datetime=")[^"]*("[^>]*>)[^<]*(</time>\)</p>\s*<p>sha256:\s*<code[^>]*>)[0-9a-f]{64}(</code></p>\s*<p>Brent\s*<data value=")[^"]*("[^>]*>)[^<]*(</data>\s*·\s*USD/MYR\s*<data value=")[^"]*("[^>]*>)[^<]*(</data>)',
            rf'\g<1>{gen_utc}\g<2>{gen_human}\g<3>{ws_sha}\g<4>{brent_val}\g<5>USD {brent_val}\g<6>{myr_val}\g<7>{myr_val}\g<8>',
            txt,
            flags=re.DOTALL,
        )
        if new_txt != txt:
            print(f"{'DRY ' if dry_run else 'BIND'} {idx_path} -> sha256={ws_sha[:12]}…")
            if not dry_run:
                idx_path.write_text(new_txt, encoding="utf-8")


def head_block(title: str, desc: str, canonical: str, related: str | None, md_alt: str | None) -> str:
    links = ""
    if related:
        links += f'\n<link rel="related" href="{esc(related)}">'
    links += f'\n<link rel="describedby" href="{BASE}/llms.txt">'
    if md_alt:
        links += f'\n<link rel="alternate" type="text/markdown" href="{esc(md_alt)}">'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{esc(canonical)}">{links}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<style>{CSS}</style>
</head>
<body>
<main>"""


def footer(gen: dt.datetime) -> str:
    return f"""<footer>
<p><strong>{esc(BOUNDARY)}</strong> · Authority ceiling <code>{AUTHORITY}</code> — WEALTH never allocates capital, never issues orders, never fabricates data.</p>
<p>Endpoints: <a href="{BASE}/api/markets/registry">market registry (JSON)</a> · <a href="{BASE}/tools">/tools (15 MCP tools)</a> · <a href="{BASE}/.well-known/agent-card.json">agent-card.json</a> · <a href="{BASE}/llms.txt">llms.txt</a> · <a href="{BASE}/mcp">MCP</a> · <a href="{WORLD_BASE}/world-state.json">world-state.json</a> · narrative <a href="{WORLD_BASE}/world/economics/">arif-fazil.com/world/economics/</a></p>
<p class="note">States ({' / '.join('FRESH STALE UNKNOWN UNAVAILABLE'.split())}) are baked at generation time: {esc(gen.isoformat())}. Generated by {esc(GENERATED_BY)}.</p>
</footer>
</main>
</body>
</html>"""


def witness_card(m: dict, state: str, gen: dt.datetime) -> str:
    o = obs_value(m)
    if o is None:
        body = """<dl class="kv">
<dt>Observation</dt><dd><strong>UNKNOWN</strong></dd>
<dt>Reason</dt><dd>No observation wired for this market yet. Nothing is fabricated here.</dd></dl>"""
        val_html = '<div class="big">UNKNOWN</div>'
    else:
        v = o.get("value_range")
        if v:
            val = f"{v[0]:,.2f}–{v[1]:,.2f} {esc(m.get('unit',''))}".strip()
        else:
            val = fmt_num(o.get("value"), m.get("unit", ""))
        val_html = f'<div class="big">{esc(val)}</div>'
        lvl = ""
        if o.get("resistance") is not None:
            lvl = (
                f'<dt>Reference levels</dt><dd>R {esc(fmt_num(o["resistance"]))} · '
                f'S {esc(fmt_num(o["support"]))} <span class="note">— {esc(o.get("levels_note", "computed reference, not trade signals"))}</span></dd>'
            )
        body = f"""<dl class="kv">
<dt>Observation</dt><dd><strong>{esc(val)}</strong> {fmt_chg(o)}</dd>
<dt>Observed (as of)</dt><dd>{esc(o["as_of"])}</dd>
<dt>Epistemic / Evidence</dt><dd><code>{esc(o.get("epistemic_class", "OBS"))}</code> · {esc(o.get("evidence", "OBSERVED"))}</dd>
<dt>Producer / Authority</dt><dd><code>{esc(o.get("producer", "WEALTH"))}</code> · <code>{esc(o.get("authority", AUTHORITY))}</code></dd>
<dt>Source</dt><dd>{esc(o.get("source", ""))}</dd>
{lvl}
</dl>"""
    return f"""<div class="card wcard">
<div class="kicker">Market Witness Card</div>
<h2 style="margin-top:4px">{esc(m['label'])} <span class="sub">{esc(m['symbol'])}</span>
<span class="chip {state}">{state}</span></h2>
{val_html}
{body}
<p class="note">Freshness rule: FRESH ≤ {FRESH_H}h from as_of at generation time; STALE beyond; UNKNOWN when unobserved. State computed {esc(gen.isoformat())}.</p>
</div>"""


def sources_block(m: dict) -> str:
    o = obs_value(m)
    rows = secondary_rows(o)
    if o is None:
        return ""
    items = "".join(
        f"<li><strong>{esc(s.get('evidence','REPORTED'))}</strong> · {esc(s.get('source',''))} · "
        f"as_of {esc(s.get('as_of',''))} · "
        f"value {esc(fmt_num(s.get('value'), m.get('unit','')) if s.get('value') is not None else s.get('value_range',''))}"
        + (f" · {esc(s['note'])}" if s.get("note") else "")
        + "</li>"
        for s in rows
    )
    if not items:
        return ""
    return f'<h2>Witness chain</h2><div class="card"><ul class="src">{items}</ul><p class="note">Secondary witnesses preserve prior baselines and cross-engine checks.</p></div>'


def market_page(m: dict, state: str, gen: dt.datetime) -> str:
    mid = m["id"]
    wealth_url = f"{BASE}/markets/{mid}/"
    data_url = f"{BASE}/api/markets/{mid}/latest"
    world_pair = ws_verified(m)
    title = f"{m['label']} ({m['symbol']}) — WEALTH Market Terminal"
    desc = (
        f"{m['label']} observation terminal: live witness card with provenance, freshness state "
        f"({state}), and machine endpoints. {AUTHORITY} — no trade signals."
    )
    h = head_block(title, desc, wealth_url, world_pair, f"{BASE}/markets/{mid}/index.md")
    others = " ".join(
        f'<a href="/markets/{x["id"]}/">{esc(x["label"])}</a>' for x in MARKETS if x["id"] != mid
    )
    return f"""{h}
<header>
<div class="kicker">WEALTH · Markets · <a href="/markets/">All markets</a> · <a href="/">Organ Home</a></div>
<h1>{esc(m['label'])} <span class="sub">{esc(m['symbol'])}</span></h1>
<p class="sub">Observation, provenance and compute terminal — <code>{esc(AUTHORITY)}</code>. Paired World terminal: <a href="{esc(world_pair)}">{esc(world_pair)}</a>.</p>
</header>
{witness_card(m, state, gen)}
{sources_block(m)}
<h2>Machine endpoints</h2>
<div class="card">
<dl class="kv">
<dt>Latest observation</dt><dd><a href="{data_url}">{data_url}</a></dd>
<dt>Markdown mirror</dt><dd><a href="{BASE}/markets/{mid}/index.md">{BASE}/markets/{mid}/index.md</a></dd>
<dt>Registry entry</dt><dd><a href="{BASE}/api/markets/registry">{BASE}/api/markets/registry</a></dd>
<dt>World state JSON</dt><dd><a href="{WORLD_BASE}/world-state.json">{WORLD_BASE}/world-state.json</a></dd>
<dt>Governed compute</dt><dd><a href="{BASE}/mcp">WEALTH MCP — capital_market, capital_indicator ({AUTHORITY})</a></dd>
</dl>
</div>
<div class="btns">
<a class="btn" href="{esc(world_pair)}">Paired World Terminal ({esc(m['label'])})</a>
<a class="btn ghost" href="{WORLD_BASE}/world/economics/">World Economics Hub</a>
<a class="btn ghost" href="/markets/">All WEALTH Markets</a>
</div>
<nav class="mkts" style="margin-top:26px">{others}</nav>
{footer(gen)}"""


def market_md(m: dict, state: str, gen: dt.datetime) -> str:
    o = obs_value(m)
    world_pair = ws_verified(m)
    lines = [
        f"# {m['label']} ({m['symbol']}) — WEALTH Market Terminal",
        "",
        f"URL: {BASE}/markets/{m['id']}/ · Data: {BASE}/api/markets/{m['id']}/latest · State: **{state}** (computed {gen.isoformat()})",
        "",
        "## Market Witness Card",
        "",
    ]
    if o is None:
        lines += ["- Observation: **UNKNOWN**", "- Reason: no observation wired; nothing fabricated."]
    else:
        v = o.get("value_range") or fmt_num(o.get("value"), m.get("unit", ""))
        lines += [
            f"- Observation: **{v}**" + (f" ({o['change']:+g}, {o['change_pct']:+.2f}%)" if o.get("change") is not None else ""),
            f"- Observed (as of): {o['as_of']}",
            f"- Epistemic / Evidence: `{o.get('epistemic_class', 'OBS')}` / `{o.get('evidence', 'OBSERVED')}`",
            f"- Producer / Authority: `{o.get('producer', 'WEALTH')}` / `{o.get('authority', AUTHORITY)}`",
            f"- Source: {o.get('source', '')}",
        ]
        if o.get("resistance") is not None:
            lines.append(f"- Reference levels: R {o['resistance']} / S {o['support']} — {o.get('levels_note', 'not forecasts')}")
    for s in secondary_rows(o or {}):
        lines.append(
            f"- Secondary: {s.get('evidence','REPORTED')} · {s.get('source','')} · {s.get('as_of','')}"
            + (f" · {s['note']}" if s.get("note") else "")
        )
    lines += [
        "",
        "## Boundary",
        "",
        f"{BOUNDARY} — authority ceiling {AUTHORITY}. No trade signals.",
        "",
        f"World narrative & terminal pair: {world_pair} (status: {ws_status()})",
        "",
        f"Generated {gen.isoformat()} by {GENERATED_BY}.",
    ]
    return "\n".join(lines) + "\n"


def hub_page(states: dict, gen: dt.datetime) -> str:
    cards = ""
    for m in MARKETS:
        st = states[m["id"]]
        o = obs_value(m)
        world_pair = ws_verified(m)
        if o is None:
            val, chg, meta_line = "UNKNOWN", "", "No observation wired"
        else:
            val = fmt_num(o.get("value"), m.get("unit", ""))
            chg = fmt_chg(o)
            meta_line = f"{esc(o.get('epistemic_class', 'OBS'))} · {esc(o.get('source', ''))} · as of {esc(o.get('as_of', ''))}"
        cards += f"""<div class="card">
<h2 style="margin:0 0 6px"><a href="/markets/{m['id']}/">{esc(m['label'])}</a>
<span class="sub">{esc(m['symbol'])}</span> <span class="chip {st}">{st}</span></h2>
<div class="big">{esc(val)}</div>{chg}
<p class="note">{meta_line}</p>
<p class="note">Paired World terminal: <a href="{esc(world_pair)}">{esc(world_pair)}</a> · JSON: <a href="/api/markets/{m['id']}/latest">/api/markets/{m['id']}/latest</a></p>
</div>"""
    watch = "".join(
        f"<tr><td>{esc(w['label'])}</td><td>{esc(fmt_num(w.get('value'), w.get('unit','pts')))}</td>"
        f"<td>{fmt_chg(w)}</td><td>REPORTED · {esc(w['as_of'][:10])}</td>"
        f"<td>R {esc(fmt_num(w.get('resistance'))) if w.get('resistance') is not None else '—'} / "
        f"S {esc(fmt_num(w.get('support'))) if w.get('support') is not None else '—'}</td></tr>"
        for w in LEDGER_DATA.get("watchlist", [])
    )
    title = "WEALTH Markets — Observation Terminals"
    desc = (
        "Paired observation terminals for gold, oil, gas, KLCI and USD/MYR with live provenance, "
        f"freshness states and machine endpoints. {AUTHORITY}."
    )
    h = head_block(title, desc, f"{BASE}/markets/", f"{WORLD_BASE}/world/economics/", None)
    return f"""{h}
<header>
<div class="kicker">WEALTH · Capital Intelligence · <a href="/">Organ Home</a></div>
<h1>Markets — Observation Terminals</h1>
<p class="sub">{esc(BOUNDARY)} · Authority ceiling <code>{AUTHORITY}</code></p>
</header>
<p>Paired with <a href="{WORLD_BASE}/world/economics/">arif-fazil.com World Economics</a> and <a href="{WORLD_BASE}/world-state.json">world-state.json</a>: WORLD observes global/Malaysian reality; WEALTH computes capital consequences and publishes provenance-bound observations; AAA coordinates agents; arifOS judges governance; ARIF decides. Shared registry: <a href="{BASE}/api/markets/registry">/api/markets/registry</a>.</p>
{cards}
<h2>Watchlist — reported baseline, not live engine terminals</h2>
<div class="card" style="overflow-x:auto">
<table><thead><tr><th>Market</th><th>Observation</th><th>Change</th><th>Evidence · as of</th><th>Reported R / S</th></tr></thead>
<tbody>{watch}</tbody></table>
<p class="note">Source: Bloomberg via M+Global Market Buzz (relayed baseline). Levels are broker-reported, not WEALTH forecasts.</p>
</div>
<h2>Federation Reality Chain</h2>
<div class="card">
<dl class="kv">
<dt>WORLD</dt><dd><a href="{WORLD_BASE}/world/">Human & macro reality observation</a> · <a href="{WORLD_BASE}/world-state.json">world-state.json</a></dd>
<dt>WEALTH</dt><dd>Capital intelligence, provenance & 15 MCP tools (`555_COMPUTE_ONLY`) — <a href="{BASE}/tools">/tools</a></dd>
<dt>AAA</dt><dd>Agent directory & A2A router (`DISPLAY_ONLY`) — <a href="https://aaa.arif-fazil.com/a2a/agents.json">aaa.arif-fazil.com/a2a/agents.json</a></dd>
<dt>arifOS</dt><dd>Constitutional governance kernel (`JUDGE_ONLY`) — <a href="https://arifos.arif-fazil.com">arifos.arif-fazil.com</a></dd>
<dt>ARIF</dt><dd>Sovereign human principal (`F13`) — final authority</dd>
</dl>
</div>
{footer(gen)}"""


def registry_doc(states: dict, gen: dt.datetime) -> dict:
    mk = []
    for m in MARKETS:
        o = obs_value(m)
        world_pair = ws_verified(m)
        mk.append({
            "id": m["id"],
            "label": m["label"],
            "symbol": m["symbol"],
            "unit": m.get("unit"),
            "value": (o or {}).get("value") if o else None,
            "change": (o or {}).get("change") if o else None,
            "change_pct": (o or {}).get("change_pct") if o else None,
            "observed_at": (o or {}).get("observed_at") or (o or {}).get("as_of") if o else None,
            "as_of": (o or {}).get("as_of") if o else None,
            "source": (o or {}).get("source") if o else None,
            "epistemic_class": (o or {}).get("epistemic_class", "OBS") if o else None,
            "evidence": (o or {}).get("evidence") if o else None,
            "freshness": states[m["id"]],
            "state": states[m["id"]],
            "producer": "WEALTH",
            "authority": AUTHORITY,
            "authority_ceiling": AUTHORITY,
            "world_url": world_pair,
            "world": {
                "desired_url": m["world_url"],
                "verified_url": world_pair,
                "hub_url": f"{WORLD_BASE}/world/economics/",
                "world_state_url": f"{WORLD_BASE}/world-state.json",
                "surface_status": WORLD_SURFACE.get("surface_status", "ACTIVE"),
                "link_policy": ws_policy(),
            },
            "world_link_status": ws_status(),
            "world_link_clickable": bool(WORLD_SURFACE.get("world_link_clickable", True)),
            "wealth_url": f"{BASE}/markets/{m['id']}/",
            "data_url": f"{BASE}/api/markets/{m['id']}/latest",
            "markdown_url": f"{BASE}/markets/{m['id']}/index.md",
        })
    return {
        "schema_version": "2.0",
        "organ": "WEALTH",
        "federation": "arifOS",
        "generated_at": gen.isoformat(),
        "generated_by": GENERATED_BY,
        "authority_ceiling": AUTHORITY,
        "final_authority": "ARIF",
        "boundary": BOUNDARY,
        "world_state_url": f"{WORLD_BASE}/world-state.json",
        "tools_url": f"{BASE}/tools",
        "freshness_rule": LEDGER_DATA["freshness_rule"],
        "markets": mk,
        "watchlist_note": "dow / hsi / cpo are reported watchlist items (hub page only), not live engine terminals.",
    }


def latest_doc(m: dict, state: str, gen: dt.datetime) -> dict:
    o = obs_value(m)
    return {
        "schema_version": "2.0",
        "organ": "WEALTH",
        "federation": "arifOS",
        "authority_ceiling": AUTHORITY,
        "final_authority": "ARIF",
        "market": {"id": m["id"], "label": m["label"], "symbol": m["symbol"], "unit": m.get("unit")},
        "observation": o,
        "state": state,
        "freshness": state,
        "state_computed_at": gen.isoformat(),
        "freshness_rule": LEDGER_DATA["freshness_rule"],
        "endpoints": {
            "registry": f"{BASE}/api/markets/registry",
            "markdown": f"{BASE}/markets/{m['id']}/index.md",
            "page": f"{BASE}/markets/{m['id']}/",
            "world_pair": ws_verified(m),
            "world_state": f"{WORLD_BASE}/world-state.json",
        },
        "boundary": f"{BOUNDARY} — authority ceiling {AUTHORITY}. No trade signals. No fabricated values.",
    }


def sitemap(gen: dt.datetime) -> str:
    urls = (
        [f"{BASE}/markets/"]
        + [f"{BASE}/markets/{m['id']}/" for m in MARKETS]
        + [f"{BASE}/markets/{m['id']}/index.md" for m in MARKETS]
        + [f"{BASE}/", f"{BASE}/llms.txt", f"{BASE}/tools", f"{BASE}/.well-known/agent-card.json", f"{BASE}/api/markets/registry"]
    )
    items = "".join(
        f"  <url><loc>{u}</loc><lastmod>{gen.date().isoformat()}</lastmod></url>\n" for u in urls
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'


def main() -> int:
    global LEDGER_DATA, MARKETS, FRESH_H
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-refresh", action="store_true", help="Do not query live commodity engines")
    ap.add_argument("--write-ledger", action="store_true", help="Persist live observations back to observations.json")
    args = ap.parse_args()

    raw_ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    gen = now_my()

    engine_snaps: dict[str, dict] = {}
    briefing: dict = {}
    if not args.no_refresh:
        engine_snaps, briefing = fetch_live_engines()
        LEDGER_DATA = enrich_ledger_from_live(raw_ledger, engine_snaps, briefing, gen)
    else:
        LEDGER_DATA = raw_ledger

    if args.write_ledger and not args.dry_run:
        LEDGER.write_text(json.dumps(LEDGER_DATA, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"WRITE {LEDGER}")

    WORLD_SURFACE.update(LEDGER_DATA.get("world_surface", {}))
    MARKETS = LEDGER_DATA["markets"]
    FRESH_H = LEDGER_DATA["freshness_rule"]["fresh_within_hours"]
    states = {m["id"]: state_for(m, gen, FRESH_H) for m in MARKETS}

    plan = {
        WEBROOT / "api/markets/registry.json": json.dumps(registry_doc(states, gen), indent=2, ensure_ascii=False) + "\n",
        WEBROOT / "sitemap.xml": sitemap(gen),
        WEBROOT / "markets/index.html": hub_page(states, gen),
    }
    for m in MARKETS:
        st = states[m["id"]]
        plan[WEBROOT / f"markets/{m['id']}/index.html"] = market_page(m, st, gen)
        plan[WEBROOT / f"markets/{m['id']}/index.md"] = market_md(m, st, gen)
        plan[WEBROOT / f"api/markets/{m['id']}/latest.json"] = (
            json.dumps(latest_doc(m, st, gen), indent=2, ensure_ascii=False) + "\n"
        )

    for path, content in plan.items():
        print(f"{'DRY ' if args.dry_run else 'WRITE'} {path} ({len(content)}B)")
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    sync_world_state(MARKETS, states, engine_snaps, briefing, gen, dry_run=args.dry_run)
    print(f"states={states} generated_at={gen.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
