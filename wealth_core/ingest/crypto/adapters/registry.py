"""Adapter registry — L2 string → instance dispatch.

Origin: proposal §3.2 (router indirection through string-named adapters).

Lazy import keeps cold-start cost near-zero: only the requested
provider module loads per call. ImportError is converted to ProviderError
so the router's existing fallback chain handles not-yet-implemented
adapters gracefully — promoting adapters one-at-a-time never breaks
the live tree (F1 AMANAH).
"""
from __future__ import annotations

import importlib
from typing import Any, Protocol


class _AdapterProto(Protocol):
    provider: str
    def fetch(self, asset: str, kind: str) -> Any: ...


_PROVIDER_MAP: dict[str, tuple[str, str]] = {
    "coingecko":      ("engines.crypto.coingecko.fetch_coingecko",      "CoinGeckoAdapter"),
    "binance_public": ("engines.crypto.binance.fetch_binance",          "BinanceAdapter"),
    "defillama":      ("engines.crypto.defillama.fetch_defillama",      "DefiLlamaAdapter"),
    "arkham":         ("engines.crypto.arkham.fetch_arkham",            "ArkhamAdapter"),
}


def get_adapter(provider: str) -> _AdapterProto:
    """Resolve provider name → adapter instance. Lazy load.

    ImportError becomes ProviderError so the router treats missing
    adapters as transient failures (falls back) rather than crashes.
    ValueError for unknown provider names — caller bug.
    """
    if provider not in _PROVIDER_MAP:
        raise ValueError(f"Unknown crypto provider: {provider!r}")

    module_path, class_name = _PROVIDER_MAP[provider]
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()
    except ImportError as e:
        # F1 AMANAH: defer gracefully instead of crashing live tree
        # when an adapter hasn't been promoted yet.
        from ..router import ProviderError
        raise ProviderError(
            f"provider {provider!r} module not yet implemented: {e}"
        ) from e
