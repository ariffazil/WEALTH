"""
WEALTH Optimizers — Mathematical Optimization Engines.

APEX-integrated optimization engines bridging MO-book patterns
to the arifOS federation governance framework.

Engines:
  - markowitz_frontier: Mean-variance portfolio (Reality organ)
  - kelly_sizing: Kelly criterion bet sizing (Execution organ)
  - robust_portfolio: Robust optimization under uncertainty (Governance organ)
  - chance_constrained: VaR/CVaR optimization (Witness organ)
  - two_stage_recourse: Two-stage stochastic program (Memory organ)

Each engine returns APEX verdicts and enforces F1-F13 floors.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from .markowitz import markowitz_frontier, markowitz_frontier_sweep
from .kelly import kelly_sizing
from .robust import robust_portfolio
from .chance_constrained import chance_constrained, cvar_portfolio
from .two_stage import two_stage_recourse, production_planning_example
from .apex_mapping import (
    APEXOrgan,
    APEXVerdict,
    APEXScore,
    APEXResult,
    FloorCheck,
    compute_apex_verdict,
    get_optimizer_mapping,
    OPTIMIZER_APEX_MAP,
)

__all__ = [
    # Engines
    "markowitz_frontier",
    "markowitz_frontier_sweep",
    "kelly_sizing",
    "robust_portfolio",
    "chance_constrained",
    "cvar_portfolio",
    "two_stage_recourse",
    "production_planning_example",
    # APEX governance
    "APEXOrgan",
    "APEXVerdict",
    "APEXScore",
    "APEXResult",
    "FloorCheck",
    "compute_apex_verdict",
    "get_optimizer_mapping",
    "OPTIMIZER_APEX_MAP",
]
