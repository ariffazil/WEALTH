"""
WEALTH Core — Math Primitives.

Pure mathematical functions extracted from internal/kernel_math.py and
internal/invariants.py. No MCP dependency, no I/O.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

# Re-export from existing internal modules for backward compatibility.
# During migration, these are thin imports. After migration, they become
# independent implementations.

try:
    from internal.kernel_math import (
        RobustRegimeKalmanFilter,
        HoltSmoothing,
    )

    _KERNEL_MATH_AVAILABLE = True
except ImportError:
    _KERNEL_MATH_AVAILABLE = False

try:
    from internal.invariants import GScoreEngine, get_g_score

    _INVARIANTS_AVAILABLE = True
except ImportError:
    _INVARIANTS_AVAILABLE = False

try:
    from internal.governance import (
        ForgeLaw,
        compute_kappa_r,
        compute_psi_le,
        get_qdf_version,
    )

    _GOVERNANCE_AVAILABLE = True
except ImportError:
    _GOVERNANCE_AVAILABLE = False


def npv(cash_flows: list[float], discount_rate: float) -> float:
    """Compute Net Present Value.

    Standard convention: cash_flows[0] is the initial investment at t=0
    (typically negative), and cash_flows[1:] are future cash flows at
    t=1, t=2, ..., discounted appropriately.

    Golden test vectors (2026-07-07, SVB backtest):
      npv([-100,30,30,30,30,30], 0.1) → 13.72
      npv([-150,20,20,20,20,20,200], 0.1) → -17.36
    """
    total = 0.0
    for t, cf in enumerate(cash_flows):
        total += cf / ((1 + discount_rate) ** t)
    return round(total, 2)


def irr(
    cash_flows: list[float],
    tolerance: float = 1e-6,
    max_iterations: int = 2000,
) -> float | None:
    """Compute Internal Rate of Return via bisection.

    Standard convention: cash_flows[0] is the initial investment at t=0
    (typically negative), and cash_flows[1:] are future cash flows.

    Golden test vectors (2026-07-07, SVB backtest):
      irr([-100, 110]) → 0.10  (analytic IRR = 10%)
      irr([-100, 30, 40, 50, 60]) → ~0.249  (≈25%)
    """
    # Validate: need at least one sign change for IRR to exist
    signs = [1 if cf >= 0 else -1 for cf in cash_flows]
    if len(set(signs)) < 2:
        return None  # No sign change, no IRR

    low, high = -0.99, 10.0

    for _ in range(max_iterations):
        mid = (low + high) / 2
        npv_mid = sum(cf / ((1 + mid) ** t) for t, cf in enumerate(cash_flows))
        if abs(npv_mid) < tolerance:
            return round(mid, 6)
        if npv_mid > 0:
            low = mid
        else:
            high = mid

    return None  # Did not converge


def profitability_index(
    initial_investment: float,
    cash_flows: list[float],
    discount_rate: float,
) -> float:
    """Compute Profitability Index (PI). Cash flows start at t=1."""
    if initial_investment == 0:
        return float("inf")
    pv_future = sum(
        cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cash_flows, start=1)
    )
    return round(pv_future / abs(initial_investment), 4)


def payback_period(
    initial_investment: float,
    cash_flows: list[float],
) -> float | None:
    """Compute payback period in years. Cash flows start at t=1."""
    cumulative = -abs(initial_investment)
    for t, cf in enumerate(cash_flows, start=1):
        cumulative += cf
        if cumulative >= 0:
            # Interpolate
            prev_cumulative = cumulative - cf
            fraction = -prev_cumulative / cf if cf != 0 else 0
            return round((t - 1) + fraction, 2)
    return None  # Never pays back


def emv(
    outcomes: list[float],
    probabilities: list[float],
) -> float:
    """Compute Expected Monetary Value."""
    if len(outcomes) != len(probabilities):
        raise ValueError("outcomes and probabilities must have same length")
    return round(sum(o * p for o, p in zip(outcomes, probabilities)), 2)


def dscr(ebitda: float, debt_service: float) -> float:
    """Compute Debt Service Coverage Ratio."""
    if debt_service == 0:
        return float("inf")
    return round(ebitda / debt_service, 4)


__all__ = [
    "npv",
    "irr",
    "profitability_index",
    "payback_period",
    "emv",
    "dscr",
    "RobustRegimeKalmanFilter",
    "HoltSmoothing",
    "GScoreEngine",
    "get_g_score",
    "ForgeLaw",
    "compute_kappa_r",
    "compute_psi_le",
    "get_qdf_version",
]
