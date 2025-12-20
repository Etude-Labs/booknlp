---
version: v1.0.0
type: major
timeframe: 2025-Q1 → 2025-Q2
status: draft
---

# BookNLP Containerization Roadmap — v1.0.0

## Overview & Objectives

Transform BookNLP from a Python library into a production-ready containerized web service, enabling:

1. **Easy deployment** — Single Docker image with all dependencies pre-installed
2. **API access** — RESTful endpoints for text analysis without Python integration
3. **Scalability** — Horizontal scaling via container orchestration
4. **GPU support** — CUDA-enabled containers for production workloads
5. **Integration** — Clean API contract for etude-narrative-analysis and other consumers

### Success Metrics

| Metric | Target |
|--------|--------|
| Container startup time (cold) | < 60s |
| API response time (small model, 10K tokens) | < 30s |
| API response time (big model, 10K tokens) | < 60s |
| Container image size | < 8GB (GPU), < 4GB (CPU) |
| Uptime (production) | 99.5% |

---

## Scope & Non-goals

### In Scope

- Dockerfile for CPU and GPU variants
- FastAPI-based REST API
- Health check and readiness endpoints
- Async job processing for long documents
- Docker Compose for local development
- Basic authentication (API key)
- OpenAPI/Swagger documentation
- Structured JSON responses
- Configurable pipeline components

### Non-goals (v1.0)

- Kubernetes Helm charts (future)
- Multi-language support beyond English
- Custom model training endpoints
- WebSocket streaming (future consideration)
- Multi-tenancy / user management
- Persistent storage of results (caller responsibility)

---

## Themes & Epics

### Theme 1: Containerization Foundation
- Dockerfile with multi-stage build
- CPU and CUDA base image variants
- Dependency pinning and reproducible builds
- Model download and caching strategy

### Theme 2: API Design & Implementation
- FastAPI application structure
- Synchronous `/analyze` endpoint for small documents
- Async job queue for large documents
- Pydantic request/response schemas
- Error handling and validation

### Theme 3: Operational Readiness
- Health and readiness probes
- Structured logging (JSON)
- Metrics endpoint (Prometheus-compatible)
- Graceful shutdown handling
- Resource limits and tuning

### Theme 4: Developer Experience
- Docker Compose for local dev
- API documentation (OpenAPI)
- Example client code
- CI/CD pipeline (GitHub Actions, self-hosted runners)
- CHANGELOG maintenance

---

## Timeline & Milestones

### Phase 1: Foundation (v0.1.0) — Week 1-2
**Goal**: Basic containerized BookNLP with CLI access

- [ ] Multi-stage Dockerfile (CPU)
- [ ] Model download during build
- [ ] Basic smoke test
- [ ] Docker Compose for local testing

**Deliverable**: `docker run booknlp:cpu python -c "from booknlp.booknlp import BookNLP; print('OK')"`

---

### Phase 2: API MVP (v0.2.0) — Week 3-4
**Goal**: Synchronous REST API for document analysis

- [ ] FastAPI application scaffold
- [ ] `POST /v1/analyze` — synchronous analysis endpoint
- [ ] `GET /v1/health` — liveness check
- [ ] `GET /v1/ready` — readiness check (model loaded)
- [ ] Pydantic schemas for request/response
- [ ] Basic error handling
- [ ] OpenAPI documentation

**Deliverable**: Working API that accepts text and returns BookNLP output as JSON

**API Design**:

```json
POST /v1/analyze
Content-Type: application/json

{
  "text": "Call me Ishmael...",
  "book_id": "moby_dick",
  "pipeline": ["entity", "quote", "supersense", "event", "coref"],
  "model": "small"
}

Response:
{
  "book_id": "moby_dick",
  "processing_time_ms": 1234,
  "tokens": [...],
  "entities": [...],
  "quotes": [...],
  "characters": [...],
  "events": [...],
  "supersenses": [...]
}
```

---

### Phase 3: GPU Support (v0.3.0) — Week 5-6
**Goal**: CUDA-enabled container for production performance

- [ ] CUDA base image (nvidia/cuda)
- [ ] PyTorch GPU detection
- [ ] GPU memory management
- [ ] Performance benchmarking
- [ ] Multi-architecture build (CPU/GPU)

**Deliverable**: `docker run --gpus all booknlp:cuda ...`

---

### Phase 4: Async Processing (v0.4.0) — Week 7-8
**Goal**: Handle large documents without timeout

- [ ] Background task queue (in-process or Redis-backed)
- [ ] `POST /v1/jobs` — submit async job
- [ ] `GET /v1/jobs/{job_id}` — poll job status
- [ ] `GET /v1/jobs/{job_id}/result` — retrieve results
- [ ] Job expiration and cleanup
- [ ] Progress reporting

**API Design**:

