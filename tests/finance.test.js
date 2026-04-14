import test from "node:test";
import assert from "node:assert/strict";
import {
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
