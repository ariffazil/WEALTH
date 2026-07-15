#!/usr/bin/env python3
"""
Sabah Depth Conversion — KT-7 Reflector Test
==============================================
Converts two-way time (TWT) to depth using the Sabah Basin velocity model
from sabah_basin_strat.yaml (GEOX ontology).

Purpose: Test whether a reflector at 12-21 km depth is consistent with
ophiolite Vp (5.0-6.5 km/s) or granite Vp (5.8-6.0 km/s).

Source: GEOX sabah_basin_strat.yaml + Kinabalu Two-Oceanics v4 model
DITEMPA BUKAN DIBERI — Depth is forged, not given.

Usage:
    python kinabalu_depth_convert.py                    # Full model
    python kinabalu_depth_convert.py --twt 8.5          # Convert TWT (seconds) to depth
    python kinabalu_depth_convert.py --depth 15000      # Convert depth (m) to TWT
    python kinabalu_depth_convert.py --test-kt7         # Test KT-7 reflector hypothesis
"""

from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# SABAH VELOCITY MODEL (from GEOX sabah_basin_strat.yaml)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class VelocityLayer:
    """A single velocity layer in the Sabah Basin."""

    name: str
    top_depth_m: float  # Top of layer (m TVDSS)
    base_depth_m: float  # Base of layer (m TVDSS)
    vp_min_km_s: float  # Minimum P-wave velocity (km/s)
    vp_max_km_s: float  # Maximum P-wave velocity (km/s)
    description: str = ""

    @property
    def thickness_m(self) -> float:
        return self.base_depth_m - self.top_depth_m

    @property
    def vp_avg_km_s(self) -> float:
        return (self.vp_min_km_s + self.vp_max_km_s) / 2.0

    @property
    def twt_top_s(self) -> float:
        """TWT to top of layer (computed by accumulation)."""
        return self._twt_top

    @property
    def twt_base_s(self) -> float:
        """TWT to base of layer."""
        return self._twt_base


# Sabah Basin velocity model — from sabah_basin_strat.yaml
# Layer boundaries at formation tops (approximate, basin-center)
SABAH_MODEL = [
    VelocityLayer(
        name="Shallow allochthonous",
        top_depth_m=0,
        base_depth_m=1500,
        vp_min_km_s=1.5,
        vp_max_km_s=2.0,
        description="Unconsolidated sediments, high velocity gradient",
    ),
    VelocityLayer(
        name="Shallow Sandakan Formation",
        top_depth_m=1500,
        base_depth_m=2500,
        vp_min_km_s=2.0,
        vp_max_km_s=2.8,
        description="Late Miocene–Pliocene shelfal clastics",
    ),
    VelocityLayer(
        name="Middle Labang Group",
        top_depth_m=2500,
        base_depth_m=4500,
        vp_min_km_s=2.8,
        vp_max_km_s=3.5,
        description="Middle Miocene deltaic–marine clastics",
    ),
    VelocityLayer(
        name="Deep Bongaya / base Tertiary",
        top_depth_m=4500,
        base_depth_m=6000,
        vp_min_km_s=3.5,
        vp_max_km_s=4.5,
        description="Oligocene–Early Miocene deepwater clastics",
    ),
    VelocityLayer(
        name="Ophiolite basement",
        top_depth_m=6000,
        base_depth_m=25000,  # Deep enough for KT-7 test
        vp_min_km_s=5.0,
        vp_max_km_s=6.5,
        description="Ultramafic–mafic igneous basement",
    ),
]

# Granite velocity range (for comparison)
GRANITE_VP_KM_S = (5.8, 6.0)  # Bulk granite Vp


# ─────────────────────────────────────────────────────────────────────────────
# DEPTH CONVERSION ENGINE
# ─────────────────────────────────────────────────────────────────────────────


