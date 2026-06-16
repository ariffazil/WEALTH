"""
WEALTH Tool Manifest — Per-tool capability manifest (mirror of arifOS arifos_registry).

F2 TRUTH: Every WEALTH tool must be registered with full provenance.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WealthToolManifest:
    """Capability manifest for a WEALTH tool."""

    tool_name: str
    lane: str  # wealth_calculate | wealth_audit
    action_class: str  # OBSERVE | ANALYZE | MUTATE | GOVERNED
    schema_hash: str
    source_path: str
    source_repository: str = "https://github.com/ariffazil/wealth"
    license: str = "AGPL-3.0"
    blast_radius: str = "LOW"  # LOW | MEDIUM | HIGH
    reversible: bool = True
    secret_touching: bool = False
    network_access: bool = True
    filesystem_access: bool = False
    human_approval_policy: str = "SABAR"  # NONE | SABAR | ALWAYS
    description: str = ""
    signed: bool = False
    signature: Optional[str] = None
    last_reviewed: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "lane": self.lane,
            "action_class": self.action_class,
            "schema_hash": self.schema_hash,
            "source_path": self.source_path,
            "source_repository": self.source_repository,
            "license": self.license,
            "blast_radius": self.blast_radius,
            "reversible": self.reversible,
            "secret_touching": self.secret_touching,
            "network_access": self.network_access,
            "filesystem_access": self.filesystem_access,
            "human_approval_policy": self.human_approval_policy,
            "description": self.description,
            "signed": self.signed,
            "signature": self.signature,
            "last_reviewed": self.last_reviewed,
        }


def build_manifest(
    tool_name: str,
    source_path: str,
    lane: str,
    action_class: str,
    description: str,
) -> WealthToolManifest:
    """Build a tool manifest from source code (computes hash)."""
    import os
    schema_hash = "b3:missing"
    if os.path.exists(source_path):
        with open(source_path, "rb") as f:
            import blake3
            schema_hash = "b3:" + blake3.blake3(f.read()).hexdigest()

    return WealthToolManifest(
        tool_name=tool_name,
        lane=lane,
        action_class=action_class,
        schema_hash=schema_hash,
        source_path=source_path,
        description=description,
    )
