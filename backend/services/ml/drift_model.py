"""
DEMO model with hardcoded weights.
NOT learned from data. NEVER decides anything regulatory.
For demonstration purposes only.
"""

import math

MODEL_VERSION = "demo-hardcoded-0.1"


def drift_risk(
    delta_temp: float,
    delta_rh: float,
    load_pct: float,
    time_spanning: float
) -> float:
    """
    Compute drift risk score using hardcoded sigmoid model.
    
    This is a DEMO model with fixed weights, not trained on real data.
    It exists solely to demonstrate ML integration patterns.
    
    Args:
        delta_temp: Absolute temperature change from baseline (°C)
        delta_rh: Absolute relative humidity change from baseline (%)
        load_pct: Load as percentage of capacity (0-100)
        time_spanning: 1 for time-spanning tests, 0 for short tests
    
    Returns:
        Risk score in [0, 1], where higher values indicate higher drift risk
    """
    # Hardcoded weights (NOT learned from data)
    z = -3.2 + 0.35 * abs(delta_temp) + 0.04 * abs(delta_rh) + 0.02 * load_pct + 0.9 * time_spanning
    
    # Clamp z to prevent overflow in exp
    z = max(-50.0, min(50.0, z))
    
    # Sigmoid: 1 / (1 + exp(-z))
    risk = 1.0 / (1.0 + math.exp(-z))
    
    # Clamp result to [0, 1]
    return max(0.0, min(1.0, risk))
