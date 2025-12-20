"""Integration tests for analyze endpoint (AC1, AC2, AC6)."""

import pytest

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


class TestAnalyzeEndpoint:
    """Integration tests for POST /v1/analyze (AC1)."""

    def test_analyze_endpoint_exists(self, client):
        """Given running API, POST /v1/analyze should exist."""
        response = client.post("/v1/analyze", json={"text": "test"})
        # Should not be 404
        assert response.status_code != 404

    def test_analyze_rejects_empty_text(self, client):
        """Given empty text, analyze should return 422."""
        response = client.post("/v1/analyze", json={"text": ""})
        assert response.status_code == 422

    def test_analyze_accepts_valid_request(self, client):
        """Given valid request, analyze should return 200 or 503."""
        response = client.post("/v1/analyze", json={
            "text": "Call me Ishmael.",
            "book_id": "test",
            "model": "small"
        })
        # 200 if models loaded, 503 if not ready
        assert response.status_code in [200, 503]


class TestAnalyzeWithPipeline:
    """Integration tests for pipeline filtering (AC2)."""

    def test_analyze_accepts_custom_pipeline(self, client):
        """Given custom pipeline, request should be accepted."""
        response = client.post("/v1/analyze", json={
            "text": "Call me Ishmael.",
            "pipeline": ["entity", "quote"]
        })
        # Should not be 422 (validation error)
        assert response.status_code != 422 or "pipeline" not in str(response.json())


class TestModelSelection:
    """Integration tests for model selection (AC6)."""

    def test_analyze_accepts_small_model(self, client):
        """Given model=small, request should be accepted."""
        response = client.post("/v1/analyze", json={
            "text": "Test text.",
            "model": "small"
        })
        assert response.status_code != 422

    def test_analyze_accepts_big_model(self, client):
        """Given model=big, request should be accepted."""
        response = client.post("/v1/analyze", json={
            "text": "Test text.",
            "model": "big"
        })
        assert response.status_code != 422

    def test_analyze_rejects_invalid_model(self, client):
        """Given invalid model, request should return 422."""
        response = client.post("/v1/analyze", json={
            "text": "Test text.",
            "model": "invalid"
        })
        assert response.status_code == 422
