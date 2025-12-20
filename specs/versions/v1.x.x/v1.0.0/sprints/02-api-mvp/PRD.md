---
title: "Sprint 02: API MVP"
version: v0.2.0
sprint: "02"
status: draft
---

# PRD: Sprint 02 — API MVP

## Problem Statement

With BookNLP containerized (Sprint 01), users still need to interact via Python code or CLI. There's no standardized way to:

1. **Integrate remotely** — Call BookNLP from other services
2. **Use from any language** — Non-Python applications can't easily use BookNLP
3. **Monitor health** — No way to check if the service is ready

## Outcomes

1. **O1**: REST API accepts text and returns structured JSON analysis
2. **O2**: Health and readiness endpoints enable container orchestration
3. **O3**: OpenAPI documentation enables client generation
4. **O4**: Both `big` and `small` models accessible via API parameter

## Non-goals

- GPU support (Sprint 03)
- Async job processing for large documents (Sprint 04)
- Authentication/rate limiting (Sprint 05)
- WebSocket streaming

## Acceptance Criteria

### AC1: POST /v1/analyze returns analysis

**Given** a running API container  
**When** `POST /v1/analyze` with `{"text": "...", "model": "small"}`  
**Then** response contains tokens, entities, quotes, characters, events, supersenses

### AC2: Pipeline components are configurable

**Given** a running API container  
**When** `POST /v1/analyze` with `{"pipeline": ["entity", "quote"]}`  
**Then** only entity and quote data is returned (faster processing)

### AC3: GET /v1/health returns liveness

**Given** a running API container  
**When** `GET /v1/health`  
**Then** response is `{"status": "ok"}` with 200 status

### AC4: GET /v1/ready returns readiness

**Given** a running API container with models loaded  
**When** `GET /v1/ready`  
**Then** response is `{"status": "ready", "model": "small"}` with 200 status

**Given** a running API container still loading  
**When** `GET /v1/ready`  
**Then** response is 503 with `{"status": "loading"}`

### AC5: OpenAPI docs available

**Given** a running API container  
**When** `GET /docs`  
**Then** Swagger UI is displayed with all endpoints documented

### AC6: Both models work via API

**Given** a running API container  
**When** `POST /v1/analyze` with `{"model": "big"}` or `{"model": "small"}`  
**Then** the specified model is used for analysis

## Success Metrics

| Metric | Target |
|--------|--------|
| API response time (small, 1K tokens) | < 10s |
| API response time (big, 1K tokens) | < 30s |
| Health check response | < 100ms |
| OpenAPI spec valid | 100% |

## Dependencies

- Sprint 01 complete (container with models)
- FastAPI
- Pydantic
- uvicorn

## Risks

| Risk | Mitigation |
|------|------------|
| Large response payloads | Implement response size limits |
| Request timeout for big model | Document limits, defer to Sprint 04 async |
| Memory pressure with concurrent requests | Single-worker for now, scale in Sprint 05 |

## References

- [Sprint 01 PRD](../01-foundation/PRD.md)
- [ROADMAP](../../ROADMAP.md)
