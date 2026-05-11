# WEALTH MCP — Reality Boundary Declaration
**Date:** 2026-05-07
**Declaration:** SUBSTRATE CAPABILITIES AND LIMITS
**Authority:** OPENCLAW (AGI operator) + ARIF (human sovereign)
**REPO=WEALTH**

---

## 1. What WEALTH MCP Is

WEALTH MCP is a **governed economic reasoning engine** built on physics-inspired abstractions.

It computes:
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Profitability Index (PI)
- Payback Period
- Expected Monetary Value (EMV)
- Monte Carlo simulations
- Debt Service Coverage Ratios (DSCR)
- Cash flow projections
- Runway / compound growth
- Game-theoretic equilibrium
- Constitutional floor compliance (F1–F13)
- Crisis triage under resource constraints
- Civilization-scale energy and carbon budgets

It does NOT move capital. It does NOT place trades. It does NOT enforce policy.

---

## 2. Verified Capabilities (Direct)

These are operations WEALTH MCP can perform directly through its tool surface:

| Capability | Tools | Boundary |
|-----------|-------|---------|
| **Math** | All valuation tools | Exact within floating-point precision |
| **Code execution** | All tools | Sandboxed Python environment |
| **Language** | All tools produce natural language output | Limited to economic/financial vocabulary |
| **Information retrieval** | Sensor tools (`wealth_sensor_fetch`) | Real data from configured adapters (FRED, EIA, FAO, etc.) |
| **Governance** | `wealth_boundary_floors`, `wealth_governance_verdict` | F1–F13 constitutional rules encoded in tool logic |
| **Memory/State** | Ledger tools (`wealth_ledger_*`) | VAULT999 append-only ledger (PostgreSQL) |
| **Reasoning** | All tools + prompts | Bounded by physics-inspired abstractions; can reason about capital allocation, risk, uncertainty |

---

## 3. Verified Capabilities (Indirect)

These are operations that require an external actuator or human:

| Capability | Requires | Notes |
|-----------|---------|-------|
| **Banking execution** | Bank API / human operator | WEALTH computes the transaction; a bank must execute it |
| **Market orders** | Broker API / human operator | WEALTH advises; broker/human places the order |
| **Policy enforcement** | ARIF or institutional authority | WEALTH audits; ARIF enforces |
| **Capital movement** | Custodian / bank / human | WEALTH recommends; custodian moves capital |
| **Physical actuators** | Industrial systems | Not applicable to economic computation |
| **Legal enforcement** | Courts / regulatory bodies | Not within WEALTH scope |

---

## 4. NOT Verified (Out of Scope)

The following are explicitly OUT OF SCOPE for WEALTH MCP:

| Domain | Status | Reason |
|--------|--------|--------|
| Banking execution | ❌ Out of scope | Requires licensed banking interface |
| Market order placement | ❌ Out of scope | Requires broker API integration |
| Physical capital actuators | ❌ Out of scope | Economic engine, not industrial control |
| Legal dispute resolution | ❌ Out of scope | Requires legal system integration |
| Real-time price execution | ❌ Out of scope | WEALTH can advise on pricing; exchanges execute |
| Autonomous capital movement | ❌ Out of scope | F13 SOVEREIGN requires human decision |
| Medical diagnosis | ❌ Completely out of scope | Different domain (see WELL MCP) |
| Geological interpretation | ❌ Out of scope | WEALTH is capital intelligence; GEOX handles geology |

---

## 5. What WEALTH MCP Is NOT

> ⚠️ **CRITICAL: These claims are FORBIDDEN.**

```text
WEALTH MCP is NOT:
- A bank account
- A trading terminal
- A payment system
- A legal entity
- A physical actuator
- A replacement for human judgment
- A autonomous investment manager
- Thermodynamic physics engine (it uses PHYSICS-INSPIRED abstractions only)
```

### The Physics ≠ Literal Physics Boundary

