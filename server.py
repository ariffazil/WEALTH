import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

__version__ = "1.3.1"
"""WEALTH v1.3.1 - native Python MCP surface for the hardened finance kernel."""

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

    class FastMCP:  # type: ignore[override]
        def __init__(self, *_args, **_kwargs):
            pass

        def tool(self, name: Optional[str] = None):
            def decorator(func):
                return func
            return decorator

        def resource(self, _uri: str):
            def decorator(func):
                return func
            return decorator

        def run(self):
            raise RuntimeError("fastmcp is not installed; import and call the WEALTH functions directly or install FastMCP to serve MCP.")

mcp = FastMCP("WEALTH Valuation Kernel")

EPSILON = 1e-9
INVALID_FLAGS = {
    "INVALID_INITIAL_INVESTMENT",
    "INVALID_CASHFLOW_SERIES",
    "INVALID_DISCOUNT_RATE",
    "INVALID_FINANCE_RATE",
    "INVALID_REINVESTMENT_RATE",
    "INVALID_SCENARIOS",
    "INVALID_SCENARIO",
    "PROBABILITY_MASS_INVALID",
    "INVALID_DEBT_SERVICE",
    "INVALID_CFADS",
    "INVALID_BASE_RATE",
}
HOLD_FLAGS = {"LEVERAGE_CRITICAL", "LEVERAGE_DEFAULT", "SOVEREIGN_DIGNITY_LOW"}
HOLD_FLAGS.add("MULTIPLE_IRR_POSSIBLE")
QUALIFY_FLAGS = {"NON_NORMAL_FLOWS", "IRR_NOT_FOUND", "NOT_RECOVERED", "EBITDA_PROXY_USED"}
EPISTEMIC_ORDER = ["UNKNOWN", "HYPOTHESIS", "ESTIMATE", "PLAUSIBLE", "CLAIM"]
RELIABILITY_TO_TAG = {
    "guaranteed": "CLAIM",
    "regular": "PLAUSIBLE",
    "irregular": "ESTIMATE",
    "speculative": "HYPOTHESIS",
}


def round_value(value: Optional[float], digits: int = 6) -> Optional[float]:
    if value is None or not math.isfinite(value):
        return value
    return round(value, digits)


def count_sign_changes(values: List[float]) -> int:
    previous_sign = 0
    changes = 0
    for value in values:
        if not math.isfinite(value) or abs(value) <= EPSILON:
            continue
        sign = 1 if value > 0 else -1
        if previous_sign != 0 and sign != previous_sign:
            changes += 1
        previous_sign = sign
    return changes


def build_cashflow_series(initial_investment: float, cash_flows: List[float], terminal_value: float = 0) -> List[float]:
    series = [-abs(initial_investment), *cash_flows]
    if terminal_value and len(series) > 1:
        series[-1] += terminal_value
    return series


def derive_confidence_band(value: Optional[float], epistemic: str = "CLAIM", mode: str = "relative") -> Optional[List[float]]:
    if value is None or not math.isfinite(value):
        return None
    upper_epistemic = str(epistemic).upper()
    relative_width = 0.25 if upper_epistemic == "HYPOTHESIS" else 0.15 if upper_epistemic == "ESTIMATE" else 0.08 if upper_epistemic == "PLAUSIBLE" else 0
    if relative_width == 0:
        return None
    if mode == "absolute-nonnegative":
        delta = max(0.05, abs(value) * relative_width)
        return [round_value(max(0.0, value - delta), 6), round_value(value + delta, 6)]
    return [round_value(value * (1 - relative_width), 6), round_value(value * (1 + relative_width), 6)]


def npv_from_series(cashflow_series: List[float], discount_rate: float) -> float:
    total = 0.0
    for index, cashflow in enumerate(cashflow_series):
        if index == 0:
            total += cashflow
        else:
            total += cashflow / pow(1 + discount_rate, index)
    return total


