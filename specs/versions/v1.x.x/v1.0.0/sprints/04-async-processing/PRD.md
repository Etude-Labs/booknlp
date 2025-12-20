---
title: "Sprint 04: Async Processing"
version: v0.4.0
sprint: "04"
status: draft
---

# PRD: Sprint 04 — Async Processing

## Problem Statement

Synchronous API times out for large documents (book-length texts). Users need a way to submit long-running jobs and poll for results.

## Outcomes

1. **O1**: Async job submission via POST /v1/jobs
2. **O2**: Job status polling via GET /v1/jobs/{id}
3. **O3**: Result retrieval via GET /v1/jobs/{id}/result
4. **O4**: Progress reporting for long-running jobs

## Non-goals

- Persistent job storage (in-memory for v0.4)
- Distributed job queue (single-node)
- WebSocket streaming

## Acceptance Criteria

### AC1: Job submission returns job ID

**Given** API with async enabled  
**When** POST /v1/jobs with large document  
**Then** returns `{"job_id": "...", "status": "pending"}`

### AC2: Job status shows progress

**Given** a submitted job  
**When** GET /v1/jobs/{id}  
**Then** returns status with progress percentage

### AC3: Completed job result retrievable

**Given** a completed job  
**When** GET /v1/jobs/{id}/result  
**Then** returns full analysis result

### AC4: Job expiration

**Given** a completed job older than TTL  
**When** GET /v1/jobs/{id}  
**Then** returns 404 (job expired)

## Success Metrics

| Metric | Target |
|--------|--------|
| Max document size | 1M tokens |
| Job TTL | 1 hour |
| Queued jobs | 10 |
| Concurrent processing | **1** (GPU constraint) |

## Constraints

### Single-Task GPU Processing

> **Critical**: Only **one job processes at a time** due to GPU memory constraints.

- Jobs are queued and processed sequentially
- Multiple jobs can be *submitted* (up to queue limit)
- Only one job *executes* at any moment
- Queue provides fair ordering (FIFO)

This constraint applies to both CPU and GPU modes to ensure consistent behavior and prevent OOM errors.

## Dependencies

- Sprint 03 complete
- Background task library (asyncio or similar)

## References

- [Sprint 03 PRD](../03-gpu-support/PRD.md)
- [ROADMAP](../../ROADMAP.md)
