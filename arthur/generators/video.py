"""
Video Generation Backends
Hybrid video generation with local and cloud backends:
- GAMMA: HunyuanVideo-1.5 (local, NVIDIA GB10)
- Veo 3.1: Google API (cloud, premium)
- Wan 2.2: Local via ComfyUI on BETA (free, 720p)
- Wan 2.6: Cloud API via PiAPI (paid, 1080p, audio, multi-shot)

Audio Integration:
- mux_audio(): Combine video with voiceover narration via ffmpeg
"""

from pathlib import Path
from enum import Enum
from typing import Optional, Literal
from dataclasses import dataclass
import subprocess
import json
import time
import httpx

from ..config import PATHS, GAMMA_VIDEO, VEO_VIDEO, COMFYUI_BETA, WAN26_API

# Re-export mux_audio for convenience
from .voice import mux_audio

__all__ = ["VideoBackend", "VideoResult", "VideoGenerator", "mux_audio"]

class VideoBackend(str, Enum):
  """Available video generation backends"""
  # Local GAMMA (HunyuanVideo-1.5)
  GAMMA_TEST = "gamma-test"          # 10 steps, ~5 min, $0
  GAMMA_MEDIUM = "gamma-medium"      # 30 steps, ~25 min, $0
  GAMMA_HIGH = "gamma-high"          # 40 steps, ~45 min, $0
  GAMMA_MAXIMUM = "gamma-maximum"    # 50 steps, ~85 min, $0

  # Cloud Veo 3.1 (Google)
  VEO_FAST = "veo-fast"              # $0.15/sec
  VEO_STANDARD = "veo-standard"      # $0.40/sec

  # Local Wan 2.2 via ComfyUI on BETA
  WAN22_BETA = "wan22-beta"          # Free, 720p, ~20-30 min

  # Cloud Wan 2.6 API (PiAPI)
  WAN26_720P = "wan26-720p"          # $0.08/sec
  WAN26_1080P = "wan26-1080p"        # $0.12/sec
  WAN26_AUDIO = "wan26-audio"        # With native audio
  WAN26_MULTISHOT = "wan26-multishot"  # Multi-lens narrative

# Quality preset mapping for GAMMA
GAMMA_PRESETS = {
  VideoBackend.GAMMA_TEST: "test",
  VideoBackend.GAMMA_MEDIUM: "medium",
  VideoBackend.GAMMA_HIGH: "high",
  VideoBackend.GAMMA_MAXIMUM: "maximum",
}

# Model mapping for Veo
VEO_MODELS = {
  VideoBackend.VEO_FAST: "veo-3.1-fast-generate-preview",
  VideoBackend.VEO_STANDARD: "veo-3.1-generate-preview",
}

@dataclass
class VideoResult:
  """Result of video generation"""
  success: bool
  path: Optional[Path]
  backend: VideoBackend
  prompt: str
  duration: Optional[float] = None
  generation_time: Optional[float] = None
  error: Optional[str] = None

