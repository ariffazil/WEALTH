# WEALTH Terminal — Sitemap & Section Wireframes

**Status:** DESIGN DRAFT · not production deploy  
**Verdict accepted:** Keep ontology + constitutional tone + three instruments. Reframe as **one WEALTH OS** with differentiated asset identities.  
**Source reality:** `shell.template.html` + `home.template.html` + `assets/{gold,oil,gas}.json` already encode one shell / three instruments. Live `/gold` `/oil` `/gas` are still near-isomorphic clones.  
**Principle:** One federation identity (WEALTH under arifOS). Distinct asset identities (Gold · Oil · Gas). Compute only — never allocate.

---

## 0. Product identity

```text
WEALTH Terminal
Capital physics under sovereign judgment.

Not a trading app.
Not three disconnected dashboards.
One operating surface · three instruments · one causal chain:
  GEOS (substrate) → arifOS (judgment) → WEALTH (compute) → F13 human veto
```

| Layer | Owns | Does not own |
|-------|------|--------------|
| **Gold** | Monetary defense, trust decay, reserve framing | Geology truth, execution |
| **Oil (Brent)** | Flow, chokepoint, industrial pulse, inventory | Monetary reserve thesis |
| **Gas** | Seasonality, storage, LNG routing, operational balance | Diagnosis, capital allocation |
| **WEALTH shell** | Parse grammar, decision gate schema, logbook | Seal authority, mutation |
| **arifOS** | Admissibility, authority, receipts | Price forecasting as truth |
| **Arif** | Final veto (F13) | — |

---

## 1. Sitemap

```text
wealth.arif-fazil.com/                 PUBLIC landing (philosophy + entry)
wealth.arif-fazil.com/terminal/        OPERATOR home (cross-asset command)
wealth.arif-fazil.com/gold/            Instrument · monetary defense
wealth.arif-fazil.com/oil/             Instrument · industrial flow
wealth.arif-fazil.com/gas/             Instrument · operational balance
wealth.arif-fazil.com/logbook/         Sovereign memory · verdicts · vetoes
wealth.arif-fazil.com/methods/         Ontology · schema · how to read
wealth.arif-fazil.com/mcp              Machine door (redirect or organ MCP)

Compatibility (root / Caddy — document only until sealed):
  arif-fazil.com/gold  → wealth … /gold/
  arif-fazil.com/oil   → wealth … /oil/
  arif-fazil.com/gas   → wealth … /gas/
  arif-fazil.com/gass  → /gas/
```

### Primary nav (WEALTH product chrome)

```text
TERMINAL · GOLD · OIL · GAS · LOGBOOK · METHODS
```

Secondary utility (right):

```text
MCP · Observatory · /999 · Arif root
```

Footer (one line, not a second dashboard):

```text
GEOS → arifOS → WEALTH · F13 human veto · One causal chain. Three layers.
Compute only. Evidence-gated. Not investment advice.
```

---

## 2. Shared shell (every instrument page)

**Stable parse template for agents** (keep):

```text
1. Product chrome + asset switcher
2. Macro ticker (context, not hero)
3. NOW pulse (dominant)
4. Asset-identity hero module (DIFFERENTIATED)
5. Primary chart (supporting the NOW claim)
6. Causal drivers (two-column: technical | world)
7. Physical substrate (asset-tuned metrics)
8. Decision gate + F13 veto
9. Compact constellation footer
```

**Hierarchy rule (fix today’s equal-weight problem):**

| Priority | Module | Visual weight |
|----------|--------|----------------|
| **P0** | NOW pulse (price + stance + confidence + timestamp + source) | Largest, top, sticky optional |
| **P1** | Asset-identity hero | Full-width, accent-tinted |
| **P2** | Chart | Large but secondary to NOW claim |
| **P3** | Drivers / substrate | Equal to each other, below chart |
| **P4** | Decision gate | Emphasized border, not same as panels |
| **P5** | Macro ticker, meta, footer | Compressed |

Reading path (human):

```text
What is the stance now? → Why (identity module + drivers)?
→ What does physics say? → What is the gate / veto?
```

---

## 3. Section-by-section wireframes

### 3.1 WEALTH Public Landing (`/`)

