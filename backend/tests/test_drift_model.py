"""
Unit tests for drift risk model.
"""

import pytest
from services.ml.drift_model import drift_risk, MODEL_VERSION


def test_model_version():
    """Test model version is set."""
    assert MODEL_VERSION == "demo-hardcoded-0.1"


def test_drift_risk_baseline():
    """Test drift risk at baseline (no change)."""
    risk = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=0.0, time_spanning=0.0)
    
    # Should be low risk at baseline
    assert 0.0 <= risk <= 1.0
    assert risk < 0.1


def test_drift_risk_bounds():
    """Test drift risk is always in [0, 1]."""
    test_cases = [
        (0.0, 0.0, 0.0, 0.0),
        (10.0, 10.0, 50.0, 1.0),
        (50.0, 50.0, 100.0, 1.0),
        (-10.0, -10.0, 0.0, 0.0),
        (100.0, 100.0, 100.0, 1.0),
    ]
    
    for delta_temp, delta_rh, load_pct, time_spanning in test_cases:
        risk = drift_risk(delta_temp, delta_rh, load_pct, time_spanning)
        assert 0.0 <= risk <= 1.0, f"Risk {risk} out of bounds for inputs: {delta_temp}, {delta_rh}, {load_pct}, {time_spanning}"


def test_drift_risk_increases_with_delta_temp():
    """Test risk increases with temperature change."""
    risk_0 = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    risk_5 = drift_risk(delta_temp=5.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    risk_10 = drift_risk(delta_temp=10.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    
    assert risk_5 > risk_0
    assert risk_10 > risk_5


def test_drift_risk_increases_with_delta_rh():
    """Test risk increases with humidity change."""
    risk_0 = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    risk_10 = drift_risk(delta_temp=0.0, delta_rh=10.0, load_pct=50.0, time_spanning=0.0)
    risk_20 = drift_risk(delta_temp=0.0, delta_rh=20.0, load_pct=50.0, time_spanning=0.0)
    
    assert risk_10 > risk_0
    assert risk_20 > risk_10


def test_drift_risk_increases_with_load():
    """Test risk increases with load percentage."""
    risk_0 = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=0.0, time_spanning=0.0)
    risk_50 = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    risk_100 = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=100.0, time_spanning=0.0)
    
    assert risk_50 > risk_0
    assert risk_100 > risk_50


def test_drift_risk_increases_with_time_spanning():
    """Test risk increases for time-spanning tests."""
    risk_short = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    risk_spanning = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=50.0, time_spanning=1.0)
    
    assert risk_spanning > risk_short


def test_drift_risk_deterministic():
    """Test drift risk is deterministic (same inputs = same output)."""
    inputs = (5.0, 10.0, 50.0, 1.0)
    
    risk_1 = drift_risk(*inputs)
    risk_2 = drift_risk(*inputs)
    risk_3 = drift_risk(*inputs)
    
    assert risk_1 == risk_2
    assert risk_2 == risk_3


def test_drift_risk_symmetric_for_delta():
    """Test absolute value is used for deltas."""
    risk_pos = drift_risk(delta_temp=5.0, delta_rh=10.0, load_pct=50.0, time_spanning=0.0)
    risk_neg = drift_risk(delta_temp=-5.0, delta_rh=-10.0, load_pct=50.0, time_spanning=0.0)
    
    assert abs(risk_pos - risk_neg) < 1e-9


def test_drift_risk_extreme_inputs():
    """Test model handles extreme inputs without error."""
    # Very large temperature change
    risk = drift_risk(delta_temp=1000.0, delta_rh=0.0, load_pct=50.0, time_spanning=0.0)
    assert 0.0 <= risk <= 1.0
    
    # Very large humidity change
    risk = drift_risk(delta_temp=0.0, delta_rh=1000.0, load_pct=50.0, time_spanning=0.0)
    assert 0.0 <= risk <= 1.0
    
    # Negative deltas
    risk = drift_risk(delta_temp=-1000.0, delta_rh=-1000.0, load_pct=0.0, time_spanning=0.0)
    assert 0.0 <= risk <= 1.0


def test_drift_risk_combined_factors():
    """Test risk with multiple factors combined."""
    # Baseline
    risk_baseline = drift_risk(delta_temp=0.0, delta_rh=0.0, load_pct=0.0, time_spanning=0.0)
    
    # All factors high
    risk_high = drift_risk(delta_temp=10.0, delta_rh=20.0, load_pct=100.0, time_spanning=1.0)
    
    assert risk_high > risk_baseline
    assert risk_high > 0.5  # Should be significantly elevated


def test_drift_risk_realistic_scenario():
    """Test realistic environmental scenario."""
    # Baseline: 20°C, 50% RH
    # Reading after 8 hours: 25°C, 60% RH, 50% load, time-spanning test
    
    risk = drift_risk(delta_temp=5.0, delta_rh=10.0, load_pct=50.0, time_spanning=1.0)
    
    assert 0.0 < risk < 1.0
    assert 0.2 < risk < 0.8  # Should be moderate risk
