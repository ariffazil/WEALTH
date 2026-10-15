"""
WEALTH Semantic Concept Layer (capital_read / capital_rank_sources / capital_breakeven).

A thin, honest read layer over ~30 REAL capital concepts. Every concept binds to
either a live engine endpoint or a printed/seeded JSON source on this VPS — no
filler concepts, no fabrication. Every observation carries a verification flag
inline (VERIFIED_LIVE | VERIFIED_SINGLE | UNVERIFIED | STALE) and a real VAULT999
receipt pointer.

Governance (owner ruling, mission wealth-mcp-semantic):
- Evidence-gate withholding applies to THESE 3 TOOLS ONLY. The 15 standing
  capital_* tools keep their advisory behaviour untouched (stricter-than-C8).
- Scoped bearer tokens enforced on these 3 tools only (tokens.json, chmod 600).
- Every invocation logged to /root/WEALTH/logs/semantic_invocations.jsonl.
- 555_COMPUTE_ONLY: reads and deductive arithmetic only. No money movement.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wealth_contracts.epistemic import ClaimState, EpistemicTag, EvidenceQuality

# ── Paths ─────────────────────────────────────────────────────────────────
_SEMANTIC_BASE = Path(__file__).resolve().parent
ONTOLOGY_PATH = _SEMANTIC_BASE / "concepts_ontology.json"
TOKENS_PATH = _SEMANTIC_BASE / "tokens.json"
INVOCATION_LOG_PATH = Path(
    os.environ.get("WEALTH_SEMANTIC_LOG", "/root/WEALTH/logs/semantic_invocations.jsonl")
)


def _receipts_path() -> Path:
    """Resolve the organ's vault receipt store (same chain as server.py/canonical.py)."""
    return Path(
        os.environ.get("WEALTH_RECEIPT_PATH")
        or os.environ.get("WEALTH_RECEIPTS_PATH")
        or "/root/VAULT999/wealth/receipts.jsonl"
    )


_RECEIPT_SCHEMA_VERSION = "2026.07.24"  # match organ receipt consumers

# ── Verification vocabulary (same discipline as the web layer) ───────────
V_VERIFIED_LIVE = "VERIFIED_LIVE"
V_VERIFIED_SINGLE = "VERIFIED_SINGLE"
V_UNVERIFIED = "UNVERIFIED"
V_STALE = "STALE"
_STALE_AFTER_DAYS = 30

_FRESHNESS_SCORES = {
    "hourly": 1.0,
    "daily": 0.9,
    "weekly": 0.75,
    "monthly": 0.6,
    "event": 0.5,
    "static": 1.0,
}

# Sealed anchors (freshness=static / constitutional locks) never drift STALE.
_SEALED_FRESHNESS = {"static"}

# Treasury sensitivity for the fiscal breakeven (sealed on /wealth/malaysia/):
# RM3-4B per $10 Brent drop; point estimate uses the 3.5 midpoint, range exposed.
_BRENT_SENSITIVITY_RM_B_PER_10USD = 3.5
_BRENT_SENSITIVITY_RANGE = (3.0, 4.0)
_DEFICIT_TRIP_PCT = 5.0

_FETCH_TIMEOUT_S = 8.0

_lock = threading.Lock()


# ═════════════════════════════════════════════════════════════════════════
# Ontology loading (mtime-cached; owner-editable without rebuild)
# ═════════════════════════════════════════════════════════════════════════
_ontology_cache: dict[str, Any] = {"mtime": None, "data": None}


def load_ontology() -> dict[str, Any]:
    """Load concepts_ontology.json, re-reading when the file changes on disk."""
    mtime = ONTOLOGY_PATH.stat().st_mtime
    with _lock:
        if _ontology_cache["data"] is None or _ontology_cache["mtime"] != mtime:
            _ontology_cache["data"] = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
            _ontology_cache["mtime"] = mtime
        return _ontology_cache["data"]


def get_concept(concept_id: str) -> dict[str, Any] | None:
    onto = load_ontology()
    for c in onto.get("concepts", []):
        if c.get("id") == concept_id:
            return c
    return None


def known_concept_ids() -> list[str]:
    return [c.get("id", "") for c in load_ontology().get("concepts", [])]


# ═════════════════════════════════════════════════════════════════════════
# Binding ranking + field extraction
# ═════════════════════════════════════════════════════════════════════════
def rank_bindings(concept: dict[str, Any]) -> list[dict[str, Any]]:
    """Rank a concept's bindings best-first by quality × freshness score."""
    ranked = []
    for b in concept.get("bindings", []):
        q = float(b.get("quality", 0.0))
        f = _FRESHNESS_SCORES.get(str(b.get("freshness", "event")), 0.5)
        ranked.append({**b, "_rank_score": round(q * f, 4)})
    ranked.sort(key=lambda b: b["_rank_score"], reverse=True)
    for i, b in enumerate(ranked, start=1):
        b["rank"] = i
    return ranked


_SEG_RE = re.compile(r"^([A-Za-z0-9_\-]+)(?:\[(.*)\])?$")


