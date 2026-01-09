"""
Keyframe extraction utilities for video analysis
Uses ffmpeg for efficient frame extraction
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
import subprocess
import tempfile
import json
import logging
import shutil

logger = logging.getLogger(__name__)

# Find ffmpeg/ffprobe binaries
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"


@dataclass
class KeyframeResult:
  """Result of keyframe extraction"""
  success: bool
  frames: list[Path] = field(default_factory=list)
  video_path: Optional[Path] = None
  duration: Optional[float] = None
  fps: Optional[float] = None
  resolution: Optional[tuple[int, int]] = None
  error: Optional[str] = None

  def cleanup(self):
    """Remove extracted frame files"""
    for frame in self.frames:
      if frame.exists():
        frame.unlink()
    logger.debug(f"Cleaned up {len(self.frames)} keyframes")


def get_video_info(video_path: Path | str) -> dict:
  """
  Get video metadata using ffprobe

  Args:
    video_path: Path to video file

  Returns:
    Dict with duration, fps, width, height, codec
  """
  video_path = Path(video_path)

  if not video_path.exists():
    return {"error": f"Video not found: {video_path}"}

  try:
    cmd = [
      FFPROBE,
      "-v", "quiet",
      "-print_format", "json",
      "-show_format",
      "-show_streams",
      str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
      return {"error": f"ffprobe failed: {result.stderr}"}

    data = json.loads(result.stdout)

    # Find video stream
    video_stream = None
    for stream in data.get("streams", []):
      if stream.get("codec_type") == "video":
        video_stream = stream
        break

    if not video_stream:
      return {"error": "No video stream found"}

    # Parse frame rate (can be "30/1" or "29.97")
    fps_str = video_stream.get("r_frame_rate", "0/1")
    if "/" in fps_str:
      num, den = fps_str.split("/")
      fps = float(num) / float(den) if float(den) > 0 else 0
    else:
      fps = float(fps_str)

    return {
      "duration": float(data.get("format", {}).get("duration", 0)),
      "fps": round(fps, 2),
      "width": int(video_stream.get("width", 0)),
      "height": int(video_stream.get("height", 0)),
      "codec": video_stream.get("codec_name", "unknown"),
      "frames": int(video_stream.get("nb_frames", 0)) or None,
      "error": None
    }

  except subprocess.TimeoutExpired:
    return {"error": "ffprobe timed out"}
  except json.JSONDecodeError:
    return {"error": "Failed to parse ffprobe output"}
  except Exception as e:
    return {"error": str(e)}


def extract_keyframes(
  video_path: Path | str,
  output_dir: Optional[Path] = None,
  num_frames: int = 3,
  strategy: Literal["uniform", "first_middle_last"] = "uniform",
  format: str = "png"
) -> KeyframeResult:
  """
  Extract keyframes from video

  Args:
    video_path: Path to video file
    output_dir: Directory for extracted frames (temp dir if None)
    num_frames: Number of frames to extract
    strategy: Extraction strategy
      - uniform: Evenly spaced throughout video
      - first_middle_last: Start, middle, end frames
    format: Output image format (png, jpg)

  Returns:
    KeyframeResult with list of frame paths
  """
  video_path = Path(video_path)

  if not video_path.exists():
    return KeyframeResult(
      success=False,
      video_path=video_path,
      error=f"Video not found: {video_path}"
    )

  # Get video info
  info = get_video_info(video_path)
  if info.get("error"):
    return KeyframeResult(
      success=False,
      video_path=video_path,
      error=info["error"]
    )

  duration = info["duration"]
  fps = info["fps"]

  if duration <= 0:
    return KeyframeResult(
      success=False,
      video_path=video_path,
      error="Video has zero duration"
    )

  # Create output directory
  if output_dir is None:
    output_dir = Path(tempfile.mkdtemp(prefix="keyframes_"))
  else:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

  # Calculate timestamps based on strategy
  if strategy == "first_middle_last":
    timestamps = [0.1, duration / 2, max(duration - 0.1, 0.2)][:num_frames]
  else:  # uniform
    if num_frames == 1:
      timestamps = [duration / 2]
    else:
      step = duration / (num_frames + 1)
      timestamps = [step * (i + 1) for i in range(num_frames)]

  # Extract frames
  frames = []
  for i, ts in enumerate(timestamps):
    output_path = output_dir / f"frame_{i:03d}.{format}"

    try:
      cmd = [
        FFMPEG,
        "-y",  # Overwrite
        "-ss", str(ts),  # Seek to timestamp
        "-i", str(video_path),
        "-frames:v", "1",  # Extract 1 frame
        "-q:v", "2",  # High quality
        str(output_path)
      ]

      result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
      )

      if result.returncode == 0 and output_path.exists():
        frames.append(output_path)
        logger.debug(f"Extracted frame at {ts:.2f}s -> {output_path}")
      else:
        logger.warning(f"Failed to extract frame at {ts:.2f}s: {result.stderr}")

    except subprocess.TimeoutExpired:
      logger.warning(f"Frame extraction timed out at {ts:.2f}s")
    except Exception as e:
      logger.warning(f"Frame extraction error at {ts:.2f}s: {e}")

  if not frames:
    return KeyframeResult(
      success=False,
      video_path=video_path,
      duration=duration,
      fps=fps,
      error="Failed to extract any frames"
    )

  logger.info(f"Extracted {len(frames)} keyframes from {video_path.name}")

  return KeyframeResult(
    success=True,
    frames=frames,
    video_path=video_path,
    duration=duration,
    fps=fps,
    resolution=(info["width"], info["height"])
  )


def extract_frame_at_time(
  video_path: Path | str,
  timestamp: float,
  output_path: Path | str
) -> bool:
  """
  Extract single frame at specific timestamp

  Args:
    video_path: Source video
    timestamp: Time in seconds
    output_path: Output image path

  Returns:
    True if successful
  """
  video_path = Path(video_path)
  output_path = Path(output_path)

  if not video_path.exists():
    logger.error(f"Video not found: {video_path}")
    return False

  try:
    cmd = [
      FFMPEG,
      "-y",
      "-ss", str(timestamp),
      "-i", str(video_path),
      "-frames:v", "1",
      "-q:v", "2",
      str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, timeout=30)
    success = result.returncode == 0 and output_path.exists()

    if success:
      logger.debug(f"Extracted frame at {timestamp:.2f}s -> {output_path}")
    else:
      logger.error(f"Failed to extract frame: {result.stderr.decode()}")

    return success

  except Exception as e:
    logger.error(f"Frame extraction failed: {e}")
    return False
