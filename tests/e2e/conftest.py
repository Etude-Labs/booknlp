"""Configuration for E2E tests."""

import os
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from booknlp.api.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app():
    """Create the FastAPI application for testing."""
    # Enable production-like settings
    os.environ["BOOKNLP_AUTH_REQUIRED"] = "true"
    os.environ["BOOKNLP_API_KEY"] = "e2e-test-key-12345"
    os.environ["BOOKNLP_RATE_LIMIT"] = "60/minute"
    os.environ["BOOKNLP_METRICS_ENABLED"] = "true"
    os.environ["BOOKNLP_SHUTDOWN_GRACE_PERIOD"] = "30"
    
    app = create_app()
    return app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for E2E tests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Get authentication headers for E2E tests."""
    return {"X-API-Key": "e2e-test-key-12345"}


@pytest.fixture
def invalid_auth_headers():
    """Get invalid authentication headers for testing."""
    return {"X-API-Key": "wrong-key-67890"}
