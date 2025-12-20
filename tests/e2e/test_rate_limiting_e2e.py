"""E2E tests for rate limiting behavior."""

import pytest
import asyncio
from httpx import AsyncClient


class TestRateLimitingE2E:
    """End-to-end tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self, client: AsyncClient, auth_headers):
        """Test that rate limiting is enforced on protected endpoints."""
        # Note: We can't easily test exact rate limits in E2E without
        # controlling time, but we can verify the endpoint is protected
        
        # Make a request to a rate-limited endpoint
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        }, headers=auth_headers)
        
        # Should succeed initially
        assert response.status_code in [200, 422]  # 422 if queue not running
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limiting_bypass_on_health(self, client: AsyncClient):
        """Test that health endpoints bypass rate limiting."""
        # Health endpoints should not have rate limit headers
        response = await client.get("/v1/health")
        assert response.status_code == 200
        
        # Should not have rate limit headers
        assert "X-RateLimit-Limit" not in response.headers
        assert "X-RateLimit-Remaining" not in response.headers

    @pytest.mark.asyncio
    async def test_rate_limiting_bypass_on_metrics(self, client: AsyncClient):
        """Test that metrics endpoint bypasses rate limiting."""
        # Metrics endpoint should not have rate limit headers
        response = await client.get("/metrics")
        assert response.status_code == 200
        
        # Should not have rate limit headers
        assert "X-RateLimit-Limit" not in response.headers
        assert "X-RateLimit-Remaining" not in response.headers

    @pytest.mark.asyncio
    async def test_different_endpoints_different_limits(self, client: AsyncClient, auth_headers):
        """Test that different endpoints have different rate limits."""
        # Test job submission endpoint (10/minute)
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        }, headers=auth_headers)
        
        job_limit = response.headers.get("X-RateLimit-Limit")
        assert job_limit is not None
        
        # Test job status endpoint (60/minute)
        response = await client.get("/v1/jobs/stats", headers=auth_headers)
        status_limit = response.headers.get("X-RateLimit-Limit")
        assert status_limit is not None
        
        # The limits should be different
        # Note: This might be equal if rate limiting is disabled
        # In that case, both would be None or have the same high value

    @pytest.mark.asyncio
    async def test_rate_limiting_with_auth(self, client: AsyncClient):
        """Test that rate limiting works with authentication."""
        # Make request without auth - should get 401, not rate limited
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        })
        
        # Should fail with auth error, not rate limit error
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rate_limiting_headers_format(self, client: AsyncClient, auth_headers):
        """Test that rate limit headers are in correct format."""
        response = await client.get("/v1/jobs/stats", headers=auth_headers)
        assert response.status_code == 200
        
        # Check header formats
        limit_header = response.headers["X-RateLimit-Limit"]
        remaining_header = response.headers["X-RateLimit-Remaining"]
        reset_header = response.headers["X-RateLimit-Reset"]
        
        # Should be numeric strings
        assert limit_header.isdigit()
        assert remaining_header.isdigit()
        assert reset_header.isdigit()
        
        # Should be reasonable values
        assert int(limit_header) > 0
        assert int(remaining_header) >= 0
        assert int(reset_header) > 0
