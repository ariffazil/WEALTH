/**
 * WEALTH Dimensional Kernel v1.3.0 - invoke_tool.js
 * Logic: Physics > Narrative
 * Convention: Absolute-Input, Under-Score Naming, Common Envelope
 */
import { calculateRiskAdjustedRate, compareCapitalAdvantage } from "../host/kernel/capitalx.js";
import { computeNetWorth } from "../host/wealth/networth.js";
import { computeCashflow } from "../host/wealth/cashflow.js";
import { projectCompoundGrowth, projectRunwayDepletion } from "../host/wealth/projection.js";

const [,, toolName, argsJson] = process.argv;
const args = JSON.parse(argsJson || "{}");

const ASSET_CLASSES = ["cash", "equity", "property", "digital", "debt", "business"];

function createEnvelope(tool, dimension, primary, secondary = {}, flags = []) {
  return {
    tool,
    dimension,
    verdict: "SEAL",
    primary_result: primary,
    secondary_metrics: secondary,
    integrity_flags: flags,
    confidence: "HIGH",
    epistemic: "CLAIM",
    epoch: new Date().toISOString()
  };
}

const tools = {
  // 1. REWARD (wealth_npv_reward)
  "npv_reward": (a) => {
    const { initial_investment, cash_flows, discount_rate, terminal_value = 0, period_unit = "annual" } = a;
    let npv = -Math.abs(initial_investment);
    for (let t = 0; t < cash_flows.length; t++) {
      npv += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    if (terminal_value > 0) npv += terminal_value / Math.pow(1 + discount_rate, cash_flows.length);
    const eaa = (npv * discount_rate) / (1 - Math.pow(1 + discount_rate, -cash_flows.length));
    return createEnvelope("wealth_npv_reward", "Reward", { npv: Number(npv.toFixed(2)) }, { eaa: Number(eaa.toFixed(2)), period_unit });
  },

  // 2. ENERGY / YIELD (wealth_irr_yield)
  "irr_yield": (a) => {
    const { initial_investment, cash_flows, reinvestment_rate = 0.1, period_unit = "annual" } = a;
    const inv = -Math.abs(initial_investment);
    const npv_func = (r) => {
      let val = inv;
      for (let t = 0; t < cash_flows.length; t++) val += cash_flows[t] / Math.pow(1 + r, t + 1);
      return val;
    };
    let irr = 0.1;
    for (let i = 0; i < 20; i++) {
      let val = npv_func(irr);
      let derivative = (npv_func(irr + 0.0001) - val) / 0.0001;
      irr = irr - val / derivative;
    }
    const n = cash_flows.length;
    let fv_inflows = 0;
    for (let t = 0; t < n; t++) if (cash_flows[t] > 0) fv_inflows += cash_flows[t] * Math.pow(1 + reinvestment_rate, n - (t + 1));
    const mirr = Math.pow(fv_inflows / Math.abs(inv), 1 / n) - 1;
    return createEnvelope("wealth_irr_yield", "Energy", { irr: Number(irr.toFixed(4)) }, { mirr: Number(mirr.toFixed(4)), period_unit });
  },

  // 3. ENERGY / CONCENTRATION (wealth_pi_efficiency)
  "pi_efficiency": (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let pv_inflows = 0;
    for (let t = 0; t < cash_flows.length; t++) pv_inflows += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    const pi = pv_inflows / Math.abs(initial_investment);
    return createEnvelope("wealth_pi_efficiency", "Energy", { pi: Number(pi.toFixed(4)) }, { verdict: pi >= 1 ? "EFFICIENT" : "EXTRACTIVE" });
  },

  // 4. ENTROPY / RISK (wealth_emv_risk)
  "emv_risk": (a) => {
    const { scenarios } = a;
    const emv = scenarios.reduce((acc, s) => acc + (s.probability * s.outcome), 0);
    return createEnvelope("wealth_emv_risk", "Entropy", { emv: Number(emv.toFixed(2)) }, { scenario_count: scenarios.length });
  },

  // 5. ENTROPY / INTEGRITY (wealth_audit_entropy)
  "audit_entropy": (a) => {
    const { initial_investment, cash_flows, discount_rate = 0.1 } = a;
    let sign_changes = 0;
    let current_sign = -1;
    for (const cf of cash_flows) {
      if (cf !== 0) {
        let sign = cf > 0 ? 1 : -1;
        if (sign !== current_sign) { sign_changes++; current_sign = sign; }
      }
    }
    const variations = [0.8, 0.9, 1.0, 1.1, 1.2];
    const sensitivity = variations.map(v => {
      let npv = -Math.abs(initial_investment);
      for (let t = 0; t < cash_flows.length; t++) npv += cash_flows[t] / Math.pow(1 + (discount_rate * v), t + 1);
      return { multiplier: v, npv: Number(npv.toFixed(2)) };
    });
    const flags = sign_changes > 1 ? ["MULTIPLE_IRR_RISK", "NON_NORMAL_FLOWS"] : [];
    return createEnvelope("wealth_audit_entropy", "Entropy", { sign_changes }, { sensitivity_sweep: sensitivity }, flags);
  },

  // 6. SURVIVAL / LEVERAGE (wealth_dscr_leverage)
  "dscr_leverage": (a) => {
    const { ebitda, principal, interest, period_unit = "annual" } = a;
    const dscr = ebitda / (principal + interest);
    const flags = dscr < 1.25 ? ["LEVERAGE_CRITICAL"] : [];
    return createEnvelope("wealth_dscr_leverage", "Survival", { dscr: Number(dscr.toFixed(2)) }, { period_unit }, flags);
  },

  // 7. TIME / RECOVERY (wealth_payback_time)
  "payback_time": (a) => {
    const { initial_investment, cash_flows, discount_rate = 0, period_unit = "annual" } = a;
    let remaining = Math.abs(initial_investment);
    let years = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      let cf = discount_rate > 0 ? cash_flows[t] / Math.pow(1 + discount_rate, t + 1) : cash_flows[t];
      if (remaining > cf) { remaining -= cf; years++; }
      else { years += remaining / cf; remaining = 0; break; }
    }
    return createEnvelope("wealth_payback_time", "Time", { payback_periods: Number(years.toFixed(2)) }, { period_unit, discounted: discount_rate > 0 });
  },

  // 8. VELOCITY / EXPANSION (wealth_growth_velocity)
  "growth_velocity": (a) => {
    const { principal, rate, years, annual_contribution = 0, monthly_burn } = a;
    const growth = projectCompoundGrowth(principal, rate, years, annual_contribution);
    const runway = projectRunwayDepletion(principal, monthly_burn, 0);
    return createEnvelope("wealth_growth_velocity", "Velocity", { growth_forecast: growth }, { runway_months: runway.months_remaining });
  },

  // 9. MASS / STATE (wealth_networth_state)
  "networth_state": (a) => {
    const validatedAssets = a.assets.map(asset => ({
      ...asset,
      tag: ASSET_CLASSES.includes(asset.tag?.toLowerCase()) ? asset.tag.toLowerCase() : "other"
    }));
    const result = computeNetWorth(validatedAssets, a.liabilities);
    return createEnvelope("wealth_networth_state", "Mass", result);
  },

  // 10. FLOW / METABOLIC (wealth_cashflow_flow)
  "cashflow_flow": (a) => {
    const result = computeCashflow(a.income, a.expenses);
    return createEnvelope("wealth_cashflow_flow", "Flow", result, { period_unit: "monthly" });
  },

  // 11. ALLOCATION / KERNEL (wealth_score_kernel)
  "score_kernel": (a) => {
    const { base_rate, dS, peace2, maruahScore, compare = false, wealth_signals = {}, extractive_signals = {} } = a;
    const flags = [];
    if (dS > 0.3) flags.push("HIGH_ENTROPY_SIGNAL");
    if (maruahScore < 0.6) flags.push("SOVEREIGN_DIGNITY_LOW");

    if (compare) {
      const comparison = compareCapitalAdvantage(base_rate, { dS, peace2, maruahScore, ...wealth_signals }, extractive_signals);
      return createEnvelope("wealth_score_kernel", "Allocation", comparison, {}, flags);
    }
    const score = calculateRiskAdjustedRate(base_rate, { dS, peace2, maruahScore, ...wealth_signals });
    return createEnvelope("wealth_score_kernel", "Allocation", score, {}, flags);
  }
};

if (!tools[toolName]) {
  console.error(`Unknown tool: ${toolName}`);
  process.exit(1);
}

try {
  const result = tools[toolName](args);
  console.log(JSON.stringify(result, null, 2));
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
