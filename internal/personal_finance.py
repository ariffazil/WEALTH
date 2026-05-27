"""
WEALTH Personal Finance — D1: Cashflow, EPF, Net Worth, Zakat
6 MCP tools for individual/family financial management.
All tools: recommendation_only=True, final_authority=Arif.
"""

import asyncio
import sys as _sys
from datetime import date as _date, datetime, timezone
from decimal import Decimal
from pathlib import Path as _Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# FastMCP server instance from monolith.py
# --------------------------------------------------------------------------- #
_monolith_dir = str(_Path(__file__).parent.parent)
if _monolith_dir not in _sys.path:
    _sys.path.insert(0, _monolith_dir)

try:
    from internal import monolith

    mcp = getattr(monolith, "mcp", None)
except Exception:  # pragma: no cover — test / dev fallback
    mcp = None


# --------------------------------------------------------------------------- #
# DB helpers
# --------------------------------------------------------------------------- #


async def _init_db():
    from .db_schema import init_schema

    await init_schema()


async def _get_txns(owner, start_dt, end_dt, category, limit):
    from .db_schema import get_transactions

    return await get_transactions(owner, start_dt, end_dt, category, limit)


async def _get_assets(owner):
    from .db_schema import get_assets

    return await get_assets(owner)


async def _get_liabs(owner):
    from .db_schema import get_liabilities

    return await get_liabilities(owner)


async def _get_epf(owner):
    from .db_schema import get_latest_epf

    return await get_latest_epf(owner)


