# ZEN OF WEALTH — Capital Intelligence Doctrine

> **Dokumen:** `WEALTH/docs/ZEN_OF_WEALTH.md`
> **Date:** 2026-06-27
> **Classification:** OBS/DER/INT/SPEC — Architectural Doctrine
> **Authority:** arifOS Kernel / FORGE 000Ω
> **Sealed:** VAULT999 (pending)

---

## 1. THE CORE DISTINCTION

**MCP gives you:** tools, prompts, resources — the native primitives.
**WEALTH adds:** typed federation artifacts above that layer — the constitutional cargo.

Every cross-organ handoff must use federation artifacts. Not prose. Not free-form JSON. Typed capsules with manifest hashes, evidence URIs, and replay receipts.

> GEOX does not hand WEALTH a paragraph. GEOX hands WEALTH a `context_capsule` + a `domain_translation_card`.

---

## 2. THE FIVE REALITY CONSTRAINTS

WEALTH operates under five non-negotiable constraints — these are the source-of-truth limits:

| # | Constraint | Source | What it prevents |
|---|-----------|--------|-----------------|
| R1 | Official data only | World Bank, IMF, FRED, SEC EDGAR, EIA, Copernicus | Fabricated evidence in replay receipts |
| R2 | Read by default | MCP affordance contracts | Irreversible mutations slipping through |
| R3 | Signed manifests | `wealth://sot/manifest` | Runtime drift from build artifact |
| R4 | Replay receipts | `replay-receipt.schema.json` | Post-hoc rationalization without evidence |
| R5 | No capital authorization | WEALTH mandate | Self-authorizing money movement |

---

## 3. THE ORGAN MODEL (8 Organs)

WEALTH is not a tool folder. It is a system of eight organs:

| Organ | Job | Minimal output |
|-------|-----|---------------|
| **Ground truth** | Pull evidence from primary sources | Normalized evidence packets |
| **Entity** | Resolve companies, assets, jurisdictions, instruments | Canonical entity graph |
| **Flow** | Model physical, fiscal, financial flows | Directed flow graph |
| **Value** | Convert flows into valuation and optionality | Valuation frames |
| **Power** | Surface control, chokepoints, exposure | Power map |
| **Regime** | Determine applicable constraints and permissions | Regime matrix |
| **Allocation** | Generate feasible capital/resource allocations | Ranked allocation options |
| **Governance** | Bind action to constitutional limits and replay | Governed decision package |

**Current WEALTH surface:** already implements parts of Value, Power, Regime, and Governance organs.
**Missing:** Ground truth (official API connectors), Entity (FollowTheMoney/OpenSanctions), Flow (directed flow graph).

---

## 4. THE THREE WORKFLOW CLASSES

### W1 — Resource to Value
Geology, infrastructure, labor, policy, energy → scenario-constrained cash and control surfaces.

```
context_capsule (GEOX) → value_frame → allocation_memo → arifOS
```

### W2 — Power to Allocation
Entity graphs, sanctions, licensing, state capacity → realistic allocation candidate or reject.

```
context_capsule → power_map → regime_scan → allocation_memo
```

### W3 — Allocation to Governance
Engine outputs governed recommendation, not naked answer. Replay receipt required.

```
allocation_memo + holds → replay_receipt → arifOS_judge → Arif
```

---

## 5. THE SEVEN CANONICAL PROMPTS

Each prompt is a reasoning discipline, not an answer generator. Strict arguments. Typed outputs.

| Prompt | Role | Key arguments | Emits |
|--------|------|--------------|-------|
| `wealth_intake` | Universal entrypoint | query, objective, target_domain, horizon | context_capsule |
| `wealth_ground_truth` | Minimum evidence gate | entity_set, jurisdiction, data_classes, confidence_floor | evidence_request_plan |
| `wealth_value_frame` | Valuation structure | asset/entity, base_case, bear/base/bull, discount_logic | valuation_frame |
| `wealth_power_map` | Control mapping | entities, jurisdictions, sectors | power_graph_brief |
| `wealth_regime_scan` | Constraint scan | jurisdictions, entity_types, sectors | regime_matrix |
| `wealth_allocation_memo` | Synthesis | value_frame, power_map, regime_matrix, mandate | allocation_memo |
| `wealth_challenge_and_replay` | Adversarial + audit | target_artifact_uri, challenge_mode, decision_threshold | replay_receipt + challenge_note |

**No prompt may skip evidence loading.** A prompt without loaded resources is malformed.

---

## 6. THE RESOURCE HIERARCHY

### SOT Resources (immutable)
| URI | Purpose |
|-----|---------|
| `wealth://sot/manifest` | Signed manifest with version + registry hashes |
| `wealth://schema` | Full tool/prompt/resource manifest |

