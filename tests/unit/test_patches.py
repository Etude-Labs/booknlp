"""Unit tests for position_ids patch (AC1, AC2)."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent


class TestPositionIdsPatch:
    """Test the position_ids patch for transformers compatibility."""

    def test_patches_module_exists(self):
        """Given the repo, patches.py should exist."""
        patches_path = REPO_ROOT / "booknlp" / "patches.py"
        assert patches_path.exists(), "booknlp/patches.py must exist"

    def test_patch_removes_position_ids_key(self):
        """Given a state_dict with position_ids, patch should remove it."""
        # Import will fail if patches.py doesn't exist
        try:
            from booknlp.patches import remove_position_ids_from_state_dict
        except ImportError:
            pytest.skip("patches.py does not exist yet")
        
        # Arrange: state_dict with position_ids
        state_dict = {
            "bert.embeddings.position_ids": [1, 2, 3],
            "bert.embeddings.word_embeddings.weight": [4, 5, 6],
            "other_key": "value",
        }
        
        # Act
        result = remove_position_ids_from_state_dict(state_dict)
        
        # Assert
        assert "bert.embeddings.position_ids" not in result
        assert "bert.embeddings.word_embeddings.weight" in result
        assert "other_key" in result

    def test_patch_handles_missing_position_ids(self):
        """Given a state_dict without position_ids, patch should not error."""
        try:
            from booknlp.patches import remove_position_ids_from_state_dict
        except ImportError:
            pytest.skip("patches.py does not exist yet")
        
        # Arrange: state_dict without position_ids
        state_dict = {
            "bert.embeddings.word_embeddings.weight": [4, 5, 6],
            "other_key": "value",
        }
        
        # Act
        result = remove_position_ids_from_state_dict(state_dict)
        
        # Assert: should return unchanged
        assert result == state_dict

    def test_patch_function_is_importable(self):
        """Given patches.py, the patch function should be importable."""
        try:
            from booknlp.patches import remove_position_ids_from_state_dict
            assert callable(remove_position_ids_from_state_dict)
        except ImportError:
            pytest.fail("Could not import remove_position_ids_from_state_dict from booknlp.patches")