def compute_twt_profile(
    model: list[VelocityLayer], max_depth_m: float = 25000, vp_mode: str = "avg"
) -> list[dict]:
    """
    Compute TWT for each layer boundary.

    Args:
        model: velocity model layers
        max_depth_m: maximum depth to compute
        vp_mode: "avg" (midpoint), "min", "max" for velocity selection

    Returns:
        List of {depth_m, twt_s, vp_km_s, layer_name}
    """
    profile = []
    accumulated_twt = 0.0  # seconds

    for layer in model:
        if layer.top_depth_m >= max_depth_m:
            break

        if vp_mode == "avg":
            vp = layer.vp_avg_km_s
        elif vp_mode == "min":
            vp = layer.vp_min_km_s
        elif vp_mode == "max":
            vp = layer.vp_max_km_s
        else:
            vp = layer.vp_avg_km_s

        # TWT through this layer (two-way: down + up = 2x thickness / Vp)
        base = min(layer.base_depth_m, max_depth_m)
        thickness = base - layer.top_depth_m
        layer_twt = 2.0 * thickness / (vp * 1000.0)  # vp in km/s, depth in m

        layer._twt_top = accumulated_twt
        accumulated_twt += layer_twt
        layer._twt_base = accumulated_twt

        profile.append(
            {
                "depth_m": base,
                "twt_s": accumulated_twt,
                "vp_km_s": vp,
                "layer_name": layer.name,
                "layer_twt_s": layer_twt,
            }
        )

    return profile


def twt_to_depth(
    twt_s: float, model: list[VelocityLayer], vp_mode: str = "avg"
) -> dict:
    """
    Convert TWT (seconds) to depth (m TVDSS).

    Walks through the velocity model, accumulating TWT until we reach
    the target TWT, then interpolates within the layer.

    Returns:
        {depth_m, tvdss_m, layer_name, vp_km_s, confidence}
    """
    accumulated_twt = 0.0

    for layer in model:
        if vp_mode == "avg":
            vp = layer.vp_avg_km_s
        elif vp_mode == "min":
            vp = layer.vp_min_km_s
        elif vp_mode == "max":
            vp = layer.vp_max_km_s
        else:
            vp = layer.vp_avg_km_s

        layer_twt = 2.0 * layer.thickness_m / (vp * 1000.0)

        if accumulated_twt + layer_twt >= twt_s:
            # Target is within this layer
            remaining_twt = twt_s - accumulated_twt
            depth_in_layer = remaining_twt * vp * 1000.0 / 2.0
            total_depth = layer.top_depth_m + depth_in_layer

            return {
                "depth_m": total_depth,
                "tvdss_m": total_depth,
                "layer_name": layer.name,
                "vp_km_s": vp,
                "confidence": "HIGH"
                if layer.name != "Ophiolite basement"
                else "MEDIUM",
                "epistemic": "DER",
            }

        accumulated_twt += layer_twt

    # Beyond model — extrapolate with last layer Vp
    last_layer = model[-1]
    if vp_mode == "avg":
        vp = last_layer.vp_avg_km_s
    elif vp_mode == "min":
        vp = last_layer.vp_min_km_s
    else:
        vp = last_layer.vp_max_km_s

    remaining_twt = twt_s - accumulated_twt
    depth_in_layer = remaining_twt * vp * 1000.0 / 2.0
    total_depth = last_layer.base_depth_m + depth_in_layer

    return {
        "depth_m": total_depth,
        "tvdss_m": total_depth,
        "layer_name": f"{last_layer.name} (extrapolated)",
        "vp_km_s": vp,
        "confidence": "LOW",
        "epistemic": "SPEC",
    }


def depth_to_twt(
    depth_m: float, model: list[VelocityLayer], vp_mode: str = "avg"
) -> dict:
    """
    Convert depth (m TVDSS) to TWT (seconds).

    Returns:
        {twt_s, layer_name, vp_km_s, confidence}
    """
    accumulated_twt = 0.0

    for layer in model:
        if depth_m <= layer.top_depth_m:
            # Already above this layer — shouldn't happen after accumulation
            continue

        if vp_mode == "avg":
            vp = layer.vp_avg_km_s
        elif vp_mode == "min":
            vp = layer.vp_min_km_s
        elif vp_mode == "max":
            vp = layer.vp_max_km_s
        else:
            vp = layer.vp_avg_km_s

        base = min(layer.base_depth_m, depth_m)
        thickness = base - layer.top_depth_m
        layer_twt = 2.0 * thickness / (vp * 1000.0)

        if depth_m <= layer.base_depth_m:
            # Target is within this layer
            return {
                "twt_s": accumulated_twt + layer_twt,
                "layer_name": layer.name,
                "vp_km_s": vp,
                "confidence": "HIGH"
                if layer.name != "Ophiolite basement"
                else "MEDIUM",
                "epistemic": "DER",
            }

        accumulated_twt += layer_twt

    # Beyond model
    last_layer = model[-1]
    if vp_mode == "avg":
        vp = last_layer.vp_avg_km_s
    else:
        vp = last_layer.vp_max_km_s

    extra_depth = depth_m - last_layer.base_depth_m
    extra_twt = 2.0 * extra_depth / (vp * 1000.0)

    return {
        "twt_s": accumulated_twt + extra_twt,
        "layer_name": f"{last_layer.name} (extrapolated)",
        "vp_km_s": vp,
        "confidence": "LOW",
        "epistemic": "SPEC",
    }


