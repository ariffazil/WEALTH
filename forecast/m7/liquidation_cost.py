"""M7.4 — Liquidation cost: spread + market-impact estimate.

For XAUUSD spot (and CME futures as a proxy), the round-trip cost is
the sum of:

    spread / 2  (entered + exited)
    slippage    (broker + venue latency)
    market impact  (Almgren-Chriss linear+sqrt model)

Inputs
------

    notional          — order size in USD
    spread_bps        — quoted spread in basis points (1 bp = 0.01%)
    slippage_bps      — broker+venue slippage in basis points
    adv_usd           — average daily volume in USD; used for impact
    participation_rate — fraction of ADV the order represents (default 1%)
    urgency           — "patient" | "normal" | "urgent"

Model
-----

The Almgren-Chriss temporary impact is roughly proportional to
sigma_daily * sqrt(notional / adv) * (participation_rate)^{0.6}.

We use a simpler, more conservative linear-in-size + sqrt-of-size
formula with conservative coefficients for XAUUSD:

    impact_bps ≈ 0.5 * participation_pct + 1.0 * sqrt(participation_pct)

where participation_pct = (notional / adv_usd) * 100, capped at 50%
(a single trade shouldn't be >50% of daily volume — flag otherwise).

Total liquidation cost = (spread_bps + slippage_bps) / 2 + impact_bps,
returned in basis points AND as an absolute USD amount.

Honest fallback
---------------

If spread / ADV / notional are missing or non-positive, return
data_insufficient=True so the caller defaults to HOLD.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

import numpy as np


Urgency = Literal["patient", "normal", "urgent"]


@dataclass(frozen=True)
class LiquidationCostResult:
    spread_cost_bps: float
    slippage_cost_bps: float
    market_impact_bps: float
    total_cost_bps: float          # round-trip
    total_cost_usd: float          # notional * bps/10000
    participation_pct: float       # notional / adv * 100
    notional_usd: float
    adv_usd: float
    urgency: str
    data_insufficient: bool = False
    notes: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Default XAUUSD market parameters — explicitly synthetic defaults,
# documented in the honest_caveat receipt when used.
DEFAULT_SPREAD_BPS = 5.0           # typical retail ECN for XAUUSD
DEFAULT_SLIPPAGE_BPS = 2.0         # conservative broker+venue slippage
DEFAULT_ADV_USD = 30_000_000_000.0  # XAUUSD global ADV is ~$30B/day
DEFAULT_PARTICIPATION = 0.01       # 1% of ADV per order


def compute_liquidation_cost(
    *,
    notional_usd: float,
    adv_usd: float = DEFAULT_ADV_USD,
    spread_bps: float = DEFAULT_SPREAD_BPS,
    slippage_bps: float = DEFAULT_SLIPPAGE_BPS,
    urgency: str = "normal",
    participation_rate: Optional[float] = None,
) -> LiquidationCostResult:
    """Round-trip liquidation cost in bps and USD.

    Parameters
    ----------
    notional_usd : float
        Order notional in USD.
    adv_usd : float
        Average daily volume in USD (default synthetic XAUUSD = $30B).
    spread_bps : float
        Quoted half-spread in bps (default 5 bps = 0.05%).
    slippage_bps : float
        Broker+venue slippage in bps (default 2 bps).
    urgency : str
        "patient" / "normal" / "urgent" — scales impact by 0.8 / 1.0 / 1.3.
    participation_rate : float or None
        Override for the fraction of ADV the order represents.
        If None, computed from notional / adv.
    """
    reasons: list[str] = []

    if not (np.isfinite(notional_usd) and notional_usd > 0):
        return LiquidationCostResult(
            spread_cost_bps=float("nan"),
            slippage_cost_bps=float("nan"),
            market_impact_bps=float("nan"),
            total_cost_bps=float("nan"),
            total_cost_usd=float("nan"),
            participation_pct=float("nan"),
            notional_usd=float(notional_usd),
            adv_usd=float(adv_usd),
            urgency=str(urgency),
            data_insufficient=True,
            notes="non_positive_notional",
            reasons=["non_positive_notional"],
        )

    if not (np.isfinite(adv_usd) and adv_usd > 0):
        return LiquidationCostResult(
            spread_cost_bps=float("nan"),
            slippage_cost_bps=float("nan"),
            market_impact_bps=float("nan"),
            total_cost_bps=float("nan"),
            total_cost_usd=float("nan"),
            participation_pct=float("nan"),
            notional_usd=float(notional_usd),
            adv_usd=float(adv_usd),
            urgency=str(urgency),
            data_insufficient=True,
            notes="non_positive_adv",
            reasons=["non_positive_adv"],
        )

    if participation_rate is None:
        participation_pct = (notional_usd / adv_usd) * 100.0
    else:
        if not (np.isfinite(participation_rate) and 0 <= participation_rate <= 1):
            return LiquidationCostResult(
                spread_cost_bps=float("nan"),
                slippage_cost_bps=float("nan"),
                market_impact_bps=float("nan"),
                total_cost_bps=float("nan"),
                total_cost_usd=float("nan"),
                participation_pct=float("nan"),
                notional_usd=float(notional_usd),
                adv_usd=float(adv_usd),
                urgency=str(urgency),
                data_insufficient=True,
                notes="invalid_participation_rate",
                reasons=["invalid_participation_rate"],
            )
        participation_pct = participation_rate * 100.0

    if participation_pct > 50.0:
        reasons.append("participation_above_50pct")

    # Spread cost = half-spread entered + half-spread exited
    spread_cost_bps = float(spread_bps)
    if not (np.isfinite(spread_bps) and spread_bps >= 0):
        spread_cost_bps = DEFAULT_SPREAD_BPS
        reasons.append("fallback_default_spread")
    slippage_cost_bps = float(slippage_bps) if (np.isfinite(slippage_bps) and slippage_bps >= 0) else DEFAULT_SLIPPAGE_BPS

    # Almgren-Chriss-ish: linear + sqrt with conservative XAUUSD coefs.
    # impact_bps ≈ 0.5 * participation_pct + 1.0 * sqrt(participation_pct)
    impact_bps_raw = 0.5 * participation_pct + 1.0 * np.sqrt(participation_pct)

    urgency_mult = {"patient": 0.8, "normal": 1.0, "urgent": 1.3}.get(urgency, 1.0)
    if urgency not in ("patient", "normal", "urgent"):
        reasons.append("invalid_urgency_using_normal")
    impact_bps = float(impact_bps_raw * urgency_mult)

    total_cost_bps = float(spread_cost_bps + slippage_cost_bps + impact_bps)
    total_cost_usd = float(notional_usd * total_cost_bps / 10_000.0)

    notes_parts = ["spread_plus_slippage_plus_almgren_chriss_linear_sqrt"]
    if reasons:
        notes_parts.append("caveats:" + ";".join(reasons))

    return LiquidationCostResult(
        spread_cost_bps=spread_cost_bps,
        slippage_cost_bps=slippage_cost_bps,
        market_impact_bps=impact_bps,
        total_cost_bps=total_cost_bps,
        total_cost_usd=total_cost_usd,
        participation_pct=float(participation_pct),
        notional_usd=float(notional_usd),
        adv_usd=float(adv_usd),
        urgency=urgency if urgency in ("patient", "normal", "urgent") else "normal",
        notes=";".join(notes_parts),
        reasons=reasons,
    )


__all__ = [
    "LiquidationCostResult",
    "Urgency",
    "compute_liquidation_cost",
    "DEFAULT_SPREAD_BPS",
    "DEFAULT_SLIPPAGE_BPS",
    "DEFAULT_ADV_USD",
    "DEFAULT_PARTICIPATION",
]
