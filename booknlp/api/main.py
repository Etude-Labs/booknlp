"""FastAPI application factory for BookNLP API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter

from booknlp.api.routes import analyze, health, jobs
from booknlp.api.services.nlp_service import get_nlp_service, initialize_nlp_service
from booknlp.api.services.job_queue import initialize_job_queue
from booknlp.api.services.async_processor import get_async_processor
from booknlp.api.rate_limit import limiter, get_rate_limit
from booknlp.api.metrics import instrument_app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown.
    
    Loads models on startup, initializes job queue, and cleans up on shutdown.
    """
    # Startup: Initialize NLP service (models loaded lazily or on demand)
    initialize_nlp_service()
    
    # Initialize and start the job queue
    job_queue = await initialize_job_queue(
        processor=get_async_processor().process,
        max_queue_size=10,
        job_ttl_seconds=3600,
    )
    
    # Load models to ensure service is ready
    nlp_service = get_nlp_service()
    nlp_service.load_models()
    
    yield
    
    # Shutdown: Stop the job queue worker
    await job_queue.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    # Configure rate limiting
    rate_limit = get_rate_limit()
    
    # Create app with rate limiting state if enabled
    if limiter:
        app = FastAPI(
            title="BookNLP API",
            description="REST API for BookNLP natural language processing",
            version="0.2.0",
            lifespan=lifespan,
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            state=limiter.state,
        )
    else:
        app = FastAPI(
            title="BookNLP API",
            description="REST API for BookNLP natural language processing",
            version="0.2.0",
            lifespan=lifespan,
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(analyze.router, prefix="/v1")
    app.include_router(jobs.router, prefix="/v1")
    
    # Instrument with Prometheus metrics
    instrument_app(app)
    
    return app


# Create app instance for uvicorn
app = create_app()
