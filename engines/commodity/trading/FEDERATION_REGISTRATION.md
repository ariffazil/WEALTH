# Trading Intelligence — Federation Organ Registration

> REGISTERED: 2026-07-16 by HERMES-PRIME (AAA-Core)
> PENDING: arifOS kernel registration + F13 sovereign ack
> STATUS: FORGING — awaiting MCP server deployment

## Organ Identity

| Field | Value |
|---|---|
| **Organ** | TRADING |
| **Port** | 8092 |
| **Stack** | Python 3.12 / FastMCP |
| **Role** | Trading intelligence — signals, regime, APEX, risk sizing |
| **Can mutate?** | No — evidence/compute only |
| **Systemd** | trading-mcp |
| **Source** | /root/trading/ |

## MCP Tools (4)

| Tool | Description | Inputs | Outputs |
|---|---|---|---|
| `trade_signal` | Full XAUUSD signal with regime + confluence + zones | (none — fetches live data) | direction, entry, SL, TP1, TP2, RR, confidence, regime, confluence_factors |
| `trade_risk` | Position sizing (Kelly + risk-based) | equity, entry, SL | lot_size, risk_amount, kelly_fraction |
| `apex_evaluate` | APEX market evaluation | (none — fetches live data) | G, C_dark, dS, state, direction, APEX primitives, volume, momentum |
| `trade_scan` | Quick market scan | (none) | price, regime, zones, RSI, EMA state, bias |

## Federation Integration

```
GEOX → arifOS → TRADING → WEALTH → A-FORGE → WELL → AAA → VAULT999
```

- TRADING computes signals (evidence only)
- arifOS judges (constitutional gate)
- WEALTH sizes positions (capital math)
- A-FORGE executes (if lease granted)
- WELL checks human readiness
- AAA displays
- VAULT999 seals

## Dependencies

- yfinance (GC=F data feed)
- /root/trading/ package (signals, risk, governance, core)
- FastMCP (mcp.server.fastmcp)

## Cron Integration

| Job | Schedule | Uses TRADING |
|---|---|---|
| Gold Signal Briefing | 8am MYT Mon-Fri | trade_signal + chart |
| XAUUSD Daily | 9am MYT Mon-Fri | apex_evaluate + trade_signal |
| Position Monitor | */15 15-05 MYT Mon-Fri | trade_scan (regime change alert) |
| Price Alert | hourly 8-20 MYT Mon-Fri | trade_scan |
| Weekly Report | Fri 8pm MYT | apex_evaluate + trade_signal + trade_risk |

## Sovereign Acknowledgment

⚠️ New tools on arifOS require F13 ratification.
This registration is FORGED but not SEALED until Arif signs.
