---
title: "Sprint 01: Foundation"
version: v0.1.0
sprint: "01"
status: draft
---

# PRD: Sprint 01 — Foundation

## Problem Statement

BookNLP is a powerful NLP pipeline for literary analysis, but it requires complex local installation with specific Python versions and dependency management. Users face:

1. **Installation friction** — Dependency conflicts, platform-specific issues
2. **Environment management** — Python version constraints, TensorFlow/PyTorch coexistence
3. **No standardized deployment** — Each user must configure their own environment

## Outcomes

1. **O1**: BookNLP runs successfully in a Docker container on Linux
2. **O2**: Both `big` and `small` models are pre-downloaded and functional
3. **O3**: All pipeline components work: entity, quote, supersense, event, coref
4. **O4**: Container builds reproducibly with pinned dependencies

## Non-goals

- REST API (Sprint 02)
- GPU support (Sprint 03)
- Async processing (Sprint 04)
- Production hardening (Sprint 05)
- Windows/macOS native support (Linux container only)

## Acceptance Criteria

### AC1: Container builds successfully

**Given** the Dockerfile and source code  
**When** `docker build -t booknlp:cpu .` is run  
**Then** the build completes without errors in < 15 minutes

### AC2: BookNLP imports without errors

**Given** a built container  
**When** `docker run booknlp:cpu python -c "from booknlp.booknlp import BookNLP; print('OK')"`  
**Then** output is "OK" with exit code 0

### AC3: Small model processes text

**Given** a built container with sample text  
**When** BookNLP processes with `model=small` and full pipeline  
**Then** all output files are generated (.tokens, .entities, .quotes, .book, .supersense)

### AC4: Big model processes text

**Given** a built container with sample text  
**When** BookNLP processes with `model=big` and full pipeline  
**Then** all output files are generated (.tokens, .entities, .quotes, .book, .supersense)

### AC5: Models are pre-downloaded

**Given** a built container  
**When** BookNLP is initialized  
**Then** no network requests are made to download models (already bundled)

### AC6: Docker Compose works for local dev

**Given** docker-compose.yml  
**When** `docker compose up` is run  
**Then** container starts and is ready for use

## Success Metrics

| Metric | Target |
|--------|--------|
| Build time | < 15 minutes |
| Image size (CPU) | < 6 GB |
| Container startup time | < 30 seconds |
| All tests pass | 100% |

## Dependencies

- Python 3.12
- PyTorch 2.5.x
- transformers 4.46.x+
- spacy 3.8.x
- tensorflow 2.18.x
- BookNLP pretrained models from UC Berkeley

## Risks

| Risk | Mitigation |
|------|------------|
| `position_ids` error with transformers | Apply patch in fork |
| Large image size | Multi-stage build, optimize layers |
| Model download failures | Pre-download during build |

## References

- [ROADMAP](../../ROADMAP.md)
- [BookNLP GitHub](https://github.com/booknlp/booknlp)
