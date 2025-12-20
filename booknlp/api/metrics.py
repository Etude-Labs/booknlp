"""Prometheus metrics configuration for BookNLP API."""

import os
from typing import Optional

from prometheus_client import REGISTRY, CollectorRegistry
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
    # Note: v7.x removed should_instrument_requests_duration (always enabled)
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_group_untemplated=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
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
    # Check if already instrumented to avoid duplicate registration in tests
    if hasattr(app.state, '_metrics_instrumented'):
        return
    
    instrumentator = create_metrics()
    
    if instrumentator:
        try:
            # Instrument the app
            instrumentator.instrument(app).expose(app)
            app.state._metrics_instrumented = True
        except ValueError as e:
            # Handle duplicate timeseries error in tests
            if "Duplicated timeseries" in str(e):
                # Clear existing collectors and retry
                _clear_metrics_registry()
                instrumentator = create_metrics()
                instrumentator.instrument(app).expose(app)
                app.state._metrics_instrumented = True
            else:
                raise


def _clear_metrics_registry() -> None:
    """Clear Prometheus registry for testing. Only use in test environments."""
    collectors_to_remove = []
    for collector in REGISTRY._names_to_collectors.values():
        collectors_to_remove.append(collector)
    
    for collector in set(collectors_to_remove):
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


# Global instrumentator instance (lazy initialization)
_instrumentator: Optional[Instrumentator] = None


def get_instrumentator() -> Optional[Instrumentator]:
    """Get the global metrics instrumentator.
    
    Returns:
        The Instrumentator instance or None if metrics disabled
    """
    global _instrumentator
    if _instrumentator is None:
        _instrumentator = create_metrics()
    return _instrumentator
