import json
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

__version__ = "1.5.0"
"""WEALTH v1.5.0 - Universal Resource Allocation Intelligence (URAI) with Constitutional Governance."""

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
            raise RuntimeError(
                "fastmcp is not installed; import and call the WEALTH functions directly or install FastMCP to serve MCP."
            )


try:
    from host.governance.floors import check_floors, maruah_band
    from host.governance.policy_engine import PolicyEngine
    from host.governance.vault import append_vault999

    GOVERNANCE_AVAILABLE = True
except Exception:
    GOVERNANCE_AVAILABLE = False

try:
    from host.coordination.lp_allocator import allocate as lp_allocate
    from host.coordination.cooperative import shapley_values, core_feasibility
    from host.coordination.strategic import nash_approximation
    from host.coordination.commons import commons_risk

    COORDINATION_AVAILABLE = True
except Exception:
    COORDINATION_AVAILABLE = False

    def lp_allocate(*_args, **_kwargs):  # type: ignore
        return {"feasible": False, "flags": ["COORDINATION_UNAVAILABLE"]}

    def shapley_values(*_args, **_kwargs):  # type: ignore
        return {
            "shapley": {},
            "total_value": 0.0,
            "flags": ["COORDINATION_UNAVAILABLE"],
        }

    def core_feasibility(*_args, **_kwargs):  # type: ignore
        return {
            "in_core": False,
            "blocking_coalitions": [],
            "flags": ["COORDINATION_UNAVAILABLE"],
        }

    def nash_approximation(*_args, **_kwargs):  # type: ignore
        return {
            "equilibrium": {},
            "converged": False,
            "flags": ["COORDINATION_UNAVAILABLE"],
        }

    def commons_risk(*_args, **_kwargs):  # type: ignore
        return {
            "tragedy_risk": 1.0,
            "scarcity_index": {},
            "flags": ["COORDINATION_UNAVAILABLE"],
        }

    def check_floors(*_args, **_kwargs):  # type: ignore
        return {
            "pass": True,
            "verdict": "SEAL",
            "violations": [],
            "holds": [],
            "warnings": [],
        }

    def maruah_band(score):  # type: ignore
        return (
            "SOVEREIGN"
            if score >= 0.85
            else "STABLE"
            if score >= 0.70
            else "FLOOR"
            if score >= 0.60
            else "AMBER"
            if score >= 0.40
            else "RED"
        )

    class PolicyEngine:  # type: ignore
        def __init__(self, *_args, **_kwargs):
            pass

        def evaluate(self, *_args, **_kwargs):
            return {
                "policy_pass": True,
                "flags": [],
                "details": {},
                "constraints_applied": [],
                "scale_mode": "enterprise",
            }

        def evaluate_envelope(self, *_args, **_kwargs):
            return {
                "policy_pass": True,
                "flags": [],
                "details": {},
                "constraints_applied": [],
                "scale_mode": "enterprise",
            }

    def append_vault999(record, **_kwargs):  # type: ignore
        return record


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
QUALIFY_FLAGS = {
    "NON_NORMAL_FLOWS",
    "IRR_NOT_FOUND",
    "NOT_RECOVERED",
    "EBITDA_PROXY_USED",
}
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


def build_cashflow_series(
    initial_investment: float, cash_flows: List[float], terminal_value: float = 0
) -> List[float]:
    series = [-abs(initial_investment), *cash_flows]
    if terminal_value and len(series) > 1:
        series[-1] += terminal_value
    return series


def derive_confidence_band(
    value: Optional[float], epistemic: str = "CLAIM", mode: str = "relative"
) -> Optional[List[float]]:
    if value is None or not math.isfinite(value):
        return None
    upper_epistemic = str(epistemic).upper()
    relative_width = (
        0.25
        if upper_epistemic == "HYPOTHESIS"
        else 0.15
        if upper_epistemic == "ESTIMATE"
        else 0.08
        if upper_epistemic == "PLAUSIBLE"
        else 0
    )
    if relative_width == 0:
        return None
    if mode == "absolute-nonnegative":
        delta = max(0.05, abs(value) * relative_width)
        return [round_value(max(0.0, value - delta), 6), round_value(value + delta, 6)]
    return [
        round_value(value * (1 - relative_width), 6),
        round_value(value * (1 + relative_width), 6),
    ]


def npv_from_series(cashflow_series: List[float], discount_rate: float) -> float:
    total = 0.0
    for index, cashflow in enumerate(cashflow_series):
        if index == 0:
            total += cashflow
        else:
            total += cashflow / pow(1 + discount_rate, index)
    return total


def present_value_breakdown(
    cashflow_series: List[float], discount_rate: float
) -> Dict[str, Any]:
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
    if (
        not isinstance(cash_flows, list)
        or len(cash_flows) == 0
        or any(not math.isfinite(value) for value in cash_flows)
    ):
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
        candidate = str(
            item.get("tag")
            or item.get("epistemic")
            or RELIABILITY_TO_TAG.get(reliability, default_tag)
        ).upper()
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


SCALE_DEFAULTS = {
    "personal": {
        "discount_rate": 0.03,
        "horizon_years": 5,
        "objective": "maximize_lifetime_utility",
    },
    "household": {
        "discount_rate": 0.04,
        "horizon_years": 10,
        "objective": "intergenerational_stability",
    },
    "sme": {
        "discount_rate": 0.10,
        "horizon_years": 5,
        "objective": "survival_and_growth",
    },
    "enterprise": {
        "discount_rate": 0.10,
        "horizon_years": 10,
        "objective": "shareholder_value",
    },
    "national": {
        "discount_rate": 0.02,
        "horizon_years": 35,
        "objective": "gdp_plus_welfare",
    },
    "crisis": {
        "discount_rate": float("inf"),
        "horizon_years": 0,
        "objective": "minimize_collapse_probability",
    },
    "civilization": {
        "discount_rate": 0.005,
        "horizon_years": 300,
        "objective": "species_continuation",
    },
    "agentic": {
        "discount_rate": 0.15,
        "horizon_years": 2,
        "objective": "capability_accumulation",
    },
}

