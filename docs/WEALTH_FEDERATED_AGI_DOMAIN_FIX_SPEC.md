# WEALTH Federated AGI Domain — Fix Specification

> **CLASSIFICATION:** C2 — Execute after floor check  
> **AUTHORITY:** FORGE (000Ω) — autonomous engineering artifact  
> **SOVEREIGN:** Muhammad Arif bin Fazil (F13, 888)  
> **DATE:** 2026-06-15  
> **STATUS:** ARTIFACT READY — no repo mutated  
> **DOCTRINE:** DITEMPA BUKAN DIBERI

---

## 0. WHY THIS EXISTS

WEALTH is a 17,313-line single-file MCP server (`internal/monolith.py`) with 86 `@mcp.tool` decorators, 19 public tools, 10 deprecated tools, ~34 hidden aliases, and 5 silently-failing tool registrations. It has strong constitutional doctrine but brittle architecture.

**The diagnosis:** WEALTH must stop being a monolith and become a **federated, typed, testable, transport-governed capital intelligence domain** that serves arifOS as an evidence organ — never an execution organ.

**The principle:** WEALTH computes. arifOS judges. AAA displays. A-FORGE executes. ARIF decides.

---

## 1. CURRENT STATE — LIVE RECON (2026-06-15)

### 1.1 WEALTH Tool Surface

**19 public tools** (from `WEALTH_PUBLIC_TOOL_ORDER`):

| Layer | Tool | Domain | Modes |
|-------|------|--------|-------|
| L0 Kernel | `wealth_system_registry_status` | META | `registry`, `health` |
| L0 Kernel | `wealth_omni_wisdom` | SYNTHESIS | `synthesize`, `deal`, `hysteresis`, `omni` |
| L0 Kernel | `wealth_agent_path` | META | keyword-based routing |
| Phase 1 | `wealth_survival_engine` | FLOW/SURVIVAL | `cashflow`, `runway`, `burn`, `liquidity`, `personal_finance` |
| L1 | `wealth_conservation_capital` | CONSERVATION | `state`, `snapshot`, `ledger_read`, `ledger_seal` |
| L1 | `wealth_flow_liquidity` | FLOW | `cashflow`, `velocity`, `triage` |
| L1 | `wealth_gradient_price` | GRADIENT | `spread`, `misprice`, `pressure` |
| L1 | `wealth_entropy_risk` | ENTROPY | `emv`, `monte_carlo`, `audit`, `asymmetry_map`, `return_classify`, `institutional` |
| L1 | `wealth_energy_productivity` | ENERGY | `pi`, `efficiency`, `roi`, `irr` |
| L1 | `wealth_time_discount` | TIME | `npv`, `irr`, `payback`, `mIRR` |
| L1 | `wealth_inertia_leverage` | INERTIA | `dscr`, `leverage`, `strain` |
| L1 | `wealth_field_macro` | FIELD | `fetch`, `snapshot`, `sources`, `health`, `vintage`, `preset`, `labor`, `reconcile` |
| L1 | `wealth_signal_information` | SIGNAL | `evoi`, `evoi_mc`, `schema` |
| L1 | `wealth_game_coordination` | GAME | `equilibrium`, `game`, `budget`, `preference` + 5 templates |
| L1 | `wealth_boundary_governance` | BOUNDARY | `floors`, `policy`, `stewardship`, `decision`, `legitimacy_audit`, `federation_readiness` |
| L2 | `wealth_governance_verdict` | GOVERNANCE | final allocation verdict |
| L2 | `wealth_inequality_kernel` | CIVILIZATION | 5-dimension inequality synthesis |
| D1 | `wealth_personal_finance` | PERSONAL | `track`, `summary`, `runway`, `net_worth`, `epf`, `zakat` |
| D3 | `wealth_market_data` | MARKET | `fx`, `commodity`, `macro` |
| D4 | `wealth_stock_analysis` | STOCK | 16 modes (verify_math through 999_engine) |

**5 silently-failing tools** (`_KNOWN_MISSING`):
- `wealth_screen_opportunity`
- `wealth_compute_viability`
- `wealth_score_risk`
- `wealth_compare_scenarios`
- `wealth_emit_investment_memo`

**10 deprecated tools** still registered with `deprecatedHint`.

**~34 hidden aliases** via `_ALIAS_DISPATCH` mapping v1 names to v2 canonical functions.

### 1.2 WEALTH Internal Structure

```
/root/WEALTH/
├── internal/
│   ├── monolith.py          # 17,313 lines — THE problem
│   ├── personal_finance.py  # D1: 6 @mcp.tool functions (inlined into monolith)
│   ├── market_data.py       # D3: 3 @mcp.tool functions (inlined into monolith)
│   ├── governance.py        # ForgeLaw, kappa_r, psi_le, QDF
│   ├── kernel_math.py       # NPV, IRR, EMV, DSCR, payback, PI
│   ├── invariants.py        # G-score (Lyapunov, entropy, boundary stress)
│   ├── organ_governance.py  # F1-F13 wrapper, patches mcp.call_tool
│   ├── db_schema.py         # PostgreSQL schema
│   ├── federation_memory.py # Cross-organ memory bridge
│   ├── pai_receipt.py       # PAI receipt generation
│   ├── vps_metrics.py       # VPS health metrics
│   ├── engines/
│   │   ├── canonical_tools.py   # 11 canonical tool implementations (commented-out decorators)
│   │   ├── five_seals.py        # Five Seals governance
│   │   ├── advisory.py          # Advisory boundary
│   │   └── compatibility_map.py # V2 canonical map
│   ├── stock/               # D4: 16 files — stock analysis engines
│   ├── bursa/               # Bursa Malaysia adapter
│   ├── world/               # Global markets (yfinance)
│   └── domains/             # Domain stubs (capital, field, personal, signal, stock, time)
├── host/                    # Modular Python libraries
│   ├── governance/          # Tri-witness
│   ├── coordination/        # Game theory
│   ├── epistemic/           # Evidence quality
│   ├── ingest/              # Data ingestion
│   ├── kernel/              # CapitalX
│   ├── wealth/              # Cashflow, maruah, networth, projection
│   └── civilizational/      # Boundary monitor, cascade detector, prosperity index
├── capitalx/                # Constitutional capital pricing (DESIGN.md only)
├── canon/                   # 14 constitutional specs
├── contracts/               # MCP surface YAML, schemas
├── tests/                   # 28 test files (Python + JS)
└── pyproject.toml           # Python 3.12, FastMCP 3.3.1+
```

