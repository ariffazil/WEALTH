"""CoinGecko public REST adapter for WEALTH CryptoRouter.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md §3.1

Constitutional mapping:
  F1 AMANAH       read-only, no auth, no state mutation, no wallet
  F2 TRUTH        source_uri mandatory; epistemic_label per kind (OBS for spot, DER for 24h)
  F9 ANTIHANTU    precise provider/asset/kind triples — no ambiguity in chain provenance
  F11 AUDITABILITY response_hash chains to VAULT999
  F12 RESILIENCE  5s hard timeout; RateLimitHit on 429; no retries (router decides)

Constraints:
  - Free tier: 10–30 calls/min ceiling (router respects the budget hint)
  - Public endpoints, no API key needed
  - No third-party deps beyond urllib (stdlib)
"""
from __future__ import annotations

import hashlib
import json
import logging
import urllib.error
import urllib.request
from typing import Literal

from wealth_core.ingest.crypto.router import (
    EpistemicLabel,
    ProviderError,
    RateLimitHit,
    SourceBundle,
)

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# F2 TRUTH: explicit WEALTH-symbol → CoinGecko id mapping for major pairs.
# Caller can pass a CoinGecko id directly (e.g. "uniswap") for obscure
# tokens — fallback lower-cases the input.
_MAJOR_PAIR_IDS: dict[str, str] = {
    "BTC":   "bitcoin",
    "ETH":   "ethereum",
    "wBTC":  "wrapped-bitcoin",
    "USDC":  "usd-coin",
    "USDT":  "tether",
    "SOL":   "solana",
    "BNB":   "binancecoin",
    "XRP":   "ripple",
    "ADA":   "cardano",
    "DOGE":  "dogecoin",
    "MATIC": "matic-network",
    "DOT":   "polkadot",
}


class CoinGeckoAdapter:
    """Read-only fetcher. Stateless. Router owns cache + fallback chain."""

    provider = "coingecko"

    def fetch(
        self,
        asset: str,
        kind: Literal["spot_price", "24h_change"],
    ) -> SourceBundle:
        if kind == "spot_price":
            return self._fetch_spot(asset)
        if kind == "24h_change":
            return self._fetch_24h(asset)
        raise ProviderError(
            f"coingecko does not support kind={kind!r} "
            f"(router dispatch bug — should not reach adapter)"
        )

    def _fetch_spot(self, asset: str) -> SourceBundle:
        cg_id = self._symbol_to_cg_id(asset)
        url = (
            f"{COINGECKO_BASE}/simple/price"
            f"?ids={cg_id}&vs_currencies=usd"
        )
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("coingecko free-tier ceiling hit (10/min)")

        try:
            payload = json.loads(raw)
            value = float(payload[cg_id]["usd"])
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise ProviderError(f"coingecko schema mismatch: {e}") from e

        return SourceBundle(
            provider=self.provider,
            asset=asset,
            kind="spot_price",
            value=value,
            currency="USD",
            source_uri=url,
            epistemic_label=EpistemicLabel.OBS,
            response_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )

    def _fetch_24h(self, asset: str) -> SourceBundle:
        """24h_change is computed from OHLC — DER, not OBS."""
        cg_id = self._symbol_to_cg_id(asset)
        url = (
            f"{COINGECKO_BASE}/coins/markets"
            f"?vs_currency=usd&ids={cg_id}"
            f"&sparkline=false&price_change_percentage=24h"
        )
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("coingecko 30/min markets ceiling")

        try:
            payload = json.loads(raw)
            if not payload:
                raise ProviderError("coingecko returned empty markets list")
            pct = float(payload[0].get("price_change_percentage_24h", 0))
        except (KeyError, ValueError, IndexError, json.JSONDecodeError) as e:
            raise ProviderError(f"coingecko schema mismatch: {e}") from e

        return SourceBundle(
            provider=self.provider,
            asset=asset,
            kind="24h_change",
            value=pct,
            currency="PCT",
            source_uri=url,
            epistemic_label=EpistemicLabel.DER,
            response_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            extras={"coingecko_id": cg_id},
        )

    def _symbol_to_cg_id(self, asset: str) -> str:
        """Light mapper. Falls back to lowercased symbol for obscure tokens."""
        upper = asset.upper()
        if upper in _MAJOR_PAIR_IDS:
            return _MAJOR_PAIR_IDS[upper]
        return asset.lower()

    def _http_get(self, url: str) -> tuple[str, int]:
        """Bare urllib. F12: 5s timeout hard cap. No retries (router decides)."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "arifOS-WEALTH-CryptoRouter/1.0",
                "Accept":      "application/json",
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode("utf-8"), resp.status
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return "", 429
            raise ProviderError(f"coingecko HTTP {e.code}: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"coingecko network failure: {e}") from e
