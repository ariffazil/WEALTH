"""
VPS Power Metrics Collector for WEALTH.
Reads /proc, /sys, and system utilities to estimate power draw and carbon.
No external API needed — computed from local hardware data.
"""

from __future__ import annotations


Author: Hermes | arifOS Federation
Forged: 2026-06-12
"""

import os
import subprocess
from typing import Dict, Any, Optional


def _read_file(path: str) -> Optional[str]:
    try:
        with open(path) as f:
            return f.read().strip()
    except (OSError, PermissionError):
        return None


def _cpu_tdp_estimate() -> float:
    """Estimate CPU TDP from model name. Conservative defaults."""
    cpuinfo = _read_file("/proc/cpuinfo")
    if cpuinfo and "EPYC" in cpuinfo:
        if "9354" in cpuinfo:
            return 280.0  # EPYC 9354P ~280W TDP (configurable, this is max)
        return 200.0  # generic EPYC
    if cpuinfo and "Xeon" in cpuinfo:
        return 205.0
    if cpuinfo and "Ryzen" in cpuinfo:
        return 105.0
    return 150.0  # unknown server-class


def _cpu_utilization() -> float:
    """Read CPU utilization from /proc/stat. Returns fraction 0.0-1.0."""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        if len(parts) < 5:
            return 0.5
        # user, nice, system, idle, iowait, irq, softirq, steal
        vals = [int(x) for x in parts[1:]]
        total = sum(vals)
        idle = vals[3] + vals[4] if len(vals) > 4 else vals[3]  # idle + iowait
        return max(0.0, min(1.0, 1.0 - (idle / total if total > 0 else 1.0)))
    except Exception:
        return 0.5


def _gpu_power_estimate() -> float:
    """Estimate GPU power if nvidia-smi available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return 0.0


def collect_power_metrics() -> Dict[str, Any]:
    """Collect current power metrics from VPS hardware.
    
    Returns:
        dict with power draw, energy, cost estimates
    """
    cpu_w = _cpu_tdp_estimate()
    cpu_util = _cpu_utilization()
    gpu_w = _gpu_power_estimate()
    
    # Estimate: CPU power = TDP * utilization * 0.7 (realistic load factor)
    # + 50W baseline for motherboard, RAM, storage, networking
    estimated_power_draw = cpu_w * cpu_util * 0.7 + gpu_w + 50.0
    
    # Malaysia grid carbon intensity ~560 gCO2/kWh (IEA 2022)
    GRID_CARBON_INTENSITY = 560.0  # gCO2/kWh
    TNB_TARIFF_MYR_PER_KWH = 0.365  # approximate residential/commercial
    
    daily_kwh = (estimated_power_draw * 24) / 1000.0
    annual_kwh = daily_kwh * 365
    daily_kg_co2e = (daily_kwh * GRID_CARBON_INTENSITY) / 1000.0
    annual_kg_co2e = daily_kg_co2e * 365
    cost_per_year_myr = annual_kwh * TNB_TARIFF_MYR_PER_KWH
    
    return {
        "power_draw_watts": round(estimated_power_draw, 1),
        "cpu_tdp_watts": cpu_w,
        "cpu_utilization_pct": round(cpu_util * 100, 1),
        "gpu_power_watts": round(gpu_w, 1),
        "daily_energy_kwh": round(daily_kwh, 3),
        "annual_energy_kwh": round(annual_kwh, 1),
        "grid_carbon_intensity_g_per_kwh": GRID_CARBON_INTENSITY,
        "daily_carbon_kg_co2e": round(daily_kg_co2e, 3),
        "annual_carbon_kg_co2e": round(annual_kg_co2e, 1),
        "cost_per_year_myr": round(cost_per_year_myr, 2),
        "tariff_myr_per_kwh": TNB_TARIFF_MYR_PER_KWH,
        "methodology": "Estimated from CPU TDP × utilization × 0.7 + 50W baseline + GPU. Malaysia grid ~560g CO2/kWh.",
        "source": "VPS /proc + /sys metrics",
    }


def power_to_carbon(power_draw_watts: float, grid_intensity: float = 560.0) -> Dict[str, Any]:
    """Convert power draw to carbon emissions estimate."""
    daily_kwh = (power_draw_watts * 24) / 1000.0
    daily_co2e_kg = (daily_kwh * grid_intensity) / 1000.0
    annual_co2e_kg = daily_co2e_kg * 365
    
    verdict = "LOW_EMITTER"
    if annual_co2e_kg > 5000:
        verdict = "HIGH_EMITTER"
    elif annual_co2e_kg > 1000:
        verdict = "MODERATE"
    elif annual_co2e_kg < 50:
        verdict = "CARBON_NEUTRAL"
    
    return {
        "power_draw_watts": round(power_draw_watts, 1),
        "daily_energy_kwh": round(daily_kwh, 3),
        "daily_carbon_kg_co2e": round(daily_co2e_kg, 3),
        "annual_carbon_kg_co2e": round(annual_co2e_kg, 1),
        "grid_carbon_intensity_g_per_kwh": grid_intensity,
        "carbon_verdict": verdict,
        "methodology": f"kWh × {grid_intensity} gCO2/kWh → CO2 estimate. Malaysia grid average (IEA 2022).",
    }
