"""
WEALTH Core — Game/Coordination Domain.

Extracted from host/coordination/ and internal/engines/.
Multi-agent incentives, bargaining, coordination.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

try:
    from internal.monolith import (
        coordination_equilibrium,
        game_theory_solve,
        agent_budget,
    )
    _GAME_AVAILABLE = True
except ImportError:
    _GAME_AVAILABLE = False

    def coordination_equilibrium(*args, **kwargs):
        return {"error": "Game engine not available"}

    def game_theory_solve(*args, **kwargs):
        return {"error": "Game engine not available"}

    def agent_budget(*args, **kwargs):
        return {"error": "Game engine not available"}


__all__ = [
    "coordination_equilibrium",
    "game_theory_solve",
    "agent_budget",
    "is_available",
]


def is_available() -> bool:
    return _GAME_AVAILABLE
