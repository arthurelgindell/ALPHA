#!/usr/bin/env python3
"""
Standalone Episode 1 video generation script
No package imports to avoid dependency issues
"""

import os
import sys
import time
import httpx
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

OUTPUT_DIR = Path("/Users/arthurdell/ARTHUR/resolve_projects/ep1_hardware")

# Episode 1 Shot List - Storyboard Aligned for 120 seconds
EP1_SHOTS = [
  # ACT 1: THE SETUP (0:00 - 0:30)
  {
    "id": "ep1_01_workspace_establish",
    "prompt": "Cinematic establishing shot of premium home office workspace, morning light streaming through windows, sleek desk setup with multiple monitors, executive chair, dark wood and metal aesthetic, professional tech environment, shallow depth of field, 4K quality",
    "duration": 10,
    "narrative": "Opening - Establish professional context"
  },
  {
    "id": "ep1_02_mac_studio_reveal",
    "prompt": "Dramatic product reveal of Apple Mac Studio computer, silver aluminum box emerging from darkness, premium studio lighting, particles of light floating around device, cinematic camera orbit, ultra-premium product photography style, 4K",
    "duration": 10,
    "narrative": "Mac Studio hero introduction"
  },
  {
    "id": "ep1_03_mac_studio_ports",
    "prompt": "Close-up detail shot of high-end computer ports and connectivity, Thunderbolt cables being connected, professional equipment integration, shallow depth of field, premium tech aesthetic, cable management perfection",
    "duration": 5,
    "narrative": "Mac Studio connectivity"
  },

  # ACT 2: THE REVEAL (0:30 - 1:00)
  {
    "id": "ep1_04_dgx_spark_unbox",
    "prompt": "Premium product unboxing sequence, champagne gold compact computer emerging from sleek black packaging, NVIDIA branding visible, hands carefully lifting device, premium materials, luxury tech aesthetic, cinematic lighting",
    "duration": 10,
    "narrative": "DGX Spark dramatic reveal"
  },
  {
    "id": "ep1_05_dgx_spark_detail",
    "prompt": "Extreme close-up of champagne gold desktop AI computer, intricate cooling vents, premium metallic finish catching light, subtle reflections, macro lens detail shot, futuristic technology aesthetic",
    "duration": 5,
    "narrative": "DGX Spark craftsmanship"
  },
  {
    "id": "ep1_06_side_by_side",
    "prompt": "Two premium desktop computers side by side on executive desk, silver aluminum cube and champagne gold compact unit, coffee mug for scale reference, symmetrical composition, premium office environment, professional product photography",
    "duration": 10,
    "narrative": "Direct comparison - the power duo"
  },

  # ACT 3: THE CAPABILITY (1:00 - 1:40)
  {
    "id": "ep1_07_neural_flow",
    "prompt": "Abstract visualization of neural network data processing, flowing streams of light particles representing AI computation, deep blue and amber color palette, futuristic data center aesthetic, smooth camera movement through data streams",
    "duration": 10,
    "narrative": "AI processing visualization"
  },
  {
    "id": "ep1_08_unified_memory",
    "prompt": "Cinematic visualization of unified memory architecture, glowing data pathways connecting components, abstract representation of 512GB memory bandwidth, cool blue and white light trails, tech diagram coming to life",
    "duration": 10,
    "narrative": "Unified memory advantage"
  },
  {
    "id": "ep1_09_petaflop_viz",
    "prompt": "Dynamic visualization of one petaflop computing power, explosion of calculated data points, mathematical formulas floating in space, gold and orange particle effects, abstract representation of massive parallel processing",
    "duration": 10,
    "narrative": "PFLOP power visualization"
  },

  # ACT 4: THE INTEGRATION (1:40 - 2:00)
  {
    "id": "ep1_10_dual_workflow",
    "prompt": "Split screen professional workflow visualization, AI model training on one side, creative content generation on other, data flowing between systems, modern dashboard interfaces, professional productivity aesthetic",
    "duration": 10,
    "narrative": "Dual system workflow"
  },
  {
    "id": "ep1_11_hero_closing",
    "prompt": "Cinematic hero shot of complete dual-computer workstation setup, dramatic lighting, camera slowly pulling back to reveal full professional environment, golden hour lighting, aspirational tech workspace, premium executive aesthetic",
    "duration": 10,
    "narrative": "Closing hero shot"
  },
]


@dataclass
class Wan26Result:
  success: bool
  task_id: str
  video_url: Optional[str]
  status: str
  error: Optional[str] = None


