"""
WEALTH Core — Personal Finance Domain (D1).

Extracted from internal/personal_finance.py. Re-exports existing engines.
Thin wrapper — real implementation stays in internal/ until full extraction.

Modes: track, summary, runway, net_worth, epf, zakat

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

try:
    from internal.personal_finance import (
        PersonalFinanceEngine,
        cashflow_track,
        cashflow_summary,
        runway_calculate,
        net_worth_snapshot,
        epf_project,
        zakat_calculate,
    )
    _PF_AVAILABLE = True
except ImportError:
    _PF_AVAILABLE = False

    class PersonalFinanceEngine:
        pass

    def cashflow_track(*args, **kwargs):
        return {"error": "Personal finance engine not available"}

    def cashflow_summary(*args, **kwargs):
        return {"error": "Personal finance engine not available"}

    def runway_calculate(*args, **kwargs):
        return {"error": "Personal finance engine not available"}

    def net_worth_snapshot(*args, **kwargs):
        return {"error": "Personal finance engine not available"}

    def epf_project(*args, **kwargs):
        return {"error": "Personal finance engine not available"}

    def zakat_calculate(*args, **kwargs):
        return {"error": "Personal finance engine not available"}


__all__ = [
    "PersonalFinanceEngine",
    "cashflow_track",
    "cashflow_summary",
    "runway_calculate",
    "net_worth_snapshot",
    "epf_project",
    "zakat_calculate",
    "is_available",
]


def is_available() -> bool:
    """Check if personal finance engines are available."""
    return _PF_AVAILABLE
