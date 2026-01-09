"""
ARTHUR Configuration
Central configuration for all infrastructure endpoints and settings
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
import os

# ============================================================================
# Infrastructure Endpoints
# ============================================================================

@dataclass
class LMStudioEndpoint:
  """LM Studio server configuration"""
  name: str
  host: str
  role: Literal["strategist", "executor"]
  port: int = 1234
  description: str = ""

  @property
  def base_url(self) -> str:
    return f"http://{self.host}:{self.port}/v1"


@dataclass
class VisionEndpoint:
  """Vision model server configuration (Tailscale HTTPS)"""
  name: str
  base_url: str
  model_id: str
  description: str = ""

@dataclass
class GenerationEndpoint:
  """Media generation backend configuration"""
  name: str
  endpoint_type: Literal["local", "api", "remote"]
  host: str = ""
  port: int = 0
  api_key: str = ""

  @property
  def url(self) -> str:
    if self.endpoint_type == "remote":
      return f"http://{self.host}:{self.port}"
    return ""

# ============================================================================
# Default Infrastructure Configuration
# ============================================================================

# LM Studio Endpoints
ALPHA_LM = LMStudioEndpoint(
  name="DeepSeek V3.1",
  host="100.65.29.44",
  port=1234,
  role="strategist",
  description="Strategic planning, complex reasoning, storyboarding"
)

BETA_LM = LMStudioEndpoint(
  name="Nemotron",
  host="100.84.202.68",
  port=1234,
  role="executor",
  description="Structured output, prompt engineering, task execution"
)

# Vision Model Endpoint (GLM-4.6V-Flash)
# Use local endpoint when running on ALPHA, Tailscale for cross-node
VISION_ALPHA = VisionEndpoint(
  name="GLM-4.6V-Flash",
  base_url="http://127.0.0.1:1234/v1",  # Local LM Studio (faster than Tailscale)
  model_id="glm-4.6v-flash",
  description="Vision-language model for image/video analysis"
)

# Alternative: Tailscale endpoint for cross-node access
# VISION_ALPHA_TAILSCALE = VisionEndpoint(
#   name="GLM-4.6V-Flash",
#   base_url="https://alpha.tail5f2bae.ts.net/v1",
#   model_id="glm-4.6v-flash",
#   description="Vision-language model (Tailscale HTTPS)"
# )

# ============================================================================
# Media Generation Endpoints (Production-Grade Only)
# ============================================================================
# NOTE: FLUX.1 and Wan 2.2 REMOVED 2026-01-06 - quality unacceptable for
# professional content. See decisions.md for rationale.

# Image Generation - Gemini Pro (API)
GEMINI_IMAGE = GenerationEndpoint(
  name="Gemini Pro Image",
  endpoint_type="api",
  api_key=os.getenv("GEMINI_API_KEY", "")
)

# Video Generation - GAMMA HunyuanVideo (Local, free)
GAMMA_VIDEO = GenerationEndpoint(
  name="HunyuanVideo-1.5",
  endpoint_type="remote",
  host="100.102.59.5",
  port=8421
)

# Video Generation - Veo 3.1 (API, premium quality)
VEO_VIDEO = GenerationEndpoint(
  name="Veo 3.1",
  endpoint_type="api",
  api_key=os.getenv("GEMINI_API_KEY", "")
)

# Video Generation - Wan 2.6 API (production-grade)
WAN26_API = GenerationEndpoint(
  name="Wan 2.6 API",
  endpoint_type="api",
  api_key=os.getenv("WAN26_API_KEY", "")
)

# ============================================================================
# DEPRECATED - DO NOT USE
# ============================================================================
# FLUX_LOCAL - Removed: Artifacts, incoherent text, unreliable
# COMFYUI_BETA - Removed: Wan 2.2 quality unacceptable
# COMFYUI_GAMMA - Removed: Wan 2.2 quality unacceptable

# ============================================================================
# Voice Generation (F5-TTS on BETA)
# ============================================================================

@dataclass
class VoiceConfig:
  """Voice generation configuration for F5-TTS on BETA"""
  beta_host: str = "beta"
  python_env: str = "/Volumes/MODELS/mlx-env/bin/python3"
  tts_script: str = "/Volumes/CLAUDE/SPHERE/scripts/voice-pro.py"
  output_dir: str = "/Volumes/MODELS/tts/output"
  reference_voice: str = "/Volumes/MODELS/tts/reference/default_voice.wav"

VOICE = VoiceConfig()

# ============================================================================
# Postmark Email Configuration
# ============================================================================

@dataclass
class PostmarkConfig:
  """Postmark email notification configuration"""
  server_token: str = field(default_factory=lambda: os.getenv("POSTMARK_SERVER_TOKEN", ""))
  default_sender: str = "alerts@dellight.ai"
  default_recipient: str = "arthur.dell@dellight.ai"

POSTMARK = PostmarkConfig()

# ============================================================================
# Paths Configuration
# ============================================================================

@dataclass
class PathConfig:
  """File system paths configuration"""
  project_root: Path = field(default_factory=lambda: Path("/Users/arthurdell/ARTHUR"))

  @property
  def scripts_dir(self) -> Path:
    return self.project_root / "scripts"

  @property
  def images_dir(self) -> Path:
    return self.project_root / "images"

  @property
  def videos_dir(self) -> Path:
    return self.project_root / "videos"

  @property
  def carousels_dir(self) -> Path:
    return self.project_root / "carousels"

  @property
  def studio_mount(self) -> Path:
    """Remote STUDIO volume on BETA"""
    return Path("/Volumes/STUDIO")

  @property
  def studio_video(self) -> Path:
    return self.studio_mount / "VIDEO"

  @property
  def studio_images(self) -> Path:
    return self.studio_mount / "IMAGES"

  @property
  def studio_carousels(self) -> Path:
    return self.studio_mount / "CAROUSELS"

  def ensure_dirs(self):
    """Create local directories if they don't exist"""
    for d in [self.images_dir, self.videos_dir, self.carousels_dir]:
      d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Design System
# ============================================================================

@dataclass
class DesignSystem:
  """Visual design system for outputs"""
  background_dark: str = "#1a1a1a"
  background_light: str = "#2d2d2d"
  accent_amber: str = "#f59e0b"
  text_primary: str = "#ffffff"
  text_secondary: str = "#a0a0a0"
  font_header: str = "Inter"
  font_body: str = "system-ui, sans-serif"

# ============================================================================
# Global Config Instance
# ============================================================================

PATHS = PathConfig()
DESIGN = DesignSystem()
