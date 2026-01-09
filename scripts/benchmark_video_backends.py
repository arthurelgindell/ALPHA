#!/usr/bin/env python3
"""
Video Backend Benchmark Script
Tests rendering performance across available backends with themed prompts.

Usage:
  python3 scripts/benchmark_video_backends.py "Theme description here"
"""

import sys
import time
import json
import httpx
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

# Wan 2.2 maximum settings for 256GB RAM
WAN22_MAX_FRAMES = 129  # ~10.75 seconds at 12fps
WAN22_MAX_STEPS = 40    # High quality
WAN22_RESOLUTION = (832, 480)  # 720p equivalent

@dataclass
class BenchmarkResult:
  """Result of a single benchmark run"""
  backend: str
  prompt: str
  success: bool
  generation_time_seconds: float
  file_size_mb: float
  frames: int
  steps: int
  resolution: tuple
  error: Optional[str] = None
  output_path: Optional[str] = None

  @property
  def frames_per_second(self) -> float:
    if self.generation_time_seconds > 0:
      return self.frames / self.generation_time_seconds
    return 0

  @property
  def video_duration_seconds(self) -> float:
    return self.frames / 12  # 12fps

class VideoBenchmark:
  """Benchmark video generation across backends"""

  def __init__(self):
    self.beta_url = "http://192.168.70.16:8188"
    self.output_dir = Path("/Users/arthurdell/ARTHUR/videos/benchmark")
    self.output_dir.mkdir(parents=True, exist_ok=True)
    self.results: list[BenchmarkResult] = []

  def check_beta_health(self) -> bool:
    """Check if BETA is available"""
    try:
      response = httpx.get(f"{self.beta_url}/system_stats", timeout=10)
      return response.status_code == 200
    except:
      return False

  def get_beta_stats(self) -> dict:
    """Get BETA system stats"""
    try:
      response = httpx.get(f"{self.beta_url}/system_stats", timeout=10)
      return response.json()
    except:
      return {}

  def create_wan22_workflow(
    self,
    prompt: str,
    num_frames: int = WAN22_MAX_FRAMES,
    steps: int = WAN22_MAX_STEPS,
    width: int = WAN22_RESOLUTION[0],
    height: int = WAN22_RESOLUTION[1],
    seed: Optional[int] = None
  ) -> dict:
    """Create Wan 2.2 text-to-video workflow for ComfyUI"""

    if seed is None:
      import random
      seed = random.randint(0, 2**31)

    # Wan 2.2 MoE workflow with high and low noise models
    workflow = {
      "1": {
        "inputs": {"unet_name": "wan2.2_t2v_high_noise_14B_fp16.safetensors"},
        "class_type": "UNETLoader",
        "_meta": {"title": "Load High Noise Model"}
      },
      "2": {
        "inputs": {"unet_name": "wan2.2_t2v_low_noise_14B_fp16.safetensors"},
        "class_type": "UNETLoader",
        "_meta": {"title": "Load Low Noise Model"}
      },
      "3": {
        "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors"},
        "class_type": "CLIPLoader",
        "_meta": {"title": "Load Text Encoder"}
      },
      "4": {
        "inputs": {"vae_name": "wan_2.1_vae.safetensors"},
        "class_type": "VAELoader",
        "_meta": {"title": "Load VAE"}
      },
      "5": {
        "inputs": {"text": prompt, "clip": ["3", 0]},
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Positive Prompt"}
      },
      "6": {
        "inputs": {"text": "low quality, blurry, distorted, watermark", "clip": ["3", 0]},
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Negative Prompt"}
      },
      "7": {
        "inputs": {"width": width, "height": height, "length": num_frames, "batch_size": 1},
        "class_type": "EmptySD3LatentImage",
        "_meta": {"title": "Empty Latent Video"}
      },
      "8": {
        "inputs": {
          "model_high_noise": ["1", 0],
          "model_low_noise": ["2", 0],
          "positive": ["5", 0],
          "negative": ["6", 0],
          "latent_image": ["7", 0],
          "seed": seed,
          "steps": steps,
          "cfg": 7.0,
          "sampler_name": "euler",
          "scheduler": "normal",
          "denoise": 1.0,
          "shift": 8.0
        },
        "class_type": "WanMoESampler",
        "_meta": {"title": "Wan MoE Sampler"}
      },
      "9": {
        "inputs": {"samples": ["8", 0], "vae": ["4", 0]},
        "class_type": "VAEDecode",
        "_meta": {"title": "VAE Decode"}
      },
      "10": {
        "inputs": {
          "images": ["9", 0],
          "fps": 12,
          "filename_prefix": "benchmark",
          "format": "video/h264-mp4"
        },
        "class_type": "SaveAnimatedWEBP",
        "_meta": {"title": "Save Video"}
      }
    }

    return workflow

  def submit_to_beta(self, workflow: dict) -> Optional[str]:
    """Submit workflow to BETA and return prompt_id"""
    try:
      response = httpx.post(
        f"{self.beta_url}/prompt",
        json={"prompt": workflow},
        timeout=30
      )
      response.raise_for_status()
      data = response.json()
      return data.get("prompt_id")
    except Exception as e:
      print(f"  Error submitting: {e}")
      return None

  def wait_for_completion(self, prompt_id: str, timeout: int = 3600) -> Optional[dict]:
    """Wait for job completion on BETA"""
    start = time.time()

    while time.time() - start < timeout:
      try:
        response = httpx.get(
          f"{self.beta_url}/history/{prompt_id}",
          timeout=30
        )
        data = response.json()

        if prompt_id in data:
          outputs = data[prompt_id].get("outputs", {})
          if outputs:
            return data[prompt_id]

        # Check queue status
        queue_response = httpx.get(f"{self.beta_url}/queue", timeout=10)
        queue_data = queue_response.json()
        running = queue_data.get("queue_running", [])
        pending = queue_data.get("queue_pending", [])

        elapsed = time.time() - start
        print(f"  [{elapsed:.0f}s] Running: {len(running)}, Pending: {len(pending)}", end="\r")

        time.sleep(10)

      except Exception as e:
        print(f"  Error checking status: {e}")
        time.sleep(10)

    return None

  def get_output_files(self, result: dict) -> list[str]:
    """Extract output filenames from result"""
    files = []
    outputs = result.get("outputs", {})

    for node_id, node_output in outputs.items():
      for key in ["gifs", "videos", "images"]:
        if key in node_output:
          for item in node_output[key]:
            if "filename" in item:
              files.append(item["filename"])

    return files

  def download_output(self, filename: str, output_path: Path) -> bool:
    """Download output file from BETA"""
    try:
      response = httpx.get(
        f"{self.beta_url}/view",
        params={"filename": filename, "type": "output"},
        timeout=120
      )
      response.raise_for_status()
      output_path.write_bytes(response.content)
      return True
    except:
      return False

  def run_beta_benchmark(
    self,
    prompt: str,
    num_frames: int = WAN22_MAX_FRAMES,
    steps: int = WAN22_MAX_STEPS,
    label: str = "test"
  ) -> BenchmarkResult:
    """Run a single benchmark on BETA"""

    print(f"\n{'='*60}")
    print(f"BETA Wan 2.2 Benchmark: {label}")
    print(f"{'='*60}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"Frames: {num_frames} (~{num_frames/12:.1f}s), Steps: {steps}")
    print(f"Resolution: {WAN22_RESOLUTION[0]}x{WAN22_RESOLUTION[1]}")

    # Check health
    if not self.check_beta_health():
      return BenchmarkResult(
        backend="beta-wan22",
        prompt=prompt,
        success=False,
        generation_time_seconds=0,
        file_size_mb=0,
        frames=num_frames,
        steps=steps,
        resolution=WAN22_RESOLUTION,
        error="BETA not available"
      )

    # Get initial RAM
    stats = self.get_beta_stats()
    ram_free_start = stats.get("system", {}).get("ram_free", 0) / 1024**3
    print(f"RAM available: {ram_free_start:.1f} GB")

    # Create and submit workflow
    workflow = self.create_wan22_workflow(prompt, num_frames, steps)

    print("Submitting workflow...")
    start_time = time.time()
    prompt_id = self.submit_to_beta(workflow)

    if not prompt_id:
      return BenchmarkResult(
        backend="beta-wan22",
        prompt=prompt,
        success=False,
        generation_time_seconds=0,
        file_size_mb=0,
        frames=num_frames,
        steps=steps,
        resolution=WAN22_RESOLUTION,
        error="Failed to submit workflow"
      )

    print(f"Submitted: {prompt_id}")
    print("Waiting for completion...")

    # Wait for completion
    result = self.wait_for_completion(prompt_id, timeout=3600)
    generation_time = time.time() - start_time

    if not result:
      return BenchmarkResult(
        backend="beta-wan22",
        prompt=prompt,
        success=False,
        generation_time_seconds=generation_time,
        file_size_mb=0,
        frames=num_frames,
        steps=steps,
        resolution=WAN22_RESOLUTION,
        error="Generation timed out"
      )

    # Get output files
    output_files = self.get_output_files(result)
    print(f"\nGeneration complete in {generation_time:.1f}s")
    print(f"Output files: {output_files}")

    if not output_files:
      return BenchmarkResult(
        backend="beta-wan22",
        prompt=prompt,
        success=False,
        generation_time_seconds=generation_time,
        file_size_mb=0,
        frames=num_frames,
        steps=steps,
        resolution=WAN22_RESOLUTION,
        error="No output files"
      )

    # Download first output
    filename = output_files[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = self.output_dir / f"beta_{label}_{timestamp}.mp4"

    print(f"Downloading to {output_path}...")
    if self.download_output(filename, output_path):
      file_size = output_path.stat().st_size / (1024 * 1024)
      print(f"Downloaded: {file_size:.2f} MB")

      bench_result = BenchmarkResult(
        backend="beta-wan22",
        prompt=prompt,
        success=True,
        generation_time_seconds=generation_time,
        file_size_mb=file_size,
        frames=num_frames,
        steps=steps,
        resolution=WAN22_RESOLUTION,
        output_path=str(output_path)
      )

      print(f"\n--- Performance ---")
      print(f"Generation time: {generation_time:.1f}s ({generation_time/60:.1f} min)")
      print(f"Video duration: {bench_result.video_duration_seconds:.1f}s")
      print(f"Frames/second: {bench_result.frames_per_second:.3f}")
      print(f"File size: {file_size:.2f} MB")

      return bench_result

    return BenchmarkResult(
      backend="beta-wan22",
      prompt=prompt,
      success=False,
      generation_time_seconds=generation_time,
      file_size_mb=0,
      frames=num_frames,
      steps=steps,
      resolution=WAN22_RESOLUTION,
      error="Failed to download output"
    )

  def run_themed_benchmark(self, prompts: list[dict]):
    """Run benchmark with themed prompts"""

    print("\n" + "="*70)
    print("VIDEO BACKEND BENCHMARK")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Prompts: {len(prompts)}")
    print(f"Output: {self.output_dir}")

    for i, prompt_config in enumerate(prompts, 1):
      prompt = prompt_config["prompt"]
      label = prompt_config.get("label", f"prompt_{i}")
      frames = prompt_config.get("frames", WAN22_MAX_FRAMES)
      steps = prompt_config.get("steps", WAN22_MAX_STEPS)

      result = self.run_beta_benchmark(prompt, frames, steps, label)
      self.results.append(result)

    # Print summary
    self.print_summary()

    # Save results
    self.save_results()

  def print_summary(self):
    """Print benchmark summary"""
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)

    successful = [r for r in self.results if r.success]
    failed = [r for r in self.results if not r.success]

    print(f"\nTotal: {len(self.results)} | Success: {len(successful)} | Failed: {len(failed)}")

    if successful:
      total_time = sum(r.generation_time_seconds for r in successful)
      total_frames = sum(r.frames for r in successful)
      avg_fps = total_frames / total_time if total_time > 0 else 0

      print(f"\nPerformance Metrics (successful runs):")
      print(f"  Total generation time: {total_time:.1f}s ({total_time/60:.1f} min)")
      print(f"  Total frames rendered: {total_frames}")
      print(f"  Average frames/second: {avg_fps:.4f}")
      print(f"  Total video duration: {sum(r.video_duration_seconds for r in successful):.1f}s")
      print(f"  Total file size: {sum(r.file_size_mb for r in successful):.2f} MB")

      print(f"\nPer-video breakdown:")
      for r in successful:
        print(f"  - {r.output_path.split('/')[-1] if r.output_path else 'N/A'}")
        print(f"    Time: {r.generation_time_seconds:.1f}s, Frames: {r.frames}, FPS: {r.frames_per_second:.4f}")

    if failed:
      print(f"\nFailed runs:")
      for r in failed:
        print(f"  - {r.error}")

  def save_results(self):
    """Save benchmark results to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = self.output_dir / f"benchmark_results_{timestamp}.json"

    results_data = {
      "timestamp": timestamp,
      "results": [asdict(r) for r in self.results],
      "summary": {
        "total": len(self.results),
        "successful": len([r for r in self.results if r.success]),
        "failed": len([r for r in self.results if not r.success])
      }
    }

    results_path.write_text(json.dumps(results_data, indent=2))
    print(f"\nResults saved to: {results_path}")


def main():
  """Main entry point"""

  if len(sys.argv) < 2:
    print("Usage: python3 benchmark_video_backends.py 'theme description'")
    print("\nOr provide prompts via stdin as JSON:")
    print('  echo \'[{"label": "test", "prompt": "..."}]\' | python3 benchmark_video_backends.py -')
    sys.exit(1)

  benchmark = VideoBenchmark()

  # Check BETA availability
  if not benchmark.check_beta_health():
    print("ERROR: BETA ComfyUI not available at http://192.168.70.16:8188")
    sys.exit(1)

  stats = benchmark.get_beta_stats()
  print(f"BETA Online: ComfyUI v{stats['system']['comfyui_version']}")
  print(f"RAM: {stats['system']['ram_free']/1024**3:.0f}GB free")

  if sys.argv[1] == "-":
    # Read JSON prompts from stdin
    prompts = json.loads(sys.stdin.read())
  else:
    # Single theme - create default prompts
    theme = " ".join(sys.argv[1:])
    prompts = [
      {
        "label": "main",
        "prompt": theme,
        "frames": WAN22_MAX_FRAMES,
        "steps": WAN22_MAX_STEPS
      }
    ]

  benchmark.run_themed_benchmark(prompts)


if __name__ == "__main__":
  main()
