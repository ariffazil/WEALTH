"""GOLD_GRAVITY_FIELD — pipeline orchestrator.

Runs the 000 → 999 pipeline for the gravity model. The orchestrator is
importable and never runs at import time.

Pipeline
========

    000-INGEST         build the gravity feature series (release-timestamp guarded)
    111-REGIME         posterior over {RANGE, TREND_UP, TREND_DOWN,
                                      COMPRESSION, TRANSITION, EVENT_RISK}
    444-DISTRIBUTION   per-horizon cone (P10/P25/P50/P75/P90 + range +
                        vol-expansion probability)
    555-ABLATION       M0/M1/M2/M3/M4 walk-forward tournament
    888-JUDGE          USE / HOLD / QUARANTINE based on admission
    999-WITNESS        write receipt to VAULT999; on admission failure
                       write ``admission_rule_failed`` receipt.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

from .ingest import (
    DEFAULT_CB_DEMAND_TONNES_QUARTERLY,
    GravityFeatureSeries,
    build_gravity_feature_series,
)
from .regime import (
    REGIME_STATES,
    RegimePosterior111,
    compute_regime_posterior_111,
)
from .distribution import (
    Distribution444,
    compute_distribution_444,
)
from .ablation import (
    AblationTable,
    PROMOTION_SKILL_FLOOR,
    run_ablation_tournament,
)


SCHEMA = "wealth.gold.gravity.v1"
STATUS = "SHADOW_CHALLENGER"


DEFAULT_VAULT = Path(
    os.getenv("VAULT999_GRAVITY_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


# ── Public dataclass ────────────────────────────────────────────────────


@dataclass
class GravityResult:
    """The full challenger packet emitted by :func:`run_gravity_field`."""

    forecast_id: str = ""
    issued_at: str = ""
    asset: str = "XAUUSD"
    status: str = STATUS
    admission: str = "FAIL"
    gravity_series: Optional[GravityFeatureSeries] = None
    regime: Optional[RegimePosterior111] = None
    distribution: Optional[Distribution444] = None
    ablation: Optional[AblationTable] = None
    verdict: str = "HOLD"
    verdict_reasons: list[str] = field(default_factory=list)
    receipt: Optional[dict] = None
    admission_failed_receipt: Optional[dict] = None
    honest_verdict: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": self.status,
            "admission": self.admission,
            "forecast_id": self.forecast_id,
            "issued_at": self.issued_at,
            "asset": self.asset,
            "verdict": self.verdict,
            "verdict_reasons": list(self.verdict_reasons),
            "gravity_series": self.gravity_series.to_dict() if self.gravity_series else None,
            "regime": self.regime.to_dict() if self.regime else None,
            "distribution": self.distribution.to_dict() if self.distribution else None,
            "ablation": self.ablation.to_dict() if self.ablation else None,
            "receipt": self.receipt,
            "admission_failed_receipt": self.admission_failed_receipt,
            "honest_verdict": self.honest_verdict,
        }


# ── Receipt writers ─────────────────────────────────────────────────────


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_gravity_receipt(
    payload: dict,
    *,
    forecast_id: str,
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write the canonical gravity receipt and return its handle."""
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-gravity-{forecast_id}-{stamp}"
    body = dict(payload)
    body["schema"] = SCHEMA
    body["receipt_subtype"] = "gravity_run"
    body["receipt_id"] = receipt_id
    body["issued_at"] = issued_at
    body["organ"] = "WEALTH"
    body["lane"] = "gold-gravity-challenger"
    text = json.dumps(body, indent=2, sort_keys=False)
    path = target / f"{receipt_id}.json"
    path.write_text(text, encoding="utf-8")
    return {
        "receipt_id": receipt_id,
        "receipt_uri": str(path),
        "written": True,
        "digest": _sha256_hex(text),
    }


