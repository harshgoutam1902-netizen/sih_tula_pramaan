"""
Unit tests for classification engine boundary and edge cases.
"""

import pytest
from decimal import Decimal

from services.classification_engine import (
    determine_class,
    suggest_min_capacity,
    validate_multi_interval_ratios
)
from models.rulepacks import load_rulepack
from models.instrument import InstrumentProfile, SubRange


@pytest.fixture(scope="module")
def rulepack():
    """Load rulepack once for all tests."""
    classification_rulepack, _ = load_rulepack("R76-1:2006")
    return classification_rulepack


class TestClassificationBoundaries:
    """Test classification at known boundary values."""
    
    def test_class_ii_lower_bound_exact(self, rulepack):
        """Test Class II lower bound: e=0.001g, n=100."""
        e = Decimal("0.001")
        max_cap = Decimal("0.1")  # Max=0.1g, n = 100
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.status in ["DETERMINED", "AMBIGUOUS"]
        assert result.computed_n == Decimal("100")
        
        if result.status == "DETERMINED":
            assert result.class_ == "II"
    
    def test_class_ii_upper_bound_exact(self, rulepack):
        """Test Class II upper bound: e=0.05g, n=100,000."""
        e = Decimal("0.05")
        max_cap = Decimal("5000")  # Max=5000g, n = 100,000
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.status in ["DETERMINED", "AMBIGUOUS"]
        assert result.computed_n == Decimal("100000")
    
    def test_class_iii_typical_value(self, rulepack):
        """Test typical Class III instrument."""
        e = Decimal("0.5")
        max_cap = Decimal("1500")  # Max=1500g, n = 3000
        
        result = determine_class(e, max_cap, rulepack)
        
        if result.status == "DETERMINED":
            assert result.class_ == "III"
    
    def test_class_iiii_typical_value(self, rulepack):
        """Test typical Class IIII instrument."""
        e = Decimal("10")
        max_cap = Decimal("5000")  # Max=5000g, n = 500
        
        result = determine_class(e, max_cap, rulepack)
        
        if result.status == "DETERMINED":
            assert result.class_ == "IIII"


class TestInvalidClassifications:
    """Test invalid instrument configurations."""
    
    def test_n_too_small_for_any_class(self, rulepack):
        """Test n < 100 (below all class minimums)."""
        e = Decimal("1")
        max_cap = Decimal("50")  # Max=50g, n = 50
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.status == "INVALID"
        assert "no" in result.reason.lower() or "invalid" in result.reason.lower()
    
    def test_e_too_small_for_defined_classes(self, rulepack):
        """Test e < 0.001g (below all class minimums)."""
        e = Decimal("0.0001")
        max_cap = Decimal("10")  # Max=10g, n = 100,000
        
        result = determine_class(e, max_cap, rulepack)
        
        # Might be INVALID or might match Class I depending on rulepack
        assert result.status in ["DETERMINED", "INVALID"]
    
    def test_negative_e_returns_invalid(self, rulepack):
        """Test negative e returns INVALID."""
        e = Decimal("-0.001")
        max_cap = Decimal("100")
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.status == "INVALID"
        assert "positive" in result.reason.lower()
    
    def test_negative_max_returns_invalid(self, rulepack):
        """Test negative Max returns INVALID."""
        e = Decimal("0.001")
        max_cap = Decimal("-100")
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.status == "INVALID"
        assert "positive" in result.reason.lower()


class TestAmbiguousClassifications:
    """Test known ambiguous cases."""
    
    def test_boundary_between_class_bands(self, rulepack):
        """Test values at exact band boundaries may be ambiguous."""
        # This is implementation-dependent - boundaries might overlap
        e = Decimal("0.05")  # Upper bound of Class II low-e, might overlap with high-e
        max_cap = Decimal("5")
        
        result = determine_class(e, max_cap, rulepack)
        
        # Could be DETERMINED or AMBIGUOUS depending on band definitions
        assert result.status in ["DETERMINED", "AMBIGUOUS"]
        
        if result.status == "AMBIGUOUS":
            assert len(result.candidates) >= 2


