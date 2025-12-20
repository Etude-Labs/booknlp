# BookNLP Container - CPU Version
# Multi-stage build for optimized image size
#
# Build: docker build -t booknlp:cpu .
# Run:   docker run -p 8000:8000 booknlp:cpu
#
# Layer ordering optimized for cache efficiency:
# 1. System deps (rarely change)
# 2. Python deps (change occasionally)
# 3. Models (change rarely, slow to download)
# 4. Source code (changes frequently, fast to copy)

# =============================================================================
# Stage 1: Dependencies - Install Python packages (cacheable)
# =============================================================================
FROM python:3.12-slim AS deps

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (most cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Models - Download pretrained models (slow, cache separately)
# =============================================================================
FROM deps AS models

# Install spacy model directly via pip (more reliable than spacy download)
# Using direct wheel URL from GitHub releases, with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# Install booknlp for model download (minimal source needed)
COPY setup.py .
COPY booknlp/ booknlp/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e .

# Pre-download BookNLP models (both big and small)
# This triggers the automatic download from UC Berkeley servers
RUN python -c "from booknlp.booknlp import BookNLP; BookNLP('en', {'pipeline': 'entity', 'model': 'big'})" || true
RUN python -c "from booknlp.booknlp import BookNLP; BookNLP('en', {'pipeline': 'entity', 'model': 'small'})" || true

# =============================================================================
# Stage 3: Runtime - Final slim image
# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy spacy model from models stage (avoid re-download)
COPY --from=models /usr/local/lib/python3.12/site-packages/en_core_web_sm /usr/local/lib/python3.12/site-packages/en_core_web_sm
COPY --from=models /usr/local/lib/python3.12/site-packages/en_core_web_sm*.dist-info /usr/local/lib/python3.12/site-packages/

# Copy downloaded BookNLP models from models stage
COPY --from=models /root/booknlp_models /root/booknlp_models

# Create non-root user with access to models
RUN useradd -m booknlp && \
    mkdir -p /home/booknlp/booknlp_models && \
    cp -r /root/booknlp_models/* /home/booknlp/booknlp_models/ 2>/dev/null || true && \
    mkdir -p /app/input /app/output && \
    chown -R booknlp:booknlp /app/input /app/output /home/booknlp

# Copy application source LAST (changes most frequently)
COPY --chown=booknlp:booknlp booknlp/ booknlp/
COPY --chown=booknlp:booknlp setup.py .

# Environment variables
ENV BOOKNLP_MODEL_PATH=/home/booknlp/booknlp_models
ENV BOOKNLP_DEFAULT_MODEL=small
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 8000

# Switch to non-root user
USER booknlp

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Default command - run API server
CMD ["uvicorn", "booknlp.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
