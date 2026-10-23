#!/usr/bin/env python3
"""
sync_manifest.py — Single-source projection generator for WEALTH & Federation surfaces.

Reference: ARIFOS::WEALTH_FEDERATION_ALIGNMENT::2026-10-23
Source of truth:
  1. FastMCP runtime introspection via wealth_mcp.server.create_mcp_server()
     (async mcp.list_tools())
  2. /root/WEALTH/tools_sot.yaml (canonical tool descriptions & domain tags)
  3. /root/WEALTH/identity.toml (canonical organ identity & BLAKE3 hash)

Projections synchronized (with --full):
  - /root/WEALTH/fastmcp.json
  - /root/WEALTH/.well-known/mcp.json (+ /var/www/html/wealth/.well-known/mcp.json)
  - /root/WEALTH/.well-known/mcp/server.json
  - /root/WEALTH/.well-known/agent.json (+ /var/www/html/wealth/.well-known/agent.json)
  - /root/AAA/agent-cards/organs/wealth/agent-card.json (+ /var/www/html/wealth/.well-known/agent-card.json)
  - /var/www/html/wealth/llms.txt (+ /root/WEALTH/llms.txt & /root/WEALTH/public/llms.txt)
  - /root/AAA/{public,dist}/a2a/agents.json (+ /var/www/html/aaa/a2a/agents.json)
  - /root/arif-fazil.com/sites/arif-fazil.com/public/.well-known/{arifos-federation.json,capabilities.json,agent-registry.json}
    (+ dist & /var/www/html/arif/ mirrors)

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import tomllib
import warnings
from datetime import datetime, timezone
from pathlib import Path

import yaml

warnings.filterwarnings("ignore", category=DeprecationWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = Path(__file__).resolve().parent / ".manifest_state.json"
SOT_PATH = REPO_ROOT / "tools_sot.yaml"
IDENTITY_PATH = REPO_ROOT / "identity.toml"

WEALTH_WEBROOT = Path("/var/www/html/wealth")
AAA_ROOT = Path("/root/AAA")
AAA_WEBROOT = Path("/var/www/html/aaa")
ARIF_SITE_ROOT = Path("/root/arif-fazil.com/sites/arif-fazil.com")
ARIF_WEBROOT = Path("/var/www/html/arif")

ZERO_TOOLS_ABORT = (
    "SYNC_ABORT: runtime returned 0 tools — possible import failure or FastMCP registration broken"
)


def get_live_tools() -> list[str]:
    """Import the federated WEALTH FastMCP server and return live tool names."""
    sys.path.insert(0, str(REPO_ROOT))
    from wealth_mcp.server import create_mcp_server

    mcp = create_mcp_server()

    async def _list() -> list[str]:
        tools = await mcp.list_tools()
        return [t.name for t in tools]

    return asyncio.run(_list())


def load_sot_tools() -> dict[str, dict]:
    """Load canonical tool metadata from tools_sot.yaml."""
    data = yaml.safe_load(SOT_PATH.read_text(encoding="utf-8"))
    tools_list = data.get("tools", [])
    return {t["name"]: t for t in tools_list if isinstance(t, dict) and "name" in t}


def load_identity() -> dict:
    """Load identity.toml and compute its BLAKE3/SHA256 hash."""
    raw = IDENTITY_PATH.read_bytes()
    parsed = tomllib.loads(raw.decode("utf-8"))
    try:
        import blake3  # type: ignore

        id_hash = blake3.blake3(raw).hexdigest()
    except Exception:
        id_hash = hashlib.sha256(raw).hexdigest()
    parsed["_identity_hash"] = id_hash
    return parsed


def atomic_write_json(path: Path, data: dict, sort_keys: bool = False) -> None:
    """Atomic JSON write: write to temp, fsync, replace (with canon-mutate for +i trees)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(data, tmp, indent=2, sort_keys=sort_keys, ensure_ascii=False)
                tmp.write("\n")
                tmp.flush()
                os.fsync(tmp.fileno())
            os.chmod(tmp_name, 0o644)
            os.replace(tmp_name, path)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
    except PermissionError:
        canon_mutate = Path("/root/scripts/canon-mutate")
        if not canon_mutate.exists():
            raise
        import subprocess

        fd, staged_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(data, tmp, indent=2, sort_keys=sort_keys, ensure_ascii=False)
                tmp.write("\n")
                tmp.flush()
                os.fsync(tmp.fileno())
            os.chmod(staged_tmp, 0o644)
            subprocess.run(
                [
                    str(canon_mutate),
                    "--agent",
                    os.environ.get("ARIFOS_AGENT_ID", "WEALTH-SYNC-MANIFEST"),
                    "--session",
                    os.environ.get("ARIFOS_SESSION_ID", "SEAL-8fa3c44343b14bde"),
                    "--trace",
                    os.environ.get("ARIFOS_TRACE_ID", "trc-ccc96aa29881"),
                    "--allow-no-change",
                    "--expect-target",
                    str(path),
                    "run",
                    str(path.parent),
                    "--",
                    "install",
                    "-m",
                    "0644",
                    staged_tmp,
                    str(path),
                ],
                check=True,
            )
        finally:
            if os.path.exists(staged_tmp):
                os.unlink(staged_tmp)


