"""GOLD_WAVE_FORGE — challenger pipeline for XAUUSD wave-aware forecasting.

Public entry point: :func:`run_wave_forge`.

Status: SHADOW_CHALLENGER. The pipeline never promotes itself; the
888-JUDGE lane only emits USE / HOLD / QUARANTINE verdicts that the
human (or downstream F13) decides on.

Pipeline (8 agents, all receipted):

    000-CAUSALITY  gate the history (no leakage, sufficient span)
    111-DECOMPOSER wavelet + CEEMDAN
    222-WAVE-STATE amplitude/phase/frequency posterior + persistence
    333-PATH-FORGE continue validated modes 72h forward
    444-STABILITY  perturbation attacks (14/30/60/90-day lookback,
                   endpoint perturbation, regime stratification)
    555-AUDITOR    walk-forward M0 / M2 / M4-TREND / M4-WAVE
    888-JUDGE      USE / HOLD / QUARANTINE
    999-WITNESS    VAULT999 receipt

The output of :func:`run_wave_forge` is a :class:`WaveForecastResult`
that carries both the forecast path AND the admission verdict. The
admission rule is the load-bearing constraint:

    M4-WAVE must beat BOTH M0 (random walk) AND M4-TREND (trend only)
    on walk-forward pinball to be promoted from SHADOW_CHALLENGER.

    If M4-WAVE does not beat M2 (the existing sparse market-reality
    model), recommend SHADOW and refuse promotion — i.e. status stays
    SHADOW_CHALLENGER.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .agents import _000_causality as causality_mod
from .agents import _111_decomposer as decomposer_mod
from .agents import _222_wave_state as wave_state_mod
from .agents import _333_path_forge as path_forge_mod
from .agents import _444_stability as stability_mod
from .agents import _555_auditor as auditor_mod
from .agents import _888_judge as judge_mod
from .agents import _999_witness as witness_mod
from .synthetic import HistorySeries, get_xauusd_history


SCHEMA = "wealth.gold.wave_forge.v1"
STATUS = "SHADOW_CHALLENGER"


@dataclass
class WaveForecastResult:
    """The full challenger packet emitted by :func:`run_wave_forge`."""

    forecast_id: str = ""
    origin_time: str = ""
    issued_at: str = ""
    asset: str = "XAUUSD"
    causality: Optional["causality_mod.CausalityCertificate"] = None
    decomposition: Optional["decomposer_mod.DecompositionRecord"] = None
    wave_state: Optional["wave_state_mod.WaveStatePosterior"] = None
    path: Optional["path_forge_mod.ForgePath"] = None
    stability: Optional["stability_mod.StabilityReport"] = None
    audit: Optional["auditor_mod.AuditReport"] = None
    verdict: Optional["judge_mod.JudgeVerdict"] = None
    receipt: Optional["witness_mod.WitnessReceipt"] = None
    admission_failed_receipt: Optional[dict] = None
    status: str = STATUS
    admission: str = "FAIL"  # PASS | FAIL — admission test outcome

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": self.status,
            "admission": self.admission,
            "forecast_id": self.forecast_id,
            "origin_time": self.origin_time,
            "issued_at": self.issued_at,
            "asset": self.asset,
            "causality": self.causality.to_dict() if self.causality else None,
            "decomposition": self.decomposition.to_dict() if self.decomposition else None,
            "wave_state": self.wave_state.to_dict() if self.wave_state else None,
            "horizons": self.path.to_dict()["horizons"] if self.path else [],
            "endpoint_stability": self.path.to_dict()["endpoint_stability"] if self.path else None,
            "mode_persistence": self.path.to_dict()["mode_persistence"] if self.path else None,
            "amplitudes": self.path.to_dict()["amplitudes"] if self.path else None,
            "phases": self.path.to_dict()["phases"] if self.path else None,
            "frequencies": self.path.to_dict()["frequencies"] if self.path else None,
            "skill_vs_M0": self.audit.skill_vs_M0 if self.audit else None,
            "skill_vs_M2": self.audit.skill_vs_M2 if self.audit else None,
            "skill_vs_M4_TREND": self.audit.skill_vs_M4_TREND if self.audit else None,
            "regime": self.wave_state.regime if self.wave_state else "UNKNOWN",
            "stability": self.stability.to_dict() if self.stability else None,
            "audit": self.audit.to_dict() if self.audit else None,
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "admission_failed_receipt": self.admission_failed_receipt,
        }


def run_wave_forge(
    *,
    history: Optional[HistorySeries] = None,
    days: int = 730,
    seed: int = 1337,
    ensemble_size: int = 50,
    write_receipt: bool = True,
    receipts_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> WaveForecastResult:
    """Run the full 000→999 pipeline and return the challenger packet.

    Parameters
    ----------
    history
        Pre-fetched history. When None, calls
        :func:`get_xauusd_history` to load via the live cascade with
        synthetic fallback.
    days
        History length in days (only used when ``history is None``).
    seed
        RNG seed for the deterministic synthetic fallback (and the
        CEEMDAN ensemble).
    ensemble_size
        CEEMDAN ensemble realisations per IMF.
    write_receipt
        When True, the 999 lane writes a VAULT999 receipt.
    receipts_dir
        Override the VAULT999 receipts directory (mostly for tests).
    now
        Wall-clock override; defaults to UTC now.
    """
    issued_at = (now or datetime.now(timezone.utc)).isoformat()
    if history is None:
        history = get_xauusd_history(days=days, seed=seed)

    # ── 000 CAUSALITY ────────────────────────────────────────────────────
    cert = causality_mod.AGENT_000_Causality(history, now=now)

    # ── 111 DECOMPOSER ───────────────────────────────────────────────────
    decomp = decomposer_mod.AGENT_111_Decomposer(
        history,
        cert,
        ensemble_size=ensemble_size,
        seed=seed,
    )

    # ── 222 WAVE-STATE ───────────────────────────────────────────────────
    if decomp.ok:
        wave_state = wave_state_mod.AGENT_222_WaveState(decomp)
    else:
        wave_state = wave_state_mod.WaveStatePosterior(
            ok=False,
            failures=["decomposition_failed"],
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── 333 PATH-FORGE ───────────────────────────────────────────────────
    if wave_state.ok:
        path = path_forge_mod.AGENT_333_PathForge(history, wave_state, cert, now=now)
    else:
        path = path_forge_mod.ForgePath(
            ok=False,
            failures=["wave_state_failed"],
            origin_time=cert.origin_time,
            observed_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── 444 STABILITY ────────────────────────────────────────────────────
    stability_report = stability_mod.AGENT_444_Stability(
        history, decomp, path, cert, seed=seed
    )

    # ── 555 AUDITOR ──────────────────────────────────────────────────────
    audit = auditor_mod.AGENT_555_Auditor(
        history=history,
        wave_state=wave_state,
        path=path,
        stability=stability_report,
        cert=cert,
        seed=seed,
        now=now,
    )

    # ── 888 JUDGE ────────────────────────────────────────────────────────
    verdict = judge_mod.AGENT_888_Judge(
        cert=cert,
        decomp=decomp,
        wave_state=wave_state,
        path=path,
        stability=stability_report,
        audit=audit,
    )

    forecast_id = f"gold-wave-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{seed:04x}"

    # ── 999 WITNESS ──────────────────────────────────────────────────────
    receipt_obj: Optional["witness_mod.WitnessReceipt"] = None
    if write_receipt:
        packet_preview = {
            "forecast_id": forecast_id,
            "origin_time": cert.origin_time,
            "issued_at": issued_at,
            "status": STATUS,
            "verdict": verdict.verdict,
        }
        receipt_obj = witness_mod.AGENT_999_Witness(
            packet_preview,
            forecast_id=forecast_id,
            receipts_dir=receipts_dir,
        )

    admission = "PASS" if verdict.verdict == "USE" else "FAIL"

    # Honest admission-failure receipt — when the challenger fails the
    # admission rule (does not beat M2) we write a dedicated receipt so
    # the audit trail records the negative result, not just the absence
    # of a USE verdict.
    admission_failed_receipt: Optional[dict] = None
    if (
        write_receipt
        and audit is not None
        and audit.ok
        and audit.skill_vs_M2 <= 0.0
    ):
        from .admission_receipt import write_admission_rule_failed_receipt

        admission_failed_receipt = write_admission_rule_failed_receipt(
            forecast_id=forecast_id,
            skill_vs_M0=audit.skill_vs_M0,
            skill_vs_M2=audit.skill_vs_M2,
            skill_vs_M4_TREND=audit.skill_vs_M4_TREND,
            n_windows=audit.n_windows,
            verdict_reason=verdict.reason_codes[0] if verdict.reason_codes else "",
            receipts_dir=receipts_dir,
        )

    return WaveForecastResult(
        forecast_id=forecast_id,
        origin_time=cert.origin_time,
        issued_at=issued_at,
        causality=cert,
        decomposition=decomp,
        wave_state=wave_state,
        path=path,
        stability=stability_report,
        audit=audit,
        verdict=verdict,
        receipt=receipt_obj,
        admission_failed_receipt=admission_failed_receipt,
        status=STATUS,
        admission=admission,
    )


__all__ = [
    "SCHEMA",
    "STATUS",
    "WaveForecastResult",
    "run_wave_forge",
]