### 1.3 MCP Transport

```
Client → HTTPS → Cloudflare Tunnel → localhost:18082
                                         │
                   ┌─────────────────────┘
                   ▼
         Starlette (uvicorn)
         ├── /mcp              (FastMCP streamable-http, stateless)
         ├── /tools            (Tool registry JSON)
         ├── /prompts          (Prompt discovery)
         ├── /resources        (Resource discovery)
         ├── /health           (Health probe)
         └── /.well-known/mcp.json (MCP Server Card)
```

**Transport:** `streamable-http` (MCP spec 2024-11-25), stateless mode.  
**Auth:** localhost-only (Cloudflare Tunnel for external).  
**Port:** 18082 (systemd overrides code default of 8082).

### 1.4 Federation Connections

```
arifOS (8088) ──MCP JSON-RPC──→ WEALTH (18082)
     │                              │
     │  federation_bridge.py        │  organ_governance.py
     │  (NATS primary,              │  (intercepts ALL tool calls,
     │   HTTP fallback)             │   adds Evidence Contract)
     │                              │
     ├── health check ←─────────────┤
     ├── tool discovery ←───────────┤
     └── tool call →────────────────┘
```

**arifOS → WEALTH paths:**
1. `wealth_bridge.py` — direct HTTP POST to `localhost:18082/mcp` (JSON-RPC `tools/call`)
2. `federation_bridge.py` — NATS primary (`arifos.requests.WEALTH`), HTTP fallback
3. Optional proxy: `ARIFOS_EXPOSE_ORGAN_BRIDGE=true` registers WEALTH tools on arifOS surface

**WEALTH → arifOS paths:**
1. Health check: `wealth_system_registry_status(mode="health")` calls arifOS at `127.0.0.1:8088`
2. Vault write: `wealth_conservation_capital(mode="ledger_seal")` → VAULT999
3. Reality ledger: `record_wealth_computation()` → side-channel log

### 1.5 Pain Points

| # | Pain Point | Severity | Evidence |
|---|-----------|----------|----------|
| 1 | 17,313-line single file | CRITICAL | `monolith.py` — any edit requires navigating entire file |
| 2 | FastMCP internal API dependency | HIGH | Line 16272: `mcp._local_provider._components` — private API, breaks on upgrade |
| 3 | 5 silently-failing tools | HIGH | `_KNOWN_MISSING` — `@mcp.tool` decorators silently fail at import |
| 4 | String-based mode routing | MEDIUM | No enum enforcement, no schema validation of mode-specific params |
| 5 | JSON string deserialization | MEDIUM | Multiple tools accept `Optional[Any]` and manually try `json.loads()` |
| 6 | 10 deprecated tools still registered | MEDIUM | Surface area bloat, parameter confusion |
| 7 | Dual registration confusion | MEDIUM | `personal_finance.py` + `market_data.py` define tools, then monolith re-wraps them |
| 8 | `host/` vs `internal/` boundary unclear | LOW | Some functions in `host/`, some in `internal/engines/`, some inlined |
| 9 | Test coverage gap | MEDIUM | Monolith too large for effective unit testing |
| 10 | No Wisdom Economics layer | HIGH | WEALTH answers "profitable?" but not "dignified? sovereign? resilient?" |
| 11 | No Power Intelligence layer | HIGH | No detection of incentive asymmetry, capture risk, rent extraction |

---

## 2. TARGET ARCHITECTURE — 5-LAYER DECOMPOSITION

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEALTH FEDERATED DOMAIN                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 5: wealth_compat/                                  │  │
│  │  Legacy aliases, deprecated tool wrappers, migration shim │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 4: wealth_arifos_bridge/                           │  │
│  │  Transport to arifOS 888_JUDGE / VAULT999                 │  │
│  │  Evidence Contract sender, health probe, vault writer     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 3: wealth_mcp/                                     │  │
│  │  Agent-facing MCP tools, prompts, resources               │  │
│  │  FastMCP registration, transport, discovery               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 2: wealth_contracts/                               │  │
│  │  Output envelopes, epistemic tags, authority grammar      │  │
│  │  Universal WEALTH envelope, claim state, evidence quality │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 1: wealth_core/                                    │  │
│  │  Pure capital, risk, wisdom, and power engines            │  │
│  │  No MCP dependency, no I/O, pure computation              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Target Repo Layout

