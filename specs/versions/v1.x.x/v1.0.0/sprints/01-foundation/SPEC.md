---
title: "Sprint 01: Foundation - Technical Specification"
version: v0.1.0
sprint: "01"
status: draft
linked_prd: ./PRD.md
---

# SPEC: Sprint 01 — Foundation

## Overview

This specification details the technical implementation for containerizing BookNLP with CPU support, pre-downloaded models, and Docker Compose for local development.

## Architecture

### Container Structure

```
booknlp/
├── Dockerfile                 # Multi-stage build for CPU
├── docker-compose.yml         # Local development
├── .dockerignore
├── requirements.txt           # Pinned dependencies
├── booknlp/                   # Source code (existing)
├── models/                    # Pre-downloaded models (in image)
│   ├── big/
│   │   ├── entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model
│   │   ├── coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model
│   │   └── speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model
│   └── small/
│       ├── entities_google_bert_uncased_L-4_H-256_A-4-v1.0.model
│       ├── coref_google_bert_uncased_L-2_H-256_A-4-v1.0.model
│       └── speaker_google_bert_uncased_L-8_H-256_A-4-v1.0.1.model
└── tests/
    └── test_container.py      # Container smoke tests
```

### Dockerfile Design

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Download models
FROM builder AS models
RUN python -c "from booknlp.booknlp import BookNLP; BookNLP('en', {'pipeline': 'entity', 'model': 'big'})"
RUN python -c "from booknlp.booknlp import BookNLP; BookNLP('en', {'pipeline': 'entity', 'model': 'small'})"

# Stage 3: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=models /root/booknlp_models /root/booknlp_models
COPY . .

# Download spacy model
RUN python -m spacy download en_core_web_sm

# Non-root user with access to models
RUN useradd -m booknlp && \
    mkdir -p /home/booknlp/booknlp_models && \
    cp -r /root/booknlp_models/* /home/booknlp/booknlp_models/
ENV BOOKNLP_MODEL_PATH=/home/booknlp/booknlp_models
USER booknlp

CMD ["python", "-m", "booknlp"]
```

## Interfaces

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOOKNLP_MODEL_PATH` | Path to models directory | `/home/booknlp/booknlp_models` |
| `BOOKNLP_DEFAULT_MODEL` | Default model size | `small` |

### Volume Mounts

| Mount | Purpose |
|-------|---------|
| `/app/input` | Input text files |
| `/app/output` | Output results |

## Dependencies (Pinned)

```
torch==2.5.1
transformers==4.46.3
spacy==3.8.3
tensorflow==2.18.0
```

## Patches Required

### position_ids Patch

Apply fix from [issue #26](https://github.com/booknlp/booknlp/issues/26) to handle transformers 4.x+ compatibility:

```python
# In booknlp/english/entity_tagger.py (or via monkey-patch)
def load_model_with_patch(model_file, device):
    state_dict = torch.load(model_file, map_location=device)
    if "bert.embeddings.position_ids" in state_dict:
        del state_dict["bert.embeddings.position_ids"]
    return state_dict
```

## Test Strategy

### Unit Tests

| Test | AC | Description |
|------|-----|-------------|
| `test_dockerfile_syntax` | AC1 | Validate Dockerfile syntax |
| `test_requirements_pinned` | AC1 | All deps have pinned versions |

### Integration Tests

| Test | AC | Description |
|------|-----|-------------|
| `test_container_builds` | AC1 | `docker build` succeeds |
| `test_booknlp_import` | AC2 | Python import works |
| `test_small_model_processing` | AC3 | Small model processes sample |
| `test_big_model_processing` | AC4 | Big model processes sample |
| `test_models_predownloaded` | AC5 | No network calls on init |
| `test_docker_compose_up` | AC6 | Compose starts successfully |

### Test Fixtures

- `fixtures/sample_text.txt` — Short sample text (~1000 words)
- `fixtures/expected_output/` — Expected output files for validation

## Telemetry

### Build Metrics

| Metric | Purpose |
|--------|---------|
| `build_duration_seconds` | Track build time |
| `image_size_bytes` | Track image size |

### Runtime Metrics (for later sprints)

Deferred to Sprint 02 (API MVP).

## Milestones

### M1: Dockerfile & Dependencies (Day 1-2)

- Create Dockerfile with multi-stage build
- Pin all dependencies in requirements.txt
- Apply position_ids patch
- Create .dockerignore

### M2: Model Pre-download (Day 3)

- Download models during build
- Verify models are bundled in image
- Test offline operation

### M3: Docker Compose & Testing (Day 4)

- Create docker-compose.yml
- Write smoke tests
- Validate all ACs

## Rollback

Not applicable for Sprint 01 (greenfield).

## Feature Flags

None for Sprint 01.

## Open Questions

1. Should we create separate images for `big` and `small` models to reduce size?
2. Should models be downloaded at build time or copied from a pre-built layer?

## References

- [PRD](./PRD.md)
- [ROADMAP](../../ROADMAP.md)
- [BookNLP Issue #26](https://github.com/booknlp/booknlp/issues/26)
