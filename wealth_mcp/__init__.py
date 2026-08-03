"""Shared live metadata for the WEALTH MCP surface."""

from __future__ import annotations

import tomllib
from pathlib import Path

CAPITAL_TOOL_NAMES = (
    "capital_primitive",
    "capital_health",
    "capital_diagnose",
    "capital_market",
    "capital_ledger",
    "capital_registry",
    "capital_entropy",
    "wealth_judge_handoff",
)

# Zen Phase 1a: shadow tools removed from MCP surface.
# All institutional access is via capital_diagnose(mode=...).
# Engines preserved; only duplicate MCP registrations removed.
INSTITUTIONAL_TOOL_NAMES: tuple[str, ...] = ()

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
