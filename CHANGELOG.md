# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-20

### Added

#### REST API
- **Async Job Processing**: Submit NLP jobs and poll for results
- **Authentication**: API key-based authentication via `X-API-Key` header
- **Rate Limiting**: Configurable per-endpoint rate limits with `slowapi`
- **Health Checks**: Liveness (`/v1/health`) and readiness (`/v1/ready`) endpoints
- **Prometheus Metrics**: Request counts, latencies, and job queue metrics at `/metrics`
- **Graceful Shutdown**: Configurable grace period for in-flight requests

#### API Endpoints
- `POST /v1/jobs` - Submit analysis job
- `GET /v1/jobs/{job_id}` - Get job status
- `GET /v1/jobs/{job_id}/result` - Get job result
- `DELETE /v1/jobs/{job_id}` - Cancel job
- `GET /v1/jobs/stats` - Queue statistics
- `POST /v1/analyze` - Synchronous analysis (small texts)

#### Docker Support
- Multi-stage Dockerfile for optimized image size
- CPU version (`booknlp:cpu`) with pre-downloaded models
- GPU version (`booknlp:gpu`) with CUDA 12.4 support
- Non-root user for security
- Health checks for container orchestration

#### Infrastructure
- GitHub Actions CI workflow (lint, test, Docker build)
- Pre-commit hooks (ruff, mypy, trailing whitespace)
- Comprehensive test suite (unit, integration, e2e)
- `pyproject.toml` with modern Python tooling configuration

### Changed
- Updated to Python 3.12
- Updated PyTorch to 2.5.1
- Updated TensorFlow to 2.18.0
- Updated Transformers to 4.46.3
- Updated spaCy to 3.8.3

### Fixed
- httpx 0.28+ compatibility with ASGITransport
- Prometheus registry conflicts in tests
- Pydantic v2 validation message format
- Docker COPY glob pattern for spacy dist-info

### Security
- API key authentication support
- Rate limiting to prevent abuse
- Input validation with size limits
- Non-root container user
- No secrets in logs or responses

## [0.1.0] - 2021-XX-XX

### Added
- Initial BookNLP release
- Part-of-speech tagging
- Dependency parsing
- Entity recognition
- Character name clustering and coreference resolution
- Quotation speaker identification
- Supersense tagging
- Event tagging
- Referential gender inference
- Small and Big model variants

[1.0.0]: https://github.com/dbamman/booknlp/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/dbamman/booknlp/releases/tag/v0.1.0
