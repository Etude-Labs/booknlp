#!/bin/bash
# Load testing script for BookNLP API

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-load-test-key}"
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
RUN_TIME="${RUN_TIME:-300}"  # 5 minutes
HOST="${HOST:-localhost}"

echo "Starting load test for BookNLP API"
echo "URL: $API_URL"
echo "Users: $USERS"
echo "Spawn rate: $SPAWN_RATE"
echo "Run time: ${RUN_TIME}s"

# Set environment variables
export BOOKNLP_API_KEY="$API_KEY"

# Run locust
locust \
    --host="$API_URL" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="${RUN_TIME}s" \
    --html="load_test_report.html" \
    --csv="load_test_results" \
    tests/load/locustfile.py

echo "Load test completed!"
echo "Results saved to:"
echo "  - load_test_report.html (HTML report)"
echo "  - load_test_results.csv (CSV data)"
echo "  - load_test_results_stats.csv (Statistics)"