CAPITAL_TERMINOLOGY = {
    "financial": {
        "npv_label": "NPV",
        "irr_label": "IRR",
        "pi_label": "PI",
        "commitment_label": "initial_investment",
        "stream_label": "cash_flows",
        "value_label": "Net Present Value",
    },
    "temporal": {
        "npv_label": "NTV",
        "irr_label": "ITR",
        "pi_label": "TI",
        "commitment_label": "initial_time_commitment",
        "stream_label": "time_streams",
        "value_label": "Net Temporal Value",
    },
    "cognitive": {
        "npv_label": "NCV",
        "irr_label": "ICR",
        "pi_label": "CI",
        "commitment_label": "initial_attention_commitment",
        "stream_label": "attention_streams",
        "value_label": "Net Cognitive Value",
    },
    "social": {
        "npv_label": "NSV",
        "irr_label": "ISR",
        "pi_label": "SI",
        "commitment_label": "initial_reputation_commitment",
        "stream_label": "reputation_streams",
        "value_label": "Net Social Value",
    },
    "ecological": {
        "npv_label": "NEV",
        "irr_label": "IER",
        "pi_label": "EI",
        "commitment_label": "initial_resource_commitment",
        "stream_label": "resource_streams",
        "value_label": "Net Ecological Value",
    },
    "strategic": {
        "npv_label": "NXV",
        "irr_label": "IXR",
        "pi_label": "XI",
        "commitment_label": "initial_option_commitment",
        "stream_label": "option_streams",
        "value_label": "Net Strategic Value",
    },
    "thermodynamic": {
        "npv_label": "NΦV",
        "irr_label": "IΦR",
        "pi_label": "ΦI",
        "commitment_label": "initial_energy_commitment",
        "stream_label": "energy_streams",
        "value_label": "Net Thermodynamic Value",
    },
}


def get_scale_defaults(scale_mode: str) -> Dict[str, Any]:
    return SCALE_DEFAULTS.get(scale_mode, SCALE_DEFAULTS["enterprise"])


def get_capital_terminology(capital_type: str) -> Dict[str, str]:
    return CAPITAL_TERMINOLOGY.get(capital_type, CAPITAL_TERMINOLOGY["financial"])


def derive_allocation_signal(
    flags: List[str], primary: Dict[str, Any], tool: str, scale_mode: str = "enterprise"
) -> str:
    if any(flag in INVALID_FLAGS for flag in flags):
        return "INSUFFICIENT_DATA"

    scale = get_scale_defaults(scale_mode)

    if tool in {"wealth_coordination_equilibrium", "wealth_game_theory_solve"}:
        tragedy_risk = primary.get("tragedy_risk", 1.0)
        if any(flag in INVALID_FLAGS for flag in flags):
            return "INSUFFICIENT_DATA"
        if primary.get("in_core") is False or any("BLOCK" in f for f in flags):
            return "REJECT"
        if tragedy_risk > 0.5:
            return "REJECT"
        if tragedy_risk > 0.3:
            return "MARGINAL"
        return "ACCEPT"

    if tool in {"wealth_npv_reward", "wealth_flow_scenario_npv"}:
        npv = primary.get("npv")
        if npv is None:
            return "INSUFFICIENT_DATA"
        if npv > 0:
            return "ACCEPT"
        if npv < 0:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_pi_efficiency":
        pi = primary.get("pi")
        if pi is None:
            return "INSUFFICIENT_DATA"
        if pi > 1:
            return "ACCEPT"
        if pi < 1:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_irr_yield":
        irr = primary.get("irr")
        if irr is None:
            return "INSUFFICIENT_DATA"
        hurdle = (
            scale["discount_rate"] if scale["discount_rate"] != float("inf") else 0.10
        )
        if irr > hurdle:
            return "ACCEPT"
        if irr < hurdle:
            return "REJECT"
        return "MARGINAL"

    if tool == "wealth_payback_time":
        payback = primary.get("payback_periods")
        if payback is None:
            return (
                "REJECT"
                if any(f == "NOT_RECOVERED" for f in flags)
                else "INSUFFICIENT_DATA"
            )
        return "ACCEPT"

    if tool == "wealth_dscr_leverage":
        dscr = primary.get("dscr")
        if dscr is None:
            return "INSUFFICIENT_DATA"
        if dscr >= 1.5:
            return "ACCEPT"
        if dscr >= 1.25:
            return "MARGINAL"
        return "REJECT"

    if tool == "wealth_growth_velocity":
        runway = primary.get("runway_months")
        if runway is not None and runway != math.inf and runway < 3:
            return "REJECT"
        return "ACCEPT"

    if tool == "wealth_cashflow_flow":
        net_monthly = primary.get("net_monthly")
        if net_monthly is not None and net_monthly < 0:
            runway = primary.get("runway_months")
            if runway is not None and runway != math.inf and runway < 3:
                return "REJECT"
            return "MARGINAL"
        return "ACCEPT"

    return "MARGINAL"


def measurement_validate_invariants(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    measurement_results: Optional[Dict[str, Any]] = None,
) -> List[str]:
    flags = []
    if measurement_results is None:
        return flags

    npv = measurement_results.get("npv")
    irr = measurement_results.get("irr")
    pi = measurement_results.get("pi")
    pv_inflows = measurement_results.get("pv_inflows")

    series = build_cashflow_series(initial_investment, cash_flows, terminal_value)
    sign_changes = count_sign_changes(series)

    if pi is not None and pv_inflows is not None:
        expected_pi = pv_inflows / abs(initial_investment)
        if abs(pi - expected_pi) > 0.001:
            flags.append("INVARIANT_VIOLATION")

    if npv is not None and pi is not None and sign_changes <= 1:
        if npv > 0 and pi <= 1:
            flags.append("INVARIANT_VIOLATION")
        if npv < 0 and pi >= 1:
            flags.append("INVARIANT_VIOLATION")

    if (
        npv is not None
        and irr is not None
        and discount_rate is not None
        and sign_changes <= 1
    ):
        if (npv > 0 and irr <= discount_rate) or (npv < 0 and irr >= discount_rate):
            flags.append("INVARIANT_VIOLATION")

    return flags


_policy_engine = PolicyEngine()


