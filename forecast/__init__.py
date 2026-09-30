"""WEALTH forecast — 7-agent forecast orchestration layer (wealth.gold.orchestration.v1).

Wraps the existing gold forecast engine (engines/commodity/gold-api/fetch_gold.py
cmd_forecast, served at localhost:3456/api/gold/forecast) with an explicit
agent discipline per arifOS doctrine:

    000 Integrity   — fetch + validate live inputs (ticker / apex / macro / forecast)
    111 Regime      — classify market regime from observed data
    333 Forecast    — extract quantile cone path at target horizons
    555 Calibration — evaluate forecast calibration state (SHADOW until
                      a walk-forward harness exists)
    777 Translator  — emit stance candidates (trade + physical saving)
    888 Judge       — final verdict: ACT / WAIT / HOLD / BLOCKED
    999 Witness     — write receipt to /root/AAA/VAULT999/receipts/

Laws binding this layer:
  - NO FAKE OHLC. Every number traces to a live endpoint or a recorded receipt.
  - Default status = SHADOW. Execution disabled, human confirmation required,
    until 555-ASI calibration is ratified (walk-forward harness present).
  - Importable, never run-on-load. Call run_orchestration() explicitly.
  - Does not modify anything under /root/WEALTH/wealth_core/.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from .event_sentinel import (
    EVENT_RISK_STATES,
    EventSentinelState,
    compute_event_risk_state,
)
from .m2 import (
    M2_REGIME_STATES,
    RegimePosterior,
    compute_regime_posterior,
)

# Import the full module so we can patch `.stamp()` onto every result
# dataclass in one place. The module's public API is re-exported below.
from .orchestrator import (
    AGENT_000_Integrity,
    AGENT_111_Regime,
    AGENT_333_Forecast,
    AGENT_555_Calibration,
    AGENT_777_Translator,
    AGENT_888_Judge,
    AGENT_999_Witness,
    OrchestrationResult,
    run_orchestration,
    GoldAPIClient,
    DEFAULT_ROUND_TRIP_COST_BPS,
    STATUS_SHADOW,
    TARGET_HORIZON_HOURS,
    VALID_REGIMES,
    VALID_VERDICTS,
    InputBundle,
    RegimeState,
    HorizonSet,
    CalibrationState,
    TranslatorOutput,
    JudgeVerdict,
    WitnessReceipt,
)


# Each agent result dataclass carries an `envelope: AgentEnvelope`. Stamp the
# envelope and return the host so every agent function has a uniform tail
# pattern. Bound once at import; idempotent on reload.
def _bind_stamp(cls):
    if hasattr(cls, "stamp"):
        return cls
    def _stamp(self):
        env = getattr(self, "envelope", None)
        if env is not None and hasattr(env, "stamp"):
            env.stamp()
        return self
    _stamp.__name__ = "stamp"
    _stamp.__qualname__ = f"{cls.__name__}.stamp"
    cls.stamp = _stamp
    return cls


for _cls in (
    InputBundle,
    RegimeState,
    HorizonSet,
    CalibrationState,
    TranslatorOutput,
    JudgeVerdict,
    WitnessReceipt,
):
    _bind_stamp(_cls)
del _cls, _bind_stamp


__all__ = [
    "AGENT_000_Integrity",
    "AGENT_111_Regime",
    "AGENT_333_Forecast",
    "AGENT_555_Calibration",
    "AGENT_777_Translator",
    "AGENT_888_Judge",
    "AGENT_999_Witness",
    "OrchestrationResult",
    "run_orchestration",
    "GoldAPIClient",
    "DEFAULT_ROUND_TRIP_COST_BPS",
    "STATUS_SHADOW",
    "TARGET_HORIZON_HOURS",
    "VALID_REGIMES",
    "VALID_VERDICTS",
    "InputBundle",
    "RegimeState",
    "HorizonSet",
    "CalibrationState",
    "TranslatorOutput",
    "JudgeVerdict",
    "WitnessReceipt",
    # v1.1 — event sentinel + M2 cross-asset regime
    "EVENT_RISK_STATES",
    "EventSentinelState",
    "compute_event_risk_state",
    "M2_REGIME_STATES",
    "RegimePosterior",
    "compute_regime_posterior",
]
