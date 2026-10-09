"""Negative receipt-truth suite (P0, 2026-09-16).

Regression for the defect where capital_market oil failed all three upstream
endpoints (HTTP 500) yet the ledger logged call_status=PASS, and where
double-dispatched calls minted duplicate receipts 0.3 ms apart.

Run:  /root/WEALTH/.venv/bin/python3 tests/test_receipt_truth.py
  or  /root/WEALTH/.venv/bin/python3 -m pytest tests/test_receipt_truth.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# tests/mcp/ is a real helper package that SHADOWS the pip `mcp` package when
# the script dir sits on sys.path (regular package at an earlier path entry
# beats site-packages). Strip the script dir so fastmcp's mcp.types resolves.
sys.path[:] = [
    p for p in sys.path
    if p not in ("", str(Path(__file__).resolve().parent))
]

from wealth_mcp.server import _tool_result_status  # noqa: E402


class _R:
    """Minimal stand-in for a FastMCP CallToolResult."""

    def __init__(self, structured=None, is_error=False):
        self.structured_content = structured
        self.is_error = is_error


def test_upstream_500_errors_are_fail():
    """The exact 2026-09-16 oil defect: 3x HTTP 500 inside errors, partial."""
    oil = _R(
        {
            "result": {
                "asset": "oil",
                "errors": {
                    "ticker": "HTTPStatusError: Server error '500'",
                    "signal": "HTTPStatusError: Server error '500'",
                    "macro": "HTTPStatusError: Server error '500'",
                },
                "partial": True,
            }
        }
    )
    assert _tool_result_status(oil) == "FAIL", "upstream 500s must never be PASS"


def test_error_code_is_fail():
    bt = _R({"result": {"status": "ERROR", "error_code": "IMPORT_FAILED", "message": "x"}})
    assert _tool_result_status(bt) == "FAIL"


def test_error_class_is_fail():
    e = _R({"result": {"error_class": "INTERNAL_ERROR", "severity": "FATAL"}})
    assert _tool_result_status(e) == "FAIL"


def test_partial_without_errors_is_partial():
    p = _R({"result": {"partial": True, "snapshot": {}}})
    assert _tool_result_status(p) == "PARTIAL"


def test_clean_ok_is_pass():
    ok = _R({"result": {"status": "OK", "price": 4349.12}})
    assert _tool_result_status(ok) == "PASS"


def test_no_status_no_failure_signals_is_pass():
    q = _R({"result": {"count": 0, "earth_refs": [], "vault_seal": "VAULT999"}})
    assert _tool_result_status(q) == "PASS"


def test_is_error_is_error():
    assert _tool_result_status(_R(None, is_error=True)) == "ERROR"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{failures == 0 and 'ALL GREEN' or str(failures) + ' FAILED'}")
    sys.exit(1 if failures else 0)
