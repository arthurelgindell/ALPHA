#!/usr/bin/env python3
"""
Parallel Video Production - Overnight Autonomous Run
Generates videos using Wan 2.6 API while BETA Wan 2.2 runs in parallel

Uses canonical Wan26APIClient from arthur.generators for retry logic and resilience.

Author: Arthur Dell
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add arthur package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.generators.wan26_api import Wan26APIClient

OUTPUT_DIR = Path("/Users/arthurdell/ARTHUR/videos/linkedin_series/wan26")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Hero shot prompts for Wan 2.6 (higher quality, faster turnaround)
HERO_PROMPTS = [
  {
    "id": "ep1_mac_studio_hero",
    "episode": 1,
    "label": "Mac Studio Reveal Hero",
    "prompt": """Cinematic product shot of two Mac Studio M3 Ultra computers side by side on a
minimal dark desk, warm amber accent lighting from above creating subtle rim light, deep
charcoal background, professional studio lighting, 8k quality, shallow depth of field,
subtle floating particle effects suggesting data flow between units, tech aesthetic,
premium product photography, smooth slow push-in camera movement""",
    "duration": 5,
    "resolution": "720P"
  },
  {
    "id": "ep2_dgx_spark_hero",
    "episode": 2,
    "label": "DGX Spark Reveal Hero",
    "prompt": """Close-up reveal of NVIDIA DGX Spark being lifted from premium packaging,
champagne gold finish catching warm light, dark professional environment, shallow depth
of field, dust particles floating in air, premium unboxing aesthetic, cinematic lighting,
smooth upward reveal motion, 8k quality, professional product photography""",
    "duration": 5,
    "resolution": "720P"
  },
  {
    "id": "ep3_neural_viz_hero",
    "episode": 3,
    "label": "Neural Network Hero",
    "prompt": """Abstract visualization of neural network processing with interconnected nodes
pulsing with amber and teal light against deep charcoal background, flowing data streams,
representing AI reasoning and DeepSeek intelligence, elegant smooth flowing motion,
premium tech aesthetic, geometric patterns, professional motion graphics quality""",
    "duration": 5,
    "resolution": "720P"
  },
  {
    "id": "ep4_claude_code_hero",
    "episode": 4,
    "label": "Claude Code Terminal Hero",
    "prompt": """Cinematic close-up of terminal window with Claude Code interface launching,
amber text appearing on dark background, command line aesthetic with cursor blinking,
professional developer environment, code characters animating, suggesting AI power
about to be unleashed, dramatic screen glow, 8k quality""",
    "duration": 5,
    "resolution": "720P"
  },
  {
    "id": "arthur_branding",
    "episode": 0,
    "label": "Arthur Dell Branding",
    "prompt": """Professional personal branding shot: the name "Arthur Dell" elegantly
