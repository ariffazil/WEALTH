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
    """
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

    return {
        "p10": round(terminal_values[int(n * 0.10)], 2),
        "p25": round(terminal_values[int(n * 0.25)], 2),
        "p50": round(terminal_values[int(n * 0.50)], 2),
        "p75": round(terminal_values[int(n * 0.75)], 2),
        "p90": round(terminal_values[int(n * 0.90)], 2),
        "mean": round(sum(terminal_values) / n, 2),
        "simulations": simulations,
        "periods": periods,
    }


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


__all__ = [
    "compute_emv",
    "monte_carlo_simulation",
    "compute_evoi",
    "detect_false_confluence",
    "compute_asymmetry",
]
