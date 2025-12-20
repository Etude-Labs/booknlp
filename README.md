# BookNLP

BookNLP is a natural language processing pipeline that scales to books and other long documents (in English), including:

* Part-of-speech tagging
* Dependency parsing
* Entity recognition
* Character name clustering (e.g., "Tom", "Tom Sawyer", "Mr. Sawyer", "Thomas Sawyer" -> TOM_SAWYER) and coreference resolution
* Quotation speaker identification
* Supersense tagging (e.g., "animal", "artifact", "body", "cognition", etc.)
* Event tagging
* Referential gender inference (TOM_SAWYER -> he/him/his)

BookNLP ships with two models, both with identical architectures but different underlying BERT sizes.  The larger and more accurate `big` model is fit for GPUs and multi-core computers; the faster `small` model is more appropriate for personal computers.  See the table below for a comparison of the difference, both in terms of overall speed and in accuracy for the tasks that BookNLP performs.


| |Small|Big|
|---|---|---|
Entity tagging (F1)|88.2|90.0|
Supersense tagging (F1)|73.2|76.2|
Event tagging (F1)|70.6|74.1|
Coreference resolution (Avg. F1)|76.4|79.0|
Speaker attribution (B3)|86.4|89.9|
CPU time, 2019 MacBook Pro (mins.)*|3.6|15.4|
CPU time, 10-core server (mins.)*|2.4|5.2|
GPU time, Titan RTX (mins.)*|2.1|2.2|

