"""FastAPI application factory for BookNLP API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from booknlp.api.routes import analyze, health
from booknlp.api.services.nlp_service import get_nlp_service, initialize_nlp_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown.
    
    Loads models on startup and cleans up on shutdown.
    """
    # Startup: Initialize NLP service (models loaded lazily or on demand)
    initialize_nlp_service()
    
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="BookNLP API",
        description="REST API for BookNLP natural language processing",
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Include routers
    app.include_router(health.router, prefix="/v1")
    app.include_router(analyze.router, prefix="/v1")
    
    return app


# Create app instance for uvicorn
app = create_app()
