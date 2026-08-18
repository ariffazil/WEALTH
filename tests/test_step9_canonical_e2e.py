"""Step 9 E2E verification -- canonical surface routing.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md §3.3 + Step 9.

Proves capital_market(asset_class="crypto", ...) routes to
crypto_router.fetch() and returns a properly wrapped SourceBundle.

Approach:
  1. Stub the FastMCP `@tool` decorator so we can call register_canonical_tools.
  2. Capture the `capital_market` callable from the registrar.
  3. Mock `CryptoRouter.fetch` to return a deterministic SourceBundle
     (avoids live network dependency, mirrors smoke-test pattern).
  4. Invoke the canonical tool and assert on the wrapped envelope.

Run: cd /root/WEALTH && python3 tests/test_step9_canonical_e2e.py
"""
from __future__ import annotations

import asyncio
import sys
import os
import traceback

sys.path.insert(0, "/root/WEALTH")
os.environ.setdefault("WEALTH_BINANCE_ENABLED", "true")


# ━━━ Stub FastMCP surface so register_canonical_tools works offline ━━━

class _StubMCP:
    """Captures FastMCP `@tool`-decorated functions for direct invocation."""
    def __init__(self):
        self.tools: dict[str, object] = {}

    def tool(self, name=None, **_kwargs):
        def decorator(func):
            self.tools[name or func.__name__] = func
            return func
        return decorator

    def __getattr__(self, name):
        # Any unanticipated @mcp.X usage becomes a no-op decorator.
        return lambda **kwargs: (lambda f: f)


# ━━━ Capture the canonical tools ━━━

from wealth_mcp.tools.canonical import register_canonical_tools  # noqa: E402

_stub = _StubMCP()
register_canonical_tools(_stub)
capital_market = _stub.tools["capital_market"]

print(f"━━ Step 9 E2E — captured capital_market via stub; tools={list(_stub.tools.keys())} ━━\n")


# ━━━ Mock the router so we don't hit live network ━━━

from unittest.mock import patch, AsyncMock  # noqa: E402
from wealth_core.ingest.crypto.router import (  # noqa: E402
    CryptoRouter,
    EpistemicLabel,
    SourceBundle,
)


def _mock_bundle() -> SourceBundle:
    return SourceBundle(
        provider="binance_public",
        asset="BTC",
        kind="spot_price",
        value=65000.0,
        currency="USD",
        source_uri="https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
        epistemic_label=EpistemicLabel.OBS,
        response_hash="step9_e2e_smoketest_mock",
    )


async def test_crypto_routing():
    """asset_class='crypto' must invoke CryptoRouter and wrap result."""
    mock_bundle = _mock_bundle()

    with patch.object(CryptoRouter, "fetch", return_value=mock_bundle) as mock_fetch:
        wrapped = await capital_market(
            mode="spot_price",
            asset_class="crypto",
            stock_payload={"asset": "BTC", "kind": "spot_price"},
            session_id="step9_e2e",
            actor_id="kimi-code/FI-008",
        )

    # Assertions
    assert isinstance(wrapped, dict), f"wrapped must be dict, got {type(wrapped)}"
    assert wrapped.get("status", "OK") != "ERROR", \
        f"Step 9 ERROR: {wrapped}"
    inner = wrapped.get("result", {})
    assert isinstance(inner, dict), f"inner must be dict, got {type(inner)}"

    # SourceBundle.model_dump() fields (Pydantic v2)
    assert inner.get("provider") == "binance_public", \
        f"provider mismatch: {inner.get('provider')}"
    assert inner.get("asset") == "BTC", \
        f"asset mismatch: {inner.get('asset')}"
    assert inner.get("kind") == "spot_price", \
        f"kind mismatch: {inner.get('kind')}"
    assert inner.get("value") == 65000.0, \
        f"value mismatch: {inner.get('value')}"
    assert "api.binance.com" in inner.get("source_uri", ""), \
        f"source_uri mismatch: {inner.get('source_uri')}"

    # Wrap envelope (EpistemicTag enum value is "OBSERVED", not the
    # crypto_adapter's EpistemicLabel.OBS string -- different enums
    # surfaced by wrap_result at the federated boundary)
    assert wrapped.get("epistemic_tag") == "OBSERVED", \
        f"epistemic_tag: {wrapped.get('epistemic_tag')}"
    assert wrapped.get("tool_name") == "capital_market", \
        f"tool_name attribution: {wrapped.get('tool_name')}"
    sources = wrapped.get("source_attribution", [])
    assert any("binance_public" in s for s in sources), \
        f"source_attribution missing binance_public: {sources}"

    # Mock was actually called
    assert mock_fetch.called, "CryptoRouter.fetch was NOT invoked"

    print("  ━━━ Scenario A: asset_class='crypto' happy-path ━━━")
    print(f"  provider       = {inner.get('provider')}")
    print(f"  asset          = {inner.get('asset')}")
    print(f"  kind           = {inner.get('kind')}")
    print(f"  value          = {inner.get('value')}")
    print(f"  source_uri     = {inner.get('source_uri')}")
    print(f"  epistemic_tag  = {wrapped.get('epistemic_tag')}")
    print(f"  source_attr    = {sources}")
    print(f"  session_id     = {wrapped.get('session_id')}")
    print("  PASS: canonical surface routes to crypto_router; envelope carries F2/F11 attribution")


