<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.09.21 (P1 — WEALTH-IDENTITY-PIVOT)
last_verified: 2026-09-21T02:01:00Z
apex_zen: arifOS = ingress + authority · WEALTH = evidence · arifOS = judgment · F13 = decision

surface:
  canonical_primitives: 13        # Ω00 + Ω01-Ω12
  societal_extensions: 2          # inequality, role scarcity
  infrastructure_tools: 2         # health, registry
  compatibility_aliases: 14       # capital_* legacy names (excluded from canonical)
  total_external_visible: 17

authority_ceiling: 555_COMPUTE_ONLY
truth_rule: live :18082/health + tools/list beat any static count in prose

doctrine:
  - WEALTH models capital consequences under uncertainty
  - Analyst (WEALTH) ≠ Judge (arifOS). WEALTH never issues constitutional verdicts.
  - Direct :18082 is engineering/diagnostic. Recommended user path:
    Client → arifOS → WEALTH → arifOS → Human.
  - "Real-time" is misleading; WEALTH reports Live/LatestAvailable with
    source, timestamp, cache_age_seconds, and staleness_class on every
    market/macro output.
-->

# WEALTH — Capital Consequence Intelligence

> **Capital consequence infrastructure, not investment advice.**
>
> WEALTH converts stocks, flows, prices, risk, productivity, time, leverage, macro conditions, information, incentives, governance, and path dependence into auditable capital evidence.
>
> *WEALTH computes. arifOS judges. A-FORGE executes approved actions. Humans remain sovereign.*

**Identity (P1 2026-09-21):**

```text
WEALTH : WorldState → CapitalConsequences        (not WorldState → InvestmentDecision)
```

**The 12-invariant Ω architecture** is the spine. NPV, RSI, Monte Carlo, backtest, ledger — these are *implementations* underneath the invariants, not the identity.

---

## Irreducible question

> **If capital moves this way, what follows — and how sure are we?**

WEALTH's job is to make the consequences of moving money *harder to hide*. It does not decide where money should go.

---

## The 12 Ω-invariants

| Ω    | Invariant | Question | Canonical name | Implementation |
|------|-----------|----------|----------------|----------------|
| Ω00  | Synthesis | Cross-dimensional roll-up → domain_assessment | `wealth_synthesize` | 12→1 roll-up; ADVISORY_ONLY |
| Ω01  | Mass      | What exists? | `wealth_conservation_capital` | assets / liabilities / reserves |
| Ω02  | Flow      | Where is money moving? | `wealth_flow_liquidity` | cash flow / burn / runway |
| Ω03  | Gradient  | What differential drives movement? | `wealth_gradient_price` | price pressure / spreads |
| Ω04  | Entropy   | How uncertain / disordered is it? | `wealth_entropy_risk` | tail risk / disorder |
| Ω05  | Energy    | What output does capital produce? | `wealth_energy_productivity` | output per capital input |
| Ω06  | Time      | What is future value worth now? | `wealth_time_discount` | NPV / IRR / decay |
| Ω07  | Inertia   | What makes the system hard to change? | `wealth_inertia_leverage` | leverage / fragility |
| Ω08  | Field     | What macro regime surrounds it? | `wealth_field_macro` | rates / FX / energy |
| Ω09  | Signal    | What information deserves belief? | `wealth_signal_information` | evidence quality / information value |
| Ω10  | Game      | What incentives shape behaviour? | `wealth_game_coordination` | incentives / bargaining |
| Ω11  | Boundary  | What constraints cannot be crossed? | `wealth_boundary_governance` | governance / stewardship |
| Ω12  | Hysteresis | How does history constrain the future? | `wealth_hysteresis_ledger` | path dependence / capital memory |

The Ω invariants are the *fundamentals*. NPV, RSI, MACD, Bollinger, PSAR, ATR, ADX, backtest, and entry planning are market-microstructure implementations underneath Ω08 (Field) and Ω09 (Signal).

---

## What WEALTH is becoming (vs what it was)

