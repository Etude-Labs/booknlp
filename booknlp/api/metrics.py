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
    
    # Note: Custom BookNLP metrics will be added in future iteration
    # - Job queue metrics (jobs_submitted_total, job_queue_size)
    # - Model metrics (model_load_time, model_loaded)
    # - Job processing duration metrics
    # See docs/TECHNICAL_DEBT.md for details
    
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