*timings measure speed to run BookNLP on a sample book of *The Secret Garden* (99K tokens).   To explore running BookNLP in Google Colab on a GPU, see [this notebook](https://colab.research.google.com/drive/1c9nlqGRbJ-FUP2QJe49h21hB4kUXdU_k?usp=sharing).

## REST API

BookNLP now provides a REST API for processing text asynchronously with production-ready features:

- **Authentication**: API key-based authentication
- **Rate Limiting**: Configurable per-endpoint limits
- **Async Processing**: Submit jobs and poll for results
- **Metrics**: Prometheus metrics for monitoring
- **Health Checks**: Liveness and readiness endpoints

### Quick Start

```bash
# Start the API server
docker run -p 8000:8000 \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-secret-key \
  booknlp:latest

# Submit a job
curl -X POST "http://localhost:8000/v1/jobs" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document.",
    "book_id": "test-book",
    "model": "small",
    "pipeline": ["entities", "quotes"]
  }'

# Check job status
curl -X GET "http://localhost:8000/v1/jobs/{job_id}" \
  -H "X-API-Key: your-secret-key"

# Get results
curl -X GET "http://localhost:8000/v1/jobs/{job_id}/result" \
  -H "X-API-Key: your-secret-key"
```

## Installation

### Option 1: Docker (Recommended)

The easiest way to use BookNLP is via Docker with the pre-built REST API:

#### CPU Version

```bash
# Pull the image
docker pull booknlp:cpu

# Run the API server
docker run -p 8000:8000 \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-secret-key \
  booknlp:cpu

# Or use docker-compose
docker compose up
```

#### GPU Version

```bash
# Pull the GPU image
docker pull booknlp:gpu

# Run with GPU support
docker run --gpus all -p 8000:8000 \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-secret-key \
  booknlp:gpu
```

### Option 2: Python Package

```bash
# Install from PyPI
pip install booknlp-api

# Run the server
booknlp-api serve --host 0.0.0.0 --port 8000
```

## API Reference

### Authentication

Set `BOOKNLP_AUTH_REQUIRED=true` and `BOOKNLP_API_KEY=your-secret-key` to enable authentication. Include the key in requests:

```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8000/v1/jobs
```

### Endpoints

#### Submit Job
```http
POST /v1/jobs
Content-Type: application/json
X-API-Key: your-secret-key

{
  "text": "Text to analyze",
  "book_id": "unique-identifier",
  "model": "small|big",
  "pipeline": ["entities", "quotes", "supersense", "events"]
}
```

#### Get Job Status
```http
GET /v1/jobs/{job_id}
X-API-Key: your-secret-key
```

#### Get Job Result
```http
GET /v1/jobs/{job_id}/result
X-API-Key: your-secret-key
```

#### Cancel Job
```http
DELETE /v1/jobs/{job_id}
X-API-Key: your-secret-key
```

#### Queue Statistics
```http
GET /v1/jobs/stats
X-API-Key: your-secret-key
```

#### Health Checks
```http
GET /v1/health  # Liveness (no auth required)
GET /v1/ready   # Readiness (no auth required)
```

#### Metrics
```http
GET /metrics  # Prometheus metrics (no auth required)
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_AUTH_REQUIRED` | `false` | Enable API key authentication |
| `BOOKNLP_API_KEY` | - | API key for authentication |
| `BOOKNLP_RATE_LIMIT` | - | Rate limit (e.g., "10/minute") |
| `BOOKNLP_METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `BOOKNLP_SHUTDOWN_GRACE_PERIOD` | `30` | Graceful shutdown period (seconds) |

## Deployment

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  booknlp:
    image: booknlp:latest
    ports:
      - "8000:8000"
    environment:
      - BOOKNLP_AUTH_REQUIRED=true
      - BOOKNLP_API_KEY=${BOOKNLP_API_KEY}
      - BOOKNLP_RATE_LIMIT=10/minute
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: booknlp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: booknlp
  template:
    metadata:
      labels:
        app: booknlp
    spec:
      containers:
      - name: booknlp
        image: booknlp:latest
        ports:
        - containerPort: 8000
        env:
        - name: BOOKNLP_AUTH_REQUIRED
          value: "true"
        - name: BOOKNLP_API_KEY
          valueFrom:
            secretKeyRef:
              name: booknlp-secrets
              key: api-key
        resources:
          requests:
            cpu: 1
            memory: 2Gi
          limits:
            cpu: 2
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /v1/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: booknlp
spec:
  selector:
    app: booknlp
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'booknlp'
    static_configs:
      - targets: ['booknlp:8000']
    metrics_path: /metrics
    scrape_interval: 15s
```

### Grafana Dashboard

Key metrics to monitor:
- `http_requests_total` - Request count by endpoint and status
- `http_request_duration_seconds` - Request latency
- `booknlp_job_queue_size` - Queue depth
- `booknlp_jobs_submitted_total` - Jobs submitted
- `booknlp_jobs_completed_total` - Jobs completed

## Testing

### End-to-End Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_job_flow_e2e.py::TestJobFlowE2E::test_full_job_flow_with_auth -v
```

### Load Testing

```bash
cd tests/load
docker-compose up  # Runs 100 users for 5 minutes
```

### Security Scanning

```bash
cd tests/security
./run_scan.sh
```

## Examples

### Python Client

```python
import asyncio
import httpx

async def analyze_text():
    async with httpx.AsyncClient() as client:
        # Submit job
        response = await client.post(
            "http://localhost:8000/v1/jobs",
            headers={"X-API-Key": "your-secret-key"},
            json={
                "text": "The quick brown fox jumps over the lazy dog.",
                "book_id": "example",
                "model": "small",
                "pipeline": ["entities", "quotes"]
            }
        )
        job_id = response.json()["job_id"]
        
        # Poll for completion
        while True:
            response = await client.get(
                f"http://localhost:8000/v1/jobs/{job_id}",
                headers={"X-API-Key": "your-secret-key"}
            )
            status = response.json()["status"]
            
            if status == "completed":
                break
            elif status == "failed":
                raise Exception("Job failed")
            
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(
            f"http://localhost:8000/v1/jobs/{job_id}/result",
            headers={"X-API-Key": "your-secret-key"}
        )
        
        return response.json()["result"]

# Run the analysis
result = asyncio.run(analyze_text())
print(f"Found {len(result['entities'])} entities")
```

### Batch Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_documents(documents):
    """Process multiple documents concurrently."""
    semaphore = asyncio.Semaphore(5)  # Limit concurrent jobs
    
    async def process_single(doc):
        async with semaphore:
            # Submit and wait for job
            # ... (see previous example)
            pass
    
    tasks = [process_single(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

## Troubleshooting

### Common Issues

1. **Job Timeout**
   - Check GPU memory usage
   - Reduce concurrent jobs
   - Use smaller model

2. **Rate Limited**
   - Check `X-RateLimit-*` headers
   - Increase rate limit if needed
   - Implement client-side throttling

3. **Authentication Failed**
   - Verify `BOOKNLP_API_KEY` is set
   - Check header format: `X-API-Key`
   - Ensure key matches exactly

### Debug Mode

```bash
# Enable debug logging
export BOOKNLP_LOG_LEVEL=debug
booknlp-api serve --log-level debug
```

### Health Checks

```bash
# Check if service is running
curl http://localhost:8000/v1/health

# Check if models are loaded
curl http://localhost:8000/v1/ready

# Check metrics
curl http://localhost:8000/metrics
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
