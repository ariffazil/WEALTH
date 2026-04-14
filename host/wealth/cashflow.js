export function computeCashflow(income = [], expenses = []) {
  const totalIncome = income.reduce((sum, i) => sum + (i.active ? (i.monthly_amount ?? 0) : 0), 0);
  const totalExpenses = expenses.reduce((sum, e) => sum + (e.active ? (e.monthly_amount ?? 0) : 0), 0);
  const net = totalIncome - totalExpenses;
  return {
    monthly_income: totalIncome,
    monthly_expenses: totalExpenses,
    net_monthly: net,
    runway_months: net > 0 ? Infinity : 0,
    burn_rate: net < 0 ? -net : 0,
    epistemic: "ESTIMATE",
    vault_log_entry: { tool: "wealth_compute_cashflow", epoch: new Date().toISOString() },
    witness: { human: false, ai: true, earth: true },
  };
}
