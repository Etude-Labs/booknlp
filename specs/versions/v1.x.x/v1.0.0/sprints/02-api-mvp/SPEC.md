---
title: "Sprint 02: API MVP - Technical Specification"
version: v0.2.0
sprint: "02"
status: draft
linked_prd: ./PRD.md
---

# SPEC: Sprint 02 — API MVP

## Overview

Implement a FastAPI-based REST API for BookNLP, providing synchronous text analysis with health/readiness endpoints and OpenAPI documentation.

## Architecture

### Project Structure

```text
booknlp/
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── analyze.py    # POST /v1/analyze
│   │   └── health.py     # GET /v1/health, /v1/ready
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── requests.py   # AnalyzeRequest
│   │   └── responses.py  # AnalyzeResponse, HealthResponse
│   └── services/
│       ├── __init__.py
│       └── nlp_service.py  # BookNLP wrapper
├── Dockerfile            # Updated with API
└── docker-compose.yml    # Updated with port mapping
```

## Interfaces

### POST /v1/analyze

**Request**:

```json
{
  "text": "Call me Ishmael. Some years ago...",
  "book_id": "moby_dick",
  "model": "small",
  "pipeline": ["entity", "quote", "supersense", "event", "coref"]
}
```

**Response**:

```json
{
  "book_id": "moby_dick",
  "model": "small",
  "processing_time_ms": 1234,
  "token_count": 150,
  "tokens": [
    {"id": 0, "word": "Call", "lemma": "call", "pos": "VB", ...}
  ],
  "entities": [
    {"id": 0, "text": "Ishmael", "type": "PER", "start": 8, "end": 15, ...}
  ],
  "quotes": [
    {"text": "...", "speaker_id": 0, "start": 0, "end": 50}
  ],
  "characters": [
    {"id": 0, "name": "Ishmael", "gender": "he/him", "mentions": 5}
  ],
  "events": [...],
  "supersenses": [...]
}
```

### GET /v1/health

**Response** (200):

```json
{"status": "ok", "timestamp": "2025-01-15T10:00:00Z"}
```

### GET /v1/ready

**Response** (200 when ready):

```json
{
  "status": "ready",
  "model_loaded": true,
  "default_model": "small",
  "available_models": ["small", "big"]
}
```

**Response** (503 when loading):

```json
{"status": "loading", "model_loaded": false}
```

### Error Responses

**400 Bad Request** (invalid input):

```json
{
  "detail": "Text cannot be empty",
  "error_code": "INVALID_INPUT"
}
```

**413 Payload Too Large** (text exceeds limit):

```json
{
  "detail": "Text exceeds maximum length of 500000 characters",
  "error_code": "PAYLOAD_TOO_LARGE"
}
```

**422 Validation Error** (Pydantic validation):

```json
{
  "detail": [{"loc": ["body", "model"], "msg": "Invalid model", "type": "value_error"}]
}
```

**500 Internal Server Error**:

```json
{
  "detail": "Processing failed",
  "error_code": "PROCESSING_ERROR",
  "request_id": "abc123"
}
```

**504 Gateway Timeout** (processing exceeds timeout):

```json
{
  "detail": "Request timed out after 300 seconds",
  "error_code": "TIMEOUT"
}
```

### Request Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max text length | 500,000 chars | ~100K words; prevents OOM |
| Request timeout | 300s | Big model on long text |
| Max concurrent requests | **1** | GPU memory constraint; see below |

### Concurrency Constraint

> **Critical**: The API processes **one request at a time** due to GPU memory constraints.

**Rationale**:
- BookNLP models consume significant GPU VRAM (2-6 GB depending on model)
- Concurrent GPU processing would cause OOM errors
- Even on CPU, concurrent processing causes memory pressure

**Implementation**:
- Single uvicorn worker (`--workers 1`)
- Requests queue automatically (FastAPI handles this)
- Return `503 Service Unavailable` with `Retry-After` header when busy (Sprint 05)

