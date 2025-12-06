from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from ...core.config import settings
from ...services import ExternalAPIService
from ..dependencies import get_external_api_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]
    environment: Dict[str, Any]

class ServiceHealthResponse(BaseModel):
    service_name: str
    status: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

@router.get("/", response_model=HealthResponse)
async def health_check(
    external_api_service: ExternalAPIService = Depends(get_external_api_service)
):
    """
    Comprehensive health check for the processor service
    
    Returns:
        HealthResponse with overall system health status
    """
    try:
        logger.info("Performing health check")
        
        # Check external APIs
        external_api_health = await external_api_service.health_check_external_apis()
        
        # Determine overall status
        all_healthy = all(external_api_health.values())
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Build response
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",  # You might want to get this from a version file
            services={
                "external_apis": external_api_health,
                "grpc_server": {
                    "status": "healthy",
                    "host": settings.grpc_server_host,
                    "port": settings.grpc_server_port
                },
                "fastapi_server": {
                    "status": "healthy",
                    "host": settings.fastapi_host,
                    "port": settings.fastapi_port
                }
            },
            environment={
                "api_base_url": settings.api_base_url,
                "order_expiry_minutes": settings.order_expiry_minutes,
                "find_max_sellers": settings.find_max_sellers,
                "log_level": settings.log_level
            }
        )
        
        logger.info(f"Health check completed with status: {overall_status}")
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )

@router.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns:
        Simple OK response if service is ready to accept traffic
    """
    try:
        # Perform basic readiness checks
        # - Check if configuration is loaded
        # - Check if required services are initialized
        
        if not settings.api_base_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration not properly loaded"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns:
        Simple OK response if service is alive
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}