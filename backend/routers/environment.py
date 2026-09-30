"""
Environment session and readings API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Optional
import logging

from database import get_db
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ========== Request/Response Models ==========

from pydantic import BaseModel, Field


class CreateEnvironmentSessionRequest(BaseModel):
    """Request to create environment session."""
    test_job_id: int
    start_temp: str = Field(..., description="Temperature (°C)", examples=["23.2"])
    start_rel_h: str = Field(..., description="Relative humidity (%)", examples=["52"])
    start_time: str = Field(..., description="ISO timestamp", examples=["2026-09-28T09:30:00Z"])
    start_bar_pres: str = Field(..., description="Barometric pressure (hPa)", examples=["1013.2"])


class CreateEnvironmentSessionResponse(BaseModel):
    """Response with created session ID."""
    environment_session_id: int
    message: str


class OverrideEnvironmentReadingRequest(BaseModel):
    """Request to override environment reading."""
    test_run_id: int
    checkpoint: str = Field(..., description="start | max | end")
    temp: str
    rel_h: str
    time: str
    bar_pres: str


class OverrideEnvironmentReadingResponse(BaseModel):
    """Response with updated reading."""
    environment_reading_id: int
    source: str
    message: str


class EnvironmentReadingResponse(BaseModel):
    """Environment reading data."""
    id: int
    test_run_id: int
    checkpoint: str
    temp: str
    rel_h: str
    time: str
    bar_pres: str
    source: str
    created_at: str
    updated_at: Optional[str]


# ========== Endpoints ==========

@router.post("/session", response_model=CreateEnvironmentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_environment_session(
    request: CreateEnvironmentSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Create environment session for a test job (Stage 3).
    
    Captures session-start environment conditions:
    - Temperature
    - Relative humidity
    - Time
    - Barometric pressure
    
    These values will auto-propagate to all tests' "At start" fields.
    """
    try:
        # Check if session already exists
        existing = db.execute(
            """
            SELECT id FROM environment_sessions
            WHERE test_job_id = :job_id
            """,
            {"job_id": request.test_job_id}
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment session already exists for test job {request.test_job_id}"
            )
        
        # Insert session
        result = db.execute(
            """
            INSERT INTO environment_sessions (
                test_job_id, start_temp, start_rel_h,
                start_time, start_bar_pres, created_at
            ) VALUES (
                :job_id, :temp, :rel_h,
                :time, :bar_pres, :created_at
            ) RETURNING id
            """,
            {
                "job_id": request.test_job_id,
                "temp": Decimal(request.start_temp),
                "rel_h": Decimal(request.start_rel_h),
                "time": datetime.fromisoformat(request.start_time.replace('Z', '+00:00')),
                "bar_pres": Decimal(request.start_bar_pres),
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
        
        session_id = result.fetchone()[0]
        
        logger.info(
            f"Environment session created: id={session_id}, "
            f"job={request.test_job_id}, "
            f"temp={request.start_temp}°C, "
            f"humidity={request.start_rel_h}%"
        )
        
        return CreateEnvironmentSessionResponse(
            environment_session_id=session_id,
            message="Environment session created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating environment session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/session/{test_job_id}", response_model=dict)
async def get_environment_session(
    test_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve environment session for a test job.
    """
    try:
        result = db.execute(
            """
            SELECT 
                id, start_temp, start_rel_h, start_time,
                start_bar_pres, created_at
            FROM environment_sessions
            WHERE test_job_id = :job_id
            """,
            {"job_id": test_job_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment session for job {test_job_id} not found"
            )
        
        return {
            "id": result[0],
            "test_job_id": test_job_id,
            "start_temp": str(result[1]),
            "start_rel_h": str(result[2]),
            "start_time": result[3].isoformat() if result[3] else None,
            "start_bar_pres": str(result[4]),
            "created_at": result[5].isoformat() if result[5] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching environment session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/reading/override", response_model=OverrideEnvironmentReadingResponse, status_code=status.HTTP_200_OK)
async def override_environment_reading(
    request: OverrideEnvironmentReadingRequest,
    db: Session = Depends(get_db)
):
    """
    Override environment reading for a specific test checkpoint.
    
    Use this when conditions change during long tests (span stability,
    damp heat, endurance).
    
    Creates or updates reading with source = "manual_override".
    """
    try:
        # Validate checkpoint
        if request.checkpoint not in ["start", "max", "end"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="checkpoint must be one of: start, max, end"
            )
        
        # Check if reading exists
        existing = db.execute(
            """
            SELECT id FROM environment_readings
            WHERE test_run_id = :test_run_id AND checkpoint = :checkpoint
            """,
            {
                "test_run_id": request.test_run_id,
                "checkpoint": request.checkpoint
            }
        ).fetchone()
        
        if existing:
            # Update existing reading
            db.execute(
                """
                UPDATE environment_readings
                SET temp = :temp,
                    rel_h = :rel_h,
                    time = :time,
                    bar_pres = :bar_pres,
                    source = 'manual_override',
                    updated_at = :updated_at
                WHERE id = :id
                """,
                {
                    "id": existing[0],
                    "temp": Decimal(request.temp),
                    "rel_h": Decimal(request.rel_h),
                    "time": datetime.fromisoformat(request.time.replace('Z', '+00:00')),
                    "bar_pres": Decimal(request.bar_pres),
                    "updated_at": datetime.utcnow()
                }
            )
            reading_id = existing[0]
            message = "Environment reading updated"
        else:
            # Create new reading
            result = db.execute(
                """
                INSERT INTO environment_readings (
                    test_run_id, checkpoint, temp, rel_h,
                    time, bar_pres, source, created_at
                ) VALUES (
                    :test_run_id, :checkpoint, :temp, :rel_h,
                    :time, :bar_pres, 'manual_override', :created_at
                ) RETURNING id
                """,
                {
                    "test_run_id": request.test_run_id,
                    "checkpoint": request.checkpoint,
                    "temp": Decimal(request.temp),
                    "rel_h": Decimal(request.rel_h),
                    "time": datetime.fromisoformat(request.time.replace('Z', '+00:00')),
                    "bar_pres": Decimal(request.bar_pres),
                    "created_at": datetime.utcnow()
                }
            )
            reading_id = result.fetchone()[0]
            message = "Environment reading created"
        
        db.commit()
        
        logger.info(
            f"Environment reading override: id={reading_id}, "
            f"test_run={request.test_run_id}, "
            f"checkpoint={request.checkpoint}"
        )
        
        return OverrideEnvironmentReadingResponse(
            environment_reading_id=reading_id,
            source="manual_override",
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error overriding environment reading: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/readings/{test_run_id}", response_model=list[EnvironmentReadingResponse])
async def get_environment_readings(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all environment readings for a test run.
    
    Returns readings for start, max, and end checkpoints (if exist).
    """
    try:
        results = db.execute(
            """
            SELECT 
                id, test_run_id, checkpoint, temp, rel_h,
                time, bar_pres, source, created_at, updated_at
            FROM environment_readings
            WHERE test_run_id = :test_run_id
            ORDER BY 
                CASE checkpoint
                    WHEN 'start' THEN 1
                    WHEN 'max' THEN 2
                    WHEN 'end' THEN 3
                END
            """,
            {"test_run_id": test_run_id}
        ).fetchall()
        
        readings = [
            EnvironmentReadingResponse(
                id=row[0],
                test_run_id=row[1],
                checkpoint=row[2],
                temp=str(row[3]),
                rel_h=str(row[4]),
                time=row[5].isoformat() if row[5] else "",
                bar_pres=str(row[6]),
                source=row[7],
                created_at=row[8].isoformat() if row[8] else "",
                updated_at=row[9].isoformat() if row[9] else None
            )
            for row in results
        ]
        
        return readings
        
    except Exception as e:
        logger.error(f"Error fetching environment readings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/summary/{test_job_id}", response_model=dict)
async def get_environment_summary(
    test_job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get consolidated environment summary for final report.
    
    Aggregates all per-test readings to show overall conditions
    during testing (min/max/avg for each parameter).
    
    **Read-only** - this is a rollup, not a data entry point.
    """
    try:
        # Get all readings for this test job
        results = db.execute(
            """
            SELECT 
                er.temp, er.rel_h, er.bar_pres
            FROM environment_readings er
            JOIN test_runs tr ON er.test_run_id = tr.id
            JOIN test_jobs tj ON tr.test_job_id = tj.id
            WHERE tj.id = :job_id
            """,
            {"job_id": test_job_id}
        ).fetchall()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No environment readings found for test job {test_job_id}"
            )
        
        # Calculate statistics
        temps = [float(row[0]) for row in results]
        humidities = [float(row[1]) for row in results]
        pressures = [float(row[2]) for row in results]
        
        return {
            "test_job_id": test_job_id,
            "reading_count": len(results),
            "temperature": {
                "min": min(temps),
                "max": max(temps),
                "avg": sum(temps) / len(temps),
                "unit": "°C"
            },
            "relative_humidity": {
                "min": min(humidities),
                "max": max(humidities),
                "avg": sum(humidities) / len(humidities),
                "unit": "%"
            },
            "barometric_pressure": {
                "min": min(pressures),
                "max": max(pressures),
                "avg": sum(pressures) / len(pressures),
                "unit": "hPa"
            },
            "note": "Consolidated from per-test records"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating environment summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
