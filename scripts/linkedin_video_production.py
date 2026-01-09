#!/usr/bin/env python3
"""
LinkedIn Video Series Production Pipeline
"The AI-Powered Professional Stack"

Generates video content using:
- BETA (Wan 2.2 14B): Local high-quality video generation (FREE)
- Wan 2.6 API: Cloud API for premium features (PAID)
- FLUX: Local image generation

Author: Arthur Dell
"""

import os
import sys
import json
import time
import httpx
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, Literal

# ============================================================================
# Configuration
# ============================================================================

BETA_URL = "http://192.168.70.16:8188"
WAN26_API_KEY = os.getenv("WAN26_API_KEY", "")
OUTPUT_BASE = Path("/Users/arthurdell/ARTHUR/videos/linkedin_series")
STUDIO_OUTPUT = Path("/Volumes/STUDIO/VIDEO/LinkedIn_TechStack_Series")

# Wan 2.2 Settings (optimized for 256GB Apple Silicon)
WAN22_CONFIG = {
  "max_frames": 97,      # ~6s at 16fps (conservative for stability)
  "default_frames": 81,  # ~5s at 16fps
  "fps": 16,
  "steps": 20,           # Total steps (split between high/low noise)
  "high_noise_steps": 10,  # Steps 0-10 use high noise model
  "cfg": 3.5,
  "shift": 8.0,
  "sampler": "euler",
  "scheduler": "simple",
  "resolution_720p": (1280, 720),
  "resolution_480p": (832, 480),
}

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class VideoPrompt:
  """A single video generation prompt"""
  id: str
  episode: int
  label: str
  prompt: str
  negative_prompt: str = "blurry, low quality, distorted, watermark, static, overexposed"
  backend: Literal["wan22", "wan26"] = "wan22"
  resolution: str = "720p"
  duration_target: float = 5.0  # seconds
  priority: Literal["hero", "detail", "b-roll"] = "detail"

@dataclass
class ProductionResult:
  """Result of video production"""
  prompt_id: str
  success: bool
  backend: str
  generation_time: float
  file_size_mb: float
  output_path: Optional[str]
  frames: int
  resolution: tuple
  error: Optional[str] = None
  prompt: str = ""

@dataclass
class ProductionBatch:
  """A batch of prompts for production"""
  name: str
  prompts: list[VideoPrompt] = field(default_factory=list)
  results: list[ProductionResult] = field(default_factory=list)

# ============================================================================
# Wan 2.2 Workflow Generator
# ============================================================================