```
/root/WEALTH/
├── wealth_core/                    # Layer 1 — Pure engines (NO MCP, NO I/O)
│   ├── __init__.py
│   ├── capital/                    # Conservation, flow, gradient, energy, time, inertia
│   │   ├── __init__.py
│   │   ├── conservation.py         # NPV, IRR, PI, payback, net worth, ledger
│   │   ├── flow.py                 # Cashflow, runway, burn, triage, velocity
│   │   ├── gradient.py             # Spread, mispricing, pressure detection
│   │   ├── energy.py               # Productivity, efficiency, ROI
│   │   ├── time_discount.py        # NPV, IRR, payback, MIRR, compounding
│   │   └── inertia.py              # DSCR, leverage, strain, fragility
│   ├── risk/                       # Entropy, signal, correlation
│   │   ├── __init__.py
│   │   ├── entropy.py              # EMV, Monte Carlo, tail risk, asymmetry
│   │   ├── signal.py               # EVOI, schema validation, information value
│   │   └── correlation.py          # Coupling, guard checks, false confluence
│   ├── wisdom/                     # NEW — Wisdom Economics
│   │   ├── __init__.py
│   │   ├── dignity_impact.py       # Does this allocation preserve human dignity?
│   │   ├── sovereignty_risk.py     # Does this create dependency/capture?
│   │   ├── resilience_score.py     # Does this survive shocks?
│   │   ├── inequality_effect.py    # Does this widen or narrow inequality?
│   │   ├── ecological_cost.py      # What is the environmental externality?
│   │   └── optionality_preserve.py # Does this preserve future choices?
│   ├── power/                      # NEW — Power Intelligence
│   │   ├── __init__.py
│   │   ├── incentive_map.py        # Who benefits? Who carries downside?
│   │   ├── capture_detector.py     # Is this advice captured by interest?
│   │   ├── rent_extraction.py      # Is hidden rent being extracted?
│   │   ├── opacity_scorer.py       # How opaque is the valuation?
│   │   ├── coercion_detector.py    # Is time-pressure being used to force action?
│   │   └── rule_asymmetry.py       # Who can change the rules? Who cannot?
│   ├── game/                       # Multi-agent coordination
│   │   ├── __init__.py
│   │   ├── equilibrium.py          # Nash, cooperative, template-based
│   │   └── coordination.py         # Budget, preference, bargaining
│   ├── macro/                      # Field/market data engines
│   │   ├── __init__.py
│   │   ├── field.py                # WorldBank, FX, commodities, presets
│   │   └── market.py               # yfinance, klse-screener adapters
│   ├── governance/                 # Boundary, inequality, verdict
│   │   ├── __init__.py
│   │   ├── boundary.py             # Floors, policy, stewardship, legitimacy
│   │   ├── inequality.py           # 5-dimension inequality kernel
│   │   └── verdict.py              # Final allocation verdict
│   ├── stock/                      # D4 Stock Analysis
│   │   ├── __init__.py
│   │   ├── math_tools.py           # verify_trade_math, position_size, r_multiple
│   │   ├── risk_tools.py           # portfolio_exposure, bursa_cost_model
│   │   ├── behavior_tools.py       # tamak_detection, pre_trade_gate
│   │   ├── fundamentals.py         # 9 business reality invariants
│   │   ├── technical.py            # TAC-9 engine
│   │   ├── contrast.py             # Anomalous contrast, false confluence
│   │   ├── indicators.py           # RSI, MACD, Bollinger, etc.
│   │   ├── screener.py             # 9-point screener
│   │   ├── market_intelligence.py  # Thermodynamic state-space
│   │   └── governance_singularity.py # Calhoun Beautiful Ones
│   ├── personal/                   # D1 Personal Finance
│   │   ├── __init__.py
│   │   ├── cashflow.py             # Track, summary
│   │   ├── runway.py               # Calculate, burn
│   │   ├── networth.py             # Snapshot
│   │   ├── epf.py                  # EPF projection
│   │   └── zakat.py                # Zakat calculation
│   └── math/                       # Shared math primitives
│       ├── __init__.py
│       ├── kernel_math.py          # NPV, IRR, EMV, DSCR core math
│       ├── invariants.py           # G-score, Lyapunov, entropy
│       └── statistical.py          # Monte Carlo, correlation, distribution
│
├── wealth_contracts/               # Layer 2 — Output envelopes & schemas
│   ├── __init__.py
│   ├── envelope.py                 # Universal WEALTH output envelope
│   ├── epistemic.py                # Epistemic tags, evidence quality
│   ├── authority.py                # Authority grammar, execution boundaries
│   ├── claim_state.py              # Claim state machine (DRAFT→VALIDATED→SEALED)
│   └── schemas/
│       ├── capital_output.json     # JSON Schema for capital domain outputs
│       ├── risk_output.json        # JSON Schema for risk domain outputs
│       ├── wisdom_output.json      # JSON Schema for wisdom domain outputs
│       ├── power_output.json       # JSON Schema for power domain outputs
│       └── stock_output.json       # JSON Schema for stock analysis outputs
│
├── wealth_mcp/                     # Layer 3 — MCP surface (agent-facing)
│   ├── __init__.py
│   ├── server.py                   # FastMCP entry point (replaces monolith.py)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── capital_tools.py        # conservation, flow, gradient, energy, time, inertia
│   │   ├── risk_tools.py           # entropy, signal, correlation
│   │   ├── wisdom_tools.py         # NEW: dignity, sovereignty, resilience, inequality, ecological, optionality
│   │   ├── power_tools.py          # NEW: incentive, capture, rent, opacity, coercion, rule_asymmetry
│   │   ├── game_tools.py           # equilibrium, coordination
│   │   ├── macro_tools.py          # field, market data
│   │   ├── governance_tools.py     # boundary, inequality, verdict
│   │   ├── stock_tools.py          # D4 stock analysis (16 modes)
│   │   ├── personal_tools.py       # D1 personal finance (6 modes)
│   │   ├── synthesis_tools.py      # omni_wisdom, agent_path
│   │   └── registry_tools.py       # system_registry_status
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── capital_analysis.py     # Prompt: analyze capital allocation
│   │   ├── risk_assessment.py      # Prompt: assess risk profile
│   │   ├── wisdom_eval.py          # Prompt: evaluate wisdom dimensions
│   │   ├── power_audit.py          # Prompt: audit power dynamics
│   │   └── stock_review.py         # Prompt: review stock thesis
│   └── resources/
│       ├── __init__.py
│       ├── doctrine.py             # wealth://doctrine/valuation
│       ├── physics_invariants.py   # wealth://physics/invariants
│       ├── floor_policy.py         # wealth://governance/floors
│       └── epistemic_ladder.py     # wealth://epistemic/ladder
│
├── wealth_arifos_bridge/           # Layer 4 — arifOS integration
│   ├── __init__.py
│   ├── evidence_contract.py        # Universal Evidence Contract sender
│   ├── vault_bridge.py             # VAULT999 write/read
│   ├── health_probe.py             # arifOS health check + federation geometry
│   ├── organ_governance.py         # F1-F13 interception (moved from internal/)
│   └── nats_bridge.py              # NATS event emission
│
├── wealth_compat/                  # Layer 5 — Legacy compatibility
│   ├── __init__.py
│   ├── alias_dispatch.py           # v1→v2 alias mapping (~34 aliases)
│   ├── deprecated_wrappers.py      # 10 deprecated tool wrappers
│   └── migration_shim.py           # Gradual migration helpers
│
├── server.py                       # NEW: Thin entry point (imports from wealth_mcp)
├── internal/                       # DEPRECATED: kept during migration, deleted after
├── host/                           # KEPT: modular Python libraries (gradually migrated to wealth_core)
├── tests/
│   ├── core/                       # NEW: tests for wealth_core (pure, fast)
│   ├── contracts/                  # NEW: tests for wealth_contracts
│   ├── mcp/                        # NEW: tests for wealth_mcp surface
│   ├── bridge/                     # NEW: tests for wealth_arifos_bridge
│   ├── compat/                     # NEW: tests for wealth_compat
│   ├── golden/                     # NEW: golden hallucination tests
│   └── integration/                # Existing integration tests
├── canon/                          # KEPT: constitutional specs
├── capitalx/                       # KEPT: constitutional capital pricing
├── pyproject.toml                  # UPDATED: new package structure
└── Makefile                        # UPDATED: new test targets
```

