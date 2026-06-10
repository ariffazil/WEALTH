"""
WEALTH Stock Analysis — Risk & Exposure Tools
══════════════════════════════════════════════

Portfolio exposure analysis and Bursa Malaysia cost model.
Purpose: Detect hidden risk before it becomes damage.

DITEMPA BUKAN DIBERI — Risk awareness is forged, not given.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ─── Tool 5: check_portfolio_exposure ────────────────────────────────────


def check_portfolio_exposure(
    positions: Optional[List[Dict[str, Any]]] = None,
    account_balance: float = 0.0,
) -> dict:
    """Total portfolio exposure and gap-down scenario analysis.

    Each position dict: ticker, position_value_rm, stop_loss_distance_pct,
    sector (optional).

    Hard rules:
      - If total exposure > 100% of account → UNSAFE
      - If one sector > 50% → CONCENTRATION_WARNING
      - If 15% gap-down damages survival → 888_HOLD
    """
    warnings: List[str] = []
    missing: List[str] = []

    if not positions:
        missing.append("positions")
    if account_balance <= 0:
        missing.append("account_balance")
    if missing:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": missing,
            "warnings": [],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    total_exposure = 0.0
    loss_if_all_stops = 0.0
    loss_if_gap_5 = 0.0
    loss_if_gap_10 = 0.0
    loss_if_gap_15 = 0.0
    sectors: Dict[str, float] = {}

    for p in positions:
        val = float(p.get("position_value_rm", 0) or 0)
        stop_pct = float(p.get("stop_loss_distance_pct", 5.0) or 5.0)
        sector = str(p.get("sector", "Unknown"))
        ticker = str(p.get("ticker", "?"))

        total_exposure += val
        loss_if_all_stops += val * (stop_pct / 100.0)
        loss_if_gap_5 += val * 0.05
        loss_if_gap_10 += val * 0.10
        loss_if_gap_15 += val * 0.15
        sectors[sector] = sectors.get(sector, 0.0) + val

    exposure_pct = (total_exposure / account_balance) * 100.0

    # ── Checks ──
    verdict = "SAFE_TO_STUDY"

    if exposure_pct > 100.0:
        verdict = "UNSAFE"
        warnings.append(
            f"OVEREXPOSED: total exposure = {exposure_pct:.1f}% of account."
        )

    max_sector_pct = 0.0
    max_sector_name = ""
    for sec, val in sectors.items():
        pct = (val / account_balance) * 100.0
        if pct > max_sector_pct:
            max_sector_pct = pct
            max_sector_name = sec
    if max_sector_pct > 50.0:
        warnings.append(
            f"SECTOR_CONCENTRATION: {max_sector_name} = {max_sector_pct:.1f}% of account."
        )
        if verdict == "SAFE_TO_STUDY":
            verdict = "NEEDS_DATA"

    # ── Survival check ──
    gap15_remaining = account_balance - loss_if_gap_15
    if gap15_remaining < account_balance * 0.5:
        verdict = "888_HOLD"
        warnings.append(
            f"SURVIVAL_RISK: 15% gap-down across all positions = RM{loss_if_gap_15:,.2f} loss. "
            f"Remaining capital: RM{gap15_remaining:,.2f}. Survival threatened."
        )

    return {
        "status": "OK",
        "verdict": verdict,
        "result": {
            "account_balance_rm": round(account_balance, 2),
            "position_count": len(positions),
            "total_exposure_rm": round(total_exposure, 2),
            "exposure_pct": round(exposure_pct, 1),
            "loss_if_all_stops_hit_rm": round(loss_if_all_stops, 2),
            "loss_if_gap_down_5pct_rm": round(loss_if_gap_5, 2),
            "loss_if_gap_down_10pct_rm": round(loss_if_gap_10, 2),
            "loss_if_gap_down_15pct_rm": round(loss_if_gap_15, 2),
            "sector_breakdown": {
                sec: {
                    "value_rm": round(val, 2),
                    "pct_of_account": round((val / account_balance) * 100.0, 1),
                }
                for sec, val in sectors.items()
            },
            "max_sector": max_sector_name,
            "max_sector_pct": round(max_sector_pct, 1),
        },
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }


# ─── Tool 6: apply_bursa_cost_model ─────────────────────────────────────


def apply_bursa_cost_model(
    entry_price: float = 0.0,
    exit_price: float = 0.0,
    position_size: int = 0,
    direction: str = "long",
) -> dict:
    """Apply Bursa Malaysia transaction cost model.

    Detects fake small winners — a +0.39% gross gain may be
    flat or negative after real costs.

    Costs modelled:
      - Brokerage: 0.10% (min RM8) — typical retail rate
      - Clearing fee: 0.03% (capped RM1,000)
      - Stamp duty: RM1.00 per RM1,000 of contract value
      - Bid-ask spread: ~0.5% (estimated, for small caps can be wider)
      - Slippage: ~0.3% (estimated, for liquid stocks)
    """
    missing: List[str] = []
    if entry_price <= 0:
        missing.append("entry_price")
    if exit_price <= 0:
        missing.append("exit_price")
    if position_size <= 0:
        missing.append("position_size")
    if missing:
        return {
            "status": "NEEDS_DATA",
            "verdict": "NEEDS_DATA",
            "missing_data": missing,
            "warnings": [],
            "recommendation_only": True,
            "final_authority": "Arif",
        }

    entry_value = entry_price * position_size
    exit_value = exit_price * position_size

    # ── Entry-side costs ──
    entry_brokerage = max(entry_value * 0.001, 8.0)
    entry_clearing = entry_value * 0.0003
    entry_stamp = max(1.0, (entry_value / 1000.0) * 1.0)
    entry_costs = entry_brokerage + entry_clearing + entry_stamp

    # ── Exit-side costs ──
    exit_brokerage = max(exit_value * 0.001, 8.0)
    exit_clearing = exit_value * 0.0003
    exit_stamp = max(1.0, (exit_value / 1000.0) * 1.0)
    exit_costs = exit_brokerage + exit_clearing + exit_stamp

    # ── Spread + slippage (estimated) ──
    spread_cost = entry_value * 0.005
    slippage_cost = entry_value * 0.003
    estimated_market_cost = spread_cost + slippage_cost

    total_costs = entry_costs + exit_costs + estimated_market_cost

    # ── Gross vs Net ──
    if direction == "long":
        gross_pl = (exit_price - entry_price) * position_size
    else:
        gross_pl = (entry_price - exit_price) * position_size

    gross_pl_pct = (gross_pl / entry_value) * 100.0 if entry_value else 0.0
    net_pl = gross_pl - total_costs
    net_pl_pct = (net_pl / entry_value) * 100.0 if entry_value else 0.0

    # ── Verdict ──
    verdict = "SAFE_TO_STUDY"
    warnings: List[str] = []
    if gross_pl_pct > 0 and net_pl_pct <= 0:
        verdict = "NEEDS_DATA"
        warnings.append(
            f"FAKE_WINNER: Gross gain +{gross_pl_pct:.2f}%, "
            f"but after all costs net = {net_pl_pct:.2f}%. "
            f"This trade may not be profitable after costs."
        )
    elif gross_pl_pct > 0 and 0 < net_pl_pct < 0.5:
        warnings.append(
            f"THIN_WINNER: Net gain only {net_pl_pct:.2f}% after costs. "
            f"Very small buffer for adverse moves."
        )

    return {
        "status": "OK",
        "verdict": verdict,
        "result": {
            "entry_value_rm": round(entry_value, 2),
            "exit_value_rm": round(exit_value, 2),
            "entry_costs": {
                "brokerage_rm": round(entry_brokerage, 2),
                "clearing_fee_rm": round(entry_clearing, 2),
                "stamp_duty_rm": round(entry_stamp, 2),
                "subtotal_rm": round(entry_costs, 2),
            },
            "exit_costs": {
                "brokerage_rm": round(exit_brokerage, 2),
                "clearing_fee_rm": round(exit_clearing, 2),
                "stamp_duty_rm": round(exit_stamp, 2),
                "subtotal_rm": round(exit_costs, 2),
            },
            "estimated_market_cost": {
                "bid_ask_spread_rm": round(spread_cost, 2),
                "slippage_rm": round(slippage_cost, 2),
                "subtotal_rm": round(estimated_market_cost, 2),
            },
            "total_costs_rm": round(total_costs, 2),
            "gross_pl_rm": round(gross_pl, 2),
            "gross_pl_pct": round(gross_pl_pct, 2),
            "net_pl_rm": round(net_pl, 2),
            "net_pl_pct": round(net_pl_pct, 2),
            "cost_model": "Bursa Malaysia retail: 0.10% brokerage (min RM8), 0.03% clearing, RM1/1k stamp, +0.5% spread +0.3% slippage (estimated)",
        },
        "warnings": warnings,
        "recommendation_only": True,
        "final_authority": "Arif",
    }
