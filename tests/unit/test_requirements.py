"""Unit tests for requirements.txt validation (AC1)."""

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent


class TestRequirementsPinned:
    """Test that requirements.txt has properly pinned dependencies."""

    def test_requirements_file_exists(self):
        """Given the repo, requirements.txt should exist."""
        requirements_path = REPO_ROOT / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt must exist"

    def test_all_dependencies_have_pinned_versions(self):
        """Given requirements.txt, all packages should have == version pins."""
        requirements_path = REPO_ROOT / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        
        content = requirements_path.read_text()
        lines = [
            line.strip() 
            for line in content.splitlines() 
            if line.strip() and not line.startswith("#")
        ]
        
        # Pattern for pinned version: package==version
        pinned_pattern = re.compile(r"^[a-zA-Z0-9_-]+==\d+\.\d+")
        
        unpinned = []
        for line in lines:
            if not pinned_pattern.match(line):
                unpinned.append(line)
        
        assert not unpinned, f"Unpinned dependencies found: {unpinned}"

    def test_required_packages_present(self):
        """Given requirements.txt, core packages should be present."""
        requirements_path = REPO_ROOT / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        
        content = requirements_path.read_text().lower()
        
        required_packages = ["torch", "transformers", "spacy", "tensorflow"]
        
        missing = [pkg for pkg in required_packages if pkg not in content]
        
        assert not missing, f"Missing required packages: {missing}"

    def test_torch_version_is_2_5_x(self):
        """Given requirements.txt, torch should be 2.5.x."""
        requirements_path = REPO_ROOT / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        
        content = requirements_path.read_text()
        
        assert "torch==2.5" in content, "torch should be version 2.5.x"

    def test_transformers_version_is_4_46_x(self):
        """Given requirements.txt, transformers should be 4.46.x."""
        requirements_path = REPO_ROOT / "requirements.txt"
        
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        
        content = requirements_path.read_text()
        
        assert "transformers==4.46" in content, "transformers should be version 4.46.x"
