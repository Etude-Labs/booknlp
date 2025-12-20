---
title: "Sprint 05: Production Hardening"
version: v0.5.0
sprint: "05"
status: draft
---

# PRD: Sprint 05 — Production Hardening

## Problem Statement

The API lacks production-ready features: authentication, rate limiting, metrics, and graceful shutdown.

## Outcomes

1. **O1**: API key authentication protects endpoints
2. **O2**: Rate limiting prevents abuse
3. **O3**: Prometheus metrics endpoint for monitoring
4. **O4**: Graceful shutdown handles in-flight requests

## Non-goals

- OAuth/OIDC integration
- User management
- Multi-tenancy

## Acceptance Criteria

### AC1: API key required in production

**Given** `BOOKNLP_AUTH_REQUIRED=true`  
**When** request without API key  
**Then** returns 401 Unauthorized

### AC2: Rate limiting enforced

**Given** rate limit of 10 req/min  
**When** 11th request in 1 minute  
**Then** returns 429 Too Many Requests

### AC3: Metrics endpoint available

**Given** running API  
**When** GET /metrics  
**Then** returns Prometheus-format metrics

### AC4: Graceful shutdown

**Given** in-flight request  
**When** SIGTERM received  
**Then** request completes before shutdown

## Success Metrics

| Metric | Target |
|--------|--------|
| Auth overhead | < 5ms |
| Metrics scrape time | < 100ms |
| Shutdown grace period | 30s |

## Dependencies

- Sprint 04 complete
- prometheus-fastapi-instrumentator

## References

- [Sprint 04 PRD](../04-async-processing/PRD.md)
- [ROADMAP](../../ROADMAP.md)
