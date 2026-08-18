"""DefiLlama public REST adapter for WEALTH CryptoRouter.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md §3.1

DefiLlama's /prices/current is an aggregator -- it pulls from Binance,
Coinbase, MEXC, Kraken, and other CEXes. This is the Option B
silent-redundancy guarantee: even when direct Binance fails, the
DefiLlama position-3 fallback still carries Binance-feed price data.

Constitutional mapping:
  F1  read-only, no auth, no state mutation
  F2  source_uri mandatory; epistemic_label = OBS for spot_price and TVL
  F11 response_hash chains to VAULT999
  F12 silent redundancy; lenient free-tier (~no hard rate limit)
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

COINLLAMA_PRICES = "https://coins.llama.fi/prices/current"
LLAMA_TVL = "https://api.llama.fi/tvl"

# F2 TRUTH: explicit WEALTH-symbol -> DefiLlama coin-identifier mapping.
# DefiLlama accepts `coingecko:<id>` identifiers for cross-source clarity.
_MAJOR_COIN_IDS: dict[str, str] = {
    "BTC":   "coingecko:bitcoin",
    "ETH":   "coingecko:ethereum",
    "wBTC":  "coingecko:wrapped-bitcoin",
    "USDC":  "coingecko:usd-coin",
    "USDT":  "coingecko:tether",
    "SOL":   "coingecko:solana",
    "BNB":   "coingecko:binancecoin",
    "XRP":   "coingecko:ripple",
    "ADA":   "coingecko:cardano",
    "DOGE":  "coingecko:dogecoin",
    "MATIC": "coingecko:matic-network",
    "DOT":   "coingecko:polkadot",
}


class DefiLlamaAdapter:
    """Read-only fetcher via DefiLlama public REST. No auth required."""

    provider = "defillama"

    def fetch(self, asset: str, kind: Literal["spot_price", "tvl"]) -> SourceBundle:
        if kind == "spot_price":
            return self._fetch_spot(asset)
        if kind == "tvl":
            return self._fetch_tvl(asset)
        raise ProviderError(
            f"defillama does not support kind={kind!r} "
            f"(router dispatch bug -- should not reach adapter)"
        )

    def _fetch_spot(self, asset: str) -> SourceBundle:
        coin_id = self._symbol_to_coin_id(asset)
        url = f"{COINLLAMA_PRICES}/{coin_id}"
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("defillama rate limit hit")

        try:
            payload = json.loads(raw)
            coins = payload.get("coins", {})
            if coin_id not in coins:
                raise ProviderError(
                    f"defillama returned no price for {coin_id}"
                )
            value = float(coins[coin_id]["price"])
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise ProviderError(f"defillama schema mismatch: {e}") from e

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

    def _fetch_tvl(self, protocol: str) -> SourceBundle:
        """For TVL, the `asset` parameter is the protocol slug (e.g., 'uniswap')."""
        slug = protocol.lower()
        url = f"{LLAMA_TVL}/{slug}"
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("defillama tvl rate limit")

        try:
            value = float(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            raise ProviderError(f"defillama tvl schema mismatch: {e}") from e

        return SourceBundle(
            provider=self.provider,
            asset=protocol,
            kind="tvl",
            value=value,
            currency="USD",
            source_uri=url,
            epistemic_label=EpistemicLabel.OBS,
            response_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )

    def _symbol_to_coin_id(self, asset: str) -> str:
        """Light mapper. Falls back to `coingecko:<lowercase>` for obscure tokens."""
        upper = asset.upper()
        if upper in _MAJOR_COIN_IDS:
            return _MAJOR_COIN_IDS[upper]
        return f"coingecko:{asset.lower()}"

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
            raise ProviderError(f"defillama HTTP {e.code}: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"defillama network failure: {e}") from e
