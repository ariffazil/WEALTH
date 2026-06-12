"""
WEALTH Stock Analysis — D4 Domain Layer
════════════════════════════════════════

Capital-risk and stock-analysis governance tools.
Not a trading coach. Not a stock promoter. Not a buy/sell oracle.

Verdicts:    SAFE_TO_STUDY | NEEDS_DATA | UNSAFE | 888_HOLD | MATH_ERROR
Authority:   WEALTH computes. arifOS judges. Arif decides.
Boundary:    recommendation_only=True, final_authority="Arif"

DITEMPA BUKAN DIBERI — Stock evidence is forged, not given.
"""

from __future__ import annotations

from .math_tools import (
    verify_trade_math,
    separate_realized_unrealized,
    calculate_position_size,
    calculate_r_multiple,
)
from .risk_tools import (
    check_portfolio_exposure,
    apply_bursa_cost_model,
)
from .behavior_tools import (
    detect_tamak_behavior,
    pre_trade_gate,
)
from .fundamentals import (
    check_fundamental_invariants,
)
from .technical import (
    run_tac9_engine,
)
from .contrast import (
    detect_anomalous_contrast,
    detect_false_confluence,
)
from .governance_singularity import (
    detect_governance_singularity,
)

__all__ = [
    "verify_trade_math",
    "separate_realized_unrealized",
    "calculate_position_size",
    "calculate_r_multiple",
    "check_portfolio_exposure",
    "apply_bursa_cost_model",
    "detect_tamak_behavior",
    "pre_trade_gate",
    "check_fundamental_invariants",
    "run_tac9_engine",
    "detect_anomalous_contrast",
    "detect_false_confluence",
    "detect_governance_singularity",
]