def create_envelope(
    tool: str,
    dimension: str,
    primary: Dict[str, Any],
    secondary: Optional[Dict[str, Any]] = None,
    flags: Optional[List[str]] = None,
    assumptions: Optional[List[str]] = None,
    epistemic: str = "CLAIM",
    verdict: Optional[str] = None,
    scale_mode: str = "enterprise",
    governance_args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    flags = flags or []
    derived_governance = verdict or derive_verdict(flags)
    derived_allocation = derive_allocation_signal(flags, primary, tool, scale_mode)
    engine_status = (
        "ERROR"
        if derived_governance == "VOID"
        else "WARNING"
        if derived_governance in ("QUALIFY", "888-HOLD")
        else "VALID"
    )
    derived_epistemic = infer_epistemic(flags, epistemic)

    envelope = {
        "tool": tool,
        "dimension": dimension,
        "verdict": derived_governance,
        "governance_verdict": derived_governance,
        "allocation_signal": derived_allocation,
        "engine_status": engine_status,
        "primary_result": primary,
        "secondary_metrics": secondary or {},
        "integrity_flags": flags,
        "confidence": confidence_from_verdict(derived_governance, flags),
        "epistemic": derived_epistemic,
        "assumptions": assumptions or [],
        "epoch": datetime.utcnow().isoformat() + "Z",
    }

    # === Constitutional Governance Layer ===
    # Governance tools are exempt from recursive envelope governance so they can audit bad proposals
    is_governance_tool = tool in {"wealth_check_floors", "wealth_policy_audit"}
    if (
        scale_mode in {"national", "crisis", "civilization", "agentic"}
        and not is_governance_tool
    ):
        gov_args = governance_args or {}
        floor_result = check_floors(
            {**gov_args, "epistemic": derived_epistemic, "scale_mode": scale_mode}
        )

        # Merge floor outcomes
        if floor_result["verdict"] == "VOID":
            envelope["governance_verdict"] = "VOID"
            envelope["allocation_signal"] = "REJECT"
            envelope["engine_status"] = "ERROR"
        elif floor_result["verdict"] == "HOLD":
            envelope["governance_verdict"] = "888-HOLD"
            envelope["allocation_signal"] = "INSUFFICIENT_DATA"
            envelope["engine_status"] = "WARNING"

        envelope["floor_check"] = {
            "verdict": floor_result["verdict"],
            "violations": floor_result["violations"],
            "holds": floor_result["holds"],
            "warnings": floor_result["warnings"],
        }

        # Policy constraints (if audit data provided)
        if gov_args:
            policy_result = _policy_engine.evaluate(gov_args, scale_mode)
            if not policy_result["policy_pass"]:
                envelope["governance_verdict"] = "VOID"
                envelope["allocation_signal"] = "REJECT"
                envelope["engine_status"] = "ERROR"
            envelope["policy_audit"] = policy_result

        # Vault all high-scale decisions
        append_vault999(
            {
                "tool": tool,
                "scale_mode": scale_mode,
                "allocation_signal": envelope["allocation_signal"],
                "governance_verdict": envelope["governance_verdict"],
                "floor_check": envelope.get("floor_check"),
                "policy_audit": envelope.get("policy_audit"),
            }
        )

    return envelope


def measurement_npv(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
) -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE"),
    ]
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


def bracket_roots(
    npv_fn, lower: float = -0.9999, upper: float = 10.0, steps: int = 4096
) -> List[List[float]]:
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


def measurement_irr(
    initial_investment: float,
    cash_flows: List[float],
    finance_rate: float = 0.1,
    reinvestment_rate: float = 0.1,
    period_unit: str = "annual",
) -> Dict[str, Any]:
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
    roots = {
        round_value(bisect_root(npv_fn, lower, upper), 10) for lower, upper in brackets
    }
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


def measurement_pi(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
) -> Dict[str, Any]:
    npv_measure = measurement_npv(
        initial_investment, cash_flows, discount_rate, terminal_value
    )
    flags = list(npv_measure["flags"])
    if (
        count_sign_changes(
            build_cashflow_series(initial_investment, cash_flows, terminal_value)
        )
        > 1
    ):
        flags.append("NON_NORMAL_FLOWS")
    pi = (
        None
        if npv_measure["pv_inflows"] is None
        else npv_measure["pv_inflows"] / abs(initial_investment)
    )
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
        if (
            scenario is None
            or not math.isfinite(scenario.get("probability"))
            or not math.isfinite(scenario.get("outcome"))
        ):
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
    downside_probability = sum(
        scenario["probability"] for scenario in scenarios if scenario["outcome"] < 0
    )
    variance = sum(
        scenario["probability"] * pow(scenario["outcome"] - emv, 2)
        for scenario in scenarios
    )
    return {
        "emv": round_value(emv, 6),
        "total_probability": round_value(total_probability, 6),
        "downside_probability": round_value(downside_probability, 6),
        "worst_outcome": round_value(
            min(scenario["outcome"] for scenario in scenarios), 6
        ),
        "best_outcome": round_value(
            max(scenario["outcome"] for scenario in scenarios), 6
        ),
        "variance": round_value(variance, 6),
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_payback(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0,
    period_unit: str = "annual",
) -> Dict[str, Any]:
    flags = [
        *validate_series(initial_investment, cash_flows),
        *validate_rate(discount_rate, "INVALID_DISCOUNT_RATE"),
    ]
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
        adjusted_cashflow = (
            raw_cashflow / pow(1 + discount_rate, index + 1)
            if discount_rate > 0
            else raw_cashflow
        )
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
        "payback_periods": round_value(payback_periods, 6)
        if payback_periods is not None
        else None,
        "discounted": discount_rate > 0,
        "period_unit": period_unit,
        "assumptions": assumptions,
        "flags": flags,
    }


def measurement_dscr(
    cfads: Optional[float],
    debt_service: Optional[float],
    ebitda: Optional[float],
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
) -> Dict[str, Any]:
    flags: List[str] = []
    numerator = cfads if cfads is not None else ebitda
    denominator = (
        debt_service if debt_service is not None else principal + interest + leases
    )
    if numerator is None or not math.isfinite(numerator):
        flags.append("INVALID_CFADS")
    if denominator is None or not math.isfinite(denominator) or denominator <= 0:
        flags.append("INVALID_DEBT_SERVICE")
    if cfads is None and ebitda is not None:
        flags.append("EBITDA_PROXY_USED")

    dscr = (
        None
        if any(flag in INVALID_FLAGS for flag in flags)
        else numerator / denominator
    )
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
        "confidence_band": None
        if dscr is None
        else derive_confidence_band(dscr, input_epistemic, "absolute-nonnegative"),
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

    r_adj = max(
        0.0,
        round_value(
            base_rate
            + entropy_penalty
            - peace_discount
            - maruah_discount
            - trust_discount
            - civ_discount,
            6,
        )
        or 0.0,
    )
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
        "uncertainty_band": [
            max(0.0, round_value(r_adj - uncertainty_radius, 6) or 0.0),
            round_value(r_adj + uncertainty_radius, 6),
        ],
        "integrity_flags": flags,
        "assumptions": [
            "CapitalX pricing is an estimate layered on top of the base rate.",
            "If entropy rises, r_adj must not decrease.",
        ],
    }