def present_value_breakdown(cashflow_series: List[float], discount_rate: float) -> Dict[str, Any]:
    discounted = []
    for index, cashflow in enumerate(cashflow_series):
        if index == 0:
            discounted.append(cashflow)
        else:
            discounted.append(cashflow / pow(1 + discount_rate, index))

    pv_inflows = sum(value for value in discounted if value > 0)
    pv_outflows = sum(abs(value) for value in discounted if value < 0)
    return {
        "discounted_cashflows": [round_value(value, 6) for value in discounted],
        "pv_inflows": round_value(pv_inflows, 6),
        "pv_outflows": round_value(pv_outflows, 6),
    }


def validate_series(initial_investment: float, cash_flows: List[float]) -> List[str]:
    flags: List[str] = []
    if not math.isfinite(initial_investment) or initial_investment == 0:
        flags.append("INVALID_INITIAL_INVESTMENT")
    if not isinstance(cash_flows, list) or len(cash_flows) == 0 or any(not math.isfinite(value) for value in cash_flows):
        flags.append("INVALID_CASHFLOW_SERIES")
    return flags


def validate_rate(rate: float, invalid_flag: str) -> List[str]:
    if not math.isfinite(rate) or rate <= -1:
        return [invalid_flag]
    return []


def weakest_epistemic(items: List[dict], default_tag: str = "CLAIM") -> str:
    if not items:
        return default_tag
    weakest_index = len(EPISTEMIC_ORDER) - 1
    for item in items:
        reliability = str(item.get("reliability", "")).lower()
        candidate = str(item.get("tag") or item.get("epistemic") or RELIABILITY_TO_TAG.get(reliability, default_tag)).upper()
        if candidate in EPISTEMIC_ORDER:
            weakest_index = min(weakest_index, EPISTEMIC_ORDER.index(candidate))
    return EPISTEMIC_ORDER[weakest_index]


def derive_verdict(flags: List[str], default_verdict: str = "SEAL") -> str:
    if any(flag in INVALID_FLAGS for flag in flags):
        return "VOID"
    if any(flag in HOLD_FLAGS for flag in flags):
        return "888-HOLD"
    if any(flag in QUALIFY_FLAGS for flag in flags):
        return "QUALIFY"
    return default_verdict


def infer_epistemic(flags: List[str], default_epistemic: str = "CLAIM") -> str:
    if any(flag in INVALID_FLAGS for flag in flags):
        return "UNKNOWN"
    if any((flag in HOLD_FLAGS) or (flag in QUALIFY_FLAGS) for flag in flags):
        return "ESTIMATE"
    return default_epistemic


def confidence_from_verdict(verdict: str, flags: List[str]) -> str:
    if verdict in {"VOID", "888-HOLD"}:
        return "LOW"
    if verdict == "QUALIFY" or flags:
        return "MEDIUM"
    return "HIGH"


def create_envelope(
    tool: str,
    dimension: str,
    primary: Dict[str, Any],
    secondary: Optional[Dict[str, Any]] = None,
    flags: Optional[List[str]] = None,
    assumptions: Optional[List[str]] = None,
    epistemic: str = "CLAIM",
    verdict: Optional[str] = None,
) -> Dict[str, Any]:
    flags = flags or []
    derived_verdict = verdict or derive_verdict(flags)
    derived_epistemic = infer_epistemic(flags, epistemic)
    return {
        "tool": tool,
        "dimension": dimension,
        "verdict": derived_verdict,
        "primary_result": primary,
        "secondary_metrics": secondary or {},
        "integrity_flags": flags,
        "confidence": confidence_from_verdict(derived_verdict, flags),
        "epistemic": derived_epistemic,
        "assumptions": assumptions or [],
        "epoch": datetime.utcnow().isoformat() + "Z",
    }


