#!/usr/bin/env bash
# Sync commodity engines from WEALTH git source to live runtime locations.
# Run after pulling updated engine source from git.
# DITEMPA BUKAN DIBERI

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[sync] Syncing commodity engines to live locations..."

# Gold engine → :3456
echo "[sync] Gold engine → /var/www/html/gold/api/"
cp "$REPO_ROOT/commodity/gold-api/server.js" /var/www/html/gold/api/
cp "$REPO_ROOT/commodity/gold-api/fetch_gold.py" /var/www/html/gold/api/
cp "$REPO_ROOT/commodity/gold-api/signal_v2.json" /var/www/html/gold/api/ 2>/dev/null || true

# Oil engine → :3457
echo "[sync] Oil engine → /var/www/html/oil/api/"
cp "$REPO_ROOT/commodity/oil-api/server.js" /var/www/html/oil/api/
cp "$REPO_ROOT/commodity/oil-api/fetch_oil.py" /var/www/html/oil/api/

# Gas engine → :3458
echo "[sync] Gas engine → /var/www/html/gas/api/"
cp "$REPO_ROOT/commodity/gas-api/server.js" /var/www/html/gas/api/
cp "$REPO_ROOT/commodity/gas-api/fetch_gas.py" /var/www/html/gas/api/

# Restart engine processes
echo "[sync] Restarting engine processes..."
for port in 3456 3457 3458; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
        echo "[sync] Killed process on port $port (PID $pid)"
    fi
done

# Wait for ports to free
sleep 1

# Start engines (they run as Node.js servers)
for dir in gold oil gas; do
    cd "/var/www/html/$dir/api"
    nohup node server.js > "/var/log/$dir-engine.log" 2>&1 &
    echo "[sync] Started $dir engine (PID $!)"
done

echo "[sync] All engines synced and restarted."
