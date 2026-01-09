#!/bin/bash
# Wrapper to run create_video.py with HunyuanVideo environment

cd /Users/arthurdell/ARTHUR/video-generation/HunyuanVideo_MLX
source venv/bin/activate
cd /Users/arthurdell/ARTHUR/scripts
python3 create_video.py "$@"
