"""Compatibility shim — canonical home is ``wealth_contracts.freshness``.

Moved 2026-10-25 to resolve boundary contract ``wealth-contract-001``:
the contract layer may not import ``wealth_mcp``. The module is stdlib-only
and its only consumer was ``wealth_contracts.envelope``.

Existing imports of ``wealth_mcp.freshness`` keep working; no behaviour change.
"""

from wealth_contracts.freshness import (  # noqa: F401
    OMEGA_FIELD_TOOLS,
    StalenessClass,
    check_freshness_admissible,
    enforce_freshness,
)
