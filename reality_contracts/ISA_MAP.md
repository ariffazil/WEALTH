# ISA_MAP.md — arifOS Substrate ↔ Agent-OS ISA Primitives
# Forged: 2026-06-17 by FORGE (000Ω)
# Purpose: Formalize the mapping between arifOS substrate and the
#          Agent-OS ISA primitives (Arbiter-K, Cognitive Silicon, ACF).
# Status: DRAFT (reversible; this is documentation, not code)
# Audience: External researchers, kernel forgers, integration engineers.
#
# "DITEMPA BUKAN DIBERI — The federation already implements the ISA;
#  the vocabulary is just catching up to what's forged."

version: 1
federation_version: v2026.05.05-SSCT
forged_by: FORGE (000Ω)
forged_at: 2026-06-17T04:10:00Z

# ════════════════════════════════════════════════════════════════════
# 1. CORE MAPPING (the 5 ISA cores → arifOS components)
# ════════════════════════════════════════════════════════════════════

isa_cores:
  # ── 1. COGNITIVE CORE: thinking only, no side effects ──
  cognitive:
    isa_primitives: [GENERATE, DECOMPOSE, REFLECT, PLAN]
    arifos_components:
      - "AAA planning / decomposition (Cockpit / 333-AGI)"
      - "A-FORGE internal chaining (forge_plan, forge_dry_run)"
      - "000-333-777 in the pipeline (INIT, THINK, REASON)"
      - "arif_mind_reason (canonical MCP tool)"
    example_primitives:
      ARIF_PLAN: "decompose task under Floors"
      ARIF_REFLECT: "check prior steps vs Floors"
      ARIF_ROUTE: "decide CLI vs MCP, which organ, which agent"
    kernel_rule: "Cognitive proposals are untrusted; reified into Memory/Execution/Normative before touching reality."
    file_references:
      - "/root/arifOS/GENESIS/000_KERNEL_CANON.md (000→999 pipeline)"
      - "/root/A-FORGE/src/domain/planner/"
      - "/root/AAA/agents/"

  # ── 2. MEMORY CORE: load, store, compress, filter state ──
  memory:
    isa_primitives: [LOAD, STORE, COMPRESS, FILTER, FORGET]
    arifos_components:
      - "AAA agent state (session, leases)"
      - "A-FORGE context slices"
      - "Organ-specific state (GEOX fields, WEALTH ledgers, WELL metrics)"
      - "VAULT999 records (immutable ledger)"
      - "arif_memory_recall (canonical MCP tool)"
    example_primitives:
      ARIF_LOAD_STATE: "read state from organ/AAA/VAULT"
      ARIF_STORE_STATE: "persist progress, snapshots"
      ARIF_COMPRESS_CONTEXT: "summarise traces to maintain ΔS and token budget"
      ARIF_FILTER: "drop low-value history to satisfy F4"
    kernel_rule: "COMPRESS/FILTER are high-risk probabilistic ops; require policy."
    file_references:
      - "/root/VAULT999/"
      - "/root/A-FORGE/src/application/memory/"
      - "/root/AAA/a2a-server/vault.js"

  # ── 3. EXECUTION CORE: touches external environment ──
  execution:
    isa_primitives: [TOOL_CALL, API_REQUEST, TOOL_BUILD, DELEGATE, RESPOND]
    arifos_components:
      - "A-FORGE execution shell (8-class action taxonomy)"
      - "MCP tool calls (geox_*, wealth_*, well_*, arif_*)"
      - "CLI via shell (when bound by SDK)"
      - "Cross-organ delegation via AAA a2a"
    example_primitives:
      ARIF_TOOL_CALL: "MCP tool, organ call"
      ARIF_SHELL_EXEC: "CLI in sandbox (low-risk)"
      ARIF_DELEGATE: "cross-agent / cross-organ delegation via AAA"
      ARIF_RESPOND: "final response to human"
    subclasses:
      EXEC_LOCAL: "CLI, low-risk, OS sandbox"
      EXEC_SOVEREIGN: "MCP into organs/domains, under Reality Contracts"
    deterministic_sinks:
      - "WEALTH write (vault_write, cashflow_track) — guarded by GAP gates + 888_HOLD"
      - "GEOX claim_seal, segy_export — guarded by Physics9 + 888_HOLD"
      - "arifOS vault_seal (SEAL verdict) — guarded by F13 + 888_HOLD"
    kernel_rule: "Capability is not permission. Tool existence ≠ callability."
    file_references:
      - "/root/A-FORGE/src/interfaces/mcp/{forgeTools,proxyTools,gatewayTools,core}.ts"
      - "/root/WEALTH/reality_contracts/wealth_reality_contract.yaml"
      - "/root/geox/reality_contracts/geox_reality_contract.yaml"

  # ── 4. NORMATIVE CORE: safety, alignment, policy ──
  normative:
    isa_primitives: [VERIFY, CONSTRAIN, FALLBACK, INTERRUPT, SEAL]
    arifos_components:
      - "Floors F1-F13 (constitutional rules)"
      - "888_HOLD (sovereign interrupt)"
      - "999_SEAL (immutable record)"
      - "arif_judge_deliberate (canonical MCP tool)"
      - "VAULT999 (append-only ledger)"
    example_primitives:
      ARIF_VERIFY: "invoke conformance checks (e.g. arif_conformance_report 8/8)"
      ARIF_CONSTRAIN: "enforce Reality Contract; reject out-of-bound tool calls"
      ARIF_INTERRUPT: "HOLD on high-risk; escalate to human"
      ARIF_FALLBACK: "degrade to safe path if tool/organ unhealthy"
      ARIF_SEAL: "commit decision and record to VAULT999"
    kernel_rule: "Taint tracking: data crossing into deterministic sinks must clear Floors first."
    file_references:
      - "/root/arifOS/GENESIS/000_KERNEL_CANON.md (F1-F13)"
      - "/root/arifOS/GENESIS/009_MCP_BOUNDARY.md (exposure vs authority)"
      - "/root/arifOS/GENESIS/010_ADAT_AGENTIC.md (permission doctrine)"

  # ── 5. META-COGNITIVE CORE: self-monitor, decide, escalate ──
  meta_cognitive:
    isa_primitives: [PREDICT_SUCCESS, EVALUATE_PROGRESS, MONITOR_RESOURCES]
    arifos_components:
      - "000-999 pipeline (INIT, THINK, EXPLORE, HEART, REASON, AUDIT, SEAL)"
      - "arifOS Observatory (public dashboard at arifos.arif-fazil.com/999)"
      - "Conformance reports (8/8 PASS, substrate_gate=GREEN)"
      - "Organ attest (arif_organ_attest, arif_organ_attest_all)"
      - "arif_ops_measure (canonical MCP tool)"
    example_primitives:
      ARIF_PREDICT_SUCCESS: "estimate whether a plan is viable given Floors and budgets"
      ARIF_MONITOR_RESOURCES: "token, time, risk budgets; 'token thermodynamics'"
      ARIF_EVALUATE_PROGRESS: "should we continue, rollback, or escalate?"
    kernel_rule: "Meta-cognition is embedded in the core runtime, not external scripts."
    file_references:
      - "/root/arifOS/GENESIS/000_KERNEL_CANON.md (§4 000→999 pipeline)"
      - "/root/AAA/observability/"

