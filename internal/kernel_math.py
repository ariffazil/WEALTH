import numpy as np
from typing import Tuple, List, Optional

class GovernanceKalmanFilter:
    """
    Kalman Filter for State-Space Estimation of Governance Health.
    States: [Omega (Capacity), S (Entropy)]
    """
    def __init__(self, dt: float = 1.0):
        # State vector [Omega, S]
        self.x = np.array([[0.7], [0.3]])  # Initial guess
        
        # State Transition Matrix (A) - Default to "Inclusive" (Omega stable, S decaying)
        # In a real run, this matrix switches based on detected Regime
        self.A = np.array([
            [1.0, 0.0],  # Omega persistence
            [0.0, 0.9]   # Entropy decay (metabolic cleanup)
        ])
        
        # Process Noise Covariance (Q)
        self.Q = np.eye(2) * 0.01
        
        # Error Covariance Matrix (P)
        self.P = np.eye(2) * 0.1
        
        # Observation Matrix (C) - Mapping States to 7 Invariants
        # Invariants: [Time, Uncertainty, Survival, Truth, Constraints, Coordination, Boundaries]
        # Omega loads on Time, Survival, Coordination
        # S loads on Uncertainty, Constraints, Boundaries
        self.C = np.array([
            [1.0, 0.0],   # Invariant 1: Time (loads on Omega)
            [0.0, 1.0],   # Invariant 2: Uncertainty (loads on S)
            [1.0, -0.5],  # Invariant 3: Survival (Omega increases, S decreases)
            [0.5, -0.5],  # Invariant 4: Truth (Inherent SNR)
            [-0.2, 1.0],  # Invariant 5: Constraints (S loads heavy)
            [0.5, -0.2],  # Invariant 6: Coordination
            [-0.1, 1.0]   # Invariant 7: Boundaries (S loads heavy)
        ])
        
        # Observation Noise Covariance (Theta)
        # Truth and Coordination start with high noise per blueprint
        self.Theta = np.diag([0.2, 0.2, 0.1, 0.5, 0.2, 0.4, 0.2])

    def predict(self, regime: str = "inclusive"):
        """State Prediction Step"""
        # Adjust A based on Regime
        if regime == "extractive":
            self.A = np.array([[0.9, 0.0], [0.1, 1.1]]) # Omega decays, S grows
        elif regime == "simulative":
            self.A = np.array([[1.0, 0.0], [0.05, 1.0]]) # S creeps up while Omega masks
        else:
            self.A = np.array([[1.0, 0.0], [0.0, 0.9]]) # Inclusive
            
        self.x = np.dot(self.A, self.x)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q

    def update(self, z: np.ndarray):
        """Measurement Update Step"""
        # Innovation (Residual)
        y = z - np.dot(self.C, self.x)
        
        # Innovation Covariance
        S = np.dot(self.C, np.dot(self.P, self.C.T)) + self.Theta
        
        # Kalman Gain
        K = np.dot(np.dot(self.P, self.C.T), np.linalg.inv(S))
        
        # Update State
        self.x = self.x + np.dot(K, y)
        
        # Update Error Covariance
        I = np.eye(self.x.shape[0])
        self.P = np.dot((I - np.dot(K, self.C)), self.P)
        
        return self.x

def calculate_g_score(omega: float, s: float) -> float:
    """G = Omega / (Omega + S)"""
    denom = omega + s
    if denom == 0: return 0.0
    return float(np.clip(omega / denom, 0.0, 1.0))

def estimate_lyapunov(history: List[float], window: int = 12) -> float:
    """
    Simplified Lyapunov Exponent (lambda) for instability detection.
    lambda > 0 implies chaotic divergence / pending phase transition.
    """
    if len(history) < window:
        return 0.0
    
    # Use log-divergence of the last N states
    recent = np.array(history[-window:])
    diffs = np.diff(np.log(np.abs(recent) + 1e-9))
    return float(np.mean(diffs))