def short_summary(desc: str) -> str:
    """Extract a clean one-line summary from a multi-line YAML tool description."""
    lines = [ln.strip() for ln in (desc or "").strip().splitlines() if ln.strip()]
    if not lines:
        return "Governed capital intelligence computation tool."
    first = lines[0]
    if len(first) > 140:
        return first[:137] + "..."
    return first


def build_skills_array(live_tools: list[str], sot_map: dict[str, dict], include_modes: bool = True) -> list[dict]:
    """Build A2A skills array directly from live runtime tool names + tools_sot.yaml."""
    skills = []
    for name in live_tools:
        sot = sot_map.get(name, {})
        tags_dict = sot.get("tags", {}) if isinstance(sot.get("tags"), dict) else {}
        domain_tag = tags_dict.get("domain", "capital")
        kind_tag = tags_dict.get("kind", "computational")
        pretty_name = name.replace("_", " ").title().replace("Wealth ", "WEALTH ").replace("Polix", "POLIX").replace("Civx", "CIVX")
        entry: dict = {
            "id": name,
            "name": pretty_name,
            "description": short_summary(sot.get("description", "")),
            "tags": [domain_tag, kind_tag],
        }
        if include_modes:
            entry["inputModes"] = ["application/json"]
            entry["outputModes"] = ["application/json"]
        skills.append(entry)
    return skills


def update_fastmcp_json(tools: list[str], identity: dict) -> None:
    path = REPO_ROOT / "fastmcp.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["capabilities"]["tools"]["count"] = len(tools)
    data["capabilities"]["tools"]["source"] = (
        "scripts/sync_manifest.py (auto-generated from FastMCP runtime mcp.list_tools(); do not hand-edit)"
    )
    data["description"] = (
        f"WEALTH Capital Intelligence — {len(tools)} public tools. Computes, never allocates."
    )
    data["version"] = identity.get("identity", {}).get("version", data.get("version", "2026.10.23"))
    atomic_write_json(path, data, sort_keys=True)


def update_wellknown_mcp(tools: list[str], today: str) -> None:
    path = REPO_ROOT / ".well-known" / "mcp.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["description"] = (
        f"WEALTH is the compute-only capital intelligence organ in the arifOS federation. "
        f"Canonical runtime: server_federated.py → wealth_mcp/server.py. "
        f"The {len(tools)}-tool public surface is discoverable via tools/list and /tools."
    )
    meta = data.setdefault("metadata", {})
    meta["last_updated"] = today
    meta["public_tool_count"] = len(tools)
    meta["canonical_capital_count"] = len(tools)
    meta["institutional_compatibility_count"] = 0
    meta["live_runtime_count"] = len(tools)
    meta["live_runtime_as_of"] = today
    meta["authority_ceiling"] = "555_COMPUTE_ONLY"
    meta["final_authority"] = "ARIF"
    meta["federation"] = "arifOS"
    meta["organ"] = "WEALTH"
    meta["role"] = "Capital Intelligence"
    meta["mcp_endpoint"] = "https://wealth.arif-fazil.com/mcp"
    meta["tools_url"] = "https://wealth.arif-fazil.com/tools"
    meta["markets_registry_url"] = "https://wealth.arif-fazil.com/api/markets/registry"
    meta["federation_identity"] = "https://arif-fazil.com/.well-known/arifos-federation.json"
    surfaces = meta.setdefault("runtime_surfaces", {})
    surfaces["canonical_federated"] = {
        "tools": len(tools),
        "entrypoint": "server_federated.py",
    }
    if "canonical_kernel" in surfaces:
        surfaces["canonical_kernel"]["tools"] = len(tools)
    atomic_write_json(path, data, sort_keys=True)
    if WEALTH_WEBROOT.is_dir():
        atomic_write_json(WEALTH_WEBROOT / ".well-known" / "mcp.json", data, sort_keys=True)

    # Also update .well-known/mcp/server.json
    srv_path = REPO_ROOT / ".well-known" / "mcp" / "server.json"
    if srv_path.exists():
        srv = json.loads(srv_path.read_text(encoding="utf-8"))
        srv["description"] = f"Capital intelligence — {len(tools)}-tool compute-only federation surface."
        srv["tools"] = len(tools)
        srv["tools_url"] = "https://wealth.arif-fazil.com/tools"
        srv["markets_registry_url"] = "https://wealth.arif-fazil.com/api/markets/registry"
        srv["federation_identity"] = "https://arif-fazil.com/.well-known/arifos-federation.json"
        srv.setdefault("identity", {})["authority"] = "555_COMPUTE_ONLY"
        srv["identity"]["final_authority"] = "ARIF"
        srv["identity"]["federation"] = "arifOS"
        srv["identity"]["organ"] = "WEALTH"
        srv["identity"]["role"] = "Capital Intelligence"
        srv.setdefault("governance", {})["authority_boundary"] = "555_COMPUTE_ONLY"
        srv["governance"]["final_authority"] = "ARIF"
        atomic_write_json(srv_path, srv)


