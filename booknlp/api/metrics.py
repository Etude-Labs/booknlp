"""Prometheus metrics configuration for BookNLP API."""

import os
from typing import Optional

from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI, Request, Response


def create_metrics() -> Optional[Instrumentator]:
    """Create and configure Prometheus metrics collector.
    
    Returns:
        Configured Instrumentator instance or None if metrics disabled
    """
    # Check if metrics are enabled (default to enabled)
    metrics_enabled = os.getenv("BOOKNLP_METRICS_ENABLED", "true").lower() == "true"
    
    if not metrics_enabled:
        return None
    
    # Create instrumentator with default metrics
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_group_untemplated=True,
        should_instrument_requests_inprogress=True,
        should_instrument_requests_duration=True,
        excluded_handlers=["/metrics"],
        env_var_name="BOOKNLP_METRICS_ENABLED",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.add(metrics.default())
    
    # Add custom metrics for BookNLP
    from prometheus_client import Counter, Histogram, Gauge
    
    # Job queue metrics
    jobs_submitted_total = Counter(
        "booknlp_jobs_submitted_total",
        "Total number of jobs submitted",
        ["model", "pipeline"]
    )
    
    jobs_completed_total = Counter(
        "booknlp_jobs_completed_total",
        "Total number of jobs completed",
        ["status", "model", "pipeline"]
    )
    
    job_queue_size = Gauge(
        "booknlp_job_queue_size",
        "Current number of jobs in queue"
    )
    
    job_processing_duration = Histogram(
        "booknlp_job_processing_duration_seconds",
        "Time spent processing jobs",
        ["model", "pipeline"],
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0]
    )
    
    # Model metrics
    model_load_time = Histogram(
        "booknlp_model_load_duration_seconds",
        "Time spent loading models",
        ["model"],
        buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
    )
    
    model_loaded = Gauge(
        "booknlp_model_loaded",
        "Whether a model is loaded",
        ["model"]
    )
    
    # Store metrics in app state for access by endpoints
    # These will be used by the job endpoints to update metrics
    
    return instrumentator


def instrument_app(app: FastAPI) -> None:
    """Instrument the FastAPI app with Prometheus metrics.
    
    Args:
        app: FastAPI application instance
    """
    instrumentator = create_metrics()
    
    if instrumentator:
        # Instrument the app
        instrumentator.instrument(app).expose(app)
        
        # Add custom metrics endpoint handler
        @app.get("/metrics", include_in_schema=False)
        async def metrics_endpoint(request: Request) -> Response:
            """Custom metrics endpoint that bypasses auth and rate limiting."""
            # The instrumentator.expose() already handles this
            # This is just for documentation
            pass


# Global instrumentator instance
_instrumentator = create_metrics()


def get_instrumentator() -> Optional[Instrumentator]:
    """Get the global metrics instrumentator.
    
    Returns:
        The Instrumentator instance or None if metrics disabled
    """
    return _instrumentator
