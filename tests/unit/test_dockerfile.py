"""Unit tests for Dockerfile validation (AC1)."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent


class TestDockerfileStructure:
    """Test that Dockerfile has correct structure."""

    def test_dockerfile_exists(self):
        """Given the repo, Dockerfile should exist."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile must exist"

    def test_dockerfile_uses_python_3_12(self):
        """Given Dockerfile, it should use Python 3.12 base image."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text()
        
        assert "python:3.12" in content, "Dockerfile should use Python 3.12"

    def test_dockerfile_has_multi_stage_build(self):
        """Given Dockerfile, it should have multiple FROM statements (multi-stage)."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text()
        from_count = content.lower().count("from ")
        
        assert from_count >= 2, f"Dockerfile should have multi-stage build (found {from_count} FROM)"

    def test_dockerfile_has_builder_stage(self):
        """Given Dockerfile, it should have a builder stage."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text().lower()
        
        assert "as deps" in content, "Dockerfile should have 'AS deps' stage"

    def test_dockerfile_copies_requirements(self):
        """Given Dockerfile, it should copy requirements.txt."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text()
        
        assert "requirements.txt" in content, "Dockerfile should reference requirements.txt"

    def test_dockerfile_installs_spacy_model(self):
        """Given Dockerfile, it should download spacy en_core_web_sm model."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text()
        
        assert "en_core_web_sm" in content, "Dockerfile should download spacy model"

    def test_dockerfile_sets_non_root_user(self):
        """Given Dockerfile, it should set a non-root user."""
        dockerfile_path = REPO_ROOT / "Dockerfile"
        
        if not dockerfile_path.exists():
            pytest.skip("Dockerfile does not exist yet")
        
        content = dockerfile_path.read_text()
        
        assert "USER " in content, "Dockerfile should set non-root USER"


class TestDockerignore:
    """Test that .dockerignore exists and excludes appropriate files."""

    def test_dockerignore_exists(self):
        """Given the repo, .dockerignore should exist."""
        dockerignore_path = REPO_ROOT / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore must exist"

    def test_dockerignore_excludes_git(self):
        """Given .dockerignore, it should exclude .git directory."""
        dockerignore_path = REPO_ROOT / ".dockerignore"
        
        if not dockerignore_path.exists():
            pytest.skip(".dockerignore does not exist yet")
        
        content = dockerignore_path.read_text()
        
        assert ".git" in content, ".dockerignore should exclude .git"

    def test_dockerignore_excludes_pycache(self):
        """Given .dockerignore, it should exclude __pycache__."""
        dockerignore_path = REPO_ROOT / ".dockerignore"
        
        if not dockerignore_path.exists():
            pytest.skip(".dockerignore does not exist yet")
        
        content = dockerignore_path.read_text()
        
        assert "__pycache__" in content or "*.pyc" in content, \
            ".dockerignore should exclude Python cache files"
