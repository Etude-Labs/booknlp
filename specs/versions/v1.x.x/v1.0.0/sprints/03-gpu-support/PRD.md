---
title: "Sprint 03: GPU Support"
version: v0.3.0
sprint: "03"
status: draft
---

# PRD: Sprint 03 — GPU Support

## Problem Statement

CPU-only processing is slow for production workloads. The `big` model takes 15+ minutes on CPU for book-length documents.

## Outcomes

1. **O1**: CUDA-enabled container processes text using GPU
2. **O2**: Automatic GPU detection with CPU fallback
3. **O3**: 5-10x performance improvement for `big` model
4. **O4**: Multi-architecture build (CPU/GPU variants)

## Non-goals

- Multi-GPU support
- AMD ROCm support
- Apple Metal support
- Concurrent GPU processing (single-task constraint)

## Acceptance Criteria

### AC1: GPU container builds

**Given** Dockerfile.gpu  
**When** `docker build -f Dockerfile.gpu -t booknlp:cuda .`  
**Then** build completes with CUDA support

### AC2: GPU detected and used

**Given** GPU container on CUDA-capable host  
**When** BookNLP processes text  
**Then** GPU is utilized (visible in nvidia-smi)

### AC3: CPU fallback works

**Given** GPU container on CPU-only host  
**When** BookNLP processes text  
**Then** processing completes on CPU without errors

### AC4: Performance improvement

**Given** GPU container with `big` model  
**When** processing 10K token document  
**Then** completes in < 60 seconds (vs 5+ minutes on CPU)

## Success Metrics

| Metric | Target |
|--------|--------|
| GPU image size | < 10 GB |
| Processing time (big, 10K tokens, GPU) | < 60s |
| GPU memory usage | < 8 GB |

## Dependencies

- Sprint 02 complete
- PyTorch 2.5.x with CUDA 12.4
- NVIDIA Container Toolkit

## References

- [Sprint 02 PRD](../02-api-mvp/PRD.md)
- [ROADMAP](../../ROADMAP.md)