def measurement_npv(initial_investment: float, cash_flows: List[float], discount_rate: float, terminal_value: float = 0, period_unit: str = "annual", input_epistemic: str = "CLAIM") -> Dict[str, Any]:
    flags = [*validate_series(initial_investment, cash_flows), *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE")]
    assumptions = [
        "NPV is the primary accept/reject metric.",
        "Discount rate and cash flow periodicity are aligned.",
    ]
    if flags:
        return {
            "npv": None,
            "eaa": None,
            "pv_inflows": None,
            "pv_outflows": None,
            "discounted_cashflows": [],
            "period_count": len(cash_flows) if isinstance(cash_flows, list) else 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    series = build_cashflow_series(initial_investment, cash_flows, terminal_value)
    breakdown = present_value_breakdown(series, discount_rate)
    npv = npv_from_series(series, discount_rate)
    periods = len(cash_flows)
    if periods == 0:
        eaa = None
    elif abs(discount_rate) <= EPSILON:
        eaa = npv / periods
    else:
        eaa = (npv * discount_rate) / (1 - pow(1 + discount_rate, -periods))
    return {
        "npv": round_value(npv, 6),
        "eaa": round_value(eaa, 6),
        "pv_inflows": breakdown["pv_inflows"],
        "pv_outflows": breakdown["pv_outflows"],
        "discounted_cashflows": breakdown["discounted_cashflows"],
        "period_count": periods,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "input_epistemic": str(input_epistemic).upper(),
        "confidence_band": derive_confidence_band(npv, input_epistemic),
        "flags": flags,
    }


def bracket_roots(npv_fn, lower: float = -0.9999, upper: float = 10.0, steps: int = 4096) -> List[List[float]]:
    brackets: List[List[float]] = []
    step = (upper - lower) / steps
    previous_rate = lower
    previous_value = npv_fn(previous_rate)
    for index in range(1, steps + 1):
        rate = lower + step * index
        value = npv_fn(rate)
        if not math.isfinite(previous_value) or not math.isfinite(value):
            previous_rate = rate
            previous_value = value
            continue
        if abs(previous_value) <= EPSILON:
            brackets.append([previous_rate, previous_rate])
        elif previous_value * value < 0:
            brackets.append([previous_rate, rate])
        elif abs(value) <= EPSILON:
            brackets.append([rate, rate])
        previous_rate = rate
        previous_value = value
    return brackets


def bisect_root(npv_fn, lower: float, upper: float, iterations: int = 200) -> float:
    if lower == upper:
        return lower
    left = lower
    right = upper
    left_value = npv_fn(left)
    for _ in range(iterations):
        midpoint = (left + right) / 2
        midpoint_value = npv_fn(midpoint)
        if not math.isfinite(midpoint_value):
            break
        if abs(midpoint_value) <= EPSILON:
            return midpoint
        if left_value * midpoint_value <= 0:
            right = midpoint
        else:
            left = midpoint
            left_value = midpoint_value
        if abs(right - left) <= EPSILON:
            return (left + right) / 2
    return (left + right) / 2


def measurement_irr(initial_investment: float, cash_flows: List[float], finance_rate: float = 0.1, reinvestment_rate: float = 0.1, period_unit: str = "annual") -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(finance_rate, "INVALID_FINANCE_RATE"),
        *validate_rate(reinvestment_rate, "INVALID_REINVESTMENT_RATE"),
    ]
    assumptions = [
        "NPV remains the primary ranking metric for mutually exclusive projects.",
        "MIRR is preferred when reinvestment should not equal IRR.",
    ]
    if flags:
        return {
            "irr": None,
            "mirr": None,
            "sign_changes": 0,
            "period_count": len(cash_flows) if isinstance(cash_flows, list) else 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    series = build_cashflow_series(initial_investment, cash_flows)
    sign_changes = count_sign_changes(series)
    if sign_changes > 1:
        flags.extend(["NON_NORMAL_FLOWS", "MULTIPLE_IRR_POSSIBLE"])

    npv_fn = lambda rate: npv_from_series(series, rate)
    brackets = bracket_roots(npv_fn)
    roots = {round_value(bisect_root(npv_fn, lower, upper), 10) for lower, upper in brackets}
    irr = next(iter(roots)) if len(roots) == 1 else None
    if len(roots) == 0:
        flags.append("IRR_NOT_FOUND")

    period_count = len(series) - 1
    pv_negative = 0.0
    fv_positive = 0.0
    for index, cashflow in enumerate(series):
        if cashflow < 0:
            pv_negative += cashflow / pow(1 + finance_rate, index)
        elif cashflow > 0:
            fv_positive += cashflow * pow(1 + reinvestment_rate, period_count - index)
    mirr = None
    if pv_negative < 0 and fv_positive > 0 and period_count > 0:
        mirr = pow(fv_positive / abs(pv_negative), 1 / period_count) - 1

    return {
        "irr": round_value(irr, 8) if irr is not None else None,
        "mirr": round_value(mirr, 8) if mirr is not None else None,
        "sign_changes": sign_changes,
        "period_count": period_count,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_pi(initial_investment: float, cash_flows: List[float], discount_rate: float, terminal_value: float = 0) -> Dict[str, Any]:
    npv_measure = measurement_npv(initial_investment, cash_flows, discount_rate, terminal_value)
    flags = list(npv_measure["flags"])
    if count_sign_changes(build_cashflow_series(initial_investment, cash_flows, terminal_value)) > 1:
        flags.append("NON_NORMAL_FLOWS")
    pi = None if npv_measure["pv_inflows"] is None else npv_measure["pv_inflows"] / abs(initial_investment)
    return {
        "pi": round_value(pi, 8) if pi is not None else None,
        "pv_inflows": npv_measure["pv_inflows"],
        "assumptions": [
            "Profitability Index is for ranking under capital rationing.",
            "PI does not override NPV for mutually exclusive decisions.",
        ],
        "flags": flags,
    }


def measurement_emv(scenarios: List[dict]) -> Dict[str, Any]:
    flags: List[str] = []
    assumptions = [
        "EMV should be paired with downside probability and scenario dispersion.",
        "Scenario probabilities should sum to 1.0.",
    ]
    if not isinstance(scenarios, list) or not scenarios:
        flags.append("INVALID_SCENARIOS")
        return {
            "emv": None,
            "total_probability": None,
            "downside_probability": None,
            "worst_outcome": None,
            "best_outcome": None,
            "variance": None,
            "assumptions": assumptions,
            "flags": flags,
        }

    for scenario in scenarios:
        if scenario is None or not math.isfinite(scenario.get("probability")) or not math.isfinite(scenario.get("outcome")):
            flags.append("INVALID_SCENARIO")
            return {
                "emv": None,
                "total_probability": None,
                "downside_probability": None,
                "worst_outcome": None,
                "best_outcome": None,
                "variance": None,
                "assumptions": assumptions,
                "flags": flags,
            }

    total_probability = sum(scenario["probability"] for scenario in scenarios)
    if abs(total_probability - 1.0) > 1e-6:
        flags.append("PROBABILITY_MASS_INVALID")

    emv = sum(scenario["probability"] * scenario["outcome"] for scenario in scenarios)
    downside_probability = sum(scenario["probability"] for scenario in scenarios if scenario["outcome"] < 0)
    variance = sum(scenario["probability"] * pow(scenario["outcome"] - emv, 2) for scenario in scenarios)
    return {
        "emv": round_value(emv, 6),
        "total_probability": round_value(total_probability, 6),
        "downside_probability": round_value(downside_probability, 6),
        "worst_outcome": round_value(min(scenario["outcome"] for scenario in scenarios), 6),
        "best_outcome": round_value(max(scenario["outcome"] for scenario in scenarios), 6),
        "variance": round_value(variance, 6),
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_payback(initial_investment: float, cash_flows: List[float], discount_rate: float = 0, period_unit: str = "annual") -> Dict[str, Any]:
    flags = [*validate_series(initial_investment, cash_flows), *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE")]
    assumptions = ["Payback should only support, not replace, NPV."]
    if flags:
        return {
            "payback_periods": None,
            "discounted": discount_rate > 0,
            "period_unit": period_unit,
            "assumptions": assumptions,
            "flags": flags,
        }

    remaining = abs(initial_investment)
    payback_periods = None
    for index, raw_cashflow in enumerate(cash_flows):
        adjusted_cashflow = raw_cashflow / pow(1 + discount_rate, index + 1) if discount_rate > 0 else raw_cashflow
        if adjusted_cashflow <= 0:
            continue
        if remaining > adjusted_cashflow:
            remaining -= adjusted_cashflow
            continue
        payback_periods = index + (remaining / adjusted_cashflow) + 1e-12
        remaining = 0
        break
    if remaining > EPSILON:
        flags.append("NOT_RECOVERED")
    return {
        "payback_periods": round_value(payback_periods, 6) if payback_periods is not None else None,
        "discounted": discount_rate > 0,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_dscr(cfads: Optional[float], debt_service: Optional[float], ebitda: Optional[float], principal: float = 0, interest: float = 0, leases: float = 0, period_unit: str = "annual", input_epistemic: str = "CLAIM") -> Dict[str, Any]:
    flags: List[str] = []
    numerator = cfads if cfads is not None else ebitda
    denominator = debt_service if debt_service is not None else principal + interest + leases
    if numerator is None or not math.isfinite(numerator):
        flags.append("INVALID_CFADS")
    if denominator is None or not math.isfinite(denominator) or denominator <= 0:
        flags.append("INVALID_DEBT_SERVICE")
    if cfads is None and ebitda is not None:
        flags.append("EBITDA_PROXY_USED")

    dscr = None if any(flag in INVALID_FLAGS for flag in flags) else numerator / denominator
    if dscr is not None and dscr < 1.0:
        flags.append("LEVERAGE_DEFAULT")
    elif dscr is not None and dscr < 1.25:
        flags.append("LEVERAGE_CRITICAL")
    return {
        "dscr": round_value(dscr, 6) if dscr is not None else None,
        "basis": "CFADS" if cfads is not None else "EBITDA",
        "period_unit": period_unit,
        "assumptions": [
            "DSCR should use CFADS when available.",
            "Minimum covenant floor defaults to 1.25x.",
        ],
        "input_epistemic": str(input_epistemic).upper(),
        "confidence_band": None if dscr is None else derive_confidence_band(dscr, input_epistemic, "absolute-nonnegative"),
        "flags": flags,
    }


def capitalx(base_rate: float, signals: Dict[str, float]) -> Dict[str, Any]:
    flags: List[str] = []
    if not math.isfinite(base_rate) or base_rate < 0:
        flags.append("INVALID_BASE_RATE")

    d_s = signals.get("dS", 0.0)
    peace2 = signals.get("peace2", 1.0)
    maruah = signals.get("maruahScore", 0.5)
    trust = signals.get("trustIndex", 0.5)
    delta_civ = signals.get("deltaCiv", 0.0)

    entropy_penalty = max(0.0, d_s * 0.5)
    peace_discount = min(0.02, max(0.0, (peace2 - 1.0) * 0.05))
    maruah_discount = min(0.03, max(0.0, (maruah - 0.5) * 0.06))
    trust_discount = min(0.02, max(0.0, (trust - 0.5) * 0.04))
    civ_discount = min(0.02, max(0.0, delta_civ * 0.10))

    r_adj = max(0.0, round_value(base_rate + entropy_penalty - peace_discount - maruah_discount - trust_discount - civ_discount, 6) or 0.0)
    if d_s > 0.3:
        flags.append("HIGH_ENTROPY_SIGNAL")
    if maruah < 0.6:
        flags.append("SOVEREIGN_DIGNITY_LOW")

    uncertainty_radius = round_value(0.01 + d_s * 0.02, 6) or 0.01
    return {
        "base_rate": round_value(base_rate, 6),
        "adjusted_rate": r_adj,
        "r_adj": r_adj,
        "adjustments": {
            "entropy_penalty": round_value(entropy_penalty, 6),
            "peace_discount": round_value(peace_discount, 6),
            "maruah_discount": round_value(maruah_discount, 6),
            "trust_discount": round_value(trust_discount, 6),
            "civ_discount": round_value(civ_discount, 6),
        },
        "uncertainty_band": [max(0.0, round_value(r_adj - uncertainty_radius, 6) or 0.0), round_value(r_adj + uncertainty_radius, 6)],
        "integrity_flags": flags,
        "assumptions": [
            "CapitalX pricing is an estimate layered on top of the base rate.",
            "If entropy rises, r_adj must not decrease.",
        ],
    }


@mcp.tool(name="wealth_npv_reward")
def npv_reward(initial_investment: float, cash_flows: List[float], discount_rate: float, terminal_value: float = 0, period_unit: str = "annual", input_epistemic: str = "CLAIM") -> Any:
    """Compute NPV, Terminal Value, and EAA. [Reward Dimension]"""
    measurement = measurement_npv(initial_investment, cash_flows, discount_rate, terminal_value, period_unit, input_epistemic)
    return create_envelope(
        "wealth_npv_reward",
        "Reward",
        {"npv": measurement["npv"]},
        {
            "eaa": measurement["eaa"],
            "pv_inflows": measurement["pv_inflows"],
            "pv_outflows": measurement["pv_outflows"],
            "period_count": measurement["period_count"],
            "period_unit": measurement["period_unit"],
            "confidence_band": measurement["confidence_band"],
        },
        measurement["flags"],
        measurement["assumptions"],
    )


@mcp.tool(name="wealth_irr_yield")
def irr_yield(initial_investment: float, cash_flows: List[float], reinvestment_rate: float = 0.1, finance_rate: float = 0.1, period_unit: str = "annual") -> Any:
    """Compute IRR and MIRR (Potential). [Energy Dimension]"""
    measurement = measurement_irr(initial_investment, cash_flows, finance_rate, reinvestment_rate, period_unit)
    return create_envelope(
        "wealth_irr_yield",
        "Energy",
        {"irr": measurement["irr"]},
        {
            "mirr": measurement["mirr"],
            "sign_changes": measurement["sign_changes"],
            "period_count": measurement["period_count"],
            "period_unit": measurement["period_unit"],
        },
        measurement["flags"],
        measurement["assumptions"],
    )


@mcp.tool(name="wealth_pi_efficiency")
def pi_efficiency(initial_investment: float, cash_flows: List[float], discount_rate: float) -> Any:
    """Compute Profitability Index (Concentration). [Energy Dimension]"""
    measurement = measurement_pi(initial_investment, cash_flows, discount_rate)
    ranking_signal = "EFFICIENT" if measurement["pi"] is not None and measurement["pi"] >= 1 else "EXTRACTIVE"
    return create_envelope(
        "wealth_pi_efficiency",
        "Energy",
        {"pi": measurement["pi"]},
        {"ranking_signal": ranking_signal},
        measurement["flags"],
        measurement["assumptions"],
    )


@mcp.tool(name="wealth_emv_risk")
def emv_risk(scenarios: List[dict]) -> Any:
    """Compute Expected Monetary Value (Probability Density). [Entropy Dimension]"""
    measurement = measurement_emv(scenarios)
    return create_envelope(
        "wealth_emv_risk",
        "Entropy",
        {"emv": measurement["emv"]},
        {
            "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
            "total_probability": measurement["total_probability"],
            "downside_probability": measurement["downside_probability"],
            "variance": measurement["variance"],
            "worst_outcome": measurement["worst_outcome"],
            "best_outcome": measurement["best_outcome"],
        },
        measurement["flags"],
        measurement["assumptions"],
        epistemic="ESTIMATE",
    )


@mcp.tool(name="wealth_audit_entropy")
def audit_entropy(initial_investment: float, cash_flows: List[float], discount_rate: float = 0.1) -> Any:
    """Audit project cash flows for noise and multiple IRRs. [Entropy Dimension]"""
    irr_measure = measurement_irr(initial_investment, cash_flows, discount_rate, discount_rate)
    sensitivity = []
    for multiplier in [0.8, 0.9, 1.0, 1.1, 1.2]:
        npv_measure = measurement_npv(initial_investment, cash_flows, discount_rate * multiplier)
        sensitivity.append({"multiplier": multiplier, "npv": npv_measure["npv"]})
    return create_envelope(
        "wealth_audit_entropy",
        "Entropy",
        {"sign_changes": irr_measure["sign_changes"]},
        {"sensitivity_sweep": sensitivity},
        irr_measure["flags"],
        irr_measure["assumptions"],
        epistemic="ESTIMATE",
    )


@mcp.tool(name="wealth_dscr_leverage")
def dscr_leverage(ebitda: Optional[float] = None, principal: float = 0, interest: float = 0, leases: float = 0, cfads: Optional[float] = None, debt_service: Optional[float] = None, period_unit: str = "annual", input_epistemic: str = "CLAIM") -> Any:
    """Compute Debt Service Coverage Ratio (Structural Load). [Survival Dimension]"""
    measurement = measurement_dscr(cfads, debt_service, ebitda, principal, interest, leases, period_unit, input_epistemic)
    return create_envelope(
        "wealth_dscr_leverage",
        "Survival",
        {"dscr": measurement["dscr"]},
        {"basis": measurement["basis"], "period_unit": measurement["period_unit"], "confidence_band": measurement["confidence_band"]},
        measurement["flags"],
        measurement["assumptions"],
    )


@mcp.tool(name="wealth_payback_time")
def payback_time(initial_investment: float, cash_flows: List[float], discount_rate: float = 0, period_unit: str = "annual") -> Any:
    """Compute Payback Period (Recovery Velocity). [Time Dimension]"""
    measurement = measurement_payback(initial_investment, cash_flows, discount_rate, period_unit)
    return create_envelope(
        "wealth_payback_time",
        "Time",
        {"payback_periods": measurement["payback_periods"]},
        {"period_unit": measurement["period_unit"], "discounted": measurement["discounted"]},
        measurement["flags"],
        measurement["assumptions"],
    )


@mcp.tool(name="wealth_growth_velocity")
def growth_velocity(principal: float, rate: float, years: int, annual_contribution: float = 0, monthly_burn: float = 0) -> Any:
    """Compute Compound Growth and Runway. [Velocity Dimension]"""
    total = principal
    for _ in range(years):
        total = total * (1 + rate) + annual_contribution
    final_value = round_value(total, 2)
    low = round_value(final_value * 0.88, 2)
    high = round_value(final_value * 1.12, 2)
    net_monthly = -monthly_burn
    runway_months = math.inf if monthly_burn <= 0 else round_value(principal / monthly_burn, 1)
    flags = ["RUNWAY_CRITICAL"] if monthly_burn > 0 and runway_months is not None and runway_months < 3 else []
    return create_envelope(
        "wealth_growth_velocity",
        "Velocity",
        {"growth_forecast": {"low": low, "mid": final_value, "high": high}},
        {"runway_months": runway_months, "final_value": final_value, "net_monthly": net_monthly},
        flags,
        ["Forward projections remain ESTIMATE by design."],
        epistemic="ESTIMATE",
    )


@mcp.tool(name="wealth_networth_state")
def networth_state(assets: Optional[List[dict]] = None, liabilities: Optional[List[dict]] = None) -> Any:
    """Compute portfolio balance sheet (Accumulated Mass). [Mass Dimension]"""
    assets = assets or []
    liabilities = liabilities or []
    asset_value = sum(asset.get("value", 0) for asset in assets if math.isfinite(asset.get("value", 0)))
    liability_value = sum(liability.get("outstanding", liability.get("principal", 0)) for liability in liabilities if math.isfinite(liability.get("outstanding", liability.get("principal", 0))))
    epistemic = weakest_epistemic([*assets, *liabilities])
    return create_envelope(
        "wealth_networth_state",
        "Mass",
        {
            "net_worth": round_value(asset_value - liability_value, 2),
            "assets": round_value(asset_value, 2),
            "liabilities": round_value(liability_value, 2),
            "tag": epistemic,
        },
        {},
        [],
        [],
        epistemic=epistemic,
    )


@mcp.tool(name="wealth_cashflow_flow")
def cashflow_flow(income: Optional[List[dict]] = None, expenses: Optional[List[dict]] = None, liquid_assets: float = 0) -> Any:
    """Compute metabolic liquidity (Flow Dimension). [Flow Dimension]"""
    income = [item for item in (income or []) if item.get("active", True)]
    expenses = [item for item in (expenses or []) if item.get("active", True)]
    total_income = sum(item.get("monthly_amount", 0) for item in income if math.isfinite(item.get("monthly_amount", 0)))
    total_expenses = sum(item.get("monthly_amount", 0) for item in expenses if math.isfinite(item.get("monthly_amount", 0)))
    net_monthly = total_income - total_expenses
    burn_rate = max(0.0, -net_monthly)
    runway_months = math.inf if burn_rate == 0 else round_value(liquid_assets / burn_rate, 1)
    flags = ["RUNWAY_CRITICAL"] if burn_rate > 0 and runway_months is not None and runway_months < 3 else []
    epistemic = weakest_epistemic([*income, *expenses], "UNKNOWN")
    return create_envelope(
        "wealth_cashflow_flow",
        "Flow",
        {
            "monthly_income": round_value(total_income, 2),
            "monthly_expenses": round_value(total_expenses, 2),
            "net_monthly": round_value(net_monthly, 2),
            "runway_months": runway_months,
            "burn_rate": round_value(burn_rate, 2),
            "tag": epistemic,
        },
        {"period_unit": "monthly"},
        flags,
        [],
        epistemic=epistemic,
    )


@mcp.tool(name="wealth_score_kernel")
def score_kernel(base_rate: float, dS: float, peace2: float, maruahScore: float, trustIndex: float = 0.5, deltaCiv: float = 0.0, compare: bool = False, wealth_signals: Optional[dict] = None, extractive_signals: Optional[dict] = None) -> Any:
    """Final Sovereign Allocation Verdict. [Allocation Dimension]"""
    wealth_payload = {"dS": dS, "peace2": peace2, "maruahScore": maruahScore, "trustIndex": trustIndex, "deltaCiv": deltaCiv}
    if wealth_signals:
        wealth_payload.update(wealth_signals)

    flags: List[str] = []
    if dS > 0.3:
        flags.append("HIGH_ENTROPY_SIGNAL")
    if maruahScore < 0.6:
        flags.append("SOVEREIGN_DIGNITY_LOW")

    wealth_result = capitalx(base_rate, wealth_payload)
    if compare:
        extractive_result = capitalx(base_rate, extractive_signals or {})
        comparison = {
            "base_rate": wealth_result["base_rate"],
            "wealth_r_adj": wealth_result["r_adj"],
            "extractive_r_adj": extractive_result["r_adj"],
            "advantage_bps": round((extractive_result["r_adj"] - wealth_result["r_adj"]) * 10000),
        }
        return create_envelope(
            "wealth_score_kernel",
            "Allocation",
            comparison,
            {},
            [*flags, *(wealth_result["integrity_flags"]), *(extractive_result["integrity_flags"])],
            ["CapitalX remains an estimate until delta_bps is proven."],
            epistemic="ESTIMATE",
        )

    return create_envelope(
        "wealth_score_kernel",
        "Allocation",
        wealth_result,
        {},
        [*flags, *(wealth_result["integrity_flags"])],
        wealth_result["assumptions"],
        epistemic="ESTIMATE",
    )


@mcp.resource("wealth://doctrine/valuation")
def get_valuation_doctrine() -> str:
    return json.dumps({
        "motto": "Physics > Narrative",
        "principles": [
            "F1: Absolute Value (NPV) is the primary anchor.",
            "F2: Reinvestment risk must be modeled via MIRR.",
            "F3: Time-Value is a physical decay function.",
            "F4: Leverage must never break the DSCR floor (1.25x).",
            "F5: Mandatory governance signals (dS, peace2, maruah) for SEAL."
        ],
        "protocol": f"Dimensional Forge v{__version__}"
    }, indent=2)


@mcp.resource("wealth://dimensions/definitions")
def get_dimensional_definitions() -> str:
    return json.dumps({
        "Reward": "Total energy output (NPV, EAA).",
        "Energy": "Efficiency and potential (IRR, PI).",
        "Entropy": "Risk, noise, and probability (EMV, Audit).",
        "Time": "Recovery velocity (Payback).",
        "Mass": "Accumulated state (Net Worth).",
        "Flow": "Metabolic rate (Cash Flow).",
        "Velocity": "Rate of expansion (Growth).",
        "Survival": "Structural load capacity (DSCR).",
        "Allocation": "Sovereign decision kernel (Score)."
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
