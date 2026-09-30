"""M7 receipt writers.

Three receipt types:

    * write_safety_gate_receipt — a survival verdict (ACT/REDUCE/HOLD/BLOCK)
    * write_honest_caveat_receipt — an explicit caveat about synthetic
      defaults / missing data / known limitations
    * (write_m7_receipt lives in engine.py and is the unified entry point)

Receipts are JSON files dropped into VAULT999/receipts/. They never
modify any other module's state — they are pure append-only witness.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .engine import M7Result, M7_SCHEMA


DEFAULT_VAULT = Path(
    os.getenv("VAULT999_M7_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _write_json(target: Path, body: dict) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(body, indent=2, sort_keys=False)
    target.write_text(text, encoding="utf-8")
    return target


def write_safety_gate_receipt(
    m7_result: M7Result,
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write a survival-verdict receipt."""
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-m7-safety-{m7_result.verdict.lower()}-{m7_result.forecast_id}-{stamp}"
    body = m7_result.to_dict()
    body["schema"] = M7_SCHEMA
    body["receipt_subtype"] = f"survival_verdict_{m7_result.verdict.lower()}"
    body["receipt_id"] = receipt_id
    body["issued_at"] = datetime.now(timezone.utc).isoformat()
    body["organ"] = "WEALTH"
    body["lane"] = "gold-m7-survival-path-risk"
    text = json.dumps(body, indent=2, sort_keys=False)
    path = target / f"{receipt_id}.json"
    path.write_text(text, encoding="utf-8")
    return {
        "receipt_id": receipt_id,
        "receipt_uri": str(path),
        "written": True,
        "digest": _sha256_hex(text),
    }


def write_honest_caveat_receipt(
    *,
    caveat_codes: list[str],
    description: str,
    forecast_id: str,
    receipts_dir: Optional[Path] = None,
) -> dict:
    """Write an explicit honest-caveat receipt.

    Use this to document synthetic defaults, missing data, or any
    situation where M7 produced a verdict on inputs that are not
    first-party live evidence. Honest receipts are the canonical way
    to satisfy the F2 (audit) requirement without hiding defaults.
    """
    target = receipts_dir if receipts_dir is not None else DEFAULT_VAULT
    target.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-m7-honest-caveat-{forecast_id}-{stamp}"
    body = {
        "schema": M7_SCHEMA,
        "receipt_subtype": "honest_caveat",
        "receipt_id": receipt_id,
        "issued_at": issued_at,
        "organ": "WEALTH",
        "lane": "gold-m7-survival-path-risk",
        "forecast_id": forecast_id,
        "caveat_codes": list(caveat_codes),
        "description": description,
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
    "write_safety_gate_receipt",
    "write_honest_caveat_receipt",
    "DEFAULT_VAULT",
]
