# Deployment — WEALTH (Capital Management)

## Prerequisites

- Docker 24+ and Docker Compose v2
- 2 CPU cores, 4GB RAM
- Ports: `18082` (WEALTH organ)

## Quick Start

```bash
git clone https://github.com/arif-fazil/WEALTH.git
cd WEALTH
docker compose up -d

# Verify
curl http://localhost:18082/health
```

## Docker Compose

```yaml
services:
  wealth:
    image: arifazil/wealth:latest
    ports:
      - "18082:18082"
    volumes:
      - wealth-ledger:/var/lib/wealth
    environment:
      - WEALTH_DATA_PATH=/var/lib/wealth
    restart: unless-stopped

volumes:
  wealth-ledger:
```

## Capabilities

- Capital health diagnostics
- Market analysis and indicators
- Entropy modeling
- Entry planning
- Portfolio health monitoring
- XAUUSD trading stack
