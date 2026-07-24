"""Shared live metadata for the WEALTH MCP surface."""

from __future__ import annotations

import tomllib
from pathlib import Path

CAPITAL_TOOL_NAMES = (
    "capital_primitive",
    "capital_health",
    "capital_diagnose",
    "capital_wisdom",
    "capital_market",
    "capital_ledger",
    "capital_registry",
    "capital_entropy",
)

INSTITUTIONAL_TOOL_NAMES = (
    "wealth_institutional_stress_index",
    "wealth_cascade_model",
    "wealth_governance_capacity",
    "wealth_external_exploitation_detect",
)

PUBLIC_TOOL_NAMES = CAPITAL_TOOL_NAMES + INSTITUTIONAL_TOOL_NAMES


def _load_identity_version() -> str:
    """Read the declared organ version without inventing a stale fallback."""
    identity_path = Path(__file__).resolve().parents[1] / "identity.toml"
    try:
        version = tomllib.loads(identity_path.read_text(encoding="utf-8"))["identity"][
            "version"
        ]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError):
        return "UNAVAILABLE"
    return str(version).strip() or "UNAVAILABLE"


WEALTH_VERSION = _load_identity_version()

__all__ = [
    "CAPITAL_TOOL_NAMES",
    "INSTITUTIONAL_TOOL_NAMES",
    "PUBLIC_TOOL_NAMES",
    "WEALTH_VERSION",
]