def update_organ_agent_json(tools: list[str], sot_map: dict[str, dict], identity: dict, today: str) -> None:
    """Update /root/WEALTH/.well-known/agent.json and /var/www/html/wealth/.well-known/agent.json."""
    path = REPO_ROOT / ".well-known" / "agent.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["federation"] = "arifOS"
    data["organ"] = "WEALTH"
    data["role"] = "Capital Intelligence"
    data["authority_ceiling"] = "555_COMPUTE_ONLY"
    data["final_authority"] = "ARIF"
    data["mcp_endpoint"] = "https://wealth.arif-fazil.com/mcp"
    data["tools_url"] = "https://wealth.arif-fazil.com/tools"
    data["markets_registry_url"] = "https://wealth.arif-fazil.com/api/markets/registry"
    data["federation_identity"] = "https://arif-fazil.com/.well-known/arifos-federation.json"
    data["identity_hash"] = identity["_identity_hash"]
    data["owned_mcp_count"] = len(tools)
    data["skills"] = build_skills_array(tools, sot_map, include_modes=False)
    a2a_ep = data.setdefault("a2a_endpoints", {})
    a2a_ep["health"] = "https://wealth.arif-fazil.com/health"
    a2a_ep["tools"] = "https://wealth.arif-fazil.com/tools"
    a2a_ep["mcp"] = "https://wealth.arif-fazil.com/mcp"
    a2a_ep["markets_registry"] = "https://wealth.arif-fazil.com/api/markets/registry"
    a2a_ep["agent_card"] = "https://wealth.arif-fazil.com/.well-known/agent-card.json"
    a2a_ep["agent_card_internal"] = "https://wealth.arif-fazil.com/.well-known/agent.json"
    meta = data.setdefault("metadata", {})
    meta["generated_at"] = today
    meta["generator"] = "scripts/sync_manifest.py"
    meta["notes"] = (
        f"This card is the organ public agent card. Synchronized from runtime mcp.list_tools() "
        f"and tools_sot.yaml ({len(tools)} public tools) with public_domain = https://wealth.arif-fazil.com."
    )
    atomic_write_json(path, data)
    if WEALTH_WEBROOT.is_dir():
        atomic_write_json(WEALTH_WEBROOT / ".well-known" / "agent.json", data)