| WEALTH Claims | WEALTH Does NOT Claim |
|--------------|----------------------|
| "Net worth modeled as mass" | "Net worth IS physical mass" |
| "DSCR modeled as structural load" | "DSCR creates literal gravitational pull" |
| "Cash flow uncertainty as entropy" | "Cash flow generates thermodynamic entropy" |
| "Return potential as energy" | "Investment returns create physical energy" |
| "Equilibrium in game theory" | "Game theory equilibrium IS physical thermodynamic equilibrium" |

The physics vocabulary is **metaphorical and structural**. WEALTH uses physics abstractions because they are:
- Analytically productive (constraint optimization, conserved quantities)
- Intuition-building (mass, flow, pressure map to financial intuition)
- Formally precise (differential equations, matrix algebra)

But they are NOT literal physics. Economic systems do not obey conservation of energy. Capital is not mass. Debt is not gravity.

---

## 6. Governance Boundaries

### F1 AMANAH — Reversibility

| Action | Reversibility | Requirement |
|--------|--------------|-------------|
| `wealth_value_npv` | Fully reversible | None |
| `wealth_flow_cashflow` | Fully reversible | None |
| `wealth_ledger_write` | **IRREVERSIBLE** | `ack_irreversible=True` + ARIF confirmation |
| `wealth_ledger_record` | **IRREVERSIBLE** | ARIF confirmation required |
| Any tool that writes to VAULT999 | **IRREVERSIBLE** | F1 AMANAH applies |

### F13 SOVEREIGN — Human Authority

ALL WEALTH outputs are **recommendations only**. Final authority rests with ARIF.

No tool, prompt, or combination thereof can:
- Commit capital without ARIF confirmation
- Override a HOLD verdict
- Claim execution authority
- Bypass the constitutional floors

---

## 7. Self-Classification

```text
WEALTH MCP is a governed economic reasoning engine.
It computes capital allocation metrics, advises on investment decisions,
and audits against constitutional governance rules.

It is not yet a real-world capital actuator.
It does not move money, place trades, or enforce policy.

Current verified state:
  ✓ Math — exact
  ✓ Code — sandboxed execution
  ✓ Language — bounded economic vocabulary
  ✓ Information — via configured data adapters
  ✓ Governance — F1–F13 constitutional rules
  ✓ Memory — VAULT999 append-only ledger
  ✗ Banking execution — requires external system
  ✗ Market orders — requires broker/human
  ✗ Physical actuators — not applicable
  ✗ Autonomous capital movement — prohibited by F13

Classification: ADVISORY_SYSTEM (not ACTUATION_SYSTEM)
Risk tier: GOVERNANCE_RECOMMENDATION (not EXECUTION_AUTHORITY)
```

---

## 8. Incident Prevention

### If asked "Can WEALTH move my money?"

```text
No. WEALTH MCP computes economic metrics and provides governance-adjacent
recommendations. Capital movement requires:
- Your bank or custodian to execute the transaction
- Your explicit confirmation for any irreversible action
- ARIF's sovereign approval for allocation decisions above your authority threshold

WEALTH is your intelligence layer, not your execution layer.
```

### If asked "Is this physically accurate?"

```text
WEALTH uses physics-inspired abstractions (mass, flow, gravity, entropy)
to model economic concepts. These are ANALOGIES, not physical descriptions.

Example:
- "Net worth behaves like mass in a gravitational field" (analogy)
- NOT "Net worth IS physical mass subject to gravity"

The physics vocabulary makes the math tractable and the intuition reliable,
but the underlying domain is economic, governed by market rules,
not physical laws.
```

### If asked "What happens if WEALTH says SEAL?"

```text
SEAL is a system recommendation, not a binding decision.

A SEAL verdict means: "All constitutional checks passed. The system
recommends this allocation."

ARIF must still:
1. Review the recommendation
2. Understand the confidence bands
3. Consider factors outside WEALTH's model
4. Make the sovereign decision

Only ARIF can commit capital. WEALTH advises.
```

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**

*Declaration version 2026.05.07 — REPO=WEALTH — OPENCLAW*