```text
┌─────────────────────────────────────────────────────────────┐
│ WEALTH · Capital physics under sovereign judgment           │
│ [Enter Terminal] [Read methods] [MCP]                       │
├─────────────────────────────────────────────────────────────┤
│ Thesis (3 lines max)                                        │
│ Price is never alone. Substrate → judgment → compute.       │
├──────────────┬──────────────┬───────────────────────────────┤
│ GOLD tile    │ OIL tile     │ GAS tile                      │
│ stance       │ stance       │ stance                        │
│ confidence   │ confidence   │ confidence                    │
│ regime       │ regime       │ regime                        │
│ substrate    │ substrate    │ substrate                     │
│ stress       │ stress       │ stress                        │
│ [Open Gold]  │ [Open Oil]   │ [Open Gas]                    │
├─────────────────────────────────────────────────────────────┤
│ Cross-asset strip: DXY · rates · VIX · geopolitics flag     │
├─────────────────────────────────────────────────────────────┤
│ Latest 3 verdicts (from logbook) · F13 note                 │
└─────────────────────────────────────────────────────────────┘
```

**CTA labels:** Enter WEALTH Terminal · Open Gold workspace · Inspect oil flow map · Open gas operations node  

---

### 3.2 Terminal Home (`/terminal/`)

Daily operator surface — **command layer**, not a fourth clone of the chart page.

```text
┌─────────────────────────────────────────────────────────────┐
│ TERMINAL · Daily command · {timestamp MYT} · source link    │
├─────────────────────────────────────────────────────────────┤
│ ALERTS (only if severity ≥ amber)                           │
├──────────┬──────────┬──────────┬────────────────────────────┤
│ Gold NOW │ Oil NOW  │ Gas NOW  │ Cross-asset regime card     │
│ stance   │ stance   │ stance   │ correlations / conflicts   │
│ conf     │ conf     │ conf     │                            │
├─────────────────────────────────────────────────────────────┤
│ Relationship board (compact)                                │
│ DXY ↔ Gold · Inventory ↔ Oil · Storage/HDD ↔ Gas            │
├─────────────────────────────────────────────────────────────┤
│ Today’s open questions (UNKNOWN list — never invent zeros)  │
├─────────────────────────────────────────────────────────────┤
│ Jump: Gold workspace · Oil workspace · Gas workspace        │
│ Logbook · Methods                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.3 Instrument workspace (shared skeleton)

```text
┌─────────────────────────────────────────────────────────────┐
│ WEALTH / {ASSET} · {identity title}                         │
│ Gold | Oil | Gas   (active state)                           │
├─────────────────────────────────────────────────────────────┤
│ MACRO TICKER (compressed height)                            │
├─────────────────────────────────────────────────────────────┤
│ ██ NOW PULSE (P0 — dominant) ██                             │
│ Price · Δ · stance pill · confidence · primary driver       │
│ S1/S2 R1/R2 · risk bars · live timestamp · source badge     │
├─────────────────────────────────────────────────────────────┤
│ ██ ASSET IDENTITY HERO (P1 — different per asset) ██        │
│ See §4                                                      │
├─────────────────────────────────────────────────────────────┤
│ CHART (P2) — supports the NOW claim, not the reverse        │
├────────────────────────────┬────────────────────────────────┤
│ CAUSAL: Technical (P3)     │ CAUSAL: World (P3)             │
├────────────────────────────┴────────────────────────────────┤
│ PHYSICAL SUBSTRATE (P3) — asset-tuned metrics only          │
├─────────────────────────────────────────────────────────────┤
│ DECISION GATE (P4)                                          │
│ Stance · action language · confidence · invalidation        │
│ Human Sovereign Veto Active — F13                           │
│ [Open related GEOX evidence] [Verify /999] [Log this day]   │
├─────────────────────────────────────────────────────────────┤
│ Footer compact: GEOS→arifOS→WEALTH · not advice             │
└─────────────────────────────────────────────────────────────┘
```

**Machine-readable block** (hidden or `<script type="application/json" id="wealth-state">`):

```json
{
  "schema": "wealth.instrument_state.v1",
  "asset": "GOLD|OIL|GAS",
  "identity": "monetary_defense|industrial_flow|operational_balance",
  "stance": "…",
  "confidence": 0.0,
  "regime": "…",
  "substrate_stress": "…",
  "epistemic": "OBSERVED|DERIVED|…",
  "unknowns": [],
  "as_of": "ISO-8601",
  "sources": [],
  "f13_veto": "ACTIVE"
}
```

---

## 4. Differentiated asset-identity heroes (fix flattening)

### GOLD — Monetary defense

```text
Title: Reserve trust / intact value
Primary question: Is money losing integrity faster than metal is losing bid?
Modules:
  · Real yields / DXY / policy uncertainty
  · Trust-decay thesis (short, labeled DERIVED/CLAIM)
  · ETF / official sector flows (if evidence exists)
  · NOT: chokepoint maps, storage % full
