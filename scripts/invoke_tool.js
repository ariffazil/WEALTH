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
