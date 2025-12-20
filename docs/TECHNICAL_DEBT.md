# Technical Debt

This document tracks technical debt items that have been identified but not yet addressed.

## [2024-12-20] Custom BookNLP Metrics

**Source**: Code Review (working)
**Category**: documentation | performance
**Priority**: low
**Files**: `booknlp/api/metrics.py`
**Description**: Custom Prometheus metrics for BookNLP (job queue size, job counts, model load time) were removed as dead code. These metrics would be valuable for monitoring production usage.
**Suggested Fix**: Implement custom metrics by:
1. Creating metrics registry in app state
2. Incrementing jobs_submitted_total in submit_job endpoint
3. Updating job_queue_size gauge when jobs are added/removed
4. Adding job_processing_duration histogram around job processing
**Effort Estimate**: medium

## [2024-12-20] Rate Limiting Headers

**Source**: Code Review (working)
**Category**: enhancement
**Priority**: low
**Files**: `booknlp/api/rate_limit.py`
**Description**: Rate limiting works but doesn't return X-RateLimit-* headers in responses. These headers help clients understand their remaining quota.
**Suggested Fix**: Update rate_limit_exceeded_handler to add headers to all responses, not just rate-limited ones. This requires middleware or custom decorator.
**Effort Estimate**: medium

## [2024-12-20] Test Granularity

**Source**: Code Review (working)
**Category**: testing
**Priority**: low
**Files**: `tests/unit/api/*.py`
**Description**: Some tests are integration-style (making actual HTTP requests) rather than pure unit tests. This makes them slower and more brittle.
**Suggested Fix**: Consider extracting pure unit tests for business logic and keeping integration tests in a separate test suite.
**Effort Estimate**: small
