"""WEALTH Crypto Router — L1 dispatch with auto-fallback.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md §3.2

Constitutional mapping (per proposal §4):
  F1 AMANAH       read-only fetch, no wallet, no order placement
  F2 TRUTH        SourceBundle.epistemic_label mandatory per response
  F3 TRI-WITNESS  per-fallback witness emission via logger (future → VAULT999)
  F4 CLARITY      60s cache reduces entropy (cache hit → SPEC label)
  F7 HUMILITY     SPEC label on stale cache, confidence capped at 0.95
  F11 AUDITABILITY response_hash chains into VAULT999
  F12 RESILIENCE  per-provider rate budget, all-priority fail → cache+HOLD
  F13 SOVEREIGN   WEALTH advisory only — never triggers trading
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .provider_config import (
    DEFAULT_PRIORITY,
    KIND_LITERAL,
    apply_geo_skip,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SourceBundle",
    "CryptoRouter",
    "EpistemicLabel",
    "RateLimitHit",
    "ProviderError",
    "AllProvidersFailed",
]


class EpistemicLabel(str, Enum):
    """F2 TRUTH — epistemic classification per response field."""
    OBS     = "OBS"
    DER     = "DER"
    INT     = "INT"
    SPEC    = "SPEC"
    UNKNOWN = "UNKNOWN"


class SourceBundle(BaseModel):
    """Canonical crypto-data bundle. All adapters must emit this contract.

    F2: source_uri + epistemic_label mandatory per response.
    F11: response_hash chains into VAULT999.
    F13: advisory only — never triggers trading.
    """
    provider:        Literal["coingecko", "binance_public", "defillama", "arkham"]
    asset:           str
    kind:            KIND_LITERAL       # type: ignore[valid-type]
    value:           float
    currency:        str = "USD"
    timestamp:       datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_uri:      str
    epistemic_label: EpistemicLabel = EpistemicLabel.OBS
    response_hash:   str | None = None
    extras:          dict[str, Any] | None = None


class RateLimitHit(Exception):
    """Provider returned 429. Router auto-fallbacks to next priority."""
    pass


class ProviderError(Exception):
    """5xx, network failure, schema mismatch. Router auto-fallbacks."""
    pass


class AllProvidersFailed(Exception):
    """All priorities failed AND no cache. Caller MUST HOLD.

    F12: this is the explicit fail-closed signal. Downstream tooling
    must not synthesize data when this is raised.
    """
    pass


class _CacheEntry:
    __slots__ = ("bundle", "stored_at")

    def __init__(self, bundle: SourceBundle):
        self.bundle = bundle
        self.stored_at = datetime.now(timezone.utc)


class CryptoRouter:
    """L1 dispatch with priority-based fallback.

    Wired to existing `wealth_sensor_fetch` via the asset_class="crypto"
    discriminator — no new canonical tool surface.
    """

    DEFAULT_CACHE_TTL = 60  # seconds; F4 CLARITY

    def __init__(self, cache_ttl_seconds: int = DEFAULT_CACHE_TTL):
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[tuple, _CacheEntry] = {}
        self._rate_window_hint: dict[str, int] = {
            "coingecko":      10,
            "binance_public": 1200,
            "defillama":      300,
            "arkham":         0,
        }

    def fetch(
        self,
        asset: str,
        kind: KIND_LITERAL,
        priority: list[str] | None = None,
    ) -> SourceBundle:
        """Dispatch + auto-fallback.

        Args:
            asset:    "BTC", "ETH", chain address (Arkham only)
            kind:     data type — determines default priority chain
            priority: optional override (e.g., obscure alt → defillama first)

        Returns:
            SourceBundle from highest-priority responsive provider.

        Raises:
            AllProvidersFailed: every provider failed AND no cache.
                               Caller MUST HOLD (F12 fail-closed).
        """
        chain = apply_geo_skip(priority or DEFAULT_PRIORITY.get(kind, ["coingecko"]))
        if not chain:
            raise AllProvidersFailed(
                f"No providers available for kind={kind} "
                f"(geo-skip may have emptied the chain)"
            )

        last_err: Exception | None = None
        for provider in chain:
            try:
                bundle = self._dispatch(provider, asset, kind)
            except RateLimitHit as e:
                logger.warning(
                    f"crypto witness: provider={provider} kind={kind} "
                    f"asset={asset} -> FALLBACK reason=rate_limit"
                )
                last_err = e
                continue
            except ProviderError as e:
                logger.warning(
                    f"crypto witness: provider={provider} kind={kind} "
                    f"asset={asset} -> FALLBACK reason=provider_error"
                )
                last_err = e
                continue

            self._cache[(asset, kind)] = _CacheEntry(bundle)
            return bundle

        cached = self._get_cache(asset, kind)
        if cached is not None:
            cached = cached.model_copy(deep=True)
            cached.epistemic_label = EpistemicLabel.SPEC
            return cached

        raise AllProvidersFailed(
            f"All {len(chain)} providers failed for asset={asset} kind={kind}; "
            f"no cache. Last error: {last_err}"
        )

    def _dispatch(
        self,
        provider: str,
        asset: str,
        kind: KIND_LITERAL,
    ) -> SourceBundle:
        """L2 dispatch via registry. Lazy import keeps cold-start light."""
        from .adapters.registry import get_adapter
        adapter = get_adapter(provider)
        return adapter.fetch(asset=asset, kind=kind)

    def _get_cache(self, asset: str, kind: str) -> SourceBundle | None:
        key = (asset, kind)
        entry = self._cache.get(key)
        if entry is None:
            return None
        age = (datetime.now(timezone.utc) - entry.stored_at).total_seconds()
        if age > self.cache_ttl:
            return None
        return entry.bundle

    @staticmethod
    def bundle_hash(raw_response: bytes | str) -> str:
        """F11: response_hash for VAULT999 chain. sha256(raw)."""
        if isinstance(raw_response, str):
            raw_response = raw_response.encode("utf-8")
        return hashlib.sha256(raw_response).hexdigest()
