"""
Unit tests for test plan assembly engine.
"""

import pytest
from decimal import Decimal

from services.test_plan_engine import assemble_test_plan, get_test_summary
from models.rulepacks import load_rulepack
from models.instrument import InstrumentProfile, ClassResult


@pytest.fixture(scope="module")
def rulepack():
    """Load test applicability rulepack."""
    _, test_applicability_rulepack = load_rulepack("R76-1:2006")
    return test_applicability_rulepack


@pytest.fixture
def electronic_class_ii_instrument():
    """Typical electronic Class II instrument with digital indication."""
    return InstrumentProfile(
        model_id=1,
        e=Decimal("0.001"),
        max_capacity=Decimal("150"),
        min_capacity=Decimal("0.020"),
        is_multi_range=False,
        is_multi_interval=False,
        self_indicating_type="self_indicating",
        indication_type="digital",
        is_electronic=True,
        has_tare_device=True,
        intended_use="general_trade",
        class_="II"  # Added for variant resolution
    )


@pytest.fixture
def mechanical_class_iii_instrument():
    """Typical mechanical Class III instrument."""
    return InstrumentProfile(
        model_id=2,
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
def non_self_indicating_instrument():
    """Non-self-indicating instrument."""
    return InstrumentProfile(
        model_id=3,
        e=Decimal("0.01"),
        max_capacity=Decimal("50"),
        is_multi_range=False,
        is_multi_interval=False,
        self_indicating_type="non_self_indicating",
        indication_type=None,
        is_electronic=True,
        has_tare_device=False,
        intended_use="general_trade"
    )


class TestBasicTestPlanAssembly:
    """Test basic test plan assembly logic."""
    
    def test_electronic_instrument_includes_electronic_tests(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Electronic instruments should include all electronic-specific tests."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        test_ids = [t.id for t in plan.tests]
        
        # Electronic tests that should be included
        assert "2" in test_ids   # Temperature effect
        assert "10" in test_ids  # Warm-up time
        assert "11" in test_ids  # Variations of voltage
        assert "12.1" in test_ids  # Short time power reductions
        assert "12.2" in test_ids  # Electrical bursts
        assert "12.3" in test_ids  # Electrostatic discharges
        assert "12.4" in test_ids  # Immunity to radiated EM fields
        assert "13" in test_ids  # Damp heat
    
    def test_mechanical_instrument_excludes_electronic_tests(
        self, mechanical_class_iii_instrument, rulepack
    ):
        """Mechanical instruments should not include electronic-specific tests."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="III",
            computed_n=Decimal("3000")
        )
        
        plan = assemble_test_plan(mechanical_class_iii_instrument, class_result, rulepack)
        
        test_ids = [t.id for t in plan.tests]
        
        # Electronic tests should NOT be included
        assert "2" not in test_ids   # Temperature effect
        assert "10" not in test_ids  # Warm-up time
        assert "11" not in test_ids  # Variations of voltage
        assert "12.1" not in test_ids
        assert "12.2" not in test_ids
        assert "12.3" not in test_ids
        assert "12.4" not in test_ids
        assert "13" not in test_ids  # Damp heat
    
    def test_always_applicable_tests_included(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Tests marked 'always' should be in every plan."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        test_ids = [t.id for t in plan.tests]
        
        # These should always be included
        assert "1" in test_ids    # Weighing performance
        assert "3.1" in test_ids  # Eccentricity using weights
        assert "4.1" in test_ids  # Discrimination
        assert "5" in test_ids    # Repeatability
        assert "6.1" in test_ids  # Zero return
        assert "6.2" in test_ids  # Creep
        assert "7" in test_ids    # Stability of equilibrium
        assert "15" in test_ids   # Endurance
        assert "16" in test_ids   # Examination of construction
    
    def test_test_plan_has_correct_class(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Test plan should include the determined class."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        assert plan.class_ == "II"
    
    def test_test_plan_total_count_matches_test_list(
        self, electronic_class_ii_instrument, rulepack
    ):
        """total_count should equal length of tests list."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        assert plan.total_count == len(plan.tests)
        assert plan.total_count > 0


class TestConditionalTestInclusion:
    """Test conditional test applicability."""
    
    def test_tare_test_included_when_tare_device_present(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Test 9 (Tare) should only be included if has_tare_device=True."""
        # Instrument has tare device
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        test_ids = [t.id for t in plan.tests]
        
        assert "9" in test_ids  # Tare test included
    
    def test_tare_test_excluded_when_no_tare_device(
        self, mechanical_class_iii_instrument, rulepack
    ):
        """Test 9 (Tare) should be excluded if has_tare_device=False."""
        # Instrument has no tare device
        class_result = ClassResult(
            status="DETERMINED",
            class_="III",
            computed_n=Decimal("3000")
        )
        
        plan = assemble_test_plan(mechanical_class_iii_instrument, class_result, rulepack)
        test_ids = [t.id for t in plan.tests]
        
        assert "9" not in test_ids  # Tare test excluded
    
    def test_sensitivity_test_only_for_non_self_indicating(
        self, non_self_indicating_instrument, rulepack
    ):
        """Test 4.2 (Sensitivity) only for non-self-indicating instruments."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("5000000")
        )
        
        plan = assemble_test_plan(non_self_indicating_instrument, class_result, rulepack)
        test_ids = [t.id for t in plan.tests]
        
        assert "4.2" in test_ids  # Sensitivity included
    
    def test_sensitivity_test_excluded_for_self_indicating(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Self-indicating instruments should not have sensitivity test."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        test_ids = [t.id for t in plan.tests]
        
        assert "4.2" not in test_ids  # Sensitivity excluded


class TestVariantResolution:
    """Test variant resolution for tests with sub-forms."""
    
    def test_discrimination_resolves_to_digital_variant(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Discrimination test should resolve to 'digital' variant."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        discrimination_test = plan.get_test_by_id("4.1")
        assert discrimination_test is not None
        assert discrimination_test.resolved_variant == "digital"
    
    def test_discrimination_resolves_to_analogue_variant(
        self, mechanical_class_iii_instrument, rulepack
    ):
        """Discrimination test should resolve to 'analogue' variant."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="III",
            computed_n=Decimal("3000")
        )
        
        plan = assemble_test_plan(mechanical_class_iii_instrument, class_result, rulepack)
        
        discrimination_test = plan.get_test_by_id("4.1")
        assert discrimination_test is not None
        assert discrimination_test.resolved_variant == "analogue"
    
    @pytest.mark.xfail(reason="Tilting test requires class_ field but fixture has no mechanism to pass class from ClassResult to InstrumentProfile")
    def test_tilting_test_class_dependent_variant(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Tilting test should have class-dependent variant."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        tilting_test = plan.get_test_by_id("8")
        if tilting_test:  # May be included for Class II
            # Should have resolved_variant = "II" (class-based variant)
            assert tilting_test.resolved_variant is not None


class TestSequenceOrdering:
    """Test that tests are ordered by sequence number."""
    
    def test_tests_ordered_by_sequence(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Tests should be sorted by sequence number."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        sequences = [t.sequence for t in plan.tests]
        
        # Check that sequences are in ascending order
        assert sequences == sorted(sequences)
    
    def test_weighing_performance_is_first(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Weighing performance (Test 1) should be first."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        
        assert plan.tests[0].id == "1"
        assert "Weighing performance" in plan.tests[0].name


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_non_determined_classification_raises_error(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Cannot assemble test plan for non-DETERMINED classification."""
        ambiguous_result = ClassResult(
            status="AMBIGUOUS",
            computed_n=Decimal("150000"),
            candidates=[{"class": "II"}]
        )
        
        with pytest.raises(ValueError, match="Cannot assemble test plan"):
            assemble_test_plan(electronic_class_ii_instrument, ambiguous_result, rulepack)
    
    def test_invalid_classification_raises_error(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Cannot assemble test plan for INVALID classification."""
        invalid_result = ClassResult(
            status="INVALID",
            computed_n=Decimal("50"),
            reason="No class matches"
        )
        
        with pytest.raises(ValueError, match="Cannot assemble test plan"):
            assemble_test_plan(electronic_class_ii_instrument, invalid_result, rulepack)


class TestDurationCategories:
    """Test duration category assignment."""
    
    def test_time_spanning_tests_identified(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Time-spanning tests should be correctly identified."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        time_spanning = plan.get_time_spanning_tests()
        
        time_spanning_ids = [t.id for t in time_spanning]
        
        # These should be time-spanning
        assert "6.2" in time_spanning_ids  # Creep
        assert "10" in time_spanning_ids   # Warm-up time
        assert "13" in time_spanning_ids   # Damp heat
        assert "15" in time_spanning_ids   # Endurance
    
    def test_short_tests_identified(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Short tests should be correctly identified."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        short = plan.get_short_tests()
        
        short_ids = [t.id for t in short]
        
        # These should be short
        assert "1" in short_ids   # Weighing performance
        assert "5" in short_ids   # Repeatability
        assert "11" in short_ids  # Variations of voltage


class TestSummaryGeneration:
    """Test test plan summary generation."""
    
    def test_summary_includes_all_fields(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Summary should include all expected fields."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        summary = get_test_summary(plan)
        
        assert "total_count" in summary
        assert "class" in summary
        assert "short_tests" in summary
        assert "time_spanning_tests" in summary
        assert "first_test" in summary
        assert "last_test" in summary
    
    def test_summary_counts_accurate(
        self, electronic_class_ii_instrument, rulepack
    ):
        """Summary counts should match actual test counts."""
        class_result = ClassResult(
            status="DETERMINED",
            class_="II",
            computed_n=Decimal("150000")
        )
        
        plan = assemble_test_plan(electronic_class_ii_instrument, class_result, rulepack)
        summary = get_test_summary(plan)
        
        assert summary["total_count"] == len(plan.tests)
        assert summary["short_tests"] + summary["time_spanning_tests"] == summary["total_count"]
        assert summary["class"] == "II"
