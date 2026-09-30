"""
Pure-function test plan assembly engine for OIML R 76 test applicability.

CRITICAL: This module contains NO I/O, NO database queries, NO LLM calls.
All functions are deterministic and fully testable.
"""

from typing import List, Dict, Any
import logging
from models.rulepacks import TestApplicabilityRulepack, TestDefinition
from models.instrument import InstrumentProfile, ClassResult
from models.test_plan import TestPlan, ResolvedTest


logger = logging.getLogger(__name__)


def assemble_test_plan(
    instrument: InstrumentProfile,
    class_result: ClassResult,
    rulepack: TestApplicabilityRulepack
) -> TestPlan:
    """
    Assemble complete test plan from instrument profile and determined class.
    
    Pure function - no side effects, deterministic output.
    
    Algorithm:
        1. Build evaluation context from instrument + class
        2. Filter tests where applies_if evaluates to True
        3. Resolve variants (e.g., discrimination → digital/analogue sub-form)
        4. Sort by sequence number
        5. Return complete test plan
    
    Args:
        instrument: Complete instrument profile
        class_result: Determined classification (must be DETERMINED status)
        rulepack: Test applicability rules from OIML R 76-2
    
    Returns:
        TestPlan with resolved tests
    
    Raises:
        ValueError: If class_result.status != "DETERMINED"
    
    Examples:
        >>> # Electronic Class II instrument with digital indication
        >>> plan = assemble_test_plan(instrument, class_result, rulepack)
        >>> len(plan.tests)
        18
        >>> plan.class_
        'II'
    """
    if class_result.status != "DETERMINED":
        raise ValueError(
            f"Cannot assemble test plan for {class_result.status} classification. "
            f"Classification must be confirmed first."
        )
    
    # Build evaluation context for applicability conditions
    ctx = _build_evaluation_context(instrument, class_result)
    
    # Filter and resolve tests
    applicable_tests: List[ResolvedTest] = []
    
    for test_def in rulepack.tests:
        # Skip tests marked VERIFY (not yet confirmed by metrologist)
        if test_def.applies_if == "VERIFY":
            logger.warning(
                f"Skipping test {test_def.id} ({test_def.name}) - "
                f"marked VERIFY, requires metrologist review"
            )
            continue
        
        # Evaluate applicability condition
        if not _evaluate_condition(test_def.applies_if, ctx):
            continue
        
        # Resolve variant if needed
        resolved_variant = None
        if test_def.variant_by:
            resolved_variant = instrument.get(test_def.variant_by)
            if resolved_variant is None:
                logger.warning(
                    f"Test {test_def.id} has variant_by={test_def.variant_by} "
                    f"but instrument has no value for that field"
                )
        
        applicable_tests.append(ResolvedTest(
            id=test_def.id,
            name=test_def.name,
            clause_ref=test_def.clause_ref,
            resolved_variant=resolved_variant,
            sequence=test_def.sequence,
            duration_category=test_def.duration_category
        ))
    
    # Sort by sequence number
    applicable_tests.sort(key=lambda t: t.sequence)
    
    return TestPlan(
        tests=applicable_tests,
        class_=class_result.class_
    )


def _build_evaluation_context(
    instrument: InstrumentProfile,
    class_result: ClassResult
) -> Dict[str, Any]:
    """
    Build context dictionary for condition evaluation.
    
    Maps instrument profile fields to a flat dictionary suitable for eval().
    """
    return {
        "class_": class_result.class_,
        "electronic": instrument.is_electronic,
        "self_indicating": instrument.self_indicating_type != "non_self_indicating",
        "self_indicating_type": instrument.self_indicating_type,
        "indication_type": instrument.indication_type,
        "has_tare_device": instrument.has_tare_device,
        "intended_use": instrument.intended_use,
        "is_multi_range": instrument.is_multi_range,
        "is_multi_interval": instrument.is_multi_interval,
    }


def _evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate applicability condition against context.
    
    Security: Uses restricted eval with no builtins to prevent code injection.
    
    Examples:
        "always" → True
        "electronic == True" → context["electronic"]
        "class_ in ['II', 'III', 'IIII']" → context["class_"] in ["II", "III", "IIII"]
        "electronic == True and has_tare_device == True" → both conditions True
    
    Args:
        condition: Python-evaluable expression string
        context: Dictionary of available variables
    
    Returns:
        Boolean result of condition evaluation
        False if condition is invalid (fail-safe)
    """
    # Special case: always apply
    if condition == "always":
        return True
    
    # Restricted eval - no builtins, only provided context
    try:
        result = eval(condition, {"__builtins__": {}}, context)
        return bool(result)
    except Exception as e:
        # Log error and fail safe (don't include test if condition broken)
        logger.error(
            f"Error evaluating condition '{condition}': {e}. "
            f"Test will not be included (fail-safe behavior)."
        )
        return False


def get_test_summary(test_plan: TestPlan) -> Dict[str, Any]:
    """
    Generate summary statistics for a test plan.
    
    Useful for displaying test plan overview to technicians.
    
    Args:
        test_plan: Assembled test plan
    
    Returns:
        Dictionary with summary statistics
    """
    time_spanning = test_plan.get_time_spanning_tests()
    short = test_plan.get_short_tests()
    
    # Group by test category (crude parsing of clause refs)
    performance_tests = [t for t in test_plan.tests if t.clause_ref.startswith("A.4")]
    environmental_tests = [t for t in test_plan.tests if t.clause_ref.startswith("A.5") or t.clause_ref.startswith("B.")]
    checklist_tests = [t for t in test_plan.tests if "Checklist" in t.name or t.id.startswith("17")]
    
    return {
        "total_count": test_plan.total_count,
        "class": test_plan.class_,
        "short_tests": len(short),
        "time_spanning_tests": len(time_spanning),
        "performance_tests": len(performance_tests),
        "environmental_tests": len(environmental_tests),
        "checklist_tests": len(checklist_tests),
        "first_test": test_plan.tests[0].name if test_plan.tests else None,
        "last_test": test_plan.tests[-1].name if test_plan.tests else None,
    }
