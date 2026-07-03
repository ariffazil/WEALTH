"""
Federation Safety Wiring — Shared Python Module
================================================

Wraps MCP tool handlers with:
  - Discovery 3: Structured error envelopes (classifyUnknown equivalent)
  - Discovery 8: Memory classification (fresh/stale/inferred/sealed)
  - Discovery 9: Epistemic signals (OBS/DER/INT/SPEC with confidence)

Usage in any organ's tool handler:

    from federation_safety import safe_tool, MemoryClass, EpistemicLayer

    @safe_tool("geox_well_ingest")
    async def geox_well_ingest(well_name: str, las_path: str = None):
        ...

Or wrap individual calls:

    result = enrich_result(data, MemoryClass.LIVE_PROBE, EpistemicLayer.OBSERVED)

FORGED: 2026-07-03
DITEMPA BUKAN DIBERI
"""

import functools
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# ─── Discovery 8: Memory Classification ─────────────────────────────


class MemoryClass(str, Enum):
    LIVE_PROBE = "LIVE_PROBE"  # Directly observed right now
    SESSION_STATE = "SESSION_STATE"  # Current session context
    CACHED_MEMORY = "CACHED_MEMORY"  # Previously observed, may be stale
    INFERRED = "INFERRED"  # Derived from other evidence
    SEALED_RECEIPT = "SEALED_RECEIPT"  # Immutable, VAULT999-sealed
    STALE = "STALE"  # Known to be outdated


class MemoryStatus:
    def __init__(
        self,
        cls: MemoryClass,
        last_verified: Optional[str] = None,
        freshness_ttl_s: int = 300,
        source: Optional[str] = None,
    ):
        self.class_ = cls
        self.last_verified = last_verified or datetime.now(timezone.utc).isoformat()
        self.freshness_ttl_s = freshness_ttl_s
        self.source = source
        self.is_fresh = self._check_fresh()

    def _check_fresh(self) -> bool:
        if not self.last_verified:
            return None
        try:
            verified = datetime.fromisoformat(self.last_verified.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - verified).total_seconds() < self.freshness_ttl_s
        except Exception:
            return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class": self.class_.value,
            "last_verified": self.last_verified,
            "freshness_ttl_s": self.freshness_ttl_s,
            "is_fresh": self.is_fresh,
            "source": self.source,
        }


def memory_live(source: str = None) -> MemoryStatus:
    return MemoryStatus(MemoryClass.LIVE_PROBE, source=source)


def memory_cached(
    last_verified: str, ttl_s: int = 300, source: str = None
) -> MemoryStatus:
    return MemoryStatus(
        MemoryClass.CACHED_MEMORY,
        last_verified=last_verified,
        freshness_ttl_s=ttl_s,
        source=source,
    )


def memory_inferred(source: str = None) -> MemoryStatus:
    return MemoryStatus(MemoryClass.INFERRED, source=source)


def memory_sealed(source: str = None) -> MemoryStatus:
    return MemoryStatus(MemoryClass.SEALED_RECEIPT, source=source)


# ─── Discovery 9: Epistemic Signal ──────────────────────────────────


class EpistemicLayer(str, Enum):
    OBSERVED = "OBS"  # Directly observed
    DERIVED = "DER"  # Computed or derived
    INTERPRETED = "INT"  # Interpreted by agent/human
    SPECULATIVE = "SPEC"  # Speculative, low confidence


class EpistemicSignal:
    def __init__(
        self,
        layer: EpistemicLayer,
        confidence: float = 0.7,
        uncertainty: List[str] = None,
        source: str = None,
        reversible: bool = True,
        authority_claim: str = "ADVISORY",
    ):
        # F7 HUMILITY: cap at 0.90
        self.evidence_layer = layer
        self.confidence = min(confidence, 0.90)
        self.uncertainty = uncertainty or []
        self.source = source
        self.reversible = reversible
        self.authority_claim = authority_claim

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_layer": self.evidence_layer.value,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "source": self.source,
            "reversible": self.reversible,
            "authority_claim": self.authority_claim,
        }


