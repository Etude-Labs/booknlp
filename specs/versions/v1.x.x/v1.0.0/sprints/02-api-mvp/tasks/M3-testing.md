---
milestone: M3
title: Testing & Docs
duration: 1 day
status: pending
---

# M3: Testing & Docs

## Tasks

### T3.1: Write unit tests

**Description**: Unit tests for schemas, service, and routes.

**Acceptance**: >80% coverage on api/ package.

**Test Strategy**:
- pytest with coverage

### T3.2: Write integration tests

**Description**: Integration tests for all endpoints.

**Acceptance**: All ACs verified by tests.

**Test Strategy**:
- TestClient for FastAPI
- Real BookNLP for analyze tests

### T3.3: Verify OpenAPI documentation

**Description**: Ensure /docs works and spec is valid.

**Acceptance**: Swagger UI loads, spec validates.

**Test Strategy**:
- Integration: GET /docs returns 200
- Validate openapi.json schema

### T3.4: Update README

**Description**: Document API usage with examples.

**Acceptance**: README includes curl examples for all endpoints.

**Sections**:
- API endpoints
- Request/response examples
- Docker run with port mapping

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Test coverage | CI pipeline |
