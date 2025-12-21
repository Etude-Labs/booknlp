"""Integration tests for async job API endpoints.

These tests run against either:
1. A real running BookNLP container (true integration tests)
2. ASGITransport for API contract tests that don't require background processing

Set BOOKNLP_TEST_URL environment variable to test against a running server.
Default: http://localhost:8001
"""

import asyncio
import os
import pytest
import pytest_asyncio
from uuid import uuid4

from httpx import AsyncClient, ASGITransport

from booknlp.api.main import create_app


# URL for real integration tests (requires running container)
BOOKNLP_TEST_URL = os.environ.get("BOOKNLP_TEST_URL", "http://localhost:8001")


async def is_server_running() -> bool:
    """Check if BookNLP server is running."""
    try:
        async with AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{BOOKNLP_TEST_URL}/v1/health")
            return resp.status_code == 200
    except Exception:
        return False


@pytest_asyncio.fixture
async def client():
    """Create test client using ASGITransport (for API contract tests)."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def live_client():
    """Create test client against real running server."""
    if not await is_server_running():
        pytest.skip(f"BookNLP server not running at {BOOKNLP_TEST_URL}")
    async with AsyncClient(base_url=BOOKNLP_TEST_URL, timeout=120.0) as client:
        yield client


@pytest.mark.asyncio
async def test_submit_job_endpoint(client):
    """Test job submission via API."""
    response = await client.post("/v1/jobs", json={
        "text": "This is a test document for analysis.",
        "book_id": "test_book",
        "model": "small",
        "pipeline": ["entity", "quote"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "submitted_at" in data
    assert data["queue_position"] == 1  # First job in queue


@pytest.mark.asyncio
async def test_get_job_status(client):
    """Test job status polling."""
    # Submit a job
    submit_response = await client.post("/v1/jobs", json={
        "text": "Test text for status check",
        "book_id": "status_test"
    })
    job_data = submit_response.json()
    job_id = job_data["job_id"]
    
    # Check status
    status_response = await client.get(f"/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["pending", "running", "completed"]
    assert 0 <= status_data["progress"] <= 100


@pytest.mark.asyncio
async def test_get_job_result(live_client):
    """Test job result retrieval against real running server.
    
    This is a true integration test that requires the BookNLP container to be running.
    Skipped automatically if server is not available.
    """
    # Submit a job
    submit_response = await live_client.post("/v1/jobs", json={
        "text": "Test text for result retrieval.",
        "book_id": "result_test"
    })
    assert submit_response.status_code == 200
    job_data = submit_response.json()
    job_id = job_data["job_id"]
    
    # Wait for completion (polling) - allow up to 60s for processing
    max_attempts = 120
    for _ in range(max_attempts):
        status_response = await live_client.get(f"/v1/jobs/{job_id}")
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"Job failed: {status_data.get('error_message')}")
        
        await asyncio.sleep(0.5)
    else:
        pytest.fail("Job did not complete in time")
    
    # Get result
    result_response = await live_client.get(f"/v1/jobs/{job_id}/result")
    assert result_response.status_code == 200
    
    result_data = result_response.json()
    assert result_data["job_id"] == job_id
    assert result_data["status"] == "completed"
    assert result_data["result"] is not None
    assert "tokens" in result_data["result"]
    assert result_data["processing_time_ms"] is not None


@pytest.mark.asyncio
async def test_get_nonexistent_job(client):
    """Test retrieving a non-existent job."""
    fake_id = str(uuid4())
    response = await client.get(f"/v1/jobs/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancel_pending_job(client):
    """Test cancelling a pending job."""
    # Submit a job
    submit_response = await client.post("/v1/jobs", json={
        "text": "Test job to cancel",
        "book_id": "cancel_test"
    })
    job_data = submit_response.json()
    job_id = job_data["job_id"]
    
    # Cancel immediately (should still be pending)
    cancel_response = await client.delete(f"/v1/jobs/{job_id}")
    assert cancel_response.status_code == 200
    
    cancel_data = cancel_response.json()
    assert cancel_data["status"] == "cancelled"
    
    # Verify job status
    status_response = await client.get(f"/v1/jobs/{job_id}")
    status_data = status_response.json()
    assert status_data["status"] == "failed"
    assert "cancelled" in status_data["error_message"]


@pytest.mark.asyncio
async def test_queue_stats_endpoint(client):
    """Test queue statistics endpoint."""
    response = await client.get("/v1/jobs/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert "total_jobs" in stats
    assert "queue_size" in stats
    assert "max_queue_size" in stats
    assert "pending" in stats
    assert "running" in stats
    assert "completed" in stats
    assert "failed" in stats
    assert "worker_running" in stats
    assert stats["max_queue_size"] == 10
    assert stats["max_concurrent_jobs"] == 1


@pytest.mark.asyncio
async def test_large_document_submission(client):
    """Test submitting a large document."""
    # Create a large text (100KB)
    large_text = "This is a sentence. " * 2000
    
    response = await client.post("/v1/jobs", json={
        "text": large_text,
        "book_id": "large_doc",
        "model": "small"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_invalid_model_parameter(client):
    """Test invalid model parameter."""
    response = await client.post("/v1/jobs", json={
        "text": "Test text",
        "model": "invalid_model"
    })
    
    # Should still accept but will fail during processing
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_empty_text_validation(client):
    """Test empty text validation."""
    response = await client.post("/v1/jobs", json={
        "text": "",
        "book_id": "empty_test"
    })
    
    # Should fail validation
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_result_before_completion(client):
    """Test getting result before job completes."""
    # Submit a job
    submit_response = await client.post("/v1/jobs", json={
        "text": "Test text for early result",
        "book_id": "early_test"
    })
    job_data = submit_response.json()
    job_id = job_data["job_id"]
    
    # Try to get result immediately
    result_response = await client.get(f"/v1/jobs/{job_id}/result")
    assert result_response.status_code == 425  # Too Early
    
    detail = result_response.json()["detail"]
    assert "not yet completed" in detail.lower()


@pytest.mark.asyncio
async def test_concurrent_job_submission(client):
    """Test submitting multiple jobs concurrently."""
    # Submit 3 jobs concurrently (fewer to avoid queue overflow from other tests)
    tasks = []
    for i in range(3):
        task = client.post("/v1/jobs", json={
            "text": f"Concurrent test job {i}",
            "book_id": f"concurrent_{i}"
        })
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    # Jobs should either succeed (200) or be rejected due to queue full (503)
    # At least some should succeed
    successful = []
    rejected = []
    for response in responses:
        if response.status_code == 200:
            data = response.json()
            assert "queue_position" in data
            assert data["queue_position"] >= 1
            successful.append(data)
        elif response.status_code == 503:
            rejected.append(response)
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    # At least one job should have been accepted
    assert len(successful) >= 1, "At least one job should be accepted"
    
    # Queue positions among successful jobs should be unique
    positions = [s["queue_position"] for s in successful]
    assert len(positions) == len(set(positions)), "Queue positions should be unique"