def update_consolidated_agent_card(tools: list[str], sot_map: dict[str, dict], identity: dict, now_iso: str) -> None:
    """Update /root/AAA/agent-cards/organs/wealth/agent-card.json and /var/www/html/wealth/.well-known/agent-card.json."""
    aaa_card_path = AAA_ROOT / "agent-cards" / "organs" / "wealth" / "agent-card.json"
    web_card_path = WEALTH_WEBROOT / ".well-known" / "agent-card.json"
    source_path = aaa_card_path if aaa_card_path.exists() else web_card_path
    if not source_path.exists():
        return
    card = json.loads(source_path.read_text(encoding="utf-8"))
    card["federation"] = "arifOS"
    card["organ"] = "WEALTH"
    card["role"] = "Capital Intelligence"
    card["authority_ceiling"] = "555_COMPUTE_ONLY"
    card["final_authority"] = "ARIF"
    card["identity_hash"] = identity["_identity_hash"]
    card["mcp_endpoint"] = "https://wealth.arif-fazil.com/mcp"
    card["tools_url"] = "https://wealth.arif-fazil.com/tools"
    card["health_url"] = "https://wealth.arif-fazil.com/health"
    card["markets_registry_url"] = "https://wealth.arif-fazil.com/api/markets/registry"
    card["federation_identity"] = "https://arif-fazil.com/.well-known/arifos-federation.json"
    card["world_state_url"] = "https://arif-fazil.com/world-state.json"
    card["description"] = (
        f"Capital intelligence organ of the arifOS federation — deductive capital math (NPV/IRR/EMV), "
        f"institutional diagnostics, market signals, and sovereign pulse compute ({len(tools)} MCP tools). "
        f"555_COMPUTE_ONLY: computes and witnesses capital reality; never allocates capital or issues SEAL."
    )
    if "principal_agent" in card and isinstance(card["principal_agent"], dict):
        card["principal_agent"]["category"] = "Capital Intelligence — 555_COMPUTE_ONLY, compute never allocate"
    if "warga_binding" in card and isinstance(card["warga_binding"], dict):
        card["warga_binding"]["authority_level"] = "555_COMPUTE_ONLY"
    if "governance_profile" in card and isinstance(card["governance_profile"], dict):
        card["governance_profile"]["authority_ceiling"] = "555_COMPUTE_ONLY"
        card["governance_profile"]["final_authority"] = "ARIF"
    card["skills"] = build_skills_array(tools, sot_map, include_modes=True)
    card["registry_snapshot_at"] = now_iso
    card["registry_source"] = ["mcp.list_tools", "tools_sot.yaml", "identity.toml"]
    card["registry_tool_count"] = {
        "source": len(tools),
        "registry": len(tools),
        "card": len(tools),
    }
    if aaa_card_path.parent.is_dir():
        atomic_write_json(aaa_card_path, card)
    if WEALTH_WEBROOT.is_dir():
        atomic_write_json(web_card_path, card)


def sync_llms_txt(tools: list[str]) -> None:
    """Keep /var/www/html/wealth/llms.txt, /root/WEALTH/llms.txt, and /root/WEALTH/public/llms.txt aligned."""
    live_llms = WEALTH_WEBROOT / "llms.txt"
    if not live_llms.exists():
        return
    text = live_llms.read_text(encoding="utf-8")
    # Ensure authority_ceiling and final_authority and /tools are explicitly stated
    text = re.sub(
        r"Authority ceiling:\s*\*\*[A-Z0-9_]+\*\*",
        "Authority ceiling: **555_COMPUTE_ONLY** · Final authority: **ARIF**",
        text,
    )
    text = re.sub(
        r"\*\*Tools:\*\*\s*\d+\s*public",
        f"**Tools:** {len(tools)} public",
        text,
    )
    text = re.sub(
        r"## Public MCP Tools \(\d+\)",
        f"## Public MCP Tools ({len(tools)})",
        text,
    )
    if "| `/tools` |" not in text and "| `/health` |" in text:
        text = text.replace(
            "| `/health` | Runtime health + tool count |\n",
            "| `/health` | Runtime health + tool count |\n"
            "| `/tools` | Canonical runtime tool list (`mcp.list_tools`) |\n"
            "| `/.well-known/arifos-federation.json` | Federation identity manifest (`https://arif-fazil.com/.well-known/arifos-federation.json`) |\n",
        )
    live_llms.write_text(text, encoding="utf-8")
    (REPO_ROOT / "llms.txt").write_text(text, encoding="utf-8")
    if (REPO_ROOT / "public").is_dir():
        (REPO_ROOT / "public" / "llms.txt").write_text(text, encoding="utf-8")


