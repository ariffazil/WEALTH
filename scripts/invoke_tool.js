/**
 * Bridge script to invoke WEALTH Dimensional Valuation tools.
 * 
 * Naming: Metric_Dimension (e.g., wealth_npv_reward)
 * Logic: Physics > Narrative
 */
import { calculateRiskAdjustedRate, compareCapitalAdvantage } from "../host/kernel/capitalx.js";
import { computeNetWorth } from "../host/wealth/networth.js";
import { computeCashflow } from "../host/wealth/cashflow.js";
import { projectCompoundGrowth, projectRunwayDepletion } from "../host/wealth/projection.js";

const [,, toolName, argsJson] = process.argv;
const args = JSON.parse(argsJson || "{}");

const tools = {
  // --- REWARD ---
  "npv_reward": (a) => {
    const { initial_investment, cash_flows, discount_rate, terminal_value = 0 } = a;
    let npv = -initial_investment;
    for (let t = 0; t < cash_flows.length; t++) {
      npv += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    if (terminal_value > 0) {
      npv += terminal_value / Math.pow(1 + discount_rate, cash_flows.length);
    }
    const eaa = (npv * discount_rate) / (1 - Math.pow(1 + discount_rate, -cash_flows.length));
    return { npv: Number(npv.toFixed(2)), eaa: Number(eaa.toFixed(2)), epistemic: "CLAIM" };
  },

  // --- ENERGY / YIELD ---
  "irr_yield": (a) => {
    const { initial_investment, cash_flows, reinvestment_rate = 0.1 } = a;
    // Simple Newton-Raphson for IRR
    const npv_func = (r) => {
      let val = -initial_investment;
      for (let t = 0; t < cash_flows.length; t++) {
        val += cash_flows[t] / Math.pow(1 + r, t + 1);
      }
      return val;
    };
    let irr = 0.1;
    for (let i = 0; i < 20; i++) {
      let val = npv_func(irr);
      let eps = 0.0001;
      let derivative = (npv_func(irr + eps) - val) / eps;
      irr = irr - val / derivative;
    }
    // MIRR
    const n = cash_flows.length;
    let fv_inflows = 0;
    for (let t = 0; t < n; t++) {
      if (cash_flows[t] > 0) fv_inflows += cash_flows[t] * Math.pow(1 + reinvestment_rate, n - (t + 1));
    }
    const mirr = Math.pow(fv_inflows / initial_investment, 1 / n) - 1;
    return { irr: Number(irr.toFixed(4)), mirr: Number(mirr.toFixed(4)), epistemic: "CLAIM" };
  },

  "pi_efficiency": (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let pv_inflows = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      pv_inflows += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    return { pi: Number((pv_inflows / initial_investment).toFixed(4)), epistemic: "CLAIM" };
  },

  // --- ENTROPY / RISK ---
  "emv_risk": (a) => {
    const { scenarios } = a;
    const emv = scenarios.reduce((acc, s) => acc + (s.probability * s.outcome), 0);
    return { emv: Number(emv.toFixed(2)), epistemic: "CLAIM" };
  },

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
    // Simple sensitivity sweep
    const variations = [0.8, 0.9, 1.0, 1.1, 1.2];
    const sensitivity = variations.map(v => {
      let npv = -initial_investment;
      for (let t = 0; t < cash_flows.length; t++) npv += cash_flows[t] / Math.pow(1 + (discount_rate * v), t + 1);
      return { var: v, npv: Number(npv.toFixed(2)) };
    });
    return { sign_changes, sensitivity, verdict: sign_changes > 1 ? "NON_NORMAL" : "NORMAL", epistemic: "CLAIM" };
  },

  "dscr_leverage": (a) => {
    const { ebitda, principal, interest } = a;
    return { dscr: Number((ebitda / (principal + interest)).toFixed(2)), epistemic: "CLAIM" };
  },

  // --- TIME ---
  "payback_time": (a) => {
    const { initial_investment, cash_flows, discount_rate = 0 } = a;
    let remaining = initial_investment;
    let years = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      let cf = discount_rate > 0 ? cash_flows[t] / Math.pow(1 + discount_rate, t + 1) : cash_flows[t];
      if (remaining > cf) { remaining -= cf; years++; }
      else { years += remaining / cf; remaining = 0; break; }
    }
    return { payback_years: Number(years.toFixed(2)), epistemic: "CLAIM" };
  },

  "growth_velocity": (a) => {
    const { principal, rate, years, annual_contribution = 0, monthly_burn = 0 } = a;
    const growth = projectCompoundGrowth(principal, rate, years, annual_contribution);
    const runway = monthly_burn > 0 ? projectRunwayDepletion(principal, monthly_burn, 0) : { status: "INFINITE" };
    return { growth, runway, epistemic: "CLAIM" };
  },

  // --- STATE ---
  "networth_state": (a) => computeNetWorth(a.assets, a.liabilities),
  "cashflow_flow": (a) => computeCashflow(a.income, a.expenses),

  // --- KERNEL ---
  "score_kernel": (a) => {
    if (a.compare) return compareCapitalAdvantage(a.base_rate, a.wealth_signals, a.extractive_signals);
    return calculateRiskAdjustedRate(a.base_rate, a);
  }
};

if (!tools[toolName]) {
  console.error(`Unknown tool: ${toolName}`);
  process.exit(1);
}

try {
  const result = await tools[toolName](args);
  console.log(JSON.stringify(result, null, 2));
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