```json
POST /v1/jobs
{
  "text": "...(large document)...",
  "book_id": "war_and_peace",
  "pipeline": ["entity", "quote", "coref"],
  "model": "big"
}

Response:
{
  "job_id": "abc123",
  "status": "pending",
  "created_at": "2025-01-15T10:00:00Z"
}

GET /v1/jobs/abc123
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 0.45,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### Phase 5: Production Hardening (v0.5.0) — Week 9-10
**Goal**: Production-ready operational features

- [ ] API key authentication
- [ ] Rate limiting
- [ ] Request size limits
- [ ] Structured JSON logging
- [ ] Prometheus metrics endpoint
- [ ] Graceful shutdown (SIGTERM handling)
- [ ] Resource limits documentation

---

### Phase 6: Release Candidate (v1.0.0-rc1) — Week 11-12
**Goal**: Final testing and documentation

- [ ] End-to-end integration tests
- [ ] Load testing and benchmarks
- [ ] Security review
- [ ] Documentation polish
- [ ] Example client implementations (Python, curl)
- [ ] Migration guide from library usage

---

### Phase 7: GA Release (v1.0.0) — Week 13
**Goal**: Production release

- [ ] Final bug fixes
- [ ] Release notes
- [ ] Docker Hub / GHCR publishing
- [ ] CHANGELOG update
- [ ] Announcement

---

## Python & Library Compatibility

> **Critical**: BookNLP has significant version constraints due to its dependency chain.
> See [GitHub Issues](https://github.com/booknlp/booknlp/issues) for known problems.

### Known Issues from Upstream

| Issue | Description | Status |
|-------|-------------|--------|
| [#26](https://github.com/booknlp/booknlp/issues/26) | `position_ids` key error with transformers 4.x+ | Requires patch |
| [#24](https://github.com/booknlp/booknlp/issues/24) | Model loading errors in updated environments | Transformers mismatch |
| [#15](https://github.com/booknlp/booknlp/issues/15) | Cannot install on Apple Silicon | TensorFlow issue |
| [#12](https://github.com/booknlp/booknlp/issues/12) | HFValidationError on Windows | Path handling |
| [#19](https://github.com/booknlp/booknlp/issues/19) | Windows encoding/path issues | Platform-specific |

### Current BookNLP Requirements (setup.py)

```python
'torch>=1.7.1',
'tensorflow>=1.15',
'spacy>=3',
'transformers>=4.11.3'
```

### Target Versions for Container

> **Strategy**: Since we're patching anyway, target **latest stable versions** on **Linux only**.

| Package | Version | Rationale |
|---------|---------|-----------|
| **Python** | 3.12.x | Latest stable; best performance |
| **PyTorch** | 2.5.x | Latest with CUDA 12.4 support |
| **transformers** | 4.46.x+ (latest) | Patch `position_ids` in fork; use latest features |
| **spacy** | 3.8.x | Latest stable |
| **tensorflow** | 2.18.x | Required for supersense; pin to latest stable |

### Compatibility Strategy

1. **Fork and patch** — Apply `position_ids` fix from issue #26 in our fork
2. **Use latest libraries** — Patch compatibility issues rather than pinning old versions
3. **Keep TensorFlow** — Required for supersense tagging; use latest stable
4. **Linux-only container** — Target platform; sidesteps Windows/macOS issues
5. **Pre-download models** — Bundle BERT models in image to avoid runtime downloads
6. **Support all model variants** — `big`, `small`, and `custom` models

### Container Base Image Options

| Option | Python | CUDA | Size | Notes |
|--------|--------|------|------|-------|
| `python:3.12-slim` | 3.12 | None | ~150MB | CPU-only |
| `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime` | 3.11 | 12.4 | ~5GB | GPU, includes PyTorch |
| `nvidia/cuda:12.4-cudnn9-runtime-ubuntu24.04` | Install | 12.4 | ~2GB | Minimal, add Python |

**Recommendation**: Use `pytorch/pytorch:2.5.1-cuda12.4` base for GPU variant to avoid PyTorch/CUDA mismatch issues.

### Supported Model Variants

| Model | Size | Use Case | GPU Recommended |
|-------|------|----------|-----------------|
| `small` | ~100MB | Development, testing, personal use | No |
| `big` | ~400MB | Production, accuracy-critical | Yes |
| `custom` | Variable | User-provided models | Depends |

All pipeline components available for all models:
- `entity` — Named entity recognition
- `quote` — Quotation detection and speaker attribution
- `supersense` — Semantic category tagging (requires TensorFlow)
- `event` — Event detection
- `coref` — Coreference resolution

---

## Dependencies & Risks

### Dependencies

| Dependency | Version | Risk Level | Mitigation |
|------------|---------|------------|------------|
| PyTorch | 2.5.x | Medium | Use pytorch base image with CUDA 12.4 |
| transformers | 4.46.x+ (latest) | Medium | Apply `position_ids` patch in fork |
| spacy | 3.8.x | Low | Bundle `en_core_web_sm` in image |
| tensorflow | 2.18.x | Medium | Required for supersense; Linux-only sidesteps issues |
| BERT models | Custom | Medium | Pre-download in Dockerfile |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| transformers API changes | Medium | Medium | Apply `position_ids` patch; test with latest |
| TensorFlow + PyTorch coexistence | Medium | Medium | Linux-only; test image thoroughly |
| Large container image size | High | Medium | Multi-stage builds, layer optimization |
| GPU memory exhaustion | Medium | High | Document limits, implement batching |
| Long processing times | High | Medium | Async jobs, progress reporting |
| Model loading latency | Medium | Medium | Warm-up on startup, keep-alive |
| Breaking changes in BookNLP | Low | High | Fork stability, version pinning |
| Python 3.7 EOL | N/A | N/A | Using Python 3.12 |

---

## Compatibility & Breaking Changes

This is a **new major version** introducing the containerized service. There are no breaking changes to the existing BookNLP Python library API.

### Compatibility Matrix

| Consumer | Compatibility |
|----------|---------------|
| Direct Python import | ✅ Unchanged |
| etude-narrative-analysis | ✅ New HTTP client adapter |
| CLI usage | ✅ Available in container |

---

## Migration & Rollout

### Feature Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `BOOKNLP_ASYNC_ENABLED` | Enable async job endpoints | `true` |
| `BOOKNLP_AUTH_REQUIRED` | Require API key | `false` (dev), `true` (prod) |
| `BOOKNLP_GPU_ENABLED` | Use GPU if available | `true` |

### Rollout Strategy

1. **Alpha** (v0.1.0-v0.3.0): Internal testing only
2. **Beta** (v0.4.0-v0.5.0): Limited external testing
3. **RC** (v1.0.0-rc1): Broader testing, documentation feedback
4. **GA** (v1.0.0): Production release

### Rollback

- Container images tagged by version
- Previous versions remain available
- No database migrations (stateless service)

---

## Security

### Secrets Management

- API keys via environment variables (`BOOKNLP_API_KEY`)
- No secrets in container images or logs
- Use `pydantic.SecretStr` for sensitive configuration

### Input Validation

- Pydantic strict mode for all request schemas
- Request size limits (configurable, default 10MB)
- Text encoding validation (UTF-8)

### Container Security

- Non-root user in container
- Read-only filesystem where possible
- Trivy scan in CI (no critical CVEs)
- Minimal base image (slim variants)

### Network Security

- HTTPS recommended for production (reverse proxy)
- CORS: explicit origins only, no wildcards in production
- Rate limiting per API key

---

## Telemetry & Quality Gates

### Tracing (OpenTelemetry)

| Span | Attributes |
|------|------------|
| `booknlp.process` | `book_id`, `model`, `pipeline`, `token_count` |
| `api.request` | `method`, `path`, `status_code`, `duration_ms` |
| `job.execute` | `job_id`, `status`, `progress` |

- Export to OTLP collector (configurable endpoint)
- Correlate logs with `trace_id`, `span_id`

### Logging (structlog)

- JSON output format
- Log levels: DEBUG (dev), INFO (events), WARNING (recoverable), ERROR (failures)
- Redact API keys and sensitive data
- Startup configuration summary (without secrets)

### Metrics to Collect

| Metric | Type | Purpose |
|--------|------|---------|
| `booknlp_requests_total` | Counter | Request volume |
| `booknlp_request_duration_seconds` | Histogram | Latency distribution |
| `booknlp_tokens_processed_total` | Counter | Throughput |
| `booknlp_errors_total` | Counter | Error rate |
| `booknlp_gpu_memory_bytes` | Gauge | Resource usage |
| `booknlp_active_jobs` | Gauge | Queue depth |

### Quality Gates

| Gate | Criteria | Phase |
|------|----------|-------|
| Unit tests pass | 100%, ≥80% coverage | All |
| Integration tests pass | 100% | v0.2.0+ |
| Container builds successfully | CPU + GPU | All |
| API responds to health check | < 5s | v0.2.0+ |
| Load test (100 concurrent) | No errors | v0.5.0+ |
| Security scan (Trivy) | No critical CVEs | v1.0.0-rc1 |

---

## References

### To Be Authored

- [ ] `specs/versions/v1.x.x/v1.0.0/sprints/01-foundation/PRD.md`
- [ ] `specs/versions/v1.x.x/v1.0.0/sprints/01-foundation/SPEC.md`
- [ ] `specs/decisions/ADR-001-api-framework-selection.md`
- [ ] `specs/decisions/ADR-002-async-job-architecture.md`
- [ ] `specs/decisions/ADR-003-container-base-image.md`

### External References

- [BookNLP GitHub](https://github.com/booknlp/booknlp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

---

## Open Questions

1. **Redis vs in-process queue**: Should async jobs use Redis for persistence, or is an in-process queue sufficient for v1.0?
2. **File upload vs text body**: Should the API accept file uploads, or require text in request body?
3. **Result storage**: Should the service store results, or is it purely stateless (caller stores)?
4. **Batch processing**: Should there be a batch endpoint for multiple documents?
5. **Model selection**: Should users be able to bring custom models, or only use bundled ones?

---

## Next Actions

1. Create sprint directory for Phase 1 (Foundation)
2. Author ADR-001 for API framework selection (FastAPI vs alternatives)
3. Draft PRD for Phase 1
4. Set up GitHub Actions for container builds
