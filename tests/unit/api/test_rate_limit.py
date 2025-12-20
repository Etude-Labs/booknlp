"""Tests for rate limiting functionality."""

import os
import pytest
import time
from httpx import AsyncClient

from booknlp.api.main import create_app


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self):
        """Test that rate limit is enforced after threshold."""
        # Set up rate limiting
        os.environ["BOOKNLP_RATE_LIMIT"] = "10/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"  # Disable auth for testing
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make 10 requests (should succeed)
            for i in range(10):
                response = await client.get("/v1/health")
                assert response.status_code == 200
            
            # 11th request should be rate limited
            response = await client.get("/v1/health")
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rate_limit_per_client(self):
        """Test that rate limiting is per-client IP."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "5/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        
        # Simulate two different clients
        async with AsyncClient(app=app, base_url="http://test") as client1:
            async with AsyncClient(app=app, base_url="http://test") as client2:
                # Client 1 makes 5 requests
                for i in range(5):
                    response = await client1.get("/v1/health")
                    assert response.status_code == 200
                
                # Client 1 should be rate limited
                response = await client1.get("/v1/health")
                assert response.status_code == 429
                
                # Client 2 should still be able to make requests
                response = await client2.get("/v1/health")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self):
        """Test that rate limit headers are included in responses."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "10/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/health")
            
            # Check for rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            
            assert response.headers["X-RateLimit-Limit"] == "10"
            assert int(response.headers["X-RateLimit-Remaining"]) <= 10

    @pytest.mark.asyncio
    async def test_rate_limit_disabled(self):
        """Test that rate limiting can be disabled."""
        # Clear rate limit env var
        if "BOOKNLP_RATE_LIMIT" in os.environ:
            del os.environ["BOOKNLP_RATE_LIMIT"]
        
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make many requests - should all succeed
            for i in range(20):
                response = await client.get("/v1/health")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_with_auth(self):
        """Test that rate limiting works with authentication."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "5/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make requests with auth
            for i in range(5):
                response = await client.get("/v1/health")
                assert response.status_code == 200
            
            # 6th request should be rate limited (not auth error)
            response = await client.get("/v1/health")
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_window(self):
        """Test that rate limit resets after time window."""
        os.environ["BOOKNLP_RATE_LIMIT"] = "2/minute"
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make 2 requests (hit the limit)
            await client.get("/v1/health")
            await client.get("/v1/health")
            
            # 3rd request should be rate limited
            response = await client.get("/v1/health")
            assert response.status_code == 429
            
            # Note: In real tests, we'd wait for the window to reset
            # For unit tests, we can't easily test time-based reset
            # This would be better tested with time mocking
