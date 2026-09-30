"""
Environment auto-propagation service for Stage 3.

This service handles automatic propagation of session-start environment
conditions to test runs, with overrides for time-spanning tests.
"""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EnvironmentReading:
    """Single environment reading at a checkpoint."""
    
    def __init__(
        self,
        test_run_id: int,
        checkpoint: str,
        temp: Decimal,
        rel_h: Decimal,
        time: datetime,
        bar_pres: Decimal,
        source: str
    ):
        self.test_run_id = test_run_id
        self.checkpoint = checkpoint
        self.temp = temp
        self.rel_h = rel_h
        self.time = time
        self.bar_pres = bar_pres
        self.source = source


class EnvironmentSession:
    """Session-start environment conditions."""
    
    def __init__(
        self,
        test_job_id: int,
        start_temp: Decimal,
        start_rel_h: Decimal,
        start_time: datetime,
        start_bar_pres: Decimal
    ):
        self.test_job_id = test_job_id
        self.start_temp = start_temp
        self.start_rel_h = start_rel_h
        self.start_time = start_time
        self.start_bar_pres = start_bar_pres


def create_environment_readings_for_test(
    test_run_id: int,
    session: EnvironmentSession,
    test_duration_category: str
) -> List[EnvironmentReading]:
    """
    Auto-create environment readings for a test based on session defaults.
    
    Logic:
    - Short tests: copy session start to all three checkpoints (start/max/end)
    - Time-spanning tests: copy session start to "start" only; prompt for max/end
    
    Args:
        test_run_id: ID of test run
        session: Session environment conditions
        test_duration_category: "short" or "time_spanning"
    
    Returns:
        List of EnvironmentReading objects to insert
    
    Examples:
        >>> session = EnvironmentSession(101, Decimal("23.2"), Decimal("52"), datetime.now(), Decimal("1013.2"))
        >>> readings = create_environment_readings_for_test(567, session, "short")
        >>> len(readings)
        3
        >>> readings[0].checkpoint
        'start'
    """
    readings = []
    
    # Always create "start" reading from session
    readings.append(EnvironmentReading(
        test_run_id=test_run_id,
        checkpoint="start",
        temp=session.start_temp,
        rel_h=session.start_rel_h,
        time=session.start_time,
        bar_pres=session.start_bar_pres,
        source="auto_carried"
    ))
    
    if test_duration_category == "short":
        # Auto-carry to max and end for short tests
        readings.append(EnvironmentReading(
            test_run_id=test_run_id,
            checkpoint="max",
            temp=session.start_temp,
            rel_h=session.start_rel_h,
            time=session.start_time,
            bar_pres=session.start_bar_pres,
            source="auto_carried"
        ))
        
        readings.append(EnvironmentReading(
            test_run_id=test_run_id,
            checkpoint="end",
            temp=session.start_temp,
            rel_h=session.start_rel_h,
            time=session.start_time,
            bar_pres=session.start_bar_pres,
            source="auto_carried"
        ))
        
        logger.debug(
            f"Created 3 auto-carried readings for short test run {test_run_id}"
        )
    else:
        # Time-spanning tests: only create "start", prompt for max/end
        logger.debug(
            f"Created 1 auto-carried reading for time-spanning test run {test_run_id}. "
            f"Max/end checkpoints will be manually entered."
        )
    
    return readings


def should_auto_propagate_checkpoint(
    test_duration_category: str,
    checkpoint: str
) -> bool:
    """
    Determine if a checkpoint should be auto-propagated from session.
    
    Rules:
    - start: always auto-propagate
    - max/end: only for short tests
    
    Args:
        test_duration_category: "short" or "time_spanning"
        checkpoint: "start", "max", or "end"
    
    Returns:
        True if checkpoint should be auto-carried from session
    
    Examples:
        >>> should_auto_propagate_checkpoint("short", "start")
        True
        >>> should_auto_propagate_checkpoint("short", "end")
        True
        >>> should_auto_propagate_checkpoint("time_spanning", "end")
        False
    """
    if checkpoint == "start":
        return True
    
    if test_duration_category == "short":
        return True
    
    return False


def get_time_spanning_tests() -> List[str]:
    """
    Get list of test IDs that are time-spanning.
    
    These tests require manual "At max" and "At end" readings
    because conditions genuinely change during the test.
    
    Returns:
        List of test IDs that span multiple sessions
    
    Examples:
        >>> tests = get_time_spanning_tests()
        >>> "6.2" in tests  # Creep
        True
        >>> "15" in tests  # Endurance
        True
    """
    # These IDs match test_applicability.yaml
    return [
        "6.2",   # Creep (up to 4 hours)
        "10",    # Warm-up time
        "13",    # Damp heat, steady state (multi-day)
        "14",    # Span stability (multiple sessions)
        "15"     # Endurance (load cycles over days)
    ]


