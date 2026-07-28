from typing import List, Dict, Any, Optional
import time

class TrajectoryDetector:
    """
    Tracks recurrence, baseline delta, and changes over time windows for entropy signals.
    """

    def __init__(self):
        pass

    def compute_trajectory(
        self, 
        current_value: float, 
        baseline_value: float, 
        history_values: List[float], 
        time_window: str = "current decision episode"
    ) -> Dict[str, Any]:
        """
        Computes the delta from baseline, trend, and recurrence patterns.
        """
        baseline_delta = abs(current_value - baseline_value)
        recurrence = len(history_values) + 1
        
        if history_values:
            # Simple average of prior values to determine direction
            historical_avg = sum(history_values) / len(history_values)
            trend = "increasing" if current_value > historical_avg else "decreasing" if current_value < historical_avg else "stable"
        else:
            trend = "stable"
            
        return {
            "recurrence": recurrence,
            "baseline_delta": float(baseline_delta),
            "trend": trend,
            "time_window": time_window,
            "status": "SIGNAL" if recurrence == 1 else "PATTERN" if recurrence <= 3 else "MATERIAL_CONTRADICTION"
        }
