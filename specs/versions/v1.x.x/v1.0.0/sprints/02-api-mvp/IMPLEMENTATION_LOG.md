---
title: "Sprint 02: API MVP - Implementation Log"
version: v0.2.0
sprint: "02"
---

# Implementation Log: Sprint 02 — API MVP

## Progress

| Date | Milestone | Task | Status | Notes |
|------|-----------|------|--------|-------|
| 2025-12-19 | M1 | T1.1 | Complete | FastAPI app factory with lifespan handler |
| 2025-12-19 | M1 | T1.2 | Complete | Health endpoint (GET /v1/health) |
| 2025-12-19 | M1 | T1.3 | Complete | Ready endpoint (GET /v1/ready) |
| 2025-12-19 | M1 | T1.4 | Complete | Dockerfile updated with uvicorn CMD |
| 2025-12-19 | M2 | T2.1 | Complete | NLPService wrapper for BookNLP |
| 2025-12-19 | M2 | T2.2 | Complete | AnalyzeRequest/Response Pydantic schemas |
| 2025-12-19 | M2 | T2.3 | Complete | POST /v1/analyze endpoint |
| 2025-12-19 | M2 | T2.4 | Complete | Pipeline filtering implemented |
| 2025-12-19 | M2 | T2.5 | Complete | Output parsing for all formats |
| 2025-12-19 | M3 | T3.1 | Complete | 31 unit tests, 68% coverage on api/ |
| 2025-12-19 | M3 | T3.2 | Complete | Integration tests for all endpoints |
| 2025-12-19 | M3 | T3.3 | Complete | OpenAPI docs verified at /docs |
| 2025-12-19 | M3 | T3.4 | Complete | README updated with API examples |

## Implementation Summary

### [2025-12-19] Sprint 02 Complete

**Implemented**: FastAPI REST API for BookNLP with health, ready, and analyze endpoints.

**Tests Added**: 31 tests (17 unit, 14 integration)
- Unit coverage: 68% overall, 100% on schemas
- All 6 acceptance criteria verified

**Files Changed**:
- `booknlp/api/main.py` - FastAPI app factory
- `booknlp/api/routes/health.py` - Health/ready endpoints
- `booknlp/api/routes/analyze.py` - Analyze endpoint
- `booknlp/api/schemas/` - Pydantic request/response schemas
- `booknlp/api/services/nlp_service.py` - BookNLP wrapper
- `Dockerfile` - Optimized with BuildKit cache mounts
- `docker-compose.yml` - Port mapping and healthcheck
- `README.md` - API documentation and examples

**Commits**: 6 commits
- 083261f: test(api): add failing tests for Sprint 02 API MVP
- 5c6ea9c: feat(api): implement M1 FastAPI scaffold with health/ready endpoints
- bbdd69a: feat(api): implement M2 analyze endpoint with pipeline filtering
- 9b21ec9: build(docker): update Dockerfile and compose for API server
- f866de5: refactor(api): consolidate duplicate TSV parsing functions
- 493e125: perf(docker): optimize build with BuildKit cache mounts

**AC Status**: All 6 ACs fully met
- AC1: POST /v1/analyze ✅
- AC2: Pipeline configurable ✅
- AC3: GET /v1/health ✅
- AC4: GET /v1/ready ✅
- AC5: OpenAPI docs ✅
- AC6: Both models work ✅

**Docker Image**: booknlp:cpu (17.1GB)
- Build time: ~7 min first build, ~10 sec for source changes
- API tested and verified working

## Decisions Made

1. **Direct pip install for spacy model**: Used GitHub release URL instead of `spacy download` command for reliability
2. **BuildKit cache mounts**: Added cache mounts for pip downloads to speed up rebuilds
3. **Layer ordering**: Reordered Dockerfile layers (deps → models → source) for optimal caching
4. **TSV parsing**: Consolidated 4 duplicate parsing functions into single generic function
5. **Timezone-aware datetime**: Used `datetime.now(timezone.utc)` instead of deprecated `utcnow()`

## Issues Encountered

1. **Spacy model download timeout**: GitHub releases had 504 errors with `spacy download` command
   - **Solution**: Switched to direct pip install from wheel URL
   
2. **Duplicate spacy download**: Original Dockerfile downloaded spacy model twice (models stage + runtime stage)
   - **Solution**: Copy spacy model from models stage instead of re-downloading

3. **Slow Docker rebuilds**: Source code changes invalidated model cache
   - **Solution**: Reordered layers and added BuildKit cache mounts

## Lessons Learned

1. **BuildKit cache mounts are essential**: Reduced rebuild time from minutes to seconds for dependency changes
2. **Layer ordering matters**: Put frequently-changing code (source) last to maximize cache hits
3. **Direct wheel URLs more reliable**: For critical dependencies, direct URLs avoid transient network issues
4. **TDD workflow effective**: Writing tests first caught schema validation issues early
5. **Docker multi-stage builds**: Separate stages for deps/models/runtime keeps final image clean