def epistemic_observed(source: str = None, confidence: float = 0.85) -> EpistemicSignal:
    return EpistemicSignal(
        EpistemicLayer.OBSERVED,
        confidence=confidence,
        source=source,
        authority_claim="EVIDENCE",
    )


def epistemic_derived(source: str = None, confidence: float = 0.75) -> EpistemicSignal:
    return EpistemicSignal(
        EpistemicLayer.DERIVED,
        confidence=confidence,
        source=source,
        authority_claim="EVIDENCE",
    )


def epistemic_inferred(
    source: str = None, confidence: float = 0.6, uncertainty: List[str] = None
) -> EpistemicSignal:
    return EpistemicSignal(
        EpistemicLayer.INTERPRETED,
        confidence=confidence,
        source=source,
        uncertainty=uncertainty,
    )


def epistemic_speculative(
    source: str = None, uncertainty: List[str] = None
) -> EpistemicSignal:
    return EpistemicSignal(
        EpistemicLayer.SPECULATIVE,
        confidence=0.3,
        source=source,
        uncertainty=uncertainty or ["speculative"],
    )


# ─── Discovery 3: Structured Error Envelopes ────────────────────────


class ErrorClass(str, Enum):
    BAD_INPUT_SHAPE = "BAD_INPUT_SHAPE"
    BAD_INPUT_VALUE = "BAD_INPUT_VALUE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    DOWNSTREAM_FAILURE = "DOWNSTREAM_FAILURE"
    DOWNSTREAM_PARSER_FAIL = "DOWNSTREAM_PARSER_FAIL"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUTHORITY_BLOCK = "AUTHORITY_BLOCK"
    FLOOR_BLOCK = "FLOOR_BLOCK"
    TOOL_SURFACE_DRIFT = "TOOL_SURFACE_DRIFT"


class Recoverability(str, Enum):
    AGENT_CAN_RETRY = "AGENT_CAN_RETRY"
    AGENT_CAN_ROUTE = "AGENT_CAN_ROUTE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    ESCALATE_TO_888_HOLD = "ESCALATE_TO_888_HOLD"
    FATAL_DO_NOT_RETRY = "FATAL_DO_NOT_RETRY"
    RETRY_SAME_LATER = "RETRY_SAME_LATER"


