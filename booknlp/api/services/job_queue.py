"""Job queue service for async BookNLP processing."""

import asyncio
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from uuid import UUID

from booknlp.api.schemas.job_schemas import Job, JobRequest, JobStatus


class JobQueue:
    """In-memory job queue with single worker for GPU constraint compliance."""
    
    def __init__(self, max_queue_size: int = 10, job_ttl_seconds: int = 3600):
        """Initialize job queue.
        
        Args:
            max_queue_size: Maximum number of jobs in queue
            job_ttl_seconds: Time-to-live for completed jobs in seconds
        """
        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=max_queue_size)
        self._jobs: dict[UUID, Job] = {}  # Job storage by ID
        self._max_queue_size = max_queue_size
        self._job_ttl = timedelta(seconds=job_ttl_seconds)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
        self._progress_callback: Optional[Callable[[UUID, float], None]] = None
        
    async def start(self, processor: Callable[[JobRequest, Callable[[float], None]], dict[str, Any]]) -> None:
        """Start the background worker.
        
        Args:
            processor: Async function that processes jobs and accepts progress callback
        """
        if self._running:
            return
            
        self._running = True
        self._processor = processor
        self._worker_task = asyncio.create_task(self._worker())
        
    async def stop(self, grace_period: float = 30.0) -> None:
        """Stop the background worker gracefully.
        
        Args:
            grace_period: Seconds to wait for current job to finish
        """
        self._running = False
        
        if self._worker_task:
            # Wait for current job to finish or timeout
            try:
                await asyncio.wait_for(
                    self._worker_task,
                    timeout=grace_period
                )
            except asyncio.TimeoutError:
                # Grace period expired, force cancel
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    # Intentionally not re-raising - we're in shutdown
                    pass
            except asyncio.CancelledError:
                # Task was cancelled, that's fine during shutdown
                # Intentionally not re-raising to allow clean shutdown
                pass
                
    async def submit_job(self, request: JobRequest) -> Job:
        """Submit a new job to the queue.
        
        Args:
            request: Job processing request
            
        Returns:
            Created job instance
            
        Raises:
            asyncio.QueueFull: If queue is full
        """
        job = Job(request=request)
        
        async with self._lock:
            self._jobs[job.job_id] = job
            
        await self._queue.put(job)
        return job
        
    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job instance if found, None otherwise
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            
            # Clean up expired jobs
            if job and self._is_expired(job):
                job.status = JobStatus.EXPIRED
                del self._jobs[job_id]
                return None
                
            return job
            
    async def update_progress(self, job_id: UUID, progress: float) -> None:
        """Update job progress.
        
        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == JobStatus.RUNNING:
                job.progress = max(0.0, min(100.0, progress))
                
    def get_queue_position(self, job_id: UUID) -> Optional[int]:
        """Get position of job in queue.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Position in queue (1-based) if pending, None otherwise
        """
        # Note: This is not thread-safe but good enough for monitoring
        for i, job in enumerate(self._queue._queue):
            if job.job_id == job_id:
                return i + 1
        return None
        
    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        async with self._lock:
            total_jobs = len(self._jobs)
            pending = sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)
            running = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
            completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)
            
            return {
                "total_jobs": total_jobs,
                "queue_size": self._queue.qsize(),
                "max_queue_size": self._max_queue_size,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "worker_running": self._running,
            }
            
    async def _worker(self) -> None:
        """Background worker that processes jobs sequentially."""
        while self._running:
            try:
                # Wait for a job with timeout to allow checking _running flag
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                
                async with self._lock:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now(timezone.utc)
                    
                try:
                    # Process the job with progress callback
                    job_id = job.job_id  # Bind before closure
                    
                    def progress_callback(progress: float) -> None:
                        # job_id is bound from outer scope
                        progress_task = asyncio.create_task(self.update_progress(job_id, progress))
                        # Save task reference to prevent garbage collection
                        _ = progress_task
                    
                    # Process the job
                    result = await self._processor(job.request, progress_callback)
                    
                    async with self._lock:
                        job.status = JobStatus.COMPLETED
                        job.result = result
                        job.completed_at = datetime.now(timezone.utc)
                        job.progress = 100.0
                        
                        # Calculate processing time
                        if job.started_at:
                            job.processing_time_ms = int(
                                (job.completed_at - job.started_at).total_seconds() * 1000
                            )
                            
                        # Extract token count from result if available
                        if result and "tokens" in result:
                            job.token_count = len(result["tokens"])
                            
                except Exception as e:
                    async with self._lock:
                        job.status = JobStatus.FAILED
                        job.error_message = str(e)
                        job.completed_at = datetime.now(timezone.utc)
                        
                self._queue.task_done()
                
            except asyncio.TimeoutError:
                # No job available, continue loop
                continue
            except Exception as e:
                # Log error but continue worker
                print(f"Worker error: {e}")
                continue
                
        # Clean up expired jobs on shutdown
        await self._cleanup_expired()
        
    def _is_expired(self, job: Job) -> bool:
        """Check if a job has expired.
        
        Args:
            job: Job to check
            
        Returns:
            True if job is expired
        """
        if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return False
            
        if not job.completed_at:
            return True
            
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._job_ttl_seconds)
        return job.completed_at < cutoff
        
    async def _cleanup_expired(self) -> None:
        """Remove expired jobs from storage."""
        async with self._lock:
            expired_ids = [
                job_id for job_id, job in self._jobs.items()
                if self._is_expired(job)
            ]
            
            for job_id in expired_ids:
                del self._jobs[job_id]


# Global job queue instance
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get the global job queue instance.
    
    Returns:
        The singleton JobQueue instance.
    """
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue


async def initialize_job_queue(
    processor: Callable[[JobRequest, Callable[[float], None]], dict[str, Any]],
    max_queue_size: int = 10,
    job_ttl_seconds: int = 3600,
) -> JobQueue:
    """Initialize and start the global job queue.
    
    Args:
        processor: Async function that processes jobs
        max_queue_size: Maximum number of jobs in queue
        job_ttl_seconds: Time-to-live for completed jobs
        
    Returns:
        The initialized JobQueue instance
    """
    global _job_queue
    _job_queue = JobQueue(max_queue_size=max_queue_size, job_ttl_seconds=job_ttl_seconds)
    await _job_queue.start(processor)
    return _job_queue