Accent: gold (existing)
```

### OIL (Brent) — Industrial flow

```text
Title: Flow · chokepoint · industrial pulse
Primary question: What does physical movement and inventory say about price?
Modules:
  · Chokepoint / geopolitics map (Hormuz, Red Sea — evidence-tagged)
  · Inventory / crude balance (if available)
  · Demand proxy / refining margin note
  · NOT: GSR / silver-primary framing
Accent: amber-blue industrial (distinct from gold)
```

### GAS — Operational balance

```text
Title: Seasonality · storage · LNG · balancing
Primary question: Is the system compressing or releasing operational stress?
Modules:
  · Storage / HDD-CDD / seasonal phase
  · LNG routing / cargo window (if evidence)
  · Thermal / pressure / compression framing (keep — distinctive)
  · Decision maturity panel (explicit: operational vs speculative)
Accent: cyan-cold (distinct)
```

---

## 5. Decision gate (shared schema, asset-tuned verbs)

| Field | Gold example | Oil example | Gas example |
|-------|--------------|-------------|-------------|
| Stance | Defend / Hold / Reduce monetary beta | Flow-supportive / Neutral / Flow-risk | Balance / Storage-watch / Vol-risk |
| Invalidation | Yields reprice up X | Inventory rebuilds | Storage trajectory flips |
| Veto | F13 human | F13 human | F13 human |
| Non-claim | Not investment advice | Not allocation | Not dispatch authority |

---

## 6. Logbook (`/logbook/`)

```text
Date | Asset | Stance | Confidence | What changed | Veto? | Link to state JSON
```

Converts dashboards → **institutional memory**. Ties to future VAULT receipts when sealed.

---

## 7. Implementation map (to existing code)

| Design piece | Existing source |
|--------------|-----------------|
| Shared shell | `/root/WEALTH/site/shell.template.html` |
| Terminal home | `/root/WEALTH/site/home.template.html` |
| Asset config | `/root/WEALTH/site/assets/{gold,oil,gas}.json` |
| Build | `/root/WEALTH/site/build.py` |
| Deploy targets | `/var/www/html/{gold,oil,gas}` (today); prefer wealth host paths |

**Do not redesign from zero.**  
**Do:**

1. Strengthen NOW hierarchy in CSS (pulse-bar scale, reduce equal card weight).  
2. Inject per-asset **identity hero** partials via `assets/*.json` + template slots.  
3. Retune macro ticker per asset (stop showing GSR/Silver as default on oil/gas).  
4. Ship Terminal home as first-class route.  
5. Compress footer.  
6. Emit `wealth.instrument_state.v1` JSON on every page for agents.

---

## 8. Agent parse grammar (stable)

Every instrument page exposes the same section IDs:

```text
#now-pulse
#identity-hero
#chart
#drivers-technical
#drivers-world
#substrate
#decision-gate
#wealth-state   (JSON)
```

Agents manage daily work against this grammar; humans see differentiated product logic inside it.

---

## 9. Phased delivery (no false “done”)

| Phase | Deliverable | Mutation |
|-------|-------------|----------|
| **W0** | This IA (docs only) | none |
| **W1** | Template hierarchy CSS + identity hero slots + asset-specific macro sets | WEALTH site branch |
| **W2** | Terminal home + logbook skeleton | WEALTH site branch |
| **W3** | wealth.instrument_state.v1 + tests | + public-state optional |
| **W4** | Host/path canonicalization under wealth.arif-fazil.com | Caddy only after seal |

Production deploy requires separate authority (arifOS + A-FORGE + human ack).

---

## 10. Design verdict (locked)

```text
KEEP:  ontology, constitutional tone, F13 veto, causal chain, three instruments
CHANGE: parallel dashboards → one WEALTH terminal
CHANGE: equal-weight modules → decisive NOW hierarchy
CHANGE: label-only differences → identity heroes (reserve / flow / operations)
CHANGE: personal-site subsection feel → first-class WEALTH product chrome
```

**Intelligence gain = machine-readable institutional structure, not more panels.**

DITEMPA BUKAN DIBERI
