"""Unit tests for Pydantic schemas (AC1, AC2)."""

import pytest


class TestAnalyzeRequestSchema:
    """Test AnalyzeRequest validation."""

    def test_analyze_request_with_valid_text(self):
        """Given valid text, AnalyzeRequest should be created."""
        try:
            from booknlp.api.schemas.requests import AnalyzeRequest
        except ImportError:
            pytest.skip("AnalyzeRequest not implemented yet")
        
        request = AnalyzeRequest(text="Call me Ishmael.")
        assert request.text == "Call me Ishmael."
        assert request.model == "small"  # default
        assert request.book_id == "document"  # default

    def test_analyze_request_rejects_empty_text(self):
        """Given empty text, AnalyzeRequest should raise validation error."""
        try:
            from booknlp.api.schemas.requests import AnalyzeRequest
            from pydantic import ValidationError
        except ImportError:
            pytest.skip("AnalyzeRequest not implemented yet")
        
        with pytest.raises(ValidationError):
            AnalyzeRequest(text="")

    def test_analyze_request_rejects_text_too_long(self):
        """Given text over 500K chars, AnalyzeRequest should raise validation error."""
        try:
            from booknlp.api.schemas.requests import AnalyzeRequest
            from pydantic import ValidationError
        except ImportError:
            pytest.skip("AnalyzeRequest not implemented yet")
        
        long_text = "x" * 500_001
        with pytest.raises(ValidationError):
            AnalyzeRequest(text=long_text)

    def test_analyze_request_accepts_valid_models(self):
        """Given valid model names, AnalyzeRequest should accept them."""
        try:
            from booknlp.api.schemas.requests import AnalyzeRequest
        except ImportError:
            pytest.skip("AnalyzeRequest not implemented yet")
        
        for model in ["small", "big"]:
            request = AnalyzeRequest(text="test", model=model)
            assert request.model == model

    def test_analyze_request_custom_pipeline(self):
        """Given custom pipeline, AnalyzeRequest should accept it."""
        try:
            from booknlp.api.schemas.requests import AnalyzeRequest
        except ImportError:
            pytest.skip("AnalyzeRequest not implemented yet")
        
        request = AnalyzeRequest(
            text="test",
            pipeline=["entity", "quote"]
        )
        assert request.pipeline == ["entity", "quote"]


class TestAnalyzeResponseSchema:
    """Test AnalyzeResponse schema."""

    def test_analyze_response_has_required_fields(self):
        """Given valid data, AnalyzeResponse should have all fields."""
        try:
            from booknlp.api.schemas.responses import AnalyzeResponse
        except ImportError:
            pytest.skip("AnalyzeResponse not implemented yet")
        
        response = AnalyzeResponse(
            book_id="test",
            model="small",
            processing_time_ms=100,
            token_count=10,
            tokens=[],
            entities=[],
            quotes=[],
            characters=[],
            events=[],
            supersenses=[]
        )
        assert response.book_id == "test"
        assert response.processing_time_ms == 100
