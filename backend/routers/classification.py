"""
Classification API endpoints for OIML R 76 accuracy class determination.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal, InvalidOperation
from typing import Optional
from datetime import datetime
import logging

from database import get_db
from models.rulepacks import load_rulepack
from models.instrument import ClassResult, ClassDetermination, InstrumentProfile
from services.classification_engine import determine_class, suggest_min_capacity
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ========== Request/Response Models ==========

from pydantic import BaseModel, Field


class DetermineClassRequest(BaseModel):
    """Request to determine accuracy class."""
    e: str = Field(..., description="Verification scale interval (grams)", examples=["0.001"])
    max_capacity: str = Field(..., description="Maximum capacity (grams)", examples=["150"])
    rulepack_version: str = Field(default="R76-1:2006", description="Rulepack version to use")


class DetermineClassResponse(ClassResult):
    """Response with classification result."""
    suggested_min_capacity: Optional[str] = Field(None, description="Suggested Min (grams)")


class ConfirmClassificationRequest(BaseModel):
    """Request to confirm a classification."""
    instrument_profile_id: int
    e: str
    max_capacity: str
    rulepack_version: str
    status: str
    determined_class: Optional[str] = None
    computed_n: str
    override_reason: Optional[str] = None
    confirmed_by: int = Field(..., description="User ID confirming classification")


class ConfirmClassificationResponse(BaseModel):
    """Response with confirmed classification ID."""
    class_determination_id: int
    message: str


# ========== Endpoints ==========

@router.post("/determine", response_model=DetermineClassResponse, status_code=status.HTTP_200_OK)
async def determine_classification(
    request: DetermineClassRequest,
    db: Session = Depends(get_db)
):
    """
    Determine accuracy class from e and Max capacity.
    
    This endpoint implements Stage 1.5 routing logic:
    1. Calculate n = Max / e (all values in grams)
    2. Match against OIML R 76-1 Table 3 class bands
    3. Return DETERMINED, AMBIGUOUS, or INVALID status
    
    **No LLM calls** - purely deterministic calculation.
    
    **Example**: e=0.001g, Max=150g → Class I (n=150,000)
    """
    try:
        # Convert string to Decimal
        try:
            e = Decimal(request.e)
        except (ValueError, InvalidOperation) as ex:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid e format: {str(ex)}"
            )
        
        try:
            max_cap = Decimal(request.max_capacity)
        except (ValueError, InvalidOperation) as ex:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid max_capacity format: {str(ex)}"
            )
        
        # Validate inputs
        if e <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification scale interval (e) must be positive"
            )
        if max_cap <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum capacity (Max) must be positive"
            )
        
        # Load rulepack
        classification_rulepack, _ = load_rulepack(
            request.rulepack_version,
            settings.rulepack_dir
        )
        
        # Determine class (pure function - deterministic)
        result = determine_class(e, max_cap, classification_rulepack)
        
        # Format computed_n to avoid scientific notation
        formatted_n = format(result.computed_n.normalize(), 'f')
        
        # Add suggested min capacity if class determined
        suggested_min = None
        if result.status == "DETERMINED" and result.class_:
            min_cap = suggest_min_capacity(e, result.class_, classification_rulepack)
            suggested_min = str(min_cap)
        
        logger.info(
            f"Classification: e={e}g, Max={max_cap}g, "
            f"n={formatted_n}, status={result.status}, "
            f"class={result.class_}"
        )
        
        return DetermineClassResponse(
            status=result.status,
            computed_n=formatted_n,
            class_=result.class_,
            candidates=result.candidates,
            reason=result.reason,
            suggested_min_capacity=suggested_min
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid input for classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        logger.error(f"Rulepack not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rulepack version '{request.rulepack_version}' not found"
        )
    except Exception as e:
        logger.error(f"Unexpected error in classification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during classification"
        )


@router.post("/confirm", response_model=ConfirmClassificationResponse, status_code=status.HTTP_201_CREATED)
async def confirm_classification(
    request: ConfirmClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm a classification determination with human validation.
    
    This endpoint persists the classification result to the database
    with audit trail information:
    - Who confirmed it (user ID)
    - When it was confirmed (timestamp)
    - Why it was overridden (if AMBIGUOUS)
    
    **AMBIGUOUS classifications require override_reason**.
    
    Returns the class_determination_id for use in test plan assembly.
    """
    try:
        # Validate AMBIGUOUS requires override_reason
        if request.status == "AMBIGUOUS" and not request.override_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="override_reason is required for AMBIGUOUS classifications"
            )
        
        # Check instrument profile exists
        # TODO: Query instrument_profiles table to verify ID exists
        
        # Check for existing determination (UNIQUE constraint)
        existing = db.execute(
            """
            SELECT id FROM class_determinations 
            WHERE instrument_profile_id = :profile_id 
            AND rulepack_version = :version
            """,
            {
                "profile_id": request.instrument_profile_id,
                "version": request.rulepack_version
            }
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Classification already exists for this instrument with rulepack {request.rulepack_version}"
            )
        
        # Insert classification determination
        result = db.execute(
            """
            INSERT INTO class_determinations (
                instrument_profile_id, rulepack_version, computed_n,
                status, determined_class, override_reason,
                confirmed_by, confirmed_at
            ) VALUES (
                :profile_id, :version, :computed_n,
                :status, :class, :reason,
                :confirmed_by, :confirmed_at
            ) RETURNING id
            """,
            {
                "profile_id": request.instrument_profile_id,
                "version": request.rulepack_version,
                "computed_n": Decimal(request.computed_n),
                "status": request.status,
                "class": request.determined_class,
                "reason": request.override_reason,
                "confirmed_by": request.confirmed_by,
                "confirmed_at": datetime.utcnow()
            }
        )
        db.commit()
        
        class_determination_id = result.fetchone()[0]
        
        # TODO: Log to audit trail (integrate with existing audit system)
        logger.info(
            f"Classification confirmed: id={class_determination_id}, "
            f"instrument={request.instrument_profile_id}, "
            f"class={request.determined_class}, "
            f"status={request.status}, "
            f"by_user={request.confirmed_by}"
        )
        
        return ConfirmClassificationResponse(
            class_determination_id=class_determination_id,
            message="Classification confirmed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming classification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during classification confirmation"
        )


