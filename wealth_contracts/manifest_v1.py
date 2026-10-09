"""
Five-Manifest Registry v1.

Separates what source DECLARES from what the actual serving process
can PROVE. Public health status for a tool derives from probe state,
not from source declaration.

  source_manifest   — what committed source declares
  build_manifest    — what was packaged into this artifact
  runtime_manifest  — what the active process registered
  public_manifest   — what an MCP client can discover (live)
  probe_manifest    — what independently passed cold-import, safe
                      invocation, schema validation, semantic
                      invariants, and failure injection

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EffectiveState(str, Enum):
    DECLARED = "DECLARED"
    IMPORTABLE = "IMPORTABLE"
    INVOKABLE = "INVOKABLE"
    VALIDATED = "VALIDATED"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    HELD = "HELD"
    UNAVAILABLE = "UNAVAILABLE"
    DEAD = "DEAD"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Source manifest ──────────────────────────────────────────────────


@dataclass
class SourceManifest:
    git_revision: str
    canonical_tool_list: list[str]
    deprecations: list[str]
    source_manifest_hash: str
    generated_at: str

    @classmethod
    def from_git(cls, tool_paths: list[str]) -> "SourceManifest":
        try:
            rev = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
        except Exception:  # noqa: BLE001
            rev = "UNKNOWN"
        canonical = sorted({t for t in tool_paths if t})
        manifest_text = f"{rev}\n" + "\n".join(canonical)
        return cls(
            git_revision=rev,
            canonical_tool_list=canonical,
            deprecations=[],
            source_manifest_hash=_sha256(manifest_text),
            generated_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "git_revision": self.git_revision,
            "canonical_tool_list": self.canonical_tool_list,
            "deprecations": self.deprecations,
            "source_manifest_hash": self.source_manifest_hash,
            "generated_at": self.generated_at,
        }


# ── Build manifest ───────────────────────────────────────────────────


@dataclass
class BuildManifest:
    build_digest: str
    revision: str
    dependency_lock_digest: str
    artifact_creation_time: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_digest": self.build_digest,
            "revision": self.revision,
            "dependency_lock_digest": self.dependency_lock_digest,
            "artifact_creation_time": self.artifact_creation_time,
        }


# ── Runtime manifest ─────────────────────────────────────────────────


@dataclass
class RuntimeManifest:
    instance_id: str
    process_start_time: str
    registered_tools: list[str]
    registered_resources: list[str]
    registered_prompts: list[str]
    runtime_manifest_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "process_start_time": self.process_start_time,
            "registered_tools": self.registered_tools,
            "registered_resources": self.registered_resources,
            "registered_prompts": self.registered_prompts,
            "runtime_manifest_hash": self.runtime_manifest_hash,
        }


# ── Public manifest ──────────────────────────────────────────────────


@dataclass
class PublicManifest:
    view: str
    included_count: int
    excluded_count: int
    exclusion_reason: str
    public_tools: list[str]
    public_resources: list[str]
    public_prompts: list[str]
    manifest_hashes: dict[str, str]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "view": self.view,
            "included_count": self.included_count,
            "excluded_count": self.excluded_count,
            "exclusion_reason": self.exclusion_reason,
            "public_tools": self.public_tools,
            "public_resources": self.public_resources,
            "public_prompts": self.public_prompts,
            "manifest_hashes": self.manifest_hashes,
            "generated_at": self.generated_at,
        }


# ── Probe manifest ───────────────────────────────────────────────────


@dataclass
class ProbeOutcome:
    capability: str
    probe_state: EffectiveState
    import_pass: bool = False
    invocation_pass: bool = False
    schema_pass: bool = False
    semantic_pass: bool = False
    failure_injection_pass: bool = False
    receipt_ref: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "probe_state": self.probe_state.value,
            "import_pass": self.import_pass,
            "invocation_pass": self.invocation_pass,
            "schema_pass": self.schema_pass,
            "semantic_pass": self.semantic_pass,
            "failure_injection_pass": self.failure_injection_pass,
            "receipt_ref": self.receipt_ref,
            "detail": self.detail,
        }


@dataclass
class ProbeManifest:
    outcomes: list[ProbeOutcome]
    generated_at: str
    probe_manifest_hash: str

    def public_status_for(self, capability: str) -> EffectiveState:
        """Effective state is the LOWEST verified state, never the best.

        A declared tool that fails import is DEAD, not healthy.
        A live tool with stale evidence is DEGRADED, not LIVE.
        """
        for o in self.outcomes:
            if o.capability == capability:
                return o.probe_state
        return EffectiveState.DECLARED

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcomes": [o.to_dict() for o in self.outcomes],
            "generated_at": self.generated_at,
            "probe_manifest_hash": self.probe_manifest_hash,
        }


def aggregate_probe_state(outcomes: list[ProbeOutcome]) -> dict[str, EffectiveState]:
    """Aggregate the worst-state-per-capability view.

    Use this for the public health surface.
    """
    worst: dict[str, EffectiveState] = {}
    rank = {
        EffectiveState.DEAD: 0,
        EffectiveState.UNAVAILABLE: 1,
        EffectiveState.DECLARED: 2,
        EffectiveState.IMPORTABLE: 3,
        EffectiveState.INVOKABLE: 4,
        EffectiveState.DEGRADED: 5,
        EffectiveState.HELD: 6,
        EffectiveState.VALIDATED: 7,
        EffectiveState.LIVE: 8,
    }
    for o in outcomes:
        prev = worst.get(o.capability)
        if prev is None or rank[o.probe_state] < rank[prev]:
            worst[o.capability] = o.probe_state
    return worst


__all__ = [
    "EffectiveState",
    "SourceManifest",
    "BuildManifest",
    "RuntimeManifest",
    "PublicManifest",
    "ProbeOutcome",
    "ProbeManifest",
    "aggregate_probe_state",
]