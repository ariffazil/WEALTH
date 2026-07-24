"""
WEALTH Core — Capital Domain.

Pure capital computation engines extracted from monolith.
No MCP dependency, no I/O, pure computation.

Submodules:
- conservation: NPV, IRR, PI, payback, net worth, ledger
- flow: Cashflow, runway, burn, triage, velocity
- gradient: Spread, mispricing, pressure detection
- energy: Productivity, efficiency, ROI
- time_discount: NPV, IRR, payback, MIRR, compounding
- inertia: DSCR, leverage, strain, fragility

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

# Re-export math primitives for convenience
from ..math import npv, irr, profitability_index, payback_period, emv, dscr


def compute_conservation(
    assets: list[dict] | None = None,
    liabilities: list[dict] | None = None,
) -> dict:
    """
    Compute capital conservation metrics.
    Returns net worth, asset total, liability total.
    """
    def _amount(item: dict) -> float:
        """Defensive extraction: reject str (would otherwise raise TypeError
        on `int + str` in sum()) and return 0 with a soft skip.  SURVIVAL-
        OF-THE-FITTEST FIX 2026-07-24."""
        raw = item.get("value", item.get("amount", 0))
        if raw is None or isinstance(raw, bool):
            return 0.0
        if isinstance(raw, (int, float)):
            return float(raw)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

    asset_total = sum(_amount(a) for a in (assets or []))
    liability_total = sum(_amount(liab) for liab in (liabilities or []))
    net_worth = asset_total - liability_total

    return {
        "net_worth": net_worth,
        "asset_total": asset_total,
        "liability_total": liability_total,
        "asset_count": len(assets or []),
        "liability_count": len(liabilities or []),
    }


def compute_flow(
    income: list[dict] | None = None,
    expenses: list[dict] | None = None,
) -> dict:
    """
    Compute cash flow metrics.
    Returns net cashflow, income total, expense total, monthly burn.
    """
    income_total = sum(i.get("amount", 0) for i in (income or []))
    expense_total = sum(e.get("amount", 0) for e in (expenses or []))
    net = income_total - expense_total

    return {
        "net_cashflow": net,
        "income_total": income_total,
        "expense_total": expense_total,
        "monthly_burn": expense_total,
        "is_positive": net > 0,
    }


def compute_runway(
    liquid_assets: float,
    monthly_burn: float,
    conservative_factor: float = 0.8,
) -> dict:
    """
    Compute financial runway in months.
    """
    effective_assets = liquid_assets * conservative_factor
    if monthly_burn <= 0:
        runway_months = float("inf")
    else:
        runway_months = effective_assets / monthly_burn

    return {
        "runway_months": round(runway_months, 1) if runway_months != float("inf") else "infinite",
        "effective_assets": effective_assets,
        "monthly_burn": monthly_burn,
        "conservative_factor": conservative_factor,
    }


def compute_gradient(
    bid: float,
    ask: float,
    reference_price: float | None = None,
) -> dict:
    """
    Compute price gradient (spread, mispricing).
    """
    spread = ask - bid
    spread_pct = (spread / bid * 100) if bid > 0 else 0
    mid = (bid + ask) / 2

    mispricing = None
    if reference_price:
        mispricing = mid - reference_price

    return {
        "spread": round(spread, 4),
        "spread_pct": round(spread_pct, 4),
        "mid_price": round(mid, 4),
        "bid": bid,
        "ask": ask,
        "reference_price": reference_price,
        "mispricing": round(mispricing, 4) if mispricing is not None else None,
    }


def compute_energy(
    output_value: float,
    input_cost: float,
) -> dict:
    """
    Compute energy/productivity metrics.
    """
    if input_cost == 0:
        pi = float("inf")
        roi = float("inf")
    else:
        pi = output_value / input_cost
        roi = (output_value - input_cost) / input_cost

    return {
        "profitability_index": round(pi, 4),
        "roi": round(roi, 4),
        "output_value": output_value,
        "input_cost": input_cost,
        "is_efficient": pi > 1.0,
    }


def compute_inertia(
    ebitda: float,
    principal: float,
    interest: float,
    leases: float = 0,
) -> dict:
    """
    Compute leverage/inertia metrics.
    """
    debt_service = interest + leases + (principal * 0.1)  # Simplified
    dscr_val = dscr(ebitda, debt_service)
    leverage_ratio = principal / ebitda if ebitda > 0 else float("inf")

    return {
        "dscr": dscr_val,
        "leverage_ratio": round(leverage_ratio, 4) if leverage_ratio != float("inf") else "infinite",
        "debt_service": debt_service,
        "ebitda": ebitda,
        "is_healthy": dscr_val > 1.25,
    }


__all__ = [
    "compute_conservation",
    "compute_flow",
    "compute_runway",
    "compute_gradient",
    "compute_energy",
    "compute_inertia",
    "npv",
    "irr",
    "profitability_index",
    "payback_period",
    "emv",
    "dscr",
]
