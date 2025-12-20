# Security Scanning

This directory contains security scanning configuration and tests for the BookNLP API.

## Security Tests

The `test_security_e2e.py` file contains end-to-end security tests that verify:
- No sensitive data leakage in error responses
- Input validation prevents malicious inputs
- SQL injection attempts are blocked
- API keys are not exposed in responses
- CORS headers are properly configured
- Rate limiting prevents brute force attacks

## Vulnerability Scanning

We use Trivy to scan Docker images for vulnerabilities.

### Running Security Scan

```bash
cd tests/security
./run_scan.sh
```

### Prerequisites

- Trivy scanner (auto-installed by script)
- Docker image to scan

### Configuration

Environment variables:
- `IMAGE_NAME`: Docker image to scan (default: booknlp:latest)
- `OUTPUT_DIR`: Report output directory (default: security-reports)
- `SEVERITY`: Severity threshold (default: HIGH,CRITICAL)

### Acceptance Criteria

The security scan passes if:
- 0 Critical vulnerabilities
- 0 High vulnerabilities
- All findings are documented

## Reports

After scanning, you'll find:
- `security-reports/vulnerabilities.html`: Interactive HTML report
- `security-reports/vulnerabilities.json`: Machine-readable data
- `security-reports/vulnerabilities.txt`: Summary text

## Security Best Practices

1. **Authentication**
   - API key required for protected endpoints
   - Keys validated against environment variable
   - No credential leakage in responses

2. **Input Validation**
   - Pydantic models validate all inputs
   - Size limits prevent DoS attacks
   - Special characters handled safely

3. **Rate Limiting**
   - Prevents brute force attacks
   - Per-endpoint limits
   - Configurable thresholds

4. **CORS Configuration**
   - Origins can be restricted
   - Methods and headers controlled
   - Credentials handled properly

5. **Error Handling**
   - No stack traces exposed
   - Generic error messages
   - No system information leaked

## Remediation

If vulnerabilities are found:

1. **Update Dependencies**
   ```bash
   pip install --upgrade package-name
   ```

2. **Rebuild Image**
   ```bash
   docker build -t booknlp:latest .
   ```

3. **Re-scan**
   ```bash
   ./run_scan.sh
   ```

4. **Document Exceptions**
   - If a vulnerability cannot be fixed
   - Add to security documentation
   - Implement compensating controls
