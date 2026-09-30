"""
Pytest configuration and shared fixtures.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from models.rulepacks import load_rulepack


@pytest.fixture(scope="session")
def rulepack_version():
    """Default rulepack version for tests."""
    return "R76-1:2006"


@pytest.fixture(scope="session")
def classification_rulepack(rulepack_version):
    """Load classification rulepack once for all tests."""
    classification, _ = load_rulepack(rulepack_version)
    return classification


@pytest.fixture(scope="session")
def test_applicability_rulepack(rulepack_version):
    """Load test applicability rulepack once for all tests."""
    _, test_applicability = load_rulepack(rulepack_version)
    return test_applicability


@pytest.fixture
def sample_class_ii_instrument():
    """Sample Class II electronic instrument profile."""
    from models.instrument import InstrumentProfile
    
    return InstrumentProfile(
        id=1,
        model_id=100,
        e=Decimal("0.001"),
        max_capacity=Decimal("150"),
        min_capacity=Decimal("0.020"),
        is_multi_range=False,
        is_multi_interval=False,
        self_indicating_type="self_indicating",
        indication_type="digital",
        is_electronic=True,
        has_tare_device=True,
        intended_use="general_trade"
    )


@pytest.fixture
def sample_class_iii_instrument():
    """Sample Class III mechanical instrument profile."""
    from models.instrument import InstrumentProfile
    
    return InstrumentProfile(
        id=2,
        model_id=101,
        e=Decimal("0.5"),
        max_capacity=Decimal("1.5"),
        min_capacity=Decimal("0.010"),
        is_multi_range=False,
        is_multi_interval=False,
        self_indicating_type="self_indicating",
        indication_type="analogue",
        is_electronic=False,
        has_tare_device=False,
        intended_use="general_trade"
    )


@pytest.fixture
def sample_environment_session():
    """Sample environment session."""
    from services.environment_service import EnvironmentSession
    
    return EnvironmentSession(
        test_job_id=101,
        start_temp=Decimal("23.2"),
        start_rel_h=Decimal("52"),
        start_time=datetime(2026, 9, 28, 9, 30),
        start_bar_pres=Decimal("1013.2")
    )