---

## 3. UNIVERSAL WEALTH ENVELOPE

Every public WEALTH MCP tool MUST return this envelope. No exceptions.

```python
# wealth_contracts/envelope.py

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
from enum import Enum

class EpistemicTag(str, Enum):
    """F2 TRUTH: label every claim with its epistemic strength."""
    OBSERVED = "OBSERVED"        # Direct measurement (price, rate, balance)
    DERIVED = "DERIVED"          # Computed from observed data (NPV, IRR)
    INTERPRETED = "INTERPRETED"  # Inferred from patterns (trend, regime)
    SPECULATED = "SPECULATED"    # Hypothesis without sufficient evidence
    ASSUMED = "ASSUMED"          # Input parameter, not verified

class ClaimState(str, Enum):
    """Where is this claim in the governance pipeline?"""
    DRAFT = "DRAFT"              # Initial computation
    QC_VERIFIED = "QC_VERIFIED"  # Passed data quality checks
    VALIDATED = "VALIDATED"      # Passed constitutional review
    SEALED = "SEALED"            # Irreversibly written to VAULT999
    CHALLENGED = "CHALLENGED"    # Competing claim exists
    VOID = "VOID"                # Rejected by governance

class EvidenceQuality(str, Enum):
    """How strong is the evidence behind this output?"""
    STRONG = "STRONG"            # Multiple corroborating sources
    MODERATE = "MODERATE"        # Single reliable source
    WEAK = "WEAK"                # Inferred or analogical
    MISSING = "MISSING"          # No evidence provided
    CONFLICTED = "CONFLICTED"    # Evidence contradicts itself

class ExecutionAuthority(str, Enum):
    """Can this output be acted upon?"""
    OBSERVATION = "OBSERVATION"  # Read-only, no action
    RECOMMENDATION = "RECOMMENDATION"  # Suggests action, requires human approval
    ADVISORY = "ADVISORY"        # Strong suggestion, needs 888_HOLD
    BLOCKED = "BLOCKED"          # Action explicitly forbidden

class MissingInput(BaseModel):
    """What evidence would strengthen this output?"""
    name: str
    description: str
    impact_if_obtained: str  # "Would upgrade epistemic tag from SPECULATED to DERIVED"

class UncertaintyBand(BaseModel):
    """Uncertainty range for numerical outputs."""
    p10: Optional[float] = None   # Optimistic
    p50: Optional[float] = None   # Median
    p90: Optional[float] = None   # Pessimistic
    distribution: str = "unknown" # lognormal, normal, triangular, unknown

class WisdomDimension(BaseModel):
    """NEW: Wisdom Economics dimension score."""
    dimension: str                # dignity, sovereignty, resilience, inequality, ecological, optionality
    score: float                  # 0.0–1.0
    evidence: str                 # Why this score
    epistemic_tag: EpistemicTag

class PowerDimension(BaseModel):
    """NEW: Power Intelligence dimension score."""
    dimension: str                # incentive_asymmetry, capture_risk, rent_extraction, opacity, coercion, rule_asymmetry
    risk_level: str               # LOW, MEDIUM, HIGH, CRITICAL
    evidence: str
    who_benefits: str
    who_carries_downside: str

class WealthEnvelope(BaseModel):
    """
    Universal WEALTH output envelope.
    Every public MCP tool returns this.
    LLM-agnostic. Model proposes. MCP contract disciplines.
    """
    # === IDENTITY ===
    tool_name: str                          # Which tool produced this
    tool_version: str = "2026.06.15"        # Tool version
    domain: str                             # capital, risk, wisdom, power, game, macro, governance, stock, personal
    
    # === RESULT ===
    result: Any                             # The actual computation result
    result_type: str                        # "scalar", "vector", "matrix", "table", "narrative"
    
    # === EPISTEMOLOGY ===
    epistemic_tag: EpistemicTag             # OBSERVED, DERIVED, INTERPRETED, SPECULATED, ASSUMED
    claim_state: ClaimState = ClaimState.DRAFT
    evidence_quality: EvidenceQuality = EvidenceQuality.MISSING
    uncertainty_band: Optional[UncertaintyBand] = None
    
    # === WISDOM ECONOMICS (NEW) ===
    wisdom_dimensions: Optional[List[WisdomDimension]] = None
    dignity_impact: Optional[str] = None    # "preserves", "erodes", "unclear"
    sovereignty_effect: Optional[str] = None # "strengthens", "weakens", "neutral"
    
    # === POWER INTELLIGENCE (NEW) ===
    power_dimensions: Optional[List[PowerDimension]] = None
    capture_risk_level: Optional[str] = None # LOW, MEDIUM, HIGH, CRITICAL
    who_benefits: Optional[str] = None
    who_carries_downside: Optional[str] = None
    
    # === AUTHORITY ===
    execution_authorized: bool = False       # NEVER True from WEALTH
    execution_authority: ExecutionAuthority = ExecutionAuthority.OBSERVATION
    human_final_authority: str = "Arif"      # F13 SOVEREIGN
    requires_888_hold: bool = False          # Does this need judge review?
    
    # === PROVENANCE ===
    source_attribution: List[str] = []       # Where did the data come from?
    computation_timestamp: str = ""          # ISO 8601
    session_id: Optional[str] = None
    actor_id: Optional[str] = None
    
    # === MISSING EVIDENCE ===
    missing_inputs: List[MissingInput] = []  # What would strengthen this?
    
    # === METADATA ===
    metadata: Dict[str, Any] = {}            # Tool-specific extra data
    warnings: List[str] = []                 # Non-blocking warnings
    errors: List[str] = []                   # Blocking errors (result may be None)
```

