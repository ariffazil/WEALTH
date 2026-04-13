/**
 * WEALTH MCP Server (stdio)
 *
 * Exposes WEALTH constitutional governance and financial engines
 * as MCP tools for any MCP-compatible host.
 *
 * Tools:
 *   wealth_check_floors      — Run F1-F13 floor checks
 *   wealth_seal_999          — Attempt 999 SEAL on a state
 *   wealth_capitalx_score    — Calculate risk-adjusted cost of capital
 *   wealth_capitalx_compare  — Compare virtuous vs extractive capital rates
 *   wealth_compute_networth  — Compute net worth with epistemic tags
 *   wealth_compute_cashflow  — Compute monthly cashflow and runway
 *   wealth_compute_maruah    — Compute Maruah dignity score
 *   wealth_project_growth    — Compound growth with F7 humility band
 *   wealth_project_runway    — Runway depletion estimate
 *
 * Resources:
 *   wealth://governance/floors    — F1-F13 definitions
 *   wealth://governance/epistemic — Epistemic tag enum
 *   wealth://sample/state         — Demo financial state
 *
 * Transport: stdio
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
} from "../src/kernel/floors.js";
import { seal999 } from "../src/kernel/seal.js";
import {
  calculateRiskAdjustedRate,
  compareCapitalAdvantage,
} from "../src/kernel/capitalx.js";
import { computeNetWorth } from "../src/wealth/networth.js";
import { computeCashflow } from "../src/wealth/cashflow.js";
import { computeMaruahScore } from "../src/wealth/maruah-score.js";
import {
  projectCompoundGrowth,
  projectRunwayDepletion,
} from "../src/wealth/projection.js";

const server = new McpServer({
  name: "wealth-mcp-server",
  version: "1.1.0",
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

// ── Tools ────────────────────────────────────────────────────────────────────

server.tool(
  "wealth_check_floors",
  "Run WEALTH F1-F13 floor checks on a proposed operation. Returns pass/fail, holds, violations, and warnings.",
  {
    type: z.string().describe("Operation type (e.g. TRANSFER, PROJECTION)"),
    reversible: z.boolean().optional().default(true).describe("Whether the operation is reversible"),
    epistemic: z.enum(["CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"]).optional().describe("Epistemic tag"),
    confidence: z.number().min(0).max(1).optional().describe("Confidence level (0-1)"),
    peace2: z.number().optional().describe("Peace score (should be >= 1.0)"),
    uncertainty_band: z.number().optional().describe("Uncertainty band for projections (F7)"),
    external_sync: z.boolean().optional().default(false).describe("Whether external sync is attempted"),
    user_consent: z.boolean().optional().default(false).describe("User consent for external sync"),
    has_unresolved_entries: z.boolean().optional().default(false).describe("Unresolved entries flag (F9)"),
    ai_is_deciding: z.boolean().optional().default(false).describe("Whether AI is attempting to decide (F10)"),
    floor_override: z.boolean().optional().default(false).describe("Floor override attempt (F12)"),
  },
  async (args) => {
    const result = checkFloors(args);
    return textContent(result);
  }
);

server.tool(
  "wealth_seal_999",
  "Attempt a 999 SEAL on a decision state. Returns sealed state + telemetry, or 888-HOLD if floors fail.",
  {
    peace2: z.number().optional().default(1.0).describe("Peace score"),
    confidence: z.number().min(0).max(1).optional().default(0.0).describe("Confidence level"),
    holds: z.array(z.string()).optional().default([]).describe("Active holds"),
    violations: z.array(z.string()).optional().default([]).describe("Active violations"),
    human_confirmed: z.boolean().optional().default(false).describe("Whether human confirmed"),
  },
  async (args) => {
    const sealed = await seal999({
      ...args,
      sealed: false,
      epoch: new Date().toISOString(),
    });
    return textContent(sealed);
  }
);

server.tool(
  "wealth_capitalx_score",
  "Calculate a risk-adjusted cost of capital from WEALTH constitutional signals.",
  {
    base_rate: z.number().min(0).describe("Starting interest rate (e.g. 0.05 for 5%)"),
    dS: z.number().optional().default(0).describe("Entropy delta"),
    peace2: z.number().optional().default(1.0).describe("Peace score"),
    maruahScore: z.number().min(0).max(1).optional().default(0.5).describe("Maruah dignity score (0-1)"),
    trustIndex: z.number().min(0).max(1).optional().default(0.5).describe("Trust topology score (0-1)"),
    deltaCiv: z.number().optional().default(0).describe("Civilization stability delta"),
  },
  async (args) => {
    const { base_rate, dS, peace2, maruahScore, trustIndex, deltaCiv } = args;
    const result = calculateRiskAdjustedRate(base_rate, {
      dS,
      peace2,
      maruahScore,
      trustIndex,
      deltaCiv,
    });
    return textContent(result);
  }
);

server.tool(
  "wealth_capitalx_compare",
  "Compare risk-adjusted rates between a WEALTH node and an extractive node. Returns advantage in basis points.",
  {
    base_rate: z.number().min(0).describe("Starting interest rate"),
    wealth_signals: z.object({
      dS: z.number().optional(),
      peace2: z.number().optional(),
      maruahScore: z.number().min(0).max(1).optional(),
      trustIndex: z.number().min(0).max(1).optional(),
      deltaCiv: z.number().optional(),
    }).describe("Constitutional signals for the virtuous node"),
    extractive_signals: z.object({
      dS: z.number().optional(),
      peace2: z.number().optional(),
      maruahScore: z.number().min(0).max(1).optional(),
      trustIndex: z.number().min(0).max(1).optional(),
      deltaCiv: z.number().optional(),
    }).describe("Constitutional signals for the extractive node"),
  },
  async (args) => {
    const result = compareCapitalAdvantage(
      args.base_rate,
      args.wealth_signals,
      args.extractive_signals
    );
    return textContent(result);
  }
);

server.tool(
  "wealth_compute_networth",
  "Compute net worth from assets and liabilities with epistemic degradation.",
  {
    assets: z.array(z.object({
      value: z.number(),
      tag: z.enum(["CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"]).optional(),
      deleted: z.boolean().optional(),
    })).optional().default([]),
    liabilities: z.array(z.object({
      principal: z.number(),
      tag: z.enum(["CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"]).optional(),
      deleted: z.boolean().optional(),
    })).optional().default([]),
  },
  async (args) => {
    const result = computeNetWorth(args.assets, args.liabilities);
    return textContent(result);
  }
);

server.tool(
  "wealth_compute_cashflow",
  "Compute monthly cashflow, burn, and runway from income and expenses.",
  {
    income: z.array(z.object({
      monthly_amount: z.number().optional(),
      reliability: z.enum(["guaranteed", "regular", "irregular", "speculative"]).optional(),
      active: z.boolean().optional(),
      deleted: z.boolean().optional(),
    })).optional().default([]),
    expenses: z.array(z.object({
      monthly_amount: z.number().optional(),
      category: z.enum(["fixed", "variable", "discretionary", "emergency"]).optional(),
      deleted: z.boolean().optional(),
    })).optional().default([]),
    liquid_assets: z.number().optional().default(0).describe("Liquid asset buffer"),
  },
  async (args) => {
    const result = computeCashflow(args.income, args.expenses, args.liquid_assets);
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
    floor: z.number().min(0).max(1).optional().default(0.6),
  },
  async (args) => {
    const result = computeMaruahScore(args);
    return textContent(result);
  }
);

server.tool(
  "wealth_project_growth",
  "Project compound growth with F7 humility bands. Returns low/mid/high estimates.",
  {
    pv: z.number().describe("Present value"),
    rate_annual: z.number().describe("Annual growth rate (e.g. 0.07 for 7%)"),
    years: z.number().int().positive().describe("Projection horizon in years"),
    uncertainty_band: z.number().min(0.03).max(0.5).optional().default(0.08).describe("F7 humility band"),
  },
  async (args) => {
    const result = projectCompoundGrowth(args.pv, args.rate_annual, args.years, args.uncertainty_band);
    return textContent(result);
  }
);

server.tool(
  "wealth_project_runway",
  "Project runway depletion given liquid assets, monthly burn, and monthly income.",
  {
    liquid_assets: z.number().describe("Liquid assets"),
    monthly_burn: z.number().describe("Monthly expenses/burn"),
    monthly_income: z.number().optional().default(0).describe("Monthly income offset"),
  },
  async (args) => {
    const result = projectRunwayDepletion(args.liquid_assets, args.monthly_burn, args.monthly_income);
    return textContent(result);
  }
);

// ── Resources ────────────────────────────────────────────────────────────────

server.resource(
  "wealth://governance/floors",
  "wealth://governance/floors",
  { mimeType: "application/json" },
  async () => ({
    contents: [
      {
        uri: "wealth://governance/floors",
        mimeType: "application/json",
        text: JSON.stringify({ FLOORS, HOLD }, null, 2),
      },
    ],
  })
);

server.resource(
  "wealth://governance/epistemic",
  "wealth://governance/epistemic",
  { mimeType: "application/json" },
  async () => ({
    contents: [
      {
        uri: "wealth://governance/epistemic",
        mimeType: "application/json",
        text: JSON.stringify({ EPISTEMIC }, null, 2),
      },
    ],
  })
);

server.resource(
  "wealth://sample/state",
  "wealth://sample/state",
  { mimeType: "application/json" },
  async () => ({
    contents: [
      {
        uri: "wealth://sample/state",
        mimeType: "application/json",
        text: JSON.stringify(
          {
            version: "1.1.0",
            metadata: { currency: "MYR", timezone: "Asia/Kuala_Lumpur" },
            assets: [
              { id: "asb_01", name: "ASB", value: 50000, tag: "CLAIM" },
              { id: "epf_01", name: "EPF Account 1", value: 120000, tag: "PLAUSIBLE" },
            ],
            liabilities: [
              { id: "loan_01", name: "Rumah Seri Kembangan", value: 350000, type: "MORTGAGE" },
            ],
            maruah: {
              score: 0.95,
              grade: "AAA_GRADE",
              factors: {
                integrity: 1.0,
                sovereignty: 0.9,
                debtDignity: 1.0,
                amanah: 1.0,
                community: 0.85,
              },
            },
          },
          null,
          2
        ),
      },
    ],
  })
);

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write("[wealth-mcp] Server started on stdio\n");
}

main().catch((err) => {
  process.stderr.write(`[wealth-mcp] Fatal: ${err}\n`);
  process.exit(1);
});
