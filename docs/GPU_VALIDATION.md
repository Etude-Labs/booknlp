# GPU Validation Guide

This document explains how to validate the BookNLP GPU container and performance targets.

## Prerequisites

### Hardware Requirements
- NVIDIA GPU with CUDA 12.4 support
- Minimum 8GB VRAM for the big model
- Recommended: RTX 3080 or better for optimal performance

### Software Requirements
1. **NVIDIA Drivers** (v535+)
   ```bash
   nvidia-smi  # Should show GPU info
   ```

2. **Docker Engine** (v20.10+)
   ```bash
   docker --version
   ```

3. **NVIDIA Container Toolkit**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

4. **Python 3.10** (Ubuntu 22.04 default)
   ```bash
   python3 --version  # Should show Python 3.10.x
   ```

## Quick Validation

Run the automated validation script:
```bash
./scripts/validate-gpu.sh
```

This script will:
- Check all prerequisites
- Build the GPU container
- Verify GPU detection
- Run performance benchmarks
- Report results

## Manual Validation Steps

### 1. Build GPU Container
```bash
DOCKER_BUILDKIT=1 docker build -f Dockerfile.gpu -t booknlp:cuda .
```

### 2. Verify GPU Detection
```bash
# Start container
docker run -d --name booknlp-gpu-test --gpus all -p 8001:8000 booknlp:cuda

# Wait 30 seconds for startup
sleep 30

# Check device info
curl http://localhost:8001/v1/ready | python3 -m json.tool
```

Expected response should show:
```json
{
  "device": "cuda",
  "cuda_available": true,
  "cuda_device_name": "NVIDIA GeForce RTX 3080"
}
```

### 3. Performance Test
```bash
# Create test file
cat > test_10k.txt << 'EOF'
[Paste 10K tokens of text here]
EOF

# Run analysis
curl -X POST http://localhost:8001/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "'"$(cat test_10k.txt)"'",
    "book_id": "perf_test",
    "model": "big"
  }'
```

The `processing_time_ms` should be less than 60000 (60 seconds).

## Performance Benchmarks

### Expected Performance
| GPU Model | Expected Time | VRAM Used |
|-----------|---------------|-----------|
| RTX 3080 | 30-45s | 6-8GB |
| RTX 4090 | 20-30s | 6-8GB |
| A100 | 15-25s | 6-8GB |

### Factors Affecting Performance
1. **GPU Memory Bandwidth**: Higher bandwidth = faster processing
2. **CUDA Cores**: More cores = better parallelization
3. **PCIe Bandwidth**: Affects model loading time
4. **System RAM**: Insufficient RAM can cause swapping

## Troubleshooting

### Container fails to start
```bash
# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### GPU not detected
```bash
# Check driver installation
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Out of Memory Errors
- Use the small model instead of big
- Close other GPU applications
- Consider a GPU with more VRAM

### Performance Below Target
1. Check GPU utilization during processing
2. Verify PCIe link speed (should be x16)
3. Update NVIDIA drivers
4. Check for thermal throttling

## CI/CD Integration

The validation can be automated in CI using GitHub Actions with GPU runners:

```yaml
jobs:
  gpu-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run GPU validation
        run: ./scripts/validate-gpu.sh
```

## Reporting Results

When reporting performance results, include:
- GPU model and driver version
- CUDA version
- Processing time for 10K tokens
- Tokens per second achieved
- Any warnings or errors