| Was | Becoming |
|-----|----------|
| "11 Tools · 18 Resources" | 13 canonical primitives + 2 extensions + 2 infrastructure |
| "AI-driven financial decision engine" | Capital consequence infrastructure |
| "Capital Diagnostics / Market Pulse / Entropy Modeling / Entry Planning / Backtest / Ledger" | Ω-invariant primitives (Mass / Flow / Gradient / Entropy / Energy / Time / Inertia / Field / Signal / Game / Boundary / Hysteresis) |
| Direct :18082 for clients | Recommended path: `Client → arifOS → WEALTH → arifOS → Human` |
| "Real-time FX, commodity, and stock indicators" | "Live and latest-available market/macro data through configured adapters, with source, timestamp, cache age, and staleness metadata" |
| "structural rot" | structural deterioration, incentive misalignment, and accumulating fragility |
| "WEALTH = truth about consequences" | WEALTH = evidence about capital consequences |
| `arifFlow — Witness Plane` | `arifFlow — metabolic telemetry` (FRAME = independent witness; VAULT999 = immutable record) |

---

## Why hysteresis deserves more prominence

Most finance systems model:

```
State_t
```

WEALTH is starting to model:

```
State_t = f(State_{t-1}, History)
```

Two institutions can have identical current balance sheets yet radically different future risk:
- one survived repeated governance breaches;
- one repeatedly refinanced;
- one normalized exceptions;
- one accumulated hidden obligations;
- one has institutional trust;
- another destroyed it.

Therefore:

```
CurrentState ≠ CompleteState
CapitalReality = PresentState + PathDependence
```

That is much deeper than another trading indicator.

---

## Architecture (P1 corrected)

```
                  ┌──────────────────────┐
                  │      Client          │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │       arifOS         │
                  │  Authority Boundary  │
                  └──────────┬───────────┘
                             │
                  bounded request
                             │
                             ▼
                  ┌──────────────────────┐
                  │       WEALTH         │
                  │ Capital Evidence     │
                  │ (Ω-invariants)       │
                  └──────────┬───────────┘
                             │
                  evidence envelope
                             │
                             ▼
                  ┌──────────────────────┐
                  │       arifOS         │
                  │      Judgment        │
                  └──────────┬───────────┘
                             │
                             ▼
                          Human
```

**WEALTH is an organ.** **arifOS is the ingress and authority boundary.**

Direct `:18082` is engineering / diagnostic only. The recommended user interface is to connect to arifOS; arifOS invokes WEALTH internally under a delegated SCT/session envelope.

---

## Federation one-liner

> WEALTH computes consequences. arifOS judges authority. A-FORGE executes approved actions. Humans remain sovereign.

The data path:

```
Reality
   ↓ evidence
WEALTH
   ↓ capital consequences
arifOS
   ↓ authority
A-FORGE
   ↓ action
Reality
```

with FRAME / VAULT999 observing and preserving the loop, and arifFlow carrying metabolic telemetry.

---

## Tool surface (P1)

```
13 canonical primitives (Ω00 + Ω01-Ω12)
  + 2 societal extensions (inequality, role scarcity)
  + 2 infrastructure tools (health, registry)
  + 14 compatibility aliases (capital_* legacy names — excluded from canonical count)
  = 17 visible surface
```

The raw count is not the point. The semantic classes are. The tool count becomes meaningful: "13 canonical capital primitives · 2 societal extensions · 2 infrastructure tools · compatibility aliases excluded."

### Ω00 wealth_synthesize — domain_assessment, NOT constitutional verdict

```json
{
  "tool_name": "wealth_synthesize",
  "domain_assessment": "FAVORABLE | CAUTION | INSUFFICIENT_EVIDENCE | CONSTRAINT_VIOLATION",
  "execution_authority": "ADVISORY_ONLY",
  "handoff": "arifOS.arif_judge",
  "constitutional_verdicts_issued": []
}
```

