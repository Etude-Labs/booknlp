"""Shared pytest configuration and fixtures for all tests."""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from prometheus_client import REGISTRY


def create_test_client(app: FastAPI) -> AsyncClient:
    """Create an AsyncClient configured for testing with ASGITransport.
    
    This is compatible with httpx >= 0.28.0 which removed the `app` parameter.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Configured AsyncClient for testing
    """
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest_asyncio.fixture
async def async_client_factory():
    """Factory fixture for creating test clients.
    
    Usage:
        async def test_something(async_client_factory):
            from booknlp.api.main import create_app
            app = create_app()
            async with async_client_factory(app) as client:
                response = await client.get("/v1/health")
    """
    async def _factory(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
        async with create_test_client(app) as client:
            yield client
    
    return _factory


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(autouse=True)
def reset_prometheus_registry():
    """Reset Prometheus registry before each test to avoid duplicate metrics.
    
    This fixture runs automatically before each test to ensure that
    tests creating FastAPI apps don't conflict with each other's metrics.
    """
    # Collect all collectors to unregister
    collectors_to_remove = []
    for collector in list(REGISTRY._names_to_collectors.values()):
        collectors_to_remove.append(collector)
    
    # Unregister each collector
    for collector in set(collectors_to_remove):
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    yield
    
    # Cleanup after test (optional, but good practice)
    collectors_to_remove = []
    for collector in list(REGISTRY._names_to_collectors.values()):
        collectors_to_remove.append(collector)
    
    for collector in set(collectors_to_remove):
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
