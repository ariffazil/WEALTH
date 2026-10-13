#!/usr/bin/env python3
"""Build the WEALTH public markets surface from the observation ledger.

ARIFOS::WORLD_WEALTH_LINKAGE::v1.0 — WEALTH side.
SOURCE: /root/WEALTH/markets/observations.json  (this repo — SOT)
OUTPUT: /var/www/html/wealth/
    api/markets/registry.json
    api/markets/<id>/latest.json
    markets/index.html, markets/<id>/index.html, markets/<id>/index.md
    sitemap.xml

Honesty rules (structural, same family as the 2026-10-12 public-claims contract):
  - No observation  -> value null, state UNKNOWN. Nothing fabricated.
  - state is computed at generation time and baked into every artifact.
  - Every value carries source + as_of + evidence class.
  - Broker-reported levels are labeled as reported, never as WEALTH forecasts.
Idempotent: rerunning re-bakes states (e.g. daily cron flips FRESH -> STALE).

Usage: python3 build_markets_surface.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "observations.json"
WEBROOT = Path("/var/www/html/wealth")
BASE = "https://wealth.arif-fazil.com"
WORLD_BASE = "https://arif-fazil.com"
GENERATED_BY = "FI-003 (Qwen Code) — build_markets_surface.py"
BOUNDARY = "World explains. WEALTH computes. arifOS judges. ARIF decides."
AUTHORITY = "COMPUTE_ONLY"
WORLD_LINK_STATUS = (
    "world_terminal_lane: SEALED (.bak-reseal) — SPA route serves the shell; "
    "World-side linkage pending F13 reversal ceremony (receipt 2026-10-14)"
)

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
    s = f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
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
<p>Endpoints: <a href="{BASE}/api/markets/registry">market registry (JSON)</a> · <a href="{BASE}/llms.txt">llms.txt</a> · <a href="{BASE}/mcp">MCP</a> · <a href="{BASE}/sitemap.xml">sitemap</a> · narrative context <a href="{WORLD_BASE}/world/economics/">arif-fazil.com/world/economics/</a></p>
<p class="note">States ({' / '.join('FRESH STALE UNKNOWN UNAVAILABLE'.split())}) are baked at generation time: {esc(gen.isoformat())}. No fabricated fallback values — an unobserved market publishes UNKNOWN. Generated by {esc(GENERATED_BY)}.</p>
</footer>
</main>
</body>
</html>"""


def witness_card(m: dict, state: str, gen: dt.datetime) -> str:
    o = obs_value(m)
    if o is None:
        body = f"""<dl class="kv">
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
            lvl = (f'<dt>Reported levels</dt><dd>R {esc(fmt_num(o["resistance"]))} · '
                   f'S {esc(fmt_num(o["support"]))} <span class="note">— broker-reported, not forecasts</span></dd>')
        body = f"""<dl class="kv">
<dt>Observation</dt><dd><strong>{esc(val)}</strong> {fmt_chg(o)}</dd>
<dt>Observed (as of)</dt><dd>{esc(o["as_of"])}{' (date precision)' if o.get('as_of_precision')=='date' else ''}</dd>
<dt>Evidence status</dt><dd>{esc(o.get("evidence","UNKNOWN"))}</dd>
<dt>Source</dt><dd>{esc(o.get("source",""))}</dd>
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
    return f'<h2>Witness chain</h2><div class="card"><ul class="src">{items}</ul><p class="note">Secondary witnesses are relayed reads — labeled SINGLE_SOURCE where no independent second source exists.</p></div>'


