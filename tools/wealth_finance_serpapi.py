#!/usr/bin/env python3
"""
wealth_finance_serpapi — Google Finance integration for WEALTH organ.
Real-time stock quotes, market overview, crypto/forex via SERP API.
Complements existing wealth_market_data (FX/commodities/macro).

Usage:
    python3 wealth_finance_serpapi.py --ticker PCHEM:KLSE
    python3 wealth_finance_serpapi.py --ticker GOOGL:NASDAQ
    python3 wealth_finance_serpapi.py --ticker BTC-USD
    python3 wealth_finance_serpapi.py --markets  # US/Europe/Asia/Crypto overview
    python3 wealth_finance_serpapi.py --trends "artificial intelligence"
    python3 wealth_finance_serpapi.py --shopping "laptop stand" --country my

Modes: ticker | markets | trends | shopping
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

FORGE_SERPAPI = "/root/A-FORGE/tools/forge_serpapi.py"


def run_serpapi(engine, query, extra_params=None):
    """Call forge_serpapi and return parsed result."""
    cmd = [sys.executable, FORGE_SERPAPI, "-e", engine, "-q", query, "--compact"]
    if extra_params:
        cmd.extend(["-p", json.dumps(extra_params)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stderr or result.stdout or "Unknown error"}


def format_stock_quote(data):
    """Format Google Finance result for WEALTH consumption."""
    summary = data.get("summary", {})
    movement = summary.get("price_movement", {})

    return {
        "domain": "finance.stock",
        "organ": "WEALTH",
        "ticker": summary.get("stock"),
        "exchange": summary.get("exchange"),
        "company": summary.get("title"),
        "price": summary.get("extracted_price"),
        "currency": summary.get("currency"),
        "movement": {
            "direction": movement.get("movement"),
            "pct": movement.get("percentage"),
            "value": movement.get("value"),
        },
        "date": summary.get("date"),
        "after_hours": summary.get("market", {}).get("price")
        if summary.get("market")
        else None,
        "budget_remaining": data.get("budget_remaining", "?"),
    }


def format_markets(data):
    """Format market overview for WEALTH dashboard."""
    markets = data.get("markets", {})

    def extract_indices(market_list):
        return [
            {
                "name": m.get("name"),
                "ticker": m.get("stock"),
                "price": m.get("price"),
                "movement": m.get("price_movement", {}).get("movement"),
                "pct": m.get("price_movement", {}).get("percentage"),
            }
            for m in (market_list or [])[:5]
        ]

    return {
        "domain": "finance.markets",
        "organ": "WEALTH",
        "us": extract_indices(markets.get("us")),
        "europe": extract_indices(markets.get("europe")),
        "asia": extract_indices(markets.get("asia")),
        "currencies": extract_indices(markets.get("currencies")),
        "crypto": extract_indices(markets.get("crypto")),
        "futures": extract_indices(markets.get("futures")),
        "top_news": markets.get("top_news"),
        "budget_remaining": data.get("budget_remaining", "?"),
    }


def format_trends(data):
    """Format Google Trends result."""
    interest = data.get("interest_over_time", {})
    return {
        "domain": "finance.trends",
        "organ": "WEALTH",
        "query": data.get("search_parameters", {}).get("q"),
        "timeline": interest.get("timeline_data", [])[-12:]
        if interest.get("timeline_data")
        else [],
        "related_queries": data.get("related_queries", []),
        "related_topics": data.get("related_topics", []),
        "budget_remaining": data.get("budget_remaining", "?"),
    }


def format_shopping(data):
    """Format Google Shopping result."""
    results = data.get("shopping_results", [])
    return {
        "domain": "commerce.shopping",
        "organ": "WEALTH",
        "products": [
            {
                "title": r.get("title"),
                "price": r.get("extracted_price"),
                "currency": r.get("extracted_price_currency", "USD"),
                "source": r.get("source"),
                "rating": r.get("rating"),
                "reviews": r.get("reviews"),
                "link": r.get("link"),
                "thumbnail": r.get("thumbnail"),
            }
            for r in results[:10]
        ],
        "count": len(results),
        "budget_remaining": data.get("budget_remaining", "?"),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="wealth_finance_serpapi — Google Finance/commerce for WEALTH"
    )
    parser.add_argument(
        "--ticker", "-t", help="Stock ticker (e.g. PCHEM:KLSE, GOOGL:NASDAQ, BTC-USD)"
    )
    parser.add_argument(
        "--markets", action="store_true", help="Market overview (US/Europe/Asia/Crypto)"
    )
    parser.add_argument("--trends", help="Google Trends query")
    parser.add_argument("--shopping", help="Google Shopping query")
    parser.add_argument(
        "--country", default="us", help="Country for shopping (default: us)"
    )
    parser.add_argument(
        "--raw", action="store_true", help="Return raw SERP API response"
    )
    args = parser.parse_args()

    if args.ticker:
        data = run_serpapi("google_finance", args.ticker, {"hl": "en"})
        if "error" in data:
            print(json.dumps(data, indent=2))
            sys.exit(1)
        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(format_stock_quote(data), indent=2))

    elif args.markets:
        data = run_serpapi("google_finance_markets", "markets", {"hl": "en"})
        if "error" in data:
            print(json.dumps(data, indent=2))
            sys.exit(1)
        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(format_markets(data), indent=2))

    elif args.trends:
        data = run_serpapi(
            "google_trends", args.trends, {"hl": "en", "data_type": "TIMESERIES"}
        )
        if "error" in data:
            print(json.dumps(data, indent=2))
            sys.exit(1)
        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(format_trends(data), indent=2))

    elif args.shopping:
        data = run_serpapi(
            "google_shopping", args.shopping, {"hl": "en", "gl": args.country}
        )
        if "error" in data:
            print(json.dumps(data, indent=2))
            sys.exit(1)
        if args.raw:
            print(json.dumps(data, indent=2))
        else:
            print(json.dumps(format_shopping(data), indent=2))

    else:
        parser.error("Specify --ticker, --markets, --trends, or --shopping")


if __name__ == "__main__":
    main()
