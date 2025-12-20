# Async Processing API Documentation

## Overview

The BookNLP API supports asynchronous processing for large documents that would timeout in synchronous mode. The async API allows you to submit jobs, poll their status, and retrieve results when ready.

## Key Features

- **Job Queue**: FIFO queue with configurable size (default: 10 jobs)
- **Single-Task Processing**: Only one job processes at a time due to GPU constraints
- **Progress Tracking**: Real-time progress updates (0-100%)
- **Job Expiration**: Completed jobs expire after 1 hour
- **Thread-Safe**: Non-blocking async operations

## API Endpoints

### Submit Job

Submit a new text analysis job to the processing queue.

```http
POST /v1/jobs
Content-Type: application/json

{
    "text": "Your document text here...",
    "book_id": "optional-document-id",
    "model": "small",
    "pipeline": ["entity", "quote", "supersense", "event", "coref"]
}
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "submitted_at": "2025-01-20T10:00:00Z",
    "queue_position": 1
}
```

### Get Job Status

Check the status and progress of a submitted job.

```http
GET /v1/jobs/{job_id}
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "progress": 45.0,
    "submitted_at": "2025-01-20T10:00:00Z",
    "started_at": "2025-01-20T10:00:05Z",
    "completed_at": null,
    "error_message": null,
    "queue_position": null
}
```

**Status Values:**
- `pending`: Job is in queue waiting to process
- `running`: Job is currently processing
- `completed`: Job finished successfully
- `failed`: Job failed with an error
- `expired`: Job results have expired (after 1 hour)

### Get Job Result

Retrieve the results of a completed job.

```http
GET /v1/jobs/{job_id}/result
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": {
        "tokens": [...],
        "entities": [...],
        "quotes": [...],
        "characters": [...],
        "events": [...],
        "supersenses": [...]
    },
    "submitted_at": "2025-01-20T10:00:00Z",
    "started_at": "2025-01-20T10:00:05Z",
    "completed_at": "2025-01-20T10:02:30Z",
    "processing_time_ms": 145000,
    "token_count": 50000
}
```

### Cancel Job

Cancel a pending job (cannot cancel jobs already running).

```http
DELETE /v1/jobs/{job_id}
```

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled"
}
```

### Get Queue Statistics

Get current statistics about the job queue.

```http
GET /v1/jobs/stats
```

**Response:**
```json
{
    "total_jobs": 5,
    "queue_size": 2,
    "max_queue_size": 10,
    "pending": 2,
    "running": 1,
    "completed": 2,
    "failed": 0,
    "worker_running": true,
    "max_document_size": 5000000,
    "job_ttl_seconds": 3600,
    "max_concurrent_jobs": 1
}
```

## Usage Examples

### Python Example

```python
import asyncio
import httpx

async def process_document_async():
    async with httpx.AsyncClient() as client:
        # Submit job
        response = await client.post("http://localhost:8000/v1/jobs", json={
            "text": "Your large document text here...",
            "book_id": "my-book",
            "model": "big"
        })
        job_data = response.json()
        job_id = job_data["job_id"]
        
        # Poll for completion
        while True:
            status_response = await client.get(f"http://localhost:8000/v1/jobs/{job_id}")
            status_data = status_response.json()
            
            print(f"Progress: {status_data['progress']}%")
            
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                print(f"Job failed: {status_data['error_message']}")
                return
            
            await asyncio.sleep(2)
        
        # Get results
        result_response = await client.get(f"http://localhost:8000/v1/jobs/{job_id}/result")
        result_data = result_response.json()
        
        # Process results
        entities = result_data["result"]["entities"]
        print(f"Found {len(entities)} entities")

# Run the async processing
asyncio.run(process_document_async())
```

### JavaScript Example

```javascript
async function processDocumentAsync(text) {
    const baseUrl = 'http://localhost:8000/v1';
    
    // Submit job
    const submitResponse = await fetch(`${baseUrl}/jobs`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            book_id: 'my-book',
            model: 'small'
        })
    });
    
    const jobData = await submitResponse.json();
    const jobId = jobData.job_id;
    
    // Poll for completion
    let statusData;
    while (true) {
        const statusResponse = await fetch(`${baseUrl}/jobs/${jobId}`);
        statusData = await statusResponse.json();
        
        console.log(`Progress: ${statusData.progress}%`);
        
        if (statusData.status === 'completed') {
            break;
        } else if (statusData.status === 'failed') {
            console.error(`Job failed: ${statusData.error_message}`);
            return;
        }
        
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Get results
    const resultResponse = await fetch(`${baseUrl}/jobs/${jobId}/result`);
    const resultData = await resultResponse.json();
    
    return resultData.result;
}

// Usage
processDocumentAsync(largeDocumentText)
    .then(result => {
        console.log(`Found ${result.entities.length} entities`);
    })
    .catch(error => {
        console.error('Processing failed:', error);
    });
```

### cURL Example

```bash
# Submit job
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/jobs \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Your document text here...",
        "book_id": "curl-test"
    }')

# Extract job ID
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

# Poll for status
while true; do
    STATUS=$(curl -s http://localhost:8000/v1/jobs/$JOB_ID)
    STATUS_VALUE=$(echo $STATUS | jq -r '.status')
    PROGRESS=$(echo $STATUS | jq -r '.progress')
    
    echo "Progress: $PROGRESS%"
    
    if [ "$STATUS_VALUE" = "completed" ]; then
        break
    elif [ "$STATUS_VALUE" = "failed" ]; then
        echo "Job failed"
        exit 1
    fi
    
    sleep 2
done

# Get results
curl -s http://localhost:8000/v1/jobs/$JOB_ID/result | jq .
```

## Constraints and Limits

- **Queue Size**: Maximum 10 concurrent jobs in queue
- **Document Size**: Up to 5,000,000 characters
- **Job TTL**: Results expire after 1 hour
- **Concurrent Processing**: Only 1 job processes at a time (GPU constraint)
- **Models**: Supports "small", "big", and "custom" models

## Error Handling

### Common HTTP Status Codes

- `200`: Success
- `400`: Invalid input (validation error)
- `404`: Job not found or expired
- `409`: Cannot cancel job (already running/completed)
- `425`: Job not yet completed (for result retrieval)
- `503`: Queue full or service not ready

### Error Response Format

```json
{
    "detail": "Error message describing what went wrong"
}
```

## Best Practices

1. **Use Async API for Large Documents**: Switch to async mode for documents over 10,000 characters
2. **Poll Reasonably**: Check status every 1-5 seconds, not more frequently
3. **Handle Timeouts**: Implement client-side timeouts for long-running jobs
4. **Clean Up**: Don't rely on job expiration - clean up results when done
5. **Monitor Queue**: Check `/v1/jobs/stats` before submitting to avoid queue full errors

## Migration from Sync API

To migrate from synchronous to asynchronous processing:

1. Replace direct `/v1/analyze` calls with job submission
2. Implement polling or webhook mechanism for completion
3. Handle job status and potential failures
4. Retrieve results from the separate endpoint

Example migration:

```python
# Old sync approach
response = await client.post("/v1/analyze", json={
    "text": document,
    "book_id": "my-book"
})
result = response.json()

# New async approach
job_response = await client.post("/v1/jobs", json={
    "text": document,
    "book_id": "my-book"
})
job_id = job_response.json()["job_id"]

# Wait for completion
while True:
    status = await client.get(f"/v1/jobs/{job_id}")
    if status.json()["status"] == "completed":
        break
    await asyncio.sleep(1)

# Get results
result_response = await client.get(f"/v1/jobs/{job_id}/result")
result = result_response.json()["result"]
```