# --------------------------------------------------------------------------- #
# Tool: wealth_cashflow_track
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_cashflow_track")
    def wealth_cashflow_track(
        owner: str = "arif",
        txn_date: Optional[str] = None,
        description: str = "",
        category: str = "expense",
        subcategory: Optional[str] = None,
        amount: float = 0.0,
        currency: str = "MYR",
    ) -> Dict[str, Any]:
        """Ω-D1-01: Cashflow Track — Record a single financial transaction.

        Args:
            owner: Person the transaction belongs to. Default: arif.
            txn_date: Transaction date (YYYY-MM-DD). Default: today.
            description: Human-readable description.
            category: salary | expense | income | investment | loan | savings | zakat
            subcategory: Optional finer category.
            amount: Positive = inflow, negative = outflow.
            currency: 3-letter ISO code. Default MYR.
        """
        parsed = txn_date or _date.today().isoformat()
        parsed_date = datetime.strptime(parsed, "%Y-%m-%d").date()

        async def _run():
            await _init_db()
            from .db_schema import upsert_transaction

            return await upsert_transaction(
                owner=owner,
                date=parsed_date,
                description=description,
                category=category,
                amount=amount,
                currency=currency,
                subcategory=subcategory,
            )

        loop = asyncio.get_event_loop()
        txn_id = loop.run_until_complete(_run())

        return {
            "mcp": "WEALTH",
            "tool": "wealth_cashflow_track",
            "status": "recorded",
            "transaction_id": txn_id,
            "date": str(parsed_date),
            "description": description,
            "category": category,
            "amount": amount,
            "currency": currency,
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_cashflow_track(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_cashflow_summary
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_cashflow_summary")
    def wealth_cashflow_summary(
        owner: str = "arif",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ω-D1-02: Cashflow Summary — Aggregate transactions by category.

        Args:
            owner: Person to summarise. Default: arif.
            start_date: YYYY-MM-DD. Default: 1st of current month.
            end_date: YYYY-MM-DD. Default: today.
            category: Filter by category. Default: all.
        """
        today = _date.today()
        start_str = start_date or today.replace(day=1).isoformat()
        end_str = end_date or today.isoformat()
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()

        async def _run():
            await _init_db()
            return await _get_txns(owner, start_dt, end_dt, category, 5000)

        loop = asyncio.get_event_loop()
        txns = loop.run_until_complete(_run())

        inflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) > 0)
        outflows = sum(float(t["amount"]) for t in txns if float(t["amount"]) < 0)
        by_cat: Dict[str, float] = {}
        for t in txns:
            c = str(t["category"])
            by_cat[c] = by_cat.get(c, 0.0) + float(t["amount"])

        return {
            "mcp": "WEALTH",
            "tool": "wealth_cashflow_summary",
            "owner": owner,
            "period": {"start": start_str, "end": end_str},
            "transaction_count": len(txns),
            "inflows": round(inflows, 4),
            "outflows": round(outflows, 4),
            "net": round(inflows + outflows, 4),
            "by_category": {k: round(v, 4) for k, v in by_cat.items()},
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_cashflow_summary(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_runway_calculate
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_runway_calculate")
    def wealth_runway_calculate(
        monthly_burn: float = 0.0,
        liquid_assets: float = 0.0,
        conservative_factor: float = 0.8,
    ) -> Dict[str, Any]:
        """Ω-D1-03: Runway Calculate — Months of financial runway.

        Args:
            monthly_burn: Average monthly net outflow (MYR).
            liquid_assets: Total accessible liquid assets (MYR).
            conservative_factor: Safety discount (0–1). Default 0.80.
        """
        adjusted = liquid_assets * conservative_factor
        months = round(adjusted / monthly_burn, 1) if monthly_burn > 0 else float("inf")
        break_even_pa = (adjusted / 12) if adjusted > 0 else 0.0

        if months < 3:
            stress = "CRITICAL — less than 3 months runway"
        elif months < 6:
            stress = "AMBER — 3–6 months, build buffer"
        elif months < 12:
            stress = "CAUTION — 6–12 months"
        else:
            stress = "GREEN — 12+ months runway"

        return {
            "mcp": "WEALTH",
            "tool": "wealth_runway_calculate",
            "months_runway": months,
            "adjusted_liquid_assets": round(adjusted, 4),
            "break_even_burn_pa": round(break_even_pa, 4),
            "monthly_burn": monthly_burn,
            "liquid_assets": liquid_assets,
            "conservative_factor": conservative_factor,
            "stress_label": stress,
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_runway_calculate(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_net_worth_snapshot
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_net_worth_snapshot")
    def wealth_net_worth_snapshot(
        owner: str = "arif",
        include_EPF: bool = True,
    ) -> Dict[str, Any]:
        """Ω-D1-04: Net Worth Snapshot — Assets minus Liabilities.

        Args:
            owner: Person to assess. Default: arif.
            include_EPF: Pull latest EPF snapshot. Default True.
        """

        async def _run():
            await _init_db()
            assets = await _get_assets(owner)
            liabs = await _get_liabs(owner)
            epf = await _get_epf(owner) if include_EPF else None

            total_assets = sum(float(a["current_value"]) for a in assets)
            total_liab = sum(float(l["outstanding"]) for l in liabs)

            by_class: Dict[str, float] = {}
            for a in assets:
                c = str(a["asset_class"])
                by_class[c] = by_class.get(c, 0.0) + float(a["current_value"])

            epf_total = 0.0
            epf_date = None
            if epf and include_EPF:
                epf_total = float(epf["total"])
                epf_date = str(epf["snapshot_date"])
                total_assets += epf_total
                by_class["epf"] = by_class.get("epf", 0.0) + epf_total

            return {
                "total_assets": round(total_assets, 4),
                "total_liabilities": round(total_liab, 4),
                "net_worth": round(total_assets - total_liab, 4),
                "asset_breakdown": {k: round(v, 4) for k, v in by_class.items()},
                "liability_breakdown": {
                    str(l["liability_class"]): round(float(l["outstanding"]), 4)
                    for l in liabs
                },
                "epf_total": round(epf_total, 4),
                "epf_date": epf_date,
            }

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_run())

        return {
            "mcp": "WEALTH",
            "tool": "wealth_net_worth_snapshot",
            "owner": owner,
            "recommendation_only": True,
            "final_authority": "Arif",
            **result,
        }

else:

    def wealth_net_worth_snapshot(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_epf_project
# --------------------------------------------------------------------------- #

if mcp:

    @mcp.tool(name="wealth_epf_project")
    def wealth_epf_project(
        current_account_1: float = 0.0,
        current_account_2: float = 0.0,
        monthly_contribution: float = 0.0,
        current_age: int = 30,
        target_age: int = 55,
        annual_rate: float = 0.0515,
        employer_match: float = 0.0,
    ) -> Dict[str, Any]:
        """Ω-D1-05: EPF Project — Project EPF accumulation to target age.

        Args:
            current_account_1: EPF Account 1 balance (MYR).
            current_account_2: EPF Account 2 balance (MYR).
            monthly_contribution: Monthly employee contribution (MYR).
            current_age: Current age. Default 30.
            target_age: Target withdrawal age. Default 55.
            annual_rate: Annual dividend rate. Default 5.15%% EPB 2024.
            employer_match: Monthly employer contribution (MYR). Default 0.
        """
        current = current_account_1 + current_account_2
        years = max(0, target_age - current_age)
        months = years * 12
        total_monthly = monthly_contribution + employer_match

        r_month = annual_rate / 12
        fv_current = current * ((1 + r_month) ** months) if r_month > 0 else current
        fv_annuity = (
            total_monthly * (((1 + r_month) ** months - 1) / r_month)
            if r_month > 0
            else total_monthly * months
        )

        projected = fv_current + fv_annuity
        total_contrib = current + (total_monthly * months)
        total_growth = projected - total_contrib

        # Malaysian EPF 2025 blended rate by age band
        def epf_rate_for_age(age: int) -> float:
            if age < 50:
                return 0.0515
            if age < 55:
                return 0.0520
            if age < 60:
                return 0.0530
            return 0.0540

        blended = (
            sum(epf_rate_for_age(current_age + y) for y in range(years)) / years
            if years > 0
            else annual_rate
        )

        return {
            "mcp": "WEALTH",
            "tool": "wealth_epf_project",
            "current_balance": current,
            "projected_total": round(projected, 4),
            "total_contributions": round(total_contrib, 4),
            "total_growth": round(total_growth, 4),
            "age_55_value": round(projected, 4),
            "years_to_target": years,
            "monthly_contribution": monthly_contribution,
            "employer_match": employer_match,
            "blended_annual_rate": round(blended, 4),
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_epf_project(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}


# --------------------------------------------------------------------------- #
# Tool: wealth_zakat_calculate
# Malaysian nisab 2024/2025: ~MYR 14,254 (gold-based, updated annually)
# --------------------------------------------------------------------------- #

NISAB_MYR = 14254.0
ZAKAT_RATE = 0.025

if mcp:

    @mcp.tool(name="wealth_zakat_calculate")
    def wealth_zakat_calculate(
        owner: str = "arif",
        year: Optional[int] = None,
        total_wealth: Optional[float] = None,
        currency: str = "MYR",
    ) -> Dict[str, Any]:
        """Ω-D1-06: Zakat Calculate — Islamic wealth tax on assets above nisab.

        Args:
            owner: Person to assess. Default: arif.
            year: Zakat year. Default: current year.
            total_wealth: Override total net wealth (MYR). If None, fetch from DB.
            currency: 3-letter ISO. Default MYR.
        """
        year = year or _date.today().year

        async def _run():
            if total_wealth is None:
                await _init_db()
                assets = await _get_assets(owner)
                liabs = await _get_liabs(owner)
                epf = await _get_epf(owner)
                total_a = sum(float(a["current_value"]) for a in assets)
                total_l = sum(float(l["outstanding"]) for l in liabs)
                if epf:
                    total_a += float(epf["total"])
                return total_a - total_l
            return total_wealth

        loop = asyncio.get_event_loop()
        wealth = loop.run_until_complete(_run())

        zakatable = max(0.0, wealth - NISAB_MYR)
        zakat_amount = zakatable * ZAKAT_RATE

        return {
            "mcp": "WEALTH",
            "tool": "wealth_zakat_calculate",
            "owner": owner,
            "year": year,
            "total_wealth": round(wealth, 4),
            "nisab_threshold_myr": NISAB_MYR,
            "is_nisab_achieved": wealth >= NISAB_MYR,
            "zakatable_wealth": round(zakatable, 4),
            "zakat_rate": ZAKAT_RATE,
            "zakat_amount": round(zakat_amount, 4),
            "currency": currency,
            "recommendation_only": True,
            "final_authority": "Arif",
        }

else:

    def wealth_zakat_calculate(**kwargs):
        return {"error": "FastMCP not initialised", "mcp": "WEALTH"}
