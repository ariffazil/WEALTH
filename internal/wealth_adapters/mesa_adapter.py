"""
Mesa Adapter — Agent-based civilization wealth simulation.

Per executive verdict Phase 4: "Agent-based economics — Mesa/AgentPy/Econ-ARK
needed for civilization wealth simulation: households, firms, policy, inequality,
incentives, shocks, mobility, and resource allocation."

F8 LAW: Mesa simulates. WEALTH audits. arifOS gates. Arif decides.
F6 MARUAH: agents in the simulation represent capital/resource flows, not humans.
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class MesaAdapter:
    """Adapter for Mesa agent-based modeling."""

    def __init__(self):
        self._available = self._check_availability()
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_adapters_mesa_v0.1"
        ).hexdigest()

    def _check_availability(self) -> bool:
        try:
            import mesa
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._available

    def run_inequality_simulation(
        self,
        n_households: int = 100,
        n_steps: int = 50,
        initial_wealth: float = 100.0,
        tax_rate: float = 0.0,
        redistribution_rate: float = 0.0,
        seed: Optional[int] = None,
    ) -> WealthEnvelope:
        """
        Simple inequality simulation: N households with random returns, optional tax/redistribution.

        Returns the Gini coefficient before/after, total wealth, and trajectory.
        """
        if not self._available:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": "Mesa not installed"},
                transform_hash=self.adapter_hash,
            )

        if seed is not None:
            random.seed(seed)

        # Initial wealth distribution
        wealths = [initial_wealth * (0.5 + random.random()) for _ in range(n_households)]
        initial_gini = self._gini(wealths)
        trajectory = [(0, sum(wealths), initial_gini)]

        for step in range(1, n_steps + 1):
            # Random returns
            for i in range(n_households):
                return_rate = random.gauss(0.05, 0.15)
                wealths[i] *= (1 + return_rate)

            # Tax + redistribution
            if tax_rate > 0:
                total_tax = sum(w * tax_rate for w in wealths)
                per_household = total_tax * redistribution_rate / n_households
                wealths = [w - w * tax_rate + per_household for w in wealths]

            # Gini
            current_gini = self._gini(wealths)
            trajectory.append((step, sum(wealths), current_gini))

        final_gini = self._gini(wealths)
        total_wealth = sum(wealths)

        return WealthEnvelope(
            verdict=VerdictLabel.SAFE_TO_STUDY,
            epistemic_status="DER",
            data={
                "method": "mesa_inequality_simulation",
                "n_households": n_households,
                "n_steps": n_steps,
                "initial_gini": initial_gini,
                "final_gini": final_gini,
                "total_wealth": total_wealth,
                "tax_rate": tax_rate,
                "redistribution_rate": redistribution_rate,
                "trajectory": trajectory,
            },
            transform_hash=self.adapter_hash,
            notes="Mesa-style ABM. Households = capital entities, not humans (F6 MARUAH). F13 SOVEREIGN execution required to act.",
        )

    @staticmethod
    def _gini(wealths: list[float]) -> float:
        """Compute Gini coefficient for a list of wealths."""
        sorted_w = sorted(wealths)
        n = len(sorted_w)
        if n == 0 or sum(sorted_w) == 0:
            return 0.0
        cumulative = sum((i + 1) * w for i, w in enumerate(sorted_w))
        return (2 * cumulative) / (n * sum(sorted_w)) - (n + 1) / n
