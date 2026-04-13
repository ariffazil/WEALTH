/**
 * WEALTH by arifOS — F1–F13 Floor Enforcement Engine
 * 
 * Physics > Narrative. Maruah > Convenience.
 * Every operation MUST pass through checkFloors() before execution.
 * 
 * DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
 */

'use strict';

// Floor definitions
const FLOORS = {
  F1:  { id: 'F1',  name: 'Reversible',          rule: 'All mutations must be reversible or declare irreversibility' },
  F2:  { id: 'F2',  name: 'Truth Band',           rule: '≥99% truth or declare confidence band explicitly' },
  F3:  { id: 'F3',  name: 'Human-AI-Evidence',    rule: 'Human judgment, AI analysis, and evidence must align' },
  F4:  { id: 'F4',  name: 'Clarity',              rule: 'Every output reduces complexity ΔS≤0, never adds noise' },
  F5:  { id: 'F5',  name: 'Peace',                rule: 'Peace score ≥ 1.0 before seal. No unresolved panic.' },
  F6:  { id: 'F6',  name: 'Maruah-First',         rule: 'ASEAN/MY dignity context. Maruah is a real variable.' },
  F7:  { id: 'F7',  name: 'Humility Band',        rule: 'Uncertainty declared: 0.03–0.15 minimum on projections' },
  F8:  { id: 'F8',  name: 'Law & Safety',         rule: 'Financial data stays local. No external sync without consent.' },
  F9:  { id: 'F9',  name: 'Anti-Hantu',           rule: 'No phantom balances, ghost transactions, or unresolved entries' },
  F10: { id: 'F10', name: 'AI Ontology',          rule: 'AI advises only. Human decides. AI never claims authority.' },
  F11: { id: 'F11', name: 'Auth Critical',        rule: 'Critical commands require authentication + 888 HOLD' },
  F12: { id: 'F12', name: 'Block Overrides',      rule: 'No bypass of floor logic permitted, by anyone' },
  F13: { id: 'F13', name: 'Sovereign Human Veto', rule: 'Human can reject any AI recommendation, unconditionally' },
};

// Epistemic tag enum
const EPISTEMIC = {
  CLAIM:      'CLAIM',
  PLAUSIBLE:  'PLAUSIBLE',
  HYPOTHESIS: 'HYPOTHESIS',
  ESTIMATE:   'ESTIMATE',
  UNKNOWN:    'UNKNOWN',
};

// Hold types
const HOLD = {
  TRIGGERED: '888-HOLD-TRIGGERED',
  CLEARED:   '888-HOLD-CLEARED',
  PENDING:   '888-HOLD-PENDING',
};

/**
 * checkFloors — Gate function. Call before ANY financial operation.
 * @param {Object} operation - { type, payload, epistemic, reversible }
 * @returns {{ pass: boolean, holds: string[], violations: string[], warnings: string[] }}
 */
function checkFloors(operation) {
  const result = {
    pass: true,
    holds: [],
    violations: [],
    warnings: [],
    epoch: new Date().toISOString(),
  };

  // F1 — Reversible
  if (operation.reversible === false) {
    result.holds.push(HOLD.TRIGGERED);
    result.holds.push(`F1: Operation "${operation.type}" declared irreversible. 888 HOLD activated.`);
    result.pass = false;
  }

  // F2 — Truth Band
  if (operation.epistemic === EPISTEMIC.UNKNOWN) {
    result.warnings.push('F2: UNKNOWN epistemic tag. Declare confidence band before proceeding.');
  }
  if (operation.confidence !== undefined && operation.confidence < 0.99 && !operation.band_declared) {
    result.warnings.push(`F2: Confidence ${operation.confidence} < 0.99 — band must be declared.`);
  }

  // F5 — Peace
  if (operation.peace2 !== undefined && operation.peace2 < 1.0) {
    result.holds.push(`F5: Peace score ${operation.peace2} < 1.0. Resolve state before seal.`);
    result.pass = false;
  }

  // F7 — Humility Band on projections
  if (operation.type === 'PROJECTION' && !operation.uncertainty_band) {
    result.violations.push('F7: Projection without uncertainty band declared. Violation.');
    result.pass = false;
  }

  // F8 — No external sync without consent
  if (operation.external_sync === true && !operation.user_consent) {
    result.violations.push('F8: External sync attempted without user consent. BLOCKED.');
    result.pass = false;
  }

  // F9 — Anti-Hantu
  if (operation.has_unresolved_entries === true) {
    result.warnings.push('F9: Unresolved entries detected. Resolve before seal.');
  }

  // F10 — AI Ontology
  if (operation.ai_is_deciding === true) {
    result.violations.push('F10: AI attempting to decide, not advise. BLOCKED.');
    result.pass = false;
  }

  // F12 — Block overrides
  if (operation.floor_override === true) {
    result.violations.push('F12: Floor override attempted. BLOCKED. No exceptions.');
    result.pass = false;
  }

  return result;
}

/**
 * assertFloors — Hard assert. Throws if floors fail.
 * @param {Object} operation
 */
function assertFloors(operation) {
  const result = checkFloors(operation);
  if (!result.pass) {
    throw new Error(
      `FLOOR VIOLATION\n` +
      `Violations: ${result.violations.join(' | ')}\n` +
      `Holds: ${result.holds.join(' | ')}\n` +
      `Epoch: ${result.epoch}`
    );
  }
  return result;
}

module.exports = { FLOORS, EPISTEMIC, HOLD, checkFloors, assertFloors };
