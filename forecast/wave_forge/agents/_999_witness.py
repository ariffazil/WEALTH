"""Agent 999 — WITNESS.

Append-only VAULT999 receipt for the wave-forge run. Mirrors the
pattern in `/root/WEALTH/forecast/orchestrator.py::AGENT_999_Witness`:
the receipt is an event record, not a seal, and a write failure is
returned honestly as ``written=False`` — never swallowed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Default receipts directory; overridable via env for tests / non-VPS hosts.
import os

DEFAULT_RECEIPTS_DIR = Path(
    os.getenv("VAULT999_WAVE_FORGE_RECEIPTS", "/root/AAA/VAULT999/receipts")
)


@dataclass(frozen=True)
class WitnessReceipt:
    """The 999-WITNESS output."""

    receipt_id: str = ""
    receipt_uri: str = ""
    written: bool = False
    digest: str = ""
    observed_at: str = ""
    failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "999-WITNESS",
            "receipt_id": self.receipt_id,
            "receipt_uri": self.receipt_uri,
            "written": bool(self.written),
            "digest": self.digest,
            "observed_at": self.observed_at,
            "failure_reason": self.failure_reason,
        }


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def AGENT_999_Witness(
    packet: dict[str, Any],
    *,
    forecast_id: str,
    receipts_dir: Optional[Path] = None,
) -> WitnessReceipt:
    """Write the receipt to VAULT999 and return its handle."""
    observed_at = datetime.now(timezone.utc).isoformat()
    target = receipts_dir if receipts_dir is not None else DEFAULT_RECEIPTS_DIR
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    receipt_id = f"wealth-gold-wave-forge-{forecast_id}-{stamp}"

    try:
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{receipt_id}.json"
        body = {
            "receipt_id": receipt_id,
            "issued_at": observed_at,
            "organ": "WEALTH",
            "lane": "gold-wave-forge-challenger",
            "schema": "wealth.gold.wave_forge.v1",
            "constitutional_tier": "999-WITNESS",
            "forecast_id": forecast_id,
            "payload": packet,
        }
        text = json.dumps(body, indent=2, sort_keys=False, default=str)
        path.write_text(text, encoding="utf-8")
        return WitnessReceipt(
            receipt_id=receipt_id,
            receipt_uri=str(path),
            written=True,
            digest=_sha256_hex(text),
            observed_at=observed_at,
        )
    except OSError as exc:
        return WitnessReceipt(
            receipt_id=receipt_id,
            receipt_uri="",
            written=False,
            digest="",
            observed_at=observed_at,
            failure_reason=f"{type(exc).__name__}:{exc}",
        )


__all__ = [
    "AGENT_999_Witness",
    "WitnessReceipt",
    "DEFAULT_RECEIPTS_DIR",
]