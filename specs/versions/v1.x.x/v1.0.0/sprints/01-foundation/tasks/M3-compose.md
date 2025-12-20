---
milestone: M3
title: Docker Compose & Testing
duration: 1 day
status: pending
---

# M3: Docker Compose & Testing

## Tasks

### T3.1: Create docker-compose.yml

**Description**: Create Docker Compose file for local development.

**Acceptance**: `docker compose up` starts container successfully.

**Test Strategy**:
- Integration: Compose up/down cycle works
- Integration: Volume mounts work correctly

**Configuration**:
```yaml
services:
  booknlp:
    build: .
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    environment:
      - BOOKNLP_DEFAULT_MODEL=small
```

---

### T3.2: Create smoke tests

**Description**: Create test script to validate all ACs.

**Acceptance**: All tests pass.

**Test Strategy**:
- Integration: Run full test suite in CI

**Tests**:
1. Container builds
2. BookNLP imports
3. Small model processes sample text
4. Big model processes sample text
5. Output files are generated correctly

---

### T3.3: Create sample test fixture

**Description**: Create sample text file for testing.

**Acceptance**: Sample text is ~1000 words of public domain fiction.

**Location**: `tests/fixtures/sample_text.txt`

---

### T3.4: Document usage

**Description**: Update README with container usage instructions.

**Acceptance**: README includes Docker build/run commands.

**Sections**:
- Building the container
- Running with Docker
- Running with Docker Compose
- Volume mounts
- Environment variables

---

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Test pass rate | CI pipeline |
| Test duration | CI pipeline |

## Rollback

N/A (greenfield)
