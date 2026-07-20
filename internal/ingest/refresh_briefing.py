"""
WEALTH Daily Briefing — full refresh with TokenRouter AI synthesis.
Fetches market data via yfinance, then uses TokenRouter + deepseek
to generate the So What analysis, economy signals, politics, social, and global context.
"""

import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

MYT = timezone(timedelta(hours=8))
NOW = datetime.now(MYT)
TODAY = NOW.strftime("%Y-%m-%d")
TARGET = Path("/var/www/html/arif/data/wealth/latest.json")
SOURCE_REPO = Path(
    "/root/arif-sites/sites/arif-fazil.com/public/data/wealth/latest.json"
)

# Load TokenRouter config from env
TOKENROUTER_KEY = os.environ.get("TOKENROUTER_API_KEY", "")
if not TOKENROUTER_KEY:
    # Source vault.env if not in environment
    env_path = "/root/.secrets/vault.env"
    if os.path.exists(env_path):
        for line in open(env_path):
            if "TOKENROUTER_API_KEY" in line and "=" in line:
                TOKENROUTER_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
TOKENROUTER_URL = "https://api.tokenrouter.com/v1/chat/completions"
MODEL = "deepseek/deepseek-v4-flash"


def get_stock(symbol):
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        hist = t.history(period="2d")
        if len(hist) >= 2:
            close = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            chg = round(close - prev, 2)
            chg_pct = round((chg / prev) * 100, 2)
            return close, chg, chg_pct
        elif len(hist) == 1:
            return float(hist["Close"].iloc[-1]), 0.0, 0.0
    except Exception as e:
        print(f"  yfinance {symbol}: {e}")
    return None, None, None


def get_fx(pair="USDMYR=X"):
    try:
        import yfinance as yf

        t = yf.Ticker(pair)
        hist = t.history(period="2d")
        if len(hist) >= 1:
            return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"  FX error: {e}")
    return None


def get_brent():
    try:
        import yfinance as yf

        t = yf.Ticker("BZ=F")
        hist = t.history(period="2d")
        return float(hist["Close"].iloc[-1]) if len(hist) >= 1 else None
    except Exception as e:
        print(f"  Brent error: {e}")
    return None


