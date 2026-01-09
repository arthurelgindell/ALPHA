"""
Vision Model Client for GLM-4.6V-Flash
Provides image analysis via OpenAI-compatible API through Tailscale Serve
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
import base64
import logging
import httpx
from openai import OpenAI

from ..config import VISION_ALPHA

logger = logging.getLogger(__name__)

# MIME type mapping for image encoding
MIME_TYPES = {
  'png': 'image/png',
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
  'gif': 'image/gif',
  'webp': 'image/webp',
  'bmp': 'image/bmp',
}


@dataclass
class VisionResult:
  """Result of vision analysis"""
  success: bool
  analysis: str
  model: str
  prompt: str
  image_path: Optional[Path] = None
  error: Optional[str] = None
  usage: Optional[dict] = field(default_factory=dict)

  def __str__(self) -> str:
    if self.success:
      return self.analysis
    return f"Error: {self.error}"


class VisionClient:
  """
  OpenAI-compatible client for GLM-4.6V-Flash vision model

  Usage:
    client = VisionClient()

    # Analyze single image
    result = client.analyze_image(
      image_path="/path/to/image.png",
      prompt="What device is shown? Is it a Mac Studio or iMac?"
    )

    # Analyze with high detail
    result = client.analyze_image(
      image_path="/path/to/image.png",
      prompt="Describe the product in detail",
      detail="high"
    )
  """

  def __init__(
    self,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = 120.0
  ):
    """
    Initialize vision client

    Args:
      base_url: Override default endpoint (default: VISION_ALPHA.base_url)
      model: Override default model ID (default: VISION_ALPHA.model_id)
      timeout: Request timeout in seconds
    """
    self.base_url = base_url or VISION_ALPHA.base_url
    self.model = model or VISION_ALPHA.model_id
    self.timeout = timeout

    self._client = OpenAI(
      base_url=self.base_url,
      api_key="lm-studio",  # LM Studio ignores API key
      timeout=timeout,
      http_client=httpx.Client(timeout=timeout)
    )

    logger.info(f"VisionClient initialized: {self.base_url} (model: {self.model})")

  def check_health(self) -> dict:
    """
    Check if vision endpoint is available

    Returns:
      dict with 'available', 'models', and 'error' keys
    """
    try:
      models = self._client.models.list()
      model_ids = [m.id for m in models.data]
      vision_available = any('v' in m.lower() or 'vision' in m.lower() for m in model_ids)
      return {
        "available": True,
        "vision_capable": vision_available,
        "models": model_ids,
        "error": None
      }
    except Exception as e:
      logger.error(f"Vision endpoint health check failed: {e}")
      return {
        "available": False,
        "vision_capable": False,
        "models": [],
        "error": str(e)
      }

  def _encode_image(self, image_path: Path) -> str:
    """
    Encode image to base64 data URL

    Args:
      image_path: Path to image file

    Returns:
      Data URL string (data:image/png;base64,...)
    """
    image_path = Path(image_path)

    if not image_path.exists():
      raise FileNotFoundError(f"Image not found: {image_path}")

    ext = image_path.suffix.lstrip('.').lower()
    mime_type = MIME_TYPES.get(ext, 'image/png')

    with open(image_path, 'rb') as f:
      image_data = base64.b64encode(f.read()).decode('utf-8')

    return f"data:{mime_type};base64,{image_data}"

  def analyze_image(
    self,
    image_path: Path | str,
    prompt: str,
    detail: Literal["low", "high"] = "low",
    temperature: float = 0.3,
    max_tokens: int = 1024
  ) -> VisionResult:
    """
    Analyze a single image

    Args:
      image_path: Path to image file (PNG, JPEG, WebP, etc.)
      prompt: Analysis prompt/question
      detail: Image detail level ("low" for faster, "high" for detailed)
      temperature: Sampling temperature (lower = more deterministic)
      max_tokens: Maximum response tokens

    Returns:
      VisionResult with analysis text
    """
    image_path = Path(image_path)

    try:
      # Encode image to base64 data URL
      image_url = self._encode_image(image_path)

      # Build multimodal message
      messages = [
        {
          "role": "user",
          "content": [
            {"type": "text", "text": prompt},
            {
              "type": "image_url",
              "image_url": {
                "url": image_url,
                "detail": detail
              }
            }
          ]
        }
      ]

      logger.debug(f"Analyzing image: {image_path} with prompt: {prompt[:50]}...")

      # Call vision model
      response = self._client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
      )

      analysis = response.choices[0].message.content
      usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0
      }

      logger.info(f"Image analysis complete: {len(analysis)} chars, {usage.get('total_tokens', 0)} tokens")

      return VisionResult(
        success=True,
        analysis=analysis,
        model=self.model,
        prompt=prompt,
        image_path=image_path,
        usage=usage
      )

    except FileNotFoundError as e:
      logger.error(f"Image file not found: {e}")
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=prompt,
        image_path=image_path,
        error=str(e)
      )

    except httpx.TimeoutException:
      logger.error(f"Vision model request timed out after {self.timeout}s")
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=prompt,
        image_path=image_path,
        error=f"Request timed out after {self.timeout}s. Model may be loading."
      )

    except httpx.ConnectError as e:
      logger.error(f"Cannot connect to vision endpoint: {e}")
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=prompt,
        image_path=image_path,
        error=f"Cannot connect to vision endpoint at {self.base_url}. Is LM Studio running?"
      )

    except Exception as e:
      logger.error(f"Vision analysis failed: {e}")
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=prompt,
        image_path=image_path,
        error=f"Unexpected error: {e}"
      )

  def analyze_batch(
    self,
    image_paths: list[Path | str],
    prompt: str,
    detail: Literal["low", "high"] = "low"
  ) -> list[VisionResult]:
    """
    Analyze multiple images with the same prompt

    Args:
      image_paths: List of image paths
      prompt: Analysis prompt for all images

    Returns:
      List of VisionResult for each image
    """
    results = []
    for i, image_path in enumerate(image_paths):
      logger.info(f"Analyzing image {i+1}/{len(image_paths)}: {image_path}")
      result = self.analyze_image(image_path, prompt, detail=detail)
      results.append(result)

    successful = sum(1 for r in results if r.success)
    logger.info(f"Batch analysis complete: {successful}/{len(results)} successful")

    return results

  def compare_images(
    self,
    image_paths: list[Path | str],
    comparison_prompt: str,
    detail: Literal["low", "high"] = "low",
    max_tokens: int = 2048
  ) -> VisionResult:
    """
    Compare multiple images in a single request

    Args:
      image_paths: 2-4 images to compare
      comparison_prompt: What to compare

    Returns:
      VisionResult with comparison analysis
    """
    if len(image_paths) < 2:
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=comparison_prompt,
        error="Need at least 2 images to compare"
      )

    if len(image_paths) > 4:
      logger.warning(f"Too many images ({len(image_paths)}), using first 4")
      image_paths = image_paths[:4]

    try:
      # Build content array with text prompt and all images
      content = [{"type": "text", "text": comparison_prompt}]

      for i, image_path in enumerate(image_paths):
        image_url = self._encode_image(Path(image_path))
        content.append({
          "type": "image_url",
          "image_url": {"url": image_url, "detail": detail}
        })

      messages = [{"role": "user", "content": content}]

      response = self._client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=0.3,
        max_tokens=max_tokens
      )

      return VisionResult(
        success=True,
        analysis=response.choices[0].message.content,
        model=self.model,
        prompt=comparison_prompt,
        usage={
          "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
          "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        }
      )

    except Exception as e:
      logger.error(f"Image comparison failed: {e}")
      return VisionResult(
        success=False,
        analysis="",
        model=self.model,
        prompt=comparison_prompt,
        error=str(e)
      )
