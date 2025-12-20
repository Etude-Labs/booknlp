"""Tests for job queue service."""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from booknlp.api.schemas.job_schemas import JobRequest, JobStatus
from booknlp.api.services.job_queue import JobQueue


@pytest.fixture
def job_queue():
    """Create a test job queue."""
    queue = JobQueue(max_queue_size=3, job_ttl_seconds=1)
    
    # Mock processor that simulates work
    async def mock_processor(request: JobRequest, progress_callback):
        # Simulate processing with progress updates
        for i in range(0, 101, 20):
            progress_callback(i)
            await asyncio.sleep(0.01)
        return {"tokens": [{"word": "test"}], "entities": []}
    
    yield queue, mock_processor


@pytest.mark.asyncio
async def test_submit_job(job_queue):
    """Test job submission."""
    queue, mock_processor = job_queue
    await queue.start(mock_processor)
    
    request = JobRequest(text="Test text", book_id="test")
    job = await queue.submit_job(request)
    
    assert job.status == JobStatus.PENDING
    assert job.request.text == "Test text"
    assert job.request.book_id == "test"
    assert job.submitted_at is not None
    
    await queue.stop()


@pytest.mark.asyncio
async def test_get_job(job_queue):
    """Test job retrieval."""
    queue, mock_processor = job_queue
    await queue.start(mock_processor)
    
    request = JobRequest(text="Test text")
    submitted_job = await queue.submit_job(request)
    
    # Retrieve job
    retrieved_job = await queue.get_job(submitted_job.job_id)
    assert retrieved_job is not None
    assert retrieved_job.job_id == submitted_job.job_id
    assert retrieved_job.status == JobStatus.PENDING
    
    await queue.stop()


@pytest.mark.asyncio
async def test_job_processing(job_queue):
    """Test job processing with progress."""
    queue, mock_processor = job_queue
    await queue.start(mock_processor)
    
    request = JobRequest(text="Test text")
    job = await queue.submit_job(request)
    
    # Wait for processing to complete
    await asyncio.sleep(0.2)
    
    # Check job completed
    completed_job = await queue.get_job(job.job_id)
    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.progress >= 99.0  # Allow for floating point precision
    assert completed_job.result is not None
    assert completed_job.processing_time_ms is not None
    
    await queue.stop()


@pytest.mark.asyncio
async def test_queue_position(job_queue):
    """Test queue position tracking."""
    queue, mock_processor = job_queue
    await queue.start(mock_processor)
    
    # Submit multiple jobs
    jobs = []
    for i in range(3):
        request = JobRequest(text=f"Test text {i}")
        job = await queue.submit_job(request)
        jobs.append(job)
    
    # Check positions
    assert queue.get_queue_position(jobs[0].job_id) == 1
    assert queue.get_queue_position(jobs[1].job_id) == 2
    assert queue.get_queue_position(jobs[2].job_id) == 3
    
    await queue.stop()


@pytest.mark.asyncio
async def test_queue_full():
    """Test queue full error."""
    queue = JobQueue(max_queue_size=1, job_ttl_seconds=1)
    
    async def mock_processor(request, progress_callback):
        await asyncio.sleep(0.1)
        return {}
    
    await queue.start(mock_processor)
    
    try:
        # Fill queue
        await queue.submit_job(JobRequest(text="Test 1"))
        
        # Should fail on second submission
        with pytest.raises(asyncio.QueueFull):
            await queue.submit_job(JobRequest(text="Test 2"))
    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_job_failure():
    """Test job failure handling."""
    queue = JobQueue(max_queue_size=2, job_ttl_seconds=1)
    
    async def failing_processor(request, progress_callback):
        raise ValueError("Processing failed")
    
    await queue.start(failing_processor)
    
    try:
        request = JobRequest(text="Test text")
        job = await queue.submit_job(request)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check job failed
        failed_job = await queue.get_job(job.job_id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error_message == "Processing failed"
        assert failed_job.completed_at is not None
    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_job_expiration():
    """Test job expiration cleanup."""
    queue = JobQueue(max_queue_size=2, job_ttl_seconds=0.1)  # Very short TTL
    
    async def fast_processor(request, progress_callback):
        progress_callback(100)
        return {"tokens": []}
    
    await queue.start(fast_processor)
    
    try:
        request = JobRequest(text="Test text")
        job = await queue.submit_job(request)
        
        # Wait for job to complete and expire
        await asyncio.sleep(0.2)
        
        # Job should be expired and cleaned up
        expired_job = await queue.get_job(job.job_id)
        assert expired_job is None
    finally:
        await queue.stop()


@pytest.mark.asyncio
async def test_queue_stats(job_queue):
    """Test queue statistics."""
    # Submit jobs
    for i in range(2):
        await job_queue.submit_job(JobRequest(text=f"Test {i}"))
    
    stats = await job_queue.get_queue_stats()
    
    assert stats["total_jobs"] == 2
    assert stats["queue_size"] == 2
    assert stats["pending"] == 2
    assert stats["running"] == 0
    assert stats["completed"] == 0
    assert stats["failed"] == 0
    assert stats["worker_running"] is True


@pytest.mark.asyncio
async def test_progress_update(job_queue):
    """Test progress updates."""
    progress_updates = []
    
    def capture_progress(progress):
        progress_updates.append(progress)
    
    # Custom processor that reports progress
    async def progress_processor(request, progress_callback):
        for i in range(0, 101, 25):
            progress_callback(i)
            await asyncio.sleep(0.01)
        return {}
    
    # Replace the processor
    await job_queue.stop()
    await job_queue.start(progress_processor)
    
    request = JobRequest(text="Test text")
    job = await job_queue.submit_job(request)
    
    # Wait for completion
    await asyncio.sleep(0.2)
    
    # Check progress was reported
    completed_job = await job_queue.get_job(job.job_id)
    assert completed_job.progress >= 99.0  # Allow for floating point precision