def classify_error(
    error: Exception, source_tool: str = None, source_organ: str = None
) -> Dict[str, Any]:
    """
    Classify an unknown error into a structured envelope.
    Python equivalent of classifyUnknown() from error-classifier.ts.
    """
    msg = str(error)
    msg_lower = msg.lower()

    # Parser patterns (check FIRST — more specific)
    if any(
        kw in msg_lower
        for kw in [
            "parse",
            "parser",
            "las",
            "seg-y",
            "segy",
            "csv",
            "corrupt",
            "malform",
        ]
    ):
        error_class = ErrorClass.DOWNSTREAM_PARSER_FAIL
        recoverability = Recoverability.AGENT_CAN_RETRY
        layer = "parser"
        severity = "RECOVERABLE"
        next_action = f"Check file format and retry ({source_tool} parser)"

    # Missing/required patterns
    elif any(
        kw in msg_lower for kw in ["missing", "required", "cannot be null", "undefined"]
    ):
        error_class = ErrorClass.MISSING_REQUIRED_FIELD
        recoverability = Recoverability.AGENT_CAN_RETRY
        layer = "input_validation"
        severity = "RECOVERABLE"
        next_action = "Provide missing fields and retry"

    # Invalid/out of range patterns
    elif any(
        kw in msg_lower for kw in ["invalid", "out of range", "must be", "expected"]
    ):
        error_class = ErrorClass.BAD_INPUT_VALUE
        recoverability = Recoverability.AGENT_CAN_RETRY
        layer = "argument_semantic"
        severity = "RECOVERABLE"
        next_action = "Fix input values and retry"

    # Authority/permission patterns
    elif any(
        kw in msg_lower
        for kw in ["lease", "authority", "forbidden", "unauthorized", "permission"]
    ):
        error_class = ErrorClass.AUTHORITY_BLOCK
        recoverability = Recoverability.ESCALATE_TO_888_HOLD
        layer = "authority"
        severity = "ESCALATE"
        next_action = "Request lease or escalate to 888_HOLD"

    # Floor patterns
    elif any(
        kw in msg_lower
        for kw in ["floor", "constitution", "amanah", "truth", "sovereign"]
    ):
        error_class = ErrorClass.FLOOR_BLOCK
        recoverability = Recoverability.ESCALATE_TO_888_HOLD
        layer = "floor"
        severity = "FATAL"
        next_action = "Constitutional floor violation — escalate to arifOS judge"

    # Drift patterns
    elif any(
        kw in msg_lower
        for kw in ["drift", "schema change", "surface drift", "tool removed"]
    ):
        error_class = ErrorClass.TOOL_SURFACE_DRIFT
        recoverability = Recoverability.ESCALATE_TO_888_HOLD
        layer = "surface_drift"
        severity = "FATAL"
        next_action = "MCP tool surface changed — investigate drift cause"

    # Timeout/rate limit patterns
    elif any(
        kw in msg_lower
        for kw in ["timeout", "etimedout", "econnrefused", "rate limit", "429"]
    ):
        error_class = ErrorClass.RESOURCE_EXHAUSTED
        recoverability = Recoverability.RETRY_SAME_LATER
        layer = "resource"
        severity = "RECOVERABLE"
        next_action = "Back off and retry with exponential delay"

    # Network patterns
    elif any(
        kw in msg_lower
        for kw in ["econnreset", "503", "502", "fetch failed", "network"]
    ):
        error_class = ErrorClass.DOWNSTREAM_FAILURE
        recoverability = Recoverability.AGENT_CAN_ROUTE
        layer = "external_dep"
        severity = "RECOVERABLE"
        next_action = "Try different organ or retry later"

    # Default: internal error
    else:
        error_class = ErrorClass.INTERNAL_ERROR
        recoverability = Recoverability.ESCALATE_TO_888_HOLD
        layer = "tool_execution"
        severity = "FATAL"
        next_action = "Log to VAULT999 and escalate — server bug"

    return {
        "isError": True,
        "error_class": error_class.value,
        "recoverability": recoverability.value,
        "suspected_layer": layer,
        "severity": severity,
        "message": msg[:500],
        "next_action": next_action,
        "epistemic_label": "DER",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_tool": source_tool,
        "source_organ": source_organ,
        "original_error": traceback.format_exc() if error.__traceback__ else None,
    }


# ─── Enriched Result ────────────────────────────────────────────────


def enrich_result(
    data: Any,
    memory: MemoryClass = MemoryClass.LIVE_PROBE,
    epistemic: EpistemicLayer = EpistemicLayer.OBSERVED,
    source: str = None,
    confidence: float = 0.85,
) -> Dict[str, Any]:
    """
    Wrap any tool result with memory + epistemic metadata.
    """
    return {
        "data": data,
        "_memory": memory.value,
        "_epistemic": {
            "evidence_layer": epistemic.value,
            "confidence": min(confidence, 0.90),
            "source": source,
            "reversible": True,
            "authority_claim": "EVIDENCE"
            if epistemic == EpistemicLayer.OBSERVED
            else "ADVISORY",
        },
    }


# ─── Safe Tool Decorator ────────────────────────────────────────────


def safe_tool(tool_name: str, organ: str = "unknown"):
    """
    Decorator that wraps any MCP tool handler with:
    - Structured error envelopes on exception
    - Memory classification on result
    - Epistemic signals on result

    Usage:
        @safe_tool("geox_well_ingest", organ="geox")
        async def geox_well_ingest(well_name: str, las_path: str = None):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                # If result is already enriched, pass through
                if (
                    isinstance(result, dict)
                    and "_memory" in result
                    and "_epistemic" in result
                ):
                    return result

                # Enrich the result
                if isinstance(result, dict) and result.get("isError"):
                    return result  # Error envelope, pass through

                return enrich_result(
                    result,
                    memory=MemoryClass.LIVE_PROBE,
                    epistemic=EpistemicLayer.OBSERVED,
                    source=tool_name,
                )

            except Exception as e:
                return classify_error(e, source_tool=tool_name, source_organ=organ)

        return wrapper

    return decorator