class Wan26Client:
  BASE_URL = "https://api.piapi.ai"

  def __init__(self, api_key: str):
    self.client = httpx.Client(
      base_url=self.BASE_URL,
      headers={"X-API-Key": api_key, "Content-Type": "application/json"},
      timeout=120.0
    )

  def text_to_video(self, prompt: str, duration: int = 5, resolution: str = "720P") -> Wan26Result:
    request = {
      "model": "Wan",
      "task_type": "wan26-txt2video",
      "input": {
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": "16:9",
        "audio": False,
        "shot_type": "single",
        "prompt_extend": True,
        "watermark": False
      }
    }

    try:
      response = self.client.post("/api/v1/task", json=request)
      data = response.json()

      if data.get("code") != 200:
        return Wan26Result(False, "", None, "failed", data.get("message"))

      task_data = data.get("data", {})
      return Wan26Result(True, task_data.get("task_id", ""), None, task_data.get("status", "pending"))
    except Exception as e:
      return Wan26Result(False, "", None, "error", str(e))

  def get_status(self, task_id: str) -> dict:
    try:
      response = self.client.get(f"/api/v1/task/{task_id}")
      data = response.json()
      if data.get("code") != 200:
        return {"status": "error", "error": data.get("message")}
      task_data = data.get("data", {})
      output = task_data.get("output", {})
      return {
        "status": task_data.get("status", "unknown"),
        "video_url": output.get("video_url") if output else None
      }
    except Exception as e:
      return {"status": "error", "error": str(e)}

  def wait_for_completion(self, task_id: str, timeout: int = 300) -> Optional[str]:
    start = time.time()
    last_status = ""
    while time.time() - start < timeout:
      status = self.get_status(task_id)
      current = status.get("status", "unknown")

      if current != last_status:
        elapsed = int(time.time() - start)
        print(f"    [{elapsed}s] Status: {current}")
        last_status = current

      if current in ("Completed", "completed"):
        return status.get("video_url")
      if current in ("Failed", "failed"):
        print(f"    ❌ Failed: {status.get('error', 'unknown')}")
        return None

      time.sleep(10)

    print(f"    ⏱️ Timeout after {timeout}s")
    return None

  def download(self, url: str, path: Path) -> bool:
    try:
      response = httpx.get(url, timeout=120.0)
      if response.status_code == 200:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return True
    except Exception as e:
      print(f"    Download error: {e}")
    return False

  def close(self):
    self.client.close()


def main():
  print("=" * 70)
  print("EPISODE 1: HARDWARE FOUNDATION - VIDEO GENERATION")
  print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  print("=" * 70)

  # Check API key
  api_key = os.environ.get("WAN26_API_KEY")
  if not api_key:
    print("ERROR: WAN26_API_KEY not set")
    sys.exit(1)

  print(f"\nAPI Key: {api_key[:8]}...{api_key[-4:]}")

  # Calculate totals
  total_duration = sum(s["duration"] for s in EP1_SHOTS)
  total_cost = total_duration * 0.08

  print(f"Shots to generate: {len(EP1_SHOTS)}")
  print(f"Total duration: {total_duration} seconds")
  print(f"Estimated cost: ${total_cost:.2f}")

  # Check existing
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  to_generate = []
  for shot in EP1_SHOTS:
    path = OUTPUT_DIR / f"{shot['id']}.mp4"
    if path.exists():
      print(f"  [skip] {shot['id']} (exists)")
    else:
      to_generate.append(shot)

  if not to_generate:
    print("\n✅ All shots already generated!")
    return

  print(f"\nGenerating {len(to_generate)} new shots...")

  # Initialize client
  client = Wan26Client(api_key)

  results = []
  for i, shot in enumerate(to_generate, 1):
    print(f"\n{'─' * 70}")
    print(f"[{i}/{len(to_generate)}] {shot['id']}")
    print(f"Narrative: {shot['narrative']}")
    print(f"Duration: {shot['duration']}s")
    print(f"Prompt: {shot['prompt'][:60]}...")
    print("─" * 70)

    # Submit
    print("  Submitting to Wan 2.6 API...")
    result = client.text_to_video(
      prompt=shot["prompt"],
      duration=shot["duration"],
      resolution="720P"
    )

    if not result.success:
      print(f"  ❌ Submit failed: {result.error}")
      continue

    print(f"  Task ID: {result.task_id}")
    print("  Waiting for completion...")

    # Wait
    video_url = client.wait_for_completion(result.task_id, timeout=300)

    if not video_url:
      print("  ❌ Generation failed")
      continue

    # Download
    output_path = OUTPUT_DIR / f"{shot['id']}.mp4"
    print(f"  Downloading to {output_path.name}...")

    if client.download(video_url, output_path):
      size_mb = output_path.stat().st_size / (1024 * 1024)
      print(f"  ✅ Saved: {size_mb:.2f} MB")
      results.append(shot)
    else:
      print("  ❌ Download failed")

    # Pause between shots
    if i < len(to_generate):
      print("  Waiting 3s...")
      time.sleep(3)

  client.close()

  # Summary
  print("\n" + "=" * 70)
  print("GENERATION COMPLETE")
  print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  print("=" * 70)

  print(f"\nSuccess: {len(results)}/{len(to_generate)}")

  if results:
    total_new = sum(s["duration"] for s in results)
    print(f"New footage: {total_new} seconds")
    print(f"Actual cost: ~${total_new * 0.08:.2f}")

    print("\nGenerated:")
    for s in results:
      print(f"  ✓ {s['id']} ({s['duration']}s)")

  # List all files
  print(f"\nAll files in {OUTPUT_DIR}:")
  for f in sorted(OUTPUT_DIR.glob("*.mp4")):
    size = f.stat().st_size / (1024 * 1024)
    print(f"  {f.name} ({size:.1f} MB)")


if __name__ == "__main__":
  main()
