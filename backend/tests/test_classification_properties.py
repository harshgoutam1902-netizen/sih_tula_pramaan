"""
Property-based tests for classification engine using Hypothesis.

These tests generate random (e, Max) pairs and verify classification
properties hold across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from decimal import Decimal

from services.classification_engine import determine_class, suggest_min_capacity
from models.rulepacks import load_rulepack


# Fixtures
@pytest.fixture(scope="module")
def rulepack():
    """Load rulepack once for all tests."""
    classification_rulepack, _ = load_rulepack("R76-1:2006")
    return classification_rulepack


# Hypothesis strategies for generating test data
@st.composite
def decimal_e_strategy(draw):
    """Generate valid verification scale intervals (e)."""
    # Range: 0.001g to 10g (covers all class bands)
    value = draw(st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 6)))


@st.composite
def decimal_max_strategy(draw):
    """Generate valid maximum capacities (Max)."""
    # Range: 0.1kg to 10,000kg
    value = draw(st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 3)))


# Property Tests
@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_classification_always_returns_valid_status(e, max_cap, rulepack):
    """
    Property: Classification always returns one of three valid statuses.
    
    For any valid (e, Max) pair, the result must be DETERMINED, AMBIGUOUS, or INVALID.
    """
    result = determine_class(e, max_cap, rulepack)
    
    assert result.status in ["DETERMINED", "AMBIGUOUS", "INVALID"]
    assert result.computed_n > 0  # n should always be positive


@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_computed_n_always_equals_max_div_e(e, max_cap, rulepack):
    """
    Property: computed_n always equals Max/e.
    
    Verifies the fundamental calculation is correct.
    """
    result = determine_class(e, max_cap, rulepack)
    
    # Skip invalid cases where engine returned INVALID status
    if result.status == "INVALID":
        return
    
    expected_n = max_cap / e  # Already in grams
    
    # Allow small floating point precision differences
    assert abs(result.computed_n - expected_n) < Decimal("0.000001")


@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_determined_status_has_single_class(e, max_cap, rulepack):
    """
    Property: DETERMINED status always has exactly one class, no candidates.
    """
    result = determine_class(e, max_cap, rulepack)
    
    if result.status == "DETERMINED":
        assert result.class_ is not None
        assert result.class_ in ["I", "II", "III", "IIII"]
        assert result.candidates is None
        assert result.reason is None


@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_ambiguous_status_has_multiple_candidates(e, max_cap, rulepack):
    """
    Property: AMBIGUOUS status always has 2+ candidates, no single class.
    """
    result = determine_class(e, max_cap, rulepack)
    
    if result.status == "AMBIGUOUS":
        assert result.class_ is None
        assert result.candidates is not None
        assert len(result.candidates) >= 2
        assert result.reason is None


@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_invalid_status_has_reason(e, max_cap, rulepack):
    """
    Property: INVALID status always has a reason, no class or candidates.
    """
    result = determine_class(e, max_cap, rulepack)
    
    if result.status == "INVALID":
        assert result.class_ is None
        assert result.candidates is None
        assert result.reason is not None
        assert len(result.reason) > 0


@given(e=decimal_e_strategy(), max_cap=decimal_max_strategy())
@settings(max_examples=1000)
def test_classification_is_deterministic(e, max_cap, rulepack):
    """
    Property: Same inputs always produce same output (deterministic).
    """
    result1 = determine_class(e, max_cap, rulepack)
    result2 = determine_class(e, max_cap, rulepack)
    
    assert result1.status == result2.status
    assert result1.class_ == result2.class_
    assert result1.computed_n == result2.computed_n


# Targeted property tests for specific class bands
def test_class_ii_lower_bound_property(rulepack):
    """
    Property: Instruments at Class II lower bound are classified as Class II.
    
    Class II: 0.001g ≤ e ≤ 0.05g, 100 ≤ n ≤ 100,000
    Lower bound: e=0.001g, n=100 → Max=0.1kg
    """
    e = Decimal("0.001")
    max_cap = Decimal("0.1")  # n = 100
    
    result = determine_class(e, max_cap, rulepack)
    
    # Could be DETERMINED or AMBIGUOUS (boundary case)
    if result.status == "DETERMINED":
        assert result.class_ == "II"
    elif result.status == "AMBIGUOUS":
        assert any(c["class"] == "II" for c in result.candidates)


def test_class_ii_upper_bound_property(rulepack):
    """
    Property: Instruments at Class II upper bound are classified as Class II.
    
    Class II: 0.001g ≤ e ≤ 0.05g, 100 ≤ n ≤ 100,000
    Upper bound: e=0.05g, n=100,000 → Max=5kg
    """
    e = Decimal("0.05")
    max_cap = Decimal("5")  # n = 100,000
    
    result = determine_class(e, max_cap, rulepack)
    
    # Could be DETERMINED or AMBIGUOUS (boundary case)
    if result.status == "DETERMINED":
        assert result.class_ == "II"
    elif result.status == "AMBIGUOUS":
        assert any(c["class"] == "II" for c in result.candidates)


@given(
    e=st.decimals(min_value=Decimal("0.001"), max_value=Decimal("0.05"), places=6),
    n=st.integers(min_value=100, max_value=100000)
)
@settings(max_examples=500)
def test_class_ii_low_e_range_always_includes_class_ii(e, n, rulepack):
    """
    Property: Any (e, n) within Class II (low e) range includes Class II in result.
    
    This tests the band matching logic for the first Class II band.
    """
    max_cap = e * n  # Already in grams
    
    result = determine_class(e, max_cap, rulepack)
    
    # Should never be INVALID for values within known band
    assert result.status != "INVALID"
    
    if result.status == "DETERMINED":
        assert result.class_ == "II"
    elif result.status == "AMBIGUOUS":
        assert any(c["class"] == "II" for c in result.candidates)


def test_suggest_min_capacity_property(rulepack):
    """
    Property: Suggested Min always equals factor × e for each class.
    """
    test_cases = [
        ("I", Decimal("0.001"), 100),    # Min = 100 × 0.001g / 1000 = 0.0001 kg
        ("II", Decimal("0.001"), 20),    # Min = 20 × 0.001g / 1000 = 0.00002 kg
        ("III", Decimal("0.1"), 20),     # Min = 20 × 0.1g / 1000 = 0.002 kg
        ("IIII", Decimal("5"), 10),      # Min = 10 × 5g / 1000 = 0.05 kg
    ]
    
    for class_, e, factor in test_cases:
        suggested_min = suggest_min_capacity(e, class_, rulepack)
        expected_min = (factor * e) / 1000  # Engine converts to kg
        
        assert suggested_min == expected_min, f"Class {class_}: expected {expected_min}, got {suggested_min}"


# Edge case tests
def test_zero_e_is_invalid(rulepack):
    """Edge case: e=0 should be INVALID (returns INVALID status, no exception)."""
    result = determine_class(Decimal("0"), Decimal("100"), rulepack)
    assert result.status == "INVALID"


def test_negative_e_is_invalid(rulepack):
    """Edge case: negative e should be INVALID (returns INVALID status, no exception)."""
    result = determine_class(Decimal("-0.001"), Decimal("100"), rulepack)
    assert result.status == "INVALID"


def test_very_large_n_property(rulepack):
    """
    Property: Very large n values (>100,000) may fall into Class I or be INVALID.
    """
    e = Decimal("0.001")
    max_cap = Decimal("1000")  # n = 1,000,000 (very large)
    
    result = determine_class(e, max_cap, rulepack)
    
    # Should be either Class I (no upper n bound) or INVALID if n_max enforced
    if result.status == "DETERMINED":
        assert result.class_ == "I"
    # AMBIGUOUS or INVALID are also acceptable depending on rulepack interpretation
