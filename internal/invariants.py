"""
WEALTH — 7 Civilizational Invariants
Chronological Truth: 2026.04.29

Governance Compliance Scoring Engine (G-Score).
"""

import numpy as np
from typing import Dict, Any, List, Optional
from .kernel_math import GovernanceKalmanFilter, calculate_g_score, estimate_lyapunov

class GScoreEngine:
    """
    Instrumentation engine to compute G-Score from 7 Governance Invariants.
    """
    def __init__(self):
        self.kf = GovernanceKalmanFilter()
        # In a production system, these would be loaded from a persistence layer (e.g. Postgres)
        self.g_history: List[float] = [0.7] * 12 
        self.s_history: List[float] = [0.3] * 12

    def compute_signals(self, params: Dict[str, Any]) -> np.ndarray:
        """
        Extract observable signals (z) from tool parameters.
        Normalization: 0.0 (Worst) to 1.0 (Best) for Omega-loaders.
        For S-loaders (Uncertainty, Constraints, Boundaries), 1.0 means HIGH Entropy.
        """
        # 1. Time (Omega-loader): Scale based on horizon_years or discount_rate
        time_sig = np.clip(params.get("horizon_years", 5) / 50.0, 0.0, 1.0)
        
        # 2. Uncertainty (S-loader): Scale based on volatility
        uncertainty_sig = np.clip(params.get("volatility", 0.2) * 2.0, 0.0, 1.0)
        
        # 3. Survival (Omega-loader): Scale based on runway_months or DSCR
        runway = params.get("runway_months", 12.0)
        if runway == float('inf'): runway = 60.0
        survival_sig = np.clip(runway / 36.0, 0.0, 1.0)
        
        # 4. Truth (SNR): 1.0 is high signal integrity
        truth_sig = np.clip(params.get("trust_index", 0.5), 0.0, 1.0)
        
        # 5. Constraints (S-loader): Count of violations
        violations = params.get("violations", [])
        constraint_sig = np.clip(len(violations) * 0.2, 0.0, 1.0)
        
        # 6. Coordination (Omega-loader): Alignment index
        coordination_sig = np.clip(params.get("maruah_score", 0.5), 0.0, 1.0)
        
        # 7. Boundaries (S-loader): Overshoot events
        overshoots = 1.0 if params.get("critical", False) else 0.0
        boundary_sig = np.clip(overshoots, 0.0, 1.0)
        
        return np.array([
            time_sig, uncertainty_sig, survival_sig, 
            truth_sig, constraint_sig, coordination_sig, 
            boundary_sig
        ])

    def evaluate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Predict -> Update -> Score.
        """
        # 1. Detect Regime (simplistic for Phase 1)
        regime = "inclusive"
        if params.get("irreversible", False) or params.get("critical", False):
            regime = "simulative"
            
        # 2. Kalman Cycle
        self.kf.predict(regime=regime)
        z = self.compute_signals(params)
        state = self.kf.update(z)
        
        omega, s = state[0][0], state[1][0]
        
        # 3. Score & Trend
        g_score = calculate_g_score(omega, s)
        delta_s = s - self.s_history[-1]
        
        self.g_history.append(g_score)
        self.s_history.append(s)
        
        # 4. Lyapunov Instability (lambda)
        lyapunov_lambda = estimate_lyapunov(self.g_history)
        
        # 5. Threshold Logic
        verdict = "GO"
        if g_score < 0.45 or lyapunov_lambda > 0.1:
            verdict = "STOP"
        elif g_score < 0.60 or delta_s > 0.05:
            verdict = "HOLD"
            
        return {
            "g_score": round(g_score, 4),
            "delta_s": round(delta_s, 4),
            "lyapunov_lambda": round(lyapunov_lambda, 4),
            "omega_capacity": round(omega, 4),
            "entropy_s": round(s, 4),
            "verdict": verdict,
            "regime": regime
        }

# Global instance for Phase 1
engine = GScoreEngine()

def get_g_score(params: Dict[str, Any]) -> Dict[str, Any]:
    return engine.evaluate(params)
