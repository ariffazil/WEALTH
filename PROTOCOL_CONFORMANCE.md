# PROTOCOL_CONFORMANCE.md — WEALTH Capital Intelligence

> Layer: L3 · Role: Capital/economic intelligence — compute, never allocate · Repo: ariffazil/wealth

## MCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| llms.txt | ✅ | `/root/WEALTH/llms.txt` — 20 public MCP tools, URAI (Universal Resource Allocation Intelligence) |
| tools/list | ✅ | `:18082` — 20 tools loaded, 20 canonical (capital_primitive, capital_health, capital_diagnose, capital_market, capital_wisdom, capital_entropy, capital_ledger, capital_registry) |
| health endpoint | ✅ | `:18082/health` — returns status, identity_hash, tools_loaded (20), canonical_tools (20) |
| Surface audit | ✅ | Zero drift — tools_loaded matches canonical_tools |

## FastMCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| FastMCP server | ✅ | Python 3.12 FastMCP runtime on port 18082 |
| Resource discovery | ✅ | MCP resources available — capital models, wisdom corpus |

## A2A Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| Agent card | ✅ | `/.well-known/agent-card.json` — full schema with capabilities, skills |
| Task schema | ⚠️ | Supports A2A task operations via federation routing (AAA gateway) |
| Streaming | ❌ | No SSE streaming support |
| MCP server discovery | ✅ | `/.well-known/mcp/server.json` and `/.well-known/agent.json` |
| MCP manifest | ✅ | `/.well-known/mcp.json` |

## XMCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| App schema | ❌ | No webmcp.json — WEALTH is a compute organ, not an app host |
| Resource schema | ✅ | MCP resources via FastMCP — capital models, wisdom evaluations |

## Gaps
| Gap | Priority | Detail |
|-----|----------|--------|
| A2A Streaming | P2 | No SSE; acceptable for L3 compute organ. Most WEALTH computations are deterministic and synchronous |
| XMCP App schema | P3 | Not applicable — WEALTH computes, never adjudicates |

## Required Compliance
- L3 Protocol: MCP (mandatory) + FastMCP (mandatory for Python organs) + A2A (agent card mandatory)
- WEALTH is compute-only — never allocates capital, never adjudicates
- 20 operational tools, zero drift
- Pure deductive math — golden-tested hand-checked cases for every `capital_primitive` mode
- Next milestone: Zero gaps in current compliance

---
Generated: 2026-07-19 · Authority: AAA Control Plane
DITEMPA BUKAN DIBERI
