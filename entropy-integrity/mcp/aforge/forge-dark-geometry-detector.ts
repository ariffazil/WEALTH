/**
 * forge_dark_geometry_detector — Build the detector from versioned signal rules.
 *
 * Modes:
 *   shadow   — observe only, no output
 *   evaluate — produce signal scores
 *   compare  — compare two evaluations
 *   promote  — promote rules from shadow to evaluate
 *
 * No direct production enforcement mode initially.
 */

import { readFileSync } from "fs";

interface SignalRule {
  id: string;
  name: string;
  patterns: string[];
  weight: number;
  benign_alternative: string;
  mode: "shadow" | "evaluate";
}

interface DetectorResult {
  detector_version: string;
  mode: string;
  signals: Array<{
    rule_id: string;
    signal_name: string;
    matches: string[];
    score: number;
    benign_alternative: string;
  }>;
  aggregate_score: number;
  timestamp: string;
}

export function forge_dark_geometry_detector(
  text: string,
  rulesPath: string,
  mode: "shadow" | "evaluate" | "compare" | "promote" = "evaluate"
): DetectorResult | { promoted: string[] } {
  const rules: SignalRule[] = JSON.parse(readFileSync(rulesPath, "utf-8"));
  const textLower = text.toLowerCase();

  if (mode === "promote") {
    // Promote shadow rules to evaluate mode
    const promoted = rules
      .filter((r) => r.mode === "shadow")
      .map((r) => {
        r.mode = "evaluate";
        return r.id;
      });
    return { promoted };
  }

  // Evaluate (or shadow)
  const signals = rules
    .filter((r) => r.mode === "evaluate" || mode === "shadow")
    .map((rule) => {
      const matches = rule.patterns.filter((p) => textLower.includes(p.toLowerCase()));
      return {
        rule_id: rule.id,
        signal_name: rule.name,
        matches,
        score: matches.length > 0 ? rule.weight * (matches.length / rule.patterns.length) : 0,
        benign_alternative: rule.benign_alternative,
      };
    })
    .filter((s) => s.matches.length > 0);

  const aggregate =
    signals.length > 0
      ? signals.reduce((sum, s) => sum + s.score, 0) / signals.length
      : 0;

  return {
    detector_version: "v1.0.0",
    mode,
    signals,
    aggregate_score: Math.round(aggregate * 10000) / 10000,
    timestamp: new Date().toISOString(),
  };
}