**Future (Sprint 04)**:
- Async job queue allows submitting multiple jobs
- Jobs processed sequentially by worker
- Clients poll for completion

## Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500_000)
    book_id: str = Field(default="document")
    model: Literal["small", "big", "custom"] = "small"
    pipeline: list[str] = ["entity", "quote", "supersense", "event", "coref"]
    custom_model_path: str | None = Field(default=None, description="Path for custom model")

class AnalyzeResponse(BaseModel):
    book_id: str
    model: str
    processing_time_ms: int
    token_count: int
    tokens: list[dict]
    entities: list[dict]
    quotes: list[dict]
    characters: list[dict]
    events: list[dict]
    supersenses: list[dict]
```

## NLP Service

```python
class NLPService:
    def __init__(self, default_model: str = "small"):
        self._models: dict[str, BookNLP] = {}
        self._default_model = default_model
        self._ready = False
    
    def load_models(self):
        """Pre-load models on startup."""
        for model in ["small", "big"]:
            self._models[model] = BookNLP("en", {
                "pipeline": "entity,quote,supersense,event,coref",
                "model": model
            })
        self._ready = True
    
    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """Run BookNLP analysis."""
        ...
    
    @property
    def is_ready(self) -> bool:
        return self._ready
```

## Dockerfile Updates

```dockerfile
# Add API dependencies
RUN pip install fastapi uvicorn

# Expose port
EXPOSE 8000

# Run API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Test Strategy

### Unit Tests

| Test | AC | Description |
|------|-----|-------------|
| `test_analyze_request_validation` | AC1 | Pydantic validates request |
| `test_pipeline_filtering` | AC2 | Only requested components returned |
| `test_health_response_schema` | AC3 | Health response matches schema |
| `test_ready_response_schema` | AC4 | Ready response matches schema |

### Integration Tests

| Test | AC | Description |
|------|-----|-------------|
| `test_analyze_endpoint` | AC1 | Full analysis returns valid JSON |
| `test_analyze_with_pipeline` | AC2 | Pipeline filtering works |
| `test_health_endpoint` | AC3 | Health returns 200 |
| `test_ready_endpoint` | AC4 | Ready returns correct status |
| `test_openapi_docs` | AC5 | /docs returns Swagger UI |
| `test_model_selection` | AC6 | Both models work |

## Telemetry

### Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `booknlp_requests_total` | Counter | `endpoint`, `model`, `status` |
| `booknlp_request_duration_seconds` | Histogram | `endpoint`, `model` |
| `booknlp_tokens_processed_total` | Counter | `model` |

### Logging

- Request received: INFO with `book_id`, `model`, `token_count`
- Request completed: INFO with `duration_ms`
- Errors: ERROR with exception details

### Tracing (OpenTelemetry)

| Span | Attributes | Purpose |
|------|------------|---------|
| `booknlp.analyze` | `book_id`, `model`, `token_count` | Root span for analyze request |
| `booknlp.pipeline.entity` | `entity_count` | Entity extraction |
| `booknlp.pipeline.quote` | `quote_count` | Quote detection |
| `booknlp.pipeline.coref` | `cluster_count` | Coreference resolution |
| `booknlp.pipeline.supersense` | `tag_count` | Supersense tagging |
| `booknlp.pipeline.event` | `event_count` | Event detection |

Trace context propagated via `traceparent` header (W3C Trace Context).

## Milestones

### M1: FastAPI Scaffold (Day 1)

- Create api/ package structure
- Implement health and ready endpoints
- Basic Dockerfile updates

### M2: Analyze Endpoint (Day 2-3)

- Implement NLPService wrapper
- Create Pydantic schemas
- Implement POST /v1/analyze
- Pipeline filtering

### M3: Testing & Docs (Day 4)

- Write unit and integration tests
- Verify OpenAPI documentation
- Update README

## Feature Flags

None for Sprint 02.

## Rollback

Revert to Sprint 01 container (CLI-only).

## References

- [PRD](./PRD.md)
- [Sprint 01 SPEC](../01-foundation/SPEC.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