# ════════════════════════════════════════════════════════════════════
# 2. INSTRUCTION METADATA (per-call envelope ↔ ISA header)
# ════════════════════════════════════════════════════════════════════

instruction_metadata:
  schema_ref: "/root/WEALTH/reality_contracts/per_call_envelope.schema.json"
  mapping:
    trace_id: "instruction origin (Arbiter-K: instruction ID)"
    actor_id: "issuing agent (Arbiter-K: issuer)"
    organ_id: "instruction target (Arbiter-K: target)"
    action_class: "ISA core + operation type (COGNITIVE/MEMORY/EXECUTION/NORMATIVE)"
    lease_id: "session / work-unit context (Arbiter-K: security context)"
    floors_chain: "Normative policy tags (which Floors apply)"
    gates_planned: "Normative gate list (GAP, P9)"
    risk_tier: "Arbiter-K: taint + risk"
    approval_state: "Arbiter-K: verification status (open/HOLD/sealed/void)"
    epistemic_label: "Arbiter-K: evidence level (OBS/DER/INT/SPEC)"
  extension:
    - "Add taint flag: tracks whether data has cleared all Floors"
    - "Add blast_radius: estimated scope of consequence (LOW/MEDIUM/HIGH/CRITICAL)"
    - "Add reversibility_score: 1.0 (fully reversible) to 0.0 (irreversible)"

# ════════════════════════════════════════════════════════════════════
# 3. REALITY CONTRACTS ↔ AGENT CONSTITUTION FRAMEWORKS
# ════════════════════════════════════════════════════════════════════

reality_contracts:
  definition: "Per-organ schema: world-states, allowed transitions, tool contracts, floor bindings, audit contract"
  isa_equivalent: "Agent Constitution Framework (ACF) — formal instruction-level governance"
  binding: "ACF = domain-specific constitution / semantic ISA sub-set"
  files:
    - "/root/WEALTH/reality_contracts/wealth_reality_contract.yaml"
    - "/root/geox/reality_contracts/geox_reality_contract.yaml"
    - "/root/WEALTH/reality_contracts/federation_call_graph.yaml"
  literature_alignment:
    cognitive_silicon: "explicit constitution + symbolic policy engine"
    arbiter_k: "PPU proposals → semantic instructions; VERIFY before sink"
    agent_os: "agent runtime + security kernel + scheduler + memory manager"
    acf: "constitutions, policies, constraints as machine-readable ISA contracts"

