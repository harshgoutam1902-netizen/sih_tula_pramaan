"""
RAG (Retrieval Augmented Generation) endpoints for clause retrieval.
Advisory-only, draft content.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from services.rag.retriever import retrieve


router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    """Request for clause retrieval."""
    query: str = Field(..., min_length=1, description="Natural language query")
    k: int = Field(3, ge=1, le=10, description="Number of results to return")


class ClauseResult(BaseModel):
    """Retrieved clause with relevance score."""
    id: str
    source: str
    text: str
    score: float


class RAGQueryResponse(BaseModel):
    """Response with retrieved clauses."""
    results: List[ClauseResult]
    advisory_only: bool = True
    draft: bool = True


class ClassExplanationResponse(BaseModel):
    """Explanation of an accuracy class."""
    accuracy_class: str
    explanation: str
    relevant_clauses: List[ClauseResult]
    advisory_only: bool = True
    draft: bool = True


# Class explanations (paraphrased)
CLASS_EXPLANATIONS = {
    "I": "Class I instruments are high-precision balances used in laboratory settings. They require e ≥ 0.001 grams and n ≥ 50,000 verification intervals.",
    "II": "Class II instruments are precision weighing devices used in trade. They have two specification bands: e between 0.001-0.05 g with n between 100-100,000, or e ≥ 0.1 g with n between 5,000-100,000.",
    "III": "Class III instruments are the most common commercial weighing devices. They have two bands: e between 0.1-2 g with n between 100-10,000, or e ≥ 5 g with n between 500-10,000.",
    "IIII": "Class IIII instruments are rough industrial weighing devices. They require e ≥ 5 grams with n between 100-1,000 verification intervals.",
}


@router.post("/query", response_model=RAGQueryResponse)
async def query_clauses(request: RAGQueryRequest) -> RAGQueryResponse:
    """
    Retrieve relevant clauses for a natural language query.
    
    **Advisory only**: Results are draft paraphrases, not official text.
    Consult OIML R76-1:2006 for certification purposes.
    """
    try:
        results = retrieve(request.query, k=request.k)
        
        return RAGQueryResponse(
            results=[
                ClauseResult(
                    id=r['id'],
                    source=r['source'],
                    text=r['text'],
                    score=r['score']
                )
                for r in results
            ],
            advisory_only=True,
            draft=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve clauses: {str(e)}"
        )


@router.get("/explain-class/{accuracy_class}", response_model=ClassExplanationResponse)
async def explain_class(
    accuracy_class: str,
    k: int = Query(3, ge=1, le=10, description="Number of clauses to retrieve")
) -> ClassExplanationResponse:
    """
    Get explanation and relevant clauses for an accuracy class.
    
    **Advisory only**: Content is draft paraphrases, not official text.
    
    Args:
        accuracy_class: One of I, II, III, IIII
        k: Number of relevant clauses to retrieve
    """
    # Normalize class name
    cls = accuracy_class.upper()
    
    if cls not in CLASS_EXPLANATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid accuracy class. Must be one of: I, II, III, IIII"
        )
    
    # Retrieve relevant clauses for this class
    query = f"accuracy class {cls} verification scale interval requirements"
    results = retrieve(query, k=k)
    
    return ClassExplanationResponse(
        accuracy_class=cls,
        explanation=CLASS_EXPLANATIONS[cls],
        relevant_clauses=[
            ClauseResult(
                id=r['id'],
                source=r['source'],
                text=r['text'],
                score=r['score']
            )
            for r in results
        ],
        advisory_only=True,
        draft=True
    )
