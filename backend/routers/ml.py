"""
ML endpoints for demo drift risk model.
DEMO only - hardcoded weights, not learned, never decides anything regulatory.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

from services.ml.drift_model import drift_risk, MODEL_VERSION


router = APIRouter(prefix="/ml", tags=["ml"])


class BaselineReading(BaseModel):
    """Baseline environmental reading."""
    temp: float = Field(..., description="Temperature in °C")
    rh: float = Field(..., description="Relative humidity in %")


class DriftReading(BaseModel):
    """Environmental reading with load information."""
    temp: float = Field(..., description="Temperature in °C")
    rh: float = Field(..., description="Relative humidity in %")
    load_pct: float = Field(50.0, ge=0, le=100, description="Load as % of capacity")
    time_spanning: float = Field(1.0, ge=0, le=1, description="1 for time-spanning, 0 for short")


class DriftRiskRequest(BaseModel):
    """Request for drift risk prediction."""
    baseline: BaselineReading
    readings: List[DriftReading]


class DriftRiskResponse(BaseModel):
    """Response with drift risk scores."""
    risks: List[float]
    model_version: str
    demo: bool = True
    draft: bool = True


@router.post("/drift-risk", response_model=DriftRiskResponse)
async def predict_drift_risk(request: DriftRiskRequest) -> DriftRiskResponse:
    """
    Predict drift risk for environmental readings.
    
    **DEMO MODEL**: Uses hardcoded weights, not learned from data.
    This model exists only to demonstrate ML integration patterns.
    It does NOT make regulatory decisions.
    
    Args:
        request: Baseline and readings with environmental conditions
    
    Returns:
        Risk scores for each reading (0-1 scale)
    """
    try:
        risks = []
        
        for reading in request.readings:
            delta_temp = reading.temp - request.baseline.temp
            delta_rh = reading.rh - request.baseline.rh
            
            risk = drift_risk(
                delta_temp=delta_temp,
                delta_rh=delta_rh,
                load_pct=reading.load_pct,
                time_spanning=reading.time_spanning
            )
            
            risks.append(risk)
        
        return DriftRiskResponse(
            risks=risks,
            model_version=MODEL_VERSION,
            demo=True,
            draft=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute drift risk: {str(e)}"
        )
