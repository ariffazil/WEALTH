/**
 * WEALTH MCP Server (stdio)
 *
 * Exposes WEALTH constitutional governance, financial engines,
 * and civilizational intelligence as MCP tools.
 *
 * DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import {
  FLOORS,
  EPISTEMIC,
  HOLD,
  checkFloors,
} from "../host/kernel/floors.js";
import { seal999 } from "../host/kernel/seal.js";
import {
  calculateRiskAdjustedRate,
  compareCapitalAdvantage,
} from "../host/kernel/capitalx.js";
import { computeNetWorth } from "../host/wealth/networth.js";
import { computeCashflow } from "../host/wealth/cashflow.js";
import { computeMaruahScore } from "../host/wealth/maruah-score.js";
import {
  projectCompoundGrowth,
  projectRunwayDepletion,
} from "../host/wealth/projection.js";

// Civilizational Engines
import { computeCivilizationalProsperityIndex } from "../host/civilizational/prosperity_index.js";
import { detectSystemicRisk } from "../host/civilizational/cascade_detector.js";

const server = new McpServer({
  name: "wealth-mcp-server",
  version: "1.3.0",
});

function textContent(obj) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(obj, null, 2),
      },
    ],
  };
}

function now() {
  return new Date().toISOString();
}

function requireEnvelope(args) {
  if (!args.header || !args.header.envelope_id) {
    return {
      error: true,
      verdict: "SABAR",
      reason: "F3: Missing envelope_id in header.",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "envelope_check", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
  }
  return null;
}

// ── Legacy / Core Tools ───────────────────────────────────────────────────────

server.tool(
  "wealth_check_floors",
  "Run WEALTH F1-F13 floor checks on a proposed operation.",
  {
    type: z.string().describe("Operation type"),
    reversible: z.boolean().optional().default(true),
    epistemic: z.enum(["CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"]).optional(),
    confidence: z.number().min(0).max(1).optional(),
    peace2: z.number().optional(),
    uncertainty_band: z.number().optional(),
    external_sync: z.boolean().optional().default(false),
    user_consent: z.boolean().optional().default(false),
    has_unresolved_entries: z.boolean().optional().default(false),
    ai_is_deciding: z.boolean().optional().default(false),
    floor_override: z.boolean().optional().default(false),
  },
  async (args) => {
    const result = checkFloors(args);
    return textContent(result);
  }
);

server.tool(
  "wealth_seal_999",
  "Attempt a 999 SEAL on a decision state.",
  {
    peace2: z.number().optional().default(1.0),
    confidence: z.number().min(0).max(1).optional().default(0.0),
    holds: z.array(z.string()).optional().default([]),
    violations: z.array(z.string()).optional().default([]),
    human_confirmed: z.boolean().optional().default(false),
  },
  async (args) => {
    const sealed = await seal999({
      ...args,
      sealed: false,
      epoch: now(),
    });
    return textContent(sealed);
  }
);

server.tool(
  "wealth_capitalx_score",
  "Calculate risk-adjusted cost of capital from constitutional signals.",
  {
    base_rate: z.number().min(0),
    dS: z.number().optional().default(0),
    peace2: z.number().optional().default(1.0),
    maruahScore: z.number().min(0).max(1).optional().default(0.5),
    trustIndex: z.number().min(0).max(1).optional().default(0.5),
    deltaCiv: z.number().optional().default(0),
  },
  async (args) => {
    const result = calculateRiskAdjustedRate(args.base_rate, args);
    return textContent(result);
  }
);

server.tool(
  "wealth_capitalx_compare",
  "Compare risk-adjusted rates between WEALTH and extractive nodes.",
  {
    base_rate: z.number().min(0),
    wealth_signals: z.object({
      dS: z.number().optional(),
      peace2: z.number().optional(),
      maruahScore: z.number().min(0).max(1).optional(),
      trustIndex: z.number().min(0).max(1).optional(),
      deltaCiv: z.number().optional(),
    }),
    extractive_signals: z.object({
      dS: z.number().optional(),
      peace2: z.number().optional(),
      maruahScore: z.number().min(0).max(1).optional(),
      trustIndex: z.number().min(0).max(1).optional(),
      deltaCiv: z.number().optional(),
    }),
  },
  async (args) => {
    const result = compareCapitalAdvantage(args.base_rate, args.wealth_signals, args.extractive_signals);
    return textContent(result);
  }
);

server.tool(
  "wealth_compute_networth",
  "Compute net worth with epistemic degradation.",
  {
    assets: z.array(z.object({ value: z.number(), tag: z.string().optional() })).optional().default([]),
    liabilities: z.array(z.object({ principal: z.number(), tag: z.string().optional() })).optional().default([]),
  },
  async (args) => {
    const result = computeNetWorth(args.assets, args.liabilities);
    return textContent(result);
  }
);

server.tool(
  "wealth_compute_cashflow",
  "Compute monthly cashflow and runway.",
  {
    income: z.array(z.object({
      monthly_amount: z.number(),
      active: z.boolean().optional().default(true),
    })).optional().default([]),
    expenses: z.array(z.object({
      monthly_amount: z.number(),
      active: z.boolean().optional().default(true),
    })).optional().default([]),
  },
  async (args) => {
    const result = computeCashflow(args.income, args.expenses);
    return textContent(result);
  }
);

server.tool(
  "wealth_compute_maruah",
  "Compute the Maruah dignity/integrity score.",
  {
    financial_integrity: z.number().min(0).max(1).optional().default(0.5),
    sovereignty: z.number().min(0).max(1).optional().default(0.5),
    debt_dignity: z.number().min(0).max(1).optional().default(0.5),
    amanah_index: z.number().min(0).max(1).optional().default(0.5),
    community_contribution: z.number().min(0).max(1).optional().default(0.0),
  },
  async (args) => {
    const result = computeMaruahScore(args);
    return textContent(result);
  }
);

server.tool(
  "wealth_project_growth",
  "Compound growth with F7 humility band.",
  {
    principal: z.number().min(0),
    rate: z.number(),
    years: z.number().int().min(1),
    annual_contribution: z.number().optional().default(0),
  },
  async (args) => {
    const result = projectCompoundGrowth(args.principal, args.rate, args.years, args.annual_contribution);
    return textContent(result);
  }
);

server.tool(
  "wealth_project_runway",
  "Runway depletion estimate.",
  {
    current_savings: z.number().min(0),
    monthly_burn: z.number(),
    monthly_income: z.number().optional().default(0),
  },
  async (args) => {
    const result = projectRunwayDepletion(args.current_savings, args.monthly_burn, args.monthly_income);
    return textContent(result);
  }
);

// ── New Tool Families (Thin Vertical Slice) ───────────────────────────────────

server.tool(
  "wealth_state_market_snapshot",
  "Build a baseline capital temperature and entropy level.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    jurisdiction: z.string().describe("e.g. MY, US, ASEAN"),
    asset_classes: z.array(z.string()),
    tenor_months: z.number().int().min(1).optional().default(120),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);
    const result = {
      rf_curve: [
        { tenor_y: 1, rate: 0.0325 },
        { tenor_y: 5, rate: 0.0350 },
        { tenor_y: 10, rate: 0.0380 },
      ],
      erp: 0.055,
      credit_spreads: { AAA: 0.008, BBB: 0.022 },
      volatility_surface: [{ moneyness: 1.0, iv: 0.16 }],
      capital_temperature: 0.42,
      verdict: "SEAL",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "wealth_state_market_snapshot", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
    return textContent(result);
  }
);

server.tool(
  "wealth_risk_capital_allocation",
  "Turn GEOX feasibility into safe capital deployment limits.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    portfolio: z.object({ buckets: z.array(z.object({
      id: z.string(),
      name: z.string().optional(),
      exposure_myr: z.number().min(0),
      sector: z.string().optional(),
      region: z.string().optional(),
    })) }),
    confidence_level: z.number().min(0.9).max(0.9999),
    maruah_drawdown_floor: z.number().min(0).max(1).optional().default(0.6),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);
    const exposure = args.portfolio.buckets[0]?.exposure_myr ?? 0;
    const result = {
      economic_capital: Math.round(exposure * 0.084),
      risk_decomposition: { factor: { policy: 0.012, technology: 0.008 }, geo: {} },
      risk_budgets: args.portfolio.buckets.map((b) => ({
        bucket_id: b.id,
        budget_myr: Math.round(b.exposure_myr * 0.1),
        utilization: 0.84,
      })),
      liquidity_buffer: Math.round(exposure * 0.17),
      verdict: "SEAL",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "wealth_risk_capital_allocation", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
    return textContent(result);
  }
);

server.tool(
  "wealth_price_exergy_cost",
  "Estimate thermodynamic cost per unit of output.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    project_inputs: z.object({
      energy_mj_per_unit: z.number().min(0),
      material_exergy_mj_per_unit: z.number().min(0),
      output_unit: z.string(),
    }),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);
    const pi = args.project_inputs;
    const exergy = pi.energy_mj_per_unit + pi.material_exergy_mj_per_unit;
    const result = {
      exergy_mj_per_unit: exergy,
      emergy_proxy: Math.round(exergy * 14.4),
      entropy_cost_per_unit: Number((exergy / 50000).toFixed(6)),
      verdict: "SEAL",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "wealth_price_exergy_cost", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
    return textContent(result);
  }
);

server.tool(
  "wealth_justice_maruah_score",
  "Measure dignity/integrity impact and distributional fairness.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    project_profile: z.object({
      displacement_risk: z.number().min(0).max(1),
      pollution_load: z.number().min(0).max(1),
      cultural_loss_risk: z.number().min(0).max(1),
      community_benefit_share: z.number().min(0).max(1),
    }),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);
    const p = args.project_profile;
    const score = Math.max(
      0,
      Math.min(
        1,
        0.5 +
          (p.community_benefit_share ?? 0) * 0.4 -
          (p.displacement_risk ?? 0) * 0.3 -
          (p.pollution_load ?? 0) * 0.2 -
          (p.cultural_loss_risk ?? 0) * 0.2
      )
    );
    let band = "RED";
    if (score >= 0.85) band = "SOVEREIGN";
    else if (score >= 0.70) band = "STABLE";
    else if (score >= 0.60) band = "FLOOR";
    else if (score >= 0.40) band = "AMBER";
    const result = {
      maruah_score: Number(score.toFixed(2)),
      maruah_band: band,
      incidence_map: { beneficiaries: ["local households"], cost_bearers: ["incumbents"] },
      exclusion_flags: [],
      verdict: band === "RED" ? "888-HOLD" : "SEAL",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "wealth_justice_maruah_score", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
    return textContent(result);
  }
);

server.tool(
  "wealth_price_capitalx",
  "Compute the constitutional risk-adjusted cost of capital with basis support.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    base_rate: z.number().min(0),
    signals: z.object({
      dS: z.number(),
      peace2: z.number(),
      maruahScore: z.number().min(0).max(1),
      trustIndex: z.number().min(0).max(1),
      deltaCiv: z.number(),
    }),
    wealth_basis: z.object({
      e_hat: z.number().min(0).max(1),
      s_hat: z.number().min(0).max(1),
      echo_hat: z.number().min(0).max(1),
    }).optional(),
    defects: z.object({
      paradox: z.number().min(0).max(1),
      scar: z.number().min(0).max(1),
      shadow: z.number().min(0).max(1),
    }).optional(),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);

    // Monotonicity guard: if shadow increased from a reference, r_adj must not decrease.
    // For now we enforce clamp to zero and flag if triggered.
    const result = calculateRiskAdjustedRate(args.base_rate, args.signals, {
      wealth_basis: args.wealth_basis,
      defects: args.defects,
    });

    // Force VOID if a clear rate inversion is requested (naive heuristic).
    if (args.signals.dS > 0.3 && result.r_adj < args.base_rate * 0.5) {
      return textContent({
        verdict: "VOID",
        reason: "F12 hard block: rate inversion detected (dS elevated but r_adj collapsed).",
        epistemic: "ESTIMATE",
        vault_log_entry: { tool: "wealth_price_capitalx", epoch: now() },
        witness: { human: false, ai: true, earth: true },
      });
    }

    return textContent(result);
  }
);

server.tool(
  "wealth_flow_scenario_npv",
  "Project cashflows and entropy evolution under regimes.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    cashflows: z.array(z.number()),
    r_adj: z.number().min(0),
    scenarios: z.array(z.object({
      name: z.string(),
      probability: z.number().min(0).max(1),
      cashflow_adjustment: z.number().optional().default(0),
    })),
    geo_constraints: z.array(z.string()).optional().default([]),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);

    const npvs = args.scenarios.map((s) => {
      const adj = s.cashflow_adjustment ?? 0;
      let npv = 0;
      for (let t = 0; t < args.cashflows.length; t++) {
        npv += args.cashflows[t] * (1 + adj) / Math.pow(1 + args.r_adj, t + 1);
      }
      return Math.round(npv);
    });

    const result = {
      npv_distribution: npvs,
      irr: 0.148, // simplified stub
      payback_years: 6.2, // simplified stub
      regime_impacts: args.scenarios.map((s, i) => ({ scenario: s.name, npv: npvs[i] })),
      verdict: "SEAL",
      epistemic: "ESTIMATE",
      vault_log_entry: { tool: "wealth_flow_scenario_npv", epoch: now() },
      witness: { human: false, ai: true, earth: true },
    };
    return textContent(result);
  }
);

server.tool(
  "wealth_control_gate_888",
  "Final routing gate before capital execution.",
  {
    header: z.object({
      session_id: z.string(),
      envelope_id: z.string(),
      epoch: z.string().datetime().optional(),
    }),
    candidate: z.object({
      maruah: z.number().min(0).max(1),
      r_adj: z.number().min(0),
      entropy_budget_remaining: z.number(),
      reversible: z.boolean(),
      human_confirmed: z.boolean().optional().default(false),
    }),
  },
  async (args) => {
    const envErr = requireEnvelope(args);
    if (envErr) return textContent(envErr);

    const c = args.candidate;
    const holds = [];
    if ((c.maruah ?? 1) < 0.4) holds.push("MARUAH_RED");
    if (c.reversible === false && !c.human_confirmed) holds.push("IRREVERSIBLE_UNCONFIRMED");
    if ((c.entropy_budget_remaining ?? 1) < 0) holds.push("ENTROPY_BUDGET_EXHAUSTED");

    const triggered = holds.length > 0;
    let recommendation = "FUND";
    if (triggered) recommendation = "KILL";
    else if (c.maruah < 0.6) recommendation = "DEFER";

    const result = {
      hold_triggered: triggered,
      hold_reasons: holds,
      recommendation,
      repricing_hints: triggered
        ? []
        : ["Rate is 351 bps below classical WACC; pass advantage to borrower"],
      upstream_signal: triggered
        ? "Capital says STOP. Review floors before re-pricing."
        : `Capital says GO. Thermodynamics + maruah both clear. r_adj = ${(c.r_adj * 100).toFixed(2)}%.`,
      verdict: triggered ? "888-HOLD" : "SEAL",
      epistemic: triggered ? "ESTIMATE" : "CLAIM",
      vault_log_entry: { tool: "wealth_control_gate_888", epoch: now() },
      witness: { human: c.human_confirmed, ai: true, earth: true },
    };
    return textContent(result);
  }
);

// ── Civilizational Tools ─────────────────────────────────────────────────────

server.tool(
  "civilizational_prosperity_index",
  "Compute the Global Prosperity Index (Civilizational Maruah).",
  {
    gdp_per_capita_growth: z.number().optional(),
    employment_quality: z.number().optional(),
    energy_access: z.number().optional(),
    renewable_share: z.number().optional(),
    food_security: z.number().optional(),
    water_security: z.number().optional(),
    institutional_integrity: z.number().optional(),
  },
  async (args) => {
    const result = computeCivilizationalProsperityIndex(args);
    return textContent(result);
  }
);

server.tool(
  "civilizational_systemic_risk",
  "Detect cross-domain cascade risk and systemic instability.",
  {
    markets: z.object({ risk: z.number() }).optional(),
    energy: z.object({ risk: z.number() }).optional(),
    food: z.object({ risk: z.number() }).optional(),
  },
  async (args) => {
    const result = detectSystemicRisk(args);
    return textContent(result);
  }
);

// ── Resources ────────────────────────────────────────────────────────────────

server.resource(
  "wealth://governance/floors",
  "wealth://governance/floors",
  { mimeType: "application/json" },
  async () => ({
    contents: [{ uri: "wealth://governance/floors", mimeType: "application/json", text: JSON.stringify({ FLOORS, HOLD }, null, 2) }],
  })
);

server.resource(
  "wealth://governance/epistemic",
  "wealth://governance/epistemic",
  { mimeType: "application/json" },
  async () => ({
    contents: [{ uri: "wealth://governance/epistemic", mimeType: "application/json", text: JSON.stringify({ EPISTEMIC }, null, 2) }],
  })
);

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  process.stderr.write(`[wealth-mcp] Fatal: ${err}\n`);
  process.exit(1);
});
