#!/bin/bash
#
# Start ComfyUI Server for Video Generation
# Optimized for 768GB RAM Mac Studio
#

set -e

# Navigate to ComfyUI directory
cd "$(dirname "$0")/../ComfyUI"

# Activate virtual environment
source venv/bin/activate

# Set environment variables for aggressive memory usage
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0  # Use all available memory
export PYTORCH_ENABLE_MPS_FALLBACK=1         # Fallback to CPU if needed

# Launch ComfyUI with optimal settings
echo "🚀 Starting ComfyUI Server..."
echo "   Server: http://127.0.0.1:8188"
echo "   Memory: 768GB unified memory (no limits)"
echo "   Backend: PyTorch MPS (Metal Performance Shaders)"
echo ""

python main.py \
  --highvram \
  --use-pytorch-cross-attention \
  --listen 0.0.0.0 \
  --port 8188

# Note: --highvram disables memory optimizations (we have 768GB, no need to optimize)
