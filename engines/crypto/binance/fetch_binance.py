"""Binance public REST adapter for WEALTH CryptoRouter.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md §3.1

Constitutional mapping:
  F1 AMANAH       read-only; no auth for /api/v3/ticker/* endpoints
  F2 TRUTH        source_uri mandatory; epistemic_label per kind
                  (OBS for spot_price, DER for 24h_change + depth_top20)
  F9 ANTIHANTU    precise provider/asset/kind triples
  F11 AUDITABILITY response_hash chains to VAULT999
  F12 RESILIENCE  5s timeout; RateLimitHit on 429; geo-detection
                  (HTTP 403/451 -> ProviderError so router skips via
                   WEALTH_BINANCE_ENABLED env gate)

Constraints:
  - Public endpoints only; no API key required
  - 1200 req/min ceiling (well above CoinGecko's 10/min)
  - US IPs geo-blocked; WEALTH_BINANCE_ENABLED=false on US VPS
  - F12 silent redundancy: DefiLlama oracle at fallback position 3
    still carries Binance-feed data via aggregation
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

BINANCE_BASE = "https://api.binance.com/api/v3"

# F2 TRUTH: explicit WEALTH-symbol -> Binance trading pair mapping.
_MAJOR_PAIR_SYMBOLS: dict[str, str] = {
    "BTC":   "BTCUSDT",
    "ETH":   "ETHUSDT",
    "wBTC":  "WBTCUSDT",
    "USDC":  "USDCUSDT",
    "USDT":  "USDTUSDT",
    "SOL":   "SOLUSDT",
    "BNB":   "BNBUSDT",
    "XRP":   "XRPUSDT",
    "ADA":   "ADAUSDT",
    "DOGE":  "DOGEUSDT",
    "MATIC": "MATICUSDT",
    "DOT":   "DOTUSDT",
}


class BinanceAdapter:
    """Read-only fetcher via Binance public REST API. No auth required.

    Router owns caching + fallback chain. Adapter only signals success
    or reasons for fallback (RateLimitHit / ProviderError).
    """

    provider = "binance_public"

    def fetch(
        self,
        asset: str,
        kind: Literal["spot_price", "24h_change", "depth_top20"],
    ) -> SourceBundle:
        if kind == "spot_price":
            return self._fetch_spot(asset)
        if kind == "24h_change":
            return self._fetch_24h(asset)
        if kind == "depth_top20":
            return self._fetch_depth(asset)
        raise ProviderError(
            f"binance does not support kind={kind!r} "
            f"(router dispatch bug -- should not reach adapter)"
        )

    def _fetch_spot(self, asset: str) -> SourceBundle:
        pair = self._symbol_to_pair(asset)
        url = f"{BINANCE_BASE}/ticker/price?symbol={pair}"
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("binance 1200/min ceiling")

        try:
            payload = json.loads(raw)
            value = float(payload["price"])
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise ProviderError(f"binance schema mismatch: {e}") from e

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
        """24h change computed from open/close -- DER."""
        pair = self._symbol_to_pair(asset)
        url = f"{BINANCE_BASE}/ticker/24hr?symbol={pair}"
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("binance 1200/min ceiling")

        try:
            payload = json.loads(raw)
            pct = float(payload["priceChangePercent"])
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise ProviderError(f"binance schema mismatch: {e}") from e

        return SourceBundle(
            provider=self.provider,
            asset=asset,
            kind="24h_change",
            value=pct,
            currency="PCT",
            source_uri=url,
            epistemic_label=EpistemicLabel.DER,
            response_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            extras={"binance_pair": pair},
        )

    def _fetch_depth(self, asset: str) -> SourceBundle:
        """Top-20 order book depth. DER. No fallback per spec.

        Returns bid-ask volume ratio in [-1, +1]:
          +1 = all bids (strong buy pressure)
           0 = balanced
          -1 = all asks (strong sell pressure)
        """
        pair = self._symbol_to_pair(asset)
        url = f"{BINANCE_BASE}/depth?symbol={pair}&limit=20"
        raw, status = self._http_get(url)

        if status == 429:
            raise RateLimitHit("binance 1200/min ceiling")

        try:
            payload = json.loads(raw)
            bids = payload.get("bids", [])
            asks = payload.get("asks", [])
            bid_volume = sum(float(b[1]) for b in bids[:20])
            ask_volume = sum(float(a[1]) for a in asks[:20])
            denom = bid_volume + ask_volume
            depth_ratio = (bid_volume - ask_volume) / denom if denom > 0 else 0.0
        except (KeyError, ValueError, json.JSONDecodeError, IndexError) as e:
            raise ProviderError(f"binance schema mismatch: {e}") from e

        return SourceBundle(
            provider=self.provider,
            asset=asset,
            kind="depth_top20",
            value=depth_ratio,
            currency="RATIO",
            source_uri=url,
            epistemic_label=EpistemicLabel.DER,
            response_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            extras={"bid_volume_20": bid_volume, "ask_volume_20": ask_volume},
        )

    def _symbol_to_pair(self, asset: str) -> str:
        """Light mapper to Binance ASSETUSDT pair format."""
        upper = asset.upper()
        if upper in _MAJOR_PAIR_SYMBOLS:
            return _MAJOR_PAIR_SYMBOLS[upper]
        return f"{upper}USDT"

    def _http_get(self, url: str) -> tuple[str, int]:
        """httpx with retry + timeout. F12: 10s timeout. Detects 403/451 as geo-block.

        Geo-block surfaces as ProviderError, NOT RateLimitHit, so the
        router's fallback chain triggers and CoinGecko gets the call.
        """
        from wealth_core.http_retry import sync_fetch_raw_with_retry
        headers = {
            "User-Agent": "arifOS-WEALTH-CryptoRouter/1.0",
            "Accept":      "application/json",
        }
        try:
            raw, status = sync_fetch_raw_with_retry(
                url, timeout=10.0, provider="binance_public", headers=headers,
            )
            if status == 429:
                return "", 429
            if status == -1:
                raise ProviderError("binance network failure after retries")
            if status in (403, 451):
                raise ProviderError(
                    f"binance geographic restriction (HTTP {status}): "
                    f"set WEALTH_BINANCE_ENABLED=false on US VPS"
                )
            if status >= 400:
                raise ProviderError(f"binance HTTP {status}")
            return raw, status
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"binance network failure: {e}") from e
