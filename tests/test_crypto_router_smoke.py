"""Step 8.5 Crypto Router Smoke Test -- substrate proof before canonical touch.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md
        + F13 reinforcement 2026-08-18 (mandatory pre-Step-9 gate).

Proves the router logic in isolation BEFORE touching the federated-11-
canonical surface (Step 9). Uses unittest.mock to inject controlled
provider failures. Deterministic; no live network dependency.

Scenarios verified:
  1. Full chain: Binance primary returns success bundle
  2. Binance 429 -> CoinGecko fallback
  3. Binance ProviderError (geo-block) -> CoinGecko fallback
  4. Binance + CoinGecko fail -> DefiLlama fallback
     (Option B silent-redundancy proven)
  5. All providers fail, no cache -> AllProvidersFailed (F12 HOLD)
  6. Cache hit after all-fail -> SPEC epistemic label (F7 humility)
  7. WEALTH_BINANCE_ENABLED=false -> Binance skipped (F12 env-guard)

Run: cd /root/WEALTH && python3 tests/test_crypto_router_smoke.py

Exit code 0 = all scenarios pass; non-zero = at least one failed.
"""
from __future__ import annotations

import os
import sys

# Bootstrap: ensure /root/WEALTH on sys.path so engines/crypto/* (a PEP 420
# namespace package) and wealth_core/ importable.
sys.path.insert(0, "/root/WEALTH")
os.environ.setdefault("WEALTH_BINANCE_ENABLED", "true")

from unittest.mock import MagicMock, patch  # noqa: E402

from wealth_core.ingest.crypto.router import (  # noqa: E402
    CryptoRouter,
    SourceBundle,
    EpistemicLabel,
    RateLimitHit,
    ProviderError,
    AllProvidersFailed,
)


# ━━━ Helpers ━━━

def _bundle(provider: str, asset: str = "BTC", kind: str = "spot_price",
            value: float = 65000.0) -> SourceBundle:
    """Canonical mock SourceBundle. Source_uri is fake but valid syntax."""
    return SourceBundle(
        provider=provider,
        asset=asset,
        kind=kind,
        value=value,
        currency="USD",
        source_uri=f"https://{provider}.example/price",
        epistemic_label=EpistemicLabel.OBS,
        response_hash="deadbeefcafebabe" * 4,
    )


def _adapter(provider: str, behavior=None):
    """Build a MagicMock adapter matching the protocol.

    behavior=None: fetch returns success bundle.
    behavior='rate_limit': fetch raises RateLimitHit.
    behavior='provider_error': fetch raises ProviderError.
    behavior='network': fetch raises ProviderError (network framing).
    """
    adapter = MagicMock()
    adapter.provider = provider
    if behavior is None:
        adapter.fetch.return_value = _bundle(provider)
    elif behavior == "rate_limit":
        adapter.fetch.side_effect = RateLimitHit(f"{provider} 429")
    elif behavior == "provider_error":
        adapter.fetch.side_effect = ProviderError(f"{provider} schema mismatch")
    elif behavior == "network":
        adapter.fetch.side_effect = ProviderError(f"{provider} network failure")
    return adapter


def _patch_all(behaviors: dict):
    """Patch all 4 adapter classes at their true module locations.

    The registry imports each via importlib.import_module + getattr(...).
    Patching the class in its home module means the next
    `getattr(importlib.import_module(path), ClassName)()` returns the mock.
    """
    return [
        patch("engines.crypto.binance.fetch_binance.BinanceAdapter",
              return_value=_adapter("binance_public", behaviors.get("binance_public"))),
        patch("engines.crypto.coingecko.fetch_coingecko.CoinGeckoAdapter",
              return_value=_adapter("coingecko", behaviors.get("coingecko"))),
        patch("engines.crypto.defillama.fetch_defillama.DefiLlamaAdapter",
              return_value=_adapter("defillama", behaviors.get("defillama"))),
    ]


# ━━━ Scenarios ━━━

def test_full_chain_success():
    """All providers succeed; Binance primary returns first."""
    router = CryptoRouter()
    patches = _patch_all({
        "binance_public": None,
        "coingecko":      None,
        "defillama":      None,
    })
    with patches[0], patches[1], patches[2]:
        result = router.fetch(asset="BTC", kind="spot_price")
        assert result.provider == "binance_public", \
            f"expected binance_public, got {result.provider}"
        assert result.value == 65000.0, f"expected 65000.0, got {result.value}"
    print("  PASS: full chain -- Binance primary returned")


def test_binance_rate_limit_coingecko_catches():
    """Binance returns 429; router catches, falls to CoinGecko."""
    router = CryptoRouter()
    patches = _patch_all({
        "binance_public": "rate_limit",
        "coingecko":      None,
        "defillama":      None,
    })
    with patches[0], patches[1], patches[2]:
        result = router.fetch(asset="BTC", kind="spot_price")
        assert result.provider == "coingecko", \
            f"expected coingecko, got {result.provider}"
    print("  PASS: binance 429 -> CoinGecko fallback")


