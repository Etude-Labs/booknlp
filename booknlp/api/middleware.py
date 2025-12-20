"""Production middleware for BookNLP API."""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from booknlp.api.config import get_settings
from booknlp.api.logging_config import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request and response."""
        settings = get_settings()
        
        # Get or generate request ID
        request_id = request.headers.get(settings.request_id_header)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers[settings.request_id_header] = request_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with timing."""
        start_time = time.time()
        
        # Get request ID if available
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            }
        )
        
        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Only add HSTS in production
        settings = get_settings()
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application.
    
    Middleware is applied in reverse order (last added runs first).
    
    Args:
        app: FastAPI application instance.
    """
    # Add middleware in reverse order of execution
    # 1. Security headers (runs last)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 2. Request logging (runs after request ID is set)
    app.add_middleware(RequestLoggingMiddleware)
    
    # 3. Request ID (runs first)
    app.add_middleware(RequestIDMiddleware)
