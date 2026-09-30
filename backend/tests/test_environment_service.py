"""
Unit tests for environment service.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from services.environment_service import (
    EnvironmentSession,
    EnvironmentReading,
    create_environment_readings_for_test,
    should_auto_propagate_checkpoint,
    get_time_spanning_tests,
    validate_environment_reading,
    calculate_environment_drift,
    check_environment_stability
)


@pytest.fixture
def sample_session():
    """Sample environment session."""
    return EnvironmentSession(
        test_job_id=101,
        start_temp=Decimal("23.2"),
        start_rel_h=Decimal("52"),
        start_time=datetime(2026, 9, 28, 9, 30),
        start_bar_pres=Decimal("1013.2")
    )


class TestCreateEnvironmentReadings:
    """Test environment reading creation logic."""
    
    def test_short_test_creates_three_readings(self, sample_session):
        """Short tests get 3 auto-carried readings (start/max/end)."""
        readings = create_environment_readings_for_test(
            test_run_id=567,
            session=sample_session,
            test_duration_category="short"
        )
        
        assert len(readings) == 3
        
        # Check checkpoints
        checkpoints = [r.checkpoint for r in readings]
        assert "start" in checkpoints
        assert "max" in checkpoints
        assert "end" in checkpoints
        
        # All should be auto-carried
        assert all(r.source == "auto_carried" for r in readings)
        
        # All should have same values (carried from session)
        for reading in readings:
            assert reading.temp == sample_session.start_temp
            assert reading.rel_h == sample_session.start_rel_h
    
    def test_time_spanning_test_creates_one_reading(self, sample_session):
        """Time-spanning tests get only 1 reading (start)."""
        readings = create_environment_readings_for_test(
            test_run_id=567,
            session=sample_session,
            test_duration_category="time_spanning"
        )
        
        assert len(readings) == 1
        assert readings[0].checkpoint == "start"
        assert readings[0].source == "auto_carried"


class TestAutoPropagateCheckpoint:
    """Test auto-propagation logic."""
    
    def test_start_always_auto_propagates(self):
        """Start checkpoint always auto-propagates."""
        assert should_auto_propagate_checkpoint("short", "start") is True
        assert should_auto_propagate_checkpoint("time_spanning", "start") is True
    
    def test_max_end_auto_propagate_for_short(self):
        """Max/end auto-propagate for short tests only."""
        assert should_auto_propagate_checkpoint("short", "max") is True
        assert should_auto_propagate_checkpoint("short", "end") is True
    
    def test_max_end_no_auto_propagate_for_time_spanning(self):
        """Max/end do NOT auto-propagate for time-spanning tests."""
        assert should_auto_propagate_checkpoint("time_spanning", "max") is False
        assert should_auto_propagate_checkpoint("time_spanning", "end") is False


class TestTimeSpanningTests:
    """Test time-spanning test identification."""
    
    def test_known_time_spanning_tests(self):
        """Verify known time-spanning tests are in list."""
        time_spanning = get_time_spanning_tests()
        
        # These are the long-running tests
        assert "6.2" in time_spanning  # Creep
        assert "10" in time_spanning   # Warm-up time
        assert "13" in time_spanning   # Damp heat
        assert "14" in time_spanning   # Span stability
        assert "15" in time_spanning   # Endurance
    
    def test_short_tests_not_in_list(self):
        """Short tests should not be in time-spanning list."""
        time_spanning = get_time_spanning_tests()
        
        # These are short tests
        assert "1" not in time_spanning   # Weighing performance
        assert "5" not in time_spanning   # Repeatability


class TestValidateEnvironmentReading:
    """Test environment reading validation."""
    
    def test_valid_reading(self):
        """Valid readings pass validation."""
        is_valid, error = validate_environment_reading(
            Decimal("23.2"),
            Decimal("52"),
            Decimal("1013.2")
        )
        
        assert is_valid is True
        assert error is None
    
    def test_temperature_too_low(self):
        """Temperature below range fails."""
        is_valid, error = validate_environment_reading(
            Decimal("5"),     # Too low
            Decimal("52"),
            Decimal("1013.2")
        )
        
        assert is_valid is False
        assert "temperature" in error.lower()
        assert "10-40" in error.lower()
    
    def test_temperature_too_high(self):
        """Temperature above range fails."""
        is_valid, error = validate_environment_reading(
            Decimal("45"),    # Too high
            Decimal("52"),
            Decimal("1013.2")
        )
        
        assert is_valid is False
        assert "temperature" in error.lower()
    
    def test_humidity_too_low(self):
        """Humidity below range fails."""
        is_valid, error = validate_environment_reading(
            Decimal("23.2"),
            Decimal("15"),    # Too low
            Decimal("1013.2")
        )
        
        assert is_valid is False
        assert "humidity" in error.lower()
    
    def test_pressure_too_low(self):
        """Pressure below range fails."""
        is_valid, error = validate_environment_reading(
            Decimal("23.2"),
            Decimal("52"),
            Decimal("800")    # Too low
        )
        
        assert is_valid is False
        assert "pressure" in error.lower()


class TestCalculateEnvironmentDrift:
    """Test environment drift calculation."""
    
    def test_drift_calculation(self):
        """Calculate drift between start and end readings."""
        start = EnvironmentReading(
            test_run_id=1,
            checkpoint="start",
            temp=Decimal("23.0"),
            rel_h=Decimal("50"),
            time=datetime(2026, 9, 28, 9, 0),
            bar_pres=Decimal("1013"),
            source="auto_carried"
        )
        
        end = EnvironmentReading(
            test_run_id=1,
            checkpoint="end",
            temp=Decimal("24.5"),
            rel_h=Decimal("55"),
            time=datetime(2026, 9, 28, 13, 0),
            bar_pres=Decimal("1012"),
            source="manual_override"
        )
        
        drift = calculate_environment_drift(start, end)
        
        assert drift["temp_drift"] == Decimal("1.5")
        assert drift["rel_h_drift"] == Decimal("5")
        assert drift["bar_pres_drift"] == Decimal("-1")
        assert drift["duration_seconds"] == 4 * 3600  # 4 hours
    
    def test_no_drift(self):
        """Zero drift when conditions stable."""
        time1 = datetime(2026, 9, 28, 9, 0)
        time2 = datetime(2026, 9, 28, 9, 30)
        
        start = EnvironmentReading(
            1, "start", Decimal("23.0"), Decimal("50"),
            time1, Decimal("1013"), "auto_carried"
        )
        
        end = EnvironmentReading(
            1, "end", Decimal("23.0"), Decimal("50"),
            time2, Decimal("1013"), "auto_carried"
        )
        
        drift = calculate_environment_drift(start, end)
        
        assert drift["temp_drift"] == Decimal("0")
        assert drift["rel_h_drift"] == Decimal("0")
        assert drift["bar_pres_drift"] == Decimal("0")


class TestCheckEnvironmentStability:
    """Test environment stability checking."""
    
    def test_stable_environment(self):
        """Stable environment passes check."""
        readings = [
            EnvironmentReading(
                1, "start", Decimal("23.0"), Decimal("50"),
                datetime.now(), Decimal("1013"), "auto_carried"
            ),
            EnvironmentReading(
                1, "max", Decimal("23.5"), Decimal("52"),
                datetime.now(), Decimal("1013"), "auto_carried"
            ),
            EnvironmentReading(
                1, "end", Decimal("23.2"), Decimal("51"),
                datetime.now(), Decimal("1013"), "auto_carried"
            )
        ]
        
        is_stable, warning = check_environment_stability(readings)
        
        assert is_stable is True
        assert warning is None
    
    def test_unstable_temperature(self):
        """Large temperature drift fails stability check."""
        readings = [
            EnvironmentReading(
                1, "start", Decimal("23.0"), Decimal("50"),
                datetime.now(), Decimal("1013"), "auto_carried"
            ),
            EnvironmentReading(
                1, "end", Decimal("26.0"), Decimal("51"),  # +3°C drift
                datetime.now(), Decimal("1013"), "manual_override"
            )
        ]
        
        is_stable, warning = check_environment_stability(
            readings,
            max_temp_drift=Decimal("2.0")
        )
        
        assert is_stable is False
        assert "temperature" in warning.lower()
        assert "3" in warning  # Drift amount
    
    def test_unstable_humidity(self):
        """Large humidity drift fails stability check."""
        readings = [
            EnvironmentReading(
                1, "start", Decimal("23.0"), Decimal("50"),
                datetime.now(), Decimal("1013"), "auto_carried"
            ),
            EnvironmentReading(
                1, "end", Decimal("23.5"), Decimal("65"),  # +15% drift
                datetime.now(), Decimal("1013"), "manual_override"
            )
        ]
        
        is_stable, warning = check_environment_stability(
            readings,
            max_humidity_drift=Decimal("10.0")
        )
        
        assert is_stable is False
        assert "humidity" in warning.lower()
    
    def test_single_reading_stable(self):
        """Single reading considered stable (can't check drift)."""
        readings = [
            EnvironmentReading(
                1, "start", Decimal("23.0"), Decimal("50"),
                datetime.now(), Decimal("1013"), "auto_carried"
            )
        ]
        
        is_stable, warning = check_environment_stability(readings)
        
        assert is_stable is True
        assert warning is None
