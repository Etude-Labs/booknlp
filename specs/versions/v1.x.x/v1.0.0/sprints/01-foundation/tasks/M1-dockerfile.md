---
milestone: M1
title: Dockerfile & Dependencies
duration: 2 days
status: pending
---

# M1: Dockerfile & Dependencies

## Tasks

### T1.1: Create requirements.txt with pinned dependencies

**Description**: Create requirements.txt with exact versions for all dependencies.

**Acceptance**: All packages have `==` version pins.

**Test Strategy**: 
- Unit: Validate file format
- Integration: `pip install -r requirements.txt` succeeds

**Dependencies**:
```
torch==2.5.1
transformers==4.46.3
spacy==3.8.3
tensorflow==2.18.0
```

---

### T1.2: Create Dockerfile with multi-stage build

**Description**: Create Dockerfile using python:3.12-slim base with multi-stage build.

**Acceptance**: `docker build` completes without errors.

**Test Strategy**:
- Integration: Build succeeds
- Verify image size < 6GB

**Stages**:
1. Builder: Install Python dependencies
2. Models: Download BookNLP models
3. Runtime: Final slim image

---

### T1.3: Apply position_ids patch

**Description**: Patch BookNLP to handle transformers 4.x+ `position_ids` key error.

**Acceptance**: BookNLP loads models without `position_ids` error.

**Test Strategy**:
- Unit: Patch function removes key correctly
- Integration: Model loads with patched code

**Implementation**: Create `patches.py` with model loading fix.

---

### T1.4: Create .dockerignore

**Description**: Create .dockerignore to exclude unnecessary files from build context.

**Acceptance**: Build context is minimal.

**Exclude**:
- `.git/`
- `*.pyc`
- `__pycache__/`
- `.env`
- `output/`
- `*.egg-info/`

---

## Telemetry

| Metric | Collection Point |
|--------|------------------|
| Build duration | CI pipeline |
| Image size | Post-build |

## Rollback

N/A (greenfield)