---

## 4. NEW DOMAINS — WISDOM ECONOMICS & POWER INTELLIGENCE

### 4.1 Wisdom Economics (`wealth_core/wisdom/`)

WEALTH must answer not just "Is this profitable?" but "Is this wise?"

| Dimension | Question | Engine |
|-----------|----------|--------|
| **Dignity Impact** | Does this allocation preserve human dignity? | `dignity_impact.py` |
| **Sovereignty Risk** | Does this create dependency or capture? | `sovereignty_risk.py` |
| **Resilience Score** | Does this survive shocks? | `resilience_score.py` |
| **Inequality Effect** | Does this widen or narrow inequality? | `inequality_effect.py` |
| **Ecological Cost** | What is the environmental externality? | `ecological_cost.py` |
| **Optionality Preserve** | Does this preserve future choices? | `optionality_preserve.py` |

**New MCP tools:**

```python
# wealth_mcp/tools/wisdom_tools.py

@mcp.tool(name="wealth_wisdom_evaluate")
async def wealth_wisdom_evaluate(
    proposal: str,           # What is being proposed?
    capital_type: str,       # financial, temporal, cognitive, social, ecological
    context: dict = None,    # Additional context
) -> WealthEnvelope:
    """
    Evaluate a capital allocation proposal across all 6 wisdom dimensions.
    Returns dignity impact, sovereignty effect, resilience score,
    inequality effect, ecological cost, and optionality preservation.
    
    This tool does NOT judge. It computes wisdom dimensions.
    arifOS judges. Arif decides.
    """
```

### 4.2 Power Intelligence (`wealth_core/power/`)

The missing AGI-grade economic layer. Detects the invisible geometry of power in any capital decision.

| Dimension | Question | Engine |
|-----------|----------|--------|
| **Incentive Map** | Who benefits? Who carries downside? | `incentive_map.py` |
| **Capture Detector** | Is this advice captured by interest? | `capture_detector.py` |
| **Rent Extraction** | Is hidden rent being extracted? | `rent_extraction.py` |
| **Opacity Scorer** | How opaque is the valuation? | `opacity_scorer.py` |
| **Coercion Detector** | Is time-pressure being used to force action? | `coercion_detector.py` |
| **Rule Asymmetry** | Who can change the rules? Who cannot? | `rule_asymmetry.py` |

**New MCP tools:**

```python
# wealth_mcp/tools/power_tools.py

@mcp.tool(name="wealth_power_audit")
async def wealth_power_audit(
    scenario: str,           # What scenario to audit
    actors: list = None,     # Known actors in the scenario
    context: dict = None,
) -> WealthEnvelope:
    """
    Audit the power dynamics of a capital scenario.
    Returns incentive map, capture risk, rent extraction score,
    opacity level, coercion signals, and rule asymmetry.
    
    Catches AI advice that sounds balanced but hides weak evidence
    or dangerous allocation geometry.
    """

@mcp.tool(name="wealth_capture_scan")
async def wealth_capture_scan(
    advice_text: str,        # AI-generated advice to scan
    source_model: str = "",  # Which model produced this
) -> WealthEnvelope:
    """
    Scan AI-generated financial advice for capture signals.
    Detects: hidden incentives, omitted downsides, false precision,
    time-pressure language, authority claims without evidence.
    """
```

---

## 5. PUBLIC MCP TOOL PRESERVATION LIST

These 19 tools MUST continue to work throughout migration. No breaking changes.

| Current Tool | Target Location | Notes |
|-------------|-----------------|-------|
| `wealth_system_registry_status` | `wealth_mcp/tools/registry_tools.py` | Meta — registry truth |
| `wealth_omni_wisdom` | `wealth_mcp/tools/synthesis_tools.py` | Synthesis — absorb wisdom + power |
| `wealth_agent_path` | `wealth_mcp/tools/synthesis_tools.py` | Meta — intent routing |
| `wealth_survival_engine` | `wealth_mcp/tools/capital_tools.py` | Flow/survival |
| `wealth_conservation_capital` | `wealth_mcp/tools/capital_tools.py` | Conservation |
| `wealth_flow_liquidity` | `wealth_mcp/tools/capital_tools.py` | Flow |
| `wealth_gradient_price` | `wealth_mcp/tools/capital_tools.py` | Gradient |
| `wealth_entropy_risk` | `wealth_mcp/tools/risk_tools.py` | Entropy |
| `wealth_energy_productivity` | `wealth_mcp/tools/capital_tools.py` | Energy |
| `wealth_time_discount` | `wealth_mcp/tools/capital_tools.py` | Time |
| `wealth_inertia_leverage` | `wealth_mcp/tools/capital_tools.py` | Inertia |
| `wealth_field_macro` | `wealth_mcp/tools/macro_tools.py` | Field |
| `wealth_signal_information` | `wealth_mcp/tools/risk_tools.py` | Signal |
| `wealth_game_coordination` | `wealth_mcp/tools/game_tools.py` | Game |
| `wealth_boundary_governance` | `wealth_mcp/tools/governance_tools.py` | Boundary |
| `wealth_governance_verdict` | `wealth_mcp/tools/governance_tools.py` | Verdict |
| `wealth_inequality_kernel` | `wealth_mcp/tools/governance_tools.py` | Inequality |
| `wealth_personal_finance` | `wealth_mcp/tools/personal_tools.py` | D1 |
| `wealth_market_data` | `wealth_mcp/tools/macro_tools.py` | D3 |
| `wealth_stock_analysis` | `wealth_mcp/tools/stock_tools.py` | D4 |