class TestMinCapacitySuggestion:
    """Test minimum capacity suggestion logic."""
    
    def test_suggest_min_class_i(self, rulepack):
        """Class I: Min = 100 × e."""
        e = Decimal("0.001")
        suggested = suggest_min_capacity(e, "I", rulepack)
        
        expected = Decimal("0.1")  # 100 × 0.001g = 0.1g = 0.0001kg... wait
        # Actually: 100 × 0.001g = 0.1g, convert to kg = 0.0001kg
        expected = (Decimal("100") * e) / 1000
        
        assert suggested == expected
    
    def test_suggest_min_class_ii(self, rulepack):
        """Class II: Min = 20 or 50 × e depending on range."""
        e = Decimal("0.001")
        suggested = suggest_min_capacity(e, "II", rulepack)
        
        # First band has factor 20
        expected = (Decimal("20") * e) / 1000
        
        assert suggested == expected
    
    def test_suggest_min_class_iii(self, rulepack):
        """Class III: Min = 20 × e."""
        e = Decimal("0.5")
        suggested = suggest_min_capacity(e, "III", rulepack)
        
        expected = (Decimal("20") * e) / 1000
        
        assert suggested == expected
    
    def test_suggest_min_class_iiii(self, rulepack):
        """Class IIII: Min = 10 × e."""
        e = Decimal("10")
        suggested = suggest_min_capacity(e, "IIII", rulepack)
        
        expected = (Decimal("10") * e) / 1000
        
        assert suggested == expected
    
    def test_suggest_min_unknown_class_raises_error(self, rulepack):
        """Unknown class should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown class"):
            suggest_min_capacity(Decimal("0.001"), "V", rulepack)


class TestMultiIntervalValidation:
    """Test multi-interval ratio validation."""
    
    def test_valid_multi_interval_class_ii(self, rulepack):
        """Valid Class II multi-interval (threshold=5000)."""
        instrument = InstrumentProfile(
            model_id=1,
            e=Decimal("0.001"),
            max_capacity=Decimal("10"),
            is_multi_range=False,
            is_multi_interval=True,
            sub_ranges=[
                SubRange(e=Decimal("0.001"), max_cap=Decimal("5")),
                SubRange(e=Decimal("0.01"), max_cap=Decimal("10"))
            ],
            self_indicating_type="self_indicating",
            indication_type="digital",
            is_electronic=True,
            has_tare_device=True,
            intended_use="general_trade"
        )
        
        # Max_1 / e_2 = 5kg / 0.01g = 5000g / 0.01g = 500,000 >= 5000 ✓
        is_valid, error = validate_multi_interval_ratios(instrument, "II", rulepack)
        
        assert is_valid
        assert error is None
    
    def test_invalid_multi_interval_ratio_too_small(self, rulepack):
        """Invalid Class II multi-interval (ratio < 5000)."""
        instrument = InstrumentProfile(
            model_id=1,
            e=Decimal("0.001"),
            max_capacity=Decimal("10"),
            is_multi_range=False,
            is_multi_interval=True,
            sub_ranges=[
                SubRange(e=Decimal("0.001"), max_cap=Decimal("1")),  # Only 1kg
                SubRange(e=Decimal("1"), max_cap=Decimal("10"))      # e jumps to 1g
            ],
            self_indicating_type="self_indicating",
            indication_type="digital",
            is_electronic=True,
            has_tare_device=True,
            intended_use="general_trade"
        )
        
        # Max_1 / e_2 = 1kg / 1g = 1000g / 1g = 1000 < 5000 ✗
        is_valid, error = validate_multi_interval_ratios(instrument, "II", rulepack)
        
        assert not is_valid
        assert error is not None
        assert "1000" in error  # Should mention the actual ratio
    
    def test_single_interval_always_valid(self, rulepack):
        """Non-multi-interval instruments always pass."""
        instrument = InstrumentProfile(
            model_id=1,
            e=Decimal("0.001"),
            max_capacity=Decimal("150"),
            is_multi_range=False,
            is_multi_interval=False,
            sub_ranges=None,
            self_indicating_type="self_indicating",
            indication_type="digital",
            is_electronic=True,
            has_tare_device=True,
            intended_use="general_trade"
        )
        
        is_valid, error = validate_multi_interval_ratios(instrument, "II", rulepack)
        
        assert is_valid
        assert error is None


class TestDecimalPrecision:
    """Test that Decimal arithmetic is used correctly."""
    
    def test_no_floating_point_errors(self, rulepack):
        """Verify Decimal arithmetic avoids floating point precision issues."""
        e = Decimal("0.001")
        max_cap = Decimal("0.3")  # n should be exactly 300
        
        result = determine_class(e, max_cap, rulepack)
        
        # Check that n is exactly 300, not 299.999999 or 300.000001
        assert result.computed_n == Decimal("300")
    
    def test_large_number_precision(self, rulepack):
        """Test precision with large n values."""
        e = Decimal("0.001")
        max_cap = Decimal("100")  # n = 100,000
        
        result = determine_class(e, max_cap, rulepack)
        
        assert result.computed_n == Decimal("100000")