def test_binance_provider_error_coingecko_catches():
    """Binance raises ProviderError (geo-block or schema); router falls to CoinGecko."""
    router = CryptoRouter()
    patches = _patch_all({
        "binance_public": "provider_error",
        "coingecko":      None,
        "defillama":      None,
    })
    with patches[0], patches[1], patches[2]:
        result = router.fetch(asset="BTC", kind="spot_price")
        assert result.provider == "coingecko"
    print("  PASS: binance ProviderError -> CoinGecko fallback")


def test_binance_and_coingecko_fail_defillama_catches():
    """Both fail; DefiLlama catches (Option B silent-redundancy proven)."""
    router = CryptoRouter()
    patches = _patch_all({
        "binance_public": "rate_limit",
        "coingecko":      "provider_error",
        "defillama":      None,
    })
    with patches[0], patches[1], patches[2]:
        result = router.fetch(asset="BTC", kind="spot_price")
        assert result.provider == "defillama", \
            f"expected defillama, got {result.provider}"
    print("  PASS: binance + coingecko fail -> DefiLlama fallback (silent-redundancy proven)")


def test_all_fail_no_cache_holds():
    """All providers fail; no cache populated -> AllProvidersFailed (F12 HOLD)."""
    router = CryptoRouter()
    patches = _patch_all({
        "binance_public": "network",
        "coingecko":      "provider_error",
        "defillama":      "rate_limit",
    })
    with patches[0], patches[1], patches[2]:
        try:
            router.fetch(asset="BTC", kind="spot_price")
            raise AssertionError("expected AllProvidersFailed to be raised")
        except AllProvidersFailed as e:
            assert "All 3 providers failed" in str(e), \
                f"unexpected AllProvidersFailed message: {e}"
    print("  PASS: all fail, no cache -> AllProvidersFailed (F12 HOLD)")


def test_cache_hit_after_all_fail_serves_stale_spec():
    """Populate cache, then all fail -> cache serves with SPEC label (F7 humility)."""
    router = CryptoRouter()

    # First call: all succeed, populates cache via Binance (position 1)
    patches = _patch_all({
        "binance_public": None,
        "coingecko":      None,
        "defillama":      None,
    })
    with patches[0], patches[1], patches[2]:
        first = router.fetch(asset="BTC", kind="spot_price")
        assert first.provider == "binance_public"
        assert first.epistemic_label == EpistemicLabel.OBS, \
            "fresh cache hit should keep OBS label"

    # Now all fail; expect stale cache with SPEC label
    fail_patches = _patch_all({
        "binance_public": "network",
        "coingecko":      "provider_error",
        "defillama":      "rate_limit",
    })
    with fail_patches[0], fail_patches[1], fail_patches[2]:
        second = router.fetch(asset="BTC", kind="spot_price")
        assert second.provider == "binance_public", \
            f"expected cached bundle from binance_public, got {second.provider}"
        assert second.epistemic_label == EpistemicLabel.SPEC, \
            f"expected SPEC on stale cache, got {second.epistemic_label}"
    print("  PASS: cache hit after all-fail -> stale cache, SPEC label (F7 humility)")


def test_geo_skip_env_guard():
    """WEALTH_BINANCE_ENABLED=false skips Binance; router falls through directly."""
    from wealth_core.ingest.crypto import provider_config as pc

    original_value = pc.WEALTH_BINANCE_ENABLED
    pc.WEALTH_BINANCE_ENABLED = False  # F12 fail-closed env-guard flipped

    try:
        router = CryptoRouter()
        patches = _patch_all({
            "binance_public": None,  # would succeed if reached
            "coingecko":      None,  # safe fallback
            "defillama":      None,
        })
        with patches[0], patches[1], patches[2]:
            result = router.fetch(asset="BTC", kind="spot_price")
            # Binance must be SKIPPED; result comes from CoinGecko (position 2)
            assert result.provider == "coingecko", \
                f"expected coingecko (Binance skipped), got {result.provider}"
    finally:
        pc.WEALTH_BINANCE_ENABLED = original_value  # restore

    print("  PASS: WEALTH_BINANCE_ENABLED=false -> Binance skipped (F12 env-guard)")


# ━━━ Runner ━━━

def main():
    print("\n━━ Step 8.5 Crypto Router Smoke Test ━━\n")
    tests = [
        test_full_chain_success,
        test_binance_rate_limit_coingecko_catches,
        test_binance_provider_error_coingecko_catches,
        test_binance_and_coingecko_fail_defillama_catches,
        test_all_fail_no_cache_holds,
        test_cache_hit_after_all_fail_serves_stale_spec,
        test_geo_skip_env_guard,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n━━ Smoke test summary: {passed} pass, {failed} fail of {len(tests)} ━━\n")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