class VideoGenerator:
  """
  Unified video generation interface

  Usage:
    gen = VideoGenerator()

    # Generate with GAMMA (local, high quality)
    result = gen.generate_gamma(
      prompt="Cinematic shot of...",
      quality="medium"
    )

    # Generate with Veo (fast turnaround)
    result = gen.generate_veo(
      prompt="Product placement shot...",
      duration=8,
      fast=True
    )
  """

  def __init__(self):
    self.gamma_url = GAMMA_VIDEO.url
    self.veo_api_key = VEO_VIDEO.api_key
    self.scripts_dir = PATHS.scripts_dir

  def check_gamma(self) -> dict:
    """Check GAMMA endpoint health"""
    try:
      response = httpx.get(f"{self.gamma_url}/health", timeout=10)
      return response.json()
    except Exception as e:
      return {"status": "error", "error": str(e)}

  def generate_gamma(
    self,
    prompt: str,
    quality: Literal["test", "medium", "high", "maximum"] = "medium",
    num_frames: Optional[int] = None,
    seed: Optional[int] = None,
    download_path: Optional[Path] = None,
    wait: bool = True
  ) -> VideoResult:
    """
    Generate video using GAMMA (HunyuanVideo-1.5)

    Args:
      prompt: Cinematic prompt using Five-Part Formula
      quality: Quality preset (test, medium, high, maximum)
      num_frames: Number of frames (auto-calculated if None)
      seed: Random seed for reproducibility
      download_path: Where to save the video
      wait: Wait for completion (blocking)

    Returns:
      VideoResult with path and metadata
    """
    # Default frame counts by quality
    default_frames = {
      "test": 25,      # ~2s
      "medium": 61,    # ~5s
      "high": 81,      # ~6.5s
      "maximum": 97    # ~8s
    }

    if num_frames is None:
      num_frames = default_frames.get(quality, 61)

    # Build request
    request_data = {
      "prompt": prompt,
      "quality": quality,
      "num_frames": num_frames
    }

    if seed is not None:
      request_data["seed"] = seed

    start_time = time.time()

    try:
      # Submit generation request
      # GAMMA can take up to 90 minutes for maximum quality
      response = httpx.post(
        f"{self.gamma_url}/generate",
        json=request_data,
        timeout=7200.0 if wait else 30.0  # 2 hour timeout if waiting
      )

      result = response.json()

      if not result.get("success"):
        return VideoResult(
          success=False,
          path=None,
          backend=VideoBackend(f"gamma-{quality}"),
          prompt=prompt,
          error=result.get("error", "Unknown error")
        )

      generation_time = time.time() - start_time
      filename = result.get("filename")

      # Download video
      if download_path is None:
        download_path = PATHS.videos_dir / filename

      download_response = httpx.get(
        f"{self.gamma_url}/download/{filename}",
        timeout=120.0
      )

      download_path.parent.mkdir(parents=True, exist_ok=True)
      download_path.write_bytes(download_response.content)

      return VideoResult(
        success=True,
        path=download_path,
        backend=VideoBackend(f"gamma-{quality}"),
        prompt=prompt,
        duration=result.get("file_size_mb"),
        generation_time=generation_time
      )

    except httpx.TimeoutException:
      return VideoResult(
        success=False,
        path=None,
        backend=VideoBackend(f"gamma-{quality}"),
        prompt=prompt,
        error="Request timed out"
      )
    except Exception as e:
      return VideoResult(
        success=False,
        path=None,
        backend=VideoBackend(f"gamma-{quality}"),
        prompt=prompt,
        error=str(e)
      )

  def generate_veo(
    self,
    prompt: str,
    duration: int = 8,
    aspect_ratio: str = "16:9",
    fast: bool = True,
    output_path: Optional[Path] = None
  ) -> VideoResult:
    """
    Generate video using Veo 3.1 API

    Args:
      prompt: Cinematic prompt using Five-Part Formula
      duration: Duration in seconds (4, 6, or 8)
      aspect_ratio: 16:9 or 9:16
      fast: Use fast model ($0.15/sec) vs standard ($0.40/sec)
      output_path: Custom output path

    Returns:
      VideoResult with path and metadata
    """
    try:
      from google import genai
      from google.genai import types
    except ImportError:
      return VideoResult(
        success=False,
        path=None,
        backend=VideoBackend.VEO_FAST if fast else VideoBackend.VEO_STANDARD,
        prompt=prompt,
        error="google-genai package not installed"
      )

    model = VEO_MODELS[VideoBackend.VEO_FAST if fast else VideoBackend.VEO_STANDARD]
    backend = VideoBackend.VEO_FAST if fast else VideoBackend.VEO_STANDARD

    try:
      client = genai.Client(api_key=self.veo_api_key)

      config = types.GenerateVideosConfig(
        durationSeconds=duration,
        aspectRatio=aspect_ratio
      )

      # Submit request
      operation = client.models.generate_videos(
        model=model,
        prompt=prompt,
        config=config
      )

      # Poll for completion
      max_wait = 600  # 10 minutes
      start_time = time.time()

      while time.time() - start_time < max_wait:
        current_op = client.operations.get(operation)
        if current_op.done:
          break
        time.sleep(10)
      else:
        return VideoResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          error="Generation timed out"
        )

      generation_time = time.time() - start_time

      # Extract and download video
      if current_op.result and hasattr(current_op.result, 'generated_videos'):
        videos = current_op.result.generated_videos
        if videos and videos[0].video:
          video_uri = videos[0].video.uri

          # Download video
          if output_path is None:
            from datetime import datetime
            output_path = PATHS.videos_dir / f"veo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

          # Download using authenticated request
          http_request = {'url': video_uri, 'method': 'GET'}
          video_data = client._api_client.request(http_request, None, stream=False).content

          output_path.parent.mkdir(parents=True, exist_ok=True)
          output_path.write_bytes(video_data)

          return VideoResult(
            success=True,
            path=output_path,
            backend=backend,
            prompt=prompt,
            duration=duration,
            generation_time=generation_time
          )

      return VideoResult(
        success=False,
        path=None,
        backend=backend,
        prompt=prompt,
        error="No video in response"
      )

    except Exception as e:
      return VideoResult(
        success=False,
        path=None,
        backend=backend,
        prompt=prompt,
        error=str(e)
      )

  def generate_wan22_local(
    self,
    prompt: str,
    num_frames: int = 81,
    steps: int = 30,
    width: int = 832,
    height: int = 480,
    seed: Optional[int] = None,
    download_path: Optional[Path] = None
  ) -> VideoResult:
    """
    Generate video using local Wan 2.2 on BETA via ComfyUI

    Args:
      prompt: Video description
      num_frames: Number of frames (81 = ~6.75s at 12fps)
      steps: Inference steps (more = higher quality)
      width: Output width (832 for 720p)
      height: Output height (480 for 720p)
      seed: Random seed for reproducibility
      download_path: Where to save the video

    Returns:
      VideoResult with path and metadata
    """
    from .comfyui import ComfyUIClient
    from ..workflows.wan22_t2v import Wan22TextToVideoWorkflow, Wan22VideoConfig

    start_time = time.time()

    try:
      # Create workflow
      config = Wan22VideoConfig(
        prompt=prompt,
        width=width,
        height=height,
        num_frames=num_frames,
        steps=steps,
        seed=seed
      )
      workflow = Wan22TextToVideoWorkflow().generate(config)

      # Connect to ComfyUI on BETA
      client = ComfyUIClient(host=COMFYUI_BETA.host, port=COMFYUI_BETA.port)

      # Check health
      health = client.check_health()
      if health.get("status") != "healthy":
        return VideoResult(
          success=False,
          path=None,
          backend=VideoBackend.WAN22_BETA,
          prompt=prompt,
          error=f"ComfyUI not healthy: {health.get('error', 'unknown')}"
        )

      # Run workflow
      if download_path is None:
        from datetime import datetime
        download_path = PATHS.videos_dir / f"wan22_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

      result = client.run_workflow(workflow, download_path=download_path)

      generation_time = time.time() - start_time
      client.close()

      if result.success:
        return VideoResult(
          success=True,
          path=download_path,
          backend=VideoBackend.WAN22_BETA,
          prompt=prompt,
          duration=num_frames / 12,  # frames / fps
          generation_time=generation_time
        )
      else:
        return VideoResult(
          success=False,
          path=None,
          backend=VideoBackend.WAN22_BETA,
          prompt=prompt,
          error=result.error
        )

    except Exception as e:
      return VideoResult(
        success=False,
        path=None,
        backend=VideoBackend.WAN22_BETA,
        prompt=prompt,
        error=str(e)
      )

  def generate_wan26_api(
    self,
    prompt: str,
    duration: int = 5,
    resolution: str = "720P",
    with_audio: bool = False,
    multi_shot: bool = False,
    aspect_ratio: str = "16:9",
    download_path: Optional[Path] = None
  ) -> VideoResult:
    """
    Generate video using Wan 2.6 cloud API for premium features

    Args:
      prompt: Video description
      duration: Duration in seconds (5, 10, or 15)
      resolution: "720P" ($0.08/sec) or "1080P" ($0.12/sec)
      with_audio: Generate synchronized audio
      multi_shot: Enable multi-lens narrative
      aspect_ratio: "16:9", "9:16", "1:1", etc.
      download_path: Where to save the video

    Returns:
      VideoResult with path and metadata
    """
    from .wan26_api import Wan26APIClient

    # Determine backend based on options
    if multi_shot:
      backend = VideoBackend.WAN26_MULTISHOT
    elif with_audio:
      backend = VideoBackend.WAN26_AUDIO
    elif resolution == "1080P":
      backend = VideoBackend.WAN26_1080P
    else:
      backend = VideoBackend.WAN26_720P

    start_time = time.time()

    try:
      client = Wan26APIClient()

      # Submit generation
      result = client.text_to_video(
        prompt=prompt,
        duration=duration,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        with_audio=with_audio,
        multi_shot=multi_shot
      )

      if not result.success:
        client.close()
        return VideoResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          error=result.error
        )

      # Wait for completion
      video_url = client.wait_for_completion(result.task_id, timeout=600)

      if not video_url:
        client.close()
        return VideoResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          error="Generation timed out or failed"
        )

      # Download video
      if download_path is None:
        from datetime import datetime
        download_path = PATHS.videos_dir / f"wan26_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

      success = client.download_video(result.task_id, download_path)
      generation_time = time.time() - start_time
      client.close()

      if success:
        return VideoResult(
          success=True,
          path=download_path,
          backend=backend,
          prompt=prompt,
          duration=duration,
          generation_time=generation_time
        )
      else:
        return VideoResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          error="Failed to download video"
        )

    except Exception as e:
      return VideoResult(
        success=False,
        path=None,
        backend=backend,
        prompt=prompt,
        error=str(e)
      )

  def check_wan22_beta(self) -> dict:
    """Check ComfyUI on BETA health"""
    from .comfyui import ComfyUIClient
    try:
      client = ComfyUIClient(host=COMFYUI_BETA.host, port=COMFYUI_BETA.port)
      health = client.check_health()
      client.close()
      return health
    except Exception as e:
      return {"status": "error", "error": str(e)}

  def select_backend(
    self,
    priority: Literal["quality", "speed", "cost"],
    needs_audio: bool = False,
    needs_1080p: bool = False,
    needs_multishot: bool = False,
    is_hero_shot: bool = False
  ) -> VideoBackend:
    """
    Smart routing based on requirements and priority

    Args:
      priority: What to optimize for (quality, speed, cost)
      needs_audio: Requires synchronized audio
      needs_1080p: Requires 1080p resolution
      needs_multishot: Requires multi-lens narrative
      is_hero_shot: Is this a hero/key shot

    Returns:
      Recommended backend
    """
    # Premium features require Wan 2.6 API
    if needs_multishot:
      return VideoBackend.WAN26_MULTISHOT
    if needs_audio:
      return VideoBackend.WAN26_AUDIO
    if needs_1080p:
      return VideoBackend.WAN26_1080P

    # Speed priority → Wan 2.6 API (fastest turnaround ~1 min)
    if priority == "speed":
      return VideoBackend.WAN26_720P

    # Cost priority → Local (free)
    if priority == "cost":
      return VideoBackend.WAN22_BETA  # Free, 720p

    # Quality priority or hero shot → GAMMA (highest quality)
    if priority == "quality" or is_hero_shot:
      return VideoBackend.GAMMA_HIGH

    # Default: local Wan 2.2 (free, good quality)
    return VideoBackend.WAN22_BETA

  def list_gamma_videos(self) -> list[dict]:
    """List videos on GAMMA server"""
    try:
      response = httpx.get(f"{self.gamma_url}/videos/list", timeout=10)
      return response.json().get("videos", [])
    except Exception:
      return []
