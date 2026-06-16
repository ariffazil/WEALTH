"""
Policy Counterfactual — Run counterfactual policy scenarios.

Compare outcomes under different policy regimes (no tax, low tax, high tax,
universal basic income, etc.) on a simulated civilization.
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class PolicyCounterfactual:
    """Run counterfactual policy scenarios on a civilization simulation."""

    def __init__(self):
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_civilization_policy_counterfactual_v0.1"
        ).hexdigest()

    @staticmethod
    def _gini(wealths: list[float]) -> float:
        sorted_w = sorted(wealths)
        n = len(sorted_w)
        if n == 0 or sum(sorted_w) == 0:
            return 0.0
        cumulative = sum((i + 1) * w for i, w in enumerate(sorted_w))
        return (2 * cumulative) / (n * sum(sorted_w)) - (n + 1) / n

    @staticmethod
    def _run_scenario(
        n_households: int,
        n_steps: int,
        tax_rate: float,
        redistribution_rate: float,
        ubi: float = 0.0,
        seed: int = 42,
    ) -> dict:
        """Run a single scenario, return summary."""
        random.seed(seed)
        wealths = [100.0 * (0.5 + random.random()) for _ in range(n_households)]
        initial_gini = PolicyCounterfactual._gini(wealths)

        for step in range(n_steps):
            for i in range(n_households):
                return_rate = random.gauss(0.04, 0.10)
                wealths[i] *= (1 + return_rate)

            if tax_rate > 0:
                total_tax = sum(w * tax_rate for w in wealths)
                per_household = total_tax * redistribution_rate / n_households
                wealths = [w - w * tax_rate + per_household + ubi for w in wealths]
            elif ubi > 0:
                wealths = [w + ubi for w in wealths]

        return {
            "tax_rate": tax_rate,
            "redistribution_rate": redistribution_rate,
            "ubi": ubi,
            "initial_gini": initial_gini,
            "final_gini": PolicyCounterfactual._gini(wealths),
            "total_wealth": sum(wealths),
            "mean_wealth": sum(wealths) / n_households,
            "min_wealth": min(wealths),
            "max_wealth": max(wealths),
        }

    def compare_scenarios(
        self,
        n_households: int = 200,
        n_steps: int = 100,
        scenarios: Optional[list[dict]] = None,
    ) -> WealthEnvelope:
        """
        Compare multiple policy scenarios.

        scenarios: list of {"name": str, "tax_rate": float, "redistribution_rate": float, "ubi": float}
        """
        if scenarios is None:
            scenarios = [
                {"name": "no_policy", "tax_rate": 0.0, "redistribution_rate": 0.0, "ubi": 0.0},
                {"name": "low_tax", "tax_rate": 0.05, "redistribution_rate": 0.4, "ubi": 0.0},
                {"name": "high_tax", "tax_rate": 0.20, "redistribution_rate": 0.7, "ubi": 0.0},
                {"name": "ubi_only", "tax_rate": 0.0, "redistribution_rate": 0.0, "ubi": 2.0},
                {"name": "ubi_plus_tax", "tax_rate": 0.15, "redistribution_rate": 0.5, "ubi": 1.0},
            ]

        results = []
        for s in scenarios:
            r = self._run_scenario(
                n_households=n_households,
                n_steps=n_steps,
                tax_rate=s.get("tax_rate", 0.0),
                redistribution_rate=s.get("redistribution_rate", 0.0),
                ubi=s.get("ubi", 0.0),
                seed=42,
            )
            r["name"] = s["name"]
            results.append(r)

        return WealthEnvelope(
            verdict=VerdictLabel.SAFE_TO_STUDY,
            epistemic_status="DER",
            data={
                "method": "policy_counterfactual",
                "n_households": n_households,
                "n_steps": n_steps,
                "scenarios": results,
            },
            transform_hash=self.adapter_hash,
            notes="Counterfactual policy comparison. Households = capital entities, not humans. F13 SOVEREIGN execution required to act on recommendations.",
        )
