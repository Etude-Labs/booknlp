"""Unit tests for FastAPI app factory."""

import pytest


class TestAppFactory:
    """Test FastAPI application factory."""

    def test_create_app_returns_fastapi_instance(self):
        """Given app factory, it should return FastAPI instance."""
        try:
            from booknlp.api.main import create_app
            from fastapi import FastAPI
        except ImportError:
            pytest.skip("App factory not implemented yet")
        
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_has_title(self):
        """Given app, it should have a title."""
        try:
            from booknlp.api.main import create_app
        except ImportError:
            pytest.skip("App factory not implemented yet")
        
        app = create_app()
        assert app.title == "BookNLP API"

    def test_app_has_version(self):
        """Given app, it should have a version."""
        try:
            from booknlp.api.main import create_app
        except ImportError:
            pytest.skip("App factory not implemented yet")
        
        app = create_app()
        assert app.version is not None