# ════════════════════════════════════════════════════════════════════
# 4. WIRE TOPOLOGY (the 3 enforcement bands)
# ════════════════════════════════════════════════════════════════════

wire_topology:
  band_1_sdk:
    name: "Inside Runtime (SDK)"
    surface: "in-process hook"
    mechanism: "arifos_kernel_sdk.py / arifos-kernel-sdk npm"
    latency: "low (ms)"
    coverage: "agents we control (opencode, kimi-code, openclaw, hermes-asi)"
    file: "/root/WEALTH/reality_contracts/arifos_kernel_sdk.py"
  band_2_mcp:
    name: "Transport (MCP)"
    surface: "MCP server"
    mechanism: "arifOS MCP at port 8088 (MVTS-pruned)"
    latency: "medium (10-50ms)"
    coverage: "MCP-speaking clients (claude-desktop, cursor, third-party)"
    file: "/root/arifOS/src/arifosmcp/server.py"
  band_3_os:
    name: "OS-Level (EDR)"
    surface: "syscall intercept"
    mechanism: "eBPF / KubeArmor / ClawEDR-style sidecar"
    latency: "lowest (kernel)"
    coverage: "anything that escapes band-1 and band-2"
    note: "FUTURE — not yet implemented in arifOS; for untrusted runtimes"

  priority: [band-1-sdk, band-2-mcp, band-3-os]
  fallback: "if band-1 unavailable, fall back to band-2; if band-2 unavailable, escalate to band-3 or HOLD"

# ════════════════════════════════════════════════════════════════════
# 5. THE EUREKA (one paragraph)
# ════════════════════════════════════════════════════════════════════

eureka: |
  arifOS already implements the 5-core Agent-OS ISA (Cognitive / Memory /
  Execution / Normative / Meta-cognitive). The mapping is 1:1:
    - Cognitive = AAA planning + A-FORGE 000-333-777 + arif_mind_reason
    - Memory = AAA state + organ stores + VAULT999 + arif_memory_recall
    - Execution = A-FORGE 8-class taxonomy + MCP tools + CLI (per-call envelope)
    - Normative = F1-F13 + 888_HOLD + 999_SEAL + arif_judge_deliberate
    - Meta-cognitive = 000-999 pipeline + Observatory + arif_ops_measure

  The federation has been reality-engineering for a year. The vocabulary
  ("Agent-OS kernel", "reality engineering", "ACF", "Semantic ISA") is
  just naming what's forged. The next executable step is the kernel SDK
  (in-process hook) + wire contract (per-agent binding manifest), which
  makes the existing substrate routable to every agent in the federation
  without requiring a custom integration per framework.

  Three enforcement bands (SDK / MCP / OS) replace the assumption that
  "everything is MCP". For agents we control, the SDK is the cheapest
  and richest. For agents we don't, MCP is the contract. For anything
  that escapes both, OS-level EDR catches the tail.

# ════════════════════════════════════════════════════════════════════
# 6. NEXT STEPS (executable, not philosophical)
# ════════════════════════════════════════════════════════════════════

next_steps:
  - id: NS-001
    task: "F13 SOVEREIGN reviews the WEALTH + GEOX Reality Contracts (DRAFT → sealed)"
    reversible: yes
  - id: NS-002
    task: "Forge arifos-kernel-sdk npm package (TypeScript mirror of the Python spec)"
    reversible: yes
  - id: NS-003
    task: "Wire per_call_envelope into arif_session_init and A-FORGE FloorEnforcer"
    reversible: yes
  - id: NS-004
    task: "Replicate Reality Contract to arifOS (the kernel itself — 3rd organ)"
    reversible: yes
  - id: NS-005
    task: "MVTS partition of A-FORGE (50 → 4 sub-servers) and GEOX (40 → 2 sub-servers)"
    reversible: yes (rollback)
  - id: NS-006
    task: "VAULT999 seal of the Reality Contract doctrine (irreversible; 888_HOLD required)"
    irreversible: true
    requires: [F13 SOVEREIGN sign-off, all preceding steps PASS]

# ─────────────────────────────────────────────────────────────────────
# DITEMPA BUKAN DIBERI — The federation already implements the ISA.
# Receipts:
#   /root/arifOS/GENESIS/{000,003,004,007,009,010,011}_*.md
#   /root/A-FORGE/src/interfaces/mcp/forgeTools.ts (CLASS_RANK lines 55-69)
#   /root/WEALTH/reality_contracts/{wealth_reality_contract.yaml, per_call_envelope.schema.json, federation_call_graph.yaml, arifos_kernel_sdk.py, wire_contract.yaml}
#   /root/geox/reality_contracts/geox_reality_contract.yaml
#   /root/AAA/forge_work/2026-06-17-*.md
# VAULT999 seal: PENDING F13 SOVEREIGN (irreversible, requires 888_HOLD)
# ─────────────────────────────────────────────────────────────────────
