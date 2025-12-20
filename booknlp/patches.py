"""Patches for BookNLP compatibility with modern library versions.

This module provides patches for known compatibility issues, particularly
the position_ids key error with transformers 4.x+.

See: https://github.com/booknlp/booknlp/issues/26
"""

from typing import Any


def remove_position_ids_from_state_dict(state_dict: dict[str, Any]) -> dict[str, Any]:
    """Remove position_ids key from BERT state dict if present.

    The transformers library 4.x+ changed how position_ids are handled,
    causing a key mismatch when loading older BookNLP models. This function
    removes the problematic key to allow model loading.

    Args:
        state_dict: PyTorch model state dictionary.

    Returns:
        State dictionary with position_ids removed if it was present.

    Example:
        >>> state_dict = {"bert.embeddings.position_ids": [...], "other": [...]}
        >>> result = remove_position_ids_from_state_dict(state_dict)
        >>> "bert.embeddings.position_ids" in result
        False
    """
    key_to_remove = "bert.embeddings.position_ids"

    if key_to_remove in state_dict:
        # Create a copy to avoid mutating the original
        state_dict = dict(state_dict)
        del state_dict[key_to_remove]

    return state_dict
