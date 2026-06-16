"""
WEALTH Adapters — Pluggable adapters for external quant libraries.

Per executive verdict:
"External libraries = calculators, sensors, simulators, stores, policy engines"
"Turn them into a governed substrate where external codebases are plugged in as adapters, not trusted authorities."

This package provides:
- pyportfolioopt_adapter.py: PyPortfolioOpt (lightweight portfolio)
- openlineage_adapter.py: OpenLineage-style evidence chain
"""

from .pyportfolioopt_adapter import PyPortfolioOptAdapter
from .openlineage_adapter import OpenLineageAdapter

__all__ = ["PyPortfolioOptAdapter", "OpenLineageAdapter"]
