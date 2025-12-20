"""Tests for API key authentication."""

import os
import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from booknlp.api.main import create_app
from booknlp.api.dependencies import verify_api_key


class TestAPIKeyAuth:
    """Test API key authentication functionality."""

    @pytest.mark.asyncio
    async def test_auth_required_returns_401(self):
        """Test that requests without API key return 401 when auth is required."""
        # Set auth required
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/v1/jobs", json={
                "text": "Test text",
                "book_id": "test"
            })
            
            assert response.status_code == 401
            assert "Missing API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_valid_api_key_succeeds(self):
        """Test that requests with valid API key succeed."""
        # Set auth required
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/v1/jobs", json={
                "text": "Test text",
                "book_id": "test"
            }, headers={"X-API-Key": "test-key-12345"})
            
            # Should not be 401 (may be 422 if queue not running, but not auth error)
            assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self):
        """Test that requests with invalid API key return 401."""
        # Set auth required
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "correct-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/v1/jobs", json={
                "text": "Test text",
                "book_id": "test"
            }, headers={"X-API-Key": "wrong-key-67890"})
            
            assert response.status_code == 401
            assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_disabled_allows_requests(self):
        """Test that when auth is disabled, requests succeed without API key."""
        # Set auth disabled
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/health")
            
            # Health endpoint should work without auth
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_auth(self):
        """Test that health endpoint bypasses authentication."""
        # Set auth required
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Health endpoint should work without auth key
            response = await client.get("/v1/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoint_bypasses_auth(self):
        """Test that metrics endpoint bypasses authentication."""
        # Set auth required
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Metrics endpoint should work without auth key
            response = await client.get("/metrics")
            # Will return 404 until implemented, but not 401
            assert response.status_code != 401

    def test_verify_api_key_dependency_valid(self):
        """Test the verify_api_key dependency with valid key."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        # Should not raise exception
        result = verify_api_key("test-key-12345")
        assert result == "test-key-12345"

    def test_verify_api_key_dependency_invalid(self):
        """Test the verify_api_key dependency with invalid key."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "correct-key-12345"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("wrong-key-67890")
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value.detail)

    def test_verify_api_key_dependency_missing(self):
        """Test the verify_api_key dependency with missing key."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
        os.environ["BOOKNLP_API_KEY"] = "test-key-12345"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(None)
        
        assert exc_info.value.status_code == 401
        assert "Missing API key" in str(exc_info.value.detail)

    def test_verify_api_key_dependency_disabled(self):
        """Test the verify_api_key dependency when auth is disabled."""
        os.environ["BOOKNLP_AUTH_REQUIRED"] = "false"
        
        # Should not raise exception even with no key
        result = verify_api_key(None)
        assert result is None
