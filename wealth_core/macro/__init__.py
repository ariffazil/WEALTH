"""
WEALTH Core — Macro/Field Domain.

Extracted from internal/market_data.py and host/ingest/.
Field/market data engines — FX, commodities, macro indicators.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

try:
    from internal.monolith import (
        wealth_field_macro,
        ingest_fetch,
        ingest_snapshot,
        ingest_sources,
        ingest_health,
    )
    _MACRO_AVAILABLE = True
except ImportError:
    _MACRO_AVAILABLE = False

    def wealth_field_macro(*args, **kwargs):
        return {"error": "Macro engine not available"}

    def ingest_fetch(*args, **kwargs):
        return {"error": "Ingest engine not available"}

    def ingest_snapshot(*args, **kwargs):
        return {"error": "Ingest engine not available"}

    def ingest_sources(*args, **kwargs):
        return {"error": "Ingest engine not available"}

    def ingest_health(*args, **kwargs):
        return {"error": "Ingest engine not available"}


__all__ = [
    "wealth_field_macro",
    "ingest_fetch",
    "ingest_snapshot",
    "ingest_sources",
    "ingest_health",
    "is_available",
]


def is_available() -> bool:
    return _MACRO_AVAILABLE
