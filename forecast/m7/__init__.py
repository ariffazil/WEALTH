"""M7 — Survival and Path-Risk organ for XAUUSD positions.

Status: SHADOW_OPERATIONAL (M7 does not predict; it refuses).

M7 is NOT a directional oracle and does NOT compete with M0/M5 on
forecasting quality. Its single mission is:

    SURVIVE_THE_PATH

Given an M5 distribution forecast + a candidate position, M7 decides
whether the forecast can SAFELY become a position. It enforces the
constraint:

    P(margin breach before thesis resolution) < alpha

and emits one of four verdicts:

    ACT     — proceed at proposed size (or scaled size)
    REDUCE  — proceed only at reduced size (size_multiplier < 1)
    HOLD    — do not act now (insufficient evidence / disagreement)
    BLOCK   — refuse (survival probability below alpha)

M7 has four powers, no more:

    may_reduce_size   = True
    may_block_trade   = True
    may_increase_size = False   (sovereign's call only)
    may_override_human = False  (sovereign decides)

Submodules
----------

    7.1 leverage_stress      — P(margin breach) at given leverage from M5
    7.2 stop_risk            — P(stop hit before target)
    7.3 expected_shortfall   — CVaR at confidence level
    7.4 liquidation_cost     — spread + market-impact estimate
    7.5 max_survivable_size  — Kelly criterion × survival probability
    7.6 thesis_half_life     — autocorrelation decay of disagreement signal
    7.7 abstention_gate      — ACT/REDUCE/HOLD/BLOCK verdict engine

Constitutional rule
-------------------

    Fundamentals propose value.
    Price reveals acceptance.
    Flow reveals pressure.
    The distribution measures uncertainty.
    M7 determines survivability.
    The judge may permit or refuse—but only the sovereign decides.

Disagreement protocol
---------------------

If the F / T / D organs disagree, M7 widens the safety envelope:

    confidence DOWN
    interval_width UP
    position_size DOWN
    review_frequency UP

M7 never merges contradictory organs into a single score. The
disagreement vector is itself a survival input (module 7.6).

Laws binding M7
---------------

* NO FORECAST — M7 does not predict gold. It only decides whether a
  proposed trade survives the path implied by someone else's forecast.
* HONEST VERDICT — if a survival input is missing or untrustworthy,
  default to HOLD (never fabricate a number to allow a trade).
* RECEIPTS — every verdict writes a receipt; HOLD and BLOCK write
  receipts with reason_codes even though no action was taken.
* REVERSIBLE — every M7 output is recomputable from its inputs.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from .abstention_gate import (
    VERDICTS,
    RegimeAction,
    SafetyGateVerdict,
    decide_safety_gate,
    REGIME_ACTION_TABLE,
)
from .disagreement import (
    DISAGREEMENT_DEFAULT,
    DisagreementVector,
    assess_disagreement,
    widen_for_disagreement,
)
from .engine import (
    M7Result,
    M7_SCHEMA,
    M7_STATUS,
    M7_AUTHORITY,
    run_m7,
    write_m7_receipt,
)
from .expected_shortfall import CVaRResult, compute_cvar
from .leverage_stress import (
    LeverageStressResult,
    compute_margin_breach_probability,
)
from .liquidation_cost import LiquidationCostResult, compute_liquidation_cost
from .max_survivable_size import (
    MaxSurvivableSizeResult,
    compute_max_survivable_size,
)
from .receipts import write_safety_gate_receipt, write_honest_caveat_receipt
from .stop_risk import StopRiskResult, compute_stop_risk
from .thesis_half_life import ThesisHalfLifeResult, compute_thesis_half_life


__all__ = [
    # Core types
    "M7Result",
    "M7_SCHEMA",
    "M7_STATUS",
    "M7_AUTHORITY",
    "run_m7",
    "write_m7_receipt",
    # Sub-module results
    "LeverageStressResult",
    "StopRiskResult",
    "CVaRResult",
    "LiquidationCostResult",
    "MaxSurvivableSizeResult",
    "ThesisHalfLifeResult",
    "SafetyGateVerdict",
    "RegimeAction",
    "DisagreementVector",
    # Public functions
    "compute_margin_breach_probability",
    "compute_stop_risk",
    "compute_cvar",
    "compute_liquidation_cost",
    "compute_max_survivable_size",
    "compute_thesis_half_life",
    "assess_disagreement",
    "widen_for_disagreement",
    "decide_safety_gate",
    "write_safety_gate_receipt",
    "write_honest_caveat_receipt",
    # Constants
    "VERDICTS",
    "REGIME_ACTION_TABLE",
    "DISAGREEMENT_DEFAULT",
]
