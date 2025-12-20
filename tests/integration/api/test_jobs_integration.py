"""Integration tests for async job API endpoints."""

import asyncio
import pytest
from uuid import uuid4

from httpx import AsyncClient

from booknlp.api.main import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
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
async def test_get_job_result(client):
    """Test job result retrieval."""
    # Submit a job
    submit_response = await client.post("/v1/jobs", json={
        "text": "Test text for result retrieval",
        "book_id": "result_test"
    })
    job_data = submit_response.json()
    job_id = job_data["job_id"]
    
    # Wait for completion (polling)
    max_attempts = 30
    for _ in range(max_attempts):
        status_response = await client.get(f"/v1/jobs/{job_id}")
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"Job failed: {status_data.get('error_message')}")
        
        await asyncio.sleep(0.1)
    else:
        pytest.fail("Job did not complete in time")
    
    # Get result
    result_response = await client.get(f"/v1/jobs/{job_id}/result")
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
    # Submit 5 jobs concurrently
    tasks = []
    for i in range(5):
        task = client.post("/v1/jobs", json={
            "text": f"Concurrent test job {i}",
            "book_id": f"concurrent_{i}"
        })
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    for i, response in enumerate(responses):
        assert response.status_code == 200
        data = response.json()
        assert data["queue_position"] == i + 1  # Position in queue
