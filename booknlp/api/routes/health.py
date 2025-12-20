"""Health and readiness endpoints."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Response, status, Request

from booknlp.api.schemas.responses import HealthResponse, ReadyResponse
from booknlp.api.rate_limit import rate_limit
from booknlp.api.config import get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns OK if the service is running.",
)
async def health(request: Request) -> HealthResponse:
    """Liveness endpoint for container orchestration.
    
    This endpoint should always return 200 if the service is running.
    It does not check dependencies - use /ready for that.
    """
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness check",
    description="Returns ready status and model availability.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is still loading"},
    },
)
async def ready(request: Request, response: Response) -> ReadyResponse:
    """Readiness endpoint for container orchestration.
    
    Returns 200 when models are loaded, 503 when still loading.
    """
    from booknlp.api.services.nlp_service import get_nlp_service
    
    nlp_service = get_nlp_service()
    settings = get_settings()
    
    if nlp_service.is_ready:
        return ReadyResponse(
            status="ready",
            model_loaded=True,
            default_model=nlp_service.default_model,
            available_models=nlp_service.available_models,
            device=str(nlp_service.device),
            cuda_available=nlp_service.cuda_available,
            cuda_device_name=nlp_service.cuda_device_name,
        )
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(
            status="loading",
            model_loaded=False,
            default_model=nlp_service.default_model,
            available_models=[],
            device=str(nlp_service.device),
            cuda_available=nlp_service.cuda_available,
            cuda_device_name=nlp_service.cuda_device_name,
        )


@router.get(
    "/info",
    summary="Service information",
    description="Returns detailed service information for debugging.",
)
async def info(request: Request) -> dict[str, Any]:
    """Service info endpoint for debugging and monitoring.
    
    Returns detailed information about the service configuration.
    """
    from booknlp.api.services.nlp_service import get_nlp_service
    from booknlp.api.services.job_queue import get_job_queue
    
    nlp_service = get_nlp_service()
    job_queue = get_job_queue()
    settings = get_settings()
    
    # Get queue stats
    queue_stats = await job_queue.get_queue_stats()
    
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        },
        "models": {
            "ready": nlp_service.is_ready,
            "default": nlp_service.default_model,
            "available": nlp_service.available_models,
            "device": str(nlp_service.device),
            "cuda_available": nlp_service.cuda_available,
            "cuda_device": nlp_service.cuda_device_name,
        },
        "queue": queue_stats,
        "config": {
            "max_queue_size": settings.max_queue_size,
            "job_ttl_seconds": settings.job_ttl_seconds,
            "rate_limit_enabled": settings.rate_limit_enabled,
            "metrics_enabled": settings.metrics_enabled,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
