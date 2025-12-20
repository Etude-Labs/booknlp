"""E2E tests for health endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthEndpointsE2E:
    """End-to-end tests for health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_accessible(self, client: AsyncClient):
        """Test that health endpoint is always accessible."""
        response = await client.get("/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_auth(self, client: AsyncClient):
        """Test that health endpoint bypasses authentication."""
        # Should work without auth headers
        response = await client.get("/v1/health")
        assert response.status_code == 200
        
        # Should work even with invalid auth
        response = await client.get("/v1/health", headers={
            "X-API-Key": "invalid-key"
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_endpoint_when_models_loaded(self, client: AsyncClient):
        """Test ready endpoint when models are loaded."""
        response = await client.get("/v1/ready")
        
        # Should be 200 if models are loaded, 503 if still loading
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "device" in data
        
        if response.status_code == 200:
            assert data["status"] == "ready"
            assert data["model_loaded"] is True
        else:
            assert data["status"] == "loading"
            assert data["model_loaded"] is False

    @pytest.mark.asyncio
    async def test_ready_endpoint_bypasses_auth(self, client: AsyncClient):
        """Test that ready endpoint bypasses authentication."""
        # Should work without auth headers
        response = await client.get("/v1/ready")
        assert response.status_code in [200, 503]
        
        # Should work even with invalid auth
        response = await client.get("/v1/ready", headers={
            "X-API-Key": "invalid-key"
        })
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_health_endpoint_not_rate_limited(self, client: AsyncClient):
        """Test that health endpoint is not rate limited."""
        # Make multiple quick requests
        for _ in range(10):
            response = await client.get("/v1/health")
            assert response.status_code == 200
        
        # Should not have rate limit headers
        response = await client.get("/v1/health")
        assert "X-RateLimit-Limit" not in response.headers
        assert "X-RateLimit-Remaining" not in response.headers

    @pytest.mark.asyncio
    async def test_ready_endpoint_not_rate_limited(self, client: AsyncClient):
        """Test that ready endpoint is not rate limited."""
        # Make multiple quick requests
        for _ in range(10):
            response = await client.get("/v1/ready")
            assert response.status_code in [200, 503]
        
        # Should not have rate limit headers
        response = await client.get("/v1/ready")
        assert "X-RateLimit-Limit" not in response.headers
        assert "X-RateLimit-Remaining" not in response.headers

    @pytest.mark.asyncio
    async def test_health_endpoint_response_format(self, client: AsyncClient):
        """Test that health endpoint returns correct format."""
        response = await client.get("/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        
        # Check values
        assert data["status"] == "ok"
        assert isinstance(data["timestamp"], str)
        
        # Should be ISO 8601 format
        assert "T" in data["timestamp"]
        assert "Z" in data["timestamp"] or "+" in data["timestamp"] or "-" in data["timestamp"][-6:]

    @pytest.mark.asyncio
    async def test_ready_endpoint_response_format(self, client: AsyncClient):
        """Test that ready endpoint returns correct format."""
        response = await client.get("/v1/ready")
        assert response.status_code in [200, 503]
        
        data = response.json()
        
        # Check required fields
        required_fields = [
            "status", "model_loaded", "default_model",
            "available_models", "device", "cuda_available",
            "cuda_device_name"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check types
        assert isinstance(data["status"], str)
        assert isinstance(data["model_loaded"], bool)
        assert isinstance(data["default_model"], str)
        assert isinstance(data["available_models"], list)
        assert isinstance(data["device"], str)
        assert isinstance(data["cuda_available"], bool)
        assert isinstance(data["cuda_device_name"], str)
