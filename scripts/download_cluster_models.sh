#!/bin/bash
# Download models for ALPHA-BETA RDMA cluster
# Run this on ALPHA (512 GB master node)
# Models will be shared across cluster via Exo

set -e

# Ensure huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
  echo "Installing huggingface-hub..."
  pip3 install huggingface-hub
fi

CACHE_DIR="${HOME}/.cache/huggingface/hub"
mkdir -p "$CACHE_DIR"

echo "===================================================================="
echo "  RDMA Cluster Model Download - ALPHA (Master)"
echo "===================================================================="
echo ""
echo "Cluster Configuration:"
echo "  - ALPHA: 512 GB RAM (Master)"
echo "  - BETA:  256 GB RAM (Worker)"
echo "  - Total: 768 GB unified memory"
echo "  - RDMA:  Thunderbolt 5 @ 80 Gb/s"
echo ""
echo "Download Plan:"
echo "  1. Llama 3.2 1B (1.24 GB)   - Testing"
echo "  2. DeepSeek V3 4-bit (378 GB) - Primary LLM"
echo "  3. Llama 3.1 70B (38 GB)    - Fast fallback (optional)"
echo "  4. Llama 3.1 8B (4.5 GB)    - Quick queries (optional)"
echo ""
echo "===================================================================="
echo ""

# Function to download with progress
download_model() {
  local repo_id="$1"
  local size="$2"
  local purpose="$3"

  echo ""
  echo "────────────────────────────────────────────────────────────────"
  echo "Downloading: $repo_id"
  echo "Size: $size | Purpose: $purpose"
  echo "────────────────────────────────────────────────────────────────"

  huggingface-cli download "$repo_id" \
    --local-dir-use-symlinks False \
    --resume-download

  echo "✓ Completed: $repo_id"
}

# 1. Testing model (quick download to verify setup)
download_model \
  "mlx-community/Llama-3.2-1B-Instruct-4bit" \
  "1.24 GB" \
  "Cluster health testing"

# 2. Primary production model
echo ""
read -p "Continue with DeepSeek V3 (378 GB, ~30-60 min download)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  download_model \
    "mlx-community/DeepSeek-V3-4bit" \
    "378 GB" \
    "Primary LLM for coding/research"
fi

# 3. Optional fast fallback model
echo ""
read -p "Download Llama 3.1 70B for fast inference? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  download_model \
    "mlx-community/Meta-Llama-3.1-70B-Instruct-4bit" \
    "38 GB" \
    "Fast fallback inference"
fi

# 4. Optional quick query model
echo ""
read -p "Download Llama 3.1 8B for quick queries? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  download_model \
    "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit" \
    "4.5 GB" \
    "Quick queries and batch processing"
fi

echo ""
echo "===================================================================="
echo "  Download Complete"
echo "===================================================================="
echo ""
echo "Models are cached at: $CACHE_DIR"
echo ""
echo "Next steps:"
echo "  1. Start Exo cluster: ~/start-exo-cluster.sh"
echo "  2. Test inference:"
echo "     curl -X POST http://localhost:52415/v1/chat/completions \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"model\": \"llama-3.2-1b\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""
echo "  3. For DeepSeek V3 (tensor parallel via JACCL):"
echo "     curl -X POST http://localhost:52415/v1/chat/completions \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"model\": \"deepseek-v3-4bit\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
echo ""
