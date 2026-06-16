"""
Civilization Wealth Adapter — Phase 4 substrate.

Per executive verdict Phase 4: "Mesa/Econ-ARK simulation lane. Inequality/mobility
simulation. Resource allocation game engine. Policy counterfactual engine."

This package provides:
- inequality_stress.py: stress-test civilizations under shocks
- policy_counterfactual.py: run counterfactual policy scenarios

(Mesa adapter is in wealth_adapters/mesa_adapter.py — re-imported here for convenience.)
"""

from ..wealth_adapters.mesa_adapter import MesaAdapter
from .inequality_stress import InequalityStress
from .policy_counterfactual import PolicyCounterfactual

__all__ = [
    "MesaAdapter",
    "InequalityStress",
    "PolicyCounterfactual",
]
