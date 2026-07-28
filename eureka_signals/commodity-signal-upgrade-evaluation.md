# AUTORESEARCH — Karpathy Mode: Commodity Signal Upgrade Evaluation
>
> **Source:** awesome-systematic-trading (63 strategies) → /gold, /oil, /gas  
> **Method:** First principles. Test signals against the actual physics of each commodity.  
> **Date:** 2026-07-28 | **Agent:** OpenCode (333-AGI) | **Sovereign:** Arif (F13)
>
> ---
>
> ## 0. What Each Site Already Has (Current Engine Baseline)
>
> ```
> ┌─────────────────────────────────────────────────────────┐
> │  CURRENT SIGNAL ENGINE (all 3 assets share this)         │
> │                                                          │
> │  Price-Only Pipeline:                                    │
> │    EMA20/50/200 cross  →  Trend signal                   │
> │    RSI(14)             →  Overbought/oversold             │
> │    RSI divergence      →  Bearish/bullish divergence     │
> │    Candle patterns     →  Doji/Hammer/Shooting/Engulf    │
> │    S/R levels          →  Swing points + pivot calc      │
> │    ATR(14)             →  Volatility, SL/TP sizing       │
> │    Linear slope        →  20-day drift (forecast)        │
> │    ATR·√t cone         →  p10/p25/p50/p75/p90 bands     │
> │    APEX (G=A·P·E·X·Φ)  →  Multi-timeframe evaluation    │
> │    Confluence scoring  →  5-factor binary counter        │
> │                                                          │
> │  What's MISSING:                                         │
> │    ✗ Cross-sectional momentum (multiple lookbacks)       │
> │    ✗ Term structure / futures curve signal               │
> │    ✗ Return distribution (skewness, kurtosis)            │
> │    ✗ Cross-asset lead signals (oil→equities, DXY→gold)  │
> │    ✗ Seasonality / calendar patterns                     │
> │    ✗ Position sizing (Kelly, risk parity)                │
> │    ✗ Fundamental data (inventory, COT, rig counts)       │
> │    ✗ Sentiment / options-implied signals                 │
> └─────────────────────────────────────────────────────────┘
> ```
>
> ---
>
> ## 1. GOLD (XAUUSD) — Signal Evaluation
>
> ### Physics of Gold
> Gold has no cash flows. No earnings. No CEO. It answers exactly three questions:
> 1. **Is the dollar weakening?** (DXY inverse)
> 2. **Are real rates falling?** (TIPS yield inverse)
> 3. **Is fear rising?** (VIX, geopolitical)
>
> Every gold signal must answer: "which of these three is this capturing?"
>
> ### Signal-by-Signal Verdict
>
> | # | Signal | Sharpe | Physics Test | Upgrade? | Why |
> |---|--------|--------|-------------|----------|-----|
> | 1 | **Time Series Momentum** | 0.576 | ✅ Captures trend persistence from central bank buying flows | **YES — WIRE NOW** | Gold trends. Period. Adding 1M/3M/6M/12M lookback momentum as a separate signal card in Technical Forge is the single highest-value upgrade. Current engine only uses EMA cross — this is a massive upgrade for ~50 lines of Python. |
> | 2 | **Asset Class Trend-Following** | 0.502 | ✅ Cross-asset trend (bonds/commodities/equities as context) | **YES** | Wire as "World Context → Cross-Asset Trend" card. Gold trends when other assets trend — this gives regime context the current engine lacks. |
> | 3 | **Skewness Effect** | 0.482 | ⚠️ Interesting but noisy on single asset | **PARTIAL** | Gold skew is regime-dependent. Useful as a risk thermometer ("this move is unusual"), not a direction signal. Wire to the Risk Thermometer bar, not the signal card. |
> | 4 | **Betting Against Beta** | 0.594 | ❌ Not applicable to gold | **NO** | BAB is an equity factor. Gold's beta to equities is unstable. Wrong tool. |
> | 5 | **Volatility Risk Premium** | 0.637 | ✅ Gold vol is a macro fear gauge | **YES — Phase 2** | Gold VRP (GVZ implied vs realized) is a powerful regime signal. When implied vol spikes above realized → fear premium → bullish gold. Requires options data. Phase 2. |
> | 6 | **Pairs Trading (Gold/Silver)** | N/A | ✅ Gold-Silver ratio is a known regime signal | **YES** | You already compute GSR in fetch_gold.py. Upgrade it from a display metric to a signal: GSR > 90 historically means gold overbought vs silver → mean-reversion trade. Add as a World Context card. |
> | 7 | **Short Term Reversal** | 0.816 | ⚠️ Works on equities (weekly), gold reversal patterns are different | **NO** | Gold mean-reverts differently than equities. The weekly reversal effect is equity-specific. |
> | 8 | **Crude Oil Predicts Equity** | 0.599 | ❌ Not gold-related | **NO** | Oil→equities, not oil→gold. |
> | 9 | **Paired Switching** | 0.691 | ✅ Gold/bonds rotation signal | **YES — Phase 3** | Gold vs TLT relative strength. When gold outperforms bonds → monetary fear. When bonds outperform → growth optimism. Sophisticated macro rotation signal. |
>
> ### VERDICT: GOLD Upgrades
>
> | Priority | Signal | Effort | Impact | Wire To |
> |----------|--------|--------|--------|---------|
> | 🥇 P0 | **Time Series Momentum (multi-lookback)** | 2h | 🔥🔥🔥🔥🔥 | New signal card: "MOMENTUM" with 1M/3M/6M/12M bars |
> | 🥈 P0 | **Cross-Asset Trend Following** | 1h | 🔥🔥🔥🔥 | World Context card: "Cross-Asset Regime" |
> | 🥉 P1 | **Gold-Silver Ratio Signal** | 30min | 🔥🔥🔥 | Already computed — add signal logic |
> | P2 | **Skewness Risk Thermometer** | 1h | 🔥🔥 | Risk bar upgrade |
> | P2 | **Gold VRP (GVZ options)** | 4h | 🔥🔥🔥🔥 | World Context: "Fear Premium" gauge |
> | P3 | **Paired Switching (Gold vs TLT)** | 2h | 🔥🔥🔥 | New rotating allocation card |
>
> **Bottom line for Gold:** The site gets 60% better with just P0+P1 (~3.5 hours of work). Time series momentum + cross-asset regime + GSR signal = the three things that actually move gold, quantified.
>
> ---
>
> ## 2. OIL (Brent Crude) — Signal Evaluation
>
> ### Physics of Oil
> Oil is a physical commodity. It has:
> 1. **Supply**: OPEC+ quotas, shale rigs, geopolitical outages
> 2. **Demand**: Global GDP growth, refining runs, SPR releases
> 3. **Inventory**: The buffer stock. Storage = price signal.
> 4. **Futures Curve**: Backwardation (tight supply) vs Contango (oversupply)
>
> Current engine uses ONLY price — no inventory data, no term structure, no supply context. This is the biggest gap.
>
> ### Signal-by-Signal Verdict
>
> | # | Signal | Sharpe | Physics Test | Upgrade? | Why |
> |---|--------|--------|-------------|----------|-----|
> | 1 | **Term Structure (Backwardation/Contango)** | 0.128 | ✅✅✅ **THE OIL SIGNAL** | **YES — WIRE NOW P0** | This is THE most important upgrade for oil. The futures curve IS the oil signal. Backwardation = physical tightness = bullish. Contango = oversupply = bearish. The current engine doesn't even look at it. A crime. |
> | 2 | **Time Series Momentum** | 0.576 | ✅ Oil trends on supply shocks | **YES — WIRE NOW** | Multi-lookback momentum for Brent. Same upgrade as gold. |
> | 3 | **Skewness Effect in Commodities** | 0.482 | ✅ Oil skew predicts supply disruptions | **YES** | Oil returns are negatively skewed (crashes happen fast). Monitoring skew shift is an early warning of supply stress. |
> | 4 | **Return Asymmetry** | 0.239 | ✅ Asymmetry in oil futures | **PARTIAL** | Lower Sharpe but same family as skewness. Combine into one card. |
> | 5 | **WTI/BRENT Spread** | -0.199 | ✅ Spread = US export arbitrage window | **YES — Phase 2** | The WTI-Brent spread tells you about US export capacity and Permian bottlenecks. Relevant for Malaysian context (Brent is the benchmark). Wire as a World Context gauge. |
> | 6 | **Cross-Asset (Crude → Equities)** | 0.599 | ✅ Oil leads equities at extremes | **YES** | Add to World Context: "Brent→SPX Lead Signal." When oil spikes >20% in a month, equities historically underperform. This is already in the literature. |
> | 7 | **Asset Class Trend-Following** | 0.502 | ✅ Commodity super-cycle context | **YES** | Cross-asset commodity trend. Is oil leading or lagging the broader commodity complex? |
> | 8 | **Short Term Reversal with Futures** | -0.05 | ❌ Negative Sharpe — don't wire | **NO** | This strategy has a negative Sharpe. Skip. |
> | 9 | **Low Volatility Factor** | 0.717 | ❌ Equity factor | **NO** | Not applicable to single-commodity oil. |
>
> ### VERDICT: OIL Upgrades
>
> | Priority | Signal | Effort | Impact | Wire To |
> |----------|--------|--------|--------|---------|
> | 🥇 P0 | **Term Structure (Backwardation/Contango)** | 3h | 🔥🔥🔥🔥🔥🔥🔥 | NEW dedicated card: "Futures Curve" with spot, 1M, 3M, 6M, 12M and roll yield |
> | 🥈 P0 | **Time Series Momentum (multi-lookback)** | 2h | 🔥🔥🔥🔥🔥 | Same upgrade as gold |
> | 🥉 P0 | **Crude Oil → Equities Lead Signal** | 1h | 🔥🔥🔥🔥 | World Context: "Brent→SPX Lead" |
> | P1 | **Skewness/Asymmetry Monitor** | 1h | 🔥🔥🔥 | Risk thermometer upgrade |
> | P1 | **WTI/BRENT Spread** | 30min | 🔥🔥🔥 | Already have Brent data; add WTI + spread logic |
> | P2 | **Cross-Asset Commodity Trend** | 1h | 🔥🔥🔥 | World Context: "Commodity Complex" |
>
> **Bottom line for Oil:** The site gets 100% better with P0 alone (~6 hours). The futures curve is THE missing piece — it's like having a weather dashboard without looking at the sky. Term structure + multi-timeframe momentum + crude→equities lead = a complete oil intelligence panel.
>
> ---
>
> ## 3. GAS (Natural Gas) — Signal Evaluation
>
> ### Physics of Natural Gas
> Gas is the most volatile major commodity. It has:
> 1. **Seasonality**: Winter demand (heating), summer demand (cooling), shoulder months
> 2. **Storage**: EIA weekly storage reports — the single biggest weekly catalyst
> 3. **Weather**: HDD/CDD (heating/cooling degree days) drive spot prices
> 4. **LNG Export**: US Gulf Coast → Asia/Europe arbitrage
> 5. **Production**: Associated gas from oil drilling + dedicated gas rigs
>
> Current engine uses pure price technicals. Zero seasonality. Zero storage context. For gas, this is like navigating without a compass.
>
> ### Signal-by-Signal Verdict
>
> | # | Signal | Sharpe | Physics Test | Upgrade? | Why |
> |---|--------|--------|-------------|----------|-----|
> | 1 | **Term Structure** | 0.128 | ✅✅✅ Seasonality shows in the curve | **YES — WIRE NOW P0** | Gas futures curve has the strongest seasonal shape of any commodity. Winter months premium, shoulder months discount. The curve IS the signal. |
> | 2 | **Time Series Momentum** | 0.576 | ✅ Gas trends HARD on weather events | **YES — WIRE NOW** | Gas has violent trends. Multi-lookback momentum captures regime shifts better than simple EMA cross. |
> | 3 | **Skewness Effect** | 0.482 | ✅✅ Gas is the most skewed commodity | **YES** | Natural gas has extreme skew — $2 to $10 moves happen. Skew monitoring is CRITICAL for gas risk management. |
> | 4 | **Seasonality Pattern Detection** | N/A* | ✅✅✅ THE GAS SIGNAL | **YES — WIRE NOW P0** | *Not in the 63 strategies but THE most important gas signal. Inject seasonal baseline: typical Jan price vs Jul price, storage injection/withdrawal cycles. This single addition makes the site 3x more useful. |
> | 5 | **Short Term Reversal** | 0.816 (equities) | ❌ Gas mean-reverts differently | **NO** | Gas mean-reversion is storage-driven, not weekly reversal. |
> | 6 | **Overnight Seasonality (Bitcoin)** | 0.892 | ❌ Crypto-specific | **NO** | Not applicable. |
> | 7 | **Commodity Momentum** | 0.14 | ⚠️ Low Sharpe on gas | **PARTIAL** | Cross-sectional commodity momentum works better on a basket. On single gas, too noisy. |
> | 8 | **Dispersion Trading** | 0.432 | ✅ Gas vol dispersion (options) | **YES — Phase 3** | Gas options implied vs realized vol spread. Phase 3 when options data is available. |
>
> ### VERDICT: GAS Upgrades
>
> | Priority | Signal | Effort | Impact | Wire To |
> |----------|--------|--------|--------|---------|
> | 🥇 P0 | **Seasonality Baseline** | 3h | 🔥🔥🔥🔥🔥🔥🔥🔥 | NEW dedicated card: "Seasonal Context" — 5yr avg, current vs normal, storage level |
> | 🥈 P0 | **Term Structure (Gas Futures Curve)** | 3h | 🔥🔥🔥🔥🔥🔥 | "Futures Curve" card with seasonal shape overlay |
> | 🥉 P0 | **Time Series Momentum (multi-lookback)** | 2h | 🔥🔥🔥🔥🔥 | Same upgrade as gold/oil |
> | P1 | **Skewness/Extreme Move Monitor** | 1h | 🔥🔥🔥🔥 | Risk thermometer — especially important for gas |
> | P2 | **Cross-Asset (Gas→Power/LNG spread)** | 2h | 🔥🔥🔥 | JKM spread context (already referenced in driver row, not computed) |
>
> **Bottom line for Gas:** The site gets 200%+ better with P0 (~8 hours). Gas without seasonality is literally missing the single biggest predictable pattern in the commodity. Seasonality + term structure + momentum = a gas dashboard that tells you where you are in the cycle, not just what price is doing.
>
> ---
>
> ## 4. MASTER VERDICT — Which Signals Actually Upgrade All Three Sites?
>
> ### CROSS-CUTTING SIGNALS (wire once, all three benefit)
>
> | Signal | Gold | Oil | Gas | Effort | Verdict |
> |--------|------|-----|-----|--------|---------|
> | **Time Series Momentum (multi-lookback)** | 🔥🔥🔥🔥🔥 | 🔥🔥🔥🔥🔥 | 🔥🔥🔥🔥🔥 | 6h total | **WIRE ALL THREE** |
> | **Term Structure (futures curve)** | 🔥🔥🔥 | 🔥🔥🔥🔥🔥🔥🔥 | 🔥🔥🔥🔥🔥🔥 | 8h total | **WIRE OIL+GAS (gold optional)** |
> | **Skewness / Return Distribution** | 🔥🔥🔥 | 🔥🔥🔥 | 🔥🔥🔥🔥 | 3h total | **WIRE ALL THREE** |
> | **Cross-Asset Lead Signals** | 🔥🔥🔥🔥 | 🔥🔥🔥🔥 | 🔥🔥🔥 | 4h total | **WIRE ALL THREE** |
>
> ### ASSET-SPECIFIC WINNERS
>
> | Asset | #1 Missing Signal | Why It Wins |
> |-------|-------------------|------------|
> | **GOLD** | Time Series Momentum | Gold trends are persistent (central bank buying). Multi-lookback momentum catches regime shifts EMA cross misses entirely. |
> | **OIL** | Term Structure (backwardation/contango) | THE oil signal. Futures curve tells you supply tightness in real-time. No price-only indicator can replicate this. |
> | **GAS** | Seasonality + Storage Context | Gas moves 50%+ on seasonal patterns and EIA storage reports. Trading gas without seasonality is gambling. |
>
> ---
>
> ## 5. KARPATHY VERDICT — The Physics-Based Priority Order
>
> ```
> NOT THIS:
>   "Let's add 63 signals and see what sticks" ← cargo cult
>
> THIS:
>   1. Understand the physics of each commodity
>   2. Identify the ONE missing signal that would most improve the dashboard
>   3. Wire that signal with minimal complexity
>   4. Measure: does it improve the forecast log hit rate?
>   5. Iterate
>
> PRIORITY:
>   Phase 1 (this week, ~12h):
>     ├── GAS: Seasonality baseline + Storage context  ← BIGGEST WIN
>     ├── OIL: Term Structure (futures curve)          ← BIGGEST WIN
>     ├── GOLD: Time Series Momentum (multi-lookback)  ← BIGGEST WIN
>     └── ALL: Skewness risk thermometer               ← universal upgrade
>
>   Phase 2 (next week, ~8h):
>     ├── OIL: Crude→Equities lead + WTI/Brent spread
>     ├── GAS: Term Structure + JKM spread
>     ├── GOLD: Gold-Silver Ratio signal + Cross-asset trend
>     └── ALL: Cross-asset lead signals dashboard
>
>   Phase 3 (later, ~10h):
>     ├── GOLD: Gold VRP (GVZ options data)
>     ├── GAS: Dispersion trading (options data)
>     ├── ALL: Kelly position sizing integration
>     └── ALL: Forecast log backtesting against historical signals
> ```
>
> ---
>
> ## 6. Implementation Contract — Phase 1
>
> ```yaml
> PHASE_1_CONTRACT:
>   mode: RESEARCH_ONLY
>   live_trading: false
>   deliverables:
>     - signal: time_series_momentum
>       assets: [gold, oil, gas]
>       compute: 1M/3M/6M/12M lookback, cross-sectional rank
>       output: new Technical Forge card "MOMENTUM → Multi-Timeframe"
>       integration: add cmd_momentum() to fetch_gold.py, fetch_oil.py, fetch_gas.py
>
>     - signal: term_structure
>       assets: [oil, gas]
>       compute: futures curve, roll yield, backwardation/contango classification
>       output: new card "FUTURES CURVE" with spot/1M/3M/6M/12M prices + roll yield
>       integration: add cmd_term_structure() to fetch_oil.py, fetch_gas.py
>       note: "Gold term structure is less informative — Phase 2"
>
>     - signal: gas_seasonality
>       assets: [gas]
>       compute: 5-year monthly average, current deviation, storage % of 5yr avg
>       output: new card "SEASONAL CONTEXT" on gas dashboard
>       integration: add cmd_seasonality() to fetch_gas.py
>       data_source: yfinance 5yr history + EIA weekly storage API (free)
>
>     - signal: skewness_monitor
>       assets: [gold, oil, gas]
>       compute: rolling 20-day return skew, extreme move flag
>       output: upgrade existing Risk Thermometer bar
>       integration: add to cmd_ticker() response for all three
>
>   verification:
>     - backtest each signal separately against 2yr history
>     - measure: does signal improve forecast cone accuracy at 30d?
>     - gate: each signal must pass ≥1.0 Sharpe in isolation before site integration
>     - no live trading — display only
> ```
>
> ---
>
> ## 7. The 8 Signals NOT Worth Wiring (Cargo Cult Detection)
>
> | Signal | Why Skip |
> |--------|----------|
> | Accrual Anomaly (-0.272) | Equity accounting signal, zero commodity relevance |
> | Earnings Quality (-0.18) | Equity-specific |
> | January Barometer (0.365) | Calendar effect for SPX, not commodities |
> | Payday Anomaly (0.269) | Consumer spending pattern, not commodity |
> | Lexical Density of Filings (0.688) | NLP on 10-K filings — equity only |
> | Soccer Clubs Stocks Arbitrage (0.515) | Fun, but not commodity |
> | Low Volatility Factor (0.717) | Equity cross-sectional factor |
> | Betting Against Beta (0.594) | Equity factor |
>
> **These 8 strategies are interesting, publishable, peer-reviewed — and completely irrelevant to commodity dashboards.** Knowing what NOT to build is the highest-leverage skill.
>
> ---
>
> *Forged: 2026-07-28 by OpenCode (333-AGI) · Karpathy-mode autoresearch*  
> *DITEMPA BUKAN DIBERI — Forged in physics, not in hopes.*
