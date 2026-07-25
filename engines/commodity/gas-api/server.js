/**
 * Natural Gas Data API Server — WEALTH Organ
 * Node.js HTTP server proxying to Python data fetcher. 5-min cache.
 * DITEMPA BUKAN DIBERI — Forged, Not Given.
 */

const http = require('http');
const { execFile } = require('child_process');
const crypto = require('crypto');
const path = require('path');
const url = require('url');

const PORT = 3458;
const PYTHON = '/root/venv/bin/python3';
const SCRIPT = path.join(__dirname, 'fetch_gas.py');
const CACHE_TTL = 300_000;

const cache = new Map();

function getCache(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > CACHE_TTL) { cache.delete(key); return null; }
  return entry.data;
}

function setCache(key, data) {
  cache.set(key, { data, ts: Date.now() });
  if (cache.size > 100) {
    const now = Date.now();
    for (const [k, v] of cache) { if (now - v.ts > CACHE_TTL * 2) cache.delete(k); }
  }
}

function runPython(command, args = []) {
  return new Promise((resolve, reject) => {
    execFile(PYTHON, [SCRIPT, command, ...args], {
      timeout: 30_000, maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    }, (err, stdout, stderr) => {
      if (err) {
        const msg = stderr || stdout || err.message;
        console.error(`[gas-api] Python error (${command}):`, msg.trim());
        reject(new Error(msg.trim()));
        return;
      }
      try { resolve(JSON.parse(stdout)); }
      catch (e) { reject(new Error(`Invalid JSON: ${e.message}`)); }
    });
  });
}

const handlers = {
  '/api/gas/apex': async () => {
    const c = getCache('apex'); if (c) return c;
    const d = await runPython('apex'); setCache('apex', d); return d;
  },
  '/api/gas/signal_v2': async () => {
    const c = getCache('signal_v2'); if (c) return c;
    const d = await runPython('signal_v2'); setCache('signal_v2', d); return d;
  },
  '/api/gas/calendar': async () => {
    const c = getCache('calendar'); if (c) return c;
    const d = await runPython('calendar'); setCache('calendar', d); return d;
  },
  '/api/gas/snapshot': async () => {
    const c = getCache('snapshot'); if (c) return c;
    const [ticker, levels, macro] = await Promise.all([
      runPython('ticker').catch(() => null),
      runPython('levels').catch(() => null),
      runPython('macro').catch(() => null),
    ]);
    if (!ticker || ticker.error) throw new Error('snapshot: ticker unavailable');
    const observed_at = new Date().toISOString();
    const unsigned = {
      schema: 'wealth.snapshot.v1',
      asset: 'gas',
      observed_at,
      source: 'yfinance + technical analysis (WEALTH commodity engine)',
      ticker: {
        symbol: ticker.symbol, price: ticker.price, change: ticker.change,
        changePct: ticker.changePct, rsi: ticker.rsi, rsiState: ticker.rsiState,
        signal: ticker.signal, confidence: ticker.confidence,
        ema20: ticker.ema20, ema50: ticker.ema50, ema200: ticker.ema200,
        emaTrend: ticker.emaTrend, pivot: ticker.pivot,
        stale: ticker.stale || false, stale_age_s: ticker.stale_age_s || 0,
      },
      levels: levels && !levels.error ? {
        support: levels.support_1h || [], resistance: levels.resistance_1h || [],
        support_daily: levels.support_daily || [], resistance_daily: levels.resistance_daily || [],
        pivot: levels.pivot,
      } : { support: ticker.support || [], resistance: ticker.resistance || [] },
      macro: macro && !macro.error ? {
        dxy: macro.dxy, us10y: macro.us10y, vix: macro.vix,
        silver: macro.silver, gsr: macro.gold_silver_ratio,
        usmyr: macro.usmyr,
      } : {},
    };
    // Deep-sort for deterministic hash matching Python json.dumps(sort_keys=True)
    const deepSort = (obj) => {
      if (Array.isArray(obj)) return obj.map(deepSort);
      if (obj !== null && typeof obj === 'object') {
        const s = {};
        Object.keys(obj).sort().forEach(k => { s[k] = deepSort(obj[k]); });
        return s;
      }
      return obj;
    };
    const canonical = JSON.stringify(deepSort(unsigned));
    unsigned.coherence_id = crypto.createHash('sha256').update(canonical).digest('hex');
    setCache('snapshot', unsigned); return unsigned;
  },
  // Short aliases
  '/api/apex': async () => handlers['/api/gas/apex'](),
  '/api/signal_v2': async () => handlers['/api/gas/signal_v2'](),
  '/api/calendar': async () => handlers['/api/gas/calendar'](),
  '/api/snapshot': async () => handlers['/api/gas/snapshot'](),
  '/api/macro': async () => handlers['/api/gas/macro'](),
  '/api/ticker': async () => handlers['/api/gas/ticker'](),
  '/api/history': async (req, res, params) => handlers['/api/gas/history'](req, res, params),
  '/api/signals': async () => handlers['/api/gas/signals'](),
  '/api/levels': async () => handlers['/api/gas/levels'](),
  '/api/gas/forecast': async (req, res, params) => {
    const horizon = params.get('horizon') || '30';
    const key = `forecast_${horizon}`;
    const c = getCache(key); if (c) return c;
    const d = await runPython('forecast', ['--horizon', horizon]);
    setCache(key, d); return d;
  },
  '/api/forecast': async (req, res, params) => handlers['/api/gas/forecast'](req, res, params),
  '/api/gas/ticker': async () => {
    const c = getCache('ticker'); if (c) return c;
    const d = await runPython('ticker'); setCache('ticker', d); return d;
  },
  '/api/gas/history': async (req, res, params) => {
    const interval = params.get('interval') || '1h';
    const period = params.get('period') || '30d';
    const key = `history_${interval}_${period}`;
    const c = getCache(key); if (c) return c;
    const d = await runPython('history', ['--interval', interval, '--period', period]);
    setCache(key, d); return d;
  },
  '/api/gas/signals': async () => {
    const c = getCache('signals'); if (c) return c;
    const d = await runPython('signals'); setCache('signals', d); return d;
  },
  '/api/gas/levels': async () => {
    const c = getCache('levels'); if (c) return c;
    const d = await runPython('levels'); setCache('levels', d); return d;
  },
  '/api/gas/macro': async () => {
    const c = getCache('macro'); if (c) return c;
    const d = await runPython('macro'); setCache('macro', d); return d;
  },
};

const startTime = Date.now();

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url, true);
  const params = new URLSearchParams(parsed.search || '');

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  if (parsed.pathname === '/health' || parsed.pathname === '/api/gas/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok', uptime: (Date.now() - startTime) / 1000,
      timestamp: new Date().toISOString(),
      endpoints: Object.keys(handlers).concat(['/health']),
      cache_size: cache.size,
    }));
    return;
  }

  const handler = handlers[parsed.pathname];
  if (!handler) {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found', endpoints: Object.keys(handlers).concat(['/health']) }));
    return;
  }

  try {
    const data = await handler(req, res, params);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: err.message }));
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[gas-api] Gas Data API running on http://127.0.0.1:${PORT}`);
  console.log(`[gas-api] Endpoints:`);
  Object.keys(handlers).forEach(h => console.log(`  GET ${h}`));
  console.log(`  GET /health`);
});

process.on('SIGTERM', () => { server.close(() => process.exit(0)); });
process.on('SIGINT', () => { server.close(() => process.exit(0)); });
