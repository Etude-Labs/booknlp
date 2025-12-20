---
milestone: M2
title: GPU Detection & Fallback
duration: 2 days
status: pending
---

# M2: GPU Detection & Fallback

## Tasks

### T2.1: Add device detection to NLPService

**Description**: Automatically detect and use GPU if available.

**Acceptance**: Service uses GPU when available, CPU when not.

**Implementation**:
- Add `_get_device()` method to NLPService
- Store device info as instance variable
- Log device selection on startup

### T2.2: Update ready endpoint with device info

**Description**: Add device information to ready response.

**Acceptance**: GET /v1/ready includes device, cuda_available fields.

**Implementation**:
- Add fields to ReadyResponse schema
- Query torch.cuda.is_available() and device name

### T2.3: Implement CPU fallback

**Description**: Gracefully fall back to CPU if GPU unavailable.

**Acceptance**: Processing works on CPU-only host with GPU image.

**Test Strategy**:
- Unit: Mock torch.cuda.is_available() returning False
- Integration: Run GPU image on CPU-only host

### T2.4: Add docker-compose GPU service

**Description**: Add booknlp-gpu service to docker-compose.yml.

**Acceptance**: `docker compose up booknlp-gpu` starts GPU container.

**Implementation**:
- Add service with GPU resource reservation
- Map to port 8001 to avoid conflict with CPU service