def market_page(m: dict, state: str, gen: dt.datetime) -> str:
    mid = m["id"]
    wealth_url = f"{BASE}/markets/{mid}/"
    data_url = f"{BASE}/api/markets/{mid}/latest"
    title = f"{m['label']} ({m['symbol']}) — WEALTH Market Terminal"
    desc = (f"{m['label']} observation terminal: live witness card with provenance, freshness state "
            f"({state}), and machine endpoints. COMPUTE_ONLY — no trade signals.")
    h = head_block(title, desc, wealth_url, m["world_url"], f"{BASE}/markets/{mid}/index.md")
    nav = ' <a href="https://arif-fazil.com">arif-fazil.com</a>'.join([""])
    others = " ".join(
        f'<a href="/markets/{x["id"]}/">{esc(x["label"])}</a>' for x in MARKETS if x["id"] != mid
    )
    return f"""{h}
<header>
<div class="kicker">WEALTH · Markets · <a href="/markets/">All markets</a></div>
<h1>{esc(m['label'])} <span class="sub">{esc(m['symbol'])}</span></h1>
<p class="sub">Observation, provenance and compute terminal — {esc(AUTHORITY)}. Narrative lives on <a href="{WORLD_BASE}/world/economics/{mid}/">World Economics</a>.</p>
</header>
{witness_card(m, state, gen)}
{sources_block(m)}
<h2>Machine endpoints</h2>
<div class="card">
<dl class="kv">
<dt>Latest observation</dt><dd><a href="{data_url}">{data_url}</a></dd>
<dt>Markdown mirror</dt><dd><a href="{BASE}/markets/{mid}/index.md">{BASE}/markets/{mid}/index.md</a></dd>
<dt>Registry entry</dt><dd><a href="{BASE}/api/markets/registry">{BASE}/api/markets/registry</a></dd>
<dt>Governed compute</dt><dd><a href="{BASE}/mcp">WEALTH MCP — capital_market, capital_indicator (COMPUTE_ONLY)</a></dd>
</dl>
</div>
<div class="btns">
<a class="btn ghost" href="{WORLD_BASE}/world/economics/{mid}/">Economic context and public analysis — World</a>
<a class="btn ghost" href="/markets/">All WEALTH markets</a>
</div>
<p class="note">{esc(WORLD_LINK_STATUS)}</p>
<nav class="mkts" style="margin-top:26px">{others}</nav>
{footer(gen)}"""


def market_md(m: dict, state: str, gen: dt.datetime) -> str:
    o = obs_value(m)
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
            f"- Observed (as of): {o['as_of']}" + (" (date precision)" if o.get("as_of_precision") == "date" else ""),
            f"- Evidence status: {o.get('evidence','UNKNOWN')}",
            f"- Source: {o.get('source','')}",
        ]
        if o.get("resistance") is not None:
            lines.append(f"- Reported levels: R {o['resistance']} / S {o['support']} — broker-reported, not forecasts")
    for s in secondary_rows(o or {}):
        lines.append(f"- Secondary: {s.get('evidence','REPORTED')} · {s.get('source','')} · {s.get('as_of','')}"
                     + (f" · {s['note']}" if s.get("note") else ""))
    lines += [
        "",
        "## Boundary",
        "",
        f"{BOUNDARY} — authority ceiling {AUTHORITY}. No trade signals.",
        "",
        f"World narrative pair: {m['world_url']} ({WORLD_LINK_STATUS})",
        "",
        f"Generated {gen.isoformat()} by {GENERATED_BY}.",
    ]
    return "\n".join(lines) + "\n"


def hub_page(states: dict, gen: dt.datetime) -> str:
    cards = ""
    for m in MARKETS:
        st = states[m["id"]]
        o = obs_value(m)
        if o is None:
            val, chg = "UNKNOWN", ""
        else:
            val = fmt_num(o.get("value"), m.get("unit", ""))
            chg = fmt_chg(o)
        cards += f"""<div class="card">
<h2 style="margin:0 0 6px"><a href="/markets/{m['id']}/">{esc(m['label'])}</a>
<span class="sub">{esc(m['symbol'])}</span> <span class="chip {st}">{st}</span></h2>
<div class="big">{esc(val)}</div>{chg}
<p class="note">World pair: <a href="{esc(m['world_url'])}">{esc(m['world_url'].replace('https://',''))}</a></p>
</div>"""
    watch = "".join(
        f"<tr><td>{esc(w['label'])}</td><td>{esc(fmt_num(w.get('value'), w.get('unit','MYR')))}</td>"
        f"<td>{fmt_chg(w)}</td><td>REPORTED · {esc(w['as_of'][:10])}</td>"
        f"<td>R {esc(fmt_num(w.get('resistance'))) if w.get('resistance') is not None else '—'} / "
        f"S {esc(fmt_num(w.get('support'))) if w.get('support') is not None else '—'}</td></tr>"
        for w in LEDGER_DATA.get("watchlist", [])
    )
    title = "WEALTH Markets — Observation Terminals"
    desc = ("Paired observation terminals for gold, oil, gas, KLCI and USD/MYR with provenance, "
            "freshness states and machine endpoints. COMPUTE_ONLY.")
    h = head_block(title, desc, f"{BASE}/markets/", f"{WORLD_BASE}/world/economics/", None)
    return f"""{h}
<header>
<div class="kicker">WEALTH · Capital Intelligence · <a href="/">Home</a></div>
<h1>Markets — Observation Terminals</h1>
<p class="sub">{esc(BOUNDARY)} · Authority ceiling <code>{AUTHORITY}</code></p>
</header>
<p>Paired with <a href="{WORLD_BASE}/world/economics/">arif-fazil.com World Economics</a>: World carries human narrative and context; this surface carries observations, provenance, computation and agent interfaces. Shared contract: <a href="{BASE}/api/markets/registry">/api/markets/registry</a>.</p>
<p class="note">{esc(WORLD_LINK_STATUS)}</p>
{cards}
<h2>Watchlist — reported, not paired terminals</h2>
<div class="card" style="overflow-x:auto">
<table><thead><tr><th>Market</th><th>Observation</th><th>Change</th><th>Evidence · as of</th><th>Reported R / S</th></tr></thead>
<tbody>{watch}</tbody></table>
<p class="note">Source: Bloomberg via M+Global Market Buzz (relayed 2026-10-14). Levels are broker-reported, not WEALTH forecasts. Not trade signals.</p>
</div>
<h2>Relationship</h2>
<div class="card">
<dl class="kv">
<dt>World Economics</dt><dd><a href="{WORLD_BASE}/world/economics/">Human narrative, Malaysia & geopolitical context</a> (terminal lane sealed — see note above)</dd>
<dt>WEALTH</dt><dd>Observations, provenance, computation, scenarios — this surface</dd>
<dt>arifOS</dt><dd>Governance judgment — <a href="https://arifos.arif-fazil.com">arifos.arif-fazil.com</a></dd>
<dt>ARIF</dt><dd>Final authority</dd>
</dl>
</div>
{footer(gen)}"""