def _extract_path(doc: Any, path: str) -> tuple[Any, list[Any]]:
    """Extract a value by dotted path.

    Supported segment forms: ``name``, ``name[3]`` (index),
    ``name[k=v]`` (first list entry whose dict field k equals v).
    Returns (value | None, list of container dicts traversed — used for
    verification-field inheritance).
    """
    containers: list[Any] = []
    node = doc
    for seg in str(path).split("."):
        m = _SEG_RE.match(seg.strip())
        if not m or not isinstance(node, dict):
            return None, containers
        name, bracket = m.group(1), m.group(2)
        if name not in node:
            return None, containers
        node = node[name]
        if bracket is not None:
            if re.fullmatch(r"-?\d+", bracket):
                idx = int(bracket)
                if not isinstance(node, list) or idx >= len(node) or idx < -len(node):
                    return None, containers
                node = node[idx]
            elif "=" in bracket:
                k, v = bracket.split("=", 1)
                if not isinstance(node, list):
                    return None, containers
                node = next(
                    (
                        e
                        for e in node
                        if isinstance(e, dict) and str(e.get(k, "")) == v
                    ),
                    None,
                )
                if node is None:
                    return None, containers
            else:
                return None, containers
        containers.append(node)
    return node, containers


def _parse_dt(raw: Any) -> datetime | None:
    if raw is None:
        return None
    s = str(raw).strip()
    for candidate in (s, s.replace("Z", "+00:00"), s[:10]):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _find_date(containers: list[Any], doc: dict[str, Any]) -> datetime | None:
    """Newest as_of / last_updated / observed_at among traversed containers + doc."""
    best: datetime | None = None
    for node in [*containers, doc]:
        if not isinstance(node, dict):
            continue
        for key in ("as_of", "collected_at", "observed_at", "last_updated", "date"):
            if key in node:
                dt = _parse_dt(node.get(key))
                if dt and (best is None or dt > best):
                    best = dt
        # nested dict values (e.g. yoy_growth_pct_claim) can carry as_of too
        for v in node.values():
            if isinstance(v, dict):
                for key in ("as_of", "collected_at", "observed_at"):
                    if key in v:
                        dt = _parse_dt(v.get(key))
                        if dt and (best is None or dt > best):
                            best = dt
    return best


def _find_verification_field(containers: list[Any], doc: dict[str, Any]) -> str | None:
    """Inherit a declared verification flag from the nearest traversed container."""
    for node in reversed([*containers, doc]):
        if isinstance(node, dict) and "verification" in node:
            v = node.get("verification")
            if isinstance(v, str) and v.strip():
                return v.strip().upper()
    return None


def _normalise_verification(raw: str | None) -> str:
    v = (raw or "").strip().upper()
    if v in (V_VERIFIED_LIVE, V_VERIFIED_SINGLE, V_UNVERIFIED, V_STALE):
        return v
    if v.startswith("VERIFIED"):
        # e.g. "VERIFIED (2 sources)" → conservative single-source reading
        return V_VERIFIED_SINGLE
    if not v:
        return V_VERIFIED_SINGLE  # unlabelled static SOT → single-source default
    return V_UNVERIFIED


