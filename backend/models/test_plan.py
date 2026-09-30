"""
Test plan models for dynamic test assembly.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class ResolvedTest(BaseModel):
    """A test with resolved variant after applicability evaluation."""
    
    id: str
    name: str
    clause_ref: str
    resolved_variant: Optional[str] = None
    sequence: int
    duration_category: Literal["short", "time_spanning"]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "4.1",
                "name": "Discrimination",
                "clause_ref": "A.4.8",
                "resolved_variant": "digital",
                "sequence": 5,
                "duration_category": "short"
            }
        }


class TestPlan(BaseModel):
    """Complete test plan for an instrument."""
    
    tests: List[ResolvedTest]
    class_: str
    total_count: int = Field(default=0)
    
    def __init__(self, **data):
        """Auto-calculate total_count on initialization."""
        super().__init__(**data)
        self.total_count = len(self.tests)
    
    def get_test_by_id(self, test_id: str) -> Optional[ResolvedTest]:
        """Get test by ID."""
        return next((t for t in self.tests if t.id == test_id), None)
    
    def get_time_spanning_tests(self) -> List[ResolvedTest]:
        """Get tests that require multiple sessions."""
        return [t for t in self.tests if t.duration_category == "time_spanning"]
    
    def get_short_tests(self) -> List[ResolvedTest]:
        """Get tests that complete in one session."""
        return [t for t in self.tests if t.duration_category == "short"]
    
    class Config:
        json_schema_extra = {
            "example": {
                "tests": [
                    {
                        "id": "1",
                        "name": "Weighing performance",
                        "clause_ref": "A.4.4 / A.5.3.1",
                        "resolved_variant": None,
                        "sequence": 1,
                        "duration_category": "short"
                    },
                    {
                        "id": "4.1",
                        "name": "Discrimination",
                        "clause_ref": "A.4.8",
                        "resolved_variant": "digital",
                        "sequence": 5,
                        "duration_category": "short"
                    }
                ],
                "class_": "II",
                "total_count": 2
            }
        }


class TestPlanRecord(BaseModel):
    """Database record for test plan."""
    
    id: Optional[int] = None
    test_job_id: int
    rulepack_version: str
    tests: List[ResolvedTest]
    class_: str
    total_count: int
    created_at: Optional[str] = None  # ISO timestamp
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_job_id": 101,
                "rulepack_version": "R76-1:2006",
                "tests": [],
                "class_": "II",
                "total_count": 18,
                "created_at": "2026-09-28T09:30:00Z"
            }
        }
