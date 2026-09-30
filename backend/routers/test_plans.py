"""
Test plan assembly API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
import logging
import json

from database import get_db
from models.rulepacks import load_rulepack
from models.instrument import InstrumentProfile, ClassResult
from models.test_plan import TestPlan, ResolvedTest
from services.test_plan_engine import assemble_test_plan, get_test_summary
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ========== Request/Response Models ==========

from pydantic import BaseModel, Field


class AssembleTestPlanRequest(BaseModel):
    """Request to assemble test plan."""
    instrument_profile_id: int
    class_determination_id: int
    rulepack_version: str = Field(default="R76-1:2006")


class AssembleTestPlanResponse(BaseModel):
    """Response with assembled test plan."""
    test_plan_id: int
    test_job_id: int
    tests: list[ResolvedTest]
    class_: str = Field(alias="class")
    total_count: int
    summary: dict
    
    class Config:
        populate_by_name = True


# ========== Endpoints ==========

@router.post("/assemble", response_model=AssembleTestPlanResponse, status_code=status.HTTP_201_CREATED)
async def assemble_test_plan_endpoint(
    request: AssembleTestPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Assemble test plan from instrument profile and confirmed classification.
    
    This endpoint implements Stage 2 test routing:
    1. Load instrument profile and classification
    2. Evaluate test applicability conditions
    3. Resolve variants (discrimination, tilting)
    4. Sort tests by sequence
    5. Persist test plan to database
    
    **No LLM calls** - purely deterministic rules engine.
    
    Returns complete test plan with resolved variants.
    """
    try:
        # Load instrument profile
        instrument_row = db.execute(
            """
            SELECT 
                id, model_id, e, max_capacity, min_capacity,
                is_multi_range, is_multi_interval, sub_ranges,
                self_indicating_type, indication_type,
                is_electronic, has_tare_device, intended_use
            FROM instrument_profiles
            WHERE id = :id
            """,
            {"id": request.instrument_profile_id}
        ).fetchone()
        
        if not instrument_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument profile {request.instrument_profile_id} not found"
            )
        
        # Convert to InstrumentProfile model
        instrument = InstrumentProfile(
            id=instrument_row[0],
            model_id=instrument_row[1],
            e=instrument_row[2],
            max_capacity=instrument_row[3],
            min_capacity=instrument_row[4],
            is_multi_range=instrument_row[5],
            is_multi_interval=instrument_row[6],
            sub_ranges=instrument_row[7],  # JSONB
            self_indicating_type=instrument_row[8],
            indication_type=instrument_row[9],
            is_electronic=instrument_row[10],
            has_tare_device=instrument_row[11],
            intended_use=instrument_row[12]
        )
        
        # Load classification determination
        class_row = db.execute(
            """
            SELECT computed_n, status, determined_class
            FROM class_determinations
            WHERE id = :id
            """,
            {"id": request.class_determination_id}
        ).fetchone()
        
        if not class_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Classification determination {request.class_determination_id} not found"
            )
        
        # Verify classification is DETERMINED
        if class_row[1] != "DETERMINED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assemble test plan for {class_row[1]} classification. Must be DETERMINED."
            )
        
        # Convert to ClassResult
        class_result = ClassResult(
            status=class_row[1],
            computed_n=class_row[0],
            class_=class_row[2]
        )
        
        # Load rulepack
        _, test_applicability_rulepack = load_rulepack(
            request.rulepack_version,
            settings.rulepack_dir
        )
        
        # Assemble test plan (pure function - deterministic)
        test_plan = assemble_test_plan(
            instrument,
            class_result,
            test_applicability_rulepack
        )
        
        # Get test_job_id (create if not exists)
        # For now, create a new test job
        test_job_result = db.execute(
            """
            INSERT INTO test_jobs (instrument_profile_id, status, created_at)
            VALUES (:profile_id, 'in_progress', :created_at)
            RETURNING id
            """,
            {
                "profile_id": request.instrument_profile_id,
                "created_at": datetime.utcnow()
            }
        )
        test_job_id = test_job_result.fetchone()[0]
        
        # Persist test plan
        tests_json = json.dumps([t.dict() for t in test_plan.tests])
        
        test_plan_result = db.execute(
            """
            INSERT INTO test_plans (
                test_job_id, rulepack_version, tests,
                class_, total_count, created_at
            ) VALUES (
                :job_id, :version, :tests,
                :class, :count, :created_at
            ) RETURNING id
            """,
            {
                "job_id": test_job_id,
                "version": request.rulepack_version,
                "tests": tests_json,
                "class": test_plan.class_,
                "count": test_plan.total_count,
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
        
        test_plan_id = test_plan_result.fetchone()[0]
        
        # Generate summary
        summary = get_test_summary(test_plan)
        
        logger.info(
            f"Test plan assembled: id={test_plan_id}, "
            f"job={test_job_id}, "
            f"instrument={request.instrument_profile_id}, "
            f"class={test_plan.class_}, "
            f"tests={test_plan.total_count}"
        )
        
        return AssembleTestPlanResponse(
            test_plan_id=test_plan_id,
            test_job_id=test_job_id,
            tests=test_plan.tests,
            class_=test_plan.class_,
            total_count=test_plan.total_count,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assembling test plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during test plan assembly"
        )


@router.get("/{test_job_id}", response_model=dict)
async def get_test_plan(
    test_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve existing test plan for a test job.
    """
    try:
        result = db.execute(
            """
            SELECT 
                id, rulepack_version, tests, class_, total_count, created_at
            FROM test_plans
            WHERE test_job_id = :job_id
            """,
            {"job_id": test_job_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan for job {test_job_id} not found"
            )
        
        return {
            "id": result[0],
            "test_job_id": test_job_id,
            "rulepack_version": result[1],
            "tests": result[2],  # JSONB
            "class": result[3],
            "total_count": result[4],
            "created_at": result[5].isoformat() if result[5] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{test_job_id}/summary", response_model=dict)
async def get_test_plan_summary(
    test_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for a test plan.
    
    Returns:
    - Total test count
    - Short vs time-spanning breakdown
    - Performance vs environmental vs checklist breakdown
    - First and last test names
    """
    try:
        result = db.execute(
            """
            SELECT tests, class_
            FROM test_plans
            WHERE test_job_id = :job_id
            """,
            {"job_id": test_job_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan for job {test_job_id} not found"
            )
        
        # Reconstruct TestPlan object
        tests_data = result[0]  # JSONB
        tests = [ResolvedTest(**t) for t in tests_data]
        test_plan = TestPlan(tests=tests, class_=result[1])
        
        # Generate summary
        summary = get_test_summary(test_plan)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test plan summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
