export function computeNetWorth(assets = [], liabilities = []) {
  const assetValue = assets.reduce((sum, a) => sum + (a.value ?? 0), 0);
  const liabilityValue = liabilities.reduce((sum, l) => sum + (l.principal ?? 0), 0);
  return {
    net_worth: assetValue - liabilityValue,
    assets: assetValue,
    liabilities: liabilityValue,
    epistemic: "ESTIMATE",
    vault_log_entry: { tool: "wealth_compute_networth", epoch: new Date().toISOString() },
    witness: { human: false, ai: true, earth: true },
  };
}
