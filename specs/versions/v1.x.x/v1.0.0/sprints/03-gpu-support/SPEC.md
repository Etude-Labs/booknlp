---
title: "Sprint 03: GPU Support - Technical Specification"
version: v0.3.0
sprint: "03"
status: draft
linked_prd: ./PRD.md
---

# SPEC: Sprint 03 — GPU Support

## Overview

Add CUDA-enabled container for GPU acceleration, providing 5-10x performance improvement for the `big` model while maintaining CPU fallback capability.

## Architecture

### Project Structure

```text
booknlp/
├── Dockerfile          # CPU version (existing)
├── Dockerfile.gpu      # CUDA version (new)
├── docker-compose.yml  # Updated with GPU service
└── booknlp/
    └── api/
        └── services/
            └── nlp_service.py  # Device detection logic
```

### Container Variants

| Variant | Base Image | Size Target | Use Case |
|---------|------------|-------------|----------|
| `booknlp:cpu` | python:3.12-slim | ~17 GB | CPU-only hosts |
| `booknlp:cuda` | nvidia/cuda:12.4-runtime | < 20 GB | GPU-enabled hosts |

## Interfaces

### Device Detection

The NLPService should automatically detect GPU availability:

```python
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

### Ready Endpoint Update

`GET /v1/ready` should report device information:

```json
{
  "status": "ready",
  "model_loaded": true,
  "default_model": "small",
  "available_models": ["small", "big"],
  "device": "cuda",
  "cuda_available": true,
  "cuda_device_name": "NVIDIA GeForce RTX 3080"
}
```

## Implementation Details

### M1: CUDA Dockerfile

**Dockerfile.gpu**:

```dockerfile
# Stage 1: Base with CUDA
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

# Install Python 3.12
RUN apt-get update && apt-get install -y python3.12 python3-pip ...

# Stage 2: Dependencies (same pattern as CPU)
FROM base AS deps
# Install PyTorch with CUDA support
RUN pip install torch==2.5.1+cu124 -f https://download.pytorch.org/whl/cu124

# Stage 3: Models
FROM deps AS models
# Same model download as CPU

# Stage 4: Runtime
FROM base AS runtime
# Copy deps and models, set up API
```

**Key Requirements**:
- Use CUDA 12.4 base image (compatible with PyTorch 2.5.x)
- Install PyTorch with CUDA support
- BuildKit cache mounts for fast rebuilds
- Non-root user (same as CPU)

### M2: GPU Detection & Fallback

**Device Selection**:

```python
# In nlp_service.py
def _get_device(self) -> torch.device:
    """Get best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")
```

**Fallback Behavior**:
- If `cuda` requested but unavailable, log warning and use CPU
- Never fail if GPU unavailable (graceful degradation)

### M3: Performance Testing

**Benchmark Script**:

```python
# tests/benchmark/test_performance.py
def test_gpu_performance_improvement():
    """GPU should be at least 5x faster than CPU for big model."""
    # Measure CPU time
    # Measure GPU time
    # Assert speedup >= 5x
```

## Docker Compose Update

```yaml
services:
  booknlp:
    # ... existing CPU config
    
  booknlp-gpu:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    image: booknlp:cuda
    ports:
      - "8001:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Test Strategy

### Unit Tests

| Test | Description | AC |
|------|-------------|-----|
| `test_device_detection_with_cuda` | Returns cuda when available | AC2 |
| `test_device_detection_without_cuda` | Returns cpu when unavailable | AC3 |
| `test_ready_response_includes_device` | Device info in ready response | AC2 |

### Integration Tests

| Test | Description | AC |
|------|-------------|-----|
| `test_gpu_container_builds` | Dockerfile.gpu builds successfully | AC1 |
| `test_analyze_uses_gpu` | GPU utilized during processing | AC2 |
| `test_cpu_fallback_works` | Processing works without GPU | AC3 |

### Performance Tests

| Test | Description | AC |
|------|-------------|-----|
| `test_big_model_gpu_under_60s` | 10K tokens < 60s on GPU | AC4 |
| `test_gpu_speedup_vs_cpu` | GPU at least 5x faster | AC4 |

## Error Handling

| Error | Response |
|-------|----------|
| CUDA OOM | 503 with message "GPU memory exhausted" |
| CUDA driver error | Fall back to CPU, log warning |
| GPU not available | Use CPU silently |

## Milestones

### M1: CUDA Dockerfile (Day 1-2)

- [ ] Create Dockerfile.gpu with CUDA 12.4 base
- [ ] Install PyTorch with CUDA support
- [ ] Verify GPU build completes
- [ ] Test model loading on GPU

### M2: GPU Detection & Fallback (Day 3-4)

- [ ] Add device detection to NLPService
- [ ] Update ready endpoint with device info
- [ ] Implement CPU fallback
- [ ] Add docker-compose GPU service

### M3: Performance Testing (Day 5-6)

- [ ] Create benchmark test suite
- [ ] Measure GPU vs CPU performance
- [ ] Verify < 60s for 10K tokens
- [ ] Document performance results

## Risks

| Risk | Mitigation |
|------|------------|
| CUDA version incompatibility | Pin CUDA 12.4, test with multiple GPUs |
| Large image size | Use runtime image, not devel |
| OOM on small GPUs | Document minimum GPU requirements |

## Dependencies

- Sprint 02 complete (API works on CPU)
- PyTorch 2.5.1 with CUDA 12.4 support
- NVIDIA Container Toolkit on host
