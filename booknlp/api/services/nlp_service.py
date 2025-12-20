"""NLP service wrapper for BookNLP."""

from typing import Any

# Global singleton instance
_nlp_service: "NLPService | None" = None


class NLPService:
    """Wrapper service for BookNLP functionality."""

    def __init__(self, default_model: str = "small"):
        """Initialize NLP service.
        
        Args:
            default_model: Default model to use for analysis.
        """
        self._default_model = default_model
        self._models: dict[str, Any] = {}
        self._ready = False
        self._available_models = ["small", "big"]

    @property
    def is_ready(self) -> bool:
        """Check if models are loaded and ready."""
        return self._ready

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return self._default_model

    @property
    def available_models(self) -> list[str]:
        """Get list of available models."""
        return self._available_models if self._ready else []

    def load_models(self) -> None:
        """Pre-load models on startup.
        
        This is called during application startup to load models
        into memory before accepting requests.
        """
        try:
            from booknlp.booknlp import BookNLP
            
            for model_name in self._available_models:
                self._models[model_name] = BookNLP("en", {
                    "pipeline": "entity,quote,supersense,event,coref",
                    "model": model_name,
                })
            self._ready = True
        except Exception as e:
            # Log error but don't crash - allow health checks to work
            print(f"Warning: Failed to load models: {e}")
            self._ready = False

    def get_model(self, model_name: str) -> Any:
        """Get a loaded model by name.
        
        Args:
            model_name: Name of the model to retrieve.
            
        Returns:
            The BookNLP model instance.
            
        Raises:
            ValueError: If model is not loaded.
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not loaded")
        return self._models[model_name]


def get_nlp_service() -> NLPService:
    """Get the global NLP service instance.
    
    Returns:
        The singleton NLPService instance.
    """
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service


def initialize_nlp_service(default_model: str = "small") -> NLPService:
    """Initialize and return the global NLP service.
    
    Args:
        default_model: Default model to use.
        
    Returns:
        The initialized NLPService instance.
    """
    global _nlp_service
    _nlp_service = NLPService(default_model=default_model)
    return _nlp_service
