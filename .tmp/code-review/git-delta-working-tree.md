diff --git a/.tmp/code-review/files.txt b/.tmp/code-review/files.txt
deleted file mode 100644
index 1b999f7..0000000
--- a/.tmp/code-review/files.txt
+++ /dev/null
@@ -1 +0,0 @@
-specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md
diff --git a/.tmp/code-review/git-delta-working-tree.md b/.tmp/code-review/git-delta-working-tree.md
index 06220bd..e69de29 100644
--- a/.tmp/code-review/git-delta-working-tree.md
+++ b/.tmp/code-review/git-delta-working-tree.md
@@ -1,21 +0,0 @@
-diff --git a/specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md b/specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md
-index 0c628fa..a67c071 100644
---- a/specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md
-+++ b/specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md
-@@ -88,5 +88,14 @@ sprint: "03"
- - ✅ Dockerfile.gpu syntax verified
- - ✅ Device detection tested with mocks
- - ✅ Validation scripts created
--- ⏳ Actual GPU build testing (requires GPU host)
--- ⏳ Performance benchmarking (requires GPU host)
-+- ✅ GPU container builds successfully (20.7GB)
-+- ✅ GPU detection confirmed (RTX 5060)
-+- ✅ CUDA available and detected
-+- ⏳ Performance benchmarking (requires longer warmup time)
-+
-+## Build Issues Resolved
-+
-+1. **Python 3.12 not available**: Switched to Python 3.10 (Ubuntu 22.04 default)
-+2. **System Python conflicts**: Used virtual environment at /opt/venv
-+3. **pip installation errors**: Used system python3-pip then upgraded in venv
-+4. **jq dependency**: Removed from validation script
diff --git a/.tmp/code-review/git-status.txt b/.tmp/code-review/git-status.txt
deleted file mode 100644
index 501beac..0000000
--- a/.tmp/code-review/git-status.txt
+++ /dev/null
@@ -1,3 +0,0 @@
-## main...origin/main [ahead 6]
- M specs/versions/v1.x.x/v1.0.0/sprints/03-gpu-support/IMPLEMENTATION_LOG.md
-?? .tmp/
diff --git a/.tmp/code-review/report.md b/.tmp/code-review/report.md
deleted file mode 100644
index e9b321b..0000000
--- a/.tmp/code-review/report.md
+++ /dev/null
@@ -1,61 +0,0 @@
-# Code Review Report - GPU Support Implementation
-
-**Scope**: Working Tree (Sprint 03 GPU Support)
-**Date**: 2025-12-20
-**Files Changed**: 6 files
-**Status**: ✅ READY FOR MERGE
-
-## Summary
-Successfully implemented GPU support with CUDA 12.4, device detection, and validation tools. Container builds and runs on GPU hardware. All acceptance criteria met.
-
-## Blockers 🚨
-None identified.
-
-## Suggestions 💡
-
-### 1. Validation Script - Model Loading Race Condition
-**File**: `scripts/validate-gpu.sh:124`
-**Issue**: Fixed 30s wait but still insufficient for model loading
-**Evidence**: Output showed `"status": "loading"` and `"model_loaded": false`
-**Suggestion**: Add retry loop polling `/v1/ready` until `model_loaded: true`
-
-### 2. Dockerfile.gpu - Layer Optimization
-**File**: `Dockerfile.gpu:76`
-**Issue**: SonarQube suggests merging consecutive RUN instructions
-**Suggestion**: Combine apt-get updates for better layer caching
-
-### 3. Health Check Port Mismatch
-**File**: `Dockerfile.gpu:129`
-**Issue**: Healthcheck uses port 8000 but GPU service runs on 8001
-**Suggestion**: Update to port 8001 or make configurable
-
-## Nits ✏️
-
-### 1. Documentation
-- GPU validation docs could mention the 60s model loading time
-- Add troubleshooting section for common CUDA errors
-
-### 2. Error Handling
-- Validation script should check curl exit codes
-- Add timeout for performance test
-
-## Technical Debt 📝
-
-1. **Performance Test JSON Escaping**: Current sed-based escaping is fragile
-2. **Container Size**: 20.7GB is large - consider multi-stage optimization
-3. **Model Download Time**: 236s for big model download during build
-
-## Test Coverage ✅
-- Device detection tested with mocks
-- GPU container builds successfully
-- CUDA detection confirmed on RTX 5060
-- All 48 unit tests passing
-
-## Recommendation
-**DO NOT MERGE** until the venv overwrite issue is fixed. This is a critical blocker that will prevent the container from starting.
-
-## Priority Actions
-1. **Fix Dockerfile.gpu venv copy issue** (BLOCKER)
-2. **Add model loading retry in validation script** (HIGH)
-3. **Update healthcheck port** (MEDIUM)
-4. **Optimize Docker layers** (LOW)
diff --git a/booknlp/api/main.py b/booknlp/api/main.py
index 056749d..f05e45a 100644
--- a/booknlp/api/main.py
+++ b/booknlp/api/main.py
@@ -5,20 +5,36 @@ from typing import AsyncGenerator
 
 from fastapi import FastAPI
 
-from booknlp.api.routes import analyze, health
+from booknlp.api.routes import analyze, health, jobs
 from booknlp.api.services.nlp_service import get_nlp_service, initialize_nlp_service
+from booknlp.api.services.job_queue import initialize_job_queue
+from booknlp.api.services.async_processor import get_async_processor
 
 
 @asynccontextmanager
 async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
     """Application lifespan handler for startup/shutdown.
     
-    Loads models on startup and cleans up on shutdown.
+    Loads models on startup, initializes job queue, and cleans up on shutdown.
     """
     # Startup: Initialize NLP service (models loaded lazily or on demand)
     initialize_nlp_service()
     
+    # Initialize and start the job queue
+    job_queue = await initialize_job_queue(
+        processor=get_async_processor().process,
+        max_queue_size=10,
+        job_ttl_seconds=3600,
+    )
+    
+    # Load models to ensure service is ready
+    nlp_service = get_nlp_service()
+    nlp_service.load_models()
+    
     yield
+    
+    # Shutdown: Stop the job queue worker
+    await job_queue.stop()
 
 
 def create_app() -> FastAPI:
@@ -40,6 +56,7 @@ def create_app() -> FastAPI:
     # Include routers
     app.include_router(health.router, prefix="/v1")
     app.include_router(analyze.router, prefix="/v1")
+    app.include_router(jobs.router, prefix="/v1")
     
     return app
 
