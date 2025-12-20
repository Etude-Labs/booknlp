"""Unit tests for NLP service (AC1, AC2, AC6)."""

import pytest
from unittest.mock import MagicMock, patch


class TestNLPService:
    """Test NLP service wrapper."""

    def test_nlp_service_initializes_with_default_model(self):
        """Given NLPService, it should have default model set."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        assert service.default_model == "small"

    def test_nlp_service_not_ready_before_loading(self):
        """Given fresh NLPService, is_ready should be False."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        assert service.is_ready is False

    def test_nlp_service_available_models_empty_when_not_ready(self):
        """Given unloaded NLPService, available_models should be empty."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        assert service.available_models == []

    def test_get_model_raises_when_not_loaded(self):
        """Given unloaded NLPService, get_model should raise ValueError."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        with pytest.raises(ValueError, match="not loaded"):
            service.get_model("small")
