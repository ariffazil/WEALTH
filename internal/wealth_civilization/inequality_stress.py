"""
Inequality Stress Test — Stress-test a civilization simulation under shocks.

Apply income/wealth shocks to a simulated population and measure the Gini response.
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class InequalityStress:
    """Run inequality stress tests on a simulated civilization."""

    def __init__(self):
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_civilization_inequality_stress_v0.1"
        ).hexdigest()

    @staticmethod
    def _gini(wealths: list[float]) -> float:
        sorted_w = sorted(wealths)
        n = len(sorted_w)
        if n == 0 or sum(sorted_w) == 0:
            return 0.0
        cumulative = sum((i + 1) * w for i, w in enumerate(sorted_w))
        return (2 * cumulative) / (n * sum(sorted_w)) - (n + 1) / n

    def run(
        self,
        n_households: int = 200,
        n_steps: int = 100,
        shock_magnitude: float = -0.3,  # -30% wealth shock
        shock_step: int = 50,
        shock_fraction: float = 0.2,  # 20% of population hit
        tax_rate: float = 0.1,
        redistribution_rate: float = 0.5,
        seed: Optional[int] = None,
    ) -> WealthEnvelope:
        """
        Simulate a civilization, apply a shock mid-run, measure Gini trajectory.

        Returns WealthEnvelope with: pre-shock Gini, post-shock Gini, recovery steps, etc.
        """
        if seed is not None:
            random.seed(seed)

        wealths = [100.0 * (0.5 + random.random()) for _ in range(n_households)]
        trajectory = [(0, sum(wealths), self._gini(wealths))]

        pre_shock_gini = trajectory[0][2]
        post_shock_gini = None
        recovery_step = None

        for step in range(1, n_steps + 1):
            # Random returns
            for i in range(n_households):
                return_rate = random.gauss(0.04, 0.10)
                wealths[i] *= (1 + return_rate)

            # Apply shock
            if step == shock_step:
                shocked = random.sample(range(n_households), int(n_households * shock_fraction))
                for i in shocked:
                    wealths[i] *= (1 + shock_magnitude)

            # Tax + redistribution
            if tax_rate > 0:
                total_tax = sum(w * tax_rate for w in wealths)
                per_household = total_tax * redistribution_rate / n_households
                wealths = [w - w * tax_rate + per_household for w in wealths]

            g = self._gini(wealths)
            trajectory.append((step, sum(wealths), g))

            if step == shock_step:
                post_shock_gini = g
            if post_shock_gini is not None and recovery_step is None and g <= pre_shock_gini * 1.05:
                recovery_step = step

        return WealthEnvelope(
            verdict=VerdictLabel.SAFE_TO_STUDY,
            epistemic_status="DER",
            data={
                "method": "mesa_inequality_stress",
                "n_households": n_households,
                "n_steps": n_steps,
                "pre_shock_gini": pre_shock_gini,
                "post_shock_gini": post_shock_gini,
                "recovery_step": recovery_step,
                "recovered": recovery_step is not None,
                "shock_magnitude": shock_magnitude,
                "shock_fraction": shock_fraction,
                "tax_rate": tax_rate,
                "redistribution_rate": redistribution_rate,
                "final_gini": trajectory[-1][2],
                "trajectory_summary": {
                    "min_gini": min(t[2] for t in trajectory),
                    "max_gini": max(t[2] for t in trajectory),
                    "min_gini_step": min(trajectory, key=lambda t: t[2])[0],
                    "max_gini_step": max(trajectory, key=lambda t: t[2])[0],
                },
            },
            transform_hash=self.adapter_hash,
            notes="Civilization stress test. Households = capital entities, not humans. F13 SOVEREIGN execution required to act.",
        )
