"""Shared utilities for capital optimizer modules."""
from __future__ import annotations


def _error_result(msg: str) -> dict:
    """Return a standardized error result dict."""
    return {"status": "ERROR", "error": msg}
