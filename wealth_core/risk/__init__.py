"""
WEALTH Core — Risk Domain.

Pure risk computation engines extracted from monolith.
No MCP dependency, no I/O, pure computation.

Submodules:
- entropy: EMV, Monte Carlo, tail risk, asymmetry
- signal: EVOI, schema validation, information value
- correlation: Coupling, guard checks, false confluence

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
import random
from typing import Any


def compute_emv(
    outcomes: list[float],
    probabilities: list[float],
) -> dict:
    """
    Compute Expected Monetary Value with variance.
    """
    if len(outcomes) != len(probabilities):
        raise ValueError("outcomes and probabilities must have same length")

    expected = sum(o * p for o, p in zip(outcomes, probabilities))
    variance = sum(p * (o - expected) ** 2 for o, p in zip(outcomes, probabilities))
    std_dev = math.sqrt(variance)

    return {
        "emv": round(expected, 2),
        "variance": round(variance, 4),
        "std_dev": round(std_dev, 4),
        "outcome_count": len(outcomes),
    }


def monte_carlo_simulation(
    initial_value: float,
    growth_rate: float,
    volatility: float,
    periods: int = 10,
    simulations: int = 1000,
    seed: int | None = None,
) -> dict:
    """
    Run Monte Carlo simulation for value projection.

    Uses geometric Brownian motion: dS = S(μdt + σdW).
    Lognormal terminal value assumption.

    RSI-04 FIX (2026-06-25): Warns when volatility > 0.40 because
    lognormal distribution tails become extreme and the mean-variance
    approximation breaks down. P10/P90 spread grows exponentially with σ.
    """
    # RSI-04 FIX: lognormality warning thresholds
    if volatility > 0.60:
        lognormality_warning = (
            "CRITICAL: volatility > 0.60. Lognormal distribution is unreliable. "
            "P10/P90 spread is extreme. Consider scenario analysis instead."
        )
        tail_risk_underestimated = True
        distribution_reliable = False
    elif volatility > 0.40:
        lognormality_warning = (
            "WARNING: volatility > 0.40. Lognormal tail risk is underestimated "
            "by simple mean-variance framework. P10/P90 spread may be larger than "
            "model projects. Consider widening confidence intervals manually."
        )
        tail_risk_underestimated = True
        distribution_reliable = True  # Still usable but needs wider bands
    else:
        lognormality_warning = None
        tail_risk_underestimated = False
        distribution_reliable = True

    if seed is not None:
        random.seed(seed)

    terminal_values = []
    for _ in range(simulations):
        value = initial_value
        for _ in range(periods):
            shock = random.gauss(0, 1)
            value *= math.exp(
                (growth_rate - 0.5 * volatility**2) + volatility * shock
            )
        terminal_values.append(value)

    terminal_values.sort()
    n = len(terminal_values)

    result = {
        "p10": round(terminal_values[int(n * 0.10)], 2),
        "p25": round(terminal_values[int(n * 0.25)], 2),
        "p50": round(terminal_values[int(n * 0.50)], 2),
        "p75": round(terminal_values[int(n * 0.75)], 2),
        "p90": round(terminal_values[int(n * 0.90)], 2),
        "mean": round(sum(terminal_values) / n, 2),
        "simulations": simulations,
        "periods": periods,
        # RSI-04 FIX fields
        "volatility": volatility,
        "tail_risk_underestimated": tail_risk_underestimated,
        "distribution_reliable": distribution_reliable,
        "lognormality_warning": lognormality_warning,
    }

    # P10/P90 spread ratio — useful diagnostic for tail width
    if result["p10"] > 0:
        result["p90_p10_ratio"] = round(result["p90"] / result["p10"], 2)
    else:
        result["p90_p10_ratio"] = None

    return result


def compute_evoi(
    prior_pos: float,
    posterior_pos: float,
    well_cost_musd: float,
    p50_value_musd: float,
    discount_rate: float = 0.1,
) -> dict:
    """
    Compute Expected Value of Information (EVOI).
    """
    # EV with info
    ev_with_info = posterior_pos * p50_value_musd - well_cost_musd
    # EV without info (use prior)
    ev_without_info = prior_pos * p50_value_musd
    # EVOI
    evoi = ev_with_info - ev_without_info

    # Discount
    evoi_discounted = evoi / (1 + discount_rate)

    return {
        "evoi": round(evoi, 4),
        "evoi_discounted": round(evoi_discounted, 4),
        "prior_pos": prior_pos,
        "posterior_pos": posterior_pos,
        "well_cost_musd": well_cost_musd,
        "p50_value_musd": p50_value_musd,
        "worth_drilling": evoi > 0,
    }


def detect_false_confluence(
    indicators: list[dict],
) -> dict:
    """
    Detect false confluence — multiple indicators that look aligned
    but are actually measuring the same underlying signal.

    Each indicator: {name, signal_class, value}
    """
    # Group by signal class
    classes: dict[str, list] = {}
    for ind in indicators:
        cls = ind.get("signal_class", "unknown")
        classes.setdefault(cls, []).append(ind)

    # If >60% of indicators share the same class, flag false confluence
    total = len(indicators)
    max_class_count = max(len(v) for v in classes.values()) if classes else 0
    concentration = max_class_count / total if total > 0 else 0

    is_false = concentration > 0.6

    return {
        "is_false_confluence": is_false,
        "concentration": round(concentration, 3),
        "unique_classes": len(classes),
        "total_indicators": total,
        "dominant_class": max(classes, key=lambda k: len(classes[k])) if classes else None,
        "warning": (
            "FALSE CONFLUENCE: indicators are measuring the same signal"
            if is_false
            else "Indicators appear independent"
        ),
    }


def compute_asymmetry(
    upside_scenarios: list[float],
    downside_scenarios: list[float],
) -> dict:
    """
    Compute risk asymmetry — is the distribution skewed?
    """
    up_mean = sum(upside_scenarios) / len(upside_scenarios) if upside_scenarios else 0
    down_mean = sum(downside_scenarios) / len(downside_scenarios) if downside_scenarios else 0

    skew = up_mean + down_mean  # Net expectation
    ratio = abs(up_mean / down_mean) if down_mean != 0 else float("inf")

    return {
        "upside_mean": round(up_mean, 4),
        "downside_mean": round(down_mean, 4),
        "net_skew": round(skew, 4),
        "up_down_ratio": round(ratio, 4) if ratio != float("inf") else "infinite",
        "is_asymmetric": abs(ratio - 1.0) > 0.3,
        "favorable": skew > 0,
    }


def fiscal_breakeven_oil_price(
    total_government_expenditure: float,
    non_oil_revenue: float,
    petronas_dividend_base_rm: float,
    oil_price_assumption_usd: float,
    petronas_production_boe_per_day: float = 350_000,
    royalty_tax_effective_rate: float = 0.30,
    target_fiscal_deficit_pct: float = 0.035,
    gdp_nominal_rm_billion: float = 390.0,
) -> dict:
    """
    HARDENING 2026-06-25: Fiscal breakeven oil price for Malaysia/Petronas.

    Computes the oil price at which the fiscal path becomes unsustainable —
    i.e., the price at which non-oil revenue + sustainable Petronas contribution
    fails to cover government expenditure within the target deficit threshold.

    This answers what Monte Carlo cannot: a single threshold, not a distribution.

    Args:
        total_government_expenditure:  RM billion/year total govt spending
        non_oil_revenue:               RM billion/year revenue excluding oil
        petronas_dividend_base_rm:     RM billion — current Petronas dividend (2026: RM20B)
        oil_price_assumption_usd:      USD/bbl — current/reference price
        petronas_production_boe_per_day: boe/day (default: ~350k = Malaysia typical)
        royalty_tax_effective_rate:     fraction of oil revenue captured by government
        target_fiscal_deficit_pct:     target deficit as % of GDP (default 3.5%)
        gdp_nominal_rm_billion:        nominal GDP in RM billion (default 390 = 2025 approx)

    Returns dict with breakeven price and fiscal sensitivity analysis.
    """
    # Annual oil production (boe)
    annual_production_boe = petronas_production_boe_per_day * 365

    # Current fiscal deficit
    current_deficit = total_government_expenditure - non_oil_revenue - petronas_dividend_base_rm
    deficit_pct = current_deficit / gdp_nominal_rm_billion

    # Target maximum deficit (budget ceiling)
    target_deficit_rm = gdp_nominal_rm_billion * target_fiscal_deficit_pct

    # Additional oil revenue needed beyond current dividend to hit target deficit
    # If current deficit > target deficit: need more oil revenue
    additional_oil_revenue_needed = max(0.0, current_deficit - target_deficit_rm)

    # Government take per barrel = production × price × effective rate
    # Revenue per usd_per_bbl = annual_production × usd_per_bbl × rate
    government_take_per_usd = annual_production_boe * royalty_tax_effective_rate / 1e9  # RM B per USD

    # Breakeven: additional oil revenue needed / government take per USD
    breakeven_price_usd = (
        additional_oil_revenue_needed / government_take_per_usd
        if government_take_per_usd > 0
        else None
    )

    # Sensitivity: how much does fiscal position change per USD move?
    fiscal_sensitivity_rm_per_usd = government_take_per_usd  # RM B per USD/bbl

    # At current price: how much is Petronas contributing vs what's needed?
    current_oil_revenue = annual_production_boe * oil_price_assumption_usd * royalty_tax_effective_rate / 1e9

    # Pressure flag: if breakeven price > current price, fiscal path needs correction
    fiscal_pressure = (
        "UNSUSTAINABLE" if breakeven_price_usd and breakeven_price_usd > oil_price_assumption_usd
        else "MANAGEABLE" if breakeven_price_usd and breakeven_price_usd < oil_price_assumption_usd * 0.8
        else "AT_RISK"
    )

    return {
        "breakeven_price_usd": round(breakeven_price_usd, 1) if breakeven_price_usd else None,
        "current_oil_price_usd": oil_price_assumption_usd,
        "fiscal_pressure": fiscal_pressure,
        "current_deficit_rm_b": round(current_deficit, 1),
        "deficit_pct_of_gdp": round(deficit_pct * 100, 2),
        "target_deficit_pct": target_fiscal_deficit_pct * 100,
        "additional_oil_revenue_needed_rm_b": round(additional_oil_revenue_needed, 1),
        "fiscal_sensitivity_rm_b_per_usd": round(fiscal_sensitivity_rm_per_usd, 3),
        "petronas_dividend_base_rm_b": petronas_dividend_base_rm,
        "non_oil_revenue_rm_b": non_oil_revenue,
        "total_govt_expenditure_rm_b": total_government_expenditure,
        "epistemic_tag": "CLAIM",
        "confidence_band": 0.70,
        "caveat": (
            "Breakeven price assumes constant production and no reserve depletion. "
            "In crisis (USD 50-), production also declines, worsening the fiscal gap. "
            "Real breakeven is higher than calculated under tail scenarios."
        ),
    }


__all__ = [
    "compute_emv",
    "monte_carlo_simulation",
    "compute_evoi",
    "detect_false_confluence",
    "compute_asymmetry",
    "fiscal_breakeven_oil_price",
]
