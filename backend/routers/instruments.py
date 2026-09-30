"""
Instrument profile API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import logging

from database import get_db
from models.instrument import InstrumentProfile
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ========== Request/Response Models ==========

from pydantic import BaseModel, Field


class CreateInstrumentProfileRequest(BaseModel):
    """Request to create instrument profile."""
    model_id: int
    
    # Classification parameters
    e: str = Field(..., description="Verification scale interval (grams)")
    max_capacity: str = Field(..., description="Maximum capacity (kg)")
    min_capacity: Optional[str] = Field(None, description="Minimum capacity (kg)")
    is_multi_range: bool = False
    is_multi_interval: bool = False
    sub_ranges: Optional[list] = None
    
    # Category parameters
    self_indicating_type: str
    indication_type: Optional[str] = None
    is_electronic: bool
    has_tare_device: bool
    intended_use: str


class UpdateInstrumentProfileRequest(BaseModel):
    """Request to update instrument profile."""
    model_id: Optional[int] = None
    e: Optional[str] = None
    max_capacity: Optional[str] = None
    min_capacity: Optional[str] = None
    is_multi_range: Optional[bool] = None
    is_multi_interval: Optional[bool] = None
    sub_ranges: Optional[list] = None
    self_indicating_type: Optional[str] = None
    indication_type: Optional[str] = None
    is_electronic: Optional[bool] = None
    has_tare_device: Optional[bool] = None
    intended_use: Optional[str] = None


class InstrumentProfileResponse(BaseModel):
    """Response with instrument profile."""
    id: int
    model_id: int
    e: str
    max_capacity: str
    min_capacity: Optional[str]
    is_multi_range: bool
    is_multi_interval: bool
    sub_ranges: Optional[dict]
    self_indicating_type: str
    indication_type: Optional[str]
    is_electronic: bool
    has_tare_device: bool
    intended_use: str
    created_at: Optional[str]
    updated_at: Optional[str]


# ========== Endpoints ==========

@router.post("", response_model=InstrumentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_instrument_profile(
    request: CreateInstrumentProfileRequest,
    db: Session = Depends(get_db)
):
    """
    Create new instrument profile (Stage 1 data capture).
    
    This endpoint saves the instrument parameters collected in Stage 1:
    - Classification parameters (e, Max, Min)
    - Category parameters (self-indicating type, electronic, etc.)
    - Multi-range/interval configuration
    
    Returns the created profile with ID for use in classification.
    """
    try:
        # Validate enum values
        valid_self_indicating = ['self_indicating', 'semi_self_indicating', 'non_self_indicating']
        if request.self_indicating_type not in valid_self_indicating:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"self_indicating_type must be one of: {', '.join(valid_self_indicating)}"
            )
        
        if request.indication_type:
            valid_indication = ['digital', 'analogue']
            if request.indication_type not in valid_indication:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"indication_type must be one of: {', '.join(valid_indication)}"
                )
        
        valid_intended_use = ['general_trade', 'direct_sales', 'price_computing', 'labelling', 'grading']
        if request.intended_use not in valid_intended_use:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"intended_use must be one of: {', '.join(valid_intended_use)}"
            )
        
        # Insert instrument profile
        import json
        
        result = db.execute(
            """
            INSERT INTO instrument_profiles (
                model_id, e, max_capacity, min_capacity,
                is_multi_range, is_multi_interval, sub_ranges,
                self_indicating_type, indication_type,
                is_electronic, has_tare_device, intended_use,
                created_at
            ) VALUES (
                :model_id, :e, :max_cap, :min_cap,
                :is_multi_range, :is_multi_interval, :sub_ranges,
                :self_ind_type, :ind_type,
                :is_electronic, :has_tare, :intended_use,
                :created_at
            ) RETURNING id, created_at
            """,
            {
                "model_id": request.model_id,
                "e": Decimal(request.e),
                "max_cap": Decimal(request.max_capacity),
                "min_cap": Decimal(request.min_capacity) if request.min_capacity else None,
                "is_multi_range": request.is_multi_range,
                "is_multi_interval": request.is_multi_interval,
                "sub_ranges": json.dumps(request.sub_ranges) if request.sub_ranges else None,
                "self_ind_type": request.self_indicating_type,
                "ind_type": request.indication_type,
                "is_electronic": request.is_electronic,
                "has_tare": request.has_tare_device,
                "intended_use": request.intended_use,
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
        
        row = result.fetchone()
        profile_id = row[0]
        created_at = row[1]
        
        logger.info(
            f"Instrument profile created: id={profile_id}, "
            f"e={request.e}, Max={request.max_capacity}, "
            f"electronic={request.is_electronic}"
        )
        
        return InstrumentProfileResponse(
            id=profile_id,
            model_id=request.model_id,
            e=request.e,
            max_capacity=request.max_capacity,
            min_capacity=request.min_capacity,
            is_multi_range=request.is_multi_range,
            is_multi_interval=request.is_multi_interval,
            sub_ranges=request.sub_ranges,
            self_indicating_type=request.self_indicating_type,
            indication_type=request.indication_type,
            is_electronic=request.is_electronic,
            has_tare_device=request.has_tare_device,
            intended_use=request.intended_use,
            created_at=created_at.isoformat() if created_at else None,
            updated_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating instrument profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{profile_id}", response_model=InstrumentProfileResponse)
async def get_instrument_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve instrument profile by ID.
    """
    try:
        result = db.execute(
            """
            SELECT 
                id, model_id, e, max_capacity, min_capacity,
                is_multi_range, is_multi_interval, sub_ranges,
                self_indicating_type, indication_type,
                is_electronic, has_tare_device, intended_use,
                created_at, updated_at
            FROM instrument_profiles
            WHERE id = :id
            """,
            {"id": profile_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument profile {profile_id} not found"
            )
        
        return InstrumentProfileResponse(
            id=result[0],
            model_id=result[1],
            e=str(result[2]),
            max_capacity=str(result[3]),
            min_capacity=str(result[4]) if result[4] else None,
            is_multi_range=result[5],
            is_multi_interval=result[6],
            sub_ranges=result[7],
            self_indicating_type=result[8],
            indication_type=result[9],
            is_electronic=result[10],
            has_tare_device=result[11],
            intended_use=result[12],
            created_at=result[13].isoformat() if result[13] else None,
            updated_at=result[14].isoformat() if result[14] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instrument profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{profile_id}", response_model=InstrumentProfileResponse)
async def update_instrument_profile(
    profile_id: int,
    request: UpdateInstrumentProfileRequest,
    db: Session = Depends(get_db)
):
    """
    Update existing instrument profile.
    
    Only provided fields will be updated (partial update).
    """
    try:
        # Check if profile exists
        existing = db.execute(
            "SELECT id FROM instrument_profiles WHERE id = :id",
            {"id": profile_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument profile {profile_id} not found"
            )
        
        # Build update query dynamically for provided fields
        update_fields = []
        update_values = {"id": profile_id, "updated_at": datetime.utcnow()}
        
        if request.model_id is not None:
            update_fields.append("model_id = :model_id")
            update_values["model_id"] = request.model_id
        
        if request.e is not None:
            update_fields.append("e = :e")
            update_values["e"] = Decimal(request.e)
        
        if request.max_capacity is not None:
            update_fields.append("max_capacity = :max_cap")
            update_values["max_cap"] = Decimal(request.max_capacity)
        
        if request.min_capacity is not None:
            update_fields.append("min_capacity = :min_cap")
            update_values["min_cap"] = Decimal(request.min_capacity)
        
        # ... add other fields similarly
        
        update_fields.append("updated_at = :updated_at")
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = f"""
            UPDATE instrument_profiles
            SET {', '.join(update_fields)}
            WHERE id = :id
        """
        
        db.execute(query, update_values)
        db.commit()
        
        logger.info(f"Instrument profile updated: id={profile_id}")
        
        # Fetch and return updated profile
        return await get_instrument_profile(profile_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating instrument profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("", response_model=List[InstrumentProfileResponse])
async def list_instrument_profiles(
    skip: int = 0,
    limit: int = 100,
    model_id: Optional[int] = None,
    is_electronic: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List instrument profiles with optional filtering.
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - model_id: Filter by model ID
    - is_electronic: Filter by electronic/mechanical
    """
    try:
        # Build WHERE clause dynamically
        where_clauses = []
        query_params = {"skip": skip, "limit": limit}
        
        if model_id is not None:
            where_clauses.append("model_id = :model_id")
            query_params["model_id"] = model_id
        
        if is_electronic is not None:
            where_clauses.append("is_electronic = :is_electronic")
            query_params["is_electronic"] = is_electronic
        
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = f"""
            SELECT 
                id, model_id, e, max_capacity, min_capacity,
                is_multi_range, is_multi_interval, sub_ranges,
                self_indicating_type, indication_type,
                is_electronic, has_tare_device, intended_use,
                created_at, updated_at
            FROM instrument_profiles
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """
        
        results = db.execute(query, query_params).fetchall()
        
        profiles = [
            InstrumentProfileResponse(
                id=row[0],
                model_id=row[1],
                e=str(row[2]),
                max_capacity=str(row[3]),
                min_capacity=str(row[4]) if row[4] else None,
                is_multi_range=row[5],
                is_multi_interval=row[6],
                sub_ranges=row[7],
                self_indicating_type=row[8],
                indication_type=row[9],
                is_electronic=row[10],
                has_tare_device=row[11],
                intended_use=row[12],
                created_at=row[13].isoformat() if row[13] else None,
                updated_at=row[14].isoformat() if row[14] else None
            )
            for row in results
        ]
        
        return profiles
        
    except Exception as e:
        logger.error(f"Error listing instrument profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instrument_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete instrument profile.
    
    WARNING: This will cascade delete all related classifications and test plans.
    """
    try:
        result = db.execute(
            "DELETE FROM instrument_profiles WHERE id = :id RETURNING id",
            {"id": profile_id}
        )
        
        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument profile {profile_id} not found"
            )
        
        db.commit()
        
        logger.warning(f"Instrument profile deleted: id={profile_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting instrument profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
