"""
⚠️ DEPRECATED — Development demo surface (SSE :8082). ZEN 2026-07-11 W6.

Production WEALTH (7 canonical capital_* tools) is streamable-http on :18082:
  server_federated.py → wealth_mcp/server.py:create_mcp_server()
  systemd: wealth-organ.service

Do NOT use this file as a process-manager entry. Excluded from production.
Kept only for local demo / historical reference.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from fastmcp import FastMCP
import sys
import os

# Add arifOS to path to import shared core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../arifOS")))
from core.shared.governed_tool import governed_tool

mcp = FastMCP("WEALTH-Civilization")

# ─── Named constants (F2 Truth: no unexplained coefficients) ───
PROJECT_LIFE_YEARS: float = 10.0       # standard project evaluation window
BRENT_BENCHMARK: float = 120.0           # USD/bbl baseline for price dignity
HEDGE_DRAG_THRESHOLD: float = 0.15       # 15% → triggers 888_HOLD
REFINERY_MARGIN_DANGER: float = 30.0      # USD/bbl — crisis threshold

# --- Models ---

class MarketAnalysis(BaseModel):
    ticker: str
    sentiment: float
    epistemic_tag: str
    confidence_band: List[float]
    humility_on_projections: bool
    risk_assessment: str

class StressTestResult(BaseModel):
    portfolio_id: str
    max_drawdown: float
    correlation_breakdown: bool
    liquidity_crisis: bool
    hold_triggered: bool

class CrisisAssessment(BaseModel):
    region: str
    energy_sovereignty: float
    grid_integrity: float
    price_dignity: float
    transition_amanah: float
    maruah_score: float
    hold_triggered: bool

class ShortagePrediction(BaseModel):
    region: str
    shortage_probability: float
    uncertainty_band: float
    horizon_days: int

class FoodSecurityIndex(BaseModel):
    country: str
    availability: float
    access: float
    utilization: float
    stability: float
    index_score: float

class ProspectEconomics(BaseModel):
    prospect_id: str
    stoiip_bbl: float
    development_capex: float
    operating_opex: float
    oil_price_assumption: float
    # ─── Multi-factor NOC model (new) ───
    effective_price: float        # hedge_lock_usd if set, else oil_price
    hedge_drag: float             # |spot - lock| / spot — F2 OBS
    fx_impact: float             # RM conversion benefit/cost — F2 OBS
    decline_factor: float         # production falloff multiplier
    downstream_cost_impact: float # refinery margin squeeze (phase 2 reserved)
    # ─── Core economics ───
    npv_10: float
    emv: float
    paradox_score: float
    verdict: str

# --- Domain: Thermodynamic Economics (Golden Path Demo) ---

@mcp.tool()
@governed_tool
async def wealth_evaluate_prospect(
    prospect_id: str,
    stoiip_bbl: float,
    capex_estimate: float = 500_000_000.0,
    opex_per_bbl: float = 15.0,
    oil_price: float = 75.0,
    geological_chance_of_success: float = 0.3,
    # ─── Multi-factor NOC params ───
    hedge_lock_usd: Optional[float] = None,
    rm_usd_rate: Optional[float] = None,
    downstream_margin_usd: Optional[float] = None,
    production_decline_rate: Optional[float] = None,
    lng_contract_price: Optional[float] = None,
    prospect_type: str = "oil",  # "oil" or "gas"
) -> ProspectEconomics:
    """
    Evaluate prospect economics (NPV/EMV) from GEOX volumetrics.
    Applies the WEALTH schema: Paradox, Echo, and multi-factor NOC model.

    Multi-factor enhancements:
    - hedge_lock_usd: locked revenue price vs spot exposure → hedge_drag
    - rm_usd_rate: USD revenue × RM cost base translation
    - downstream_margin_usd: refinery margin squeeze (phase 2 reserved)
    - production_decline_rate: mature field falloff → decline_factor
    - lng_contract_price: gas projects use contract vs spot spread
    - prospect_type: routes oil vs gas pricing logic

    888_HOLD trigger: hedge_drag > 15% OR emv < 0 AND paradox_score > 0.8
    """
    # Vector 2: Cross-System Volumetric Coupling
    if not stoiip_bbl or stoiip_bbl == 0:
        try:
            from host.governance.vault_supabase import get_latest_geox_volumetrics
            geox_data = get_latest_geox_volumetrics(prospect_id)
            if geox_data:
                stoiip_bbl = geox_data.get("stoiip_bbl", stoiip_bbl)
                # If we have a vision bridge ref, log it
                geox_ref = geox_data.get("vision_bridge_ref")
        except Exception:
            pass

    # ── Price effective ──
    effective_price = hedge_lock_usd if hedge_lock_usd else oil_price
    hedge_drag = abs(oil_price - effective_price) / oil_price if hedge_lock_usd and oil_price != effective_price else 0.0

    # ── Recovery factor with decline adjustment ──
    recovery_factor = 0.35
    decline_factor = 1.0
    if production_decline_rate:
        # 4.5 = PROJECT_LIFE_YEARS × 0.45 (empirical production-curve weighting)
        avg_decline_factor = max(0.5, 1.0 - (production_decline_rate * 4.5))
        decline_factor = avg_decline_factor
        recovery_factor = 0.35 * avg_decline_factor

    recoverable_reserves = stoiip_bbl * recovery_factor

    # ── FX conversion (USD revenue → RM cost base) ──
    fx_impact = 0.0
    if rm_usd_rate:
        gross_revenue_usd = recoverable_reserves * effective_price
        gross_revenue_rm = gross_revenue_usd * rm_usd_rate
        capex_rm = capex_estimate * rm_usd_rate
        total_opex_rm = recoverable_reserves * opex_per_bbl * rm_usd_rate
        fx_impact = (rm_usd_rate - 4.5) * gross_revenue_usd / 1_000_000  # RM deviation from baseline in millions
    else:
        gross_revenue_rm = recoverable_reserves * effective_price
        capex_rm = capex_estimate
        total_opex_rm = recoverable_reserves * opex_per_bbl

    net_cash_flow = gross_revenue_rm - capex_rm - total_opex_rm

    # ── LNG gas spread (gas prospects only) ──
    if prospect_type == "gas" and lng_contract_price:
        # Contract gas earns a premium over spot; negative delta = discount
        lng_delta = (lng_contract_price - effective_price) * recoverable_reserves * 0.3
        net_cash_flow += lng_delta

    # ── NPV10 (flat production, 10-year project life) ──
    npv_10 = net_cash_flow * 0.614

    # ── EMV ──
    emv = (npv_10 * geological_chance_of_success) - (capex_estimate * (1 - geological_chance_of_success))

    # ── Paradox ──
    paradox_score = 0.8 if (emv < 0 or capex_estimate > 1_000_000_000) else 0.2

    # ── Downstream cost impact (phase 2 — reserved) ──
    downstream_cost_impact = 0.0
    if downstream_margin_usd:
        # When refinery margins compress, development cost rises
        refinery_stress = max(0.0, (REFINERY_MARGIN_DANGER - downstream_margin_usd) / REFINERY_MARGIN_DANGER)
        downstream_cost_impact = capex_estimate * refinery_stress * 0.05

    # WEALTH does not Seal; it only qualifies. arifOS holds the final Seal.
    hold_triggered = (
        hedge_drag > HEDGE_DRAG_THRESHOLD
        or emv < 0
        or paradox_score >= 0.5
    )
    verdict = "888-HOLD" if hold_triggered else "QUALIFY"

    return ProspectEconomics(
        prospect_id=prospect_id,
        stoiip_bbl=stoiip_bbl,
        development_capex=capex_estimate,
        operating_opex=total_opex_rm,
        oil_price_assumption=oil_price,
        effective_price=effective_price,
        hedge_drag=hedge_drag,
        fx_impact=fx_impact,
        decline_factor=decline_factor,
        downstream_cost_impact=downstream_cost_impact,
        npv_10=npv_10,
        emv=emv,
        paradox_score=paradox_score,
        verdict=verdict,
    )

# --- Domain 1: Stock Market Intelligence (WEALTH-Markets) ---

@mcp.tool()
@governed_tool
async def markets_analyze_ticker(ticker: str, depth: str = "standard") -> MarketAnalysis:
    """Analyze stock with F1-F13 governance."""
    return MarketAnalysis(
        ticker=ticker.upper(),
        sentiment=0.5,
        epistemic_tag="ESTIMATE",
        confidence_band=[0.03, 0.15],
        humility_on_projections=True,
        risk_assessment="LOW"
    )

@mcp.tool()
@governed_tool
async def markets_portfolio_stress_test(
    portfolio_id: str,
    holdings: List[str],
    scenarios: List[str]
) -> StressTestResult:
    """Run 888 HOLD-aware stress tests."""
    return StressTestResult(
        portfolio_id=portfolio_id,
        max_drawdown=-0.05,
        correlation_breakdown=False,
        liquidity_crisis=False,
        hold_triggered=False
    )

# --- Domain 2: Energy Crisis Monitor (WEALTH-Energy) ---

@mcp.tool()
@governed_tool
async def energy_crisis_assess(
    region: str,
    # ─── Oil price context (optional — multi-factor model) ───
    brent_price_usd: Optional[float] = None,
    domestic_production_pct: Optional[float] = None,
    rm_usd_rate: Optional[float] = None,
    refinery_margin_usd: Optional[float] = None,
) -> CrisisAssessment:
    """
    Assess energy crisis severity with F1-F13 constitutional floors.

    Multi-factor model (when params provided):
    - price_dignity: citizen affordability under oil price stress
    - energy_sovereignty: domestic production buffers global spikes
    - grid_integrity: refinery margin squeeze when crude spikes
    - transition_amanah: clean transition readiness
    - maruah: citizen dignity under energy stress

    888_HOLD trigger: price_dignity < 0.5 AND not Malaysia sovereign.

    Note: hedge_drag belongs in wealth_evaluate_prospect (investment context),
    not here (sovereignty/affordability context). Kept separate per domain scope.
    """
    _is_malaysia = region.upper() == "MALAYSIA"

    if brent_price_usd is not None and domestic_production_pct is not None:
        price_burden = 1.0 - domestic_production_pct
        price_dignity = max(0.3, 1.0 - (brent_price_usd / BRENT_BENCHMARK) * price_burden)
        energy_sovereignty = min(1.0, domestic_production_pct + (1.0 - price_burden) * 0.3)

        # Bug 2 fix: refinery_stress must default to 0.0 when None (was NameError)
        refinery_stress = max(0.0, (REFINERY_MARGIN_DANGER - refinery_margin_usd) / REFINERY_MARGIN_DANGER) \
            if refinery_margin_usd else 0.0
        grid_integrity = max(0.5, 0.9 - refinery_stress * 0.4)

        # FX amplifier: RM weakens when USD strengthens (oil up → USD up → RM up)
        if rm_usd_rate:
            fx_amplifier = rm_usd_rate / 4.5
            normalized_revenue = (brent_price_usd / 75.0) * fx_amplifier
        else:
            normalized_revenue = brent_price_usd / 75.0

        maruah_score = price_dignity * energy_sovereignty * (1.0 - refinery_stress)

        # 888_HOLD: price dignity breach + non-sovereign → escalate
        hold_triggered = (price_dignity < 0.5 and not _is_malaysia)
    else:
        price_dignity = 0.7
        energy_sovereignty = 0.8
        grid_integrity = 0.9
        maruah_score = 0.73
        hold_triggered = False

    return CrisisAssessment(
        region=region.upper(),
        energy_sovereignty=energy_sovereignty,
        grid_integrity=grid_integrity,
        price_dignity=price_dignity,
        transition_amanah=0.5,
        maruah_score=maruah_score,
        hold_triggered=hold_triggered,
    )

@mcp.tool()
@governed_tool
async def energy_shortage_predict(
    region: str,
    horizon_days: int = 30
) -> ShortagePrediction:
    """Predict energy shortages with humility bands."""
    return ShortagePrediction(
        region=region.upper(),
        shortage_probability=0.1,
        uncertainty_band=0.05,
        horizon_days=horizon_days
    )

# --- Domain 3: Food Security Monitor (WEALTH-Food) ---

@mcp.tool()
@governed_tool
async def food_security_index(country: str) -> FoodSecurityIndex:
    """Calculate food security with Maruah adaptation."""
    return FoodSecurityIndex(
        country=country.upper(),
        availability=0.8,
        access=0.7,
        utilization=0.9,
        stability=0.8,
        index_score=0.8
    )

# --- Resources ---

@mcp.resource("market://{ticker}/fundamentals")
def get_fundamentals(ticker: str) -> str:
    """Real-time fundamentals with epistemic tags"""
    return f"Fundamentals for {ticker.upper()}: [CLAIM] Verified"

@mcp.resource("energy://{region}/realtime-mix")
def get_energy_mix(region: str) -> str:
    """Real-time energy production by source"""
    return f"Energy mix for {region.upper()}: 30% Renewable [CLAIM]"

@mcp.resource("food://global/prices")
def get_global_food_prices() -> str:
    """FAO food price index components"""
    return "Global food price index: 120.5 [ESTIMATE]"

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8082)
