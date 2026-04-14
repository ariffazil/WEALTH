/**
 * Bridge script to invoke WEALTH functions from Python/CLI.
 */
import { checkFloors } from "../host/kernel/floors.js";
import { seal999 } from "../host/kernel/seal.js";
import { calculateRiskAdjustedRate, compareCapitalAdvantage } from "../host/kernel/capitalx.js";
import { computeNetWorth } from "../host/wealth/networth.js";
import { computeCashflow } from "../host/wealth/cashflow.js";
import { computeMaruahScore } from "../host/wealth/maruah-score.js";
import { projectCompoundGrowth, projectRunwayDepletion } from "../host/wealth/projection.js";
import { computeCivilizationalProsperityIndex } from "../host/civilizational/prosperity_index.js";
import { detectSystemicRisk } from "../host/civilizational/cascade_detector.js";

const [,, toolName, argsJson] = process.argv;
const args = JSON.parse(argsJson || "{}");

const tools = {
  check_floors: (a) => checkFloors(a),
  seal_999: (a) => seal999(a),
  capitalx_score: (a) => calculateRiskAdjustedRate(a.base_rate, a),
  capitalx_compare: (a) => compareCapitalAdvantage(a.base_rate, a.wealth_signals, a.extractive_signals),
  compute_networth: (a) => computeNetWorth(a.assets, a.liabilities),
  compute_cashflow: (a) => computeCashflow(a.income, a.expenses),
  compute_maruah: (a) => computeMaruahScore(a),
  project_growth: (a) => projectCompoundGrowth(a.principal, a.rate, a.years, a.annual_contribution),
  project_runway: (a) => projectRunwayDepletion(a.current_savings, a.monthly_burn, a.monthly_income),
  civilizational_prosperity: (a) => computeCivilizationalProsperityIndex(a),
  civilizational_risk: (a) => detectSystemicRisk(a),
  
  // --- Capital Budgeting & Project Analysis (F2 CLAIM) ---
  
  capital_npv: (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let npv = -initial_investment;
    for (let t = 0; t < cash_flows.length; t++) {
      npv += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    return { 
      npv: Number(npv.toFixed(2)),
      verdict: npv > 0 ? "SEAL" : "VOID",
      epistemic: "CLAIM",
      timestamp: new Date().toISOString()
    };
  },

  capital_irr: (a) => {
    const { initial_investment, cash_flows } = a;
    // Simple Newton-Raphson for IRR
    const npv_func = (r) => {
      let val = -initial_investment;
      for (let t = 0; t < cash_flows.length; t++) {
        val += cash_flows[t] / Math.pow(1 + r, t + 1);
      }
      return val;
    };
    let irr = 0.1; // Initial guess
    for (let i = 0; i < 20; i++) {
      let val = npv_func(irr);
      let eps = 0.0001;
      let derivative = (npv_func(irr + eps) - val) / eps;
      irr = irr - val / derivative;
    }
    return { 
      irr: Number(irr.toFixed(4)),
      epistemic: "CLAIM",
      timestamp: new Date().toISOString()
    };
  },

  capital_emv: (a) => {
    const { scenarios } = a; // [{ probability, outcome }]
    const emv = scenarios.reduce((acc, s) => acc + (s.probability * s.outcome), 0);
    return { 
      emv: Number(emv.toFixed(2)),
      epistemic: "CLAIM",
      timestamp: new Date().toISOString()
    };
  },

  capital_pi: (a) => {
    const { initial_investment, cash_flows, discount_rate } = a;
    let pv_inflows = 0;
    for (let t = 0; t < cash_flows.length; t++) {
      pv_inflows += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
    }
    const pi = pv_inflows / initial_investment;
    return { 
      profitability_index: Number(pi.toFixed(4)),
      verdict: pi > 1 ? "SEAL" : "VOID",
      epistemic: "CLAIM"
    };
  },

  capital_payback: (a) => {
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
    return { 
      payback_years: remaining === 0 ? Number(years.toFixed(2)) : Infinity,
      epistemic: "CLAIM"
    };
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
