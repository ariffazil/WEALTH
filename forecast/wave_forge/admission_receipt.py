"""Honest admission_rule_failed receipt.

Per the task contract, when M4-WAVE does not beat M2 (the existing
sparse market-reality model), we must:

1. Recommend SHADOW (status stays SHADOW_CHALLENGER).
2. Write an explicit ``admission_rule_failed`` receipt to VAULT999.

This module exposes a single function,
:func:`write_admission_rule_failed_receipt`, that writes a fixed-format
receipt distinguishing the admission failure from a normal run receipt.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import hashlib


DEFAULT_VAULT = Path(
    os.getenv("VAULT999_WAVE_FORGE_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_admission_rule_failed_receipt(
    *,
    forecast_id: str,
    skill_vs_M0: float,
    skill_vs_M2: float,
    skill_vs_M4_TREND: float,
    n_windows: int,
    verdict_reason: str,
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write the explicit admission_rule_failed receipt and return its handle.

    The receipt body has a stable schema so downstream audit tools can
    group by ``receipt_subtype == 'admission_rule_failed'``.
    """
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-wave-forge-admission-failed-{forecast_id}-{stamp}"
    body = {
        "schema": "wealth.gold.wave_forge.v1",
        "receipt_subtype": "admission_rule_failed",
        "receipt_id": receipt_id,
        "issued_at": issued_at,
        "organ": "WEALTH",
        "lane": "gold-wave-forge-challenger",
        "forecast_id": forecast_id,
        "admission_decision": "RECOMMEND_SHADOW_STATUS_UNCHANGED",
        "skill_vs_M0": skill_vs_M0,
        "skill_vs_M2": skill_vs_M2,
        "skill_vs_M4_TREND": skill_vs_M4_TREND,
        "n_windows": n_windows,
        "verdict_reason": verdict_reason,
        "honest_verdict": (
            "M4-WAVE does not add measurable incremental skill over M2 on the "
            "current XAUUSD history. The challenger stays SHADOW_CHALLENGER; "
            "no promotion is recommended."
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


__all__ = [
    "write_admission_rule_failed_receipt",
    "DEFAULT_VAULT",
]