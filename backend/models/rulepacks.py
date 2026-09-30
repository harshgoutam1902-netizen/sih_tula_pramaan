"""
Rulepack models for OIML R 76 classification and test applicability.

These models load and validate versioned YAML rulepack files.
All regulatory decision logic operates on these data structures.
"""

from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator
import yaml


class ClassBand(BaseModel):
    """A single accuracy class band from OIML R 76-1 Table 3."""
    
    class_: Literal["I", "II", "III", "IIII"] = Field(alias="class")
    e_min_g: Decimal
    e_max_g: Optional[Decimal]
    n_min: int
    n_max: Optional[int]
    min_capacity_factor: int
    note: Optional[str] = None
    
    class Config:
        populate_by_name = True
    
    def matches(self, e: Decimal, n: Decimal) -> bool:
        """
        Check if (e, n) falls within this band's boundaries.
        
        Args:
            e: Verification scale interval in grams
            n: Number of scale intervals (Max / e)
        
        Returns:
            True if (e, n) matches this band's criteria
        """
        # Check e boundaries
        e_ok = (self.e_min_g <= e)
        if self.e_max_g is not None:
            e_ok = e_ok and (e <= self.e_max_g)
        
        # Check n boundaries
        n_ok = (self.n_min <= n)
        if self.n_max is not None:
            n_ok = n_ok and (n <= self.n_max)
        
        return e_ok and n_ok
    
    def __str__(self) -> str:
        e_max_str = f"{self.e_max_g}g" if self.e_max_g else "∞"
        n_max_str = str(self.n_max) if self.n_max else "∞"
        return f"Class {self.class_}: {self.e_min_g}g ≤ e ≤ {e_max_str}, {self.n_min} ≤ n ≤ {n_max_str}"


class ClassificationRulepack(BaseModel):
    """Classification rules from OIML R 76-1:2006."""
    
    version: str
    class_bands: List[ClassBand]
    multi_interval_ratios: dict[str, int]
    special_application_allowed: bool = True
    
    @validator("class_bands")
    def validate_bands_not_empty(cls, v):
        if not v:
            raise ValueError("class_bands cannot be empty")
        return v
    
    @validator("multi_interval_ratios")
    def validate_all_classes_have_ratios(cls, v):
        required_classes = {"I", "II", "III", "IIII"}
        if not required_classes.issubset(v.keys()):
            missing = required_classes - v.keys()
            raise ValueError(f"Missing multi_interval_ratios for classes: {missing}")
        return v
    
    @classmethod
    def load_from_yaml(cls, filepath: str) -> "ClassificationRulepack":
        """Load rulepack from YAML file with validation."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


class TestDefinition(BaseModel):
    """A single test definition from OIML R 76-2 applicability matrix."""
    
    id: str
    name: str
    clause_ref: str
    applies_if: str  # Python-evaluable expression or "always" or "VERIFY"
    variant_by: Optional[str] = None  # Field name for variant selection
    sequence: int
    duration_category: Literal["short", "time_spanning"]
    note: Optional[str] = None
    
    @validator("applies_if")
    def validate_applies_if_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("applies_if cannot be empty")
        return v
    
    @validator("sequence")
    def validate_sequence_positive(cls, v):
        if v <= 0:
            raise ValueError("sequence must be positive")
        return v


class TestApplicabilityRulepack(BaseModel):
    """Test applicability matrix from OIML R 76-2:2006."""
    
    version: str
    tests: List[TestDefinition]
    
    @validator("tests")
    def validate_tests_not_empty(cls, v):
        if not v:
            raise ValueError("tests cannot be empty")
        return v
    
    @validator("tests")
    def validate_unique_test_ids(cls, v):
        ids = [t.id for t in v]
        if len(ids) != len(set(ids)):
            duplicates = [tid for tid in ids if ids.count(tid) > 1]
            raise ValueError(f"Duplicate test IDs found: {duplicates}")
        return v
    
    @validator("tests")
    def validate_unique_sequences(cls, v):
        sequences = [t.sequence for t in v]
        if len(sequences) != len(set(sequences)):
            duplicates = [seq for seq in sequences if sequences.count(seq) > 1]
            raise ValueError(f"Duplicate sequence numbers found: {duplicates}")
        return v
    
    def get_test_by_id(self, test_id: str) -> Optional[TestDefinition]:
        """Get test definition by ID."""
        return next((t for t in self.tests if t.id == test_id), None)
    
    def get_time_spanning_tests(self) -> List[TestDefinition]:
        """Get all tests that span multiple sessions."""
        return [t for t in self.tests if t.duration_category == "time_spanning"]
    
    @classmethod
    def load_from_yaml(cls, filepath: str) -> "TestApplicabilityRulepack":
        """Load rulepack from YAML file with validation."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


# Module-level cache for loaded rulepacks
_rulepack_cache: dict[str, tuple[ClassificationRulepack, TestApplicabilityRulepack]] = {}


def load_rulepack(version: str, rulepack_dir: str = "rulepacks") -> tuple[ClassificationRulepack, TestApplicabilityRulepack]:
    """
    Load both classification and test applicability rulepacks for a version.
    
    Results are cached in memory. To reload, restart the application.
    
    Args:
        version: Rulepack version (e.g., "R76-1:2006")
        rulepack_dir: Base directory for rulepacks
    
    Returns:
        Tuple of (ClassificationRulepack, TestApplicabilityRulepack)
    
    Raises:
        FileNotFoundError: If rulepack files don't exist
        ValueError: If rulepack validation fails
    """
    if version in _rulepack_cache:
        return _rulepack_cache[version]
    
    # Normalize version to directory name (e.g., "R76-1:2006" -> "oiml-r76-1_2006")
    version_dir = version.lower().replace(":", "_").replace("-", "_").replace(" ", "_")
    base_path = str(__import__("pathlib").Path(__file__).resolve().parents[2] / "rulepacks" / "oiml-r76-1_2006")
    
    classification_path = f"{base_path}/classification.yaml"
    test_applicability_path = f"{base_path}/test_applicability.yaml"
    
    classification_rulepack = ClassificationRulepack.load_from_yaml(classification_path)
    test_applicability_rulepack = TestApplicabilityRulepack.load_from_yaml(test_applicability_path)
    
    # Verify versions match
    if classification_rulepack.version != version:
        raise ValueError(f"Classification rulepack version mismatch: expected {version}, got {classification_rulepack.version}")
    if test_applicability_rulepack.version != version:
        raise ValueError(f"Test applicability rulepack version mismatch: expected {version}, got {test_applicability_rulepack.version}")
    
    _rulepack_cache[version] = (classification_rulepack, test_applicability_rulepack)
    return _rulepack_cache[version]


def clear_rulepack_cache():
    """Clear the rulepack cache. Used for testing or hot-reloading."""
    global _rulepack_cache
    _rulepack_cache = {}
