"""Health and readiness endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Response, status, Request

from booknlp.api.schemas.responses import HealthResponse, ReadyResponse
from booknlp.api.rate_limit import rate_limit, get_rate_limit

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns OK if the service is running.",
)
@rate_limit("60/minute")  # More lenient for health checks
async def health(request: Request) -> HealthResponse:
    """Liveness endpoint for container orchestration."""
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
@rate_limit("60/minute")  # More lenient for health checks
async def ready(request: Request, response: Response) -> ReadyResponse:
    """Readiness endpoint for container orchestration.
    
    Returns 200 when models are loaded, 503 when still loading.
    """
    # Import here to avoid circular imports and allow lazy loading
    from booknlp.api.services.nlp_service import get_nlp_service
    
    nlp_service = get_nlp_service()
    
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
