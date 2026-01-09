#!/bin/bash
# Test if Nemotron-3-Nano-30B works with Exo cluster
# This model is already downloaded (31 GB), so zero download time!

set -e

NEMOTRON_PATH="/Users/arthurdell/ARTHUR/MODELS/lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit"
HF_CACHE="$HOME/.cache/huggingface/hub"
MODEL_CACHE="$HF_CACHE/models--lmstudio-community--NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit"

echo "===================================================================="
echo "  Nemotron-3-Nano-30B Exo Compatibility Test"
echo "===================================================================="
echo ""

# Check if Nemotron exists
if [ ! -d "$NEMOTRON_PATH" ]; then
  echo "❌ Nemotron model not found at: $NEMOTRON_PATH"
  exit 1
fi

echo "✅ Nemotron model found (31 GB)"
echo "   Location: $NEMOTRON_PATH"
echo ""

# Create HuggingFace cache structure
echo "Setting up HuggingFace cache structure..."
mkdir -p "$MODEL_CACHE/snapshots"

# Create symlink if it doesn't exist
if [ ! -L "$MODEL_CACHE/snapshots/default" ]; then
  ln -s "$NEMOTRON_PATH" "$MODEL_CACHE/snapshots/default"
  echo "✅ Created symlink: $MODEL_CACHE/snapshots/default"
else
  echo "✅ Symlink already exists"
fi
echo ""

# Check if Exo is running
echo "Checking Exo cluster status..."
if ! curl -s http://localhost:52415/health > /dev/null 2>&1; then
  echo "⚠️  Exo cluster not running. Starting..."
  echo ""
  echo "Please run in another terminal:"
  echo "  ~/start-exo-cluster.sh"
  echo ""
  read -p "Press Enter when Exo cluster is running..."
fi

# List available models
echo ""
echo "Checking if Exo can discover Nemotron..."
MODELS=$(curl -s http://localhost:52415/models 2>/dev/null || echo '[]')

if echo "$MODELS" | grep -qi "nemotron"; then
  echo "✅ Exo discovered Nemotron model!"
  echo ""
  echo "Available models containing 'nemotron':"
  echo "$MODELS" | python3 -c "
import sys, json
models = json.load(sys.stdin)
for m in models:
    if 'nemotron' in m.lower():
        print(f'  - {m}')
" 2>/dev/null || echo "$MODELS"
else
  echo "⚠️  Nemotron not found in Exo model list"
  echo ""
  echo "Available models:"
  echo "$MODELS" | python3 -m json.tool 2>/dev/null | head -20
  echo ""
  echo "This likely means:"
  echo "  1. Exo doesn't support custom NemotronH architecture, or"
  echo "  2. Model needs different naming/path structure"
  echo ""
  echo "Trying inference anyway with common name variations..."
fi

# Try inference with different model name patterns
echo ""
echo "===================================================================="
echo "  Testing Inference"
echo "===================================================================="
echo ""

MODEL_NAMES=(
  "nvidia-nemotron-3-nano-30b"
  "nemotron-3-nano-30b"
  "NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit"
  "lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit"
)

SUCCESS=false

for MODEL_NAME in "${MODEL_NAMES[@]}"; do
  echo "Trying model name: $MODEL_NAME"

  RESPONSE=$(curl -s -X POST http://localhost:52415/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$MODEL_NAME\",
      \"messages\": [{\"role\": \"user\", \"content\": \"What is 2+2? Answer in one short sentence.\"}],
      \"max_tokens\": 50
    }" 2>&1)

  # Check if response contains "choices" (success indicator)
  if echo "$RESPONSE" | grep -q '"choices"'; then
    echo "✅ SUCCESS! Inference worked with model name: $MODEL_NAME"
    echo ""

    # Extract and display response
    CONTENT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['choices'][0]['message']['content'])
except:
    print('Could not parse response')
" 2>/dev/null)

    echo "Model response: $CONTENT"
    SUCCESS=true
    break
  else
    # Check for specific error
    if echo "$RESPONSE" | grep -qi "not found\|unsupported\|invalid"; then
      ERROR=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('error', {}).get('message', 'Unknown error'))
except:
    print('$RESPONSE')
" 2>/dev/null)
      echo "  ❌ Error: $ERROR"
    else
      echo "  ⚠️  Unexpected response (check logs)"
    fi
  fi
  echo ""
done

echo ""
echo "===================================================================="
echo "  Test Results"
echo "===================================================================="
echo ""

if [ "$SUCCESS" = true ]; then
  echo "🎉 Nemotron-3-Nano-30B works with Exo!"
  echo ""
  echo "Model details:"
  echo "  - Size: 31 GB (already downloaded)"
  echo "  - Architecture: Hybrid Mamba-Transformer with MoE"
  echo "  - Context: 262k tokens"
  echo "  - Quantization: 8-bit"
  echo ""
  echo "You can now use Nemotron for testing the RDMA cluster."
  echo "No need to download additional models!"
  echo ""
  echo "Next: Test tensor parallelism with DeepSeek V3 or Llama 70B"
else
  echo "❌ Nemotron incompatible with Exo"
  echo ""
  echo "Likely reason: Custom NemotronH architecture not supported"
  echo ""
  echo "Recommended fallback: Download Llama 1B for testing"
  echo ""
  echo "  huggingface-cli download mlx-community/Llama-3.2-1B-Instruct-4bit"
  echo ""
  echo "Then test with:"
  echo "  ./scripts/test_rdma_cluster.sh"
  echo ""
fi

echo "===================================================================="
