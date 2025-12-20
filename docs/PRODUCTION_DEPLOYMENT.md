# Production Deployment Guide

This guide covers deploying BookNLP API in production environments.

## Environment Variables

All configuration is done via environment variables with the `BOOKNLP_` prefix.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_ENVIRONMENT` | `development` | Environment: `development`, `staging`, `production` |
| `BOOKNLP_DEBUG` | `false` | Enable debug mode (never in production) |
| `BOOKNLP_HOST` | `0.0.0.0` | Server bind address |
| `BOOKNLP_PORT` | `8000` | Server port |
| `BOOKNLP_WORKERS` | `1` | Number of workers (keep at 1 for GPU) |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_AUTH_REQUIRED` | `false` | Require API key authentication |
| `BOOKNLP_API_KEY` | - | API key for authentication (required if auth enabled) |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `BOOKNLP_CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials in CORS |
| `BOOKNLP_CORS_ALLOW_METHODS` | `*` | Allowed HTTP methods |
| `BOOKNLP_CORS_ALLOW_HEADERS` | `*` | Allowed HTTP headers |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `BOOKNLP_RATE_LIMIT_DEFAULT` | `60/minute` | Default rate limit |
| `BOOKNLP_RATE_LIMIT_ANALYZE` | `10/minute` | Rate limit for /analyze |
| `BOOKNLP_RATE_LIMIT_JOBS` | `10/minute` | Rate limit for /jobs |

### Job Queue

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_MAX_QUEUE_SIZE` | `10` | Maximum pending jobs |
| `BOOKNLP_JOB_TTL_SECONDS` | `3600` | Job result retention (1 hour) |
| `BOOKNLP_SHUTDOWN_GRACE_PERIOD` | `30` | Shutdown wait time in seconds |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |
| `BOOKNLP_LOG_FORMAT` | `json` | Log format: `json` or `console` |
| `BOOKNLP_LOG_INCLUDE_TIMESTAMP` | `true` | Include timestamps in logs |

### Metrics

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOKNLP_METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `BOOKNLP_METRICS_PATH` | `/metrics` | Metrics endpoint path |

---

## Production Configuration Example

```bash
# .env.production
BOOKNLP_ENVIRONMENT=production
BOOKNLP_DEBUG=false

# Authentication
BOOKNLP_AUTH_REQUIRED=true
BOOKNLP_API_KEY=your-secure-api-key-here

# CORS - restrict to your domains
BOOKNLP_CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Rate Limiting
BOOKNLP_RATE_LIMIT_ENABLED=true
BOOKNLP_RATE_LIMIT_DEFAULT=60/minute
BOOKNLP_RATE_LIMIT_ANALYZE=10/minute

# Logging
BOOKNLP_LOG_LEVEL=INFO
BOOKNLP_LOG_FORMAT=json

# Metrics
BOOKNLP_METRICS_ENABLED=true
```

---

## Docker Deployment

### Build Image

```bash
docker build -t booknlp-api:latest .
```

### Run Container

```bash
docker run -d \
  --name booknlp-api \
  --gpus all \
  -p 8000:8000 \
  -e BOOKNLP_ENVIRONMENT=production \
  -e BOOKNLP_AUTH_REQUIRED=true \
  -e BOOKNLP_API_KEY=your-api-key \
  -e BOOKNLP_CORS_ORIGINS=https://your-domain.com \
  -e BOOKNLP_RATE_LIMIT_ENABLED=true \
  booknlp-api:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  booknlp-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOOKNLP_ENVIRONMENT=production
      - BOOKNLP_AUTH_REQUIRED=true
      - BOOKNLP_API_KEY=${BOOKNLP_API_KEY}
      - BOOKNLP_CORS_ORIGINS=${BOOKNLP_CORS_ORIGINS}
      - BOOKNLP_RATE_LIMIT_ENABLED=true
      - BOOKNLP_LOG_FORMAT=json
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
```

---

## Kubernetes Deployment

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: booknlp-api
spec:
  replicas: 1  # GPU constraint - single replica per GPU
  selector:
    matchLabels:
      app: booknlp-api
  template:
    metadata:
      labels:
        app: booknlp-api
    spec:
      containers:
      - name: booknlp-api
        image: booknlp-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: BOOKNLP_ENVIRONMENT
          value: "production"
        - name: BOOKNLP_AUTH_REQUIRED
          value: "true"
        - name: BOOKNLP_API_KEY
          valueFrom:
            secretKeyRef:
              name: booknlp-secrets
              key: api-key
        - name: BOOKNLP_CORS_ORIGINS
          value: "https://your-domain.com"
        - name: BOOKNLP_RATE_LIMIT_ENABLED
          value: "true"
        - name: BOOKNLP_LOG_FORMAT
          value: "json"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
          requests:
            nvidia.com/gpu: 1
            memory: "8Gi"
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /v1/ready
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: booknlp-api
spec:
  selector:
    app: booknlp-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: booknlp-secrets
type: Opaque
stringData:
  api-key: "your-secure-api-key-here"
```

---

## Health Checks

### Liveness Probe
- **Endpoint**: `GET /v1/health`
- **Purpose**: Verify service is running
- **Expected**: Always returns 200 if service is up

### Readiness Probe
- **Endpoint**: `GET /v1/ready`
- **Purpose**: Verify models are loaded and ready
- **Expected**: 200 when ready, 503 when loading

### Info Endpoint
- **Endpoint**: `GET /v1/info`
- **Purpose**: Debug and monitoring information
- **Returns**: Service version, model status, queue stats

---

## Security Checklist

- [ ] Set `BOOKNLP_ENVIRONMENT=production`
- [ ] Enable authentication: `BOOKNLP_AUTH_REQUIRED=true`
- [ ] Use strong API key (32+ characters)
- [ ] Restrict CORS origins to your domains
- [ ] Enable rate limiting
- [ ] Use HTTPS (via reverse proxy)
- [ ] Set appropriate resource limits
- [ ] Configure log aggregation
- [ ] Set up metrics monitoring (Prometheus/Grafana)
- [ ] Configure alerts for errors and latency

---

## Monitoring

### Prometheus Metrics

The `/metrics` endpoint exposes Prometheus metrics:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_inprogress` - Current in-flight requests

### Recommended Alerts

```yaml
groups:
- name: booknlp
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate on BookNLP API

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 30
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High latency on BookNLP API

  - alert: ServiceDown
    expr: up{job="booknlp-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: BookNLP API is down
```

---

## Troubleshooting

### Service Not Starting

1. Check logs: `docker logs booknlp-api`
2. Verify GPU is available: `nvidia-smi`
3. Check memory: Models require ~8GB RAM

### Slow Responses

1. Check queue size: `GET /v1/info`
2. Verify GPU utilization: `nvidia-smi`
3. Consider text size limits

### Authentication Errors

1. Verify `BOOKNLP_AUTH_REQUIRED=true`
2. Check `BOOKNLP_API_KEY` is set
3. Ensure `X-API-Key` header is sent

### Rate Limiting

1. Check `X-RateLimit-*` response headers
2. Adjust limits via environment variables
3. Consider per-client rate limiting
