"""Job management endpoints for async processing."""

from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from booknlp.api.schemas.job_schemas import (
    JobRequest,
    JobResponse,
    JobStatusResponse,
    JobResultResponse,
    JobStatus,
    JOB_NOT_FOUND_MSG,
)
from booknlp.api.services.job_queue import get_job_queue
from booknlp.api.services.async_processor import get_async_processor
from booknlp.api.dependencies import verify_api_key
from booknlp.api.rate_limit import rate_limit

router = APIRouter(tags=["Jobs"])


@router.post(
    "/jobs",
    response_model=JobResponse,
    summary="Submit job",
    description="Submit a new text analysis job to the processing queue.",
    responses={
        200: {"description": "Job submitted successfully"},
        400: {"description": "Invalid input"},
        503: {"description": "Queue full or service not ready"},
    },
)
@rate_limit("10/minute")
async def submit_job(
    request: JobRequest,
    api_key: str = Depends(verify_api_key)
) -> JobResponse:
    """Submit a new job for async processing.
    
    Args:
        request: Job submission request with text and options
        
    Returns:
        Job submission response with job ID and status
        
    Raises:
        HTTPException: If queue is full or validation fails
    """
    job_queue = get_job_queue()
    
    # Check queue capacity
    stats = await job_queue.get_queue_stats()
    if stats["queue_size"] >= stats["max_queue_size"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processing queue is full. Please try again later.",
        )
    
    try:
        # Submit job to queue
        job = await job_queue.submit_job(request)
        
        # Get queue position if pending
        queue_position = None
        if job.status == JobStatus.PENDING:
            queue_position = job_queue.get_queue_position(job.job_id)
        
        return JobResponse(
            job_id=job.job_id,
            status=job.status,
            submitted_at=job.submitted_at,
            queue_position=queue_position,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@router.get(
    "/jobs/stats",
    summary="Get queue statistics",
    description="Get current statistics about the job queue and processing status.",
    responses={
        200: {"description": "Statistics retrieved successfully"},
    },
)
@rate_limit("30/minute")
async def get_queue_stats(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get queue statistics.
    
    Returns:
        Dictionary with queue statistics
    """
    job_queue = get_job_queue()
    stats = await job_queue.get_queue_stats()
    
    # Add additional info
    stats.update({
        "max_document_size": 5000000,  # 5M characters
        "job_ttl_seconds": 3600,  # 1 hour
        "max_concurrent_jobs": 1,  # GPU constraint
    })
    
    return stats


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status and progress of a submitted job.",
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"description": "Job not found or expired"},
    },
)
@rate_limit("60/minute")
async def get_job_status(
    job_id: UUID,
    api_key: str = Depends(verify_api_key)
) -> JobStatusResponse:
    """Get the current status of a job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Current job status and progress
        
    Raises:
        HTTPException: If job not found
    """
    job_queue = get_job_queue()
    
    # Retrieve job
    job = await job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=JOB_NOT_FOUND_MSG,
        )
    
    # Get queue position if pending
    queue_position = None
    if job.status == JobStatus.PENDING:
        queue_position = job_queue.get_queue_position(job.job_id)
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        submitted_at=job.submitted_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        queue_position=queue_position,
    )


@router.get(
    "/jobs/{job_id}/result",
    response_model=JobResultResponse,
    summary="Get job result",
    description="Retrieve the results of a completed job.",
    responses={
        200: {"description": "Job results retrieved successfully"},
        404: {"description": "Job not found or expired"},
        425: {"description": "Job not yet completed"},
    },
)
@rate_limit("30/minute")
async def get_job_result(
    job_id: UUID,
    api_key: str = Depends(verify_api_key)
) -> JobResultResponse:
    """Get the results of a completed job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Job results if completed
        
    Raises:
        HTTPException: If job not found, expired, or not completed
    """
    job_queue = get_job_queue()
    
    # Retrieve job
    job = await job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=JOB_NOT_FOUND_MSG,
        )
    
    # Check if job is completed
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail=f"Job not yet completed. Current status: {job.status.value}",
        )
    
    return JobResultResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        submitted_at=job.submitted_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        processing_time_ms=job.processing_time_ms,
        token_count=job.token_count,
    )


@router.delete(
    "/jobs/{job_id}",
    summary="Cancel job",
    description="Cancel a pending job. Cannot cancel jobs that are already running.",
    responses={
        200: {"description": "Job cancelled successfully"},
        404: {"description": "Job not found or expired"},
        409: {"description": "Job already running or completed"},
    },
)
@rate_limit("20/minute")
async def cancel_job(
    job_id: UUID,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Cancel a pending job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Cancellation confirmation
        
    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    job_queue = get_job_queue()
    
    # Retrieve job
    job = await job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=JOB_NOT_FOUND_MSG,
        )
    
    # Can only cancel pending jobs
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in status: {job.status.value}",
        )
    
    # Update job status
    job.status = JobStatus.FAILED
    job.error_message = "Job cancelled by user"
    job.completed_at = job.submitted_at
    
    return {"job_id": str(job_id), "status": "cancelled"}
