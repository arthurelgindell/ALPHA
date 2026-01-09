"""
Image Generation Backends
Wraps FLUX.1 (local) and Gemini Pro Image (API)
"""

from pathlib import Path
from enum import Enum
from typing import Optional, Literal
from dataclasses import dataclass
import subprocess
import tempfile

from ..config import PATHS, FLUX_LOCAL, GEMINI_IMAGE
from ..output.manager import OutputManager, OutputType

class ImageBackend(str, Enum):
  """Available image generation backends"""
  FLUX_SCHNELL = "flux-schnell"      # Fast, local, Apache 2.0
  FLUX_DEV = "flux-dev"              # High quality, local, non-commercial
  GEMINI_PRO = "gemini-pro"          # API, complex scenes

# Resolution presets (FLUX-optimized, divisible by 64)
PRESETS = {
  "1:1": (1024, 1024),       # Square
  "4:3": (1152, 896),        # Standard
  "3:2": (1216, 832),        # Photo
  "16:9": (1344, 768),       # HD
  "16:9-large": (1920, 1088),# Full HD
  "21:9": (1536, 640),       # Ultrawide
  "9:16": (768, 1344),       # Vertical/mobile
  "4:5": (1024, 1280),       # LinkedIn carousel (divisible by 64)
}

@dataclass
class ImageResult:
  """Result of image generation"""
  success: bool
  path: Optional[Path]
  backend: ImageBackend
  prompt: str
  resolution: str
  error: Optional[str] = None

class ImageGenerator:
  """
  Unified image generation interface

  Usage:
    gen = ImageGenerator()

    # Quick generation with FLUX
    result = gen.generate(
      prompt="Product shot of laptop on desk",
      backend=ImageBackend.FLUX_SCHNELL,
      preset="16:9-large"
    )

    # Complex scene with Gemini
    result = gen.generate_gemini(
      prompt="Detailed SCALS prompt...",
      aspect_ratio="1:1"
    )
  """

  def __init__(self, output_manager: Optional[OutputManager] = None):
    self.output_manager = output_manager or OutputManager()
    self.scripts_dir = PATHS.scripts_dir

  def generate(
    self,
    prompt: str,
    backend: ImageBackend = ImageBackend.FLUX_SCHNELL,
    preset: str = "16:9-large",
    width: Optional[int] = None,
    height: Optional[int] = None,
    steps: Optional[int] = None,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
  ) -> ImageResult:
    """
    Generate image using FLUX backend

    Args:
      prompt: Text prompt
      backend: FLUX model to use
      preset: Resolution preset (ignored if width/height provided)
      width: Custom width (must be divisible by 64)
      height: Custom height (must be divisible by 64)
      steps: Number of inference steps
      seed: Random seed for reproducibility
      output_path: Custom output path

    Returns:
      ImageResult with path and metadata
    """
    # Determine resolution
    if width and height:
      res_width, res_height = width, height
    else:
      res_width, res_height = PRESETS.get(preset, PRESETS["16:9-large"])

    # Determine model
    model = "schnell" if backend == ImageBackend.FLUX_SCHNELL else "dev"

    # Build command
    cmd = [
      "python3",
      str(self.scripts_dir / "generate_image.py"),
      prompt,
      "--model", model,
      "--width", str(res_width),
      "--height", str(res_height),
    ]

    if steps:
      cmd.extend(["--steps", str(steps)])

    if seed:
      cmd.extend(["--seed", str(seed)])

    if output_path:
      cmd.extend(["--output", str(output_path)])

    # Run generation
    try:
      result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
      )

      if result.returncode == 0:
        # Parse output path from stdout
        for line in result.stdout.split('\n'):
          if 'Saved to:' in line:
            path_str = line.split('Saved to:')[1].strip()
            return ImageResult(
              success=True,
              path=Path(path_str),
              backend=backend,
              prompt=prompt,
              resolution=f"{res_width}x{res_height}"
            )

        # Fallback: check default output location
        if output_path and output_path.exists():
          return ImageResult(
            success=True,
            path=output_path,
            backend=backend,
            prompt=prompt,
            resolution=f"{res_width}x{res_height}"
          )

        return ImageResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          resolution=f"{res_width}x{res_height}",
          error="Could not determine output path"
        )

      else:
        return ImageResult(
          success=False,
          path=None,
          backend=backend,
          prompt=prompt,
          resolution=f"{res_width}x{res_height}",
          error=result.stderr
        )

    except subprocess.TimeoutExpired:
      return ImageResult(
        success=False,
        path=None,
        backend=backend,
        prompt=prompt,
        resolution=f"{res_width}x{res_height}",
        error="Generation timed out"
      )
    except Exception as e:
      return ImageResult(
        success=False,
        path=None,
        backend=backend,
        prompt=prompt,
        resolution=f"{res_width}x{res_height}",
        error=str(e)
      )

  def generate_gemini(
    self,
    prompt: str,
    aspect_ratio: str = "16:9",
    output_filename: Optional[str] = None
  ) -> ImageResult:
    """
    Generate image using Gemini Pro Image API

    Args:
      prompt: SCALS-formatted prompt
      aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)
      output_filename: Custom output filename

    Returns:
      ImageResult with path and metadata
    """
    # Import Gemini client
    try:
      from google import genai
      from google.genai import types
    except ImportError:
      return ImageResult(
        success=False,
        path=None,
        backend=ImageBackend.GEMINI_PRO,
        prompt=prompt,
        resolution=f"1024x1024 ({aspect_ratio})",
        error="google-genai package not installed"
      )

    try:
      client = genai.Client(api_key=GEMINI_IMAGE.api_key)

      response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
          response_modalities=["IMAGE"],
          image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
          tools=[types.Tool(google_search=types.GoogleSearch())]
        )
      )

      # Save image
      if output_filename is None:
        from datetime import datetime
        output_filename = f"gemini_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

      output_path = PATHS.images_dir / output_filename

      if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
          if hasattr(part, 'inline_data') and part.inline_data:
            with open(output_path, 'wb') as f:
              f.write(part.inline_data.data)

            return ImageResult(
              success=True,
              path=output_path,
              backend=ImageBackend.GEMINI_PRO,
              prompt=prompt,
              resolution=f"1024x1024 ({aspect_ratio})"
            )

      return ImageResult(
        success=False,
        path=None,
        backend=ImageBackend.GEMINI_PRO,
        prompt=prompt,
        resolution=f"1024x1024 ({aspect_ratio})",
        error="No image in response"
      )

    except Exception as e:
      return ImageResult(
        success=False,
        path=None,
        backend=ImageBackend.GEMINI_PRO,
        prompt=prompt,
        resolution=f"1024x1024 ({aspect_ratio})",
        error=str(e)
      )

  def select_backend(
    self,
    complexity: Literal["simple", "moderate", "complex"],
    needs_text: bool = False,
    needs_consistency: bool = False
  ) -> ImageBackend:
    """
    Select appropriate backend based on requirements

    Args:
      complexity: Scene complexity
      needs_text: Requires accurate text rendering
      needs_consistency: Requires character/brand consistency

    Returns:
      Recommended backend
    """
    # Gemini for complex scenes, text, or consistency
    if complexity == "complex" or needs_text or needs_consistency:
      return ImageBackend.GEMINI_PRO

    # FLUX for fast iteration and backgrounds
    return ImageBackend.FLUX_SCHNELL
