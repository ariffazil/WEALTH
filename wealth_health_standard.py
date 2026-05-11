"""
WEALTH Federation Health Standard
════════════════════════════════
Standardized 3-layer health check for the WEALTH capital evidence organ.
Aligned with FTC-1 and WELL MCP health schemas.
"""

from typing import Any, Dict
from datetime import datetime, timezone
from host.ingest.health import get_tracker

def wealth_get_health() -> Dict[str, Any]:
    """
    Canonical three-layer health check for WEALTH.
    
    Layer 1 — Service: Is the monolith process alive and responsive?
    Layer 2 — Instrument: Are registries, analyzers, and schemas valid?
    Layer 3 — Domain Truth: Is capital data fresh, reconciled, and verified?
    """
    tracker = get_tracker()
    adapters = tracker.all_adapters()
    now = datetime.now(timezone.utc)
    
    # Layer 1: Service
    service = {
        "status": "OK",
        "transport": "HTTP/JSON",
        "uptime_seconds": 0, # Placeholder — would be real in a running server
    }
    
    # Layer 2: Instrument
    instrument = {
        "registry_count": len(adapters),
        "schema_version": "2026.05.11",
        "status": "OK" if len(adapters) > 0 else "DEGRADED",
    }
    
    # Layer 3: Domain Truth (Capital Intelligence)
    # Check for stale adapters or divergences
    stale_count = 0
    divergence_count = 0
    for a in adapters:
        h = tracker.get_health(a)
        if h.get("stale"): stale_count += 1
        if any(f.startswith("DIVERGENCE") for f in h.get("flags", [])):
            divergence_count += 1
            
    domain_truth = {
        "metrics_fresh": stale_count == 0,
        "reconciliation_passed": divergence_count == 0,
        "truth_status": "VERIFIED" if (stale_count == 0 and divergence_count == 0) else "UNVERIFIED",
        "vintage": now.isoformat(),
    }
    
    # Final Verdict
    verdict = "PASS"
    if stale_count > 5 or divergence_count > 0:
        verdict = "WARN"
    if len(adapters) == 0:
        verdict = "FAIL"
        
    return {
        "mcp": "WEALTH-MONOLITH",
        "verdict": verdict,
        "service": service,
        "instrument": instrument,
        "domain_truth": domain_truth,
        "timestamp": now.isoformat(),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