**New tools to add:**

| New Tool | Location | Purpose |
|----------|----------|---------|
| `wealth_wisdom_evaluate` | `wealth_mcp/tools/wisdom_tools.py` | 6-dimension wisdom evaluation |
| `wealth_power_audit` | `wealth_mcp/tools/power_tools.py` | Power dynamics audit |
| `wealth_capture_scan` | `wealth_mcp/tools/power_tools.py` | AI advice capture detection |

---

## 6. NON-NEGOTIABLE TESTS

### 6.1 Golden Hallucination Tests (`tests/golden/`)

```python
# tests/golden/test_no_hallucinated_numbers.py
"""
Every numerical output must trace to an input or a named constant.
No fabricated precision. No invented rates. No phantom percentages.
"""

def test_npv_traces_to_inputs():
    """NPV output must reference actual cash flows and discount rate."""
    result = compute_npv(cash_flows=[100, 200, 300], discount_rate=0.10)
    assert result.source_cash_flows == [100, 200, 300]
    assert result.source_discount_rate == 0.10
    assert result.epistemic_tag == "DERIVED"

def test_no_phantom_percentage():
    """No tool may return a percentage without source attribution."""
    envelope = wealth_entropy_risk(mode="emv", scenarios=[...])
    for value in envelope.result.values():
        if isinstance(value, float) and 0 <= value <= 1:
            assert envelope.source_attribution, f"Percentage {value} has no source"

def test_fx_rate_has_source():
    """FX rates must attribute to Frankfurter API or mark as STALE."""
    envelope = wealth_market_data(mode="fx", base="USD", targets="MYR")
    assert "frankfurter" in str(envelope.source_attribution).lower() or \
           envelope.epistemic_tag == "ASSUMED"
```

### 6.2 Registry Truth Tests (`tests/mcp/`)

```python
# tests/mcp/test_registry_truth.py
"""
Every tool in WEALTH_PUBLIC_TOOL_ORDER must be callable.
No phantom tools. No ghost aliases. No silent failures.
"""

def test_all_public_tools_callable():
    """Every public tool must respond to a safe probe call."""
    for tool_name in WEALTH_PUBLIC_TOOL_ORDER:
        result = call_tool_safe(tool_name, {"mode": "health"})
        assert result is not None, f"{tool_name} returned None"
        assert "error" not in str(result).lower() or "Unknown tool" not in str(result)

def test_no_phantom_tools():
    """No tool may be listed in registry but return 'Unknown tool'."""
    registered = list_registered_tools()
    for tool in registered:
        result = call_tool_safe(tool, {})
        assert "Unknown tool" not in str(result), f"Phantom tool: {tool}"

def test_known_missing_fails_loudly():
    """_KNOWN_MISSING tools must either register or be removed from PUBLIC_TOOL_ORDER."""
    for tool in _KNOWN_MISSING:
        assert tool not in WEALTH_PUBLIC_TOOL_ORDER or \
               tool in list_registered_tools(), \
               f"{tool} is in PUBLIC_TOOL_ORDER but not registered"
```

### 6.3 Envelope Contract Tests (`tests/contracts/`)

```python
# tests/contracts/test_envelope_contract.py
"""
Every public tool must return a valid WealthEnvelope.
No bare dicts. No raw numbers. No unstructured output.
"""

def test_every_tool_returns_envelope():
    """All public tools must return WealthEnvelope."""
    for tool_name in WEALTH_PUBLIC_TOOL_ORDER:
        result = call_tool_safe(tool_name, get_safe_args(tool_name))
        envelope = WealthEnvelope.model_validate(result)
        assert envelope.tool_name == tool_name
        assert envelope.epistemic_tag in EpistemicTag.__members__.values()
        assert envelope.execution_authorized == False  # WEALTH never authorizes

def test_epistemic_tag_present():
    """No output without epistemic tag."""
    envelope = call_tool("wealth_conservation_capital", {"mode": "state"})
    assert envelope.epistemic_tag is not None
    assert envelope.epistemic_tag != ""

def test_execution_never_authorized():
    """WEALTH computes. It never authorizes execution."""
    for tool_name in WEALTH_PUBLIC_TOOL_ORDER:
        result = call_tool_safe(tool_name, get_safe_args(tool_name))
        envelope = WealthEnvelope.model_validate(result)
        assert envelope.execution_authorized == False, \
               f"{tool_name} authorized execution — VIOLATION"
```

### 6.4 Wisdom & Power Tests (`tests/core/`)

```python
# tests/core/test_wisdom_dimensions.py
"""
Wisdom Economics must return all 6 dimensions.
No dimension may be missing without explanation.
"""

def test_wisdom_returns_all_dimensions():
    result = compute_wisdom(
        proposal="Invest 80% of portfolio in single tech stock",
        capital_type="financial"
    )
    dimensions = {d.dimension for d in result.wisdom_dimensions}
    assert dimensions == {"dignity", "sovereignty", "resilience",
                          "inequality", "ecological", "optionality"}

def test_power_audit_detects_capture():
    result = compute_power_audit(
        scenario="AI recommends buying stock X because it's undervalued",
        actors=["AI model", "broker", "investor"]
    )
    assert result.capture_risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert result.who_benefits is not None
    assert result.who_carries_downside is not None
```