async def test_default_asset_class_unchanged():
    """asset_class default 'fx_commodity' must NOT touch crypto_router.

    Proves the diff is backward-compatible: existing fx/commodity/stock
    callers see no behavior change.
    """
    # We can't easily reach the legacy `_call_legacy_tool` (it's an
    # internal closure to the federated server's legacy bridge).
    # Instead: assert that the new branch was NOT taken -- if a
    # CryptoRouter.fetch call happened, that means our branch fired
    # by accident on the default path.
    with patch.object(CryptoRouter, "fetch") as mock_fetch:
        try:
            # mode="indicator" is a known existing mode. asset_class
            # is left at default ("fx_commodity"). The function will
            # attempt to call the legacy indicator path, which may
            # itself fail in offline mode, but that's not crypto's
            # concern -- we only assert crypto_router was NOT called.
            await capital_market(
                mode="indicator",
                indicator="usd_myr",
                country="MYS",
                session_id="step9_backcompat_test",
            )
        except Exception:
            # Legacy bridge may legitimately fail offline; we only
            # care that crypto_router was not invoked.
            pass

    assert not mock_fetch.called, \
        "CryptoRouter.fetch was called on default asset_class path -- " \
        "backward compat broken"

    print("\n  ━━━ Scenario B: asset_class default 'fx_commodity' (back-compat) ━━━")
    print("  PASS: crypto_router NOT invoked on existing-mode call paths")


async def test_crypto_error_envelope():
    """CryptoRouter exception must produce a structured ERROR envelope,
    not crash the canonical surface (F12 RESILIENCE)."""
    with patch.object(
        CryptoRouter, "fetch",
        side_effect=RuntimeError("simulated provider outage"),
    ):
        wrapped = await capital_market(
            mode="spot_price",
            asset_class="crypto",
            stock_payload={"asset": "ETH", "kind": "spot_price"},
        )

    # wrap_result nests status inside result; errors[] is wrapper-level
    assert wrapped.get("result", {}).get("status") == "ERROR", \
        f"expected ERROR envelope, got: {wrapped}"
    assert wrapped.get("result", {}).get("error_code") == "CRYPTO_ROUTER_FAILED", \
        f"wrong error_code: {wrapped}"
    errs = wrapped.get("errors", [])
    assert any("simulated provider outage" in e for e in errs), \
        f"error message not propagated: {errs}"

    print("\n  ━━━ Scenario C: crypto_router exception ━━━")
    print(f"  error_code    = {wrapped.get('result', {}).get('error_code')}")
    print(f"  errors        = {errs}")
    print("  PASS: F12 RESILIENCE -- canonical surface returns ERROR envelope, not crash")


async def main():
    print("\n━━ Step 9 E2E -- capital_market(asset_class='crypto') ━━\n")
    passed = 0
    failed = 0
    tests = [
        test_crypto_routing,
        test_default_asset_class_unchanged,
        test_crypto_error_envelope,
    ]
    for t in tests:
        try:
            await t()
            passed += 1
        except Exception as e:
            print(f"\n  FAIL: {t.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n━━ Step 9 E2E summary: {passed} pass, {failed} fail of {len(tests)} ━━\n")
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
