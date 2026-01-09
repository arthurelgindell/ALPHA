#!/usr/bin/env python3
"""
Wan 2.6 API Retry - Simplified prompts for failed videos
Output: /Volumes/STUDIO/VIDEO/linkedin_series/wan26/

Uses canonical Wan26APIClient from arthur.generators for retry logic and resilience.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add arthur package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.generators.wan26_api import Wan26APIClient

OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/wan26")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Simplified prompts - shorter and more focused
RETRY_SHOTS = [
  {"id": "ep1_hero", "prompt": "Apple Mac Studio silver aluminum computer on dark background, dramatic product lighting, slow reveal"},
  {"id": "ep1_dual", "prompt": "Two Mac Studio computers on walnut desk, professional workspace, warm lighting, slow camera movement"},
  {"id": "ep1_perf", "prompt": "Abstract neural network visualization, glowing amber and teal data streams, dark background, cinematic"},
  {"id": "ep1_flow", "prompt": "Creative software workflow on computer screen, multiple windows, smooth transitions"},
  {"id": "ep2_bench", "prompt": "Animated performance charts and data visualization, professional infographic style, dark theme"},
  {"id": "ep3_universe", "prompt": "AI models floating in space constellation, holographic cards connected by light beams, cosmic aesthetic"},
  {"id": "ep3_deepseek", "prompt": "Neural network architecture visualization, tokens flowing through layers, technical diagram animation"},
  {"id": "ep3_multi", "prompt": "Multiple AI nodes orchestrating workflow, data flow visualization, professional diagram style"},
  {"id": "ep3_output", "prompt": "AI generating text and code in real-time, typing animation, dark interface with glowing elements"},
  {"id": "ep4_term", "prompt": "Developer terminal with code scrolling, syntax highlighting, dramatic screen glow illuminating keyboard"},
  {"id": "ep4_code", "prompt": "Code generation in IDE, syntax highlighted code appearing line by line, professional coding aesthetic"},
  {"id": "ep4_edit", "prompt": "Multiple files being edited simultaneously, code changes rippling across files, IDE interface"},
  {"id": "ep4_git", "prompt": "Git commit history timeline with branches merging, version control visualization, DevOps aesthetic"},
  {"id": "brand_intro", "prompt": "AI-Powered Professional Stack title reveal, elegant typography animation, amber and teal on dark"},
  {"id": "brand_trans", "prompt": "Smooth geometric transition animation, morphing shapes, premium motion graphics, amber teal palette"},
  {"id": "brand_outro", "prompt": "Four icons assembling into grid, brand lockup animation, fade to black, professional ending"}
]


def main():
  print("=" * 60)
  print("WAN 2.6 API RETRY - SIMPLIFIED PROMPTS")
  print(f"Shots: {len(RETRY_SHOTS)} | Duration: 15s each")
  print(f"Output: {OUTPUT_DIR}")
  print("=" * 60)

  # Initialize client (validates API key)
  try:
    client = Wan26APIClient()
  except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

  jobs = []

  # Submit with delay between each to avoid rate limiting
  for i, shot in enumerate(RETRY_SHOTS, 1):
    print(f"\n[{i}/{len(RETRY_SHOTS)}] {shot['id']}")
    print(f"  Prompt: {shot['prompt'][:60]}...")

    result = client.text_to_video(
      prompt=shot["prompt"],
      duration=15,
      resolution="720P",
      aspect_ratio="16:9",
      with_audio=False,
      prompt_extend=True
    )

    if result.success:
      print(f"  Submitted: {result.task_id[:8]}...")
      jobs.append({
        "shot": shot,
        "task_id": result.task_id,
        "status": "pending",
        "cost_estimate": result.cost_estimate
      })
    else:
      print(f"  ERROR: {result.error}")
      jobs.append({"shot": shot, "status": "submit_failed", "error": result.error})

    time.sleep(2)  # 2 second delay between submissions

  print("\n" + "=" * 60)
  print("MONITORING - checking every 30 seconds")
  print("=" * 60)

  while True:
    pending = [j for j in jobs if j["status"] == "pending"]
    if not pending:
      break

    for job in pending:
      status = client.get_task_status(job["task_id"])

      if status.get("status") in ("Completed", "completed") and status.get("video_url"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wan26_retry_{job['shot']['id']}_{ts}.mp4"
        path = OUTPUT_DIR / filename

        print(f"\n✅ {job['shot']['id']}: Downloading...")

        if client.download_video(job["task_id"], path):
          job["status"] = "completed"
          job["file"] = str(path)
          job["size"] = path.stat().st_size / 1e6
          print(f"   Saved: {filename} ({job['size']:.1f}MB)")
        else:
          job["status"] = "download_failed"
          print(f"   Download failed")

      elif status.get("status") in ("Failed", "failed"):
        job["status"] = "failed"
        job["error"] = status.get("error", "Generation failed")
        print(f"\n❌ {job['shot']['id']}: {job['error']}")

    pending_count = len([j for j in jobs if j["status"] == "pending"])
    completed_count = len([j for j in jobs if j["status"] == "completed"])
    failed_count = len([j for j in jobs if j["status"] in ["failed", "submit_failed", "download_failed"]])
    print(f"\r  Pending: {pending_count} | Completed: {completed_count} | Failed: {failed_count}", end="", flush=True)

    if pending_count > 0:
      time.sleep(30)

  # Cleanup
  client.close()

  # Summary
  print("\n\n" + "=" * 60)
  print("SUMMARY")
  print("=" * 60)

  ok = [j for j in jobs if j["status"] == "completed"]
  fail = [j for j in jobs if j["status"] in ["failed", "submit_failed", "download_failed"]]

  print(f"Total: {len(jobs)} | Success: {len(ok)} | Failed: {len(fail)}")

  if ok:
    total_size = sum(j.get("size", 0) for j in ok)
    total_duration = len(ok) * 15
    total_cost = sum(j.get("cost_estimate", 0) for j in ok)
    print(f"Total duration: {total_duration}s ({total_duration/60:.1f} min)")
    print(f"Total size: {total_size:.1f}MB")
    print(f"Est. cost: ${total_cost:.2f}")

  # Save results
  results_path = OUTPUT_DIR / f"retry_15s_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  with open(results_path, 'w') as f:
    json.dump({
      "shots": len(RETRY_SHOTS),
      "completed": len(ok),
      "failed": len(fail),
      "jobs": jobs
    }, f, indent=2, default=str)
  print(f"\nResults: {results_path}")


if __name__ == "__main__":
  main()
