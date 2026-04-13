/**
 * WEALTH by arifOS — VAULT999 Append-Only Ledger
 * 
 * Every decision path is immutable. No mutation. No deletion.
 * DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
 */

import { appendFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { createHash } from 'node:crypto';

/**
 * Initialize the VAULT999 ledger.
 * @param {string} path - Path to JSONL file
 * @returns {{ path: string }}
 */
export function initVault999(path = './data/vault999.jsonl') {
  const absolute = resolve(path);
  const dir = dirname(absolute);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  return { path: absolute };
}

/**
 * Append an immutable record to VAULT999.
 * @param {Object} record
 * @param {{ path: string }} vault
 * @returns {Object} Record with vault_seal, epoch, and integrity hash
 */
export function appendVault999(record, vault) {
  const entry = {
    ...record,
    vault_seal: 'VAULT999',
    epoch: new Date().toISOString(),
    integrity: computeIntegrityHash(record),
  };
  const line = JSON.stringify(entry) + '\n';
  appendFileSync(vault.path, line);
  return entry;
}

function computeIntegrityHash(record) {
  return createHash('sha256').update(JSON.stringify(record)).digest('hex').slice(0, 16);
}
