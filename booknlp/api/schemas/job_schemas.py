"""Job-related schemas for async processing."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

# Constants for repeated field descriptions
UNIQUE_JOB_ID_DESC = "Unique job identifier"
CURRENT_STATUS_DESC = "Current job status"
SUBMISSION_TIME_DESC = "Job submission timestamp"
JOB_NOT_FOUND_MSG = "Job not found or has expired"


class JobStatus(str, Enum):
    """Status of a processing job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class JobRequest(BaseModel):
    """Request to submit a new job."""
    text: str = Field(..., min_length=1, max_length=5000000, description="Text to analyze")
    book_id: Optional[str] = Field(None, description="Identifier for the document")
    model: str = Field("small", description="Model size: small, big, or custom")
    pipeline: list[str] = Field(
        default=["entity", "quote", "supersense", "event", "coref"],
        description="Pipeline components to run"
    )
    custom_model_path: Optional[str] = Field(
        None, description="Path for custom model (only when model='custom')"
    )


class JobResponse(BaseModel):
    """Response after job submission."""
    job_id: UUID = Field(..., description=UNIQUE_JOB_ID_DESC)
    status: JobStatus = Field(..., description=CURRENT_STATUS_DESC)
    submitted_at: datetime = Field(..., description=SUBMISSION_TIME_DESC)
    queue_position: Optional[int] = Field(
        None, description="Position in queue if pending"
    )


class JobStatusResponse(BaseModel):
    """Response for job status polling."""
    job_id: UUID = Field(..., description=UNIQUE_JOB_ID_DESC)
    status: JobStatus = Field(..., description=CURRENT_STATUS_DESC)
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    submitted_at: datetime = Field(..., description=SUBMISSION_TIME_DESC)
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    queue_position: Optional[int] = Field(
        None, description="Position in queue if pending"
    )


class JobResultResponse(BaseModel):
    """Response for completed job results."""
    job_id: UUID = Field(..., description=UNIQUE_JOB_ID_DESC)
    status: JobStatus = Field(..., description=CURRENT_STATUS_DESC)
    result: Optional[dict[str, Any]] = Field(
        None, description="Analysis results if completed"
    )
    submitted_at: datetime = Field(..., description=SUBMISSION_TIME_DESC)
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    token_count: Optional[int] = Field(None, description="Number of tokens processed")


class Job(BaseModel):
    """Internal job representation."""
    job_id: UUID = Field(default_factory=uuid4)
    request: JobRequest
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    token_count: Optional[int] = None

    model_config = ConfigDict(
        ser_json_timedelta="iso8601",
    )
