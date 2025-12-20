---
milestone: M1
title: CUDA Dockerfile
duration: 2 days
status: pending
---

# M1: CUDA Dockerfile

## Tasks

### T1.1: Create Dockerfile.gpu

**Description**: Create CUDA-enabled Dockerfile based on nvidia/cuda base image.

**Acceptance**: `docker build -f Dockerfile.gpu -t booknlp:cuda .` completes.

**Implementation**:
- Use nvidia/cuda:12.4.1-runtime-ubuntu22.04 base
- Install Python 3.12
- Install PyTorch with CUDA support
- Follow same layer ordering as CPU Dockerfile

### T1.2: Install PyTorch with CUDA

**Description**: Configure PyTorch to use CUDA 12.4.

**Acceptance**: `torch.cuda.is_available()` returns True in container.

**Implementation**:
- Use official PyTorch wheel for CUDA 12.4
- Pin version to 2.5.1+cu124

### T1.3: Verify GPU build

**Description**: Confirm build completes and produces working image.

**Acceptance**: Container starts and loads models on GPU.

**Test Strategy**:
- Integration: Build Dockerfile.gpu
- Integration: Run container and check torch.cuda.is_available()
