"""
Wan 2.6 Cloud API Client
PiAPI integration for premium video generation features

Features:
- Text-to-Video (T2V): Up to 15 seconds, 1080p, with audio
- Image-to-Video (I2V): Animate images with motion
- Reference-to-Video (R2V): Character/object preservation

Pricing (as of 2025):
- 720p: $0.08/second
- 1080p: $0.12/second
"""

import os
import time
import logging
import httpx
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal, Callable, TypeVar
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_with_backoff(
  max_retries: int = 3,
  initial_delay: float = 1.0,
  backoff_factor: float = 2.0,
  retryable_exceptions: tuple = (httpx.TimeoutException, httpx.ConnectError)
) -> Callable:
  """
  Decorator for retry logic with exponential backoff.

  Args:
    max_retries: Maximum number of retry attempts
    initial_delay: Initial delay between retries (seconds)
    backoff_factor: Multiplier for delay after each retry
    retryable_exceptions: Exceptions that trigger retry
  """
  def decorator(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
      delay = initial_delay
      last_exception = None

      for attempt in range(max_retries + 1):
        try:
          return func(*args, **kwargs)
        except retryable_exceptions as e:
          last_exception = e
          if attempt < max_retries:
            logger.warning(
              f"{func.__name__} attempt {attempt + 1} failed: {e}. "
              f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)
            delay *= backoff_factor
          else:
            logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
        except httpx.HTTPStatusError as e:
          # Retry on rate limiting (429) and server errors (5xx)
          if e.response.status_code == 429 or e.response.status_code >= 500:
            last_exception = e
            if attempt < max_retries:
              # Use longer delay for rate limiting
              retry_delay = delay * 2 if e.response.status_code == 429 else delay
              logger.warning(
                f"{func.__name__} HTTP {e.response.status_code}. "
                f"Retrying in {retry_delay:.1f}s..."
              )
              time.sleep(retry_delay)
              delay *= backoff_factor
            else:
              logger.error(f"{func.__name__} failed with HTTP {e.response.status_code}")
          else:
            raise  # Don't retry client errors (4xx except 429)

      raise last_exception if last_exception else RuntimeError("Retry failed")
    return wrapper
  return decorator

class Wan26TaskType(str, Enum):
  """Wan 2.6 API task types"""
  TEXT_TO_VIDEO = "wan26-txt2video"
  IMAGE_TO_VIDEO = "wan26-img2video"
  REFERENCE_TO_VIDEO = "wan26-ref2video"

@dataclass
class Wan26Result:
  """Result of Wan 2.6 API generation"""
  success: bool
  task_id: str
  video_url: Optional[str]
  status: str
  prompt: str
  resolution: str
  duration: int
  cost_estimate: float
  error: Optional[str] = None
  audio_url: Optional[str] = None

class Wan26APIClient:
  """
  Wan 2.6 cloud API client for premium video generation

  Usage:
    client = Wan26APIClient()

    # Text-to-video with audio
    result = client.text_to_video(
      prompt="A cinematic shot of a robot in a futuristic city",
      duration=5,
      resolution="720P",
      with_audio=True
    )

    # Wait for completion and download
    if client.wait_for_completion(result.task_id):
      client.download_video(result.task_id, Path("output.mp4"))

    # Image-to-video
    result = client.image_to_video(
      image_url="https://example.com/image.png",
      prompt="The scene comes alive with motion",
      duration=5
    )

    # Reference-to-video (character preservation)
    result = client.reference_to_video(
      reference_url="https://example.com/reference.mp4",
      prompt="The character walks through a new environment"
    )
  """

  BASE_URL = "https://api.piapi.ai"

  # Pricing per second
  PRICING = {
    "720P": 0.08,
    "1080P": 0.12
  }

  def __init__(self, api_key: Optional[str] = None):
    """
    Initialize Wan 2.6 API client

    Args:
      api_key: PiAPI API key (defaults to WAN26_API_KEY env var)
    """
    self.api_key = api_key or os.getenv("WAN26_API_KEY")
    if not self.api_key:
      raise ValueError(
        "Wan 2.6 API key required. Set WAN26_API_KEY environment variable "
        "or pass api_key parameter. Get key from https://piapi.ai"
      )

    self.client = httpx.Client(
      base_url=self.BASE_URL,
      headers={
        "X-API-Key": self.api_key,
        "Content-Type": "application/json"
      },
      timeout=120.0
    )
    logger.info("Wan26APIClient initialized")

  @retry_with_backoff(max_retries=3, initial_delay=2.0, backoff_factor=2.0)
  def _post_with_retry(self, endpoint: str, json_data: dict) -> httpx.Response:
    """POST request with retry logic"""
    response = self.client.post(endpoint, json=json_data)
    response.raise_for_status()
    return response

  @retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
  def _get_with_retry(self, endpoint: str) -> httpx.Response:
    """GET request with retry logic"""
    response = self.client.get(endpoint)
    response.raise_for_status()
    return response

  def _calculate_cost(self, duration: int, resolution: str) -> float:
    """Calculate estimated cost for generation"""
    rate = self.PRICING.get(resolution, 0.08)
    return duration * rate

  def _submit_task(
    self,
    task_type: Wan26TaskType,
    input_params: dict,
    webhook_url: Optional[str] = None
  ) -> Wan26Result:
    """Submit a generation task to the API"""
    request_body = {
      "model": "Wan",
      "task_type": task_type.value,
      "input": input_params
    }

    if webhook_url:
      request_body["config"] = {
        "webhook_config": {"endpoint": webhook_url}
      }

    try:
      response = self._post_with_retry("/api/v1/task", request_body)
      data = response.json()
      logger.info(f"Task submitted: {data.get('data', {}).get('task_id', 'unknown')}")

      if data.get("code") != 200:
        return Wan26Result(
          success=False,
          task_id="",
          video_url=None,
          status="failed",
          prompt=input_params.get("prompt", ""),
          resolution=input_params.get("resolution", "720P"),
          duration=input_params.get("duration", 5),
          cost_estimate=0,
          error=data.get("message", "Unknown error")
        )

      task_data = data.get("data", {})
      return Wan26Result(
        success=True,
        task_id=task_data.get("task_id", ""),
        video_url=None,  # Will be available after completion
        status=task_data.get("status", "pending"),
        prompt=input_params.get("prompt", ""),
        resolution=input_params.get("resolution", "720P"),
        duration=input_params.get("duration", 5),
        cost_estimate=self._calculate_cost(
          input_params.get("duration", 5),
          input_params.get("resolution", "720P")
        )
      )

    except httpx.HTTPStatusError as e:
      return Wan26Result(
        success=False,
        task_id="",
        video_url=None,
        status="error",
        prompt=input_params.get("prompt", ""),
        resolution=input_params.get("resolution", "720P"),
        duration=input_params.get("duration", 5),
        cost_estimate=0,
        error=f"HTTP error: {e.response.status_code}"
      )
    except Exception as e:
      return Wan26Result(
        success=False,
        task_id="",
        video_url=None,
        status="error",
        prompt=input_params.get("prompt", ""),
        resolution=input_params.get("resolution", "720P"),
        duration=input_params.get("duration", 5),
        cost_estimate=0,
        error=str(e)
      )

  def text_to_video(
    self,
    prompt: str,
    duration: int = 5,
    resolution: str = "720P",
    aspect_ratio: str = "16:9",
    with_audio: bool = True,
    multi_shot: bool = False,
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    prompt_extend: bool = True
  ) -> Wan26Result:
    """
    Generate video from text prompt

    Args:
      prompt: Text description of desired video
      duration: Video length (5, 10, or 15 seconds)
      resolution: Output resolution ("720P" or "1080P")
      aspect_ratio: "16:9", "9:16", "1:1", "4:3", or "3:4"
      with_audio: Generate synchronized audio
      multi_shot: Enable multi-lens narrative mode
      negative_prompt: What to avoid in generation
      seed: Reproducibility seed (0-2147483647)
      prompt_extend: Auto-extend short prompts

    Returns:
      Wan26Result with task_id for status checking
    """
    input_params = {
      "prompt": prompt,
      "duration": duration,
      "resolution": resolution,
      "aspect_ratio": aspect_ratio,
      "audio": with_audio,
      "shot_type": "multi" if multi_shot else "single",
      "prompt_extend": prompt_extend,
      "watermark": False
    }

    if negative_prompt:
      input_params["negative_prompt"] = negative_prompt
    if seed is not None:
      input_params["seed"] = seed

    return self._submit_task(Wan26TaskType.TEXT_TO_VIDEO, input_params)

  def image_to_video(
    self,
    image_url: str,
    prompt: str,
    duration: int = 5,
    resolution: str = "720P",
    aspect_ratio: str = "16:9",
    with_audio: bool = False,
    seed: Optional[int] = None
  ) -> Wan26Result:
    """
    Animate an image into video

    Args:
      image_url: URL of source image
      prompt: Motion/action description
      duration: Video length (5, 10, or 15 seconds)
      resolution: Output resolution
      aspect_ratio: Output aspect ratio
      with_audio: Generate synchronized audio
      seed: Reproducibility seed

    Returns:
      Wan26Result with task_id
    """
    input_params = {
      "image_url": image_url,
      "prompt": prompt,
      "duration": duration,
      "resolution": resolution,
      "aspect_ratio": aspect_ratio,
      "audio": with_audio,
      "watermark": False
    }

    if seed is not None:
      input_params["seed"] = seed

    return self._submit_task(Wan26TaskType.IMAGE_TO_VIDEO, input_params)

  def reference_to_video(
    self,
    reference_url: str,
    prompt: str,
    duration: int = 5,
    resolution: str = "720P",
    with_audio: bool = False
  ) -> Wan26Result:
    """
    Generate video preserving character/object from reference

    Note: R2V supports up to 10 seconds max (vs 15 for T2V/I2V)

    Args:
      reference_url: URL of reference video (up to 5 seconds)
      prompt: Scene/action description
      duration: Video length (5 or 10 seconds max)
      resolution: Output resolution
      with_audio: Generate synchronized audio

    Returns:
      Wan26Result with task_id
    """
    # R2V max duration is 10 seconds
    duration = min(duration, 10)

    input_params = {
      "video_url": reference_url,
      "prompt": prompt,
      "duration": duration,
      "resolution": resolution,
      "audio": with_audio,
      "watermark": False
    }

    return self._submit_task(Wan26TaskType.REFERENCE_TO_VIDEO, input_params)

  def get_task_status(self, task_id: str) -> dict:
    """
    Check status of a generation task

    Args:
      task_id: Task ID from submit response

    Returns:
      Task status dict with video_url when complete
    """
    try:
      response = self._get_with_retry(f"/api/v1/task/{task_id}")
      data = response.json()

      if data.get("code") != 200:
        logger.warning(f"Task {task_id} status check failed: {data.get('message')}")
        return {"status": "error", "error": data.get("message")}

      task_data = data.get("data", {})
      output = task_data.get("output", {})
      status = task_data.get("status", "unknown")

      logger.debug(f"Task {task_id} status: {status}")

      return {
        "status": status,
        "video_url": output.get("video_url") if output else None,
        "audio_url": output.get("audio_url") if output else None,
        "error": task_data.get("error", {}).get("message") if task_data.get("error") else None
      }

    except httpx.HTTPStatusError as e:
      logger.error(f"HTTP error checking task {task_id}: {e.response.status_code}")
      return {"status": "error", "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
      logger.error(f"Error checking task {task_id}: {e}")
      return {"status": "error", "error": str(e)}

  def wait_for_completion(
    self,
    task_id: str,
    timeout: int = 300,
    poll_interval: int = 5
  ) -> Optional[str]:
    """
    Wait for task completion and return video URL

    Args:
      task_id: Task ID to monitor
      timeout: Max wait time in seconds
      poll_interval: Seconds between status checks

    Returns:
      Video URL if successful, None if failed/timeout
    """
    start_time = time.time()
    logger.info(f"Waiting for task {task_id} (timeout: {timeout}s)")

    while time.time() - start_time < timeout:
      status = self.get_task_status(task_id)
      elapsed = int(time.time() - start_time)

      if status.get("status") in ("Completed", "completed"):
        logger.info(f"Task {task_id} completed in {elapsed}s")
        return status.get("video_url")

      if status.get("status") in ("Failed", "failed"):
        logger.error(f"Task {task_id} failed: {status.get('error', 'unknown')}")
        return None

      time.sleep(poll_interval)

    logger.warning(f"Task {task_id} timed out after {timeout}s")
    return None

  def download_video(
    self,
    task_id: str,
    output_path: Path,
    include_audio: bool = True
  ) -> bool:
    """
    Download completed video to local path

    Args:
      task_id: Task ID of completed generation
      output_path: Local path to save video
      include_audio: Download audio track separately (if available)

    Returns:
      True if download successful
    """
    status = self.get_task_status(task_id)

    if status.get("status") not in ("Completed", "completed"):
      return False

    video_url = status.get("video_url")
    if not video_url:
      return False

    try:
      # Download video
      logger.info(f"Downloading video from task {task_id}")
      response = httpx.get(video_url, timeout=120.0)
      response.raise_for_status()

      output_path.parent.mkdir(parents=True, exist_ok=True)
      output_path.write_bytes(response.content)
      logger.info(f"Video saved to {output_path} ({len(response.content) / 1e6:.1f}MB)")

      # Download audio if available and requested
      audio_url = status.get("audio_url")
      if include_audio and audio_url:
        audio_path = output_path.with_suffix(".audio.mp3")
        audio_response = httpx.get(audio_url, timeout=60.0)
        audio_response.raise_for_status()
        audio_path.write_bytes(audio_response.content)
        logger.info(f"Audio saved to {audio_path}")

      return True

    except httpx.HTTPStatusError as e:
      logger.error(f"HTTP error downloading video: {e.response.status_code}")
      return False
    except httpx.TimeoutException:
      logger.error("Timeout downloading video")
      return False
    except IOError as e:
      logger.error(f"IO error saving video: {e}")
      return False
    except Exception as e:
      logger.error(f"Unexpected error downloading video: {e}")
      return False

  def close(self):
    """Close HTTP client"""
    self.client.close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