def sync_aaa_agents_json(tools: list[str]) -> None:
    """Synchronize AAA public/dist/live a2a/agents.json organ projections."""
    targets = [
        AAA_ROOT / "public" / "a2a" / "agents.json",
        AAA_ROOT / "dist" / "a2a" / "agents.json",
        AAA_WEBROOT / "a2a" / "agents.json",
    ]
    existing = [p for p in targets if p.exists()]
    if not existing:
        return
    data = json.loads(existing[0].read_text(encoding="utf-8"))
    organ_updates = {
        "wealth": {
            "description": (
                f"Capital intelligence organ — deductive math (NPV/IRR/EMV), institutional diagnostics, "
                f"markets, sovereign pulse compute. {len(tools)} MCP tools. 555_COMPUTE_ONLY."
            ),
            "version": "2026.10.23",
            "protocolVersion": "1.0",
            "endpoint": "https://wealth.arif-fazil.com/mcp",
            "tools_url": "https://wealth.arif-fazil.com/tools",
            "health_url": "https://wealth.arif-fazil.com/health",
            "markets_registry_url": "https://wealth.arif-fazil.com/api/markets/registry",
            "agent_card_url": "https://wealth.arif-fazil.com/.well-known/agent-card.json",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
            "tools_count": len(tools),
        },
        "geox": {
            "protocolVersion": "1.0",
            "endpoint": "https://geox.arif-fazil.com/mcp",
            "health_url": "https://geox.arif-fazil.com/health",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
        },
        "well": {
            "protocolVersion": "1.0",
            "endpoint": "https://well.arif-fazil.com/mcp",
            "health_url": "https://well.arif-fazil.com/health",
            "authority_ceiling": "REFLECT_ONLY",
            "final_authority": "ARIF",
        },
        "arifos": {
            "protocolVersion": "1.0",
            "endpoint": "https://arifos.arif-fazil.com/mcp",
            "health_url": "https://arifos.arif-fazil.com/health",
            "authority_ceiling": "JUDGE_ONLY",
            "final_authority": "ARIF",
        },
        "a-forge-mcp": {
            "protocolVersion": "1.0",
            "endpoint": "https://mcp.arif-fazil.com/mcp",
            "health_url": "https://mcp.arif-fazil.com/health",
            "authority_ceiling": "EXECUTE_AFTER_SEAL",
            "final_authority": "ARIF",
        },
        "aaa-gateway": {
            "protocolVersion": "1.0",
            "endpoint": "https://aaa.arif-fazil.com/a2a",
            "health_url": "https://aaa.arif-fazil.com/health",
            "authority_ceiling": "DISPLAY_ONLY",
            "final_authority": "ARIF",
        },
    }
    for agent in data.get("agents", []):
        aid = agent.get("id")
        if aid in organ_updates:
            agent.update(organ_updates[aid])
    for p in existing:
        atomic_write_json(p, data)


