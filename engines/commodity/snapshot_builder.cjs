/**
 * Shared commodity snapshot builder — WEALTH Organ
 *
 * Single source of truth for `wealth.snapshot.v1` assembly and the
 * `coherence_id` hash. Previously this block was triplicated byte-for-byte
 * across gold-api / oil-api / gas-api server.js (only `asset` differed),
 * which is a drift surface: a fix applied to one lane silently left the
 * other two behind.
 *
 * Hash semantics: JSON.stringify of a deep-key-sorted object, then sha256.
 * The deep sort exists so the digest matches Python's
 * `json.dumps(obj, sort_keys=True, separators=(',',':'), ensure_ascii=False)`
 * — which is what tests recompute independently. Do not change either side
 * without changing both.
 *
 * DITEMPA BUKAN DIBERI — Forged, Not Given.
 */

'use strict';

const crypto = require('crypto');

/** Key-sorted clone, recursively. Arrays keep order; object keys sort. */
function nodeBody(obj) {
  if (Array.isArray(obj)) return obj.map(nodeBody);
  if (obj !== null && typeof obj === 'object') {
    const sorted = {};
    Object.keys(obj).sort().forEach((key) => { sorted[key] = nodeBody(obj[key]); });
    return sorted;
  }
  return obj;
}

/** Canonical serialization used for both hashing and cross-language comparison. */
function canonicalize(unsigned) {
  return JSON.stringify(nodeBody(unsigned));
}

/** sha256 hex of the canonical body. */
function coherenceId(unsigned) {
  return crypto.createHash('sha256').update(canonicalize(unsigned)).digest('hex');
}

/**
 * Assemble a wealth.snapshot.v1 object from the three raw lanes.
 *
 * @param {object}   p
 * @param {string}   p.asset      'gold' | 'oil' | 'gas'
 * @param {object}   p.ticker     raw ticker payload (required; error => throw)
 * @param {object?}  p.levels     raw levels payload, may be null/error
 * @param {object?}  p.macro      raw macro payload, may be null/error
 * @param {string}   p.observedAt ISO-8601 timestamp for the whole snapshot
 * @returns {object} snapshot with a single `observed_at` key and a coherence_id
 */
function buildSnapshot({ asset, ticker, levels, macro, observedAt }) {
  if (!ticker || ticker.error) throw new Error('snapshot: ticker unavailable');
  if (!observedAt) throw new Error('snapshot: observedAt required');

  const unsigned = {
    schema: 'wealth.snapshot.v1',
    asset,
    observed_at: observedAt,
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

  unsigned.coherence_id = coherenceId(unsigned);
  return unsigned;
}

module.exports = { buildSnapshot, nodeBody, canonicalize, coherenceId };
