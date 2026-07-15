#!/usr/bin/env python3
"""WEALTH — DEPRECATED entry (monolith path).

⚠️  PRODUCTION ENTRY IS: server_federated.py  (wealth-organ.service)
    Membrane: wealth_mcp/server.py
    Core:     wealth_core/
    Docs:     ENTRYPOINTS.md

This module still re-exports internal.monolith for tests/scripts only.
Do NOT use as production MCP server. Removal target: 2026-08-15.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import runpy
import sys
import warnings

warnings.warn(
    "WEALTH server.py is DEPRECATED. Use server_federated.py (canonical). "
    "See ENTRYPOINTS.md",
    DeprecationWarning,
    stacklevel=1,
)

from internal.monolith import *  # noqa: F403


if __name__ == "__main__":
    from pathlib import Path

    print(
        "DEPRECATED: server.py (monolith path). "
        "Redirecting to canonical server_federated.py — see ENTRYPOINTS.md",
        file=sys.stderr,
    )
    federated = Path(__file__).resolve().with_name("server_federated.py")
    runpy.run_path(str(federated), run_name="__main__")
