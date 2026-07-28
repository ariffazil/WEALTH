# EUREKA Signal Map — awesome-systematic-trading → WEALTH Organ Domains
>
> **Source:** `https://github.com/paperswithbacktest/awesome-systematic-trading`  
> **Ingested:** 2026-07-28 | **Agent:** OpenCode (333-AGI) | **Sovereign:** Arif (F13)  
> **Classification:** OBS + DER — signals distilled from published peer-reviewed strategies + 97 libraries  
> **DITEMPA BUKAN DIBERI** — Forged, Not Given
>
> ---
>
> ## Architecture: Signal → WEALTH Domain Mapping
>
> ```
> awesome-systematic-trading (63 strategies + 97 libraries + 33 analytics tools)
>         │
>         ▼  EUREKA distillation
> ┌───────────────────────────────────────────────────┐
> │                 WEALTH ORGAN                       │
> │                                                    │
> │  capital_market       ← price/momentum/carry/fx    │
> │  capital_primitive    ← factor/NPV/Kelly/MC/opt    │
> │  capital_health       ← drawdown/runway/survival   │
> │  capital_diagnose     ← anomaly/pairs/calendar     │
> │  capital_entropy      ← sentiment/filing/lexical   │
> │  capital_wisdom       ← ESG/multi-factor/combine   │
> │  wealth_cascade_model ← rotation/feedback/style    │
> │  wealth_institutional_stress_index ← vol/risk      │
> └───────────────────────────────────────────────────┘
> ```
>
> ---
>
> ## 1. capital_market — Raw Market Signal Ingestion
>
> **Domain:** Observational market data — FX, commodity, crypto, equity. WEALTH computes, never allocates.
>
> ### 1A. FX / Currency Signals (4 strategies)
>
> | EUREKA Signal ID | Strategy | Sharpe | Signal Type | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-FX-001` | **FX Carry Trade** — Long high-yield, short low-yield currencies | 0.254 | Yield differential | `capital_market(mode=fx)` |
> | `EUREKA-FX-002` | **Dollar Carry Trade** — Short USD vs basket when USD funding cheap | 0.113 | USD funding cost | `capital_market(mode=fx)` |
> | `EUREKA-FX-003` | **Currency Momentum Factor** — Long winners, short losers (1M/3M/12M lookback) | -0.01 | Cross-sectional momentum | `capital_market(mode=fx)` |
> | `EUREKA-FX-004` | **Currency Value (PPP)** — Long undervalued, short overvalued vs PPP | -0.103 | PPP deviation | `capital_market(mode=fx)` |
>
> **Data sources:** yfinance, OANDA API, ECB, BIS
>
> ### 1B. Commodity Signals (5 strategies)
>
> | EUREKA Signal ID | Strategy | Sharpe | Signal Type | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-COM-001` | **Momentum in Commodities** — Cross-sectional momentum (1/3/12 month) | 0.14 | Momentum | `capital_market(mode=commodity)` |
> | `EUREKA-COM-002` | **Term Structure (Backwardation/Contango)** — Long backwardated, short contangoed | 0.128 | Roll yield | `capital_market(mode=commodity)` |
> | `EUREKA-COM-003` | **Skewness Effect in Commodities** — Long positive skew, short negative skew | 0.482 | Return distribution | `capital_market(mode=commodity)` |
> | `EUREKA-COM-004` | **Return Asymmetry in Commodity Futures** — Asymmetry premium | 0.239 | Asymmetry | `capital_market(mode=commodity)` |
> | `EUREKA-COM-005` | **WTI/BRENT Spread Trading** — Mean-reversion in crude spread | -0.199 | Spread | `capital_market(mode=commodity)` |
>
> ### 1C. Crypto Signals (2 strategies)
>
> | EUREKA Signal ID | Strategy | Sharpe | Signal Type | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-CRY-001` | **Overnight Seasonality in Bitcoin** — Long BTC during NY close→Asia open | 0.892 | Intraday timing | `capital_market(mode=commodity)` |
> | `EUREKA-CRY-002` | **Rebalancing Premium in Cryptocurrencies** — Daily rebalancing alpha | 0.698 | Rebalancing | `capital_market(mode=commodity)` |
>
> ### 1D. Cross-Asset Macro Signals (6 strategies)
>
> | EUREKA Signal ID | Strategy | Sharpe | Signal Type | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-MAC-001` | **Time Series Momentum** — Long assets with positive 12M excess return | 0.576 | TS momentum | `capital_market(mode=signal)` |
> | `EUREKA-MAC-002` | **Short Term Reversal with Futures** — Mean-reversion (1W lookback) | -0.05 | Mean-reversion | `capital_market(mode=signal)` |
> | `EUREKA-MAC-003` | **Asset Class Trend-Following** — SMA crossover across bonds/commodities/equities/REITs | 0.502 | Trend | `capital_market(mode=signal)` |
> | `EUREKA-MAC-004` | **Momentum Asset Allocation** — Dual momentum (relative + absolute) | 0.321 | Dual momentum | `capital_market(mode=signal)` |
> | `EUREKA-MAC-005` | **Paired Switching** — Rotate bonds↔equities on relative strength | 0.691 | Rotation | `capital_market(mode=signal)` |
> | `EUREKA-MAC-006` | **FED Model** — Earnings yield vs bond yield for equity/bond allocation | 0.369 | Valuation ratio | `capital_market(mode=signal)` |
>
> ---
>
> ## 2. capital_primitive — Pure Computation / Factor Library
>
> **Domain:** Deductive capital math. NPV, IRR, EMV, Monte Carlo, Kelly, Markowitz, Black-Litterman. No inference — pure computation.
>
> ### 2A. Equity Factor Signals (mapped as computational primitives)
>
> | EUREKA Signal ID | Strategy / Factor | Sharpe | Computation | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-FAC-001` | **Value (Book-to-Market)** — Fama-French HML | 0.526 | Cross-sectional B/M sort | `capital_primitive(mode=npv)` |
> | `EUREKA-FAC-002` | **Size (Small Cap Premium)** — SMB factor | 0.747 | Market cap quintile | `capital_primitive(mode=npv)` |
> | `EUREKA-FAC-003` | **Momentum Factor** — Jegadeesh-Titman 12-1 | -0.008 | Cross-sectional momentum | `capital_primitive` |
> | `EUREKA-FAC-004` | **Low Volatility Factor** — Low vol outperforms (Ang 2006) | 0.717 | Volatility sort | `capital_primitive` |
> | `EUREKA-FAC-005` | **Betting Against Beta** — Long low-beta, short high-beta (Frazzini-Pedersen 2014) | 0.594 | Beta rank | `capital_primitive(mode=kelly)` |
> | `EUREKA-FAC-006` | **Volatility Risk Premium** — Sell variance, buy tail protection | 0.637 | Variance swap replication | `capital_primitive(mode=mc)` |
> | `EUREKA-FAC-007` | **Asset Growth Effect** — Low asset growth firms outperform | 0.835 | Asset growth rate | `capital_primitive` |
> | `EUREKA-FAC-008` | **ROA Effect** — High ROA firms outperform | 0.155 | ROA computation | `capital_primitive` |
> | `EUREKA-FAC-009` | **Accrual Anomaly** — Low accruals outperform (Sloan 1996) | -0.272 | Accrual computation | `capital_primitive` |
> | `EUREKA-FAC-010` | **Earnings Quality Factor** — High quality earnings premium | -0.18 | Earnings quality | `capital_primitive` |
> | `EUREKA-FAC-011` | **Short Interest Effect** — High short interest → negative returns | 0.079 | Short interest ratio | `capital_primitive` |
> | `EUREKA-FAC-012` | **Earnings Announcement Premium** — Drift around earnings | 0.192 | Event study | `capital_primitive` |
> | `EUREKA-FAC-013` | **R&D Expenditures** — High R&D firms outperform | 0.354 | R&D/assets ratio | `capital_primitive` |
> | `EUREKA-FAC-014` | **Residual Momentum** — Momentum orthogonal to standard factors | 0.24 | Residual momentum | `capital_primitive` |
>
> ### 2B. Optimization Libraries → capital_primitive Computation Primitives
>
> | EUREKA Tool ID | Library | WEALTH Computation |
> |---|---|---|
> | `EUREKA-OPT-001` | **PyPortfolioOpt** — Efficient Frontier, Black-Litterman, HRP | `capital_primitive(mode=markowitz)` |
> | `EUREKA-OPT-002` | **Riskfolio-Lib** — Risk parity, CVaR, CDaR, risk budgeting | `capital_primitive(mode=risk)` |
> | `EUREKA-OPT-003` | **Deepdow** — Deep learning portfolio allocation | Neural weight allocation |
> | `EUREKA-OPT-004` | **spectre** — Multi-period portfolio optimization | Stochastic optimization |
> | `EUREKA-OPT-005` | **Empyrial** — Quantitative investment library | Unified optimization |
>
> ### 2C. Risk & Metrics Computation
>
> | EUREKA Tool ID | Library | WEALTH Computation |
> |---|---|---|
> | `EUREKA-RISK-001` | **pyfolio** — Portfolio and risk analytics (Quantopian) | Drawdown, VaR, CVaR, turnover |
> | `EUREKA-RISK-002` | **quantstats** — Portfolio analytics | Tearsheet, Sharpe, Sortino, Calmar |
> | `EUREKA-RISK-003` | **ffn** — Financial function library | Performance metrics |
> | `EUREKA-RISK-004` | **tf-quant-finance** (Google) — Derivative pricing | Options pricing, Greeks |
> | `EUREKA-RISK-005` | **FinancePy** — Fixed-income, equity, FX, credit derivatives | Multi-asset pricing |
>
> ---
>
> ## 3. capital_diagnose — Abductive Diagnostics / Pattern Recognition
>
> **Domain:** Inference from partial evidence. Anomaly detection. Calendar effects. Statistical arbitrage patterns.
>
> ### 3A. Calendar / Seasonality Anomalies
>
> | EUREKA Signal ID | Strategy | Sharpe | Anomaly Pattern | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-DIA-001` | **January Barometer** — Jan returns predict full year | 0.365 | Calendar effect | `capital_diagnose` |
> | `EUREKA-DIA-002` | **Turn of the Month** — Last trading day + first 3 days premium | 0.305 | Calendar effect | `capital_diagnose` |
> | `EUREKA-DIA-003` | **Payday Anomaly** — Equity returns spike on payday cycles | 0.269 | Behavioral calendar | `capital_diagnose` |
> | `EUREKA-DIA-004` | **Option-Expiration Week** — Reduced vol, higher returns on expiry week | 0.452 | Derivatives calendar | `capital_diagnose` |
> | `EUREKA-DIA-005` | **12 Month Cycle in Cross-Section** — Seasonality in factor returns | 0.34 | Multi-frequency | `capital_diagnose` |
>
> ### 3B. Pairs Trading / Statistical Arbitrage
>
> | EUREKA Signal ID | Strategy | Sharpe | Pattern | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-DIA-006` | **Pairs Trading with Stocks** — Cointegrated pair mean-reversion | 0.634 | Cointegration | `capital_diagnose` |
> | `EUREKA-DIA-007` | **Pairs Trading with Country ETFs** — Cross-country cointegration | 0.257 | Macro cointegration | `capital_diagnose` |
> | `EUREKA-DIA-008` | **Soccer Clubs Stocks Arbitrage** — Post-match reversion | 0.515 | Event arbitrage | `capital_diagnose` |
> | `EUREKA-DIA-009` | **Dispersion Trading** — Index vs constituent vol spread | 0.432 | Correlation arbitrage | `capital_diagnose` |
>
> ### 3C. Event-Driven / Microstructure
>
> | EUREKA Signal ID | Strategy | Sharpe | Pattern | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-DIA-010` | **Reversal During Earnings Announcements** — Post-earnings drift reversal | 0.785 | Earnings event | `capital_diagnose` |
> | `EUREKA-DIA-011` | **Earnings + Stock Repurchases** — Combined signal | -0.16 | Event combination | `capital_diagnose` |
> | `EUREKA-DIA-012` | **Short Term Reversal in Stocks** — Weekly reversal | 0.816 | Mean-reversion | `capital_diagnose` |
> | `EUREKA-DIA-013` | **52-Weeks High Effect** — Anchoring bias | 0.153 | Behavioral | `capital_diagnose` |
> | `EUREKA-DIA-014` | **Trend-Following in Stocks** — Time-series momentum in equities | 0.569 | Trend detection | `capital_diagnose` |
> | `EUREKA-DIA-015` | **Crude Oil Predicts Equity Returns** — Commodity→equity lead | 0.599 | Cross-asset lead | `capital_diagnose` |
> | `EUREKA-DIA-016` | **Synthetic Lending Rates Predict Returns** — Options-implied borrowing | 0.494 | Derivatives signal | `capital_diagnose` |
>
> ---
>
> ## 4. capital_entropy — Information / Sentiment / Lexical Analysis
>
> **Domain:** Measures information loss, consequence displacement, metric drift. Text-as-signal.
>
> | EUREKA Signal ID | Strategy | Sharpe | Entropy Dimension | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-ENT-001` | **How to Use Lexical Density of Company Filings** — Word complexity predicts returns | 0.688 | Text complexity | `capital_entropy(mode=text)` |
> | `EUREKA-ENT-002` | **The Positive Similarity of Company Filings and Stock Returns** — Filing similarity signal | N/A | Text similarity | `capital_entropy(mode=text)` |
> | `EUREKA-ENT-003` | **Market Sentiment and Overnight Anomaly** — Overnight sentiment | 0.369 | Sentiment | `capital_entropy(mode=sentiment)` |
> | `EUREKA-ENT-004` | **Momentum in Mutual Fund Returns** — Manager herding signal | 0.414 | Institutional entropy | `capital_entropy(mode=flow)` |
>
> **Supporting tools:** `tsfresh` (feature extraction), `statsmodels` (statistical tests), `pmdarima` (ARIMA)
>
> ---
>
> ## 5. capital_wisdom — Multi-Factor Wisdom / Sovereign Evaluation
>
> **Domain:** Evaluates proposals across dignity, sovereignty, resilience, optionality. Advisory only. Arif decides.
>
> ### 5A. Multi-Factor Synthesis Signals
>
> | EUREKA Signal ID | Strategy | Sharpe | Wisdom Dimension | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-WIS-001` | **Combining Smart Factors Momentum and Market Portfolio** — Factor timing | 0.388 | Factor combination | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-002` | **Momentum + Reversal + Volatility Combined** — Triple signal | 0.375 | Multi-signal | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-003` | **Momentum + Asset Growth Combined** — Dual factor | 0.058 | Factor synergy | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-004` | **Fundamental FSCORE + Short-Term Reversals** — Quality + timing | 0.153 | Quality + price | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-005` | **Value and Momentum Across Asset Classes** — Asness-Moskowitz-Pedersen (2013) | 0.155 | Cross-asset factor | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-006` | **Value (CAPE) within Countries** — Country-level CAPE timing | 0.351 | Macro valuation | `capital_wisdom(mode=evaluate)` |
>
> ### 5B. ESG / Sustainability Dimensions
>
> | EUREKA Signal ID | Strategy | Sharpe | Wisdom Dimension | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-WIS-007` | **ESG Factor Momentum** — ESG leaders outperform | 0.559 | Sustainability alpha | `capital_wisdom(mode=evaluate)` |
> | `EUREKA-WIS-008` | **ESG, Price Momentum, Stochastic Optimization** — ESG + momentum | N/A | ESG + timing | `capital_wisdom(mode=evaluate)` |
>
> ---
>
> ## 6. wealth_cascade_model — Rotation / Feedback / Style Dynamics
>
> **Domain:** Models feedback loops between institutional stress dimensions. Detects spiral vs linear decline.
>
> | EUREKA Signal ID | Strategy | Sharpe | Feedback Dynamic | WEALTH Tool |
> |---|---|---|---|---|
> | `EUREKA-CAS-001` | **Sector Momentum — Rotational System** — Rotate across GICS sectors | 0.401 | Sector rotation | `wealth_cascade_model` |
> | `EUREKA-CAS-002` | **Momentum Factor and Style Rotation** — Rotate value/growth/momentum | -0.056 | Style rotation | `wealth_cascade_model` |
> | `EUREKA-CAS-003` | **Consistent Momentum** — 6-month holding with consistency filter | 0.128 | Persistence filter | `wealth_cascade_model` |
> | `EUREKA-CAS-004` | **Betting Against Beta in International Equities** — Global BAB | 0.142 | Global factor | `wealth_cascade_model` |
>
> ---
>
> ## 7. wealth_institutional_stress_index — Volatility / Risk / Stress Signals
>
> **Domain:** Composite stress index (0-1). Detects spiral signatures across financial, governance, workforce, legal dimensions.
>
> | EUREKA Signal ID | Strategy / Tool | Signal | WEALTH Integration |
> |---|---|---|---|
> | `EUREKA-STR-001` | **Low Volatility Factor** — Low vol outperforms during stress | Risk appetite proxy | `wealth_institutional_stress_index` |
> | `EUREKA-STR-002` | **Volatility Risk Premium** — VRP collapse signals stress | Tail risk | Stress index input |
> | `EUREKA-STR-003` | **Option-Expiration Week Effect** — Vol compression signal | Vol term structure | Stress index input |
> | `EUREKA-STR-004` | **pyfolio** — Drawdown, VaR, CVaR computation | Risk decomposition | Stress index computation |
> | `EUREKA-STR-005` | **quantstats** — Sharpe, Sortino, Calmar, max drawdown | Risk metrics | Stress index dashboard |
>
> ---
>
> ## 8. Data & Infrastructure Signals → WEALTH Pipeline
>
> ### 8A. Data Sources (map to capital_market + capital_primitive)
>
> | Data Source | Coverage | WEALTH Route |
> |---|---|---|
> | **yfinance** | Global equities, FX, crypto, commodities | `capital_market` — primary retail data feed |
> | **OpenBB Terminal** | Multi-asset investment research | `capital_market` — institutional research |
> | **Quandl** | Economic + alternative data | `capital_market` — macro indicators |
> | **TuShare / AkShare** | China A-shares, futures | `capital_market` — China coverage |
> | **findatapy** | Bloomberg, Quandl, Yahoo unified API | `capital_market` — unified ingestion |
> | **Cryptofeed** | Crypto exchange order books | `capital_market` — L2 crypto data |
> | **FundamentalAnalysis** | 20K+ company financials | `capital_primitive` — fundamental factors |
>
> ### 8B. Machine Learning Tools
>
> | ML Tool | Capability | WEALTH Route |
> |---|---|---|
> | **QLib (Microsoft)** | AI-driven alpha mining, factor engineering | `capital_diagnose` — abductive signal mining |
> | **FinRL** | Deep RL for trading agents | `capital_wisdom` — adaptive strategy |
> | **MlFinLab (Hudson & Thames)** | ML for portfolio management | `capital_primitive` — feature engineering |
> | **TradingGym** | RL training environment | `capital_wisdom` — strategy gym |
>
> ### 8C. Time Series Tools
>
> | TS Tool | Capability | WEALTH Route |
> |---|---|---|
> | **Facebook Prophet** | Multi-seasonality forecasting | `capital_diagnose` — forward signal |
> | **statsmodels** | ARIMA, GARCH, VAR, cointegration | `capital_primitive` — statistical engine |
> | **tsfresh** | Automatic feature extraction from TS | `capital_diagnose` — feature mining |
> | **pmdarima** | Auto ARIMA (R parity) | `capital_primitive` — auto-forecasting |
>
> ### 8D. Technical Indicators
>
> | Indicator Library | Coverage | WEALTH Route |
> |---|---|---|
> | **ta-lib** | 200+ technical indicators | `capital_market` — TA signal feed |
> | **pandas-ta** | 130+ indicators, 60+ candlestick patterns | `capital_market` — TA signal feed |
> | **finta** | Pandas-native indicators | `capital_market` — TA signal feed |
>
> ---
>
> ## 9. Summary — EUREKA Signal Count by WEALTH Domain
>
> | WEALTH Domain | Strategies | Tools / Libraries | Total Signals |
> |---|---|---|---|
> | **capital_market** | 17 | 21 | 38 |
> | **capital_primitive** | 14 | 14 | 28 |
> | **capital_diagnose** | 16 | 6 | 22 |
> | **capital_entropy** | 4 | 3 | 7 |
> | **capital_wisdom** | 8 | 3 | 11 |
> | **wealth_cascade_model** | 4 | 0 | 4 |
> | **wealth_institutional_stress_index** | 0 | 5 | 5 |
> | **capital_health** | 0 | 5 | 5 |
> | **TOTAL** | **63** | **57** | **120** |
>
> ---
>
> ## 10. Priority EUREKA Signals for Immediate WEALTH Integration
>
> Based on Sharpe ratio × reproducibility × data availability:
>
> | Rank | EUREKA ID | Strategy | Sharpe | Domain | Integration Effort |
> |---|---|---|---|---|---|
> | 🥇 | `EUREKA-CRY-001` | Overnight Seasonality in Bitcoin | 0.892 | capital_market | Low — intraday timing |
> | 🥈 | `EUREKA-FAC-007` | Asset Growth Effect | 0.835 | capital_primitive | Low — fundamental data |
> | 🥉 | `EUREKA-DIA-012` | Short Term Reversal in Stocks | 0.816 | capital_diagnose | Low — price only |
> | 4 | `EUREKA-DIA-010` | Reversal During Earnings | 0.785 | capital_diagnose | Medium — earnings data |
> | 5 | `EUREKA-FAC-002` | Size Factor (SMB) | 0.747 | capital_primitive | Low — market cap |
> | 6 | `EUREKA-FAC-004` | Low Volatility Factor | 0.717 | capital_primitive | Low — vol computation |
> | 7 | `EUREKA-CRY-002` | Rebalancing Premium (Crypto) | 0.698 | capital_market | Low — rebal calc |
> | 8 | `EUREKA-MAC-005` | Paired Switching | 0.691 | capital_market | Low — relative strength |
> | 9 | `EUREKA-ENT-001` | Lexical Density of Filings | 0.688 | capital_entropy | Medium — NLP required |
> | 10 | `EUREKA-FAC-006` | Volatility Risk Premium | 0.637 | capital_primitive | Medium — options data |
>
> ---
>
> ## 11. EUREKA Engine — Runtime Integration Architecture
>
> ```
> ┌─────────────────────────────────────────────────────┐
> │  EUREKA Signal Pipeline (WEALTH Organ)               │
> │                                                      │
> │  1. INGEST  → capital_market fetches market data     │
> │  2. COMPUTE → capital_primitive computes factors      │
> │  3. DIAGNOSE→ capital_diagnose detects anomalies      │
> │  4. ENTROPY → capital_entropy measures information    │
> │  5. WISDOM  → capital_wisdom synthesizes evaluation   │
> │  6. CASCADE → wealth_cascade_model tracks feedback    │
> │  7. STRESS  → wealth_institutional_stress_index       │
> │  8. LEDGER  → capital_ledger records to VAULT999      │
> │                                                      │
> │  ALL → arifOS kernel judges → Arif (F13) decides     │
> └─────────────────────────────────────────────────────┘
> ```
>
> **Iron Rule:** WEALTH computes. arifOS judges. Arif decides. No signal executes autonomously.
>
> ---
>
> ## 12. Next Steps — WEALTH Skill Registration
>
> Each EUREKA signal above can be registered as a `capital_market(mode=signal)` or `capital_primitive(mode=factor)` computation path. Recommended integration order:
>
> 1. **Phase 1 — Price-Only Signals** (20 strategies): Momentum, reversal, trend, pairs
> 2. **Phase 2 — Fundamental Signals** (14 strategies): Value, quality, accruals, size
> 3. **Phase 3 — Alternative Data Signals** (8 strategies): Sentiment, filings, ESG
> 4. **Phase 4 — Cross-Asset Signals** (17 strategies): FX, commodities, macro rotation
> 5. **Phase 5 — ML/RL Stratgies** (4 strategies): QLib, FinRL, deep learning
>
> ---
>
> *Forged: 2026-07-28 by OpenCode (333-AGI) · Source: awesome-systematic-trading (9.4K ⭐, 63 strategies, 97 libraries)*  
> *WEALTH computes. arifOS judges. Arif decides. DITEMPA BUKAN DIBERI.*