@router.get("/suggest-min/{e}/{accuracy_class}", response_model=dict)
async def get_suggested_min_capacity(
    e: str,
    accuracy_class: str,
    rulepack_version: str = "R76-1:2006"
):
    """
    Get suggested minimum capacity for a given e and class.
    
    Helper endpoint for Stage 1 form to show suggested Min value.
    Technician can override this suggestion.
    
    **Formula**: Min = factor × e (factor from Table 3, all values in grams)
    - Class I: Min = 100 × e
    - Class II: Min = 20 × e or 50 × e (depends on range)
    - Class III: Min = 20 × e
    - Class IIII: Min = 10 × e
    """
    try:
        e_decimal = Decimal(e)
        
        if e_decimal <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="e must be positive"
            )
        
        if accuracy_class not in ["I", "II", "III", "IIII"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="accuracy_class must be one of: I, II, III, IIII"
            )
        
        # Load rulepack
        classification_rulepack, _ = load_rulepack(
            rulepack_version,
            settings.rulepack_dir
        )
        
        # Calculate suggested min
        min_cap = suggest_min_capacity(e_decimal, accuracy_class, classification_rulepack)
        
        return {
            "e": str(e_decimal),
            "accuracy_class": accuracy_class,
            "suggested_min_capacity": str(min_cap),
            "unit": "g",
            "note": "Technician can override this value if needed"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating suggested min: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/history/{instrument_profile_id}", response_model=list)
async def get_classification_history(
    instrument_profile_id: int,
    db: Session = Depends(get_db)
):
    """
    Get classification history for an instrument profile.
    
    Returns all classification determinations for this instrument,
    ordered by most recent first.
    """
    try:
        results = db.execute(
            """
            SELECT 
                id, rulepack_version, computed_n, status,
                determined_class, override_reason,
                confirmed_by, confirmed_at, created_at
            FROM class_determinations
            WHERE instrument_profile_id = :profile_id
            ORDER BY created_at DESC
            """,
            {"profile_id": instrument_profile_id}
        ).fetchall()
        
        history = [
            {
                "id": row[0],
                "rulepack_version": row[1],
                "computed_n": str(row[2]),
                "status": row[3],
                "determined_class": row[4],
                "override_reason": row[5],
                "confirmed_by": row[6],
                "confirmed_at": row[7].isoformat() if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None
            }
            for row in results
        ]
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching classification history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
