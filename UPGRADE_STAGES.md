# WEALTH MCP Upgrade Stages — Full Architecture Map
# Forged: 2026-08-18 | DITEMPA BUKAN DIBERI
# Authority: F13 SOVEREIGN

## Current State: Stage 1 (Adaptive WEALTH) — ACHIEVED

```
Market → Regime Map → Ensemble → Compass → Stress → Asymmetric → Entry
```

Tools: capital_diagnose(regime_map), capital_backtest(compass/stress_test/ensemble),
       capital_health(asymmetric_risk)

---

## Stage 2: Institutional WEALTH

### Purpose: See flows, liquidity, and strategic regimes

### Engines Required:

#### FLOWX — Capital Flow Tracker
- Track: Treasury flows, ETF flows, pension flows, SWF flows, central bank flows
- Graph: Source → Route → Intermediate → Destination → Beneficiary
- Question: "Who moved the money? Why? Where? At what scale?"
- Data sources: BNM, SC Malaysia, Bank Negara, ETF providers, pension funds
- MCP tool: capital_flows (new) or capital_market(mode=flows)
- Implementation: Graph-based flow modeling, anomaly detection

#### LIQUIDITYX — Money Plumbing Engine
- Track: Repo rates, funding costs, swap spreads, dealer balance sheets
- Question: "Who creates liquidity? Who destroys it?"
- Regimes: LIQUID, NORMAL, STRESSED, FROZEN
- Data sources: BNM monetary data, interbank rates, FX reserves
- MCP tool: capital_liquidity (new) or capital_market(mode=liquidity)
- Implementation: Liquidity regime classification, stress indicators

#### REGIMEX — Strategic State Machine
- States: INFLATION, DEFLATION, EXPANSION, CONTRACTION, WAR, CRISIS, RECOVERY
- Track: Macro regime transitions, policy regime shifts
- Question: "What world are we in? What world is emerging?"
- Data sources: CPI, GDP, PMI, employment, commodity prices, geopolitical events
- MCP tool: capital_diagnose(mode=strategic_regime)
- Implementation: Hidden Markov Model or Bayesian regime switching

### Dependencies:
- FLOWX requires: real-time flow data feeds (macrox, capitalx)
- LIQUIDITYX requires: monetary data API integration
- REGIMEX requires: macro data aggregation layer

---

## Stage 3: Systemic WEALTH

### Purpose: See power, institutions, and sovereign structure

### Engines Required:

#### POLIX — Power & Ownership Graph
- Graph edges: Owns, Controls, Funds, Influences, Appoints, Benefits
- Track: Corporate ownership chains, director networks, fund holdings
- Question: "Who actually decides? Who benefits?"
- Data sources: Companies Commission, SC filings, annual reports, fund disclosures
- MCP tool: capital_politics (new) or capital_diagnose(mode=power_graph)
- Implementation: Graph database (FalkorDB), ownership chain resolution

#### INSTITUTIONX — Institutional Capital Map
- Models: Central banks, SWFs, pensions, custodians, clearinghouses, regulators
- Track: Balance sheet authority, capital allocation power
- Question: "Where does authority live? Where is balance-sheet power?"
- Data sources: BNM, EPF, KWAP, PNB, SC, Bursa Malaysia
- MCP tool: capital_institutions (new) or capital_diagnose(mode=institution_map)
- Implementation: Institutional entity database, authority scoring

#### SOVX — Sovereign Digital Twin
- Malaysia model: BNM, Treasury, PETRONAS, EPF, KWAP, PNB, MGS, MYR, Banks, Exports, Energy, Demographics
- Outputs: Sovereignty Score, Strategic Autonomy, Dependency Index, Resilience Index
- Question: "Can the system absorb a shock?"
- Data sources: DOSM, BNM, Treasury, PETRONAS FRA, World Bank
- MCP tool: capital_sovereign (new) or capital_health(mode=sovereignty)
- Implementation: System dynamics model, shock simulation

### Dependencies:
- POLIX requires: corporate registry API, fund disclosure data
- INSTITUTIONX requires: institutional balance sheet data
- SOVX requires: macro + fiscal + energy + demographic data aggregation

---

## Stage 4: VOID WEALTH

### Purpose: See hidden incentives, constraints, dependencies, emergence

### Engines Required:

#### REFLEXX — Narrative-Reality Engine
- Track: Narrative dominance, expectation momentum, belief divergence, reflexivity intensity
- Question: "What beliefs are becoming reality? What narratives are self-fulfilling?"
- Data sources: News sentiment, social media, analyst reports, policy statements
- MCP tool: capital_reflexivity (new) or capital_diagnose(mode=reflexivity)
- Implementation: Sentiment analysis, narrative divergence scoring, reflexivity loop detection

#### NETRISK — Contagion Network Engine
- Models: Interbank, energy, supply chain, debt, sovereign, trade, currency
- Question: "If X fails, who fails next?"
- Data sources: BIS, BNM, trade data, supply chain data, debt schedules
- MCP tool: capital_contagion (new) or capital_diagnose(mode=contagion)
- Implementation: Network graph, cascade simulation, fragility scoring

#### VOIDX — 6 Decay Detection Engines
1. Incentive Drift — "What behavior gets rewarded?"
2. Consequence Gap — "Who benefits? Who pays?"
3. Dependency Concentration — "What happens if node X disappears?"
4. Narrative-Reality Divergence — "Are words converging with reality?"
5. Optionality Destruction — "Can the institution still change direction?"
6. Reflexive Fragility — "What happens if confidence falls?"

- Question: "What has become inevitable?"
- Data sources: All upstream engines + institutional analysis
- MCP tool: capital_diagnose(mode=voidx)
- Implementation: 6 sub-engines, decay equation, institutional health scoring

### Dependencies:
- REFLEXX requires: NLP sentiment pipeline, narrative database
- NETRISK requires: network graph, interconnection data
- VOIDX requires: all upstream engines + institutional analysis capability

---

## Upgrade Sequence (Priority Order)

### Phase 1: Data Foundation (Months 1-3)
1. macrox — Macroeconomic data aggregator (CPI, GDP, PMI, employment)
2. capitalx — Capital market data feeds (flows, volumes, institutional holdings)
3. creditx — Credit data (spreads, ratings, debt schedules)

### Phase 2: Stage 2 Engines (Months 3-6)
4. FLOWX — Capital flow tracking
5. LIQUIDITYX — Liquidity regime classification
6. REGIMEX — Strategic regime detection

### Phase 3: Stage 3 Engines (Months 6-9)
7. POLIX — Power & ownership graph
8. INSTITUTIONX — Institutional capital map
9. SOVX — Sovereign digital twin

### Phase 4: Stage 4 Engines (Months 9-12)
10. REFLEXX — Narrative-reality engine
11. NETRISK — Contagion network engine
12. VOIDX — 6 decay detection engines

---

## Key Insight

Stage 1 (Adaptive) improved DECISION GEOMETRY.
Stages 2-4 improve REALITY CONTACT.

The PETRONAS test shows: even without FLOWX/POLIX/VOIDX as live engines,
the VOIDX analytical framework produces structured institutional assessment.

The engines automate what the framework describes.
