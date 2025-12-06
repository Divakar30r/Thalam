# Health check endpoints

from fastapi import APIRouter
from shared.models import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="requestor"
    )

@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint"""
    return HealthResponse(
        status="ready",
        service="requestor"
    )