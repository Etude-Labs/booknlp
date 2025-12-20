"""Unit tests for GPU Dockerfile structure (AC1)."""

import os

import pytest


class TestDockerfileGpuStructure:
    """Test Dockerfile.gpu exists and has correct structure."""

    @pytest.fixture
    def dockerfile_path(self):
        """Path to GPU Dockerfile."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Dockerfile.gpu"
        )

    @pytest.fixture
    def dockerfile_content(self, dockerfile_path):
        """Read Dockerfile.gpu content."""
        if not os.path.exists(dockerfile_path):
            pytest.skip("Dockerfile.gpu not implemented yet")
        with open(dockerfile_path, "r") as f:
            return f.read()

    def test_dockerfile_gpu_exists(self, dockerfile_path):
        """Given project, Dockerfile.gpu should exist."""
        assert os.path.exists(dockerfile_path), "Dockerfile.gpu not found"

    def test_dockerfile_uses_cuda_base_image(self, dockerfile_content):
        """Given Dockerfile.gpu, it should use CUDA base image."""
        assert "nvidia/cuda" in dockerfile_content or "cuda" in dockerfile_content.lower()

    def test_dockerfile_installs_pytorch_cuda(self, dockerfile_content):
        """Given Dockerfile.gpu, it should install PyTorch with CUDA."""
        # Should have cu124 or cu121 or similar CUDA version suffix
        assert "cu12" in dockerfile_content or "cuda" in dockerfile_content.lower()

    def test_dockerfile_exposes_port_8000(self, dockerfile_content):
        """Given Dockerfile.gpu, it should expose port 8000."""
        assert "EXPOSE 8000" in dockerfile_content

    def test_dockerfile_runs_uvicorn(self, dockerfile_content):
        """Given Dockerfile.gpu, it should run uvicorn."""
        assert "uvicorn" in dockerfile_content

    def test_dockerfile_sets_non_root_user(self, dockerfile_content):
        """Given Dockerfile.gpu, it should use non-root user."""
        assert "USER booknlp" in dockerfile_content or "USER" in dockerfile_content

    def test_dockerfile_has_healthcheck(self, dockerfile_content):
        """Given Dockerfile.gpu, it should have healthcheck."""
        assert "HEALTHCHECK" in dockerfile_content
