"""
Instrument profile models for classification and test planning.
"""

from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class SubRange(BaseModel):
    """A single sub-range for multi-range or multi-interval instruments."""
    
    e: Decimal
    max_cap: Decimal
    min_cap: Optional[Decimal] = None
    
    @validator("e", "max_cap", "min_cap")
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Values must be positive")
        return v


class InstrumentProfile(BaseModel):
    """Complete instrument profile for classification and test routing."""
    
    # Database ID (optional for creation)
    id: Optional[int] = None
    model_id: int
    
    # ========== Classification Parameters ==========
    e: Decimal = Field(..., description="Verification scale interval (grams)")
    max_capacity: Decimal = Field(..., description="Maximum capacity (kg)")
    min_capacity: Optional[Decimal] = Field(None, description="Minimum capacity (kg)")
    
    is_multi_range: bool = False
    is_multi_interval: bool = False
    sub_ranges: Optional[List[SubRange]] = None
    
    # ========== Category Parameters ==========
    self_indicating_type: Literal["self_indicating", "semi_self_indicating", "non_self_indicating"]
    indication_type: Optional[Literal["digital", "analogue"]] = Field(
        None,
        description="Required if self_indicating_type is 'self_indicating'"
    )
    is_electronic: bool
    has_tare_device: bool
    intended_use: Literal["general_trade", "direct_sales", "price_computing", "labelling", "grading"]
    
    @validator("e", "max_capacity", "min_capacity")
    def validate_positive_values(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Capacity and interval values must be positive")
        return v
    
    @validator("indication_type", always=True)
    def validate_indication_type_required_for_self_indicating(cls, v, values):
        """indication_type is required for self_indicating instruments."""
        if "self_indicating_type" in values:
            if values["self_indicating_type"] == "self_indicating" and v is None:
                raise ValueError("indication_type is required for self_indicating instruments")
        return v
    
    @validator("sub_ranges", always=True)
    def validate_sub_ranges_for_multi(cls, v, values):
        """sub_ranges required if multi-range or multi-interval."""
        is_multi = values.get("is_multi_range") or values.get("is_multi_interval")
        if is_multi and not v:
            raise ValueError("sub_ranges required for multi-range or multi-interval instruments")
        return v
    
    def get(self, field_name: str):
        """Helper for variant resolution in test plan assembly."""
        return getattr(self, field_name, None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "e": "0.001",
                "max_capacity": "150",
                "min_capacity": "0.020",
                "is_multi_range": False,
                "is_multi_interval": False,
                "self_indicating_type": "self_indicating",
                "indication_type": "digital",
                "is_electronic": True,
                "has_tare_device": True,
                "intended_use": "general_trade"
            }
        }


class ClassResult(BaseModel):
    """Result of classification determination."""
    
    status: Literal["DETERMINED", "AMBIGUOUS", "INVALID"]
    computed_n: Decimal
    class_: Optional[str] = None
    candidates: Optional[List[dict]] = None  # Serialized ClassBand objects
    reason: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "DETERMINED",
                    "computed_n": "150000.000000",
                    "class_": "II",
                    "candidates": None,
                    "reason": None
                },
                {
                    "status": "AMBIGUOUS",
                    "computed_n": "100000.000000",
                    "class_": None,
                    "candidates": [{"class": "II", "note": "Upper e bound"}],
                    "reason": None
                },
                {
                    "status": "INVALID",
                    "computed_n": "50.000000",
                    "class_": None,
                    "candidates": None,
                    "reason": "No class band matches e=0.001g, n=50"
                }
            ]
        }


class ClassDetermination(BaseModel):
    """Persisted classification with human confirmation."""
    
    id: Optional[int] = None
    instrument_profile_id: int
    rulepack_version: str
    computed_n: Decimal
    status: Literal["DETERMINED", "AMBIGUOUS", "INVALID"]
    determined_class: Optional[str] = None
    candidates: Optional[dict] = None  # JSON serialized
    confirmed_by: Optional[int] = None  # User ID
    override_reason: Optional[str] = None
    confirmed_at: Optional[str] = None  # ISO timestamp
    
    @validator("override_reason", always=True)
    def validate_override_reason_for_ambiguous(cls, v, values):
        """override_reason required for AMBIGUOUS confirmations."""
        if values.get("status") == "AMBIGUOUS" and not v:
            raise ValueError("override_reason is required for AMBIGUOUS classifications")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "instrument_profile_id": 123,
                "rulepack_version": "R76-1:2006",
                "computed_n": "150000.000000",
                "status": "DETERMINED",
                "determined_class": "II",
                "candidates": None,
                "confirmed_by": 45,
                "override_reason": None,
                "confirmed_at": "2026-09-28T10:42:00Z"
            }
        }
