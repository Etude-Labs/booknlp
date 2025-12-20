# BookNLP Container - CPU Version
# Multi-stage build for optimized image size
#
# Build: docker build -t booknlp:cpu .
# Run:   docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output booknlp:cpu

# =============================================================================
# Stage 1: Builder - Install Python dependencies
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install BookNLP from source
COPY setup.py .
COPY booknlp/ booknlp/
RUN pip install --no-cache-dir -e .

# =============================================================================
# Stage 2: Models - Download pretrained models
# =============================================================================
FROM builder AS models

# Download spacy model
RUN python -m spacy download en_core_web_sm

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
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy downloaded models from models stage
COPY --from=models /root/booknlp_models /root/booknlp_models
COPY --from=models /root/.cache /root/.cache

# Copy application source
COPY booknlp/ booknlp/
COPY setup.py .

# Download spacy model in runtime (smaller than copying)
RUN python -m spacy download en_core_web_sm

# Create non-root user with access to models
RUN useradd -m booknlp && \
    mkdir -p /home/booknlp/booknlp_models && \
    cp -r /root/booknlp_models/* /home/booknlp/booknlp_models/ 2>/dev/null || true && \
    mkdir -p /app/input /app/output && \
    chown -R booknlp:booknlp /app/input /app/output /home/booknlp

# Environment variables
ENV BOOKNLP_MODEL_PATH=/home/booknlp/booknlp_models
ENV BOOKNLP_DEFAULT_MODEL=small

# Expose API port
EXPOSE 8000

# Switch to non-root user
USER booknlp

# Default command - run API server
CMD ["uvicorn", "booknlp.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
