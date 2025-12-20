#!/bin/bash
# GPU Validation Script for BookNLP
# 
# This script validates the GPU container build and performance.
# Run on a host with NVIDIA GPU and Docker with GPU support.
#
# Usage: ./scripts/validate-gpu.sh

set -e

echo "🚀 BookNLP GPU Validation Script"
echo "================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check NVIDIA driver
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA driver not found. Please install NVIDIA drivers."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

# Check NVIDIA Container Toolkit
if ! docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA Container Toolkit not installed or GPU not accessible."
    echo "   Install with: sudo apt-get install -y nvidia-container-toolkit"
    echo "   Then restart Docker: sudo systemctl restart docker"
    exit 1
fi

echo "✅ Prerequisites met"

# Show GPU info
echo ""
echo "🎮 GPU Information:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits

# Build GPU container
echo ""
echo "🔨 Building GPU container..."
DOCKER_BUILDKIT=1 docker build -f Dockerfile.gpu -t booknlp:cuda .

if [ $? -eq 0 ]; then
    echo "✅ GPU container built successfully"
else
    echo "❌ GPU container build failed"
    exit 1
fi

# Run container and check device detection
echo ""
echo "🔍 Testing device detection..."

# Start container in background
docker run -d --name booknlp-gpu-test --gpus all -p 8001:8000 booknlp:cuda

# Wait for startup with model loading check
echo "⏳ Waiting for API to start..."
sleep 30

# Check if model is loaded, wait longer if needed
for i in {1..10}; do
    READY_RESPONSE=$(curl -s http://localhost:8001/v1/ready || echo "")
    if [[ $READY_RESPONSE == *"model_loaded\":true"* ]]; then
        echo "✅ Model loaded successfully"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "⚠️ Model not fully loaded after 5 minutes, proceeding anyway"
    fi
    echo "⏳ Waiting for model to load... ($i/10)"
    sleep 30
done

# Check ready endpoint
READY_RESPONSE=$(curl -s http://localhost:8001/v1/ready || echo "")

if [[ $READY_RESPONSE == *"cuda"* ]]; then
    echo "✅ GPU detected and being used"
    echo "📊 Device info:"
    echo "$READY_RESPONSE" | python3 -m json.tool
else
    echo "❌ GPU not detected in container"
    docker logs booknlp-gpu-test
    docker rm -f booknlp-gpu-test
    exit 1
fi

# Performance test with 10K tokens
echo ""
echo "⚡ Running performance test (10K tokens)..."
cat > /tmp/test_text.txt << 'EOF'
The old mansion stood at the end of the lane, its windows dark and empty. Sarah walked slowly up the 
gravel path, her footsteps crunching in the evening silence. She had inherited this place from her 
grandmother, a woman she barely remembered. The lawyer had called it "a significant property" but 
looking at it now, Sarah could only see decay and neglect.

The front door creaked as she pushed it open. Inside, dust motes danced in the fading light that 
filtered through grimy windows. Furniture lay draped in white sheets, ghostly shapes in the gloom.
Sarah pulled out her phone and turned on the flashlight, sweeping it across the entrance hall.

"Hello?" she called out, though she wasn't sure why. The house had been empty for years. Her voice 
echoed off the high ceilings and faded into silence.

She found the living room first, a grand space with a fireplace that dominated one wall. Above the 
mantle hung a portrait, and Sarah's breath caught when she saw it. The woman in the painting looked 
exactly like her. The same dark hair, the same green eyes, the same slight upturn at the corner of 
the mouth. It was like looking into a mirror that showed her dressed in Victorian clothing.

"Grandmother," Sarah whispered. She had seen photographs, of course, but this portrait captured 
something the old photos had missed. There was a spark in those painted eyes, a hint of secrets 
kept and stories untold.

The rest of the house revealed more mysteries. In the library, she found shelves of leather-bound 
journals, all written in her grandmother's careful hand. In the study, there was a locked desk 
drawer that rattled when she tried to open it. In the conservatory, dead plants in ornate pots 
stood like sentinels around a central fountain that had long since run dry.

But it was the basement that held the biggest surprise. Behind a hidden door, disguised as part of 
the wall paneling, Sarah found a room that shouldn't exist. The space was clean, unlike the rest 
of the house. Modern equipment hummed quietly in the corners. Computer screens glowed with data 
she couldn't understand.

"What were you doing down here, Grandmother?" Sarah asked the empty room.

A voice behind her made her spin around. "I was hoping you'd find this place."

The woman standing in the doorway looked exactly like the portrait upstairs, exactly like Sarah 
herself. But that was impossible. Her grandmother had died ten years ago.

"Don't be afraid," the woman said with a smile that Sarah recognized as her own. "I have so much 
to tell you, and we don't have much time. They'll be coming soon."

"Who?" Sarah managed to ask. "Who's coming?"

"The others," her grandmother said. "The ones who've been waiting for you to claim your inheritance. 
The real inheritance, not the house. You see, my dear, our family has been guarding something for 
generations. Something powerful. Something dangerous. And now it's your turn."

She held out her hand, and in her palm was a small golden key that seemed to glow with its own light.

"Are you ready to learn the truth about who you really are?"
EOF

# Create base text
BASE_TEXT=$(cat /tmp/test_text.txt)

# Repeat text to reach ~10K tokens
for i in {2..10}; do
    echo "" >> /tmp/test_text.txt
    echo "Chapter $i" >> /tmp/test_text.txt
    echo "$BASE_TEXT" >> /tmp/test_text.txt
done

# Run performance test
START_TIME=$(date +%s%3N)
# Escape JSON properly without jq
TEXT_ESCAPED=$(cat /tmp/test_text.txt | sed 's/"/\\"/g' | tr -d '\n' | tr -d '\r')
RESPONSE=$(curl -s -X POST http://localhost:8001/v1/analyze \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"$TEXT_ESCAPED\",
        \"book_id\": \"performance_test\",
        \"model\": \"big\"
    }")
END_TIME=$(date +%s%3N)

PROCESSING_TIME=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_ms', 0))")
TOKEN_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token_count', 0))")

# Calculate metrics
SECONDS=$((PROCESSING_TIME / 1000))
TOKENS_PER_SEC=$((TOKEN_COUNT * 1000 / PROCESSING_TIME))

echo "📈 Performance Results:"
echo "   Tokens processed: $TOKEN_COUNT"
echo "   Processing time: ${SECONDS}s"
echo "   Tokens/second: $TOKENS_PER_SEC"

# Check if meets target
if [ $PROCESSING_TIME -lt 60000 ]; then
    echo "✅ Performance target met (< 60s)"
else
    echo "❌ Performance target NOT met (${SECONDS}s ≥ 60s)"
fi

# Cleanup
docker rm -f booknlp-gpu-test
rm -f /tmp/test_text.txt

echo ""
echo "🎉 GPU validation complete!"