### 6.5 Transport Tests (`tests/bridge/`)

```python
# tests/bridge/test_arifos_bridge.py
"""
WEALTH → arifOS bridge must work.
Evidence Contract must be well-formed.
VAULT999 writes must be hash-chained.
"""

def test_evidence_contract_well_formed():
    """Evidence Contract sent to arifOS must have all required fields."""
    contract = build_evidence_contract(
        tool_name="wealth_conservation_capital",
        result={"net_worth": 100000},
        epistemic_tag="DERIVED"
    )
    assert "tool_name" in contract
    assert "epistemic_tag" in contract
    assert "claim_state" in contract
    assert "evidence_quality" in contract

def test_health_probe_reaches_arifos():
    """WEALTH health check must reach arifOS kernel."""
    result = probe_arifos_health()
    assert result.status == "ALIVE" or result.status == "DEGRADED_NOT_FAILED"
```

---

## 7. MCP TRANSPORT CONTRACT

### 7.1 What Changes

| Aspect | Current | Target |
|--------|---------|--------|
| Entry point | `internal/monolith.py` (17K lines) | `server.py` (thin) → `wealth_mcp/server.py` |
| Tool registration | 86 `@mcp.tool` in one file | ~22 `@mcp.tool` across 11 files |
| Output format | Bare dicts, raw numbers | `WealthEnvelope` always |
| Mode routing | String comparison, no validation | Enum-validated mode dispatch |
| Registry cleanup | `mcp._local_provider._components` hack | FastMCP public API only |
| Prompts | 0 | 5 reasoning workflows |
| Resources | 0 callable | 4 readable contexts |

### 7.2 What Stays the Same

| Aspect | Value | Why |
|--------|-------|-----|
| Port | 18082 | systemd unit unchanged |
| Transport | streamable-http, stateless | MCP spec compliant |
| Auth | localhost-only | Security doctrine |
| Public tools | 19 (preserved) + 3 (new) | No breaking changes |
| Cloudflare Tunnel | `wealth.arif-fazil.com/mcp` | External access unchanged |
| Dependencies | pyproject.toml | Same Python deps |

### 7.3 New `server.py` (Thin Entry Point)

```python
# /root/WEALTH/server.py — NEW thin entry point
"""
WEALTH Federated Domain — MCP Server Entry Point.

This replaces internal/monolith.py as the canonical entry point.
It imports from wealth_mcp/ and exposes the same MCP surface.
"""

from wealth_mcp.server import create_mcp_server

mcp = create_mcp_server()

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount
    
    app = mcp.http_app(
        transport="streamable-http",
        stateless_http=True,
        json_response=True,
    )
    
    uvicorn.run(app, host="127.0.0.1", port=18082)
```

---

## 8. ARIFOS BRIDGE CONTRACT

### 8.1 Evidence Contract

Every WEALTH tool call that produces a judgment-eligible result MUST send an Evidence Contract to arifOS.

```python
# wealth_arifos_bridge/evidence_contract.py

class EvidenceContract(BaseModel):
    """What WEALTH sends to arifOS after computing."""
    tool_name: str
    domain: str
    epistemic_tag: str          # OBSERVED, DERIVED, INTERPRETED, SPECULATED
    claim_state: str            # DRAFT, QC_VERIFIED, VALIDATED
    evidence_quality: str       # STRONG, MODERATE, WEAK, MISSING, CONFLICTED
    result_summary: str         # Human-readable summary
    numerical_claims: dict      # Key numerical outputs
    uncertainty_band: dict      # P10, P50, P90
    missing_inputs: list        # What would strengthen this
    source_attribution: list    # Where data came from
    wisdom_dimensions: list     # NEW: wisdom scores
    power_dimensions: list      # NEW: power audit
    requires_888_hold: bool     # Does this need judge review?
    timestamp: str              # ISO 8601
```

### 8.2 VAULT999 Write Contract

```python
# wealth_arifos_bridge/vault_bridge.py

async def seal_to_vault(
    payload: str,
    actor_id: str = "WEALTH",
    session_id: str = None,
    ack_irreversible: bool = False,
) -> dict:
    """
    Seal a computation result to VAULT999.
    Only for SEALED claims. Requires ack_irreversible=True.
    Routes to arifOS arif_seal tool.
    """
```

---

## 9. PHASED MIGRATION PLAN

### Phase 0: Preparation (Day 1)

```bash
# 1. Create feature branch
cd /root/WEALTH && git checkout -b feat/federated-domain

# 2. Create new directory structure
mkdir -p wealth_core/{capital,risk,wisdom,power,game,macro,governance,stock,personal,math}
mkdir -p wealth_contracts/schemas
mkdir -p wealth_mcp/{tools,prompts,resources}
mkdir -p wealth_arifos_bridge
mkdir -p wealth_compat
mkdir -p tests/{core,contracts,mcp,bridge,compat,golden,integration}

# 3. Create __init__.py files
find wealth_core wealth_contracts wealth_mcp wealth_arifos_bridge wealth_compat -type d -exec touch {}/__init__.py \;
```

### Phase 1: Contracts (Day 2-3)

1. Implement `wealth_contracts/envelope.py` (WealthEnvelope)
2. Implement `wealth_contracts/epistemic.py` (EpistemicTag, ClaimState, EvidenceQuality)
3. Implement `wealth_contracts/authority.py` (ExecutionAuthority)
4. Write `tests/contracts/test_envelope_contract.py`
5. **VERIFY:** All contract tests pass

### Phase 2: Core Engines (Day 4-10)

