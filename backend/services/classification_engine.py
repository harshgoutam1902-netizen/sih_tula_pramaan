"""
Pure-function classification engine for OIML R 76 accuracy classes.

CRITICAL: This module contains NO I/O, NO database queries, NO LLM calls.
All functions are deterministic and fully testable.
"""

from decimal import Decimal
from typing import List, Optional
from models.rulepacks import ClassificationRulepack, ClassBand
from models.instrument import ClassResult, InstrumentProfile


def determine_class(
    e: Decimal,
    max_cap: Decimal,
    rulepack: ClassificationRulepack
) -> ClassResult:
    """
    Determine accuracy class from verification scale interval and maximum capacity.
    
    Pure function - no side effects, deterministic output.
    
    Algorithm:
        1. Validate inputs (e > 0, max_cap > 0)
        2. Calculate n = Max / e (all values in grams)
        3. Find all class bands where (e, n) falls within boundaries
        4. Return DETERMINED (1 match), AMBIGUOUS (2+ matches), or INVALID (0 matches)
    
    Args:
        e: Verification scale interval in grams
        max_cap: Maximum capacity in grams
        rulepack: Classification rules from OIML R 76-1
    
    Returns:
        ClassResult with status and determined class or candidates
    
    Examples:
        >>> rulepack = load_rulepack("R76-1:2006")[0]
        >>> result = determine_class(Decimal("0.001"), Decimal("150"), rulepack)
        >>> result.status
        'DETERMINED'
        >>> result.class_
        'I'
    """
    # Validate inputs
    if e <= 0 or max_cap <= 0:
        return ClassResult(
            status="INVALID",
            computed_n=Decimal("0"),
            reason="e and Max must both be positive values"
        )
    
    # Calculate number of scale intervals (all values in grams)
    n = max_cap / e
    
    # Find all matching class bands
    matches: List[ClassBand] = [
        band for band in rulepack.class_bands
        if band.matches(e, n)
    ]
    
    # No matches - invalid configuration
    if len(matches) == 0:
        return ClassResult(
            status="INVALID",
            computed_n=n,
            reason=f"No class band matches e={e}g, n={n:.2f}"
        )
    
    # Multiple matches - ambiguous, requires human confirmation
    if len(matches) > 1:
        # Serialize ClassBand objects for JSON response
        candidates = [
            {
                "class": band.class_,
                "e_range": f"{band.e_min_g}g - {band.e_max_g if band.e_max_g else '∞'}",
                "n_range": f"{band.n_min} - {band.n_max if band.n_max else '∞'}",
                "note": band.note
            }
            for band in matches
        ]
        return ClassResult(
            status="AMBIGUOUS",
            computed_n=n,
            candidates=candidates
        )
    
    # Single match - determined class
    return ClassResult(
        status="DETERMINED",
        computed_n=n,
        class_=matches[0].class_
    )


def suggest_min_capacity(
    e: Decimal,
    class_: str,
    rulepack: ClassificationRulepack
) -> Decimal:
    """
    Suggest minimum capacity based on class-specific factor from Table 3.
    
    Technician can override this suggestion.
    
    Args:
        e: Verification scale interval in grams
        class_: Determined accuracy class (I, II, III, IIII)
        rulepack: Classification rules
    
    Returns:
        Suggested Min in kilograms
    
    Raises:
        ValueError: If class not found in rulepack
    
    Examples:
        >>> rulepack = load_rulepack("R76-1:2006")[0]
        >>> suggest_min_capacity(Decimal("0.001"), "II", rulepack)
        Decimal('0.020')  # 20 × 0.001g = 0.020kg
    """
    # Find the class band
    band = next(
        (b for b in rulepack.class_bands if b.class_ == class_),
        None
    )
    
    if not band:
        raise ValueError(f"Unknown class: {class_}")
    
    # Min = factor × e (convert grams to kilograms)
    min_cap_g = band.min_capacity_factor * e
    min_cap_kg = min_cap_g / 1000
    
    return min_cap_kg


def validate_multi_interval_ratios(
    instrument: InstrumentProfile,
    class_: str,
    rulepack: ClassificationRulepack
) -> tuple[bool, Optional[str]]:
    """
    Validate multi-interval ratios per OIML R 76-1 Table 4.
    
    Rule: For each partial range i (except the last):
          Max_i / e_(i+1) >= threshold from Table 4
    
    Args:
        instrument: Instrument profile with sub_ranges
        class_: Determined accuracy class
        rulepack: Classification rules with multi_interval_ratios
    
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    
    Examples:
        >>> # Class II threshold is 5000
        >>> # If Max_1 = 10kg and e_2 = 0.001g:
        >>> # Ratio = 10000g / 0.001g = 10,000,000 >= 5000 ✓
    """
    if not instrument.is_multi_interval:
        return True, None
    
    if not instrument.sub_ranges or len(instrument.sub_ranges) < 2:
        return False, "Multi-interval instrument must have at least 2 sub-ranges"
    
    threshold = rulepack.multi_interval_ratios.get(class_)
    if threshold is None:
        return False, f"No multi-interval threshold defined for class {class_}"
    
    # Check each transition except the last
    for i in range(len(instrument.sub_ranges) - 1):
        current_range = instrument.sub_ranges[i]
        next_range = instrument.sub_ranges[i + 1]
        
        # Max_i / e_(i+1) >= threshold
        # Convert max_cap from kg to g
        max_i_g = current_range.max_cap * 1000
        ratio = max_i_g / next_range.e
        
        if ratio < threshold:
            return False, (
                f"Partial range {i+1} transition invalid: "
                f"Max_{i+1} / e_{i+2} = {ratio:.2f} < {threshold} "
                f"(required for Class {class_})"
            )
    
    return True, None
