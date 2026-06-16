"""
WEALTH Policy Inputs — OPA policy input builders for WEALTH tools.

Builds the input dict for OPA evaluation before any mutation-capable tool.
"""

from __future__ import annotations

from typing import Any, Optional


def build_policy_input(
    actor_id: str,
    tool: str,
    action_class: str,
    session_id: Optional[str] = None,
    resource: Optional[str] = None,
    reversible: bool = True,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build OPA policy input for a WEALTH tool call."""
    return {
        "actor_id": actor_id,
        "action_class": action_class,
        "tool": tool,
        "session_id": session_id or "",
        "resource": resource or "",
        "reversible": reversible,
        "organ": "WEALTH",
        **(extra or {}),
    }
