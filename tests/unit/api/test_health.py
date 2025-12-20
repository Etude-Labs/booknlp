"""Unit tests for health endpoints (AC3, AC4)."""

import pytest


class TestHealthEndpoint:
    """Test health endpoint schema and behavior."""

    def test_health_response_has_status_field(self):
        """Given health endpoint, response should have status field."""
        try:
            from booknlp.api.schemas.responses import HealthResponse
        except ImportError:
            pytest.skip("HealthResponse not implemented yet")
        
        response = HealthResponse(status="ok")
        assert response.status == "ok"

    def test_health_response_has_timestamp_field(self):
        """Given health endpoint, response should have timestamp field."""
        try:
            from booknlp.api.schemas.responses import HealthResponse
        except ImportError:
            pytest.skip("HealthResponse not implemented yet")
        
        from datetime import datetime
        response = HealthResponse(status="ok", timestamp=datetime.now())
        assert response.timestamp is not None


class TestReadyEndpoint:
    """Test ready endpoint schema and behavior."""

    def test_ready_response_has_required_fields(self):
        """Given ready endpoint, response should have all required fields."""
        try:
            from booknlp.api.schemas.responses import ReadyResponse
        except ImportError:
            pytest.skip("ReadyResponse not implemented yet")
        
        response = ReadyResponse(
            status="ready",
            model_loaded=True,
            default_model="small",
            available_models=["small", "big"]
        )
        assert response.status == "ready"
        assert response.model_loaded is True
        assert response.default_model == "small"
        assert "small" in response.available_models

    def test_ready_response_loading_state(self):
        """Given models loading, ready response should show loading status."""
        try:
            from booknlp.api.schemas.responses import ReadyResponse
        except ImportError:
            pytest.skip("ReadyResponse not implemented yet")
        
        response = ReadyResponse(
            status="loading",
            model_loaded=False,
            default_model="small",
            available_models=[]
        )
        assert response.status == "loading"
        assert response.model_loaded is False
