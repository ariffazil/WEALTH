# PROTOCOL_CONFORMANCE.md — WEALTH Capital Intelligence

> Layer: L3 · Role: Capital/economic intelligence — compute, never allocate · Repo: ariffazil/wealth

## MCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| llms.txt | ✅ | `/root/WEALTH/llms.txt` — 12 public MCP tools, compute-only |
| tools/list | ✅ | `:18082` — 12 tools loaded: 8 `capital_*` tools plus 4 institutional compatibility tools |
| health endpoint | ✅ | `:18082/health` — distinguishes live tool count and source SHA from declared or unverified fallback metadata |
| Surface audit | ✅ | Source registration and manifests declare the same 12-tool surface |

## FastMCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| FastMCP server | ✅ | Python 3.12 FastMCP runtime on port 18082 |
| Resource discovery | ✅ | MCP resources available — capital models, wisdom corpus |

## A2A Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| Agent card | ✅ | `/.well-known/agent.json` — consolidated federation card |
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
- 12 operational public tools, zero source-manifest drift
- Pure deductive math — golden-tested hand-checked cases for every `capital_primitive` mode
- Next milestone: Zero gaps in current compliance

---
Generated: 2026-07-19 · Authority: AAA Control Plane
DITEMPA BUKAN DIBERI
