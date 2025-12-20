"""Integration tests for API endpoints (AC1-AC6)."""

import pytest


# Skip all tests if FastAPI/httpx not available
try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not FASTAPI_AVAILABLE,
    reason="FastAPI not available"
)


@pytest.fixture
def client():
    """Create test client for API."""
    try:
        from booknlp.api.main import create_app
    except ImportError:
        pytest.skip("API not implemented yet")
    
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Integration tests for GET /v1/health (AC3)."""

    def test_health_returns_200(self, client):
        """Given running API, GET /v1/health should return 200."""
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        """Given running API, health should return status ok."""
        response = client.get("/v1/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_has_timestamp(self, client):
        """Given running API, health should include timestamp."""
        response = client.get("/v1/health")
        data = response.json()
        assert "timestamp" in data


class TestReadyEndpoint:
    """Integration tests for GET /v1/ready (AC4)."""

    def test_ready_returns_status_code(self, client):
        """Given running API, GET /v1/ready should return valid status."""
        response = client.get("/v1/ready")
        # Can be 200 (ready) or 503 (loading)
        assert response.status_code in [200, 503]

    def test_ready_has_model_loaded_field(self, client):
        """Given running API, ready should have model_loaded field."""
        response = client.get("/v1/ready")
        data = response.json()
        assert "model_loaded" in data


class TestOpenAPIDocs:
    """Integration tests for OpenAPI documentation (AC5)."""

    def test_openapi_json_available(self, client):
        """Given running API, /openapi.json should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data

    def test_docs_endpoint_available(self, client):
        """Given running API, /docs should be available."""
        response = client.get("/docs")
        assert response.status_code == 200