@mcp.tool(name="wealth_npv_reward")
def npv_reward(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute NPV, Terminal Value, and EAA. [Reward Dimension]"""
    measurement = measurement_npv(
        initial_investment,
        cash_flows,
        discount_rate,
        terminal_value,
        period_unit,
        input_epistemic,
    )
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
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_irr_yield")
def irr_yield(
    initial_investment: float,
    cash_flows: List[float],
    reinvestment_rate: float = 0.1,
    finance_rate: float = 0.1,
    period_unit: str = "annual",
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute IRR and MIRR (Potential). [Energy Dimension]"""
    measurement = measurement_irr(
        initial_investment, cash_flows, finance_rate, reinvestment_rate, period_unit
    )
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        0,
        {
            "npv": npv_from_series(
                build_cashflow_series(initial_investment, cash_flows), discount_rate
            ),
            "irr": measurement["irr"],
        },
    )
    all_flags = list(dict.fromkeys([*measurement["flags"], *invariant_flags]))
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
        all_flags,
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_pi_efficiency")
def pi_efficiency(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
    terminal_value: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Profitability Index (Concentration). [Energy Dimension]"""
    measurement = measurement_pi(
        initial_investment, cash_flows, discount_rate, terminal_value
    )
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        terminal_value,
        {"pi": measurement["pi"], "pv_inflows": measurement["pv_inflows"]},
    )
    all_flags = list(dict.fromkeys([*measurement["flags"], *invariant_flags]))
    ranking_signal = (
        "EFFICIENT"
        if measurement["pi"] is not None and measurement["pi"] >= 1
        else "EXTRACTIVE"
    )
    return create_envelope(
        "wealth_pi_efficiency",
        "Energy",
        {"pi": measurement["pi"]},
        {"ranking_signal": ranking_signal},
        all_flags,
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_emv_risk")
def emv_risk(scenarios: List[dict], scale_mode: str = "enterprise") -> Any:
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
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_audit_entropy")
def audit_entropy(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> Any:
    """Audit project cash flows for noise and multiple IRRs. [Entropy Dimension]"""
    irr_measure = measurement_irr(
        initial_investment, cash_flows, discount_rate, discount_rate
    )
    npv_measure = measurement_npv(initial_investment, cash_flows, discount_rate)
    invariant_flags = measurement_validate_invariants(
        initial_investment,
        cash_flows,
        discount_rate,
        0,
        {"npv": npv_measure["npv"], "irr": irr_measure["irr"]},
    )
    all_flags = list(dict.fromkeys([*irr_measure["flags"], *invariant_flags]))
    sensitivity = []
    for multiplier in [0.8, 0.9, 1.0, 1.1, 1.2]:
        sweep_npv = measurement_npv(
            initial_investment, cash_flows, discount_rate * multiplier
        )
        sensitivity.append({"multiplier": multiplier, "npv": sweep_npv["npv"]})
    return create_envelope(
        "wealth_audit_entropy",
        "Entropy",
        {"sign_changes": irr_measure["sign_changes"]},
        {"sensitivity_sweep": sensitivity},
        all_flags,
        irr_measure["assumptions"],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_dscr_leverage")
def dscr_leverage(
    ebitda: Optional[float] = None,
    principal: float = 0,
    interest: float = 0,
    leases: float = 0,
    cfads: Optional[float] = None,
    debt_service: Optional[float] = None,
    period_unit: str = "annual",
    input_epistemic: str = "CLAIM",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Debt Service Coverage Ratio (Structural Load). [Survival Dimension]"""
    measurement = measurement_dscr(
        cfads,
        debt_service,
        ebitda,
        principal,
        interest,
        leases,
        period_unit,
        input_epistemic,
    )
    return create_envelope(
        "wealth_dscr_leverage",
        "Survival",
        {"dscr": measurement["dscr"]},
        {
            "basis": measurement["basis"],
            "period_unit": measurement["period_unit"],
            "confidence_band": measurement["confidence_band"],
        },
        measurement["flags"],
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_payback_time")
def payback_time(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float = 0,
    period_unit: str = "annual",
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Payback Period (Recovery Velocity). [Time Dimension]"""
    measurement = measurement_payback(
        initial_investment, cash_flows, discount_rate, period_unit
    )
    return create_envelope(
        "wealth_payback_time",
        "Time",
        {"payback_periods": measurement["payback_periods"]},
        {
            "period_unit": measurement["period_unit"],
            "discounted": measurement["discounted"],
        },
        measurement["flags"],
        measurement["assumptions"],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_growth_velocity")
def growth_velocity(
    principal: float,
    rate: float,
    years: int,
    annual_contribution: float = 0,
    monthly_burn: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute Compound Growth and Runway. [Velocity Dimension]"""
    total = principal
    for _ in range(years):
        total = total * (1 + rate) + annual_contribution
    final_value = round_value(total, 2)
    low = round_value(final_value * 0.88, 2)
    high = round_value(final_value * 1.12, 2)
    net_monthly = -monthly_burn
    runway_months = (
        math.inf if monthly_burn <= 0 else round_value(principal / monthly_burn, 1)
    )
    flags = (
        ["RUNWAY_CRITICAL"]
        if monthly_burn > 0 and runway_months is not None and runway_months < 3
        else []
    )
    return create_envelope(
        "wealth_growth_velocity",
        "Velocity",
        {"growth_forecast": {"low": low, "mid": final_value, "high": high}},
        {
            "runway_months": runway_months,
            "final_value": final_value,
            "net_monthly": net_monthly,
        },
        flags,
        ["Forward projections remain ESTIMATE by design."],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_networth_state")
def networth_state(
    assets: Optional[List[dict]] = None,
    liabilities: Optional[List[dict]] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute portfolio balance sheet (Accumulated Mass). [Mass Dimension]"""
    assets = assets or []
    liabilities = liabilities or []
    asset_value = sum(
        asset.get("value", 0)
        for asset in assets
        if math.isfinite(asset.get("value", 0))
    )
    liability_value = sum(
        liability.get("outstanding", liability.get("principal", 0))
        for liability in liabilities
        if math.isfinite(liability.get("outstanding", liability.get("principal", 0)))
    )
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
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_cashflow_flow")
def cashflow_flow(
    income: Optional[List[dict]] = None,
    expenses: Optional[List[dict]] = None,
    liquid_assets: float = 0,
    scale_mode: str = "enterprise",
) -> Any:
    """Compute metabolic liquidity (Flow Dimension). [Flow Dimension]"""
    income = [item for item in (income or []) if item.get("active", True)]
    expenses = [item for item in (expenses or []) if item.get("active", True)]
    total_income = sum(
        item.get("monthly_amount", 0)
        for item in income
        if math.isfinite(item.get("monthly_amount", 0))
    )
    total_expenses = sum(
        item.get("monthly_amount", 0)
        for item in expenses
        if math.isfinite(item.get("monthly_amount", 0))
    )
    net_monthly = total_income - total_expenses
    burn_rate = max(0.0, -net_monthly)
    runway_months = (
        math.inf if burn_rate == 0 else round_value(liquid_assets / burn_rate, 1)
    )
    flags = (
        ["RUNWAY_CRITICAL"]
        if burn_rate > 0 and runway_months is not None and runway_months < 3
        else []
    )
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
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_score_kernel")
def score_kernel(
    base_rate: float,
    d_s: float,
    peace2: float,
    maruah_score: float,
    trust_index: float = 0.5,
    delta_civ: float = 0.0,
    compare: bool = False,
    wealth_signals: Optional[dict] = None,
    extractive_signals: Optional[dict] = None,
    scale_mode: str = "enterprise",
) -> Any:
    """Final Sovereign Allocation Verdict. [Allocation Dimension]"""
    wealth_payload = {
        "dS": d_s,
        "peace2": peace2,
        "maruahScore": maruah_score,
        "trustIndex": trust_index,
        "deltaCiv": delta_civ,
    }
    if wealth_signals:
        wealth_payload.update(wealth_signals)

    flags: List[str] = []
    if d_s > 0.3:
        flags.append("HIGH_ENTROPY_SIGNAL")
    if maruah_score < 0.6:
        flags.append("SOVEREIGN_DIGNITY_LOW")

    wealth_result = capitalx(base_rate, wealth_payload)
    if compare:
        extractive_result = capitalx(base_rate, extractive_signals or {})
        comparison = {
            "base_rate": wealth_result["base_rate"],
            "wealth_r_adj": wealth_result["r_adj"],
            "extractive_r_adj": extractive_result["r_adj"],
            "advantage_bps": round(
                (extractive_result["r_adj"] - wealth_result["r_adj"]) * 10000
            ),
        }
        return create_envelope(
            "wealth_score_kernel",
            "Allocation",
            comparison,
            {},
            [
                *flags,
                *(wealth_result["integrity_flags"]),
                *(extractive_result["integrity_flags"]),
            ],
            ["CapitalX remains an estimate until delta_bps is proven."],
            epistemic="ESTIMATE",
            scale_mode=scale_mode,
        )

    return create_envelope(
        "wealth_score_kernel",
        "Allocation",
        wealth_result,
        {},
        [*flags, *(wealth_result["integrity_flags"])],
        wealth_result["assumptions"],
        epistemic="ESTIMATE",
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_personal_decision")
def personal_decision(
    alternatives: List[dict],
    constraints: dict,
    values: Optional[dict] = None,
    scale_mode: str = "personal",
) -> Any:
    """Rank personal alternatives under constraints. [Personal Dimension]"""
    values = values or {}
    ranked = []
    flags = []
    for alt in alternatives:
        cost = alt.get("cost", 0)
        time = alt.get("time_hours", 0)
        utility = alt.get("expected_utility", 0)
        weight_money = values.get("weight_money", 0.33)
        weight_time = values.get("weight_time", 0.33)
        weight_utility = values.get("weight_utility", 0.34)
        budget = constraints.get("budget", math.inf)
        time_budget = constraints.get("time_budget", math.inf)
        score = (
            weight_money * (-cost / max(budget, 1))
            + weight_time * (-time / max(time_budget, 1))
            + weight_utility * utility
        )
        feasible = cost <= budget and time <= time_budget
        ranked.append(
            {
                "name": alt.get("name"),
                "score": round_value(score, 6),
                "feasible": feasible,
            }
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)
    if not any(r["feasible"] for r in ranked):
        flags.append("NO_FEASIBLE_ALTERNATIVE")
    return create_envelope(
        "wealth_personal_decision",
        "Personal",
        {"ranked_alternatives": ranked},
        {"constraint_summary": constraints},
        flags,
        ["Personal decisions trade money, time, and subjective utility."],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_agent_budget")
def agent_budget(
    compute_budget_usd: float,
    token_budget: float,
    time_deadline_hours: float,
    expected_value_of_information: float,
    actions: List[dict],
    scale_mode: str = "agentic",
) -> Any:
    """Optimal action sequence for an AI agent under resource constraints. [Agentic Dimension]"""
    feasible = []
    for action in actions:
        cost = action.get("compute_cost_usd", 0) + action.get("token_cost", 0) * 0.00001
        time = action.get("time_hours", 0)
        value = action.get("expected_value", 0)
        if cost <= compute_budget_usd and time <= time_deadline_hours:
            feasible.append(
                {
                    "name": action.get("name"),
                    "cost": round_value(cost, 6),
                    "value": value,
                    "efficiency": round_value(value / max(cost, 1e-9), 6),
                }
            )
    feasible.sort(key=lambda x: x["efficiency"], reverse=True)
    selected = []
    remaining_budget = compute_budget_usd
    remaining_time = time_deadline_hours
    total_value = 0.0
    for action in feasible:
        if (
            action["cost"] <= remaining_budget
            and action["cost"] * 0.00001 <= token_budget
            and action.get("time_hours", 0) <= remaining_time
        ):
            selected.append(action["name"])
            remaining_budget -= action["cost"]
            remaining_time -= action.get("time_hours", 0)
            total_value += action["value"]
    flags = []
    if total_value < expected_value_of_information:
        flags.append("VALUE_OF_INFORMATION_NEGATIVE")
    return create_envelope(
        "wealth_agent_budget",
        "Agentic",
        {"selected_actions": selected, "total_value": round_value(total_value, 6)},
        {
            "remaining_budget": round_value(remaining_budget, 2),
            "remaining_time": round_value(remaining_time, 2),
        },
        flags,
        ["Agent budgets optimize value per unit of compute and latency."],
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_crisis_triage")
def crisis_triage(
    resources: dict,
    demands: List[dict],
    recovery_horizon_days: float = 30,
    scale_mode: str = "crisis",
) -> Any:
    """Survival-oriented resource triage. [Crisis Dimension]"""
    total_supply = sum(v for v in resources.values() if math.isfinite(v))
    total_demand = sum(
        d.get("amount", 0) for d in demands if math.isfinite(d.get("amount", 0))
    )
    gap = total_demand - total_supply
    sorted_demands = sorted(demands, key=lambda d: d.get("urgency", 1), reverse=True)
    allocated = []
    remaining = dict(resources)
    for demand in sorted_demands:
        name = demand.get("name")
        amount = demand.get("amount", 0)
        res_type = demand.get("resource_type", "general")
        available = remaining.get(res_type, remaining.get("general", 0))
        grant = min(amount, available)
        remaining[res_type] = available - grant
        if res_type != "general" and "general" in remaining:
            remaining["general"] -= grant
        allocated.append(
            {
                "name": name,
                "granted": round_value(grant, 2),
                "shortfall": round_value(amount - grant, 2),
            }
        )
    survival_probability = max(0.0, min(1.0, total_supply / max(total_demand, 1e-9)))
    flags = []
    if survival_probability < 0.5:
        flags.append("SURVIVAL_CRITICAL")
    elif survival_probability < 0.8:
        flags.append("SURVIVAL_AT_RISK")
    return create_envelope(
        "wealth_crisis_triage",
        "Crisis",
        {
            "survival_probability": round_value(survival_probability, 4),
            "resource_gap": round_value(gap, 2),
        },
        {
            "triage_allocation": allocated,
            "recovery_horizon_days": recovery_horizon_days,
        },
        flags,
        ["Crisis mode prioritizes survival probability over efficiency."],
        scale_mode=scale_mode,
        governance_args={
            "reversible": False,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0,
            "maruah_score": 0.6,
            "runway_months": recovery_horizon_days / 30.0,
        },
    )


@mcp.tool(name="wealth_civilization_stewardship")
def civilization_stewardship(
    population: float,
    energy_budget_twh: float,
    carbon_budget_gt: float,
    tech_growth_rate: float,
    time_horizon_years: int = 100,
    scale_mode: str = "civilization",
) -> Any:
    """Long-term civilization sustainability path. [Civilization Dimension]"""
    flags = []
    energy_per_capita = energy_budget_twh / max(population, 1)
    carbon_intensity = carbon_budget_gt / max(energy_budget_twh, 1)
    sustainable_growth = tech_growth_rate * (1 - carbon_intensity)
    projected_pop = population * pow(
        1 + min(tech_growth_rate, 0.02), time_horizon_years / 100
    )
    collapse_risk = max(0.0, min(1.0, (projected_pop * 10) / max(energy_budget_twh, 1)))
    if collapse_risk > 0.5:
        flags.append("CIVILIZATION_COLLAPSE_RISK_HIGH")
    if carbon_intensity > 0.05:
        flags.append("CARBON_BUDGET_EXHAUSTION")
    sustainability_index = max(
        0.0, min(1.0, sustainable_growth / max(collapse_risk, 0.01))
    )
    return create_envelope(
        "wealth_civilization_stewardship",
        "Civilization",
        {
            "sustainability_index": round_value(sustainability_index, 4),
            "collapse_risk": round_value(collapse_risk, 4),
            "sustainable_growth_rate": round_value(sustainable_growth, 6),
        },
        {
            "energy_per_capita_twh": round_value(energy_per_capita, 6),
            "projected_population_billions": round_value(projected_pop / 1e9, 4),
            "time_horizon_years": time_horizon_years,
        },
        flags,
        ["Civilization modeling uses long-horizon, low-discount assumptions."],
        scale_mode=scale_mode,
        governance_args={
            "reversible": False,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - collapse_risk,
            "maruah_score": 0.5,
            "carbon_intensity": carbon_intensity,
            "social_stability_index": 1.0 - collapse_risk,
        },
    )


@mcp.tool(name="wealth_coordination_equilibrium")
def coordination_equilibrium(
    agents: List[dict],
    shared_resources: dict,
    mechanism: str = "cooperative",
    scale_mode: str = "enterprise",
) -> Any:
    """Multi-agent resource coordination and equilibrium analysis. [Coordination Dimension]"""
    # Normalize agents to LP schema
    lp_agents = []
    for agent in agents:
        lp_agents.append(
            {
                "name": agent.get("name", "unnamed"),
                "utility": agent.get("utility", {res: 1.0 for res in shared_resources}),
                "demand": agent.get("resource_demand", {}),
            }
        )

    lp_result = lp_allocate(lp_agents, shared_resources)
    commons = commons_risk(lp_agents, shared_resources)
    tragedy_risk = commons["tragedy_risk"]
    conflicts = []
    if "DEMAND_PARTIALLY_UNMET" in commons.get("flags", []):
        for name, unmet in lp_result.get("unmet_demand", {}).items():
            for res, gap in unmet.items():
                conflicts.append({"agent": name, "resource": res, "gap": gap})

    cooperative_surplus = 0.0
    if mechanism == "cooperative":
        for agent in agents:
            cooperative_surplus += agent.get("cooperative_value", 0)

    flags = commons.get("flags", [])
    if not conflicts and lp_result["feasible"]:
        flags.append("EQUILIBRIUM_FEASIBLE")

    return create_envelope(
        "wealth_coordination_equilibrium",
        "Coordination",
        {
            "tragedy_risk": round_value(tragedy_risk, 4),
            "conflict_count": len(conflicts),
            "total_welfare": lp_result.get("total_welfare", 0.0),
        },
        {
            "conflicts": conflicts,
            "cooperative_surplus": round_value(cooperative_surplus, 2),
            "mechanism": mechanism,
            "shadow_prices": commons.get("shadow_prices", {}),
        },
        flags,
        [
            "Coordination layer uses LP shadow prices and scarcity metrics, not hand-wavy ratios."
        ],
        scale_mode=scale_mode,
        governance_args={
            "reversible": True,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - tragedy_risk,
            "maruah_score": 0.6,
            "dS": tragedy_risk,
        },
    )


@mcp.tool(name="wealth_game_theory_solve")
def game_theory_solve(
    agents: List[dict],
    resources: dict,
    mechanism: str = "cooperative",
    solve_equilibrium: bool = False,
    scale_mode: str = "enterprise",
) -> Any:
    """Multi-agent allocation brain: LP welfare, Shapley/core, and Nash approximation. [Coordination Dimension]"""
    lp_agents = []
    for agent in agents:
        lp_agents.append(
            {
                "name": agent.get("name", "unnamed"),
                "utility": agent.get("utility", {res: 1.0 for res in resources}),
                "demand": agent.get("resource_demand", {}),
            }
        )

    lp_result = lp_allocate(lp_agents, resources)
    commons = commons_risk(lp_agents, resources)
    shapley = shapley_values(lp_agents, resources)
    core = core_feasibility(lp_agents, resources, lp_result.get("allocations"))

    equilibrium = {}
    if solve_equilibrium:
        eq = nash_approximation(lp_agents, resources)
        equilibrium = {
            "allocations": eq.get("equilibrium", {}),
            "converged": eq.get("converged", False),
            "iterations": eq.get("iterations", 0),
        }

    flags = []
    if not lp_result["feasible"]:
        flags.append("LP_INFEASIBLE")
    if commons.get("tragedy_risk", 0.0) > 0.5:
        flags.append("TRAGEDY_OF_COMMONS")
    if not core.get("in_core", False):
        flags.append("CORE_BLOCK_DETECTED")
    if solve_equilibrium and not equilibrium.get("converged", False):
        flags.append("NASH_NO_CONVERGENCE")

    return create_envelope(
        "wealth_game_theory_solve",
        "Coordination",
        {
            "total_welfare": lp_result.get("total_welfare", 0.0),
            "tragedy_risk": commons.get("tragedy_risk", 0.0),
            "in_core": core.get("in_core", False),
            "blocking_coalitions": core.get("blocking_coalitions", [])[:5],
        },
        {
            "allocations": lp_result.get("allocations", {}),
            "shadow_prices": commons.get("shadow_prices", {}),
            "shapley": shapley.get("shapley", {}),
            "scarcity_index": commons.get("scarcity_index", {}),
            "equilibrium": equilibrium,
        },
        flags,
        [
            "Game-theory solver replaces naive tragedy-risk with LP, core, and equilibrium logic."
        ],
        scale_mode=scale_mode,
        governance_args={
            "reversible": True,
            "human_confirmed": False,
            "epistemic": "ESTIMATE",
            "peace2": 1.0 - commons.get("tragedy_risk", 0.0),
            "maruah_score": 0.6,
            "dS": commons.get("tragedy_risk", 0.0),
        },
    )


@mcp.tool(name="wealth_monte_carlo_forecast")
def monte_carlo_forecast(
    initial_commitment: float,
    mean_cash_flows: List[float],
    volatilities: List[float],
    discount_rate: float = 0.1,
    simulations: int = 10000,
    distribution: str = "lognormal",
    scale_mode: str = "enterprise",
) -> Any:
    """Stochastic forecast with probability-weighted outcomes. [Risk Dimension]"""
    import random

    random.seed(42)
    npvs = []
    periods = len(mean_cash_flows)
    for _ in range(simulations):
        draws = []
        for i, mean in enumerate(mean_cash_flows):
            vol = volatilities[i] if i < len(volatilities) else volatilities[-1]
            if distribution == "lognormal":
                sigma = math.sqrt(math.log1p((vol / max(abs(mean), 1e-9)) ** 2))
                mu = math.log(max(abs(mean), 1e-9)) - 0.5 * sigma**2
                draw = random.lognormvariate(mu, sigma) * (1 if mean >= 0 else -1)
            elif distribution == "triangular":
                low = mean * (1 - vol)
                high = mean * (1 + vol)
                draw = random.triangular(low, high, mean)
            else:
                draw = random.gauss(mean, vol)
            draws.append(draw)
        npv = -abs(initial_commitment) + sum(
            draws[t] / pow(1 + discount_rate, t + 1) for t in range(periods)
        )
        npvs.append(npv)
    npvs.sort()
    positive_prob = sum(1 for n in npvs if n > 0) / len(npvs)
    es_5 = npvs[int(len(npvs) * 0.05)] if npvs else 0
    upside_95 = npvs[int(len(npvs) * 0.95)] if npvs else 0
    mean_npv = sum(npvs) / len(npvs) if npvs else 0
    variance_npv = sum((n - mean_npv) ** 2 for n in npvs) / len(npvs) if npvs else 0
    flags = []
    if positive_prob < 0.5:
        flags.append("MAJORITY_DOWNSIDE")
    return create_envelope(
        "wealth_monte_carlo_forecast",
        "Risk",
        {
            "probability_positive_nrv": round_value(positive_prob, 4),
            "expected_shortfall_5pct": round_value(es_5, 2),
            "upside_potential_95pct": round_value(upside_95, 2),
        },
        {
            "mean_npv": round_value(mean_npv, 2),
            "volatility_of_outcome": round_value(math.sqrt(variance_npv), 2),
            "simulations": simulations,
            "distribution": distribution,
        },
        flags,
        ["Monte Carlo provides density estimates, not deterministic guarantees."],
        scale_mode=scale_mode,
        governance_args={
            "epistemic": "ESTIMATE",
            "uncertainty_band": [round_value(es_5, 2), round_value(upside_95, 2)],
            "scale_mode": scale_mode,
        },
    )


# === INGESTION LAYER ===
try:
    from host.ingest.registry import get_registry

    INGEST_AVAILABLE = True
except Exception:
    INGEST_AVAILABLE = False

    def get_registry():  # type: ignore
        return None


@mcp.tool(name="wealth_ingest_fetch")
def ingest_fetch(
    source: str,
    series_id: str,
    entity_code: str,
    use_cache: bool = True,
    bus: str = "slow",
) -> Any:
    """Fetch a live data series from an open public source. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_fetch",
            "Sense",
            {"records": []},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.fetch(
        source, series_id, entity_code, use_cache=use_cache, bus=bus
    )
    flags = result.get("flags", [])
    return create_envelope(
        "wealth_ingest_fetch",
        "Sense",
        {"count": result["count"], "cached": result.get("cached", False)},
        {"records": result["records"][:50], "flags": flags},
        flags,
        ["Live feeds carry source, timestamp, unit, and revision metadata."],
    )


@mcp.tool(name="wealth_ingest_snapshot")
def ingest_snapshot(entity_code: str, sources: Optional[List[str]] = None) -> Any:
    """Fetch a cross-source macro/energy/carbon snapshot for a geography. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_snapshot",
            "Sense",
            {"coverage": 0},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.snapshot(entity_code, sources=sources)
    flags = result.get("flags", [])
    return create_envelope(
        "wealth_ingest_snapshot",
        "Sense",
        {"coverage": result["coverage"], "entity_code": entity_code},
        {"snapshot": result["snapshot"], "flags": flags},
        flags,
        ["Snapshot assembles orthogonal reality anchors for a single geography."],
    )


@mcp.tool(name="wealth_ingest_sources")
def ingest_sources() -> Any:
    """List available data sources and their adapter status. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_sources",
            "Sense",
            {"sources": []},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    sources = registry.available_sources()
    return create_envelope(
        "wealth_ingest_sources",
        "Sense",
        {"sources": sources},
        {},
        [],
        [
            "Sources are ranked by sovereignty: central bank > multilateral > aggregator."
        ],
    )


@mcp.tool(name="wealth_ingest_health")
def ingest_health(adapter: Optional[str] = None) -> Any:
    """Return bus health metrics: latency, cache age, field completeness, stale flags. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_health",
            "Sense",
            {},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    health = registry.health(adapter)
    return create_envelope(
        "wealth_ingest_health",
        "Sense",
        {"health": health},
        {},
        [],
        ["Health tracks latency, success rate, cache age, and observation freshness."],
    )


@mcp.tool(name="wealth_ingest_vintage")
def ingest_vintage(
    source: str, series_id: str, entity_code: str, vintage_date: str
) -> Any:
    """Fetch a specific vintage of a series (FRED/ALFRED). [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_vintage",
            "Sense",
            {"count": 0},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    try:
        if source == "FRED":
            result = registry.fetch(
                source,
                series_id,
                entity_code,
                use_cache=False,
                vintage_dates=[vintage_date],
                bus="archive",
            )
        else:
            result = {
                "records": [],
                "flags": [f"VINTAGE_UNSUPPORTED:{source}"],
                "count": 0,
            }
    except Exception as exc:
        result = {"records": [], "flags": [f"VINTAGE_ERROR:{exc}"], "count": 0}
    return create_envelope(
        "wealth_ingest_vintage",
        "Sense",
        {"count": result["count"]},
        {"records": result["records"][:50], "flags": result["flags"]},
        result["flags"],
        ["Vintages preserve truth as it was known at a specific date."],
    )


@mcp.tool(name="wealth_ingest_reconcile")
def ingest_reconcile(entity_code: str) -> Any:
    """Cross-source divergence detection for a geography. [Sense Dimension]"""
    if not INGEST_AVAILABLE:
        return create_envelope(
            "wealth_ingest_reconcile",
            "Sense",
            {},
            {},
            ["INGEST_LAYER_UNAVAILABLE"],
            ["Ingest layer failed to initialize."],
        )
    registry = get_registry()
    result = registry.reconcile(entity_code)
    return create_envelope(
        "wealth_ingest_reconcile",
        "Sense",
        {
            "divergences": result["divergences"],
            "snapshot_coverage": result["snapshot_coverage"],
        },
        {"flags": result["flags"]},
        result["flags"],
        ["Reconciliation surfaces contradictory signals across independent sources."],
    )


@mcp.tool(name="wealth_check_floors")
def check_floors_tool(
    reversible: bool = True,
    human_confirmed: bool = False,
    epistemic: str = "ESTIMATE",
    ai_is_deciding: bool = False,
    floor_override: bool = False,
    peace2: float = 1.0,
    maruah_score: float = 0.5,
    uncertainty_band: Optional[List[float]] = None,
    operation_type: str = "PROJECTION",
    scale_mode: str = "enterprise",
    task_definition: str = "",
    phantom_entries: bool = False,
    critical: bool = False,
    pin_verified: bool = False,
) -> Any:
    """Evaluate F1–F13 constitutional floors. [Governance Dimension]"""
    result = check_floors(
        {
            "reversible": reversible,
            "human_confirmed": human_confirmed,
            "epistemic": epistemic,
            "ai_is_deciding": ai_is_deciding,
            "floor_override": floor_override,
            "peace2": peace2,
            "maruah_score": maruah_score,
            "uncertainty_band": uncertainty_band,
            "operation_type": operation_type,
            "scale_mode": scale_mode,
            "task_definition": task_definition,
            "phantom_entries": phantom_entries,
            "critical": critical,
            "pin_verified": pin_verified,
        }
    )
    gov_verdict = {
        "HOLD": "888-HOLD",
        "VOID": "VOID",
        "CAUTION": "QUALIFY",
        "SEAL": "SEAL",
    }.get(result["verdict"], "SEAL")
    return create_envelope(
        "wealth_check_floors",
        "Governance",
        {"pass": result["pass"], "verdict": result["verdict"]},
        {
            "violations": result["violations"],
            "holds": result["holds"],
            "warnings": result["warnings"],
            "maruah_band": maruah_band(maruah_score),
        },
        [*result["violations"], *result["holds"]],
        ["F1-F13 floors are hard constraints, not suggestions."],
        epistemic=epistemic,
        verdict=gov_verdict,
        scale_mode=scale_mode,
    )


@mcp.tool(name="wealth_policy_audit")
def policy_audit(
    proposal: dict, constraints: Optional[dict] = None, scale_mode: str = "enterprise"
) -> Any:
    """Audit an allocation proposal against configurable policy constraints. [Governance Dimension]"""
    engine = PolicyEngine(constraints)
    result = engine.evaluate(proposal, scale_mode)
    policy_verdict = (
        "VOID"
        if not result["policy_pass"]
        else ("QUALIFY" if result["flags"] else "SEAL")
    )
    return create_envelope(
        "wealth_policy_audit",
        "Governance",
        {"policy_pass": result["policy_pass"]},
        {
            "flags": result["flags"],
            "details": result["details"],
            "constraints_applied": result["constraints_applied"],
        },
        result["flags"],
        ["Policy constraints encode constitutional economic boundaries."],
        verdict=policy_verdict,
        scale_mode=scale_mode,
    )


@mcp.resource("wealth://doctrine/valuation")
def get_valuation_doctrine() -> str:
    return json.dumps(
        {
            "motto": "Physics > Narrative",
            "principles": [
                "F1: Absolute Value (NPV) is the primary anchor.",
                "F2: Reinvestment risk must be modeled via MIRR.",
                "F3: Time-Value is a physical decay function.",
                "F4: Leverage must never break the DSCR floor (1.25x).",
                "F5: Mandatory governance signals (dS, peace2, maruah) for SEAL.",
            ],
            "protocol": f"Dimensional Forge v{__version__}",
        },
        indent=2,
    )


@mcp.resource("wealth://dimensions/definitions")
def get_dimensional_definitions() -> str:
    return json.dumps(
        {
            "Reward": "Total energy output (NPV, EAA).",
            "Energy": "Efficiency and potential (IRR, PI).",
            "Entropy": "Risk, noise, and probability (EMV, Audit).",
            "Time": "Recovery velocity (Payback).",
            "Mass": "Accumulated state (Net Worth).",
            "Flow": "Metabolic rate (Cash Flow).",
            "Velocity": "Rate of expansion (Growth).",
            "Survival": "Structural load capacity (DSCR).",
            "Allocation": "Sovereign decision kernel (Score).",
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
