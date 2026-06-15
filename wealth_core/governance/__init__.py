"""
WEALTH Core — Governance Domain.

Extracted from internal/governance.py and internal/engines/.
Boundary, inequality, verdict engines.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from ..math import ForgeLaw, compute_kappa_r, compute_psi_le, get_qdf_version

try:
    from internal.monolith import (
        wealth_boundary_governance,
        wealth_governance_verdict,
        wealth_inequality_kernel,
    )
    _GOV_AVAILABLE = True
except ImportError:
    _GOV_AVAILABLE = False

    def wealth_boundary_governance(*args, **kwargs):
        return {"error": "Governance engine not available"}

    def wealth_governance_verdict(*args, **kwargs):
        return {"error": "Governance engine not available"}

    def wealth_inequality_kernel(*args, **kwargs):
        return {"error": "Inequality engine not available"}


__all__ = [
    "ForgeLaw",
    "compute_kappa_r",
    "compute_psi_le",
    "get_qdf_version",
    "wealth_boundary_governance",
    "wealth_governance_verdict",
    "wealth_inequality_kernel",
    "is_available",
]


def is_available() -> bool:
    return _GOV_AVAILABLE