1. Extract `wealth_core/math/` from `internal/kernel_math.py` and `internal/invariants.py`
2. Extract `wealth_core/capital/` from `internal/engines/canonical_tools.py`
3. Extract `wealth_core/risk/` from `internal/engines/canonical_tools.py`
4. Extract `wealth_core/stock/` from `internal/stock/`
5. Extract `wealth_core/personal/` from `internal/personal_finance.py`
6. Extract `wealth_core/game/` from `host/coordination/`
7. Extract `wealth_core/macro/` from `internal/market_data.py` and `host/ingest/`
8. Extract `wealth_core/governance/` from `internal/governance.py` and `host/governance/`
9. **NEW:** Implement `wealth_core/wisdom/` (6 engines)
10. **NEW:** Implement `wealth_core/power/` (6 engines)
11. Write `tests/core/` for each engine
12. **VERIFY:** All core tests pass

### Phase 3: MCP Surface (Day 11-14)

1. Implement `wealth_mcp/server.py` (FastMCP entry point)
2. Implement `wealth_mcp/tools/` (11 tool files, 22 tools)
3. Implement `wealth_mcp/prompts/` (5 reasoning workflows)
4. Implement `wealth_mcp/resources/` (4 readable contexts)
5. Write `tests/mcp/test_registry_truth.py`
6. **VERIFY:** All MCP tests pass, all 22 tools callable

### Phase 4: Bridge & Compat (Day 15-17)

1. Implement `wealth_arifos_bridge/` (evidence contract, vault bridge, health probe)
2. Implement `wealth_compat/` (alias dispatch, deprecated wrappers)
3. Write `tests/bridge/` and `tests/compat/`
4. **VERIFY:** arifOS can still call all WEALTH tools, aliases still work

### Phase 5: Integration & Cutover (Day 18-21)

1. Implement new `server.py` (thin entry point)
2. Update `pyproject.toml` (new package structure)
3. Update `Makefile` (new test targets)
4. Run full test suite: `pytest tests/ -q --tb=short`
5. Run golden hallucination tests
6. Run registry truth tests
7. Update systemd unit to use new `server.py`
8. **VERIFY:** `curl localhost:18082/health` returns healthy
9. **VERIFY:** arifOS can attest WEALTH organ
10. **VERIFY:** All 22 public tools callable via MCP

### Phase 6: Cleanup (Day 22-28)

1. Move `internal/` to `_archive/internal_legacy/`
2. Move `host/` modules to `wealth_core/` (gradual)
3. Remove deprecated tools from `wealth_compat/`
4. Update AGENTS.md, SPEC.md, canon/ docs
5. Commit: `feat(wealth): federated domain — 5-layer decomposition`
6. Push to `origin/main`

---

## 10. COMMIT PLAN

```
feat(wealth): add wealth_contracts — universal envelope + epistemic tags
feat(wealth): add wealth_core/math — pure math primitives
feat(wealth): add wealth_core/capital — conservation, flow, gradient, energy, time, inertia
feat(wealth): add wealth_core/risk — entropy, signal, correlation
feat(wealth): add wealth_core/wisdom — NEW: 6-dimension wisdom economics
feat(wealth): add wealth_core/power — NEW: 6-dimension power intelligence
feat(wealth): add wealth_core/stock — D4 stock analysis engines
feat(wealth): add wealth_core/personal — D1 personal finance engines
feat(wealth): add wealth_core/game — multi-agent coordination
feat(wealth): add wealth_core/macro — field, market data
feat(wealth): add wealth_core/governance — boundary, inequality, verdict
feat(wealth): add wealth_mcp — MCP tools, prompts, resources
feat(wealth): add wealth_arifos_bridge — evidence contract, vault, health
feat(wealth): add wealth_compat — legacy aliases, deprecated wrappers
feat(wealth): add server.py — thin entry point replacing monolith
feat(wealth): add golden hallucination tests
feat(wealth): add registry truth tests
feat(wealth): add envelope contract tests
chore(wealth): update pyproject.toml for new package structure
chore(wealth): update Makefile for new test targets
chore(wealth): update AGENTS.md for federated domain
chore(wealth): archive internal/ monolith
```

---

## 11. EXACT FIRST COMMAND FOR CODING AGENT

```bash
cd /root/WEALTH && git checkout -b feat/federated-domain && mkdir -p wealth_core/{capital,risk,wisdom,power,game,macro,governance,stock,personal,math} wealth_contracts/schemas wealth_mcp/{tools,prompts,resources} wealth_arifos_bridge wealth_compat tests/{core,contracts,mcp,bridge,compat,golden,integration} && find wealth_core wealth_contracts wealth_mcp wealth_arifos_bridge wealth_compat -type d -exec touch {}/__init__.py \; && echo "Directory structure created. Begin Phase 1: Contracts."
```

---

## 12. SUCCESS CRITERIA

| Criterion | Verification |
|-----------|-------------|
| All 19 existing tools still work | `pytest tests/mcp/test_registry_truth.py` |
| No phantom tools | Registry truth test |
| No hallucinated numbers | Golden hallucination tests |
| Every output has epistemic tag | Envelope contract tests |
| WEALTH never authorizes execution | Envelope contract tests |
| arifOS can attest WEALTH | `arif_organ_attest(organ_id="WEALTH")` returns ALIVE |
| Wisdom dimensions present on demand | `tests/core/test_wisdom_dimensions.py` |
| Power audit catches capture | `tests/core/test_power_audit.py` |
| Monolith is gone | `wc -l internal/monolith.py` → file archived |
| New server starts healthy | `curl localhost:18082/health` |

---

## 13. WHAT THIS ARTIFACT DOES NOT DO

- Does not mutate any repo
- Does not change systemd units (yet)
- Does not remove `internal/monolith.py` (archives it)
- Does not change the public MCP tool names
- Does not change the port or transport
- Does not touch arifOS, A-FORGE, AAA, GEOX, or WELL
- Does not make capital allocation decisions
- Does not authorize execution

**WEALTH computes. arifOS judges. AAA displays. A-FORGE executes. ARIF decides.**

---

*DITEMPA BUKAN DIBERI — Forged, not given.*  
*FORGE (000Ω) · 2026-06-15 · C2 Execute*