def registry_doc(states: dict, gen: dt.datetime) -> dict:
    mk = []
    for m in MARKETS:
        o = obs_value(m)
        mk.append({
            "id": m["id"], "label": m["label"], "symbol": m["symbol"], "unit": m.get("unit"),
            "world_url": m["world_url"],
            "wealth_url": f"{BASE}/markets/{m['id']}/",
            "data_url": f"{BASE}/api/markets/{m['id']}/latest",
            "markdown_url": f"{BASE}/markets/{m['id']}/index.md",
            "authority_ceiling": AUTHORITY,
            "state": states[m["id"]],
            "evidence": (o or {}).get("evidence") if o else None,
            "as_of": (o or {}).get("as_of") if o else None,
            "world_link_status": WORLD_LINK_STATUS,
        })
    return {
        "schema_version": "1.0",
        "generated_at": gen.isoformat(),
        "generated_by": GENERATED_BY,
        "authority_ceiling": AUTHORITY,
        "boundary": BOUNDARY,
        "freshness_rule": LEDGER_DATA["freshness_rule"],
        "markets": mk,
        "watchlist_note": "dow / hsi / cpo are reported watchlist items (hub page only), not paired terminals.",
    }


def latest_doc(m: dict, state: str, gen: dt.datetime) -> dict:
    o = obs_value(m)
    return {
        "schema_version": "1.0",
        "market": {"id": m["id"], "label": m["label"], "symbol": m["symbol"], "unit": m.get("unit")},
        "observation": o,
        "state": state,
        "state_computed_at": gen.isoformat(),
        "freshness_rule": LEDGER_DATA["freshness_rule"],
        "endpoints": {
            "registry": f"{BASE}/api/markets/registry",
            "markdown": f"{BASE}/markets/{m['id']}/index.md",
            "page": f"{BASE}/markets/{m['id']}/",
            "world_pair": m["world_url"],
        },
        "boundary": f"{BOUNDARY} — authority ceiling {AUTHORITY}. No trade signals. No fabricated values.",
    }


def sitemap(gen: dt.datetime) -> str:
    urls = [f"{BASE}/markets/"] + [f"{BASE}/markets/{m['id']}/" for m in MARKETS] + \
           [f"{BASE}/markets/{m['id']}/index.md" for m in MARKETS] + \
           [f"{BASE}/", f"{BASE}/llms.txt", f"{BASE}/api/markets/registry"]
    items = "".join(
        f"  <url><loc>{u}</loc><lastmod>{gen.date().isoformat()}</lastmod></url>\n" for u in urls
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'


def main() -> int:
    global LEDGER_DATA, MARKETS, FRESH_H
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    LEDGER_DATA = json.loads(LEDGER.read_text())
    MARKETS = LEDGER_DATA["markets"]
    FRESH_H = LEDGER_DATA["freshness_rule"]["fresh_within_hours"]
    gen = now_my()
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
        plan[WEBROOT / f"api/markets/{m['id']}/latest.json"] = json.dumps(latest_doc(m, st, gen), indent=2, ensure_ascii=False) + "\n"

    for path, content in plan.items():
        print(f"{'DRY ' if args.dry_run else 'WRITE'} {path} ({len(content)}B)")
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(f"states={states} generated_at={gen.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
