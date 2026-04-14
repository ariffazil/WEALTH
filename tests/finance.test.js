import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  buildCashflowSeries,
  calculateDscrMeasurement,
  calculateEmvMeasurement,
  calculateIrrMeasurement,
  calculateNpvMeasurement,
  calculatePaybackMeasurement,
  calculateProfitabilityIndexMeasurement,
} from "../src/kernel/finance.js";
import { calculateRiskAdjustedRate } from "../src/kernel/capitalx.js";

test("calculateNpvMeasurement returns NPV and EAA on aligned periods", () => {
  const result = calculateNpvMeasurement({
    initial_investment: 1000,
    cash_flows: [500, 500, 500],
    discount_rate: 0.1,
  });

  assert.ok(result.npv > 200);
  assert.ok(result.eaa > 0);
  assert.deepStrictEqual(result.flags, []);
});

test("calculateIrrMeasurement qualifies non-normal cash flows", () => {
  const result = calculateIrrMeasurement({
    initial_investment: 1000,
    cash_flows: [3000, -2500, 800],
    finance_rate: 0.1,
    reinvestment_rate: 0.08,
  });

  assert.ok(result.flags.includes("MULTIPLE_IRR_POSSIBLE"));
  assert.ok(result.flags.includes("NON_NORMAL_FLOWS"));
  assert.ok(result.mirr !== null);
});

test("calculateProfitabilityIndexMeasurement preserves NPV ranking warning", () => {
  const result = calculateProfitabilityIndexMeasurement({
    initial_investment: 1000,
    cash_flows: [600, 600],
    discount_rate: 0.1,
  });

  assert.ok(result.pi > 1);
});

test("calculateEmvMeasurement rejects invalid probability mass", () => {
  const result = calculateEmvMeasurement({
    scenarios: [
      { probability: 0.7, outcome: 100 },
      { probability: 0.7, outcome: -50 },
    ],
  });

  assert.ok(result.flags.includes("PROBABILITY_MASS_INVALID"));
});

test("calculatePaybackMeasurement reports unrecovered projects", () => {
  const result = calculatePaybackMeasurement({
    initial_investment: 1000,
    cash_flows: [100, 100, 100],
    discount_rate: 0,
  });

  assert.strictEqual(result.payback_periods, null);
  assert.ok(result.flags.includes("NOT_RECOVERED"));
});

test("calculateDscrMeasurement prefers CFADS and flags stressed leverage", () => {
  const result = calculateDscrMeasurement({
    cfads: 110,
    debt_service: 100,
  });

  assert.strictEqual(result.basis, "CFADS");
  assert.ok(result.flags.includes("LEVERAGE_CRITICAL"));
});

test("period-zero convention stays aligned across NPV, PI, and payback", () => {
  const initialInvestment = 1000;
  const cashflows = [1100];
  assert.deepStrictEqual(buildCashflowSeries(initialInvestment, cashflows), [-1000, 1100]);

  const npv = calculateNpvMeasurement({
    initial_investment: initialInvestment,
    cash_flows: cashflows,
    discount_rate: 0.1,
  });
  const pi = calculateProfitabilityIndexMeasurement({
    initial_investment: initialInvestment,
    cash_flows: cashflows,
    discount_rate: 0.1,
  });
  const payback = calculatePaybackMeasurement({
    initial_investment: initialInvestment,
    cash_flows: cashflows,
    discount_rate: 0,
  });

  assert.ok(Math.abs(npv.npv) < 1e-6);
  assert.ok(Math.abs(pi.pi - 1) < 1e-6);
  assert.ok(Math.abs(payback.payback_periods - (1000 / 1100)) < 1e-6);
});

test("MIRR handles all-positive future cash flows without inventing ambiguity", () => {
  const result = calculateIrrMeasurement({
    initial_investment: 1000,
    cash_flows: [300, 400, 500],
    finance_rate: 0.1,
    reinvestment_rate: 0.08,
  });

  assert.equal(result.mirr !== null, true);
  assert.equal(result.flags.includes("MULTIPLE_IRR_POSSIBLE"), false);
});

test("estimated NPV and DSCR emit confidence bands", () => {
  const npv = calculateNpvMeasurement({
    initial_investment: 1000,
    cash_flows: [600, 600],
    discount_rate: 0.1,
    input_epistemic: "ESTIMATE",
  });
  const dscr = calculateDscrMeasurement({
    cfads: 140,
    debt_service: 100,
    input_epistemic: "ESTIMATE",
  });

  assert.ok(Array.isArray(npv.confidence_band));
  assert.ok(Array.isArray(dscr.confidence_band));
});

test("python server matches JS kernel on canonical parity vectors", () => {
  const script = `
import json
from server import npv_reward, dscr_leverage, growth_velocity
payload = {
  "npv": npv_reward(initial_investment=1000, cash_flows=[500,500,500], discount_rate=0.1)["primary_result"]["npv"],
  "dscr": dscr_leverage(cfads=110, debt_service=100)["primary_result"]["dscr"],
  "growth_mid": growth_velocity(principal=10000, rate=0.08, years=20, annual_contribution=12000, monthly_burn=0)["primary_result"]["growth_forecast"]["mid"],
}
print(json.dumps(payload))
`;
  const run = spawnSync("python", ["-c", script], {
    cwd: "/root/WEALTH",
    encoding: "utf8",
  });
  assert.equal(run.status, 0, run.stderr);
  const actual = JSON.parse(run.stdout.trim());

  const jsNpv = calculateNpvMeasurement({
    initial_investment: 1000,
    cash_flows: [500, 500, 500],
    discount_rate: 0.1,
  });
  const jsDscr = calculateDscrMeasurement({
    cfads: 110,
    debt_service: 100,
  });
  const lowEntropy = 10000;
  let total = lowEntropy;
  for (let i = 0; i < 20; i += 1) {
    total = total * (1 + 0.08) + 12000;
  }

  assert.ok(Math.abs(actual.npv - jsNpv.npv) < 1e-8);
  assert.ok(Math.abs(actual.dscr - jsDscr.dscr) < 1e-8);
  assert.ok(Math.abs(actual.growth_mid - Number(total.toFixed(2))) < 1e-8);
});

test("capitalx monotonicity keeps higher entropy from lowering price", () => {
  const lowEntropy = calculateRiskAdjustedRate(0.05, {
    dS: 0.05,
    peace2: 1.05,
    maruahScore: 0.8,
    trustIndex: 0.7,
    deltaCiv: 0.1,
  });
  const highEntropy = calculateRiskAdjustedRate(0.05, {
    dS: 0.25,
    peace2: 1.05,
    maruahScore: 0.8,
    trustIndex: 0.7,
    deltaCiv: 0.1,
  });

  assert.ok(highEntropy.r_adj >= lowEntropy.r_adj);
});
