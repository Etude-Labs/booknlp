"""Unit tests for GPU device detection (AC2, AC3)."""

import pytest
from unittest.mock import patch, MagicMock


class TestDeviceDetection:
    """Test device detection in NLPService."""

    def test_get_device_returns_cuda_when_available(self):
        """Given CUDA available, _get_device should return cuda device."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        
        with patch("torch.cuda.is_available", return_value=True):
            device = service._get_device()
            assert str(device) == "cuda" or "cuda" in str(device)

    def test_get_device_returns_cpu_when_cuda_unavailable(self):
        """Given CUDA unavailable, _get_device should return cpu device."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        
        with patch("torch.cuda.is_available", return_value=False):
            device = service._get_device()
            assert str(device) == "cpu"

    def test_nlp_service_stores_device_info(self):
        """Given NLPService, it should store device information."""
        from booknlp.api.services.nlp_service import NLPService
        
        service = NLPService()
        
        # Service should have device property
        assert hasattr(service, "device") or hasattr(service, "_device")


class TestReadyResponseDeviceInfo:
    """Test ready endpoint includes device information."""

    def test_ready_response_has_device_field(self):
        """Given ReadyResponse, it should have device field."""
        try:
            from booknlp.api.schemas.responses import ReadyResponse
        except ImportError:
            pytest.skip("ReadyResponse not available")
        
        # Check if device field exists in model
        fields = ReadyResponse.model_fields
        assert "device" in fields, "ReadyResponse should have device field"

    def test_ready_response_has_cuda_available_field(self):
        """Given ReadyResponse, it should have cuda_available field."""
        try:
            from booknlp.api.schemas.responses import ReadyResponse
        except ImportError:
            pytest.skip("ReadyResponse not available")
        
        fields = ReadyResponse.model_fields
        assert "cuda_available" in fields, "ReadyResponse should have cuda_available field"
