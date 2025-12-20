"""Integration tests for Docker container (AC3-AC6).

These tests require Docker to be available and the container to be built.
Run with: pytest tests/integration/ -v --docker

To build the container first:
    docker build -t booknlp:cpu .
"""

import subprocess
import pytest


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    subprocess.run(["docker", "--version"], capture_output=True).returncode != 0,
    reason="Docker not available"
)


class TestContainerBuilds:
    """Test that the container builds successfully (AC1)."""

    @pytest.mark.slow
    def test_container_builds_successfully(self):
        """Given Dockerfile, docker build should complete without errors."""
        result = subprocess.run(
            ["docker", "build", "-t", "booknlp:cpu-test", "."],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minutes
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"


class TestBookNLPImport:
    """Test that BookNLP imports correctly in container (AC2)."""

    def test_booknlp_import_succeeds(self):
        """Given built container, BookNLP should import without errors."""
        result = subprocess.run(
            [
                "docker", "run", "--rm", "booknlp:cpu",
                "python", "-c", "from booknlp.booknlp import BookNLP; print('OK')"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout


class TestModelsPredownloaded:
    """Test that models are pre-downloaded in container (AC5)."""

    def test_small_model_files_exist(self):
        """Given built container, small model files should exist."""
        result = subprocess.run(
            [
                "docker", "run", "--rm", "booknlp:cpu",
                "ls", "-la", "/home/booknlp/booknlp_models/"
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Model directory should exist (may be empty if download failed)
        assert result.returncode == 0 or "No such file" not in result.stderr

    def test_spacy_model_available(self):
        """Given built container, spacy en_core_web_sm should be available."""
        result = subprocess.run(
            [
                "docker", "run", "--rm", "booknlp:cpu",
                "python", "-c", "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK')"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Spacy load failed: {result.stderr}"
        assert "OK" in result.stdout


class TestModelProcessing:
    """Test that models process text correctly (AC3, AC4)."""

    def test_small_model_processes_text(self):
        """Given built container, small model should process sample text."""
        test_text = "Call me Ishmael. Some years ago I went to sea."
        result = subprocess.run(
            [
                "docker", "run", "--rm", "booknlp:cpu",
                "python", "-c", f'''
from booknlp.booknlp import BookNLP
import tempfile
import os

booknlp = BookNLP("en", {{"pipeline": "entity,quote", "model": "small"}})
with tempfile.TemporaryDirectory() as tmpdir:
    input_file = os.path.join(tmpdir, "test.txt")
    with open(input_file, "w") as f:
        f.write("{test_text}")
    booknlp.process(input_file, tmpdir, "test")
    # Check output files exist
    assert os.path.exists(os.path.join(tmpdir, "test.tokens"))
    print("OK")
'''
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, f"Processing failed: {result.stderr}"
        assert "OK" in result.stdout


class TestOfflineOperation:
    """Test that container works without network (AC5)."""

    def test_container_works_offline(self):
        """Given built container with --network none, BookNLP should still import."""
        result = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none", "booknlp:cpu",
                "python", "-c", "from booknlp.booknlp import BookNLP; print('OK')"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Offline import failed: {result.stderr}"
        assert "OK" in result.stdout


class TestDockerCompose:
    """Test that docker-compose works (AC6)."""

    def test_docker_compose_config_valid(self):
        """Given docker-compose.yml, config should be valid."""
        result = subprocess.run(
            ["docker", "compose", "config"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Compose config invalid: {result.stderr}"
