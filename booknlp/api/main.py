"""FastAPI application factory for BookNLP API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from booknlp.api.config import get_settings
from booknlp.api.logging_config import configure_logging, get_logger
from booknlp.api.middleware import setup_middleware
from booknlp.api.routes import analyze, health, jobs
from booknlp.api.services.nlp_service import get_nlp_service, initialize_nlp_service
from booknlp.api.services.job_queue import initialize_job_queue
from booknlp.api.services.async_processor import get_async_processor
from booknlp.api.rate_limit import limiter
from booknlp.api.metrics import instrument_app

# Configure logging on module load
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown.
    
    Loads models on startup, initializes job queue, and cleans up on shutdown.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version} ({settings.environment.value})")
    
    # Startup: Initialize NLP service (models loaded lazily or on demand)
    initialize_nlp_service()
    
    # Initialize and start the job queue
    job_queue = await initialize_job_queue(
        processor=get_async_processor().process,
        max_queue_size=settings.max_queue_size,
        job_ttl_seconds=settings.job_ttl_seconds,
    )
    
    # Load models to ensure service is ready
    nlp_service = get_nlp_service()
    nlp_service.load_models()
    logger.info("Models loaded, service ready")
    
    yield
    
    # Shutdown: Stop the job queue worker with grace period
    logger.info("Shutting down...")
    await job_queue.stop(grace_period=settings.shutdown_grace_period)
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    
    # Common FastAPI configuration
    common_config = {
        "title": settings.app_name,
        "description": "REST API for BookNLP natural language processing",
        "version": settings.app_version,
        "lifespan": lifespan,
        "docs_url": "/docs" if not settings.is_production else None,
        "redoc_url": "/redoc" if not settings.is_production else None,
        "openapi_url": "/openapi.json" if not settings.is_production else None,
    }
    
    # Create app with rate limiting state if enabled
    if limiter:
        common_config["state"] = limiter.state
        app = FastAPI(**common_config)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    else:
        app = FastAPI(**common_config)
    
    # Add custom middleware (request ID, logging, security headers)
    setup_middleware(app)
    
    # Add CORS middleware with configurable origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Include routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(analyze.router, prefix="/v1")
    app.include_router(jobs.router, prefix="/v1")
    
    # Instrument with Prometheus metrics
    if settings.metrics_enabled:
        instrument_app(app)
    
    return app


# Create app instance for uvicorn
app = create_app()
