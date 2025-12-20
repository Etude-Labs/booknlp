"""Rate limiting configuration for BookNLP API."""

import os
import time
from typing import Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse


def get_rate_limit() -> Optional[str]:
    """Get rate limit from environment variable.
    
    Returns:
        Rate limit string (e.g., "10/minute") or None if disabled
    """
    return os.getenv("BOOKNLP_RATE_LIMIT")


def create_limiter() -> Optional[Limiter]:
    """Create and configure rate limiter.
    
    Returns:
        Configured Limiter instance or None if rate limiting disabled
    """
    rate_limit = get_rate_limit()
    if not rate_limit:
        return None
    
    # Create limiter with key function based on client IP
    return Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors.
    
    Args:
        request: The request that exceeded the rate limit
        exc: The RateLimitExceeded exception
        
    Returns:
        JSON response with 429 status code
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": f"Rate limit exceeded. Try again in {exc.detail} seconds."
        },
        headers={
            "Retry-After": str(exc.detail),
            "X-RateLimit-Limit": str(exc.detail),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + int(exc.detail)),
        }
    )


# Create global limiter instance
limiter = create_limiter()


def rate_limit(limit: str):
    """Decorator for rate limiting endpoints.
    
    Args:
        limit: Rate limit string (e.g., "10/minute")
        
    Returns:
        Decorator function or no-op if rate limiting disabled
    """
    if not limiter:
        # Rate limiting disabled, return no-op decorator
        def decorator(func):
            return func
        return decorator
    
    return limiter.limit(limit)