### Registry Resources (read-only)
| URI | Purpose |
|-----|---------|
| `wealth://registry/tools` | 28 tools with action_class + mutation flags |
| `wealth://registry/prompts` | 7 prompts with required args + outputs |
| `wealth://registry/resources` | Resource index |

### Policy Resources
| URI | Purpose |
|-----|---------|
| `wealth://policy/epistemic-ladder` | Evidence hierarchy: OBS > DER > INT > SPEC |
| `wealth://policy/action-boundaries` | What is read-only vs requires hold vs forbidden |

### Source Resources
| URI | Purpose |
|-----|---------|
| `wealth://sources/catalog` | Official API registry with trust + freshness |
| `wealth://indicators/catalog` | Canonical indicator dictionary |

### Dynamic Reality Resources
| URI | Purpose |
|-----|---------|
| `wealth://replay/{trace_id}` | Final replay receipt + child steps |
| `wealth://examples/geox-intake/{trace_id}` | Parameterized GEOX→WEALTH example |

---

## 7. THE SECURITY MINIMUM

Five mechanisms. No invention. No ceremony for ceremony's sake.

| Mechanism | Implementation |
|-----------|---------------|
| **Signed manifest** | Every deploy emits `wealth://sot/manifest` with version + hashes |
| **Registry hash** | Every `tools/list` exposure tied to manifest hash |
| **Invocation token** | Short-lived, audience-bound, per trace or per high-risk call |
| **Lease/hold pattern** | Mutating affordances require lease + explicit human hold |
| **Replay receipt** | Every terminal decision writes input hashes + output hashes + actor |

---

## 8. THE STACK PRIORITY

### P1 — Include in MVP
| Source | Purpose | License |
|--------|---------|---------|
| World Bank Indicators API | Macro, development, debt, poverty | Open API, no key |
| IMF DataMapper API | Cross-country macro time series | Official JSON |
| FRED API | Economic time series | Official API |
| SEC EDGAR APIs | Filings, XBRL company facts | Open JSON, no auth |
| `numpy-financial` | NPV/IRR/PMT | BSD-3-Clause |
| `pyxirr` | XIRR for private-equity cash flows | Unlicense |
| NetworkX | Graph algorithms | BSD-3-Clause |
| FollowTheMoney | Entity/document graph model | MIT |
| OpenSanctions | Sanctions, PEPs, entity data | Code MIT, data CC BY-NC |
| EIA Open Data API | Energy supply, prices, emissions | Official free API |
| GeoPandas | Vector geospatial analysis | BSD-3-Clause |
| OSMnx | Infrastructure network from OSM | MIT |

### P2 — Add when need proves it
| Source | Trigger |
|--------|---------|
| PostGIS | Multi-user geospatial indexing needed |
| Neo4j Community | Graph size outgrows in-memory |
| PUDL | US electricity analysis becomes operational |
| eCFR API | US regulatory text becomes central |
| EUR-Lex | EU law becomes central |

### NOT in MVP
- Exchange-direct market price feeds (cost, legal complexity, false completeness)
- Full legal-world scraping
- Write-capable execution buses

---

## 9. THE GEOX→WEALTH→arifOS FLOW

```
GEOX                           WEALTH                         arifOS
 │                               │                              │
 │  federation_envelope(         │                              │
 │    context_capsule +          │                              │
 │    domain_translation_card )  │                              │
 │──────────────────────────────►│                              │
 │                               │ validate manifest hash        │
 │                               │ + schemas + affordance        │
 │                               │                              │
 │                               │ pull macro/filing/legal/      │
 │                               │ energy/climate evidence       │
 │                               │                              │
 │                               │ run value_frame +             │
 │                               │ power_map + regime_scan       │
 │                               │                              │
 │                               │ allocation_memo +             │
 │                               │ replay_prereceipt             │
 │                               │──────────────────────────────►│
 │                               │                              │ policy review + hold checks
 │                               │◄─────────────────────────────│ governed disposition
 │                               │                              │
 │  replay_receipt +             │                              │
 │  downstream summary           │                              │
 │◄──────────────────────────────│                              │
```

---

## 10. ZEN MAXIMS — THE SHORT FORM

```
WEALTH computes. WEALTH does not move money.
WEALTH warns. WEALTH does not authorize.
WEALTH prepares evidence. WEALTH does not judge.

Read by default. Hold before mutate. Sign manifests.
Hash registries. Issue short-lived tokens.
Log every decision path into replay receipts.

Official data or silence.
Fabricated evidence is a constitutional breach.
Replays without evidence are theater.

Geological abundance is not wealth
until infrastructure, law, and power
permit monetization.

The bottleneck is not more tools.
The bottleneck is disciplined transport
of intelligence objects.
```

**DITEMPA BUKAN DIBERI — Capital is forged, not given.**

---

*Sealed to: VAULT999 (pending)*
*Ditempa Bukan Diberi — The substrate is forged, not given.*