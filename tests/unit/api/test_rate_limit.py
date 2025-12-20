"""Tests for rate limiting functionality."""

import os
import pytest
import time
from httpx import AsyncClient, ASGITransport

from booknlp.api.main import create_app


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_health_endpoint_not_rate_limited(self):
        """Test that health endpoint bypasses rate limiting (by design)."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "2/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Health endpoint should not be rate limited even with many requests
            for _ in range(10):
                response = await client.get("/v1/health")
                assert response.status_code == 200  # Should never get 429

    def test_rate_limit_decorator_exists(self):
        """Test that rate_limit decorator function exists and returns correctly."""
        from booknlp.api.rate_limit import rate_limit
        
        # When rate limiting is disabled (no env var), decorator should be a no-op
        if "BOOKNLP_RATE_LIMIT" in os.environ:
            del os.environ["BOOKNLP_RATE_LIMIT"]
        
        # Reload to pick up env change
        from booknlp.api import rate_limit as rl_module
        import importlib
        importlib.reload(rl_module)
        
        # Get decorator - should return no-op when disabled
        decorator = rl_module.rate_limit("10/minute")
        
        # Apply to a simple function
        def test_func():
            return "test"
        
        decorated = decorator(test_func)
        # Should return same function (no-op)
        assert decorated() == "test"

    @pytest.mark.asyncio
    async def test_rate_limit_disabled_no_429(self):
        """Test that when rate limiting is disabled, no 429 responses occur."""
        # Clear rate limit env var
        if "BOOKNLP_RATE_LIMIT" in os.environ:
            del os.environ["BOOKNLP_RATE_LIMIT"]
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Many requests should never get 429 when rate limiting is disabled
            for _ in range(20):
                response = await client.post("/v1/analyze", json={"text": "test"})
                # Should get 503 (not ready) or 200, but never 429
                assert response.status_code != 429

    def test_limiter_created_when_env_set(self):
        """Test that limiter is created when BOOKNLP_RATE_LIMIT env var is set."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "10/minute"
        
        # Reload to pick up env change
        from booknlp.api import rate_limit as rl_module
        import importlib
        importlib.reload(rl_module)
        
        # Limiter should be created
        assert rl_module.limiter is not None
        assert rl_module.get_rate_limit() == "10/minute"

    def test_limiter_not_created_when_disabled(self):
        """Test that limiter is not created when BOOKNLP_RATE_LIMIT env var is not set."""
        # Clear rate limit env var
        if "BOOKNLP_RATE_LIMIT" in os.environ:
            del os.environ["BOOKNLP_RATE_LIMIT"]
        
        # Reload to pick up env change
        from booknlp.api import rate_limit as rl_module
        import importlib
        importlib.reload(rl_module)
        
        # Limiter should be None
        assert rl_module.limiter is None
        assert rl_module.get_rate_limit() is None

    def test_get_rate_limit_returns_env_value(self):
        """Test that get_rate_limit returns the environment variable value."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "100/hour"
        
        from booknlp.api import rate_limit as rl_module
        import importlib
        importlib.reload(rl_module)
        
        assert rl_module.get_rate_limit() == "100/hour"
