"""M7.0 — orchestrator: wire M7.1 → M7.7 into a single survival packet.

Public entry point: :func:`run_m7`.

M7's job is NOT to predict gold. It is to decide whether a forecast
(someone else's — typically M5) can SAFELY become a position. Inputs:

    m5_forecast        — dict from run_m5() or the JSON on disk
    side               — "LONG" / "SHORT" / "FLAT"
    entry, stop, target — absolute price levels
    leverage           — proposed leverage multiple
    margin_buffer      — distance from entry to margin call (fraction)
    spread_bps,
    slippage_bps,
    adv_usd            — liquidation cost inputs
    notional_usd       — proposed notional
    equity_usd         — account equity
    max_acceptable_loss_usd — the user's loss ceiling (in USD)
    horizon_h          — M5 horizon (1, 6, 24, 72)
    f_signal,
    t_signal,
    d_signal           — disagreement organ signals (-1 .. 1)
    disagreement_series — historical disagreement magnitudes for M7.6
    edge_log           — log-return edge per period (from upstream)
    sigma_log          — log-return sigma per period
    alpha              — survival-prob threshold (default 0.10)

Outputs (see :class:`M7Result`):

    probability_of_margin_breach
    probability_of_stop_before_target
    expected_shortfall                (CVaR)
    liquidation_cost_bps,
    liquidation_cost_usd
    maximum_survivable_size_usd
    thesis_half_life_bars
    size_multiplier
    verdict                           (ACT / REDUCE / HOLD / BLOCK)

Laws
----

* NO FORECAST — M7 inherits a forecast from M5 and does not modify it.
* HONEST VERDICT — if any module returns data_insufficient=True,
  M7.7 escalates to HOLD, never fabricates numbers to authorise a trade.
* REVERSIBLE — every output is recomputable from its inputs.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import numpy as np

from .abstention_gate import (
    DEFAULT_ALPHA,
    REGIME_ACTION_TABLE,
    SafetyGateVerdict,
    decide_safety_gate,
)
from .disagreement import (
    DISAGREEMENT_DEFAULT,
    DisagreementVector,
    assess_disagreement,
)
from .expected_shortfall import CVaRResult, compute_cvar
from .leverage_stress import LeverageStressResult, compute_margin_breach_probability
from .liquidation_cost import (
    DEFAULT_ADV_USD,
    DEFAULT_SLIPPAGE_BPS,
    DEFAULT_SPREAD_BPS,
    LiquidationCostResult,
    compute_liquidation_cost,
)
from .max_survivable_size import (
    KELLY_FRACTION_OF_RAW,
    MaxSurvivableSizeResult,
    compute_max_survivable_size,
)
from .stop_risk import StopRiskResult, compute_stop_risk
from .thesis_half_life import ThesisHalfLifeResult, compute_thesis_half_life


M7_SCHEMA = "wealth.gold.m7.v1"
M7_STATUS = "SHADOW_OPERATIONAL"

# Authority tuple — what M7 may and may NOT do.
M7_AUTHORITY = {
    "may_reduce_size": True,
    "may_block_trade": True,
    "may_increase_size": False,
    "may_override_human": False,
}

DEFAULT_VAULT = Path(
    os.getenv("VAULT999_M7_RECEIPTS", "/root/AAA/VAULT999/receipts")
)

Side = Literal["LONG", "SHORT", "FLAT"]


@dataclass(frozen=True)
class M7Result:
    forecast_id: str
    origin_time: str
    issued_at: str
    asset: str
    data_source: str
    data_is_synthetic: bool
    side: str
    horizon_h: int
    last_close: float

    # Sub-module results
    leverage_stress: Optional[LeverageStressResult] = None
    stop_risk: Optional[StopRiskResult] = None
    cvar: Optional[CVaRResult] = None
    liquidation_cost: Optional[LiquidationCostResult] = None
    max_survivable_size: Optional[MaxSurvivableSizeResult] = None
    thesis_half_life: Optional[ThesisHalfLifeResult] = None
    disagreement: Optional[DisagreementVector] = None
    safety_gate: Optional[SafetyGateVerdict] = None

    # Final outputs (mirrored for the spec's required field names)
    probability_of_margin_breach: float = float("nan")
    probability_of_stop_before_target: float = float("nan")
    expected_shortfall: float = float("nan")           # CVaR in price units
    liquidation_cost_bps: float = float("nan")
    liquidation_cost_usd: float = float("nan")
    maximum_survivable_size_usd: float = float("nan")
    thesis_half_life_bars: float = float("nan")
    size_multiplier: float = 0.0
    verdict: str = "HOLD"

    # Provenance
    schema: str = M7_SCHEMA
    status: str = M7_STATUS
    authority: dict = field(default_factory=lambda: dict(M7_AUTHORITY))
    reason_codes: list[str] = field(default_factory=list)
    honest_verdict: str = ""
    caveats: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        out = {
            "schema": self.schema,
            "status": self.status,
            "authority": self.authority,
            "forecast_id": self.forecast_id,
            "origin_time": self.origin_time,
            "issued_at": self.issued_at,
            "asset": self.asset,
            "data_source": self.data_source,
            "data_is_synthetic": self.data_is_synthetic,
            "side": self.side,
            "horizon_h": self.horizon_h,
            "last_close": self.last_close,
            "probability_of_margin_breach": self.probability_of_margin_breach,
            "probability_of_stop_before_target": self.probability_of_stop_before_target,
            "expected_shortfall": self.expected_shortfall,
            "liquidation_cost_bps": self.liquidation_cost_bps,
            "liquidation_cost_usd": self.liquidation_cost_usd,
            "maximum_survivable_size_usd": self.maximum_survivable_size_usd,
            "thesis_half_life_bars": self.thesis_half_life_bars,
            "size_multiplier": self.size_multiplier,
            "verdict": self.verdict,
            "reason_codes": self.reason_codes,
            "caveats": self.caveats,
            "honest_verdict": self.honest_verdict,
        }
        # Sub-module dicts (None-safe)
        if self.leverage_stress is not None:
            out["leverage_stress"] = self.leverage_stress.to_dict()
        if self.stop_risk is not None:
            out["stop_risk"] = self.stop_risk.to_dict()
        if self.cvar is not None:
            out["cvar"] = self.cvar.to_dict()
        if self.liquidation_cost is not None:
            out["liquidation_cost"] = self.liquidation_cost.to_dict()
        if self.max_survivable_size is not None:
            out["max_survivable_size"] = self.max_survivable_size.to_dict()
        if self.thesis_half_life is not None:
            out["thesis_half_life"] = self.thesis_half_life.to_dict()
        if self.disagreement is not None:
            out["disagreement"] = self.disagreement.to_dict()
        if self.safety_gate is not None:
            out["safety_gate"] = self.safety_gate.to_dict()
        return out


def _pick_m5_horizon(m5_forecast: dict, horizon_h: int) -> Optional[dict]:
    horizons = m5_forecast.get("horizons") or []
    for h in horizons:
        if int(h.get("horizon_h", -1)) == int(horizon_h):
            return h
    return None


def _default_m5_horizon_quantiles(m5_forecast: dict, horizon_h: int) -> Optional[dict]:
    """Fallback quantiles if the requested horizon is missing.

    We don't fabricate — if the horizon isn't present we return None
    and let M7 default to HOLD.
    """
    return _pick_m5_horizon(m5_forecast, horizon_h)


def _implied_edge_sigma_from_m5(
    m5_horizon: dict, side: str
) -> tuple[float, float]:
    """Derive (edge_log, sigma_log) from the M5 horizon for Kelly sizing.

    edge_log is the log-return edge per period (signed).
    sigma_log is the per-period log vol.

    M5 doesn't emit an edge — the edge comes from upstream signals. The
    default edge here is 0 (no edge). Callers should pass an explicit
    ``edge_log`` if they have one.
    """
    p10 = m5_horizon.get("p10")
    p50 = m5_horizon.get("p50")
    p90 = m5_horizon.get("p90")
    sigma_h = m5_horizon.get("sigma_h")
    if not all(isinstance(x, (int, float)) for x in (p10, p50, p90, sigma_h)):
        return 0.0, float("nan")
    if not all(np.isfinite(x) for x in (p10, p50, p90, sigma_h)):
        return 0.0, float("nan")
    if sigma_h <= 0:
        return 0.0, float("nan")
    # Default edge = 0. M7 is not a forecaster.
    return 0.0, float(sigma_h)


def run_m7(
    *,
    m5_forecast: dict,
    side: str = "FLAT",
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    leverage: float = 1.0,
    margin_buffer: float = 0.20,
    horizon_h: int = 24,
    # Liquidation cost inputs
    notional_usd: float = 0.0,
    equity_usd: float = 100_000.0,
    spread_bps: float = DEFAULT_SPREAD_BPS,
    slippage_bps: float = DEFAULT_SLIPPAGE_BPS,
    adv_usd: float = DEFAULT_ADV_USD,
    urgency: str = "normal",
    participation_rate: Optional[float] = None,
    # Risk ceiling
    max_acceptable_loss_usd: float = 5_000.0,
    # Disagreement signals (-1..1)
    f_signal: float = 0.0,
    t_signal: float = 0.0,
    d_signal: float = 0.0,
    # Thesis half-life
    disagreement_series: Optional[list[float]] = None,
    # Kelly sizing
    edge_log: Optional[float] = None,
    sigma_log: Optional[float] = None,
    # Survival threshold
    alpha: float = DEFAULT_ALPHA,
) -> M7Result:
    """Run M7 — Survival and Path-Risk decision.

    Returns an :class:`M7Result` whose verdict ∈ {ACT, REDUCE, HOLD, BLOCK}.
    """
    issued_at = datetime.now(timezone.utc).isoformat()
    forecast_id = m5_forecast.get("forecast_id") or f"m7-{int(datetime.now(timezone.utc).timestamp())}"

    # Provenance from M5
    origin_time = m5_forecast.get("origin_time") or issued_at
    asset = m5_forecast.get("asset") or "XAUUSD"
    data_source = m5_forecast.get("data_source") or "UNKNOWN"
    data_is_synthetic = bool(m5_forecast.get("data_is_synthetic"))
    last_close = float(m5_forecast.get("last_close") or float("nan"))
    m5_horizon = _default_m5_horizon_quantiles(m5_forecast, horizon_h)
    if m5_horizon is None and np.isfinite(last_close) and last_close > 0:
        # If the requested horizon is missing, fall back to nearest
        horizons = m5_forecast.get("horizons") or []
        if horizons:
            nearest = min(horizons, key=lambda h: abs(int(h.get("horizon_h", 0)) - horizon_h))
            m5_horizon = nearest

    caveats: list[str] = []
    reason_codes: list[str] = []

    # Disagreement (F/T/D preservation)
    disagreement = assess_disagreement(f_value=f_signal, t_value=t_signal, d_value=d_signal)
    strong_disagreement = bool(disagreement.reasons and "strong_disagreement" in disagreement.reasons)

    # 7.1 leverage_stress
    lev_stress = None
    if m5_horizon is not None:
        lev_stress = compute_margin_breach_probability(
            m5_horizon=m5_horizon,
            side=side,
            leverage=leverage,
            margin_buffer=margin_buffer,
            horizon_h=horizon_h,
        )
    p_margin_breach = lev_stress.p_margin_breach if lev_stress else float("nan")

    # 7.2 stop_risk
    stop_res = None
    if (entry is not None) and (stop is not None) and (target is not None) and (m5_horizon is not None):
        sigma_h = float(m5_horizon.get("sigma_h", float("nan")))
        if not np.isfinite(sigma_h):
            sigma_h = 0.0
        stop_res = compute_stop_risk(
            side=side,
            entry=float(entry),
            stop=float(stop),
            target=float(target),
            sigma_path=max(sigma_h, 1e-8),
        )
    p_stop_first = stop_res.p_stop_before_target if stop_res else float("nan")

    # 7.3 expected_shortfall (CVaR)
    cvar_res = None
    if m5_horizon is not None:
        cvar_res = compute_cvar(m5_horizon=m5_horizon, side=side, horizon_h=horizon_h, alpha=0.05)
    cvar_price = cvar_res.cvar_alpha if cvar_res else float("nan")
    # CVaR in USD ≈ cvar_price * notional_shares (USD/price)
    if np.isfinite(cvar_price) and last_close and last_close > 0 and notional_usd > 0:
        cvar_usd = float(cvar_price * notional_usd / last_close)
    else:
        cvar_usd = float("nan")
    cvar_exceeds_max_loss = bool(
        np.isfinite(cvar_usd) and np.isfinite(max_acceptable_loss_usd) and cvar_usd > max_acceptable_loss_usd
    )

    # 7.4 liquidation_cost
    liq_res = None
    if notional_usd > 0:
        liq_res = compute_liquidation_cost(
            notional_usd=notional_usd,
            adv_usd=adv_usd,
            spread_bps=spread_bps,
            slippage_bps=slippage_bps,
            urgency=urgency,
            participation_rate=participation_rate,
        )
    participation_above_50pct = bool(
        liq_res is not None and liq_res.participation_pct > 50.0
    )

    # 7.6 thesis_half_life (need the disagreement series)
    hl_res = None
    if disagreement_series:
        hl_res = compute_thesis_half_life(disagreement_series=disagreement_series)

    # Half-life penalty: clamp persistence_score into (0, 1]
    half_life_penalty = 1.0
    if hl_res is not None and np.isfinite(hl_res.persistence_score):
        half_life_penalty = float(max(0.0, min(1.0, hl_res.persistence_score)))

    # 7.5 max_survivable_size
    mss = None
    if equity_usd > 0:
        # Derive edge / sigma if not given.
        if edge_log is None or sigma_log is None:
            if m5_horizon is not None:
                default_edge, default_sigma = _implied_edge_sigma_from_m5(m5_horizon, side)
                if edge_log is None:
                    edge_log = default_edge
                if sigma_log is None or not np.isfinite(sigma_log):
                    sigma_log = default_sigma
            else:
                if edge_log is None:
                    edge_log = 0.0
                if sigma_log is None:
                    sigma_log = float("nan")

        # survival probability = 1 - p_margin_breach
        if np.isfinite(p_margin_breach):
            survival_prob = max(0.0, min(1.0, 1.0 - p_margin_breach))
        else:
            survival_prob = 0.0
            caveats.append("p_margin_breach_nan_survival_zero")

        # Apply disagreement's size_multiplier.
        size_disc_mult = float(disagreement.size_multiplier)

        mss = compute_max_survivable_size(
            edge_log=float(edge_log),
            sigma_log=float(sigma_log) if np.isfinite(sigma_log) else float("nan"),
            survival_prob=survival_prob,
            equity_usd=float(equity_usd),
            round_trip_cost_bps=float(liq_res.total_cost_bps) if liq_res else 0.0,
            disagreement_penalty=size_disc_mult,
            half_life_penalty=half_life_penalty,
        )

    # 7.7 safety_gate
    # data_insufficient: any required module returned data_insufficient=True
    data_insufficient = any([
        lev_stress is not None and lev_stress.data_insufficient,
        stop_res is not None and stop_res.data_insufficient,
        cvar_res is not None and cvar_res.data_insufficient,
        liq_res is not None and liq_res.data_insufficient,
        mss is not None and mss.data_insufficient,
        hl_res is not None and hl_res.data_insufficient,
    ])
    if m5_horizon is None:
        data_insufficient = True
        caveats.append("m5_horizon_missing")

    # M5.7 regime label — fall back to RANGE if unknown
    m5_regime = (m5_forecast.get("abstention") or {}).get("regime") or "RANGE"

    safety_gate = decide_safety_gate(
        regime=str(m5_regime),
        p_margin_breach=float(p_margin_breach) if np.isfinite(p_margin_breach) else 0.5,
        p_stop_before_target=float(p_stop_first) if np.isfinite(p_stop_first) else 0.0,
        cvar_exceeds_max_loss=bool(cvar_exceeds_max_loss),
        participation_above_50pct=bool(participation_above_50pct),
        strong_disagreement=bool(strong_disagreement),
        data_insufficient=bool(data_insufficient),
        alpha=float(alpha),
        flat_position=(side == "FLAT"),
    )

    # Final size_multiplier = safety_gate.size_multiplier × Kelly fraction (if available)
    final_size = float(safety_gate.size_multiplier)
    if mss is not None and np.isfinite(mss.max_survivable_size_usd) and equity_usd > 0:
        # M7 may not INCREASE size — multiply, never replace.
        kelly_pct = float(mss.kelly_fraction_final)
        kelly_pct = max(0.0, min(1.0, kelly_pct))
        final_size = float(safety_gate.size_multiplier * kelly_pct)
    elif mss is not None:
        # Kelly data insufficient — fall back to safety_gate size only.
        caveats.append("kelly_data_insufficient_size_from_safety_gate_only")
    else:
        # No Kelly at all — safety_gate size only.
        caveats.append("no_kelly_input_size_from_safety_gate_only")

    final_size = max(0.0, min(1.0, final_size))
    if safety_gate.verdict == "BLOCK":
        final_size = 0.0

    # Reason codes: combine sub-module + safety gate
    reason_codes.extend(safety_gate.reason_codes)
    if lev_stress is not None and lev_stress.reasons:
        reason_codes.extend(["leverage_stress:" + r for r in lev_stress.reasons])
    if stop_res is not None and stop_res.reasons:
        reason_codes.extend(["stop_risk:" + r for r in stop_res.reasons])
    if mss is not None and mss.reasons:
        reason_codes.extend(["max_survivable_size:" + r for r in mss.reasons])
    if liq_res is not None and liq_res.reasons:
        reason_codes.extend(["liquidation_cost:" + r for r in liq_res.reasons])
    if disagreement.reasons:
        reason_codes.extend(["disagreement:" + r for r in disagreement.reasons])

    # Honest verdict — narrative summary
    verdict_text = (
        f"M7 verdict={safety_gate.verdict} size_multiplier={final_size:.3f} "
        f"regime={m5_regime} survival_p={safety_gate.survival_prob:.3f} "
        f"p_margin_breach={p_margin_breach if np.isfinite(p_margin_breach) else float('nan')} "
        f"p_stop_first={p_stop_first if np.isfinite(p_stop_first) else float('nan')}. "
        f"M7 does not predict gold — it only decides whether the M5 forecast "
        f"can safely become a position. The sovereign still decides."
    )

    return M7Result(
        forecast_id=str(forecast_id),
        origin_time=str(origin_time),
        issued_at=issued_at,
        asset=str(asset),
        data_source=str(data_source),
        data_is_synthetic=bool(data_is_synthetic),
        side=str(side),
        horizon_h=int(horizon_h),
        last_close=last_close,
        leverage_stress=lev_stress,
        stop_risk=stop_res,
        cvar=cvar_res,
        liquidation_cost=liq_res,
        max_survivable_size=mss,
        thesis_half_life=hl_res,
        disagreement=disagreement,
        safety_gate=safety_gate,
        probability_of_margin_breach=float(p_margin_breach) if np.isfinite(p_margin_breach) else float("nan"),
        probability_of_stop_before_target=float(p_stop_first) if np.isfinite(p_stop_first) else float("nan"),
        expected_shortfall=float(cvar_price) if np.isfinite(cvar_price) else float("nan"),
        liquidation_cost_bps=float(liq_res.total_cost_bps) if liq_res else float("nan"),
        liquidation_cost_usd=float(liq_res.total_cost_usd) if liq_res else float("nan"),
        maximum_survivable_size_usd=float(mss.max_survivable_size_usd) if mss else float("nan"),
        thesis_half_life_bars=float(hl_res.half_life_bars) if hl_res else float("nan"),
        size_multiplier=float(final_size),
        verdict=str(safety_gate.verdict),
        reason_codes=list(reason_codes),
        caveats=list(caveats),
        honest_verdict=verdict_text,
    )


def write_m7_receipt(
    m7_result: M7Result,
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write a JSON receipt for the M7 verdict."""
    import hashlib
    import json

    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-m7-{m7_result.verdict.lower()}-{m7_result.forecast_id}-{stamp}"
    body = m7_result.to_dict()
    body["receipt_subtype"] = f"survival_verdict_{m7_result.verdict.lower()}"
    body["receipt_id"] = receipt_id
    text = json.dumps(body, indent=2, sort_keys=False)
    path = target / f"{receipt_id}.json"
    path.write_text(text, encoding="utf-8")
    return {
        "receipt_id": receipt_id,
        "receipt_uri": str(path),
        "written": True,
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
    }


__all__ = [
    "M7Result",
    "M7_SCHEMA",
    "M7_STATUS",
    "M7_AUTHORITY",
    "Side",
    "run_m7",
    "write_m7_receipt",
    "DEFAULT_VAULT",
    "DEFAULT_SPREAD_BPS",
    "DEFAULT_SLIPPAGE_BPS",
    "DEFAULT_ADV_USD",
    "DEFAULT_ALPHA",
    "REGIME_ACTION_TABLE",
]