def validate_environment_reading(
    temp: Decimal,
    rel_h: Decimal,
    bar_pres: Decimal
) -> tuple[bool, Optional[str]]:
    """
    Validate environment reading values are within reasonable ranges.
    
    Ranges based on typical laboratory conditions:
    - Temperature: 10°C to 40°C
    - Relative humidity: 20% to 90%
    - Barometric pressure: 900 hPa to 1100 hPa
    
    Args:
        temp: Temperature in °C
        rel_h: Relative humidity in %
        bar_pres: Barometric pressure in hPa
    
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    
    Examples:
        >>> validate_environment_reading(Decimal("23.2"), Decimal("52"), Decimal("1013.2"))
        (True, None)
        >>> validate_environment_reading(Decimal("50"), Decimal("52"), Decimal("1013.2"))
        (False, 'Temperature 50°C outside normal range (10-40°C)')
    """
    # Temperature check (10°C to 40°C)
    if temp < 10 or temp > 40:
        return False, f"Temperature {temp}°C outside normal range (10-40°C)"
    
    # Relative humidity check (20% to 90%)
    if rel_h < 20 or rel_h > 90:
        return False, f"Relative humidity {rel_h}% outside normal range (20-90%)"
    
    # Barometric pressure check (900 hPa to 1100 hPa)
    if bar_pres < 900 or bar_pres > 1100:
        return False, f"Barometric pressure {bar_pres} hPa outside normal range (900-1100 hPa)"
    
    return True, None


def calculate_environment_drift(
    start_reading: EnvironmentReading,
    end_reading: EnvironmentReading
) -> dict:
    """
    Calculate drift in environment conditions during a test.
    
    Useful for time-spanning tests where conditions change.
    
    Args:
        start_reading: Reading at test start
        end_reading: Reading at test end
    
    Returns:
        Dictionary with drift values
    
    Examples:
        >>> start = EnvironmentReading(1, "start", Decimal("23.0"), Decimal("50"), datetime.now(), Decimal("1013"))
        >>> end = EnvironmentReading(1, "end", Decimal("24.5"), Decimal("55"), datetime.now(), Decimal("1012"))
        >>> drift = calculate_environment_drift(start, end)
        >>> drift["temp_drift"]
        Decimal('1.5')
    """
    return {
        "temp_drift": end_reading.temp - start_reading.temp,
        "temp_drift_percent": ((end_reading.temp - start_reading.temp) / start_reading.temp) * 100,
        "rel_h_drift": end_reading.rel_h - start_reading.rel_h,
        "bar_pres_drift": end_reading.bar_pres - start_reading.bar_pres,
        "duration_seconds": (end_reading.time - start_reading.time).total_seconds()
    }


def check_environment_stability(
    readings: List[EnvironmentReading],
    max_temp_drift: Decimal = Decimal("2.0"),
    max_humidity_drift: Decimal = Decimal("10.0")
) -> tuple[bool, Optional[str]]:
    """
    Check if environment remained stable during test.
    
    Used for tests that require stable conditions (most performance tests).
    
    Args:
        readings: List of readings to check
        max_temp_drift: Maximum allowed temperature drift (°C)
        max_humidity_drift: Maximum allowed humidity drift (%)
    
    Returns:
        Tuple of (is_stable, warning_message)
    
    Examples:
        >>> readings = [...]  # Stable readings
        >>> is_stable, msg = check_environment_stability(readings)
        >>> is_stable
        True
    """
    if len(readings) < 2:
        return True, None  # Can't check stability with <2 readings
    
    # Find min/max for each parameter
    temps = [r.temp for r in readings]
    humidities = [r.rel_h for r in readings]
    
    temp_range = max(temps) - min(temps)
    humidity_range = max(humidities) - min(humidities)
    
    warnings = []
    
    if temp_range > max_temp_drift:
        warnings.append(
            f"Temperature varied by {temp_range}°C (limit: {max_temp_drift}°C)"
        )
    
    if humidity_range > max_humidity_drift:
        warnings.append(
            f"Humidity varied by {humidity_range}% (limit: {max_humidity_drift}%)"
        )
    
    if warnings:
        return False, "; ".join(warnings)
    
    return True, None
