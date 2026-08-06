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


# Live MCP surface metadata (SOT — synced 2026-08-06 by C1 fix).
# Source of truth for counts advertised in wealth://schema and wealth://health.
# NOTE: keep in sync with @mcp.resource(uri=...) decorators in server.py.
WEALTH_RESOURCE_URIS: tuple[str, ...] = (
    "wealth://schema",
    "wealth://tools/registry",
    "wealth://prompts/index",
    "wealth://domains/index",
    "wealth://runtime/policy",
    "wealth://canon/002-human-law",
    "wealth://glossary",
    "wealth://federation/contract",
    "wealth://health",
    "wealth://reality/context",
    "wealth://market/sources",
    "wealth://risk/thresholds",
    "wealth://affordance/contracts",
    "wealth://handoff/arifos-schema",
    "wealth://replay/receipt-schema",
    "wealth://schema/field-dictionary",
    "wealth://epistemic/tag-definitions",
    "wealth://provenance/feeds",
)

WEALTH_PROMPT_NAMES: tuple[str, ...] = (
    "wealth_reality_intake_loop",
    "wealth_capital_diagnosis_loop",
    "wealth_risk_downside_loop",
    "wealth_market_reality_loop",
    "wealth_allocation_judgment_loop",
    "wealth_institutional_power_loop",
    "wealth_arifos_handoff_loop",
)


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
