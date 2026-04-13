/**
 * WEALTH by arifOS — 000–999 Pipeline State Machine
 * 
 * Every decision cycle runs this pipeline.
 * No stage can be skipped.
 * 
 * DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
 */

'use strict';

const { checkFloors } = require('./floors');
const { emitTelemetry } = require('./telemetry');

const STAGES = {
  INIT:    '000',
  THINK:   '111',
  EXPLORE: '333',
  HEART:   '555',
  REASON:  '777',
  AUDIT:   '888',
  SEAL:    '999',
};

/**
 * runPipeline — Execute a full 000–999 decision cycle
 * @param {Object} context - The decision context
 * @param {Object} handlers - Stage handler functions { init, think, explore, heart, reason }
 * @returns {Object} Sealed result with telemetry
 */
async function runPipeline(context, handlers = {}) {
  const state = {
    stage: STAGES.INIT,
    epoch: new Date().toISOString(),
    context,
    options: [],
    chosen: null,
    holds: [],
    violations: [],
    peace2: 1.0,
    confidence: 0.0,
    sealed: false,
  };

  // 000 INIT — Boot, safety scan
  state.stage = STAGES.INIT;
  state.epoch = new Date().toISOString();
  if (handlers.init) await handlers.init(state);

  // 111 THINK — Clean reason, no narrative bias
  state.stage = STAGES.THINK;
  if (handlers.think) await handlers.think(state);

  // 333 EXPLORE — Generate ≥3 options
  state.stage = STAGES.EXPLORE;
  if (handlers.explore) await handlers.explore(state);
  if (state.options.length < 3) {
    state.violations.push('333: Fewer than 3 options explored. Pipeline integrity compromised.');
  }

  // 555 HEART — Peace ≥ 1.0 + Maruah check
  state.stage = STAGES.HEART;
  if (handlers.heart) await handlers.heart(state);
  if (state.peace2 < 1.0) {
    state.holds.push('555: Peace < 1.0. Cannot proceed to REASON.');
    state.stage = STAGES.AUDIT;
    return await _audit(state);
  }

  // 777 REASON — Compare trade-offs
  state.stage = STAGES.REASON;
  if (handlers.reason) await handlers.reason(state);

  // 888 AUDIT — Declare holds + uncertainty
  state.stage = STAGES.AUDIT;
  state = await _audit(state);
  if (state.holds.length > 0) return state; // Blocked at audit

  // 999 SEAL — Telemetry emit, epoch stamp
  return await _seal(state);
}

async function _audit(state) {
  state.stage = STAGES.AUDIT;
  const floorCheck = checkFloors({
    type: 'PIPELINE_SEAL',
    peace2: state.peace2,
    reversible: state.holds.length === 0,
    ai_is_deciding: false,
    floor_override: false,
  });
  state.holds.push(...floorCheck.holds);
  state.violations.push(...floorCheck.violations);
  return state;
}

async function _seal(state) {
  state.stage = STAGES.SEAL;
  state.sealed = true;
  const telemetry = await emitTelemetry(state);
  state.telemetry = telemetry;
  return state;
}

module.exports = { STAGES, runPipeline };