# ═════════════════════════════════════════════════════════════════════════
# Fetchers (stdlib only)
# ═════════════════════════════════════════════════════════════════════════
def _fetch_engine(locator: str) -> dict[str, Any]:
    req = urllib.request.Request(  # noqa: S310 — loopback/owned hosts only
        locator,
        headers={"User-Agent": "wealth-mcp-semantic/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT_S) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _fetch_static(locator: str) -> dict[str, Any]:
    p = Path(locator)
    if not p.is_file():
        raise FileNotFoundError(f"static source absent: {locator}")
    return json.loads(p.read_text(encoding="utf-8"))


# ═════════════════════════════════════════════════════════════════════════
# Resolution
# ═════════════════════════════════════════════════════════════════════════
def resolve_concept(concept_id: str) -> dict[str, Any]:
    """Resolve a concept to its best observable observation.

    Returns one of:
      {"status": "resolved", "observation": {...}}
      {"status": "unresolved", "errors": [...], "attempts": [...]}
    Never fabricates a number: fetch failure surfaces the feed name.
    """
    concept = get_concept(concept_id)
    if concept is None:
        return {
            "status": "unknown_concept",
            "errors": [f"unknown concept_id '{concept_id}'"],
            "known_concept_ids": known_concept_ids(),
        }

    errors: list[str] = []
    attempts: list[dict[str, Any]] = []
    for binding in rank_bindings(concept):
        locator = str(binding.get("locator", ""))
        kind = str(binding.get("source_kind", "static_json"))
        try:
            if kind == "engine_api":
                try:
                    doc = _fetch_engine(locator)
                except (urllib.error.URLError, OSError, ValueError):
                    public = binding.get("public_locator")
                    if public:
                        doc = _fetch_engine(str(public))
                    else:
                        raise
            elif kind == "static_json":
                doc = _fetch_static(locator)
            elif kind == "computed":
                raise ValueError(
                    f"binding kind 'computed' has no resolver on '{concept_id}'"
                )
            else:
                raise ValueError(f"unknown binding source_kind '{kind}'")
        except Exception as exc:  # noqa: BLE001 — fail-state honesty below
            errors.append(f"feed {locator}: {type(exc).__name__}: {exc}")
            attempts.append({"locator": locator, "ok": False})
            continue

        value, containers = _extract_path(doc, str(binding.get("jsonpath_or_field", "")))
        if value is None:
            errors.append(
                f"feed {locator}: field '{binding.get('jsonpath_or_field')}' not found"
            )
            attempts.append({"locator": locator, "ok": False})
            continue

        scale = binding.get("scale")
        if scale is not None and isinstance(value, (int, float)):
            value = round(float(value) * float(scale), 6)
            if value == int(value):
                value = float(value)

        # ── Verification determination ────────────────────────────────
        if kind == "engine_api":
            ticker = doc.get("ticker", {}) if isinstance(doc, dict) else {}
            stale_flag = bool(ticker.get("stale", False)) if isinstance(ticker, dict) else False
            observed_at = _parse_dt(doc.get("observed_at")) if isinstance(doc, dict) else None
            age_days = (
                (datetime.now(timezone.utc) - observed_at).total_seconds() / 86400.0
                if observed_at
                else None
            )
            if stale_flag or (age_days is not None and age_days > _STALE_AFTER_DAYS):
                verification = V_STALE
            else:
                verification = V_VERIFIED_LIVE
            source = locator
            as_of = doc.get("observed_at") if isinstance(doc, dict) else None
            source_declared = "stale" if stale_flag else None
        else:
            declared = _find_verification_field(containers, doc)
            verification = _normalise_verification(declared)
            declared_as_of = binding.get("declared_as_of")
            age_dt = (
                _parse_dt(declared_as_of) if declared_as_of else _find_date(containers, doc)
            )
            age_days = (
                (datetime.now(timezone.utc) - age_dt).total_seconds() / 86400.0
                if age_dt
                else None
            )
            freshness = str(binding.get("freshness", "event"))
            if (
                verification in (V_VERIFIED_LIVE, V_VERIFIED_SINGLE)
                and freshness not in _SEALED_FRESHNESS
                and age_days is not None
                and age_days > _STALE_AFTER_DAYS
            ):
                verification = V_STALE
            source = locator
            as_of = str(age_dt.date()) if age_dt else None
            source_declared = declared

        formula_note = None
        for node in containers:
            if isinstance(node, dict) and node.get("formula_note"):
                formula_note = str(node["formula_note"])
                break

        observation = {
            "concept_id": concept_id,
            "value": value,
            "unit": concept.get("unit"),
            "verification": verification,
            "source": source,
            "source_kind": kind,
            "source_declared_verification": source_declared,
            "binding_quality": binding.get("quality"),
            "binding_freshness": binding.get("freshness"),
            "rank_score": binding.get("_rank_score"),
            "observed_at": as_of,
            "entity_id": concept.get("entity_default"),
            "title": concept.get("title"),
            "description": concept.get("description"),
            "refresh": concept.get("refresh"),
            "source_note": concept.get("description"),
        }
        if formula_note:
            observation["formula_note"] = formula_note
        if binding.get("scale") is not None:
            observation["formula_note"] = (
                f"raw field '{binding.get('jsonpath_or_field')}' scaled ×{binding.get('scale')} "
                f"to unit '{concept.get('unit')}'"
            )
        if isinstance(age_days, (int, float)):
            observation["age_days"] = round(age_days, 2)
        return {"status": "resolved", "observation": observation}

    return {"status": "unresolved", "errors": errors, "attempts": attempts}


# ═════════════════════════════════════════════════════════════════════════
# Scoped tokens (3 new tools only — v1, no OAuth)
# ═════════════════════════════════════════════════════════════════════════
_SCOPE_TOOL_MATRIX: dict[str, tuple[str, ...]] = {
    "wealth:read": ("capital_read", "capital_rank_sources"),
    "wealth:compute": ("capital_read", "capital_rank_sources", "capital_breakeven"),
    "wealth:admin": ("capital_read", "capital_rank_sources", "capital_breakeven"),
}

_TOKEN_CACHE: dict[str, Any] = {"mtime": None, "data": {}}


def _load_tokens() -> dict[str, dict[str, Any]]:
    try:
        mtime = TOKENS_PATH.stat().st_mtime
    except OSError:
        return {}
    with _lock:
        if _TOKEN_CACHE["data"] is None or _TOKEN_CACHE["mtime"] != mtime:
            try:
                raw = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
                _TOKEN_CACHE["data"] = raw.get("tokens", {})
            except (OSError, json.JSONDecodeError):
                _TOKEN_CACHE["data"] = {}
            _TOKEN_CACHE["mtime"] = mtime
        return _TOKEN_CACHE["data"]


def _extract_bearer_token(token_arg: str | None) -> tuple[str | None, str | None]:
    """Resolve token from Authorization: Bearer | X-Wealth-Token | token= arg.

    Returns (token, via) — via names the channel for the audit log.
    """
    try:
        from fastmcp.server.dependencies import get_http_headers

        # include authorization explicitly: FastMCP strips credential headers
        # (authorization/cookie) from the default header view.
        headers = get_http_headers(include={"authorization"}) or {}
    except Exception:
        headers = {}
    norm = {str(k).lower(): v for k, v in headers.items()}
    authz = norm.get("authorization", "")
    if authz.lower().startswith("bearer "):
        tok = authz[7:].strip()
        if tok:
            return tok, "authorization_bearer"
    xtok = norm.get("x-wealth-token", "")
    if xtok.strip():
        return xtok.strip(), "x_wealth_token_header"
    if token_arg and str(token_arg).strip():
        return str(token_arg).strip(), "token_arg"
    return None, None


def authenticate(token_arg: str | None, tool_name: str) -> dict[str, Any]:
    """Return {ok, label, scopes, via} for the calling token on this tool."""
    token, via = _extract_bearer_token(token_arg)
    if not token:
        return {
            "ok": False,
            "reason": "missing token — supply Authorization: Bearer <token>, "
            "X-Wealth-Token header, or token= argument",
            "label": None,
            "scopes": [],
            "via": via,
        }
    entry = _load_tokens().get(token)
    if not entry:
        return {"ok": False, "reason": "invalid token", "label": None, "scopes": [], "via": via}
    scopes = list(entry.get("scopes", []))
    allowed: set[str] = set()
    for s in scopes:
        allowed.update(_SCOPE_TOOL_MATRIX.get(s, ()))
    if tool_name not in allowed:
        return {
            "ok": False,
            "reason": f"token label '{entry.get('label')}' scopes {scopes} do not "
            f"authorize '{tool_name}'",
            "label": entry.get("label"),
            "scopes": scopes,
            "via": via,
        }
    return {"ok": True, "label": entry.get("label"), "scopes": scopes, "via": via}


# ═════════════════════════════════════════════════════════════════════════
# Invocation log + vault receipt (REAL ledger pointers)
# ═════════════════════════════════════════════════════════════════════════
def log_invocation(record: dict[str, Any]) -> None:
    """Append one JSONL line to the semantic invocation log. Fail-soft."""
    try:
        INVOCATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {"timestamp_utc": datetime.now(timezone.utc).isoformat(), **record},
            default=str,
            ensure_ascii=False,
        )
        with _lock:
            with INVOCATION_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError:
        pass  # logging must never break the compute path


def write_semantic_receipt(
    tool_name: str,
    arguments: dict[str, Any],
    call_status: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a receipt to the organ's VAULT999 receipt store.

    Follows the organ receipt schema used by server.py::_emit_receipt so the
    receipt is first-class for capital_ledger(mode=query) consumers.
    Returns {receipt_id, path, persisted}.
    """
    path = _receipts_path()
    receipt_id = str(uuid.uuid4())
    receipt = {
        "receipt_id": receipt_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "actor_id": "wealth-mcp/semantic",
        "tool_name": tool_name,
        "arguments": {
            k: v
            for k, v in (arguments or {}).items()
            if k not in ("token", "actor_signature", "nonce", "_meta")
        },
        "epistemic_state": "DERIVED",
        "evidence_quality": "OBSERVED" if call_status == "PASS" else "MISSING",
        "domain": "semantic",
        "call_status": call_status,
        "idempotency_key": None,
        "governance_status": "READONLY",
        "transport": "mcp_call_tool",
        "schema_version": _RECEIPT_SCHEMA_VERSION,
        "semantic_layer": True,
    }
    if extra:
        receipt.update(extra)
    persisted = False
    error = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(receipt, default=str, ensure_ascii=False) + "\n")
        persisted = True
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"receipt_id": receipt_id, "path": str(path), "persisted": persisted, "error": error}


def arifos_meta(
    evidence_gate: str,
    receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    """Governance envelope block required on every new-tool result."""
    if receipt and receipt.get("receipt_id"):
        pointer = f"{receipt['path']}#{receipt['receipt_id']}"
    else:
        pointer = f"{_receipts_path()}#UNPERSISTED_WRITE_FAILED"
    return {
        "arifOS_fidelity": "F1-F13",
        "delta_s": "≤0",
        "reversibility": "reversible",
        "evidence_gate": evidence_gate,
        "ledger_pointer": pointer,
    }


# ═════════════════════════════════════════════════════════════════════════
# Fiscal breakeven (deductive — golden-tested)
# ═════════════════════════════════════════════════════════════════════════
def compute_budget_balance_breakeven(
    spot: float,
    fiscal_deficit_pct: float,
    gdp_rm_b: float,
    sensitivity_rm_b_per_10usd: float = _BRENT_SENSITIVITY_RM_B_PER_10USD,
    deficit_trip_pct: float = _DEFICIT_TRIP_PCT,
) -> dict[str, Any]:
    """Deductive fiscal-breakeven Brent.

    deficit_headroom_rm_b = ((deficit_trip_pct − fiscal_deficit_pct) / 100) × gdp_rm_b
    breakeven_brent       = spot − (deficit_headroom_rm_b / sensitivity) × 10

    Hand-checked golden: spot=100, deficit=3.8, gdp=1900, sens=3.5
      → headroom = 1.2% × 1900 = 22.8 RM B → allowance = 22.8/3.5×10 = 65.142857…
      → breakeven = 34.8571 (range 24.0–43.0 for sens ∈ [3, 4]).
    """
    headroom_rm_b = ((deficit_trip_pct - fiscal_deficit_pct) / 100.0) * gdp_rm_b
    allowance = (headroom_rm_b / sensitivity_rm_b_per_10usd) * 10.0
    # Range: low sensitivity bound (3.0) → largest allowance → LOWEST breakeven.
    allowance_low_breakeven = (headroom_rm_b / _BRENT_SENSITIVITY_RANGE[0]) * 10.0
    allowance_high_breakeven = (headroom_rm_b / _BRENT_SENSITIVITY_RANGE[1]) * 10.0
    return {
        "deficit_headroom_rm_b": round(headroom_rm_b, 4),
        "allowance_usd": round(allowance, 4),
        "breakeven_brent": round(spot - allowance, 4),
        "breakeven_brent_range_low": round(spot - allowance_low_breakeven, 4),
        "breakeven_brent_range_high": round(spot - allowance_high_breakeven, 4),
        "sensitivity_rm_b_per_10usd": sensitivity_rm_b_per_10usd,
        "sensitivity_range": list(_BRENT_SENSITIVITY_RANGE),
    }


# ═════════════════════════════════════════════════════════════════════════
# Tool registration
# ═════════════════════════════════════════════════════════════════════════
_SEMANTIC_TOOL_VERSION = "2026.10.15"


def _refusal(tool_name: str, reason: str, auth: dict[str, Any]) -> dict[str, Any]:
    """Structured refusal — no concept data, no numbers."""
    receipt = write_semantic_receipt(
        tool_name, {"auth_refused": True}, "REFUSED", extra={"refusal_reason": reason}
    )
    log_invocation(
        {
            "tool": tool_name,
            "token_label": auth.get("label"),
            "via": auth.get("via"),
            "scope": auth.get("scopes"),
            "outcome": "REFUSED",
            "reason": reason,
        }
    )
    from wealth_contracts.envelope import wrap_result

    d = wrap_result(
        tool_name=tool_name,
        domain="semantic",
        result={
            "status": "REFUSED",
            "reason": reason,
            "required_scopes": sorted(
                {s for s, tools in _SCOPE_TOOL_MATRIX.items() if tool_name in tools}
            ),
        },
        epistemic_tag=EpistemicTag.ASSUMED,
        evidence_quality=EvidenceQuality.MISSING,
        claim_state=ClaimState.DRAFT,
        errors=[f"AUTH: {reason}"],
        metadata={"semantic_layer": True, "auth_via": auth.get("via")},
    )
    d["_meta"] = {"arifOS": arifos_meta("failed", receipt)}
    return d


def _gate_fail(
    tool_name: str,
    concept_ids: list[str],
    errors: list[str],
    input_requests: list[dict[str, str]],
    arguments: dict[str, Any],
    auth: dict[str, Any],
) -> dict[str, Any]:
    """Evidence-gate FAIL: structured result with NO numbers (MRTR spirit)."""
    receipt = write_semantic_receipt(
        tool_name,
        arguments,
        "EVIDENCE_GATE_FAILED",
        extra={"evidence_gate": "failed", "errors": errors},
    )
    log_invocation(
        {
            "tool": tool_name,
            "token_label": auth.get("label"),
            "via": auth.get("via"),
            "scope": auth.get("scopes"),
            "concept_id": arguments.get("concept_id"),
            "entity_id": arguments.get("entity_id"),
            "evidence_gate": "failed",
            "outcome": "WITHHELD",
            "errors": errors,
        }
    )
    from wealth_contracts.envelope import wrap_result

    d = wrap_result(
        tool_name=tool_name,
        domain="semantic",
        result={
            "status": "WITHHELD",
            "evidence_gate": "failed",
            "withheld": True,
            "numbers": None,
            "concept_ids": concept_ids,
            "errors": errors,
            "input_requests": input_requests,
        },
        epistemic_tag=EpistemicTag.ASSUMED,
        evidence_quality=EvidenceQuality.MISSING,
        claim_state=ClaimState.DRAFT,
        source_attribution=[],
        errors=errors,
        metadata={"semantic_layer": True},
    )
    d["_meta"] = {"arifOS": arifos_meta("failed", receipt)}
    return d


def register_semantic_tools(mcp) -> None:
    """Register the 3 semantic-layer tools. Call from server.py."""
    from wealth_contracts.envelope import wrap_result

    # ── 1. capital_read ───────────────────────────────────────────────
    @mcp.tool(
        name="capital_read",
        description=(
            "Semantic concept layer: read ONE governed capital concept by id "
            "(e.g. commodity.brent.spot, gold.cb_streak_months, petronas.net_cash_rm_b, "
            "sovereign.fiscal_deficit_pct). Every observation carries an inline "
            "verification flag (VERIFIED_LIVE | VERIFIED_SINGLE | UNVERIFIED | STALE) "
            "and a real VAULT999 ledger pointer. Evidence gate: if no binding resolves "
            "or the observation is UNVERIFIED, the number is WITHHELD and input_requests "
            "names what is missing — never a guess. Scoped token required "
            "(wealth:read / wealth:compute / wealth:admin). "
            "SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl "
            "and an invocation log line to /root/WEALTH/logs/semantic_invocations.jsonl."
        ),
        tags={"domain": "semantic", "kind": "observational", "canonical": "semantic-v1"},
    )
    async def capital_read(
        concept_id: str,
        entity_id: str | None = None,
        as_of: str | None = None,
        token: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        auth = authenticate(token, "capital_read")
        if not auth["ok"]:
            return _refusal("capital_read", auth["reason"], auth)

        arguments = {
            "concept_id": concept_id,
            "entity_id": entity_id,
            "as_of": as_of,
        }
        concept = get_concept(concept_id)
        if concept is None:
            return _gate_fail(
                "capital_read",
                [concept_id],
                [f"unknown concept_id '{concept_id}'"],
                [
                    {
                        "field": "concept_id",
                        "why": f"'{concept_id}' is not in concepts_ontology.json; "
                        f"known ids: {', '.join(known_concept_ids())}",
                    }
                ],
                arguments,
                auth,
            )

        resolution = resolve_concept(concept_id)
        if resolution["status"] == "unknown_concept":
            return _gate_fail(
                "capital_read", [concept_id], resolution["errors"], [], arguments, auth
            )
        if resolution["status"] == "unresolved":
            return _gate_fail(
                "capital_read",
                [concept_id],
                resolution["errors"],
                [
                    {
                        "field": str((concept.get("bindings") or [{}])[0].get(
                            "jsonpath_or_field", "source field"
                        )),
                        "why": f"no binding for '{concept_id}' could be fetched or parsed; "
                        "provide the source feed/field or restore the locator",
                    }
                ],
                arguments,
                auth,
            )

        obs = resolution["observation"]
        if entity_id:
            obs["entity_id"] = entity_id
        if as_of:
            obs["requested_as_of"] = as_of
            obs["as_of_note"] = (
                f"as_of '{as_of}' requested; the resolver serves current state only — "
                f"observation is from observed_at={obs.get('observed_at')}"
            )

        gate = "failed" if obs["verification"] == V_UNVERIFIED else "passed"
        if gate == "failed":
            return _gate_fail(
                "capital_read",
                [concept_id],
                [
                    f"observation for '{concept_id}' resolved but is UNVERIFIED "
                    f"(source {obs['source']}); number withheld"
                ],
                [
                    {
                        "field": concept_id,
                        "why": "observation resolved but is UNVERIFIED "
                        "(source's own verification declaration or absence of one) — "
                        "supply a verified source (second witness or sealed print) "
                        "before this number can be released",
                    }
                ],
                arguments,
                auth,
            )

        receipt = write_semantic_receipt(
            "capital_read",
            arguments,
            "PASS",
            extra={
                "evidence_gate": gate,
                "verification": obs["verification"],
                "concept_id": concept_id,
            },
        )
        log_invocation(
            {
                "tool": "capital_read",
                "token_label": auth.get("label"),
                "via": auth.get("via"),
                "scope": auth.get("scopes"),
                "concept_id": concept_id,
                "entity_id": obs.get("entity_id"),
                "as_of": as_of,
                "verification": obs["verification"],
                "evidence_gate": gate,
                "outcome": "OK",
            }
        )
        d = wrap_result(
            tool_name="capital_read",
            domain="semantic",
            result=obs,
            result_type="object",
            epistemic_tag=EpistemicTag.OBSERVED
            if obs["verification"] in (V_VERIFIED_LIVE, V_VERIFIED_SINGLE, V_STALE)
            else EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.OBSERVED,
            claim_state=ClaimState.QC_VERIFIED
            if obs["verification"] in (V_VERIFIED_LIVE, V_VERIFIED_SINGLE)
            else ClaimState.DRAFT,
            source_attribution=[obs["source"]],
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            metadata={
                "semantic_layer": True,
                "verification": obs["verification"],
                "entity_id": obs.get("entity_id"),
            },
        )
        d["_meta"] = {"arifOS": arifos_meta(gate, receipt)}
        return d

    # ── 2. capital_rank_sources ───────────────────────────────────────
    @mcp.tool(
        name="capital_rank_sources",
        description=(
            "Semantic concept layer: list the bindings backing ONE concept, ranked "
            "best-first by quality × freshness. Shows locator, quality, freshness, "
            "verification policy, and computed rank — the transparency surface for "
            "capital_read resolution. Metadata only (no fetching, no numbers). "
            "Scoped token required (wealth:read / wealth:compute / wealth:admin). "
            "SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl "
            "and an invocation log line."
        ),
        tags={"domain": "semantic", "kind": "observational", "canonical": "semantic-v1"},
    )
    async def capital_rank_sources(
        concept_id: str,
        token: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        auth = authenticate(token, "capital_rank_sources")
        if not auth["ok"]:
            return _refusal("capital_rank_sources", auth["reason"], auth)

        arguments = {"concept_id": concept_id}
        concept = get_concept(concept_id)
        if concept is None:
            return _gate_fail(
                "capital_rank_sources",
                [concept_id],
                [f"unknown concept_id '{concept_id}'"],
                [
                    {
                        "field": "concept_id",
                        "why": f"'{concept_id}' is not in concepts_ontology.json; "
                        f"known ids: {', '.join(known_concept_ids())}",
                    }
                ],
                arguments,
                auth,
            )

        ranked = [
            {
                "rank": b["rank"],
                "source_kind": b.get("source_kind"),
                "locator": b.get("locator"),
                "public_locator": b.get("public_locator"),
                "jsonpath_or_field": b.get("jsonpath_or_field"),
                "quality": b.get("quality"),
                "freshness": b.get("freshness"),
                "verification_policy": b.get("verification_policy"),
                "rank_score": b.get("_rank_score"),
            }
            for b in rank_bindings(concept)
        ]
        receipt = write_semantic_receipt("capital_rank_sources", arguments, "PASS")
        log_invocation(
            {
                "tool": "capital_rank_sources",
                "token_label": auth.get("label"),
                "via": auth.get("via"),
                "scope": auth.get("scopes"),
                "concept_id": concept_id,
                "evidence_gate": "passed",
                "outcome": "OK",
                "bindings": len(ranked),
            }
        )
        d = wrap_result(
            tool_name="capital_rank_sources",
            domain="semantic",
            result={
                "concept_id": concept_id,
                "title": concept.get("title"),
                "unit": concept.get("unit"),
                "refresh": concept.get("refresh"),
                "bindings": ranked,
                "resolution_rule": "best binding by quality × freshness; "
                "fall through to next on fetch failure",
            },
            result_type="object",
            epistemic_tag=EpistemicTag.OBSERVED,
            evidence_quality=EvidenceQuality.OBSERVED,
            claim_state=ClaimState.QC_VERIFIED,
            source_attribution=[ONTOLOGY_PATH.name],
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            metadata={"semantic_layer": True},
        )
        d["_meta"] = {"arifOS": arifos_meta("passed", receipt)}
        return d

    # ── 3. capital_breakeven ──────────────────────────────────────────
    @mcp.tool(
        name="capital_breakeven",
        description=(
            "Semantic concept layer: deductive fiscal-breakeven Brent for Malaysia. "
            "anchor='budget_balance': breakeven = spot − ((5% − deficit%)/100 × GDP) "
            "/ sensitivity × 10, with sensitivity RM3–4B per $10 (Treasury, sealed) — "
            "point estimate uses the 3.5 midpoint and the range is exposed. "
            "anchor='dividend_floor': returns the sealed Overlay T-A anchor ($67.34) "
            "with provenance. 555_COMPUTE_ONLY — arithmetic, never advice or execution. "
            "Every input carries its verification flag inline; any UNVERIFIED input "
            "withholds the result (input_requests instead of a guess). Scoped token "
            "required (wealth:compute or wealth:admin). "
            "SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl "
            "and an invocation log line."
        ),
        tags={"domain": "semantic", "kind": "deductive", "canonical": "semantic-v1"},
    )
    async def capital_breakeven(
        market: str = "MY",
        fiscal_anchor: str = "budget_balance",
        token: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        auth = authenticate(token, "capital_breakeven")
        if not auth["ok"]:
            return _refusal("capital_breakeven", auth["reason"], auth)

        arguments = {"market": market, "fiscal_anchor": fiscal_anchor}
        anchor = str(fiscal_anchor).lower()

        if str(market).upper() != "MY":
            return _gate_fail(
                "capital_breakeven",
                [],
                [f"market '{market}' is not wired — only MY (Malaysia federal) exists"],
                [
                    {
                        "field": "market",
                        "why": "fiscal breakeven requires a wired sovereign data layer; "
                        "only MY is seeded (/var/www/html/arif/data/sovereign/malaysia.json)",
                    }
                ],
                arguments,
                auth,
            )
        if anchor not in ("budget_balance", "dividend_floor"):
            return _gate_fail(
                "capital_breakeven",
                [],
                [f"unknown fiscal_anchor '{fiscal_anchor}'"],
                [
                    {
                        "field": "fiscal_anchor",
                        "why": "must be 'budget_balance' (deductive) or 'dividend_floor' "
                        "(sealed Overlay T-A anchor)",
                    }
                ],
                arguments,
                auth,
            )

        # ── Gather inputs with their verification flags ───────────────
        inputs: dict[str, dict[str, Any]] = {}
        needed = ["commodity.brent.spot", "sovereign.fiscal_deficit_pct"]
        if anchor == "dividend_floor":
            needed.append("commodity.brent.dividend_floor")
        else:
            needed.append("sovereign.gdp_rm_t")
        errors: list[str] = []
        for cid in needed:
            res = resolve_concept(cid)
            if res["status"] != "resolved":
                errors.extend(res.get("errors") or [f"{cid}: unresolvable"])
                inputs[cid] = {"resolved": False}
                continue
            obs = res["observation"]
            inputs[cid] = {
                "resolved": True,
                "value": obs["value"],
                "verification": obs["verification"],
                "source": obs["source"],
                "observed_at": obs.get("observed_at"),
            }
            if obs["verification"] == V_UNVERIFIED:
                errors.append(
                    f"{cid}: observation is UNVERIFIED (source {obs['source']})"
                )

        if errors or any(not v.get("resolved") for v in inputs.values()):
            missing_map = {
                "commodity.brent.spot": "live Brent spot from the oil engine "
                "(http://127.0.0.1:3457/api/snapshot)",
                "sovereign.fiscal_deficit_pct": "sealed federal deficit %GPD print in "
                "/var/www/html/arif/data/sovereign/malaysia.json",
                "sovereign.gdp_rm_t": "explicit gdp_rm_t in "
                "/var/www/html/arif/data/sovereign/malaysia.json",
                "commodity.brent.dividend_floor": "sealed floor_price_usd in "
                "/var/www/html/arif/data/oil/floor.json",
            }
            return _gate_fail(
                "capital_breakeven",
                needed,
                errors,
                [
                    {"field": cid, "why": f"required input unavailable — {missing_map.get(cid, 'source feed unresolvable')}"}
                    for cid in needed
                    if not inputs.get(cid, {}).get("resolved")
                ]
                or [
                    {
                        "field": "verification",
                        "why": "a required input resolved but is UNVERIFIED — supply a "
                        "verified source before the computation is released",
                    }
                ],
                arguments,
                auth,
            )

        spot = float(inputs["commodity.brent.spot"]["value"])
        receipt_extra = {"evidence_gate": "passed", "anchor": anchor}

        if anchor == "dividend_floor":
            floor = float(inputs["commodity.brent.dividend_floor"]["value"])
            result = {
                "status": "OK",
                "market": "MY",
                "fiscal_anchor": "dividend_floor",
                "breakeven_brent": floor,
                "formula": "breakeven_brent = sealed Overlay T-A dividend-floor anchor "
                "(no computation) — at $67.34 sustained Brent, PETRONAS dividend "
                "extraction falls below the RM20B floor",
                "anchor_provenance": {
                    "source": inputs["commodity.brent.dividend_floor"]["source"],
                    "verification": inputs["commodity.brent.dividend_floor"]["verification"],
                    "observed_at": inputs["commodity.brent.dividend_floor"].get("observed_at"),
                    "note": "Model anchor sealed on /wealth/malaysia/ (Overlay T-A). "
                    "Single model source — not an observation.",
                },
                "inputs": {
                    k: {
                        "value": v.get("value"),
                        "verification": v.get("verification"),
                        "source": v.get("source"),
                    }
                    for k, v in inputs.items()
                },
                "context": {
                    "spot_now": spot,
                    "spot_verification": inputs["commodity.brent.spot"]["verification"],
                    "above_floor": spot > floor,
                },
            }
            epistemic = EpistemicTag.OBSERVED
            claim = ClaimState.QC_VERIFIED
        else:
            deficit = float(inputs["sovereign.fiscal_deficit_pct"]["value"])
            gdp_res = resolve_concept("sovereign.gdp_rm_t")
            gdp_obs = gdp_res["observation"]
            if gdp_obs["verification"] == V_UNVERIFIED:
                return _gate_fail(
                    "capital_breakeven",
                    needed,
                    ["sovereign.gdp_rm_t: UNVERIFIED"],
                    [
                        {
                            "field": "gdp_rm_t",
                            "why": "explicit GDP (RM trillion) required in "
                            "/var/www/html/arif/data/sovereign/malaysia.json — "
                            "never re-derived at call time",
                        }
                    ],
                    arguments,
                    auth,
                )
            gdp_rm_b = float(gdp_obs["value"]) * 1000.0
            math_block = compute_budget_balance_breakeven(spot, deficit, gdp_rm_b)
            result = {
                "status": "OK",
                "market": "MY",
                "fiscal_anchor": "budget_balance",
                "breakeven_brent": math_block["breakeven_brent"],
                "formula": "breakeven_brent = spot − (deficit_headroom_rm_b / "
                "sensitivity_rm_b_per_10usd) × 10 ; deficit_headroom_rm_b = "
                "((5 − fiscal_deficit_pct)/100) × GDP_rm_b",
                "components": {
                    "spot_usd": {
                        "value": spot,
                        "verification": inputs["commodity.brent.spot"]["verification"],
                        "source": inputs["commodity.brent.spot"]["source"],
                    },
                    "fiscal_deficit_pct": {
                        "value": deficit,
                        "verification": inputs["sovereign.fiscal_deficit_pct"]["verification"],
                        "source": inputs["sovereign.fiscal_deficit_pct"]["source"],
                    },
                    "gdp_rm_b": {
                        "value": gdp_rm_b,
                        "verification": gdp_obs["verification"],
                        "source": gdp_obs["source"],
                        "formula_note": gdp_obs.get("formula_note"),
                    },
                    "deficit_headroom_rm_b": {
                        "value": math_block["deficit_headroom_rm_b"],
                        "verification": "DERIVED",
                        "formula_note": "((5 − deficit_pct)/100) × GDP_rm_b — deductive",
                    },
                    "sensitivity_rm_b_per_10usd": {
                        "value": math_block["sensitivity_rm_b_per_10usd"],
                        "range": math_block["sensitivity_range"],
                        "verification": "VERIFIED_SINGLE",
                        "source": "Treasury, sealed on /wealth/malaysia/ "
                        "(+RM3-4B per $10 drop); point estimate = 3.5 midpoint",
                    },
                },
                "breakeven_brent_range": [
                    math_block["breakeven_brent_range_low"],
                    math_block["breakeven_brent_range_high"],
                ],
                "range_note": "range from Treasury sensitivity bounds RM3.0–4.0B per $10",
                "inputs": {
                    k: {
                        "value": v.get("value"),
                        "verification": v.get("verification"),
                        "source": v.get("source"),
                    }
                    for k, v in inputs.items()
                },
            }
            epistemic = EpistemicTag.DERIVED
            claim = ClaimState.QC_VERIFIED

        receipt = write_semantic_receipt("capital_breakeven", arguments, "PASS", extra=receipt_extra)
        log_invocation(
            {
                "tool": "capital_breakeven",
                "token_label": auth.get("label"),
                "via": auth.get("via"),
                "scope": auth.get("scopes"),
                "concept_id": "capital_breakeven",
                "entity_id": market,
                "fiscal_anchor": anchor,
                "evidence_gate": "passed",
                "breakeven_brent": result.get("breakeven_brent"),
                "outcome": "OK",
            }
        )
        d = wrap_result(
            tool_name="capital_breakeven",
            domain="capital",
            result=result,
            result_type="object",
            epistemic_tag=epistemic,
            evidence_quality=EvidenceQuality.OBSERVED,
            claim_state=claim,
            source_attribution=sorted({v["source"] for v in inputs.values() if v.get("source")}),
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
            metadata={"semantic_layer": True, "fiscal_anchor": anchor},
        )
        d["_meta"] = {"arifOS": arifos_meta("passed", receipt)}
        return d