def sync_arif_fazil_projections(tools: list[str], sot_map: dict[str, dict], identity: dict, now_iso: str, today: str) -> None:
    """Synchronize arif-fazil.com federation identity, capabilities, and agent-registry projections."""
    # 1. arifos-federation.json
    fed_paths = [
        ARIF_SITE_ROOT / "public" / ".well-known" / "arifos-federation.json",
        ARIF_SITE_ROOT / "public" / "_shared" / "arifos-federation.json",
        ARIF_SITE_ROOT / "dist" / ".well-known" / "arifos-federation.json",
        ARIF_SITE_ROOT / "dist" / "_shared" / "arifos-federation.json",
        Path("/root/arif-fazil.com/sites/shared/arifos-federation.json"),
        ARIF_WEBROOT / ".well-known" / "arifos-federation.json",
        ARIF_WEBROOT / "_shared" / "arifos-federation.json",
        Path("/var/www/html/.well-known/arifos-federation.json"),
    ]
    existing_fed = [p for p in fed_paths if p.exists()]
    if existing_fed:
        fed = json.loads(existing_fed[0].read_text(encoding="utf-8"))
        fed["version"] = "2.0.0"
        fed["as_of"] = today
        fed["final_authority"] = "ARIF"
        fed["sovereign"] = "Muhammad Arif bin Fazil (F13 SOVEREIGN)"
        fed["canonical_url"] = "https://arif-fazil.com/.well-known/arifos-federation.json"
        fed["compatibility_alias"] = "https://arif-fazil.com/federation/identity.json"
        domains = fed.setdefault("domains", {})
        domains["arifOS"] = {
            "url": "https://arifos.arif-fazil.com",
            "mcp_endpoint": "https://arifos.arif-fazil.com/mcp",
            "health_url": "https://arifos.arif-fazil.com/health",
            "role": "Constitutional governance kernel",
            "authority_ceiling": "JUDGE_ONLY",
            "final_authority": "ARIF",
            "protocol": "MCP",
            "status": "active",
        }
        domains["AAA"] = {
            "url": "https://aaa.arif-fazil.com",
            "a2a_endpoint": "https://aaa.arif-fazil.com/a2a",
            "agents_registry": "https://aaa.arif-fazil.com/a2a/agents.json",
            "health_url": "https://aaa.arif-fazil.com/health",
            "role": "Control plane, A2A coordination, and agent directory",
            "authority_ceiling": "DISPLAY_ONLY",
            "final_authority": "ARIF",
            "protocol": "A2A v1.0.0",
            "status": "active",
        }
        domains["A-FORGE"] = {
            "url": "https://mcp.arif-fazil.com",
            "mcp_endpoint": "https://mcp.arif-fazil.com/mcp",
            "health_url": "https://mcp.arif-fazil.com/health",
            "role": "Governed engineering execution shell",
            "authority_ceiling": "EXECUTE_AFTER_SEAL",
            "final_authority": "ARIF",
            "protocol": "MCP",
            "status": "active",
        }
        domains["GEOX"] = {
            "url": "https://geox.arif-fazil.com",
            "mcp_endpoint": "https://geox.arif-fazil.com/mcp",
            "health_url": "https://geox.arif-fazil.com/health",
            "human_surface": "https://arif-fazil.com/earth/",
            "role": "Earth and geoscience intelligence",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
            "protocol": "MCP",
            "status": "active",
        }
        domains["WEALTH"] = {
            "organ": "WEALTH",
            "federation": "arifOS",
            "url": "https://wealth.arif-fazil.com",
            "mcp_endpoint": "https://wealth.arif-fazil.com/mcp",
            "tools_url": "https://wealth.arif-fazil.com/tools",
            "health_url": "https://wealth.arif-fazil.com/health",
            "markets_registry_url": "https://wealth.arif-fazil.com/api/markets/registry",
            "markets_hub_url": "https://wealth.arif-fazil.com/markets/",
            "agent_card": "https://wealth.arif-fazil.com/.well-known/agent-card.json",
            "llms_txt": "https://wealth.arif-fazil.com/llms.txt",
            "human_surface": "https://arif-fazil.com/economics/",
            "vitals_surface": "https://arif-fazil.com/vitals/",
            "world_state_url": "https://arif-fazil.com/world-state.json",
            "role": "Capital Intelligence",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
            "identity_hash": identity["_identity_hash"],
            "tools_count": len(tools),
            "protocol": "MCP",
            "status": "active",
            "note": "Computes and witnesses capital reality. Never judges, allocates capital, or issues sovereign SEAL.",
        }
        domains["WELL"] = {
            "url": "https://well.arif-fazil.com",
            "mcp_endpoint": "https://well.arif-fazil.com/mcp",
            "health_url": "https://well.arif-fazil.com/health",
            "role": "Human readiness and vitality guard",
            "authority_ceiling": "REFLECT_ONLY",
            "final_authority": "ARIF",
            "protocol": "MCP",
            "status": "active",
        }
        domains["CHRON"] = {
            "url": "https://chron.arif-fazil.com",
            "mcp_endpoint": "https://chron.arif-fazil.com/mcp",
            "role": "Temporal consequence and calibration tracker",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
            "protocol": "MCP",
            "status": "active",
        }
        fed["reality_loop"] = {
            "chain": "WORLD (Observe) -> WEALTH/GEOX/WELL (Compute & Sense) -> AAA (Coordinate) -> arifOS (Judge) -> ARIF (Decide)",
            "world_state": "https://arif-fazil.com/world-state.json",
            "markets_registry": "https://wealth.arif-fazil.com/api/markets/registry",
            "capabilities_manifest": "https://arif-fazil.com/.well-known/capabilities.json",
            "agent_registry": "https://arif-fazil.com/.well-known/agent-registry.json",
        }
        for p in existing_fed:
            atomic_write_json(p, fed)
        for alias_p in [
            ARIF_SITE_ROOT / "public" / "federation" / "identity.json",
            ARIF_WEBROOT / "federation" / "identity.json",
        ]:
            atomic_write_json(alias_p, fed)

    # 2. capabilities.json
    cap_paths = [
        ARIF_SITE_ROOT / "public" / ".well-known" / "capabilities.json",
        ARIF_SITE_ROOT / "dist" / ".well-known" / "capabilities.json",
        ARIF_WEBROOT / ".well-known" / "capabilities.json",
        Path("/var/www/html/.well-known/capabilities.json"),
    ]
    existing_cap = [p for p in cap_paths if p.exists()]
    if existing_cap:
        cap = json.loads(existing_cap[0].read_text(encoding="utf-8"))
        cap["version"] = "2.0.0"
        cap["generated_at"] = now_iso
        cap["generator"] = "WEALTH scripts/sync_manifest.py (from runtime mcp.list_tools)"
        cap["canonical_url"] = "https://arif-fazil.com/.well-known/capabilities.json"
        cap["compatibility_alias"] = "https://arif-fazil.com/capabilities.json"
        surfaces = cap.setdefault("surfaces", {})
        wealth_caps = [
            {
                "name": t,
                "description": short_summary(sot_map.get(t, {}).get("description", "")),
                "protocol": "mcp",
                "tool": t,
                "path": "https://wealth.arif-fazil.com/mcp",
            }
            for t in tools
        ]
        wealth_caps.extend(
            [
                {
                    "name": "wealth_tools_list",
                    "description": f"Live runtime tool list ({len(tools)} tools) via FastMCP introspection",
                    "protocol": "http",
                    "path": "https://wealth.arif-fazil.com/tools",
                },
                {
                    "name": "wealth_markets_registry",
                    "description": "Paired WORLD <-> WEALTH market observation registry with freshness states",
                    "protocol": "http",
                    "path": "https://wealth.arif-fazil.com/api/markets/registry",
                },
                {
                    "name": "wealth_health",
                    "description": "WEALTH organ health, BLAKE3 identity hash, and live tool count",
                    "protocol": "http",
                    "path": "https://wealth.arif-fazil.com/health",
                },
            ]
        )
        surfaces["wealth.arif-fazil.com"] = {
            "ring": "CAPITAL",
            "organ": "WEALTH",
            "federation": "arifOS",
            "role": "Capital Intelligence — NPV, risk, conservation, markets, institutional diagnostics",
            "authority_ceiling": "555_COMPUTE_ONLY",
            "final_authority": "ARIF",
            "mcp_endpoint": "https://wealth.arif-fazil.com/mcp",
            "tools_url": "https://wealth.arif-fazil.com/tools",
            "markets_registry_url": "https://wealth.arif-fazil.com/api/markets/registry",
            "agent_card": "https://wealth.arif-fazil.com/.well-known/agent-card.json",
            "tools_count": len(tools),
            "capabilities": wealth_caps,
        }
        # Clean stale /wealth/gold/api/* paths on arif-fazil.com surface entry
        if "arif-fazil.com" in surfaces:
            af_caps = surfaces["arif-fazil.com"].get("capabilities", [])
            path_fixes = {
                "/wealth/api/overview": "https://wealth.arif-fazil.com/api/markets/registry",
                "/wealth/api/ticker": "https://wealth.arif-fazil.com/api/markets/registry",
                "/wealth/api/briefing": "https://wealth.arif-fazil.com/api/wealth/briefing",
                "/wealth/gold/api/gold/ticker": "https://wealth.arif-fazil.com/gold/api/snapshot",
                "/wealth/gold/api/gold/history": "https://wealth.arif-fazil.com/gold/api/snapshot",
                "/wealth/gold/api/gold/signals": "https://wealth.arif-fazil.com/gold/api/snapshot",
                "/wealth/gold/api/gold/levels": "https://wealth.arif-fazil.com/gold/api/snapshot",
                "/wealth/gold/api/gold/macro": "https://wealth.arif-fazil.com/gold/api/snapshot",
                "/makcikgpt/": "https://arif-fazil.com/world/makcikgpt/",
                "/geox/": "https://arif-fazil.com/earth/",
            }
            for c in af_caps:
                if c.get("path") in path_fixes:
                    c["path"] = path_fixes[c["path"]]
        for p in existing_cap:
            atomic_write_json(p, cap)
        for alias_p in [
            ARIF_SITE_ROOT / "public" / "capabilities.json",
            ARIF_WEBROOT / "capabilities.json",
            Path("/var/www/html/capabilities.json"),
        ]:
            atomic_write_json(alias_p, cap)

    # 3. agent-registry.json
    reg_paths = [
        ARIF_SITE_ROOT / "public" / ".well-known" / "agent-registry.json",
        ARIF_SITE_ROOT / "dist" / ".well-known" / "agent-registry.json",
        ARIF_WEBROOT / ".well-known" / "agent-registry.json",
        Path("/var/www/html/.well-known/agent-registry.json"),
    ]
    existing_reg = [p for p in reg_paths if p.exists()]
    if existing_reg:
        reg = json.loads(existing_reg[0].read_text(encoding="utf-8"))
        reg["as_of"] = today
        for entry in reg.get("entries", []):
            if entry.get("id") == "organ:wealth":
                entry["access_scope"] = "555_COMPUTE_ONLY"
                entry["authority_ceiling"] = "555_COMPUTE_ONLY"
                entry["final_authority"] = "ARIF"
                entry["mcp_endpoint"] = "https://wealth.arif-fazil.com/mcp"
                entry["tools_url"] = "https://wealth.arif-fazil.com/tools"
                entry["markets_registry"] = "https://wealth.arif-fazil.com/api/markets/registry"
                entry["agent_card"] = "https://wealth.arif-fazil.com/.well-known/agent-card.json"
                entry["public_tools"] = tools
                entry["tools_count"] = len(tools)
            elif entry.get("id") == "organ:aaa":
                entry["a2a_endpoint"] = "https://aaa.arif-fazil.com/a2a"
                entry["agents_directory"] = "https://aaa.arif-fazil.com/a2a/agents.json"
        for p in existing_reg:
            atomic_write_json(p, reg)


