---
milestone: M1
title: FastAPI Scaffold
duration: 1 day
status: pending
---

# M1: FastAPI Scaffold

## Tasks

### T1.1: Create FastAPI application

**Description**: Create api/ package with FastAPI app factory.

**Acceptance**: `uvicorn api.main:app` starts without errors.

**Test Strategy**:
- Unit: App factory returns FastAPI instance
- Integration: Server starts and responds

### T1.2: Implement GET /v1/health

**Description**: Implement liveness endpoint.

**Acceptance**: Returns `{"status": "ok"}` with 200.

**Test Strategy**:
- Integration: GET /v1/health returns 200

### T1.3: Implement GET /v1/ready

**Description**: Implement readiness endpoint with model status.

**Acceptance**: Returns ready status when models loaded, 503 when loading.

**Test Strategy**:
- Unit: Mock model loading states
- Integration: Verify status codes

### T1.4: Update Dockerfile for API

**Description**: Add FastAPI/uvicorn deps and expose port 8000.

**Acceptance**: Container starts API server on port 8000.

**Test Strategy**:
- Integration: `docker run -p 8000:8000` responds to health check

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Health check latency | Prometheus histogram |