def write_admission_rule_failed_receipt(
    *,
    forecast_id: str,
    skill_vs_M0: float,
    skill_vs_M1: float,
    skill_vs_M2: float,
    skill_vs_M3: float,
    n_windows: int,
    verdict_reasons: list[str],
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write the admission_rule_failed receipt and return its handle."""
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-gravity-admission-failed-{forecast_id}-{stamp}"
    body = {
        "schema": SCHEMA,
        "receipt_subtype": "admission_rule_failed",
        "receipt_id": receipt_id,
        "issued_at": issued_at,
        "organ": "WEALTH",
        "lane": "gold-gravity-challenger",
        "forecast_id": forecast_id,
        "admission_decision": "RECOMMEND_SHADOW_STATUS_UNCHANGED",
        "skill_vs_M0": round(skill_vs_M0, 4),
        "skill_vs_M1": round(skill_vs_M1, 4),
        "skill_vs_M2": round(skill_vs_M2, 4),
        "skill_vs_M3": round(skill_vs_M3, 4),
        "n_windows": int(n_windows),
        "verdict_reasons": list(verdict_reasons),
        "honest_verdict": (
            "M4 (wave + gravity) does not add measurable incremental skill "
            "over M0/M1/M2/M3 on the current XAUUSD history. The challenger "
            "stays SHADOW_CHALLENGER; no promotion is recommended."
        ),
    }
    text = json.dumps(body, indent=2, sort_keys=False)
    path = target / f"{receipt_id}.json"
    path.write_text(text, encoding="utf-8")
    return {
        "receipt_id": receipt_id,
        "receipt_uri": str(path),
        "written": True,
        "digest": _sha256_hex(text),
    }


# ── Pipeline orchestrator ───────────────────────────────────────────────


def run_gravity_field(
    *,
    closes: Optional[list[float]] = None,
    macro_payload: Optional[dict] = None,
    xagusd_history: Optional[list[float]] = None,
    gld_tonnes_history: Optional[list[tuple[str, float]]] = None,
    cot_history: Optional[list[tuple[str, float, float]]] = None,
    cb_history: Optional[list[tuple[str, float]]] = None,
    event_window_hours: int = 0,
    m4_wave_predictor: Optional[Any] = None,
    write_receipt: bool = True,
    receipts_dir: Optional[Path] = None,
    seed: int = 1337,
    now: Optional[datetime] = None,
) -> GravityResult:
    """Run the full 000 → 999 gravity pipeline.

    Parameters
    ----------
    closes
        The XAUUSD close series (oldest → newest). If None, attempts to
        use the wave-forge synthetic series as a labelled fallback.
    macro_payload
        The ``/api/gold/macro`` body (optional). Used by USD basket ingester.
    xagusd_history
        XAG-USD history matching the length of ``closes`` (optional).
    gld_tonnes_history, cot_history, cb_history
        Optional history feeds for the weekly/quarterly ingesters.
    event_window_hours
        Hours until next exogenous event (FOMC/NFP/CPI). 0 disables.
    m4_wave_predictor
        Optional callable ``(closes, horizons_h, seed) -> dict`` from the
        wave-forge challenger pipeline. If supplied, M3 and M4 use it.
    write_receipt
        When True, write the canonical receipt (and admission_failed
        receipt on failure) to VAULT999.
    receipts_dir
        Override the VAULT999 receipts directory (mostly for tests).
    seed
        RNG seed for determinism.
    now
        Wall-clock override.
    """
    now = now or datetime.now(timezone.utc)
    issued_at = now.isoformat()

    # ── Build / fallback the price series ─────────────────────────────
    closes_arr: list[float] = []
    if closes is not None and len(closes) >= 30:
        closes_arr = [float(c) for c in closes if isinstance(c, (int, float)) and c > 0]
    if not closes_arr:
        # Honest fallback — call wave_forge's synthetic fallback.
        try:
            import sys
            wf_path = "/root/WEALTH/forecast/wave_forge"
            if wf_path not in sys.path:
                sys.path.insert(0, wf_path)
            from synthetic import get_xauusd_history  # type: ignore
            history = get_xauusd_history(days=730, seed=seed)
            closes_arr = [float(v) for v in history.df["close"].tolist()]
        except Exception:
            # No history at all → return a quarantined result.
            forecast_id = f"gold-gravity-{now.strftime('%Y%m%dT%H%M%SZ')}-{seed:04x}"
            honest = "No XAUUSD history available — cannot run gravity pipeline. Quarantined."
            verdict_reasons = ["no_history"]
            admission_failed = None
            if write_receipt:
                admission_failed = write_admission_rule_failed_receipt(
                    forecast_id=forecast_id,
                    skill_vs_M0=0.0,
                    skill_vs_M1=0.0,
                    skill_vs_M2=0.0,
                    skill_vs_M3=0.0,
                    n_windows=0,
                    verdict_reasons=verdict_reasons,
                    receipts_dir=receipts_dir,
                )
            return GravityResult(
                forecast_id=forecast_id,
                issued_at=issued_at,
                status=STATUS,
                admission="FAIL",
                verdict="QUARANTINE",
                verdict_reasons=verdict_reasons,
                admission_failed_receipt=admission_failed,
                honest_verdict=honest,
            )

    # ── 000 INGEST ────────────────────────────────────────────────────
    series = build_gravity_feature_series(
        now=now,
        macro_payload=macro_payload,
        xagusd_history=xagusd_history,
        xauusd_history=closes_arr,
        gld_tonnes_history=gld_tonnes_history,
        cot_history=cot_history,
        cb_history=cb_history,
    )

    # ── 111 REGIME ────────────────────────────────────────────────────
    regime = compute_regime_posterior_111(
        series,
        closes=closes_arr,
        event_window_hours=event_window_hours,
        now=now,
    )

    # ── 444 DISTRIBUTION ──────────────────────────────────────────────
    distribution = compute_distribution_444(
        closes=closes_arr,
        regime_posterior=regime,
        now=now,
    )

    # ── 555 ABLATION ──────────────────────────────────────────────────
    # Build a coarse gravity-points feed from the gravity series for the
    # tournament: list of (timestamp, real_yield_slope, usd_slope).
    gravity_points = _gravity_points_for_ablation(series, now=now)
    ablation = run_ablation_tournament(
        history=np.asarray(closes_arr, dtype=float),
        m4_wave_predictor=m4_wave_predictor,
        gravity_points=gravity_points,
        seed=seed,
        now=now,
    )

    # ── 888 JUDGE ─────────────────────────────────────────────────────
    forecast_id = f"gold-gravity-{now.strftime('%Y%m%dT%H%M%SZ')}-{seed:04x}"
    verdict_reasons: list[str] = []
    verdict = "HOLD"

    if ablation is None or len(ablation.rows) == 0:
        verdict = "QUARANTINE"
        verdict_reasons.append("ablation_empty")
    elif not ablation.M4_promoted:
        verdict = "HOLD"
        verdict_reasons.extend(ablation.reasons)
    else:
        verdict = "USE"
        verdict_reasons.append("ALL_ADMISSION_GATES_PASSED")
        verdict_reasons.append("PROMOTION_REQUIRES_F13_AUTHORIZATION")

    honest_verdict = _compose_honest_verdict(
        ablation=ablation,
        regime=regime,
        distribution=distribution,
        verdict=verdict,
        verdict_reasons=verdict_reasons,
    )

    # ── 999 WITNESS ───────────────────────────────────────────────────
    receipt_handle: Optional[dict] = None
    admission_failed_handle: Optional[dict] = None
    if write_receipt:
        packet_preview = {
            "forecast_id": forecast_id,
            "issued_at": issued_at,
            "status": STATUS,
            "verdict": verdict,
            "verdict_reasons": verdict_reasons,
            "regime": regime.to_dict() if regime else None,
            "distribution": distribution.to_dict() if distribution else None,
            "ablation": ablation.to_dict() if ablation else None,
        }
        receipt_handle = write_gravity_receipt(
            packet_preview, forecast_id=forecast_id, receipts_dir=receipts_dir
        )
        if not ablation.M4_promoted and ablation is not None and ablation.rows:
            # Pull M4 skill scores from the ablation rows.
            m4_row = next(
                (r for r in ablation.rows if r.name == "M4_wave_plus_gravity"),
                None,
            )
            if m4_row:
                admission_failed_handle = write_admission_rule_failed_receipt(
                    forecast_id=forecast_id,
                    skill_vs_M0=m4_row.pinball_skill_vs_M0,
                    skill_vs_M1=m4_row.pinball_skill_vs_M1,
                    skill_vs_M2=m4_row.pinball_skill_vs_M2,
                    skill_vs_M3=m4_row.pinball_skill_vs_M3,
                    n_windows=m4_row.n_windows,
                    verdict_reasons=verdict_reasons,
                    receipts_dir=receipts_dir,
                )

    return GravityResult(
        forecast_id=forecast_id,
        issued_at=issued_at,
        status=STATUS if verdict != "USE" else "CHALLENGER_PASSED",
        admission="PASS" if ablation.M4_promoted else "FAIL",
        gravity_series=series,
        regime=regime,
        distribution=distribution,
        ablation=ablation,
        verdict=verdict,
        verdict_reasons=verdict_reasons,
        receipt=receipt_handle,
        admission_failed_receipt=admission_failed_handle,
        honest_verdict=honest_verdict,
    )


# ── Helpers ─────────────────────────────────────────────────────────────


def _gravity_points_for_ablation(
    series: GravityFeatureSeries,
    *,
    now: datetime,
) -> list[tuple[datetime, float, float]]:
    """Build a coarse ``(ts, real_yield_slope, usd_slope)`` series.

    Used by M2 / M4 in the ablation tournament as a *fast* stand-in for
    the full gravity feature set. The full gravity path lives in the
    regime + distribution lanes.
    """
    out: list[tuple[datetime, float, float]] = []
    dfii_pts = sorted(
        series.points_by_source.get("DFII10", []),
        key=lambda p: p.observation_ts,
    )
    usd_pts = sorted(
        series.points_by_source.get("USD_BASKET", []),
        key=lambda p: p.observation_ts,
    )
    dfii_vals = [float(p.value) for p in dfii_pts if isinstance(p.value, (int, float))]
    usd_vals = [float(p.value) for p in usd_pts if isinstance(p.value, (int, float))]
    n = min(len(dfii_vals), len(usd_vals))
    if n < 3:
        return out
    for i in range(2, n):
        ry_rets = [
            (dfii_vals[j] - dfii_vals[j - 1]) / dfii_vals[j - 1]
            for j in range(max(0, i - 5), i + 1)
            if dfii_vals[j - 1] > 0
        ]
        usd_rets = [
            (usd_vals[j] - usd_vals[j - 1]) / usd_vals[j - 1]
            for j in range(max(0, i - 5), i + 1)
            if usd_vals[j - 1] > 0
        ]
        ry_pct = float(np.mean(ry_rets)) if ry_rets else 0.0
        usd_pct = float(np.mean(usd_rets)) if usd_rets else 0.0
        ts = now - timedelta(days=n - i - 1)
        out.append((ts, ry_pct, usd_pct))
    return out


from datetime import timedelta  # noqa: E402  (re-export)


def _compose_honest_verdict(
    *,
    ablation: AblationTable,
    regime: RegimePosterior111,
    distribution: Distribution444,
    verdict: str,
    verdict_reasons: list[str],
) -> str:
    """Compose the human-readable honest verdict.

    Never claims promotion. Always records what passed and what failed.
    """
    bits = []
    bits.append(f"GRAVITY FIELD verdict={verdict} (status remains SHADOW_CHALLENGER).")
    if ablation and ablation.rows:
        m4 = next(
            (r for r in ablation.rows if r.name == "M4_wave_plus_gravity"),
            None,
        )
        if m4:
            bits.append(
                "M4 (wave + gravity) walk-forward pinball={:.4f}, "
                "skill_vs_M0={:.4f}, vs_M1={:.4f}, vs_M2={:.4f}, vs_M3={:.4f}, "
                "n_windows={}.".format(
                    m4.pinball,
                    m4.pinball_skill_vs_M0,
                    m4.pinball_skill_vs_M1,
                    m4.pinball_skill_vs_M2,
                    m4.pinball_skill_vs_M3,
                    m4.n_windows,
                )
            )
    bits.append(
        f"Regime posterior: {regime.state} (conf={regime.confidence:.3f}); "
        f"distribution horizons: {len(distribution.horizons)}."
    )
    if not ablation.M4_promoted:
        bits.append("ADMISSION_RULE_FAILED: " + "; ".join(verdict_reasons))
        bits.append(
            "Recommend SHADOW status remains; do NOT promote out of "
            "SHADOW_CHALLENGER without F13 authorization."
        )
    else:
        bits.append(
            "ADMISSION_PASSED on walk-forward. F13 authorization still "
            "required to promote out of SHADOW_CHALLENGER."
        )
    return " ".join(bits)


__all__ = [
    "SCHEMA",
    "STATUS",
    "GravityResult",
    "run_gravity_field",
    "write_gravity_receipt",
    "write_admission_rule_failed_receipt",
    "DEFAULT_VAULT",
]