def load_snapshot() -> set[str]:
    if SNAPSHOT_PATH.exists():
        try:
            data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return set()


def save_snapshot(tools: list[str]) -> None:
    SNAPSHOT_PATH.write_text(json.dumps(sorted(tools), indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync WEALTH & federation projections from FastMCP runtime introspection."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Synchronize all WEALTH, AAA, and arif-fazil.com discovery projections",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute diff and verify SOT parity without writing files",
    )
    args = parser.parse_args()

    live_tools = get_live_tools()
    if not live_tools:
        print(ZERO_TOOLS_ABORT, file=sys.stderr)
        return 1

    sot_map = load_sot_tools()
    if set(live_tools) != set(sot_map.keys()):
        missing_in_sot = sorted(set(live_tools) - set(sot_map.keys()))
        extra_in_sot = sorted(set(sot_map.keys()) - set(live_tools))
        print(
            f"SYNC_ABORT: runtime tools ({len(live_tools)}) != tools_sot.yaml ({len(sot_map)})\n"
            f"  missing in SOT: {missing_in_sot}\n  extra in SOT: {extra_in_sot}",
            file=sys.stderr,
        )
        return 2

    identity = load_identity()
    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now_dt.strftime("%Y-%m-%d")

    old = load_snapshot()
    added = sorted(set(live_tools) - old)
    removed = sorted(old - set(live_tools))
    print(f"Live runtime tools: {len(live_tools)} (verified 100% parity with tools_sot.yaml)")
    if added:
        print(f"  + added ({len(added)}): {', '.join(added)}")
    if removed:
        print(f"  - removed ({len(removed)}): {', '.join(removed)}")

    if args.dry_run:
        print("DRY RUN — no files written")
        return 0

    update_fastmcp_json(live_tools, identity)
    print(f"  → fastmcp.json: count = {len(live_tools)}")

    if args.full:
        update_wellknown_mcp(live_tools, today)
        print(f"  → .well-known/mcp.json + mcp/server.json: count = {len(live_tools)}")
        update_organ_agent_json(live_tools, sot_map, identity, today)
        print(f"  → .well-known/agent.json: count = {len(live_tools)}")
        update_consolidated_agent_card(live_tools, sot_map, identity, now_iso)
        print(f"  → .well-known/agent-card.json (AAA + WEALTH webroot): count = {len(live_tools)}")
        sync_llms_txt(live_tools)
        print(f"  → llms.txt (WEALTH webroot + repo): count = {len(live_tools)}")
        sync_aaa_agents_json(live_tools)
        print(f"  → AAA a2a/agents.json (source + dist + webroot): count = {len(live_tools)}")
        sync_arif_fazil_projections(live_tools, sot_map, identity, now_iso, today)
        print(f"  → arif-fazil.com (.well-known/arifos-federation.json, capabilities.json, agent-registry.json): synced")

    save_snapshot(live_tools)
    return 0


if __name__ == "__main__":
    sys.exit(main())
