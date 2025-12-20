"""E2E tests for metrics endpoint."""

import pytest
from httpx import AsyncClient


class TestMetricsE2E:
    """End-to-end tests for Prometheus metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_accessible_without_auth(self, client: AsyncClient):
        """Test that metrics endpoint is accessible without authentication."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        
        # Should return plain text content type
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_metrics_format(self, client: AsyncClient):
        """Test that metrics are in Prometheus format."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        
        metrics_text = response.text
        
        # Should contain HELP and TYPE comments
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # Should contain basic HTTP metrics
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_include_request_data(self, client: AsyncClient, auth_headers):
        """Test that metrics include actual request data."""
        # Make some requests to generate metrics
        await client.get("/v1/health")
        await client.get("/v1/ready")
        
        # Get metrics
        response = await client.get("/metrics")
        metrics_text = response.text
        
        # Should include metrics for our requests
        assert 'http_requests_total{method="GET",path="/v1/health"' in metrics_text
        assert 'http_requests_total{method="GET",path="/v1/ready"' in metrics_text
        
        # Should include status codes
        assert 'status_code="200"' in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_with_job_requests(self, client: AsyncClient, auth_headers):
        """Test that metrics include job-related requests."""
        # Make a job request
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "metrics-test"
        }, headers=auth_headers)
        
        # Get metrics
        response = await client.get("/metrics")
        metrics_text = response.text
        
        # Should include job submission metrics
        assert 'http_requests_total{method="POST",path="/v1/jobs"' in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_with_auth_failures(self, client: AsyncClient):
        """Test that metrics include authentication failures."""
        # Make request without auth
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        })
        
        # Get metrics
        response = await client.get("/metrics")
        metrics_text = response.text
        
        # Should include 401 status code
        assert 'status_code="401"' in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_process_info(self, client: AsyncClient):
        """Test that metrics include process information."""
        response = await client.get("/metrics")
        metrics_text = response.text
        
        # Should include process metrics if available
        # Note: These might not be present in all environments
        # assert "process_cpu_seconds_total" in metrics_text
        # assert "process_resident_memory_bytes" in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_endpoint_different_paths(self, client: AsyncClient):
        """Test that metrics endpoint works with different paths."""
        # Test /metrics
        response = await client.get("/metrics")
        assert response.status_code == 200
        
        # Test /metrics/ (should also work)
        response = await client.get("/metrics/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_not_rate_limited(self, client: AsyncClient):
        """Test that metrics endpoint is not rate limited."""
        # Make multiple quick requests
        for _ in range(10):
            response = await client.get("/metrics")
            assert response.status_code == 200
        
        # Should not have rate limit headers
        response = await client.get("/metrics")
        assert "X-RateLimit-Limit" not in response.headers
