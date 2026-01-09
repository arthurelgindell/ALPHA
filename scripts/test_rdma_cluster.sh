#!/bin/bash
# Quick RDMA cluster validation script
# Tests cluster health before large model downloads

set -e

echo "===================================================================="
echo "  RDMA Cluster Quick Test"
echo "===================================================================="
echo ""

# Check if running on ALPHA
if [[ "$(hostname)" != *"alpha"* ]]; then
  echo "⚠️  Warning: This script should run on ALPHA (master node)"
  read -p "Continue anyway? [y/N] " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# Test 1: RDMA device status
echo "Test 1: Checking RDMA device status..."
if /usr/bin/ibv_devinfo -d rdma_en4 | grep -q "PORT_ACTIVE"; then
  echo "✅ RDMA device rdma_en4 is PORT_ACTIVE"
else
  echo "❌ RDMA device not active. Check Thunderbolt connection."
  exit 1
fi
echo ""

# Test 2: Exo cluster health
echo "Test 2: Checking Exo cluster status..."
if curl -s http://localhost:52415/health > /dev/null 2>&1; then
  echo "✅ Exo API is responsive"

  # Get cluster info
  CLUSTER_INFO=$(curl -s http://localhost:52415/state | python3 -c "
import sys, json
d = json.load(sys.stdin)
profiles = d.get('nodeProfiles', {})
print(f'{len(profiles)} nodes, {sum(p.get(\"memory\",{}).get(\"ramTotal\",{}).get(\"inBytes\",0) for p in profiles.values())/(1024**3):.0f} GB')
" 2>/dev/null)

  echo "✅ Cluster: $CLUSTER_INFO"
else
  echo "❌ Exo cluster not running. Start with: ~/start-exo-cluster.sh"
  exit 1
fi
echo ""

# Test 3: Check if small model is downloaded
echo "Test 3: Checking for test model..."
CACHE_DIR="$HOME/.cache/huggingface/hub"
if ls "$CACHE_DIR"/models--mlx-community--Llama-3.2-1B* > /dev/null 2>&1; then
  echo "✅ Llama 3.2 1B model found"
  HAS_MODEL=true
else
  echo "⚠️  Llama 3.2 1B not found. Downloading (1.24 GB)..."
  huggingface-cli download mlx-community/Llama-3.2-1B-Instruct-4bit \
    --local-dir-use-symlinks False
  HAS_MODEL=true
fi
echo ""

# Test 4: Quick inference test
if [ "$HAS_MODEL" = true ]; then
  echo "Test 4: Testing inference with Llama 3.2 1B..."

  RESPONSE=$(curl -s -X POST http://localhost:52415/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "llama-3.2-1b",
      "messages": [{"role": "user", "content": "What is 2+2?"}],
      "max_tokens": 50
    }')

  if echo "$RESPONSE" | grep -q "choices"; then
    echo "✅ Inference successful!"

    # Extract response
    CONTENT=$(echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['choices'][0]['message']['content'] if 'choices' in d else 'N/A')
" 2>/dev/null)

    echo ""
    echo "Model response: $CONTENT"
  else
    echo "❌ Inference failed. Response:"
    echo "$RESPONSE"
    exit 1
  fi
fi
echo ""

# Test 5: RDMA activity check (for future tensor parallel tests)
echo "Test 5: Checking for JACCL/RDMA activity in logs..."
if grep -q "JACCL\|distributed" /tmp/exo-alpha.log 2>/dev/null; then
  echo "✅ JACCL/distributed activity detected in logs"
else
  echo "ℹ️  No tensor parallel activity yet (expected for small models)"
fi
echo ""

echo "===================================================================="
echo "  ✅ RDMA Cluster Validation Complete"
echo "===================================================================="
echo ""
echo "Next steps:"
echo "  1. Cluster is healthy and ready for model downloads"
echo "  2. Small model (1B) tested successfully"
echo "  3. Ready to download production models:"
echo ""
echo "     cd /Users/arthurdell/ARTHUR"
echo "     ./scripts/download_cluster_models.sh"
echo ""
echo "  Or test with 8B model first (faster inference, <1 min download):"
echo ""
echo "     huggingface-cli download mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
echo "     curl -X POST http://localhost:52415/v1/chat/completions \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"model\": \"llama-3.1-8b\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""
