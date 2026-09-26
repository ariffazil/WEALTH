"""PASS receipt writer for M5 admission.

When the admission test passes (skill > 0 + coverage ≈ targets +
narrower bands + lower QLIKE), we still emit an explicit PASS receipt
so the audit trail has full provenance. The receipt marks the run as
ADMISSION_PASS but keeps M5 in SHADOW_CHALLENGER status — promotion
out of SHADOW is an F13-level decision, not an M5 decision.

The receipt is differentiated from the admission_rule_failed receipt
by ``receipt_subtype == "admission_pass"``.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .engine import SCHEMA, WalkForwardResult


DEFAULT_VAULT = Path(
    os.getenv("VAULT999_M5_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_admission_pass_receipt(
    *,
    forecast_id: str,
    wf_result: WalkForwardResult,
    receipts_dir: Optional[Path] = None,
    honest_verdict: Optional[str] = None,
) -> dict:
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-m5-admission-pass-{forecast_id}-{stamp}"
    body = {
        "schema": SCHEMA,
        "receipt_subtype": "admission_pass",
        "receipt_id": receipt_id,
        "issued_at": issued_at,
        "organ": "WEALTH",
        "lane": "gold-m5-adaptive-distribution",
        "forecast_id": forecast_id,
        "admission_decision": "ADMISSION_PASS_STATUS_SHADOW_CHALLENGER_RETAINED",
        "walk_forward": {
            "n_windows": int(wf_result.n_windows),
            "m5_pinball": wf_result.m5_pinball,
            "m0_pinball": wf_result.m0_pinball,
            "skill_vs_M0": wf_result.skill_vs_M0,
            "m5_coverage_p10_p90": wf_result.m5_coverage_p10_p90,
            "m0_coverage_p10_p90": wf_result.m0_coverage_p10_p90,
            "m5_coverage_p25_p75": wf_result.m5_coverage_p25_p75,
            "m0_coverage_p25_p75": wf_result.m0_coverage_p25_p75,
            "m5_interval_width_mean": wf_result.m5_interval_width_mean,
            "m0_interval_width_mean": wf_result.m0_interval_width_mean,
            "m5_qlike": wf_result.m5_qlike,
            "m0_qlike": wf_result.m0_qlike,
        },
        "admission_reasons": list(wf_result.admission_reasons),
        "honest_verdict": honest_verdict or (
            "M5 (Adaptive Distribution Engine) satisfies the admission rule on the "
            "current XAUUSD history (skill_vs_M0 > 0, coverage ≈ targets, narrower "
            "bands, lower QLIKE). M5 stays in SHADOW_CHALLENGER; promotion out of "
            "SHADOW is an F13-level decision."
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


__all__ = ["write_admission_pass_receipt", "DEFAULT_VAULT"]