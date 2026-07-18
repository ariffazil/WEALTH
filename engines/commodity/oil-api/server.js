/**
 * Brent Crude Oil Data API Server — WEALTH Organ
 * Node.js HTTP server proxying to Python data fetcher. 5-min cache.
 * DITEMPA BUKAN DIBERI — Forged, Not Given.
 */

const http = require('http');
const { execFile } = require('child_process');
const path = require('path');
const url = require('url');

const PORT = 3457;
const PYTHON = '/root/venv/bin/python3';
const SCRIPT = path.join(__dirname, 'fetch_oil.py');
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
        console.error(`[oil-api] Python error (${command}):`, msg.trim());
        reject(new Error(msg.trim()));
        return;
      }
      try { resolve(JSON.parse(stdout)); }
      catch (e) { reject(new Error(`Invalid JSON: ${e.message}`)); }
    });
  });
}

const handlers = {
  '/api/oil/apex': async () => {
    const c = getCache('apex'); if (c) return c;
    const d = await runPython('apex'); setCache('apex', d); return d;
  },
  '/api/oil/signal_v2': async () => {
    const c = getCache('signal_v2'); if (c) return c;
    const d = await runPython('signal_v2'); setCache('signal_v2', d); return d;
  },
  '/api/oil/calendar': async () => {
    const c = getCache('calendar'); if (c) return c;
    const d = await runPython('calendar'); setCache('calendar', d); return d;
  },
  '/api/apex': async () => handlers['/api/oil/apex'](),
  '/api/signal_v2': async () => handlers['/api/oil/signal_v2'](),
  '/api/calendar': async () => handlers['/api/oil/calendar'](),
  '/api/macro': async () => handlers['/api/oil/macro'](),
  '/api/ticker': async () => handlers['/api/oil/ticker'](),
  '/api/history': async (req, res, params) => handlers['/api/oil/history'](req, res, params),
  '/api/signals': async () => handlers['/api/oil/signals'](),
  '/api/levels': async () => handlers['/api/oil/levels'](),
  '/api/oil/ticker': async () => {
    const c = getCache('ticker'); if (c) return c;
    const d = await runPython('ticker'); setCache('ticker', d); return d;
  },
  '/api/oil/history': async (req, res, params) => {
    const interval = params.get('interval') || '1h';
    const period = params.get('period') || '30d';
    const key = `history_${interval}_${period}`;
    const c = getCache(key); if (c) return c;
    const d = await runPython('history', ['--interval', interval, '--period', period]);
    setCache(key, d); return d;
  },
  '/api/oil/signals': async () => {
    const c = getCache('signals'); if (c) return c;
    const d = await runPython('signals'); setCache('signals', d); return d;
  },
  '/api/oil/levels': async () => {
    const c = getCache('levels'); if (c) return c;
    const d = await runPython('levels'); setCache('levels', d); return d;
  },
  '/api/oil/macro': async () => {
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

  if (parsed.pathname === '/health' || parsed.pathname === '/api/oil/health') {
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
  console.log(`[oil-api] Oil Data API running on http://127.0.0.1:${PORT}`);
  console.log(`[oil-api] Endpoints:`);
  Object.keys(handlers).forEach(h => console.log(`  GET ${h}`));
  console.log(`  GET /health`);
});

process.on('SIGTERM', () => { server.close(() => process.exit(0)); });
process.on('SIGINT', () => { server.close(() => process.exit(0)); });
