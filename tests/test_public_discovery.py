"""
tests/test_public_discovery.py — organ-owned public discovery/data source parity.

Verifies the four properties the slice was approved to repair:

  1. public/sitemap.xml advertises ONLY real live routes on wealth.arif-fazil.com.
  2. public/robots.txt matches the sitemap's domain and Sitemap: pointer.
  3. .well-known/agent.json is the canonical public agent card, with no
     confusion with the makcikgpt DRAFT_ONLY persona.
  4. Commodity routes (oil/gas/gold/wealth) advertised by the sitemap exist
     on disk under site/dist/, and are declared in contracts/tools.yaml and
     contracts/mcp_surface.yaml.

Run with the rest of the WEALTH test suite:
    PYTHONPATH=. pytest tests/test_public_discovery.py -q --tb=short
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO / "public"
SITEMAP = PUBLIC / "sitemap.xml"
ROBOTS = PUBLIC / "robots.txt"
AGENT_CARD = REPO / ".well-known" / "agent.json"
MCP_MANIFEST = REPO / ".well-known" / "mcp.json"
TOOLS_YAML = REPO / "contracts" / "tools.yaml"
MCP_SURFACE_YAML = REPO / "contracts" / "mcp_surface.yaml"
SITE_DIST = REPO / "site" / "dist"
DRAFT_PERSONA_CARD = REPO / "agent-cards" / "makcikgpt.json"

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ORGAN_DOMAIN = "wealth.arif-fazil.com"


# ── 1. sitemap.xml ────────────────────────────────────────────────────────


def _sitemap_urls() -> list[str]:
    tree = ET.parse(SITEMAP)
    return [el.text.strip() for el in tree.findall(".//sm:loc", SITEMAP_NS) if el.text]


def test_sitemap_exists_and_is_valid_xml():
    assert SITEMAP.exists(), f"missing {SITEMAP}"
    # Will raise ParseError if malformed.
    ET.parse(SITEMAP)


def test_sitemap_advertises_only_organ_domain():
    urls = _sitemap_urls()
    assert urls, "sitemap must contain at least one URL"
    for url in urls:
        assert url.startswith(f"https://{ORGAN_DOMAIN}/"), (
            f"sitemap advertises non-organ URL: {url}"
        )


def test_sitemap_excludes_makcikgpt_draft_persona():
    urls = _sitemap_urls()
    assert not any("makcikgpt" in u for u in urls), (
        "sitemap leaks the makcikgpt DRAFT_ONLY persona: "
        + ", ".join(u for u in urls if "makcikgpt" in u)
    )


def test_sitemap_includes_commodity_terminal_routes():
    urls = _sitemap_urls()
    required = [
        f"https://{ORGAN_DOMAIN}/wealth/",
        f"https://{ORGAN_DOMAIN}/wealth/gold/",
        f"https://{ORGAN_DOMAIN}/wealth/oil/",
        f"https://{ORGAN_DOMAIN}/wealth/gas/",
        f"https://{ORGAN_DOMAIN}/wealth/llms.txt",
        f"https://{ORGAN_DOMAIN}/llms.txt",
        f"https://{ORGAN_DOMAIN}/.well-known/agent.json",
        f"https://{ORGAN_DOMAIN}/.well-known/mcp.json",
    ]
    missing = [r for r in required if r not in urls]
    assert not missing, f"sitemap is missing required routes: {missing}"


def test_sitemap_commodity_dist_files_exist():
    """Every commodity route advertised by the sitemap must have a real file.

    The terminal routes under ``/wealth/...`` are rendered into
    ``site/dist/{asset}/index.html`` (asset ∈ {gold, oil, gas, wealth})
    by site/build.py — so the on-disk file is ``site/dist/<asset>/index.html``,
    NOT ``site/dist/wealth/<asset>/index.html``.
    """
    urls = _sitemap_urls()
    dist_assets = {"gold", "oil", "gas", "wealth"}
    for url in urls:
        if not url.startswith(f"https://{ORGAN_DOMAIN}/"):
            continue
        path = url[len(f"https://{ORGAN_DOMAIN}") :]
        # Match /wealth/<asset>/ (or /wealth/llms.txt etc.).
        m = re.match(r"^/wealth/(?P<asset>[a-z]+)/?$", path)
        if not m:
            continue
        asset = m.group("asset")
        if asset not in dist_assets:
            continue
        candidate = SITE_DIST / asset / "index.html"
        assert candidate.exists() and candidate.stat().st_size > 0, (
            f"terminal route {path} has no dist file at {candidate}"
        )


# ── 2. robots.txt ─────────────────────────────────────────────────────────


def test_robots_targets_organ_domain():
    text = ROBOTS.read_text()
    assert ORGAN_DOMAIN in text, f"robots.txt does not mention {ORGAN_DOMAIN}"
    # Sitemap pointer matches organ.
    m = re.search(r"^Sitemap:\s*(\S+)", text, re.MULTILINE)
    assert m, "robots.txt has no Sitemap: directive"
    assert m.group(1) == f"https://{ORGAN_DOMAIN}/sitemap.xml", (
        f"robots.txt Sitemap points at {m.group(1)}, expected "
        f"https://{ORGAN_DOMAIN}/sitemap.xml"
    )


def test_robots_does_not_advertise_makcikgpt_route():
    """robots.txt must not Allow or Sitemap any makcikgpt route.

    The clarifying comment about draft personas is permitted; only
    crawler directives leaking the draft domain are forbidden.
    """
    text = ROBOTS.read_text()
    bad_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "makcikgpt" in stripped.lower():
            bad_lines.append(stripped)
    assert not bad_lines, (
        f"robots.txt has crawler directives referencing makcikgpt: {bad_lines}"
    )


# ── 3. .well-known/agent.json canonization ────────────────────────────────


def test_agent_card_is_canonical_organ_card():
    card = json.loads(AGENT_CARD.read_text())
    assert card.get("card_kind") == "organ_public_agent_card", (
        ".well-known/agent.json must self-identify as the organ public card"
    )
    assert card.get("canonical_path") == "/.well-known/agent.json"
    assert card.get("url") == f"https://{ORGAN_DOMAIN}", (
        f"organ card url is {card.get('url')}, expected https://{ORGAN_DOMAIN}"
    )


def test_agent_card_does_not_advertise_draft_persona():
    card = json.loads(AGENT_CARD.read_text())
    # The card may reference the persona in do_not_confuse_with, but must not
    # list it as a route/skill/capability.
    serialized = json.dumps(card).lower()
    assert "makcikgpt.arif-fazil.com" not in serialized, (
        "organ agent card leaks the makcikgpt draft domain"
    )


def test_makcikgpt_card_is_marked_draft_only():
    persona = json.loads(DRAFT_PERSONA_CARD.read_text())
    assert persona.get("capabilities", {}).get("draft_only") is True, (
        "makcikgpt persona must declare draft_only=true"
    )
    assert "DRAFT_ONLY" in persona.get("scopes", []), (
        "makcikgpt persona scopes must include DRAFT_ONLY"
    )
    # Persona must NOT be referenced from the organ public agent card's skills.
    organ = json.loads(AGENT_CARD.read_text())
    organ_skills = {s.get("id") for s in organ.get("skills", []) if isinstance(s, dict)}
    assert "makcikgpt" not in str(organ_skills).lower(), (
        "organ public agent card must not list makcikgpt as a skill"
    )


# ── 4. Commodity route expectations in contracts ──────────────────────────


def test_tools_yaml_declares_terminal_and_organ_routes():
    import yaml

    doc = yaml.safe_load(TOOLS_YAML.read_text())
    routes = doc.get("public_routes", {})
    assert "organ" in routes and "terminal" in routes, (
        "contracts/tools.yaml must declare public_routes.{organ,terminal}"
    )
    paths = {r["path"] for r in routes["terminal"]}
    for required in ("/wealth/", "/wealth/gold/", "/wealth/oil/", "/wealth/gas/"):
        assert required in paths, (
            f"contracts/tools.yaml public_routes.terminal is missing {required}"
        )


def test_mcp_surface_yaml_declares_commodity_routes():
    import yaml

    doc = yaml.safe_load(MCP_SURFACE_YAML.read_text())
    routes = doc.get("public_discovery_routes", {}).get("terminal", [])
    paths = {r["path"] for r in routes}
    for required in ("/wealth/", "/wealth/gold/", "/wealth/oil/", "/wealth/gas/"):
        assert required in paths, (
            f"contracts/mcp_surface.yaml public_discovery_routes.terminal "
            f"is missing {required}"
        )


def test_dist_files_for_commodity_routes_exist():
    for asset in ("gold", "oil", "gas", "wealth"):
        index = SITE_DIST / asset / "index.html"
        assert index.exists() and index.stat().st_size > 0, f"missing or empty: {index}"


def test_dist_llms_txt_exists_for_terminal():
    llms = SITE_DIST / "wealth" / "llms.txt"
    assert llms.exists() and llms.stat().st_size > 0, f"missing: {llms}"
