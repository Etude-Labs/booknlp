#!/bin/bash
# Security scanning script for BookNLP API

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-booknlp:latest}"
OUTPUT_DIR="${OUTPUT_DIR:-security-reports}"
SEVERITY="${SEVERITY:-HIGH,CRITICAL}"

echo "Running security scan on Docker image: $IMAGE_NAME"
echo "Severity threshold: $SEVERITY"
echo "Output directory: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "Trivy is not installed. Installing..."
    case "$(uname -s)" in
        Linux*)
            sudo apt-get update
            sudo apt-get install wget apt-transport-https gnupg lsb-release
            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
            echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
            sudo apt-get update
            sudo apt-get install trivy
            ;;
        Darwin*)
            brew install trivy
            ;;
        *)
            echo "Unsupported OS. Please install Trivy manually."
            exit 1
            ;;
    esac
fi

# Update Trivy DB
echo "Updating Trivy vulnerability database..."
trivy image --download-db-only

# Run security scan
echo "Running vulnerability scan..."
trivy image \
    --format json \
    --output "$OUTPUT_DIR/vulnerabilities.json" \
    --severity "$SEVERITY" \
    "$IMAGE_NAME"

# Generate HTML report
echo "Generating HTML report..."
trivy image \
    --format template \
    --template "@contrib/html.tpl" \
    --output "$OUTPUT_DIR/vulnerabilities.html" \
    --severity "$SEVERITY" \
    "$IMAGE_NAME"

# Generate summary
echo "Generating summary report..."
trivy image \
    --format table \
    --severity "$SEVERITY" \
    "$IMAGE_NAME" | tee "$OUTPUT_DIR/vulnerabilities.txt"

# Check for critical findings
echo "Checking for critical vulnerabilities..."
CRITICAL_COUNT=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL") | .VulnerabilityID' "$OUTPUT_DIR/vulnerabilities.json" | wc -l || echo "0")
HIGH_COUNT=$(jq -r '.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH") | .VulnerabilityID' "$OUTPUT_DIR/vulnerabilities.json" | wc -l || echo "0")

echo ""
echo "=== SCAN SUMMARY ==="
echo "Critical vulnerabilities: $CRITICAL_COUNT"
echo "High vulnerabilities: $HIGH_COUNT"

if [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  Security issues found!"
    echo "Review the full report at: $OUTPUT_DIR/vulnerabilities.html"
    
    # Exit with error if critical issues found
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        echo "❌ Critical vulnerabilities detected - failing scan"
        exit 1
    fi
else
    echo ""
    echo "✅ No critical or high vulnerabilities found!"
fi

echo ""
echo "Reports saved to:"
echo "  - $OUTPUT_DIR/vulnerabilities.html (interactive)"
echo "  - $OUTPUT_DIR/vulnerabilities.json (machine-readable)"
echo "  - $OUTPUT_DIR/vulnerabilities.txt (summary)"
