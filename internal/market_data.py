"""
WEALTH Market Data — D3: FX, Commodities, Macro Indicators
3 MCP tools for live market intelligence.
Data sourced from public APIs (no API key required).
All tools: recommendation_only=True, final_authority=Arif.
"""

from __future__ import annotations


import sys as _sys
from datetime import date as _date
from pathlib import Path as _Path
from typing import Any, Dict, Optional

import httpx
import httpx2  # FastMCP 4 migration

# --------------------------------------------------------------------------- #
# FastMCP server instance from monolith.py
# --------------------------------------------------------------------------- #
_mono_dir = str(_Path(__file__).parent.parent)
if _mono_dir not in _sys.path:
    _sys.path.insert(0, _mono_dir)

try:
    from internal import monolith

    mcp = getattr(monolith, "mcp", None)
except Exception:
    mcp = None


# --------------------------------------------------------------------------- #
# HTTP client defaults
# --------------------------------------------------------------------------- #
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


# --------------------------------------------------------------------------- #
# Tool: wealth_fx_rate
# Uses Frankfurter API (no key required) — base EUR, pair list flexible
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_fx_rate")
    def wealth_fx_rate(
        base: str = "USD",
        targets: str = "MYR,SGD,GBP,EUR,JPY,CNY,AUD",
        as_of_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ω-D3-01: FX Rate — Live or historical foreign-exchange rates.

        Args:
            base: Base currency ISO code. Default USD.
            targets: Comma-separated target currencies. Default MYR,SGD,GBP,EUR,JPY,CNY,AUD.
            as_of_date: Historical date YYYY-MM-DD. Default: latest.
        """
        target_list = [t.strip() for t in targets.split(",")]
        params: Dict[str, Any] = {"base": base.upper()}
        if as_of_date:
            params["date"] = as_of_date

        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                url = "https://api.frankfurter.dev/v1/latest"
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            rates = data.get("rates", {})
            result = {
                f"{base.upper()}/{t.upper()}": round(rates.get(t, float("nan")), 4)
                for t in target_list
                if t.upper() != base.upper()
            }
            return {
                "mcp": "WEALTH",
                "tool": "wealth_fx_rate",
                "base": base.upper(),
                "date": data.get("date") or as_of_date,
                "rates": result,
                "provider": "Frankfurter API",
                "recommendation_only": True,
                "final_authority": "Arif",
            }
        except (httpx.HTTPError, httpx2.HTTPError) as e:
            return {
                "mcp": "WEALTH",
                "tool": "wealth_fx_rate",
                "status": "error",
                "message": str(e),
                "base": base.upper(),
                "targets": target_list,
                "recommendation_only": True,
                "final_authority": "Arif",
            }

else:

    def wealth_fx_rate(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_commodity_price
# Uses EIA open data or approximate proxies.
# For brent crude: use Frankfurter commodity proxy or EIA open API.
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_commodity_price")
    def wealth_commodity_price(
        commodity: str = "brent_crude",
        unit: str = "usd_per_bbl",
        as_of_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ω-D3-02: Commodity Price — Approximate market prices for key commodities.

        Supported commodities:
            brent_crude  — Brent crude oil (USD/barrel)
            lng_asia     — LNG Asia spot (USD/MMBtu) — approximate
            coal_api2    — API2 coal (USD/tonne) — approximate
            gold         — Gold (USD/troy oz)
            malaysia_rsd — Malaysian crude Miri (USD/barrel) — approximate

        Args:
            commodity: One of the supported commodities above.
            unit: Reporting unit (informational only).
            as_of_date: YYYY-MM-DD for historical. Default: latest.

        Note: Exact live pricing requires Bloomberg/Refinitiv API.
              These values are approximate proxies for WEALTH internal use.
        """
        # Static approximate lookup — update periodically
        # Real implementation would call EIA / Bloomberg / ICE
        APPROX_PRICES = {
            "brent_crude": {
                "price": 78.50,
                "unit": "USD/bbl",
                "source": "EIA estimate",
                "note": "Replace with live ICE/OPEP secondary source",
            },
            "lng_asia": {
                "price": 10.20,
                "unit": "USD/MMBtu",
                "source": "SLRChina/Peak consultancy estimate",
                "note": "Spot MOPS; actual LTC deals differ",
            },
            "coal_api2": {
                "price": 113.00,
                "unit": "USD/tonne",
                "source": "API2 ICE assessment",
                "note": "Cal-23 contract price",
            },
            "gold": {
                "price": 4063.40,
                "unit": "USD/troy_oz",
                "source": "LBMA PM fix + market breakout (2026)",
                "note": "Updated 2026-07-16 from stale 2024 fixture ($2,340). Live: ~$3,980-$4,100 range. Confirm with LBMA for exact fix.",
            },
            "malaysia_rsd": {
                "price": 82.00,
                "unit": "USD/bbl",
                "source": "Miri/Bintulu spot estimate",
                "note": "Light sweet crude — actual LTC price differs",
            },
        }

        commodity = commodity.lower().strip()
        info = APPROX_PRICES.get(commodity)

        if not info:
            return {
                "mcp": "WEALTH",
                "tool": "wealth_commodity_price",
                "status": "unsupported",
                "commodity": commodity,
                "supported": list(APPROX_PRICES.keys()),
                "recommendation_only": True,
                "final_authority": "Arif",
            }

        return {
            "mcp": "WEALTH",
            "tool": "wealth_commodity_price",
            "commodity": commodity,
            "price": info["price"],
            "unit": unit,
            "price_unit": info["unit"],
            "date": as_of_date or _date.today().isoformat(),
            "source": info["source"],
            "note": info["note"],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_commodity_price(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_macro_indicator
# World Bank / IMF / Bank Negara Malaysia open data.
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_macro_indicator")
    def wealth_macro_indicator(
        indicator: str = "usd_myr",
        country: str = "MYS",
        as_of_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ω-D3-03: Macro Indicator — Key macroeconomic indicators.

        Supported indicators:
            usd_myr       — USD/MYR exchange rate
            inflation_my  — Malaysia CPI inflation (annual %)
            gdp_growth_my — Malaysia GDP growth (annual %)
            brent         — Brent crude (USD/bbl) — proxy
            opec_basket   — OPEC reference basket (USD/bbl)
            coal_api2     — API2 coal (USD/tonne)
            interest_rate_my — Bank Negara Malaysia OPR rate (%)

        Args:
            indicator: One of the supported indicators above.
            country: ISO country code (for contextual indicators). Default MYS.
            as_of_date: YYYY-MM-DD. Default: latest.

        Data sources: World Bank API, Bank Negara Malaysia API, EIA.
        """
        indicator = indicator.lower().strip()

        # World Bank API (no key)
        def world_bank(
            indicator_code: str, country_code: str = "MYS"
        ) -> Optional[Dict]:
            try:
                url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
                params = {"format": "json", "per_page": 1, "date": "2020:2025"}
                with httpx.Client(timeout=_TIMEOUT) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    items = resp.json()
                    if isinstance(items, list) and len(items) > 1 and items[1]:
                        entry = items[1][0]
                        return {
                            "value": entry.get("value"),
                            "year": entry.get("date"),
                            "country": entry.get("country", {}).get("value"),
                        }
            except Exception:
                pass
            return None

        # Bank Negara Malaysia API (no key)
        def bank_negara(series_id: str) -> Optional[Dict]:
            try:
                url = "https://api.banknegara.gov.my/v1/statistics"
                params = {"series_id": series_id, "per_page": 1}
                with httpx.Client(timeout=_TIMEOUT) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    if data and isinstance(data, list):
                        return {
                            "value": data[0].get("value"),
                            "unit": data[0].get("unit"),
                        }
            except Exception:
                pass
            return None

        # EIA open data
        def eia_price(product: str) -> Optional[float]:
            try:
                # EIA petroleum status page (scraped approximation)
                url = "https://www.eia.gov/petroleum/"
                with httpx.Client(timeout=_TIMEOUT) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                return None  # Would need proper scraper
            except Exception:
                return None

        results: Dict[str, Any] = {
            "mcp": "WEALTH",
            "tool": "wealth_macro_indicator",
            "indicator": indicator,
            "country": country,
            "date": as_of_date or _date.today().isoformat(),
            "recommendation_only": True,
            "final_authority": "Arif",
        }

        if indicator == "usd_myr":
            fx_data = world_bank("PA.NUS.FCRF", "MYS")  # USD/MYR
            if fx_data and fx_data.get("value"):
                results["value"] = round(fx_data["value"], 4)
                results["year"] = fx_data.get("year")
                results["source"] = "World Bank / Penn World Table"
            else:
                # Fallback: use frankfurter
                try:
                    with httpx.Client(timeout=_TIMEOUT) as client:
                        r = client.get(
                            "https://api.frankfurter.dev/v1/latest",
                            params={"base": "USD", "symbols": "MYR"},
                        )
                        r.raise_for_status()
                        d = r.json()
                        results["value"] = round(d["rates"]["MYR"], 4)
                        results["source"] = "Frankfurter API"
                except Exception:
                    results["value"] = None
                    results["status"] = "unavailable"

        elif indicator == "inflation_my":
            data = world_bank("FP.CPI.TOTL.ZG", "MYS")
            if data:
                results["value"] = data.get("value")
                results["year"] = data.get("year")
                results["source"] = "World Bank CPI"
            else:
                results["status"] = "unavailable"

        elif indicator == "gdp_growth_my":
            data = world_bank("NY.GDP.MKTP.KD.ZG", "MYS")
            if data:
                results["value"] = data.get("value")
                results["year"] = data.get("year")
                results["source"] = "World Bank GDP"
            else:
                results["status"] = "unavailable"

        elif indicator == "interest_rate_my":
            # Bank Negara OPR — approximate from public releases
            results["value"] = 3.00  # OPR as of 2024-2025
            results["source"] = "Bank Negara Malaysia OPR (public release)"
            results["note"] = "Verify against latest BNM statistical release"

        elif indicator in ("brent", "opec_basket", "coal_api2"):
            # Approximate static values — replace with live feed
            STATIC = {
                "brent": {"value": 78.50, "source": "EIA weekly estimate"},
                "opec_basket": {"value": 76.80, "source": "OPEC OPEC Reference Basket"},
                "coal_api2": {"value": 113.00, "source": "ICE API2 assessment"},
            }
            info = STATIC.get(indicator, {})
            results["value"] = info.get("value")
            results["source"] = info.get("source", "approximate")
            results["note"] = "Replace with live ICE/EIA feed for production"

        else:
            results["status"] = "unsupported"
            results["supported"] = [
                "usd_myr",
                "inflation_my",
                "gdp_growth_my",
                "brent",
                "opec_basket",
                "coal_api2",
                "interest_rate_my",
            ]

        return results

else:

    def wealth_macro_indicator(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}

# NOTE: wealth_market_data tool lives in monolith.py (canonical home).
# Gold mode added there to avoid name conflicts.
