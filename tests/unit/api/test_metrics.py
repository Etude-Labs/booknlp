"""Tests for Prometheus metrics endpoint."""

import os
import pytest
from httpx import AsyncClient

from booknlp.api.main import create_app


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint functionality."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that /metrics returns Prometheus-formatted metrics."""
        # Disable auth for testing
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/metrics")
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            
            # Check for basic Prometheus metrics format
            metrics_text = response.text
            assert "# HELP" in metrics_text
            assert "# TYPE" in metrics_text
            
            # Should include FastAPI metrics
            assert "http_requests_total" in metrics_text
            assert "http_request_duration_seconds" in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_endpoint_bypasses_auth(self):
        """Test that metrics endpoint bypasses authentication."""
        # Enable auth
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Should work without auth key
            response = await client.get("/metrics")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_includes_custom_metrics(self):
        """Test that custom BookNLP metrics are included."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make some requests to generate metrics
            await client.get("/v1/health")
            await client.get("/v1/ready")
            
            # Get metrics
            response = await client.get("/metrics")
            metrics_text = response.text
            
            # Should have request metrics
            assert 'http_requests_total{method="GET",path="/v1/health"' in metrics_text
            assert 'http_requests_total{method="GET",path="/v1/ready"' in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_includes_process_metrics(self):
        """Test that process metrics are included."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/metrics")
            metrics_text = response.text
            
            # Should include process metrics
            assert "process_cpu_seconds_total" in metrics_text
            assert "process_resident_memory_bytes" in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_endpoint_different_paths(self):
        """Test metrics endpoint works with different base paths."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test with /metrics
            response = await client.get("/metrics")
            assert response.status_code == 200
            
            # Test with /metrics/ (should also work)
            response = await client.get("/metrics/")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_labels_included(self):
        """Test that appropriate labels are included in metrics."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make a request that will return 200
            await client.get("/v1/health")
            
            response = await client.get("/metrics")
            metrics_text = response.text
            
            # Should include status code label
            assert 'status_code="200"' in metrics_text
            assert 'method="GET"' in metrics_text

    @pytest.mark.asyncio
    async def test_metrics_with_rate_limiting(self):
        """Test that metrics work even when rate limiting is enabled."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        os.environ["BOOKNLP_RATE_LIMIT"] = "10/minute"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make requests
            await client.get("/v1/health")
            
            # Get metrics
            response = await client.get("/metrics")
            assert response.status_code == 200
            
            # Should still have metrics even with rate limiting
            assert "http_requests_total" in response.text