def synthesize_with_ai(klci, klci_pct, usd_myr, brent, date_str):
    """Use TokenRouter + deepseek to generate the briefing narrative.
    Grounded in Malaysian policy facts file — never from training memory."""
    if not TOKENROUTER_KEY:
        print("  No TokenRouter key — skipping AI synthesis")
        return None

    market_data = {
        "date": date_str,
        "klci": f"{klci:.2f}" if klci else None,
        "klci_change_pct": f"{klci_pct:.2f}%" if klci_pct else None,
        "usd_myr": f"{usd_myr:.4f}" if usd_myr else None,
        "brent": f"${brent:.2f}" if brent else None,
    }

    # Load grounded policy facts
    facts_path = Path(__file__).parent / "facts/malaysia_policy.json"
    policy_facts = {}
    if facts_path.exists():
        with open(facts_path) as f:
            policy_facts = json.load(f)

    # System context: always-true facts
    system_context = f"""You are the WEALTH capital intelligence engine for arifOS. These are GROUND TRUTH facts about Malaysian policy and global schedules. You MUST USE these facts. You MUST NOT contradict them. If a fact is not in this context, say "No data" rather than relying on your training memory.

GROUND TRUTH — MALAYSIA POLICY (current as of {date_str}):
{json.dumps(policy_facts, indent=2)}

SCHEDULED FOMC MEETINGS (do NOT report outcomes before these dates):
- July 28-29, 2026 (NOT YET HELD)
- September 16, 2026
- November 4, 2026
- December 16, 2026

INSTITUTIONAL ROLES:
- DOSM: releases GDP advance estimates, CPI
- BNM: sets OPR, monetary policy
- Neither institution issues the other's data."""

    prompt = f"""Today's market data (yfinance verified):
{json.dumps(market_data, indent=2)}

Generate a Malaysian daily briefing. Return valid JSON only.

Every section must include a "source_id" field (e.g. "BURSA", "DOSM", "BNM", "MERDEKA", "KPDN", "MOF", or "NONE" if unverifiable).

Structure:
{{
  "so_what": [
    {{
      "domain": "MARKET|FX / RINGGIT|OIL & GAS|COST OF LIVING|POLITICS",
      "signal": "Short headline (max 8 words)",
      "delta": "What the ground says — data, no interpretation (1-2 sentences)",
      "omega": "What the logic concludes — evidence-based implication (1-2 sentences)",
      "xi": "What capital should do — actionable signal (1-2 sentences)",
      "psi": "Sovereign check — human stake (1 sentence)",
      "tone": "caution|neutral|positive|critical",
      "source_id": "BURSA|DOSM|BNM|MERDEKA|KPDN|MOF|NONE"
    }}
  ],
  "economy": {{
    "items": [
      {{"title": "Label", "desc": "1-2 sentences", "category": "GDP|TRADE|FISCAL|INFLATION|SNAPSHOT", "source_id": "..."}}
    ]
  }},
  "politics": {{
    "narratives": [
      {{"title": "Headline (~6 words)", "desc": "1-2 sentences", "source_id": "..."}}
    ],
    "economy_policy": [
      {{"title": "Policy name", "desc": "1-2 sentences", "source_id": "..."}}
    ],
    "regional": [
      {{"title": "Region/event", "desc": "1-2 sentences", "source_id": "..."}}
    ]
  }},
  "social": {{
    "cost_of_living": [{{"title": "Topic", "desc": "1-2 sentences", "source_id": "..."}}],
    "labor": [{{"title": "Topic", "desc": "1-2 sentences", "source_id": "..."}}],
    "youth_career": [{{"title": "Topic", "desc": "1-2 sentences", "source_id": "..."}}]
  }},
  "global": {{
    "fed": {{"items": [{{"title": "Fed move", "desc": "1-2 sentences", "source_id": "FOMC"}}]}},
    "china": {{"items": [{{"title": "China signal", "desc": "1-2 sentences", "source_id": "..."}}]}},
    "asean": {{"items": [{{"title": "ASEAN topic", "desc": "1-2 sentences", "source_id": "..."}}]}}
  }}
}}

HARD RULES — VIOLATION WILL VOID THE OUTPUT:
1. NEVER report outcome of a future FOMC, MPC, or OPEC meeting. The July 28-29 FOMC has NOT happened.
2. NEVER fabricate quotes from Powell, Anwar, or any official. If you cannot verify the exact quote, omit it.
3. Every claim MUST have a source_id. If you don't know the source, set source_id="NONE".
4. Use the GROUND TRUTH facts above — do not contradict them with your training memory.
5. RON95 subsidy was REFORMED via BUDI95 (Sept 2025). Unsubsidised price is RM3.72. Do NOT say "still pending."
6. Diesel was rationalised in Peninsula June 2024 (not 2025). Current price RM4.37.
7. DOSM releases GDP advance estimates, not BNM. Q2 2026 advance estimate is 5.8%.
8. Anwar's Merdeka Center approval rating is 52%. The 42% figure is "right direction" — a different question.
9. Brent last actual settle: $88.10 (July 17). Do not report it as traded at $90+.
10. Be direct, no corporate speak. Malaysian context. Return ONLY valid JSON. No markdown."""

    try:
        import urllib.request

        req = urllib.request.Request(
            TOKENROUTER_URL,
            data=json.dumps(
                {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_context},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000,
                }
            ).encode(),
            headers={
                "Authorization": f"Bearer {TOKENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(content)
            so_what = parsed.get("so_what", [])
            economy = parsed.get("economy", {}).get("items", [])
            print(
                f"  AI synthesis: {len(so_what)} signals, {len(economy)} economy items"
            )

            # Validate source_ids — flag any "NONE" entries
            for s in so_what:
                if s.get("source_id") == "NONE":
                    s["delta"] = s.get("delta", "") + " [UNVERIFIED]"
                    s["omega"] = s.get("omega", "") + " [UNVERIFIED]"
            return parsed
    except Exception as e:
        print(f"  AI synthesis error: {e}")
        return None


def main():
    os.environ.setdefault("TZ", "Asia/Kuala_Lumpur")
    print(f"[{TODAY}] Refreshing briefing...")

    # 1. Market data
    klci, klci_chg, klci_pct = get_stock("^KLSE")
    usd_myr = get_fx("USDMYR=X")
    brent = get_brent()
    print(f"  KLCI: {klci} ({klci_chg:+g}) USD/MYR: {usd_myr} Brent: ${brent}")

    # 2. AI synthesis
    ai = synthesize_with_ai(klci, klci_pct, usd_myr, brent, TODAY)

    # 3. Build briefing
    briefing = {
        "meta": {
            "date": TODAY,
            "generated_at": NOW.isoformat(),
            "source": "arifOS WEALTH — yfinance + TokenRouter deepseek",
            "model_note": f"Synth via {MODEL}. Market data from yfinance.",
        },
        "bursa": {
            "klci_close": klci,
            "klci_change_pct": klci_pct,
            "most_active": None,
            "top_gainers_search": [],
            "source_urls": ["https://www.bursamalaysia.com/market"],
        },
        "ringgit": {
            "usd_myr": usd_myr,
            "trend": f"1 USD = {usd_myr:.4f} MYR" if usd_myr else "No data",
            "sources": ["https://www.bnm.gov.my"],
        },
        "economy": ai.get("economy", {"items": []}) if ai else {"items": []},
        "politics": ai.get(
            "politics", {"narratives": [], "economy_policy": [], "regional": []}
        )
        if ai
        else {"narratives": [], "economy_policy": [], "regional": []},
        "social": ai.get(
            "social", {"cost_of_living": [], "labor": [], "youth_career": []}
        )
        if ai
        else {"cost_of_living": [], "labor": [], "youth_career": []},
        "oil_energy": {
            "brent_price": brent,
            "malaysia_oil": [],
            "energy_transition": [],
        },
        "global": ai.get(
            "global",
            {"fed": {"items": []}, "china": {"items": []}, "asean": {"items": []}},
        )
        if ai
        else {"fed": {"items": []}, "china": {"items": []}, "asean": {"items": []}},
        "so_what": ai.get("so_what", []) if ai else [],
    }

    # 4. Write to both live and source
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with open(TARGET, "w") as f:
        json.dump(briefing, f, indent=2, default=str)
    print(f"  Written: {TARGET}")

    if SOURCE_REPO:
        SOURCE_REPO.parent.mkdir(parents=True, exist_ok=True)
        with open(SOURCE_REPO, "w") as f:
            json.dump(briefing, f, indent=2, default=str)
        print(f"  Written: {SOURCE_REPO}")

    print(f"  Summary: KLCI={klci} USD/MYR={usd_myr} Brent=${brent}")
    print(f"  So What: {len(briefing['so_what'])} signals")


if __name__ == "__main__":
    main()
