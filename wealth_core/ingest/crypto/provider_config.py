"""WEALTH Crypto Router — provider priority + F12 env-guard.

Origin: /root/WEALTH/forge_work/CRYPTO_SENSOR_EXTENSION_PROPOSAL_v1.md
        §1 (provider matrix) + §3.2 (router scaffolding)

Step 1 review artifact. No forge_evaluate at this layer (pure config).
Each adapter file carries its own evaluation receipt.
"""
from __future__ import annotations

import os
from typing import Literal

# ─── F12 RESILIENCE: env-var gate for Binance geo enforcement ────────────────
# Set WEALTH_BINANCE_ENABLED=false on VPS where Binance API geo-blocks
# (e.g., US IPs). Router auto-skips Binance with no code patch required.
WEALTH_BINANCE_ENABLED: bool = os.getenv(
    "WEALTH_BINANCE_ENABLED", "true"
).lower() in ("true", "1", "yes")


# ─── Per-kind provider priority (Option B locked 2026-08-18) ──────────────────
class FallbackPriority:
    """Provider priority chain per data kind.

    Spot price — Binance (latency, depth) → CoinGecko (broad coverage) → DefiLlama oracle.
    24h change — Binance (clean data) → CoinGecko (markets endpoint).
    Depth     — Binance only (CoinGecko / DefiLlama don't expose top-20).
    TVL       — DefiLlama only (canonical DeFi TVL source).
    Flow      — Arkham only (no fallback — explicit HOLD on key miss).
    """
    SPOT_PRICE:  list[str] = ["binance_public", "coingecko", "defillama"]
    CHANGE_24H:  list[str] = ["binance_public", "coingecko"]
    DEPTH_TOP20: list[str] = ["binance_public"]
    TVL:         list[str] = ["defillama"]
    FLOW:        list[str] = ["arkham"]


KIND_LITERAL = Literal[
    "spot_price", "24h_change", "depth_top20", "tvl", "flow",
]

DEFAULT_PRIORITY: dict[str, list[str]] = {
    "spot_price":  FallbackPriority.SPOT_PRICE,
    "24h_change":  FallbackPriority.CHANGE_24H,
    "depth_top20": FallbackPriority.DEPTH_TOP20,
    "tvl":         FallbackPriority.TVL,
    "flow":        FallbackPriority.FLOW,
}


def apply_geo_skip(priority: list[str]) -> list[str]:
    """Skip Binance if geo-disabled. F12 fail-closed."""
    if WEALTH_BINANCE_ENABLED:
        return priority
    return [p for p in priority if p != "binance_public"]
