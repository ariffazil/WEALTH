"""
WEALTH Core — Named-Entity Claim Gate.

P1 (WEALTH-RECONCILIATION-20260916): any claim about a real, named
institution or person may be published as OBSERVED only with an EXTERNAL
citation — the engine's own output is never a source. This gate is the
mechanism that would have blocked the false "zero independent NEDs" claim
before it reached a public page: that claim had no external source, was
computed from discarded input, and contradicted the institution's own
leadership record.

Rules (F2 TRUTH / F7 HUMILITY / structures-not-people, F13 2026-09-16):
  1. Non-entity claims carry no citation requirement (recorded as NON_ENTITY).
  2. Person-trait/behavior/competence claims are REJECTED — score
     structures, never personalities.
  3. Named-entity claims are OBS_ELIGIBLE only when:
     - source_uri is external (not self/engine/internal transport)
     - retrieved_at is present and ISO-8601
     - freshness within policy (freshness_days, if declared)
     - contradiction_check.status == CHECKED with an external second source
  4. Any HOLD or REJECT blocks the publication batch.

Pure computation: no I/O, no network fetches — the gate validates the
caller's declared evidence, it does not manufacture it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

# A source inside the federation's own surface is not an external witness.
_SELF_SOURCE_MARKERS = (
    "arif-fazil.com",
    "wealth://",
    "arifos://",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "file:",
)

_PERSON_FORBIDDEN_CATEGORIES = {
    "trait",
    "behavior",
    "character",
    "competence",
    "performance",
    "motive",
}


def _is_external_source(uri: str) -> bool:
    u = (uri or "").strip().lower()
    if not u:
        return False
    if u.startswith("/") or u.startswith("./"):
        return False
    return not any(marker in u for marker in _SELF_SOURCE_MARKERS)


def _parse_iso(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _validate_one(claim: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    text = str(claim.get("claim_text") or "")[:300]
    entities = claim.get("about_entities") or []
    entities = [e for e in entities if isinstance(e, dict) and e.get("name")]
    verdict = {
        "claim_text": text,
        "entities": [e.get("name") for e in entities],
        "verdict": "OBS_ELIGIBLE",
        "reasons": [],
    }

    if not entities:
        verdict["verdict"] = "NON_ENTITY"
        verdict["reasons"].append("no named entities — citation not required")
        return verdict

    # Rule 2 — structures, not people.
    for e in entities:
        if str(e.get("type", "")).lower() == "person" and str(
            claim.get("category", "")
        ).lower() in _PERSON_FORBIDDEN_CATEGORIES:
            verdict["verdict"] = "REJECT"
            verdict["reasons"].append(
                f"person-claim on '{e.get('name')}' in forbidden category "
                f"'{claim.get('category')}' — score structures, not personalities"
            )
            return verdict

    # Rule 3 — external citation ladder.
    source_uri = str(claim.get("source_uri") or "").strip()
    if not source_uri:
        verdict["verdict"] = "HOLD"
        verdict["reasons"].append("missing_citation: named-entity claim has no source_uri")
        return verdict
    if not _is_external_source(source_uri):
        verdict["verdict"] = "HOLD"
        verdict["reasons"].append(
            f"self_sourced: '{source_uri}' is not an external witness — "
            "engine output and own-domain pages never count as source"
        )
        return verdict

    retrieved_at = _parse_iso(claim.get("retrieved_at"))
    if retrieved_at is None:
        verdict["verdict"] = "HOLD"
        verdict["reasons"].append(
            "missing_retrieval_timestamp: retrieved_at absent or not ISO-8601"
        )
        return verdict
    verdict["retrieved_at"] = claim.get("retrieved_at")

    freshness_days = claim.get("freshness_days")
    if freshness_days is not None:
        try:
            age_days = (now - retrieved_at).total_seconds() / 86400.0
            if age_days > float(freshness_days):
                verdict["verdict"] = "HOLD"
                verdict["reasons"].append(
                    f"stale: retrieved {age_days:.1f}d ago exceeds "
                    f"freshness policy {float(freshness_days):.1f}d"
                )
                return verdict
        except (TypeError, ValueError):
            pass  # malformed policy — do not silently pass: fall through flagged
            verdict["reasons"].append("malformed freshness_days policy (ignored)")

    cc = claim.get("contradiction_check") or {}
    cc_status = str(cc.get("status", "")).upper()
    if cc_status != "CHECKED":
        verdict["verdict"] = "HOLD"
        verdict["reasons"].append(
            "contradiction_unchecked: no CHECKED contradiction check — "
            "an unchallenged single source may not publish as OBSERVED"
        )
        return verdict
    second = str(cc.get("second_source_uri") or "").strip()
    if not _is_external_source(second):
        verdict["verdict"] = "HOLD"
        verdict["reasons"].append(
            "invalid_second_source: contradiction check cites no external second source"
        )
        return verdict

    verdict["source_uri"] = source_uri
    verdict["second_source_uri"] = second
    return verdict


def validate_claims(
    claims: List[Dict[str, Any]],
    default_freshness_days: float | None = None,
) -> Dict[str, Any]:
    """Validate a batch of claims for publication. Gate semantics:
    any HOLD or REJECT blocks the batch."""
    now = datetime.now(timezone.utc)
    batch = claims or []
    results = [_validate_one(c, now) for c in batch]
    counts: Dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    blocking = counts.get("HOLD", 0) + counts.get("REJECT", 0)
    return {
        "status": "PASS" if not blocking else "BLOCKED",
        "publication_gate": "PASS" if not blocking else "BLOCKED",
        "claim_count": len(results),
        "verdict_counts": counts,
        "claims": results,
        "gate_rule": (
            "named-entity OBS claims require external source + retrieval "
            "timestamp + CHECKED contradiction (external second source); "
            "person-trait claims rejected; any HOLD/REJECT blocks the batch"
        ),
    }