`WEALTH_ₐₛₛₑₛₛₘₑₙₜ ≠ arifOSᵥₑᵣᵈᵢcₜ`. WEALTH never returns SEAL / HOLD / SABAR / VOID. Those belong to arifOS.arif_judge.

### Market/macro outputs (Ω08 / Ω09) carry mandatory freshness

```json
{
  "source": "Frankfurter API | wealth://commodity | …",
  "timestamp": "2026-09-21T02:01:24.866489+00:00",
  "cache_age_seconds": 0,
  "staleness_class": "LIVE | RECENT | STALE | ARCHIVAL"
}
```

Doctrine: *Freshness ≠ Truth. LatestAvailable ≠ RealTime.*

### L11 AUTH gate (P1 fix)

Direct :18082 connector previously required `session_id` for every tool, including diagnostic reads. P1 restores OBSERVE-class exemptions:
- `capital_market`, `capital_registry`, `capital_primitive`, `capital_entropy`, `capital_indicator`, `capital_backtest`, `capital_entry_plan`, `capital_claims`, `capital_diagnose`, `capital_health`, `capital_polix`, `capital_civx`, `wealth_synthesize` — and their legacy aliases — now pass without a session.
- MUTATE tools (`capital_ledger`, `wealth_judge_handoff`) still require a verified session.

---

## CHRON × WEALTH — the prediction → outcome → calibration loop

```
WEALTH predicts   capital consequence / probability / risk band / falsifier
CHRON records     what WEALTH believed / when / using what evidence
Reality occurs
CHRON verifies    vs predicted
WEALTH recalibrates
HERMES checks    narrative distortion
arifOS governs    future use
```

This gives Prediction → Outcome → Calibration → ImprovedCapitalModel rather than endless investment commentary. That is where WEALTH becomes institutionally different.

---

## Historical collapse replay — discipline required

Replay historical financial collapses using only information available before the collapse. The benchmark requires:
- `case` (e.g., 2008 GFC, 1997 Asian crisis)
- `cutoff_date` (cryptographic exclusion of post-cutoff evidence)
- `allowed_sources` (only what was available before cutoff)
- `forbidden_future_sources` (regression test against contamination)
- `predicted_signal`, `actual_failure`
- `false_positive_controls` (firms that looked bad but survived)
- `score`

The proper test is `Model(E_{t<collapse}) → RiskSignal_t` with all post-cutoff evidence cryptographically excluded. Without negative controls, the demonstration collapses into `FailedCompany → FindWarningSigns` which is much easier.

CHRON's prediction ledger is the substrate for this benchmark.

---

## What I would execute next in WEALTH

This packet (P1) executes 4 of 7 items Arif specified; the rest are deferred:

- ✅ **1** Fix session-envelope interface so arifOS → WEALTH works end-to-end without losing identity/authority.
- ✅ **2** Declare the Ω00-Ω12 surface canonical; move old capital_* names into an explicit compatibility layer.
- ✅ **3** Remove constitutional verdict ownership from wealth_synthesize; make its output explicitly advisory/domain-level.
- ⏭ **4** Repin and test the capital_polix schema drift (done in FEDERATION-CONVERGENCE-P0).
- ✅ **5** Make freshness/provenance mandatory on every market/macro output.
- 📋 **6** CHRON-linked forecast calibration before claiming predictive superiority (deferred).
- 📋 **7** Historical-collapse replay as a proper pre-cutoff benchmark with negative controls (deferred).

---

## Identity, restated

> arifOS's irreducible question is **"May this action happen?"**
>
> WEALTH's irreducible question is **"If capital moves this way, what follows — and how sure are we?"**
>
> HERMES asks **"What exactly are we claiming?"**
>
> CHRON asks **"What did we expect, and what actually happened?"**

And the new WEALTH identity, restated:

> **WEALTH — Capital Consequence Intelligence.**
>
> It does not decide where money should go.
> It makes the consequences of moving it harder to hide.

---

**Licensed under AGPL-3.0.**

**DITEMPA BUKAN DIBERI.**