def create_wan22_workflow(
  prompt: str,
  negative_prompt: str = "",
  width: int = 1280,
  height: int = 720,
  num_frames: int = 81,
  steps: int = 20,
  cfg: float = 3.5,
  seed: Optional[int] = None
) -> dict:
  """
  Create Wan 2.2 14B text-to-video workflow for ComfyUI

  Uses MoE architecture with two-stage sampling:
  1. High noise model (steps 0-10)
  2. Low noise model (steps 10+)
  """

  if seed is None:
    seed = random.randint(0, 2**31)

  if not negative_prompt:
    negative_prompt = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"

  high_steps = min(10, steps // 2)

  workflow = {
    # High Noise Model
    "37": {
      "inputs": {
        "unet_name": "wan2.2_t2v_high_noise_14B_fp16.safetensors",
        "weight_dtype": "default"
      },
      "class_type": "UNETLoader"
    },
    # Low Noise Model
    "56": {
      "inputs": {
        "unet_name": "wan2.2_t2v_low_noise_14B_fp16.safetensors",
        "weight_dtype": "default"
      },
      "class_type": "UNETLoader"
    },
    # CLIP Text Encoder
    "38": {
      "inputs": {
        "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "type": "wan",
        "device": "default"
      },
      "class_type": "CLIPLoader"
    },
    # VAE
    "39": {
      "inputs": {
        "vae_name": "wan_2.1_vae.safetensors"
      },
      "class_type": "VAELoader"
    },
    # Model Sampling for High Noise
    "54": {
      "inputs": {
        "model": ["37", 0],
        "shift": 8.0
      },
      "class_type": "ModelSamplingSD3"
    },
    # Model Sampling for Low Noise
    "55": {
      "inputs": {
        "model": ["56", 0],
        "shift": 8.0
      },
      "class_type": "ModelSamplingSD3"
    },
    # Positive Prompt
    "6": {
      "inputs": {
        "text": prompt,
        "clip": ["38", 0]
      },
      "class_type": "CLIPTextEncode"
    },
    # Negative Prompt
    "7": {
      "inputs": {
        "text": negative_prompt,
        "clip": ["38", 0]
      },
      "class_type": "CLIPTextEncode"
    },
    # Empty Latent Video
    "61": {
      "inputs": {
        "width": width,
        "height": height,
        "length": num_frames,
        "batch_size": 1
      },
      "class_type": "EmptyHunyuanLatentVideo"
    },
    # First Sampler (High Noise Model, steps 0-10)
    "57": {
      "inputs": {
        "model": ["54", 0],
        "positive": ["6", 0],
        "negative": ["7", 0],
        "latent_image": ["61", 0],
        "add_noise": "enable",
        "noise_seed": seed,
        "steps": steps,
        "cfg": cfg,
        "sampler_name": "euler",
        "scheduler": "simple",
        "start_at_step": 0,
        "end_at_step": high_steps,
        "return_with_leftover_noise": "enable"
      },
      "class_type": "KSamplerAdvanced"
    },
    # Second Sampler (Low Noise Model, steps 10+)
    "58": {
      "inputs": {
        "model": ["55", 0],
        "positive": ["6", 0],
        "negative": ["7", 0],
        "latent_image": ["57", 0],
        "add_noise": "disable",
        "noise_seed": 0,
        "steps": steps,
        "cfg": cfg,
        "sampler_name": "euler",
        "scheduler": "simple",
        "start_at_step": high_steps,
        "end_at_step": 10000,
        "return_with_leftover_noise": "disable"
      },
      "class_type": "KSamplerAdvanced"
    },
    # VAE Decode
    "8": {
      "inputs": {
        "samples": ["58", 0],
        "vae": ["39", 0]
      },
      "class_type": "VAEDecode"
    },
    # Save as WEBP Animation
    "28": {
      "inputs": {
        "images": ["8", 0],
        "filename_prefix": "linkedin",
        "fps": 16,
        "lossless": False,
        "quality": 85,
        "method": "default"
      },
      "class_type": "SaveAnimatedWEBP"
    },
    # Save as WEBM Video
    "47": {
      "inputs": {
        "images": ["8", 0],
        "filename_prefix": "linkedin",
        "codec": "vp9",
        "fps": 16,
        "crf": 23
      },
      "class_type": "SaveWEBM"
    }
  }

  return workflow

# ============================================================================
# BETA ComfyUI Client
# ============================================================================

class BetaComfyUIClient:
  """Client for BETA ComfyUI Wan 2.2 generation"""

  def __init__(self, base_url: str = BETA_URL):
    self.base_url = base_url
    self.client = httpx.Client(timeout=30.0)

  def check_health(self) -> dict:
    """Check BETA health"""
    try:
      response = self.client.get(f"{self.base_url}/system_stats")
      response.raise_for_status()
      data = response.json()
      return {
        "status": "healthy",
        "comfyui_version": data["system"]["comfyui_version"],
        "ram_free_gb": data["system"]["ram_free"] / 1024**3,
        "device": data["devices"][0]["name"]
      }
    except Exception as e:
      return {"status": "error", "error": str(e)}

  def submit_workflow(self, workflow: dict) -> Optional[str]:
    """Submit workflow and return prompt_id"""
    try:
      response = self.client.post(
        f"{self.base_url}/prompt",
        json={"prompt": workflow}
      )
      response.raise_for_status()
      return response.json().get("prompt_id")
    except Exception as e:
      print(f"Submit error: {e}")
      return None

  def get_queue_status(self) -> dict:
    """Get queue status"""
    try:
      response = self.client.get(f"{self.base_url}/queue")
      return response.json()
    except httpx.TimeoutException:
      return {"error": "timeout"}
    except Exception as e:
      print(f"Queue status error: {e}")
      return {}

  def get_history(self, prompt_id: str) -> Optional[dict]:
    """Get history for prompt"""
    try:
      response = self.client.get(f"{self.base_url}/history/{prompt_id}")
      data = response.json()
      return data.get(prompt_id)
    except httpx.TimeoutException:
      return None
    except Exception as e:
      print(f"History error for {prompt_id}: {e}")
      return None

  def wait_for_completion(self, prompt_id: str, timeout: int = 3600) -> Optional[dict]:
    """Wait for workflow completion"""
    start = time.time()

    while time.time() - start < timeout:
      history = self.get_history(prompt_id)

      if history:
        outputs = history.get("outputs", {})
        if outputs:
          return history

      # Progress update
      queue = self.get_queue_status()
      running = len(queue.get("queue_running", []))
      pending = len(queue.get("queue_pending", []))
      elapsed = time.time() - start
      print(f"\r  [{elapsed:.0f}s] Running: {running}, Pending: {pending}    ", end="", flush=True)

      time.sleep(5)

    return None

  def get_output_files(self, history: dict) -> list[str]:
    """Extract output filenames"""
    files = []
    outputs = history.get("outputs", {})

    for node_id, node_output in outputs.items():
      for key in ["gifs", "videos", "images"]:
        if key in node_output:
          for item in node_output[key]:
            if "filename" in item:
              files.append(item["filename"])

    return files

  def download_file(self, filename: str, output_path: Path) -> bool:
    """Download output file"""
    try:
      response = self.client.get(
        f"{self.base_url}/view",
        params={"filename": filename, "type": "output"},
        timeout=120.0
      )
      response.raise_for_status()
      output_path.parent.mkdir(parents=True, exist_ok=True)
      output_path.write_bytes(response.content)
      return True
    except Exception as e:
      print(f"Download error: {e}")
      return False

  def generate_video(
    self,
    prompt: str,
    negative_prompt: str = "",
    width: int = 1280,
    height: int = 720,
    num_frames: int = 81,
    steps: int = 20,
    output_dir: Path = OUTPUT_BASE
  ) -> ProductionResult:
    """Generate a single video"""

    print(f"\n{'='*60}")
    print(f"Generating: {prompt[:60]}...")
    print(f"Resolution: {width}x{height}, Frames: {num_frames}")

    # Create workflow
    workflow = create_wan22_workflow(
      prompt=prompt,
      negative_prompt=negative_prompt,
      width=width,
      height=height,
      num_frames=num_frames,
      steps=steps
    )

    # Submit
    start_time = time.time()
    prompt_id = self.submit_workflow(workflow)

    if not prompt_id:
      return ProductionResult(
        prompt_id="",
        success=False,
        backend="wan22-beta",
        generation_time=0,
        file_size_mb=0,
        output_path=None,
        frames=num_frames,
        resolution=(width, height),
        error="Failed to submit workflow",
        prompt=prompt
      )

    print(f"Submitted: {prompt_id}")

    # Wait for completion
    history = self.wait_for_completion(prompt_id)
    generation_time = time.time() - start_time

    print()  # Newline after progress

    if not history:
      return ProductionResult(
        prompt_id=prompt_id,
        success=False,
        backend="wan22-beta",
        generation_time=generation_time,
        file_size_mb=0,
        output_path=None,
        frames=num_frames,
        resolution=(width, height),
        error="Generation timed out",
        prompt=prompt
      )

    # Get output files
    output_files = self.get_output_files(history)

    if not output_files:
      return ProductionResult(
        prompt_id=prompt_id,
        success=False,
        backend="wan22-beta",
        generation_time=generation_time,
        file_size_mb=0,
        output_path=None,
        frames=num_frames,
        resolution=(width, height),
        error="No output files",
        prompt=prompt
      )

    # Download first output (prefer webm)
    webm_files = [f for f in output_files if f.endswith('.webm')]
    target_file = webm_files[0] if webm_files else output_files[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"wan22_{timestamp}_{target_file}"

    if self.download_file(target_file, output_path):
      file_size = output_path.stat().st_size / (1024 * 1024)

      print(f"✅ Generated: {output_path.name}")
      print(f"   Time: {generation_time:.1f}s, Size: {file_size:.2f}MB")

      return ProductionResult(
        prompt_id=prompt_id,
        success=True,
        backend="wan22-beta",
        generation_time=generation_time,
        file_size_mb=file_size,
        output_path=str(output_path),
        frames=num_frames,
        resolution=(width, height),
        prompt=prompt
      )

    return ProductionResult(
      prompt_id=prompt_id,
      success=False,
      backend="wan22-beta",
      generation_time=generation_time,
      file_size_mb=0,
      output_path=None,
      frames=num_frames,
      resolution=(width, height),
      error="Download failed",
      prompt=prompt
    )

# ============================================================================
# LinkedIn Series Prompts
# ============================================================================

EPISODE_1_PROMPTS = [
  VideoPrompt(
    id="ep1_hero_reveal",
    episode=1,
    label="Mac Studio Reveal",
    prompt="Cinematic product shot of two Mac Studio M3 Ultra computers side by side on minimal dark desk, warm amber accent lighting from above creating subtle rim light, deep charcoal background, professional studio lighting, shallow depth of field, subtle floating particle effects suggesting data flow, premium tech aesthetic, smooth slow push-in camera movement",
    backend="wan22",
    resolution="720p",
    priority="hero"
  ),
  VideoPrompt(
    id="ep1_macro_vent",
    episode=1,
    label="Mac Studio Macro",
    prompt="Close-up macro shot of Mac Studio M3 Ultra ventilation grille with soft amber light emerging from within, suggesting immense processing power, shallow depth of field, dust particles floating in light beam, cinematic atmosphere, slow drift camera movement, professional product photography aesthetic",
    backend="wan22",
    resolution="720p",
    priority="detail"
  ),
  VideoPrompt(
    id="ep1_power_shot",
    episode=1,
    label="Mac Studio Power",
    prompt="Dramatic low angle shot of Mac Studio M3 Ultra, hero lighting with strong amber key light, dark moody atmosphere, slight lens flare effect, suggesting power and capability, slow upward camera tilt, professional product photography, premium tech aesthetic",
    backend="wan22",
    resolution="720p",
    priority="hero"
  ),
]

EPISODE_2_PROMPTS = [
  VideoPrompt(
    id="ep2_dgx_reveal",
    episode=2,
    label="DGX Spark Reveal",
    prompt="Close-up of hands lifting NVIDIA DGX Spark from premium packaging, champagne gold finish catching warm light, dark professional environment, shallow depth of field, dust particles in air, premium unboxing aesthetic, smooth reveal motion, cinematic lighting",
    backend="wan22",
    resolution="720p",
    priority="hero"
  ),
  VideoPrompt(
    id="ep2_scale",
    episode=2,
    label="DGX Scale Context",
    prompt="DGX Spark device placed next to coffee cup for scale comparison, champagne gold finish, perforated metal grille texture, warm desk lamp lighting, professional workspace, shallow depth of field, gentle ambient movement, emphasizing compact size versus power",
    backend="wan22",
    resolution="720p",
    priority="detail"
  ),
]

EPISODE_3_PROMPTS = [
  VideoPrompt(
    id="ep3_neural_viz",
    episode=3,
    label="Neural Network Visualization",
    prompt="Abstract visualization of neural network processing, interconnected nodes pulsing with amber and teal light, deep charcoal background, flowing data streams, representing AI reasoning, elegant smooth flowing motion, premium tech aesthetic, geometric patterns",
    backend="wan22",
    resolution="720p",
    priority="hero"
  ),
  VideoPrompt(
    id="ep3_multi_model",
    episode=3,
    label="Multi-Model Flow",
    prompt="Abstract visualization of multiple AI models working together, color-coded data streams in amber and teal colors flowing and merging, dark background, suggesting orchestrated intelligence, smooth flowing motion, premium motion graphics aesthetic",
    backend="wan22",
    resolution="720p",
    priority="detail"
  ),
]

EPISODE_4_PROMPTS = [
  VideoPrompt(
    id="ep4_terminal",
    episode=4,
    label="Claude Code Terminal",
    prompt="Close-up of terminal window with code interface launching, amber text on dark background, command line aesthetic, professional developer environment, cursor blinking with smooth animation, code characters appearing, suggesting power about to be unleashed",
    backend="wan22",
    resolution="720p",
    priority="hero"
  ),
  VideoPrompt(
    id="ep4_agentic",
    episode=4,
    label="Agentic Coding",
    prompt="Multiple code windows appearing and being edited simultaneously on screen, suggesting autonomous coding agent at work, professional IDE environment with syntax highlighting, warm desk lighting reflection, rapid but elegant typing motion, smooth window transitions",
    backend="wan22",
    resolution="720p",
    priority="detail"
  ),
]

# Combine all prompts
ALL_PROMPTS = (
  EPISODE_1_PROMPTS +
  EPISODE_2_PROMPTS +
  EPISODE_3_PROMPTS +
  EPISODE_4_PROMPTS
)

# ============================================================================
# Main Production Functions
# ============================================================================

def run_benchmark(client: BetaComfyUIClient, num_videos: int = 3):
  """Run performance benchmark"""

  print("\n" + "="*70)
  print("LINKEDIN VIDEO SERIES - PERFORMANCE BENCHMARK")
  print("="*70)

  # Select benchmark prompts
  benchmark_prompts = ALL_PROMPTS[:num_videos]

  results = []
  total_frames = 0
  total_time = 0

  for i, vp in enumerate(benchmark_prompts, 1):
    print(f"\n[{i}/{len(benchmark_prompts)}] {vp.label}")

    # Calculate frames for ~5 second video
    num_frames = int(5 * 16)  # 5 seconds at 16fps = 80 frames

    # Get resolution
    if vp.resolution == "720p":
      width, height = 1280, 720
    else:
      width, height = 832, 480

    result = client.generate_video(
      prompt=vp.prompt,
      negative_prompt=vp.negative_prompt,
      width=width,
      height=height,
      num_frames=num_frames,
      steps=20,
      output_dir=OUTPUT_BASE / "benchmark"
    )

    results.append(result)

    if result.success:
      total_frames += result.frames
      total_time += result.generation_time

  # Print summary
  print("\n" + "="*70)
  print("BENCHMARK SUMMARY")
  print("="*70)

  successful = [r for r in results if r.success]
  failed = [r for r in results if not r.success]

  print(f"\nTotal: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}")

  if successful:
    avg_time = total_time / len(successful)
    avg_fps = total_frames / total_time if total_time > 0 else 0

    print(f"\nPerformance Metrics:")
    print(f"  Total generation time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Total frames rendered: {total_frames}")
    print(f"  Average time per video: {avg_time:.1f}s")
    print(f"  Average frames/second: {avg_fps:.4f}")
    print(f"  Video duration generated: {total_frames/16:.1f}s")

    print(f"\nPer-video breakdown:")
    for r in successful:
      video_dur = r.frames / 16
      fps = r.frames / r.generation_time if r.generation_time > 0 else 0
      print(f"  - {Path(r.output_path).name if r.output_path else 'N/A'}")
      print(f"    Gen: {r.generation_time:.1f}s | Video: {video_dur:.1f}s | FPS: {fps:.4f} | Size: {r.file_size_mb:.2f}MB")

  # Save results
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  results_path = OUTPUT_BASE / f"benchmark_results_{timestamp}.json"
  results_path.parent.mkdir(parents=True, exist_ok=True)

  results_data = {
    "timestamp": timestamp,
    "total_videos": len(results),
    "successful": len(successful),
    "total_time_seconds": total_time,
    "total_frames": total_frames,
    "results": [asdict(r) for r in results]
  }

  results_path.write_text(json.dumps(results_data, indent=2))
  print(f"\nResults saved: {results_path}")

  return results

def main():
  """Main entry point"""

  print("\n" + "="*70)
  print("LINKEDIN VIDEO SERIES PRODUCTION PIPELINE")
  print("The AI-Powered Professional Stack")
  print("="*70)

  # Create output directories
  OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
  (OUTPUT_BASE / "benchmark").mkdir(exist_ok=True)

  # Initialize client
  client = BetaComfyUIClient()

  # Check health
  health = client.check_health()
  print(f"\nBETA Status: {health.get('status')}")

  if health.get("status") != "healthy":
    print(f"Error: {health.get('error')}")
    sys.exit(1)

  print(f"  ComfyUI: v{health.get('comfyui_version')}")
  print(f"  RAM Free: {health.get('ram_free_gb', 0):.1f} GB")
  print(f"  Device: {health.get('device')}")

  # Check command line args
  if len(sys.argv) > 1:
    if sys.argv[1] == "benchmark":
      num = int(sys.argv[2]) if len(sys.argv) > 2 else 3
      run_benchmark(client, num)
    elif sys.argv[1] == "single":
      prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "A cinematic shot of a futuristic workspace"
      client.generate_video(prompt=prompt)
  else:
    print("\nUsage:")
    print("  python3 linkedin_video_production.py benchmark [num_videos]")
    print("  python3 linkedin_video_production.py single 'prompt here'")
    print("\nAvailable prompts:")
    for vp in ALL_PROMPTS:
      print(f"  - EP{vp.episode}: {vp.label} ({vp.priority})")

if __name__ == "__main__":
  main()
