/**
 * Bridge script to invoke WEALTH valuation tools from Python/CLI.
 * 
 * WEALTH = Valuation Kernel (NPV, IRR, Networth, Cashflow).
 * Governance (Floors/Seal) moves to arifOS.
 * World-state (Macro) moves to GEOX.
 */
import { calculateRiskAdjustedRate, compareCapitalAdvantage } from "../host/kernel/capitalx.js";
import { computeNetWorth } from "../host/wealth/networth.js";
import { computeCashflow } from "../host/wealth/cashflow.js";
import { projectCompoundGrowth, projectRunwayDepletion } from "../host/wealth/projection.js";

const [,, toolName, argsJson] = process.argv;
const args = JSON.parse(argsJson || "{}");

const tools = {
  // --- Personal & Portfolio Valuation (wealth.personal.*) ---
  "personal.networth": (a) => computeNetWorth(a.assets, a.liabilities),
  "personal.cashflow": (a) => computeCashflow(a.income, a.expenses),
  "personal.growth": (a) => projectCompoundGrowth(a.principal, a.rate, a.years, a.annual_contribution),
  "personal.runway": (a) => projectRunwayDepletion(a.current_savings, a.monthly_burn, a.monthly_income),

  // --- Capital & Project Evaluation (wealth.capital.*) ---
  "capital.score": (a) => calculateRiskAdjustedRate(a.base_rate, a),
  "capital.compare": (a) => compareCapitalAdvantage(a.base_rate, a.wealth_signals, a.extractive_signals),
  
  "capital.npv": (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let npv = -initial_investment;
    for (let t = 0; t < cash_flows.length; t++) {
      npv += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    return { npv: Number(npv.toFixed(2)), epistemic: "CLAIM" };
  },

  "capital.irr": (a) => {
    const { initial_investment, cash_flows } = a;
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
    return { irr: Number(irr.toFixed(4)), epistemic: "CLAIM" };
  },

  "capital.mirr": (a) => {
    const { initial_investment, cash_flows, finance_rate, reinvestment_rate } = a;
    const n = cash_flows.length;
    let fv_inflows = 0;
    for (let t = 0; t < n; t++) {
      if (cash_flows[t] > 0) {
        fv_inflows += cash_flows[t] * Math.pow(1 + reinvestment_rate, n - (t + 1));
      }
    }
    const mirr = Math.pow(fv_inflows / initial_investment, 1 / n) - 1;
    return { mirr: Number(mirr.toFixed(4)), epistemic: "CLAIM" };
  },

  "capital.emv": (a) => {
    const { scenarios } = a;
    const emv = scenarios.reduce((acc, s) => acc + (s.probability * s.outcome), 0);
    return { emv: Number(emv.toFixed(2)), epistemic: "CLAIM" };
  },

  "capital.pi": (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let pv_inflows = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      pv_inflows += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    const pi = pv_inflows / initial_investment;
    return { profitability_index: Number(pi.toFixed(4)), epistemic: "CLAIM" };
  },

  "capital.payback": (a) => {
    const { initial_investment, cash_flows, discounted = false, discount_rate = 0 } = a;
    let remaining = initial_investment;
    let years = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      let cf = discounted ? cash_flows[t] / Math.pow(1 + discount_rate, t + 1) : cash_flows[t];
      if (remaining > cf) {
        remaining -= cf;
        years++;
      } else {
        years += remaining / cf;
        remaining = 0;
        break;
      }
    }
    return { payback_years: remaining === 0 ? Number(years.toFixed(2)) : Infinity, epistemic: "CLAIM" };
  },

  "capital.roi": (a) => {
    const { initial_investment, cash_flows } = a;
    const total_return = cash_flows.reduce((acc, cf) => acc + cf, 0);
    const roi = (total_return - initial_investment) / initial_investment;
    return { roi: Number(roi.toFixed(4)), epistemic: "CLAIM" };
  },

  "capital.eaa": (a) => {
    const { npv, discount_rate, years } = a;
    const eaa = (npv * discount_rate) / (1 - Math.pow(1 + discount_rate, -years));
    return { eaa: Number(eaa.toFixed(2)), epistemic: "CLAIM" };
  },

  "capital.audit": (a) => {
    const { initial_investment, cash_flows } = a;
    let sign_changes = 0;
    let current_sign = -1;
    for (const cf of cash_flows) {
      if (cf !== 0) {
        let sign = cf > 0 ? 1 : -1;
        if (sign !== current_sign) {
          sign_changes++;
          current_sign = sign;
        }
      }
    }
    const warnings = [];
    if (sign_changes > 1) warnings.push("Non-normal cash flows: Multiple IRRs possible.");
    if (initial_investment <= 0) warnings.push("Zero or negative initial investment detected.");
    return { sign_changes, potential_issues: warnings, audit_verdict: warnings.length === 0 ? "PASS" : "WARN", epistemic: "CLAIM" };
  },

  "capital.dscr": (a) => {
    const { ebitda, principal, interest } = a;
    const dscr = ebitda / (principal + interest);
    return {
      dscr: Number(dscr.toFixed(2)),
      verdict: dscr >= 1.2 ? "SAFE" : "RISK",
      epistemic: "CLAIM"
    };
  },

  "capital.terminal": (a) => {
    const { final_cash_flow, growth_rate, wacc, method = "gordon_growth", exit_multiple = 0 } = a;
    let terminal_value = 0;
    if (method === "gordon_growth") {
      terminal_value = (final_cash_flow * (1 + growth_rate)) / (wacc - growth_rate);
    } else if (method === "exit_multiple") {
      terminal_value = final_cash_flow * exit_multiple;
    }
    return {
      terminal_value: Number(terminal_value.toFixed(2)),
      method,
      epistemic: "CLAIM"
    };
  },

  "capital.sensitivity": (a) => {
    const { initial_investment, cash_flows, discount_rate, variations = [0.9, 1.0, 1.1] } = a;
    const results = variations.map(v => {
      const adj_dr = discount_rate * v;
      let npv = -initial_investment;
      for (let t = 0; t < cash_flows.length; t++) {
        npv += cash_flows[t] / Math.pow(1 + adj_dr, t + 1);
      }
      return { variation: v, discount_rate: adj_dr, npv: Number(npv.toFixed(2)) };
    });
    return { sensitivity_table: results, epistemic: "CLAIM" };
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