# ─────────────────────────────────────────────────────────────────────────────
# KT-7 REFLECTOR TEST
# ─────────────────────────────────────────────────────────────────────────────


def test_kt7_reflector(depth_km_range: tuple = (12, 21)) -> dict:
    """
    Test whether a reflector at 12-21 km depth is consistent with
    ophiolite Vp or granite Vp.

    The falsification framework (kinabalu_falsification_framework_2026-07-03.md)
    states:
    - If depth matches ophiolite-Vp range (5.0-6.5 km/s) → H1 strengthens
    - If depth matches granite-Vp (5.8-6.0 km/s bulk) → W3 falsifies

    The overlap zone (5.8-6.0 km/s) is ambiguous — both ophiolite and granite
    have similar Vp in this range. The discriminator is:
    - Ophiolite: broader range (5.0-6.5), often with high-amplitude irregular top
    - Granite: narrower range (5.8-6.0), more uniform character

    Returns:
        {test_results: [...], verdict, confidence, next_action}
    """
    results = []

    for depth_km in range(depth_km_range[0], depth_km_range[1] + 1, 1):
        depth_m = depth_km * 1000.0

        # Compute TWT for this depth using avg velocity
        twt_result = depth_to_twt(depth_m, SABAH_MODEL, vp_mode="avg")
        twt_min = depth_to_twt(depth_m, SABAH_MODEL, vp_mode="min")
        twt_max = depth_to_twt(depth_m, SABAH_MODEL, vp_mode="max")

        # What layer is this in?
        layer_name = twt_result["layer_name"]
        vp_avg = twt_result["vp_km_s"]

        # Check consistency with ophiolite vs granite
        ophiolite_consistent = 5.0 <= vp_avg <= 6.5
        granite_consistent = 5.8 <= vp_avg <= 6.0

        if granite_consistent and ophiolite_consistent:
            discrimination = "AMBIGUOUS — both ophiolite and granite possible"
            discriminator_value = "LOW"
        elif ophiolite_consistent:
            discrimination = "OPHIOLITE preferred — Vp outside granite range"
            discriminator_value = "MEDIUM"
        else:
            discrimination = "NEITHER — Vp outside expected ranges"
            discriminator_value = "HIGH (kills both)"

        results.append(
            {
                "depth_km": depth_km,
                "depth_m": depth_m,
                "twt_avg_s": round(twt_result["twt_s"], 3),
                "twt_range_s": [round(twt_min["twt_s"], 3), round(twt_max["twt_s"], 3)],
                "vp_avg_km_s": vp_avg,
                "layer": layer_name,
                "ophiolite_consistent": ophiolite_consistent,
                "granite_consistent": granite_consistent,
                "discrimination": discrimination,
                "discriminator_value": discriminator_value,
            }
        )

    # Verdict
    ambiguous_count = sum(1 for r in results if "AMBIGUOUS" in r["discrimination"])
    ophiolite_count = sum(1 for r in results if "OPHIOLITE" in r["discrimination"])
    neither_count = sum(1 for r in results if "NEITHER" in r["discrimination"])

    if ambiguous_count > len(results) * 0.7:
        verdict = "WEAK DISCRIMINATOR — velocity overlap too large"
        confidence = 0.3
    elif ophiolite_count > len(results) * 0.5:
        verdict = "OPHIOLITE SUPPORTED — Vp consistent with oceanic basement"
        confidence = 0.6
    elif neither_count > 0:
        verdict = "SURPRISING — Vp outside both expected ranges"
        confidence = 0.5
    else:
        verdict = "INCONCLUSIVE — mixed signal"
        confidence = 0.4

    return {
        "test": "KT-7 Reflector Depth Conversion",
        "depth_range_km": depth_km_range,
        "results": results,
        "verdict": verdict,
        "confidence": confidence,
        "epistemic": "DER",
        "next_action": "Requires actual TWT measurement from seismic data. "
        "This model provides the conversion framework only.",
        "caveat": "The velocity model uses layer-average Vp. Real velocity "
        "varies with depth (compaction), lithology, and pore pressure. "
        "Checkshot/VSP data would improve accuracy.",
        "source": "GEOX sabah_basin_strat.yaml + Kinabalu v4 falsification framework",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Sabah Depth Conversion — KT-7 Reflector Test"
    )
    parser.add_argument("--twt", type=float, help="Convert TWT (seconds) to depth")
    parser.add_argument("--depth", type=float, help="Convert depth (m TVDSS) to TWT")
    parser.add_argument(
        "--test-kt7", action="store_true", help="Run KT-7 reflector test"
    )
    parser.add_argument(
        "--profile", action="store_true", help="Show full TWT-depth profile"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.test_kt7:
        result = test_kt7_reflector()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 70)
            print("KT-7 REFLECTOR DEPTH CONVERSION TEST")
            print("=" * 70)
            print(
                f"\nDepth range: {result['depth_range_km'][0]}-{result['depth_range_km'][1]} km"
            )
            print(f"Verdict: {result['verdict']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Epistemic: {result['epistemic']}")
            print(f"\nCaveat: {result['caveat']}")
            print(f"\nNext: {result['next_action']}")
            print("\n" + "-" * 70)
            print(f"{'Depth':>8} {'TWT':>8} {'Vp':>8} {'Layer':>30} {'Discrimination'}")
            print("-" * 70)
            for r in result["results"]:
                print(
                    f"{r['depth_km']:>6} km {r['twt_avg_s']:>7.2f}s {r['vp_avg_km_s']:>7.1f} "
                    f"{r['layer']:>30} {r['discrimination'][:40]}"
                )

    elif args.twt is not None:
        result = twt_to_depth(args.twt, SABAH_MODEL)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"TWT: {args.twt}s → Depth: {result['depth_m']:.0f} m TVDSS")
            print(f"Layer: {result['layer_name']}")
            print(f"Vp: {result['vp_km_s']:.1f} km/s")
            print(f"Confidence: {result['confidence']}")

    elif args.depth is not None:
        result = depth_to_twt(args.depth, SABAH_MODEL)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Depth: {args.depth:.0f} m → TWT: {result['twt_s']:.3f}s")
            print(f"Layer: {result['layer_name']}")
            print(f"Vp: {result['vp_km_s']:.1f} km/s")
            print(f"Confidence: {result['confidence']}")

    elif args.profile:
        profile = compute_twt_profile(SABAH_MODEL)
        if args.json:
            print(json.dumps(profile, indent=2))
        else:
            print("=" * 70)
            print("SABAH BASIN VELOCITY MODEL — TWT-DEPTH PROFILE")
            print("=" * 70)
            print(f"{'Depth (m)':>12} {'TWT (s)':>10} {'Vp (km/s)':>10} {'Layer'}")
            print("-" * 70)
            for p in profile:
                print(
                    f"{p['depth_m']:>12.0f} {p['twt_s']:>10.3f} {p['vp_km_s']:>10.1f} {p['layer_name']}"
                )

    else:
        # Default: show profile + KT-7 test
        print("=" * 70)
        print("SABAH DEPTH CONVERSION — KT-7 REFLECTOR TEST")
        print("Source: GEOX sabah_basin_strat.yaml + Kinabalu v4")
        print("=" * 70)

        # Profile
        profile = compute_twt_profile(SABAH_MODEL)
        print(f"\n{'Depth (m)':>12} {'TWT (s)':>10} {'Vp (km/s)':>10} {'Layer'}")
        print("-" * 60)
        for p in profile:
            print(
                f"{p['depth_m']:>12.0f} {p['twt_s']:>10.3f} {p['vp_km_s']:>10.1f} {p['layer_name']}"
            )

        # KT-7 test
        print("\n" + "=" * 70)
        result = test_kt7_reflector()
        print(f"\nKT-7 Verdict: {result['verdict']}")
        print(f"Confidence: {result['confidence']}")
        print(
            f"\nKey insight: At 12-21 km depth, Vp = {result['results'][0]['vp_avg_km_s']:.1f} km/s"
        )
        print(f"This is in the OPHIOLITE range (5.0-6.5 km/s)")
        print(f"Granite overlap zone: 5.8-6.0 km/s — AMBIGUOUS")
        print(
            f"\nTo discriminate: need actual TWT from seismic + checkshot calibration"
        )


if __name__ == "__main__":
    main()
