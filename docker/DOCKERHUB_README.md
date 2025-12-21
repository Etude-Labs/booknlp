# BookNLP

[![GitHub](https://img.shields.io/badge/GitHub-jahales%2Fbooknlp-blue)](https://github.com/jahales/booknlp)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/jahales/booknlp/blob/main/LICENSE)

Natural language processing pipeline for books and long documents, with a production-ready REST API.

> This is an extended fork of [BookNLP](https://github.com/dbamman/book-nlp) by David Bamman, adding Docker support, REST API, authentication, and production features.

## Quick Start

```bash
# Pull and run (CPU version)
docker run -p 8000:8000 \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-secret-key \
  etudelabs/booknlp:cpu

# Or GPU version
docker run --gpus all -p 8000:8000 \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-secret-key \
  etudelabs/booknlp:gpu
```

## Available Tags

| Tag | Description | Size |
|-----|-------------|------|
| `latest` | Latest CPU version | ~4GB |
| `cpu`, `1.0.0-cpu` | CPU version (Python 3.12) | ~4GB |
| `gpu`, `1.0.0-gpu` | GPU version (CUDA 12.4) | ~8GB |

## API Usage

### Submit a Job

```bash
curl -X POST "http://localhost:8000/v1/jobs" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alice was beginning to get very tired of sitting by her sister on the bank.",
    "book_id": "alice",
    "model": "small",
    "pipeline": ["entities", "quotes"]
  }'
```

### Check Job Status

```bash
curl -X GET "http://localhost:8000/v1/jobs/{job_id}" \
  -H "X-API-Key: your-secret-key"
```

### Get Results

```bash
curl -X GET "http://localhost:8000/v1/jobs/{job_id}/result" \
  -H "X-API-Key: your-secret-key"
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/jobs` | POST | Submit analysis job |
| `/v1/jobs/{id}` | GET | Get job status |
| `/v1/jobs/{id}/result` | GET | Get job results |
| `/v1/jobs/{id}` | DELETE | Cancel job |
| `/v1/jobs/stats` | GET | Queue statistics |
| `/v1/health` | GET | Liveness check (no auth) |
| `/v1/ready` | GET | Readiness check (no auth) |
| `/metrics` | GET | Prometheus metrics (no auth) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_AUTH_REQUIRED` | `false` | Enable API key authentication |
| `BOOKNLP_API_KEY` | - | API key for authentication |
| `BOOKNLP_RATE_LIMIT` | - | Rate limit (e.g., `10/minute`) |
| `BOOKNLP_METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `BOOKNLP_SHUTDOWN_GRACE_PERIOD` | `30` | Graceful shutdown period (seconds) |

## Docker Compose

```yaml
version: '3.8'

services:
  booknlp:
    image: etudelabs/booknlp:cpu
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
```

## NLP Features

BookNLP provides comprehensive literary text analysis:

* **Entity Recognition** - Identify characters, locations, organizations
* **Character Clustering** - Group name variants (Tom, Tom Sawyer, Mr. Sawyer → TOM_SAWYER)
* **Coreference Resolution** - Link pronouns to characters
* **Speaker Attribution** - Identify who speaks each quote
* **Supersense Tagging** - Semantic categories (person, location, cognition, etc.)
* **Event Tagging** - Identify narrative events
* **Gender Inference** - Infer character gender from context

## Model Variants

| Model | Accuracy | Speed |
|-------|----------|-------|
| `small` | Good (F1: 88.2) | Fast (~3.5 min/book on CPU) |
| `big` | Better (F1: 90.0) | Slower (~15 min/book on CPU) |

*Timings based on 99K token book (The Secret Garden)*

## Links

* **GitHub**: https://github.com/jahales/booknlp
* **Original BookNLP**: https://github.com/dbamman/book-nlp
* **Documentation**: https://github.com/jahales/booknlp#readme

## License

MIT License

Original BookNLP © 2021 David Bamman  
REST API and Docker extensions © 2024 Etude Labs
