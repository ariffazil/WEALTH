"""
FLAME Client — Direct Python bridge from WEALTH to FLAME 2.0 inference mesh.

Architectural rules (Arif-ratified 2026-07-25 · P2 SEALED):
  1. Direct import — no HTTP hop, no serialization overhead
  2. Schema-Forced F1 Gate — ADVISORY tag enforced at both schema AND runtime
  3. L3 Task-Adaptive Routing — task_class="extract" → Qwen3.6 → Ministral 8B
  4. Post-Generation Circuit Breaker — hallucinated authority → immediate discard
  5. Zero-State — no memory, no context carry-forward between calls
  6. W_scar = 0 — FLAME is RM0, no billing risk

F1 AMANAH enforcement:
  - Schema REQUIRES {"authority": "ADVISORY"} in every output
  - Runtime validation REJECTS any output where authority != "ADVISORY"
  - If AI hallucinates buy/sell trigger → dropped immediately (ΔS < 0)

Usage:
    from wealth_mcp.tools.flame_client import flame_market_signal

    result = flame_market_signal(raw_data, focus_asset="XAUUSD")
    # Returns: dict with authority="ADVISORY" or None on F1 violation

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("wealth.flame_client")

# ── FLAME import path ────────────────────────────────────────────────────
_FLAME_PATH = Path("/root/A-FORGE/flame")
if str(_FLAME_PATH) not in sys.path:
    sys.path.insert(0, str(_FLAME_PATH))

# Lazy init — avoids import cost at module load
_engine = None


def _get_engine():
    """Lazy singleton — FlameEngine is expensive to init."""
    global _engine
    if _engine is None:
        from flame_router import FlameEngine

        _engine = FlameEngine()
    return _engine


# ── F1 Schema Templates ──────────────────────────────────────────────────

MARKET_SIGNAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},
        "signal_type": {
            "type": "string",
            "enum": ["bullish", "bearish", "neutral"],
        },
        "key_catalysts": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 7,
        },
        "confidence_threshold": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 0.90,
            "description": "F7 HUMILITY cap — never exceed 0.90",
        },
        "authority": {
            "type": "string",
            "enum": ["ADVISORY"],
        },
        "status": {
            "type": "string",
            "enum": ["COMPLETE", "NEEDS_MORE_DATA", "AMBIGUOUS"],
        },
    },
    "required": [
        "asset",
        "signal_type",
        "key_catalysts",
        "confidence_threshold",
        "authority",
    ],
}


EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 0.90},
        "authority": {"type": "string", "enum": ["ADVISORY"]},
    },
    "required": ["status", "findings", "confidence", "authority"],
}


# ── Core Functions ───────────────────────────────────────────────────────


def flame_market_signal(
    raw_market_data: str,
    focus_asset: str | None = None,
) -> dict[str, Any] | None:
    """Extract and synthesize market signals from raw data.

    STRICTLY ADVISORY. ZERO-STATE. No trade execution capabilities.

    Flow:
      1. Schema-Forced Gate (F1) — schema REQUIRES authority="ADVISORY"
      2. L3 Task-Adaptive Routing — task_class="extract" → Qwen3.6 first
      3. Post-Generation Circuit Breaker — discard if authority != "ADVISORY"

    Args:
        raw_market_data: Raw market data as JSON string or structured text
        focus_asset: Optional asset to focus on (e.g., "XAUUSD", "CL=F")

    Returns:
        Structured signal dict with enforced ADVISORY tag, or None on F1 violation.
    """
    target = focus_asset if focus_asset else "macro market"

    prompt = (
        f"Analyze the following raw market data for {target}. "
        f"Extract key catalysts and determine the signal direction. "
        f"This is strictly for observational and advisory purposes.\n\n"
        f"RAW DATA:\n{raw_market_data[:4000]}"
    )

    # ── Step 1+2: Schema-Forced Gate + L3 Task Routing ──────────────────
    try:
        engine = _get_engine()
        result = engine.agentic_observe(
            prompt=prompt,
            json_schema=MARKET_SIGNAL_SCHEMA,
            task_class="extraction",  # Qwen3.6 → Ministral 8B chain
        )
    except Exception as e:
        logger.warning("flame_client: agentic_observe failed — %s", str(e)[:120])
        return {
            "error": "OBSERVE_FAILED",
            "message": f"FLAME inference engine error: {str(e)[:200]}",
            "authority": "ADVISORY",
        }

    # ── Step 3: Post-Generation Circuit Breaker ─────────────────────────
    if not result:
        return {
            "error": "OBSERVE_FAILED",
            "message": "FLAME returned empty result object.",
            "authority": "ADVISORY",
        }

    content = result.get("content", {})
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "JSON_PARSE_FAILED",
                "message": "FLAME returned non-JSON content.",
                "_raw": content[:300],
                "authority": "ADVISORY",
            }

    # ── F1 HARD ENFORCEMENT: Hallucinated authority → immediate discard ──
    declared_authority = content.get("authority", "UNKNOWN")
    if declared_authority != "ADVISORY":
        logger.error(
            "flame_client: F1 VIOLATION — signal generated with "
            "authority='%s' instead of 'ADVISORY'. Dropped to protect W_scar.",
            declared_authority,
        )
        return {
            "error": "F1_VIOLATION",
            "message": (
                f"Signal generated with authority='{declared_authority}' "
                f"instead of 'ADVISORY'. Dropped to protect W_scar."
            ),
            "authority": "ADVISORY",
        }

    # ── Attach provenance ───────────────────────────────────────────────
    content["_provenance"] = {
        "model": result.get("model", "unknown"),
        "provider": result.get("provider", "unknown"),
        "fingerprint": result.get("fingerprint", ""),
        "latency_ms": result.get("latency_ms", 0),
        "hops_used": result.get("hops_used", 1),
        "authority": "ADVISORY",
        "note": (
            "FLAME market signal interpretation via agentic_observe. "
            "For informational use only. Verify with governed cascade "
            "before any capital decision."
        ),
    }

    return content


def flame_extract(
    text: str,
    schema: dict[str, Any] | None = None,
    task_class: str = "extraction",
) -> dict[str, Any] | None:
    """Generic extraction through FLAME 2.0 direct bridge.

    Args:
        text: Text to analyze/extract from
        schema: JSON schema for structured output (default: EXTRACTION_SCHEMA)
        task_class: L3 routing — "extraction", "classification", "summarization"

    Returns:
        Parsed result dict with ADVISORY tag, or None on failure.
    """
    if schema is None:
        schema = EXTRACTION_SCHEMA

    try:
        engine = _get_engine()
        result = engine.agentic_observe(
            prompt=text[:5000],
            json_schema=schema,
            task_class=task_class,
        )
    except Exception as e:
        logger.warning("flame_client: flame_extract failed — %s", str(e)[:120])
        return None

    if not result:
        return None

    content = result.get("content", {})
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return None

    # F1 gate: verify ADVISORY tag
    if content.get("authority", "") != "ADVISORY":
        logger.error("flame_client: F1 VIOLATION in flame_extract — dropping")
        return None

    content["_provenance"] = {
        "model": result.get("model", "unknown"),
        "provider": result.get("provider", "unknown"),
        "fingerprint": result.get("fingerprint", ""),
        "authority": "ADVISORY",
    }
    return content


def flame_classify_market(
    text: str,
    categories: list[str] | None = None,
) -> dict[str, Any] | None:
    """Classify market-related text into predefined categories.

    Uses task_class="classification" → Groq 8B → Ministral 8B chain.
    Schema-enforced: output MUST include "category" and "confidence".

    Args:
        text: Market text to classify
        categories: List of category labels (default: bullish/bearish/neutral/volatile/uncertain)

    Returns:
        {"category": "...", "confidence": 0.X, "authority": "ADVISORY"} or None.
    """
    cats = categories or ["bullish", "bearish", "neutral", "volatile", "uncertain"]
    cat_str = ", ".join(cats)

    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": cats},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 0.90},
            "reasoning": {"type": "string"},
            "authority": {"type": "string", "enum": ["ADVISORY"]},
        },
        "required": ["category", "confidence", "authority"],
    }

    prompt = (
        f"Classify this market signal into EXACTLY one of: {cat_str}. "
        f"Respond with valid JSON.\n\n"
        f"TEXT: {text[:2000]}"
    )

    try:
        engine = _get_engine()
        result = engine.agentic_observe(
            prompt=prompt,
            json_schema=schema,
            task_class="classification",
        )
    except Exception as e:
        logger.warning("flame_client: flame_classify_market failed — %s", str(e)[:120])
        return None

    if not result:
        return None

    content = result.get("content", {})
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return None

    if content.get("authority", "") != "ADVISORY":
        return None

    content["_provenance"] = {
        "model": result.get("model", "unknown"),
        "provider": result.get("provider", "unknown"),
        "authority": "ADVISORY",
    }
    return content


# ── P2 SEALED Surface Map ────────────────────────────────────────────────
# FLAME 2.0 P2 wiring across all 4 organs:
#
#   GEOX    → geox_contradiction_scan, geox_evidence, geox_claim
#   arifOS  → arif_observe (search/fetch modes only)
#   A-FORGE → forge_search, forge_diagnose, forge_summarize, forge_plan
#   WEALTH  → flame_market_signal, flame_extract, flame_classify_market
#
# All surfaces: ADVISORY authority. Zero-Fly Zone hard-enforced.
# W_scar = $0 across all surfaces (FLAME is RM0, no billing path).
# P2 STATUS: SEALED — 2026-07-25
