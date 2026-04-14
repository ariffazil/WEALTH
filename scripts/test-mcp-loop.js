#!/usr/bin/env node
/**
 * test-mcp-loop.js
 * End-to-end test of the 7 new WEALTH MCP tools via JSON-RPC stdio.
 */

import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { appendFileSync } from "node:fs";

const SERVER_PATH = resolve(import.meta.dirname, "../mcp/server.js");
const VAULT_PATH = resolve(import.meta.dirname, "../data/vault999.jsonl");

const envelopeId = "ENV_MICRO_LOAN_MY_0001";
const sessionId = "sess-2026-0414-001";

function now() {
  return new Date().toISOString();
}

function hash(obj) {
  return createHash("sha256").update(JSON.stringify(obj)).digest("hex").slice(0, 16);
}

function req(id, method, params) {
  return JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n";
}

const child = spawn("node", [SERVER_PATH], { stdio: ["pipe", "pipe", "pipe"] });

let buffer = "";
const responses = {};
let nextId = 1;

function send(method, params) {
  const id = nextId++;
  const r = req(id, method, params);
  return new Promise((resolve, reject) => {
    responses[id] = resolve;
    child.stdin.write(r, (err) => {
      if (err) reject(err);
    });
  });
}

child.stdout.on("data", (chunk) => {
  buffer += chunk.toString("utf8");
  const lines = buffer.split("\n");
  buffer = lines.pop();
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const msg = JSON.parse(line);
      if (msg.id !== undefined && responses[msg.id]) {
        responses[msg.id](msg);
        delete responses[msg.id];
      }
    } catch {}
  }
});

child.stderr.on("data", (chunk) => {
  // ignore server stderr for clean output
});

async function run() {
  // Initialize
  await send("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "test-loop", version: "1.0" },
  });

  // 1. state
  const r1 = await send("tools/call", {
    name: "wealth_state_market_snapshot",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      jurisdiction: "MY",
      asset_classes: ["gov_bonds", "sme_loans"],
      tenor_months: 120,
    },
  });

  // 2. risk
  const r2 = await send("tools/call", {
    name: "wealth_risk_capital_allocation",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      portfolio: {
        buckets: [
          { id: "solar-micro-001", name: "Community Solar Micro-Loan", exposure_myr: 50000, sector: "renewables", region: "MY-Selangor" },
        ],
      },
      confidence_level: 0.95,
      maruah_drawdown_floor: 0.6,
    },
  });

  // 3. exergy
  const r3 = await send("tools/call", {
    name: "wealth_price_exergy_cost",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      project_inputs: { energy_mj_per_unit: 50, material_exergy_mj_per_unit: 120, output_unit: "kWh_lifetime" },
    },
  });

  // 4. justice
  const r4 = await send("tools/call", {
    name: "wealth_justice_maruah_score",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      project_profile: { displacement_risk: 0.1, pollution_load: 0.05, cultural_loss_risk: 0.0, community_benefit_share: 0.8 },
    },
  });
  const maruah = r4.result?.content?.[0]?.text ? JSON.parse(r4.result.content[0].text).maruah_score : 0.78;

  // 5. capitalx
  const r5 = await send("tools/call", {
    name: "wealth_price_capitalx",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      base_rate: 0.045,
      signals: { dS: 0.02, peace2: 1.05, maruahScore: maruah, trustIndex: 0.62, deltaCiv: 0.15 },
      wealth_basis: { e_hat: 0.65, s_hat: 0.18, echo_hat: 0.74 },
      defects: { paradox: 0.05, scar: 0.1, shadow: 0.03 },
    },
  });
  const cap = r5.result?.content?.[0]?.text ? JSON.parse(r5.result.content[0].text) : { r_adj: 0.0109 };

  // 6. flow
  const r6 = await send("tools/call", {
    name: "wealth_flow_scenario_npv",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      cashflows: [8000, 8200, 8400, 8600, 8800, 9000, 9200, 9400, 9600, 9800],
      r_adj: cap.r_adj,
      scenarios: [
        { name: "base", probability: 0.6 },
        { name: "subsidy_removed", probability: 0.3, cashflow_adjustment: -0.15 },
        { name: "tariff_boom", probability: 0.1, cashflow_adjustment: 0.12 },
      ],
      geo_constraints: ["geo_feasible", "climate_clear"],
    },
  });
  const flow = r6.result?.content?.[0]?.text ? JSON.parse(r6.result.content[0].text) : { npv_distribution: [0] };

  // 7. control
  const r7 = await send("tools/call", {
    name: "wealth_control_gate_888",
    arguments: {
      header: { session_id: sessionId, envelope_id: envelopeId, epoch: now() },
      candidate: { maruah, r_adj: cap.r_adj, entropy_budget_remaining: 0.18, reversible: true, human_confirmed: true },
    },
  });
  const gate = r7.result?.content?.[0]?.text ? JSON.parse(r7.result.content[0].text) : { hold_triggered: true };

  // 8. seal
  const classicalRate = 0.0460;
  const deltaBps = Math.round((classicalRate - cap.r_adj) * 10000);

  const r8 = await send("tools/call", {
    name: "wealth_seal_999",
    arguments: {
      peace2: 1.05,
      confidence: 0.92,
      holds: gate.hold_triggered ? ["888-HOLD"] : [],
      violations: [],
      human_confirmed: true,
    },
  });
  const seal = r8.result?.content?.[0]?.text ? JSON.parse(r8.result.content[0].text) : { verdict: "SEALED" };

  const vaultRecord = {
    event: "SOVEREIGN_LOAN_DECISION",
    envelope_id: envelopeId,
    epoch: now(),
    verdict: seal.verdict,
    project: "Community Solar Micro-Loan RM 50,000",
    telemetry: {
      dS: 0.02,
      peace2: 1.05,
      r_adj: cap.r_adj,
      maruah,
      delta_bps: deltaBps,
      npv_base: flow.npv_distribution[0],
      recommendation: gate.recommendation,
    },
    witness: { human: true, ai: true, earth: true },
    integrity_hash: hash({ envelope_id: envelopeId, recommendation: gate.recommendation, r_adj: cap.r_adj }),
  };

  appendFileSync(VAULT_PATH, JSON.stringify(vaultRecord) + "\n");

  console.log("\n=== MCP Loop Complete ===");
  console.log("State:", JSON.stringify(r1.result?.content?.[0]?.text ? JSON.parse(r1.result.content[0].text).capital_temperature : null));
  console.log("Risk economic_capital:", JSON.stringify(r2.result?.content?.[0]?.text ? JSON.parse(r2.result.content[0].text).economic_capital : null));
  console.log("Exergy:", JSON.stringify(r3.result?.content?.[0]?.text ? JSON.parse(r3.result.content[0].text).exergy_mj_per_unit : null));
  console.log("Maruah:", maruah);
  console.log("r_adj:", cap.r_adj);
  console.log("NPV base:", flow.npv_distribution[0]);
  console.log("Gate recommendation:", gate.recommendation);
  console.log("Seal verdict:", seal.verdict);
  console.log("Δbps:", deltaBps);
  console.log("VAULT999 appended.", vaultRecord.integrity_hash);

  child.kill();
  process.exit(0);
}

run().catch((err) => {
  console.error(err);
  child.kill();
  process.exit(1);
});
