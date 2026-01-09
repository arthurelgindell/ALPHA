#!/usr/bin/env python3
"""
Inspect the generated video to understand what went wrong
"""

import cv2
import numpy as np
from pathlib import Path

video_path = "/Users/arthurdell/ARTHUR/videos/raw/test_wan22_1767162506.mp4"

print(f"Inspecting: {video_path}")
print(f"File size: {Path(video_path).stat().st_size / 1024:.1f} KB")
print()

# Open video
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("ERROR: Could not open video file")
    exit(1)

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
codec = int(cap.get(cv2.CAP_PROP_FOURCC))

print("Video Properties:")
print(f"  Resolution: {width}x{height}")
print(f"  FPS: {fps}")
print(f"  Frame count: {frame_count}")
print(f"  Duration: {frame_count/fps:.2f}s")
print(f"  Codec: {codec}")
print()

# Sample frames to check content
print("Sampling frames...")
sample_indices = [0, frame_count // 4, frame_count // 2, 3 * frame_count // 4, frame_count - 1]

for idx in sample_indices:
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ret, frame = cap.read()

    if ret:
        # Calculate statistics
        mean = frame.mean()
        std = frame.std()
        min_val = frame.min()
        max_val = frame.max()

        # Check for patterns
        unique_colors = len(np.unique(frame.reshape(-1, frame.shape[2]), axis=0))

        print(f"Frame {idx}/{frame_count}:")
        print(f"  Mean: {mean:.2f}, Std: {std:.2f}, Range: [{min_val}, {max_val}]")
        print(f"  Unique colors: {unique_colors}")

        # Check if frame is mostly uniform (corrupted)
        if std < 5:
            print(f"  ⚠️  WARNING: Very low variance - likely corrupted")

        # Save sample frame
        sample_path = Path("/Users/arthurdell/ARTHUR/videos/raw") / f"frame_{idx:04d}.png"
        cv2.imwrite(str(sample_path), frame)
        print(f"  Saved to: {sample_path}")
    else:
        print(f"Frame {idx}: Failed to read")
    print()

cap.release()

print("Inspection complete")
