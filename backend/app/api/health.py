"""
API router for health check endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import HealthCheck, ErrorResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheck,
    responses={
        500: {"model": ErrorResponse, "description": "Service unhealthy"}
    }
)
async def health_check() -> HealthCheck:
    """
    Health check endpoint to verify service status.
    
    Returns:
        Health check response with service status
    """
    try:
        # Basic health check - could be extended to check:
        # - Database connectivity
        # - Vector store status
        # - External API availability
        # - Disk space
        # - Memory usage
        
        logger.info("Health check requested")
        
        return HealthCheck(
            status="healthy",
            version=settings.VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unhealthy: {str(e)}"
        )


@router.get(
    "/health/detailed",
    responses={
        200: {"description": "Detailed health information"},
        500: {"model": ErrorResponse, "description": "Service unhealthy"}
    }
)
async def detailed_health_check():
    """
    Detailed health check with component status.
    
    Returns:
        Detailed health information
    """
    try:
        logger.info("Detailed health check requested")
        
        # Check various components
        health_info = {
            "status": "healthy",
            "version": settings.VERSION,
            "components": {
                "api": "healthy",
                "vector_store": "healthy",
                "file_system": "healthy"
            },
            "configuration": {
                "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE
            }
        }
        
        # TODO: Add actual component health checks
        # - Test Chroma connection
        # - Check upload directory accessibility
        # - Verify OpenAI API key validity
        
        return health_info
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service unhealthy: {str(e)}"
        )

