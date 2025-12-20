# Load Testing

This directory contains load testing configuration for the BookNLP API using Locust.

## Requirements

- Python 3.8+
- Locust: `pip install locust`
- Or use Docker: `docker-compose up`

## Running Load Tests

### Option 1: Using Docker (Recommended)

```bash
cd tests/load
docker-compose up
```

This will:
- Start the BookNLP API with load testing configuration
- Run Locust with 100 concurrent users for 5 minutes
- Generate reports in the `reports/` directory

### Option 2: Using Local API

1. Start the BookNLP API:
```bash
export BOOKNLP_AUTH_REQUIRED=true
export BOOKNLP_API_KEY=load-test-key
uvicorn booknlp.api.main:app --host 0.0.0.0 --port 8000
```

2. Run the load test:
```bash
cd tests/load
./run_load_test.sh
```

## Configuration

Environment variables:
- `API_URL`: Target API URL (default: http://localhost:8000)
- `API_KEY`: API key for authentication (default: load-test-key)
- `USERS`: Number of concurrent users (default: 100)
- `SPAWN_RATE`: Users spawned per second (default: 10)
- `RUN_TIME`: Test duration in seconds (default: 300)

## Test Scenarios

The load test simulates realistic usage patterns:

- **Job Submission** (10%): Submit new text analysis jobs
- **Status Checks** (20%): Poll job status
- **Result Retrieval** (5%): Get completed job results
- **Queue Stats** (15%): Check queue statistics
- **Health Checks** (30%): Health/ready endpoints (no auth)
- **Metrics** (10%): Metrics endpoint (no auth)
- **Job Cancellation** (5%): Cancel pending jobs

## Acceptance Criteria

The load test passes if:
- 100 concurrent users for 5 minutes
- 0 errors (excluding rate limiting)
- P99 latency < 120 seconds
- Success rate = 100%

## Reports

After completion, you'll find:
- `load_test_report.html`: Interactive HTML report
- `load_test_results.csv`: Raw timing data
- `load_test_results_stats.csv`: Summary statistics

## Troubleshooting

### High Error Rate
- Check if API is running: `curl http://localhost:8000/v1/health`
- Verify API key is correct
- Check rate limiting settings

### Low Throughput
- Increase rate limit: `BOOKNLP_RATE_LIMIT=1000/minute`
- Check GPU availability
- Monitor queue size

### High Latency
- Check GPU memory usage
- Monitor job queue backlog
- Consider reducing concurrent users
