export function projectCompoundGrowth(principal, rate, years, annual_contribution = 0) {
  let total = principal;
  for (let y = 1; y <= years; y++) {
    total = total * (1 + rate) + annual_contribution;
  }
  return {
    final_value: Number(total.toFixed(2)),
    total_contributed: principal + annual_contribution * years,
    growth_only: Number((total - principal - annual_contribution * years).toFixed(2)),
    uncertainty_band: [0.03, 0.12],
    epistemic: "ESTIMATE",
    vault_log_entry: { tool: "wealth_project_growth", epoch: new Date().toISOString() },
    witness: { human: false, ai: true, earth: true },
  };
}

export function projectRunwayDepletion(current_savings, monthly_burn, monthly_income = 0) {
  const net = monthly_income - monthly_burn;
  const months = net >= 0 ? Infinity : current_savings / -net;
  return {
    runway_months: net >= 0 ? Infinity : Number(months.toFixed(1)),
    net_monthly: net,
    epistemic: "ESTIMATE",
    vault_log_entry: { tool: "wealth_project_runway", epoch: new Date().toISOString() },
    witness: { human: false, ai: true, earth: true },
  };
}