displayed in modern typography against a sophisticated dark gradient background with
subtle amber accent lighting, premium corporate aesthetic, clean minimalist design,
professional tech executive branding, smooth text reveal animation, 8k quality""",
    "duration": 5,
    "resolution": "720P"
  }
]


def produce_video(client: Wan26APIClient, prompt_config: dict) -> dict:
  """Produce a single video using the canonical client."""
  prompt_id = prompt_config["id"]
  label = prompt_config["label"]
  prompt = prompt_config["prompt"]
  duration = prompt_config.get("duration", 5)
  resolution = prompt_config.get("resolution", "720P")

  print(f"\n{'='*60}")
  print(f"Producing: {label}")
  print(f"Duration: {duration}s, Resolution: {resolution}")
  print(f"{'='*60}")

  # Submit
  start_time = time.time()
  result = client.text_to_video(
    prompt=prompt,
    duration=duration,
    resolution=resolution,
    aspect_ratio="16:9",
    with_audio=False,
    prompt_extend=True
  )

  if not result.success:
    return {
      "id": prompt_id,
      "label": label,
      "success": False,
      "error": result.error,
      "generation_time": 0,
      "file_size_mb": 0
    }

  task_id = result.task_id
  print(f"Submitted: {task_id}")
  print(f"Est. cost: ${result.cost_estimate:.2f}")

  # Wait and download
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  output_path = OUTPUT_DIR / f"wan26_{prompt_id}_{timestamp}.mp4"

  # Poll for completion
  timeout = 300
  poll_start = time.time()

  while time.time() - poll_start < timeout:
    status = client.get_task_status(task_id)
    elapsed = int(time.time() - poll_start)

    print(f"  [{elapsed}s] Status: {status.get('status')}", end="\r")

    if status.get("status") in ("completed", "Completed"):
      if status.get("video_url"):
        print(f"\n  Downloading...")

        if client.download_video(task_id, output_path):
          generation_time = time.time() - start_time
          file_size = output_path.stat().st_size / (1024 * 1024)

          print(f"\n✅ Success: {output_path.name}")
          print(f"   Time: {generation_time:.1f}s, Size: {file_size:.2f}MB")

          return {
            "id": prompt_id,
            "label": label,
            "success": True,
            "task_id": task_id,
            "output_path": str(output_path),
            "generation_time": generation_time,
            "file_size_mb": file_size,
            "cost_estimate": result.cost_estimate
          }

    elif status.get("status") in ("failed", "Failed"):
      print(f"\n  Generation failed: {status.get('error')}")
      return {
        "id": prompt_id,
        "label": label,
        "success": False,
        "task_id": task_id,
        "error": status.get("error", "Generation failed"),
        "generation_time": time.time() - start_time,
        "file_size_mb": 0
      }

    time.sleep(5)

  print("\n  Timeout waiting for completion")
  return {
    "id": prompt_id,
    "label": label,
    "success": False,
    "task_id": task_id,
    "error": "Timeout",
    "generation_time": time.time() - start_time,
    "file_size_mb": 0
  }


def produce_all(client: Wan26APIClient, prompts: list[dict]) -> list[dict]:
  """Produce all videos."""
  print("\n" + "="*70)
  print("WAN 2.6 API HERO VIDEO PRODUCTION")
  print(f"Videos to produce: {len(prompts)}")
  print("="*70)

  results = []

  for i, prompt_config in enumerate(prompts, 1):
    print(f"\n[{i}/{len(prompts)}]", end="")
    result = produce_video(client, prompt_config)
    results.append(result)

  # Summary
  print("\n" + "="*70)
  print("PRODUCTION SUMMARY")
  print("="*70)

  successful = [r for r in results if r.get("success")]
  failed = [r for r in results if not r.get("success")]

  print(f"\nTotal: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}")

  if successful:
    total_time = sum(r["generation_time"] for r in successful)
    total_size = sum(r["file_size_mb"] for r in successful)
    total_cost = sum(r.get("cost_estimate", 0) for r in successful)

    print(f"\nSuccessful renders:")
    for r in successful:
      print(f"  ✅ {r['label']}")
      print(f"     Path: {r.get('output_path', 'N/A')}")
      print(f"     Time: {r['generation_time']:.1f}s, Size: {r['file_size_mb']:.2f}MB")

    print(f"\nTotal time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Total size: {total_size:.2f}MB")
    print(f"Estimated cost: ${total_cost:.2f}")

  if failed:
    print(f"\nFailed renders:")
    for r in failed:
      print(f"  ❌ {r['label']}: {r.get('error', 'Unknown error')}")

  # Save results
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  results_path = OUTPUT_DIR / f"production_results_{timestamp}.json"
  results_path.write_text(json.dumps({
    "timestamp": timestamp,
    "total": len(results),
    "successful": len(successful),
    "failed": len(failed),
    "results": results
  }, indent=2))
  print(f"\nResults saved: {results_path}")

  return results


def main():
  """Main entry point"""
  print("\n" + "="*70)
  print("WAN 2.6 HERO VIDEO PRODUCTION")
  print("="*70)

  # Initialize client (validates API key)
  try:
    client = Wan26APIClient()
  except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

  # Produce all hero videos
  produce_all(client, HERO_PROMPTS)

  # Cleanup
  client.close()

  print("\n" + "="*70)
  print("WAN 2.6 HERO PRODUCTION COMPLETE")
  print(f"Output directory: {OUTPUT_DIR}")
  print("="*70)


if __name__ == "__main__":
  main()
