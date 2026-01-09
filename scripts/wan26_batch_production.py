#!/usr/bin/env python3
"""
Wan 2.6 API Batch Production - 15-second videos
LinkedIn Series: The AI-Powered Professional Stack
Output: /Volumes/STUDIO/VIDEO/linkedin_series/wan26/
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# API Configuration
API_KEY = os.environ.get("WAN26_API_KEY", "f67f75762688be088232f53be99c58cc996e80c96c6e75a5f0c5887c65cff8a2")
API_URL = "https://api.piapi.ai/api/v1/task"
OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/wan26")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 15-second hero shots for maximum impact
SHOTS_15S = [
  {
    "id": "ep1_hero_reveal",
    "episode": 1,
    "label": "Mac Studio Hero Reveal",
    "prompt": "Cinematic product reveal of Apple Mac Studio M3 Ultra, compact silver aluminum desktop box with rounded corners and ventilation holes on top, dramatic lighting sweep from left to right revealing machined aluminum surface, professional studio lighting on seamless dark background, shallow depth of field, smooth camera motion, shot on RED V-RAPTOR 8K, premium tech product commercial"
  },
  {
    "id": "ep1_dual_setup",
    "episode": 1,
    "label": "Mac Studio Dual Workstation",
    "prompt": "Two Apple Mac Studio computers side by side on premium walnut desk in professional workspace, warm amber accent lighting from above, organized cable management, Studio Display monitors visible in background, cinematic slow dolly shot moving right to left, shallow depth of field, professional photography"
  },
  {
    "id": "ep1_performance",
    "episode": 1,
    "label": "M3 Ultra Performance Visualization",
    "prompt": "Abstract visualization of Apple M3 Ultra chip performance, neural engine pathways glowing in amber and electric teal colors, data streams flowing through unified memory architecture, particle effects representing compute power, dark background with subtle grid, cinematic camera push-in"
  },
  {
    "id": "ep1_workflow",
    "episode": 1,
    "label": "Creative Workflow Demo",
    "prompt": "Professional creative workflow on Mac Studio, multiple 4K video timeline streams, AI model training dashboard with live metrics, smooth transitions between applications, productive workspace aesthetic, screen recording style with subtle camera movement, modern UI design"
  },
  {
    "id": "ep2_unboxing",
    "episode": 2,
    "label": "DGX Spark Unboxing",
    "prompt": "Cinematic unboxing reveal of NVIDIA DGX Spark desktop supercomputer, champagne gold metallic finish emerging from premium black packaging, dramatic top-down camera angle slowly revealing the device, professional studio lighting with soft shadows, anticipation building, luxury product reveal aesthetic"
  },
  {
    "id": "ep2_scale",
    "episode": 2,
    "label": "DGX Spark Scale Comparison",
    "prompt": "NVIDIA DGX Spark desktop supercomputer next to everyday objects showing compact size - coffee mug, hardcover book, smartphone - demonstrating petaflop AI performance in small form factor, smooth 360 degree camera orbit around the arrangement, clean white surface, professional product photography"
  },
  {
    "id": "ep2_inference",
    "episode": 2,
    "label": "DGX Spark AI Inference",
    "prompt": "Abstract visualization of AI inference running on NVIDIA DGX Spark, neural network layer activations lighting up in sequence, data flowing through Grace Blackwell architecture, electric teal and amber particle streams, matrix-style data visualization, cinematic camera flying through the network"
  },
  {
    "id": "ep2_benchmark",
    "episode": 2,
    "label": "DGX Spark Benchmarks",
    "prompt": "Animated benchmark results and performance charts for DGX Spark, bar graphs rising and competing, data visualizations materializing in 3D space, professional infographic animation style, dark background with glowing data points, smooth transitions between metrics"
  },
  {
    "id": "ep3_universe",
    "episode": 3,
    "label": "AI Model Universe",
    "prompt": "Expansive visualization of AI model ecosystem, floating holographic model cards and neural network architectures arranged in 3D constellation, camera flying through this universe of AI capabilities, stars and connections between models, deep space aesthetic with nebula colors, epic scale"
  },
  {
    "id": "ep3_deepseek",
    "episode": 3,
    "label": "DeepSeek Architecture",
    "prompt": "DeepSeek large language model architecture visualization, mixture of experts routing system with tokens flowing to specialized expert modules, attention pattern matrices lighting up, technical diagram transforming into beautiful 3D animation, data flows in amber and teal"
  },
  {
    "id": "ep3_multimodel",
    "episode": 3,
    "label": "Multi-Model Orchestration",
    "prompt": "Multiple AI models working together in orchestrated workflow, visual representation of model handoffs and specialization, conductor-style coordination visualization, different model types represented as distinct glowing nodes, smooth data flow between them, professional infographic aesthetic"
  },
  {
    "id": "ep3_output",
    "episode": 3,
    "label": "AI Output Generation",
    "prompt": "AI generating creative content in real-time, text appearing character by character, images rendering progressively, code syntax highlighting as it writes, multiple output types emerging simultaneously, productive and impressive visualization, dark interface with glowing outputs"
  },
  {
    "id": "ep4_terminal",
    "episode": 4,
    "label": "Claude Code Terminal",
    "prompt": "Developer terminal launching Claude Code CLI, command line interface with syntax highlighting appearing, code suggestions scrolling smoothly, professional dark theme terminal, dramatic screen glow illuminating keyboard and desk in darkness, cinematic rack focus"
  },
  {
    "id": "ep4_codegen",
    "episode": 4,
    "label": "Claude Code Generation",
    "prompt": "Claude Code AI generating production code in real-time, syntax highlighted code appearing line by line, intelligent completions and suggestions showing, split view with file tree navigation, multiple files being edited, productive professional developer aesthetic"
  },
  {
    "id": "ep4_multiedit",
    "episode": 4,
    "label": "Multi-File Editing",
    "prompt": "Claude Code simultaneously editing multiple source files, changes rippling across interconnected codebase, refactoring visualization with connections between files, professional IDE aesthetic, smooth transitions between file views, impressive productivity demonstration"
  },
  {
    "id": "ep4_git",
    "episode": 4,
    "label": "Git Workflow",
    "prompt": "Git version control workflow visualization, commit history timeline flowing and branching, pull request creation with diff highlights, merge animations, branch management visualization, professional DevOps aesthetic with glowing connection lines"
  },
  {
    "id": "brand_intro",
    "episode": 0,
    "label": "Series Introduction",
    "prompt": "The AI-Powered Professional Stack title reveal, premium cinematic typography animation, letters assembling from particles, amber and electric teal accent colors on deep charcoal background, subtle lens flare, professional motion graphics, building anticipation"
  },
  {
    "id": "brand_transitions",
    "episode": 0,
    "label": "Episode Transitions",
    "prompt": "Smooth geometric transition animation, flowing abstract shapes morphing between states, premium motion graphics with amber and teal color palette, particle dissolution and reformation effects, professional broadcast quality, seamless loop potential"
  },
  {
    "id": "brand_outro",
    "episode": 0,
    "label": "Series Finale",
    "prompt": "Final brand lockup animation, four episode icons assembling into unified grid, Arthur Dell signature appearing below, premium ending sequence with subtle particle effects, professional fade to black, satisfying conclusion aesthetic"
  }
]

def submit_video(shot: dict) -> dict:
  """Submit a single video to Wan 2.6 API"""
  payload = {
    "model": "wan-ai/Wan2.1-T2V-14B",
    "task_type": "video_generation",
    "input": {
      "prompt": shot["prompt"],
      "negative_prompt": "blurry, low quality, distorted, ugly, watermark, text overlay, amateur",
      "duration": 15,
      "resolution": "720P",
      "seed": -1
    }
  }

  headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  }

  try:
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
  except Exception as e:
    return {"error": str(e)}

def check_status(task_id: str) -> dict:
  """Check task status"""
  headers = {"X-API-Key": API_KEY}
  try:
    response = requests.get(f"{API_URL}/{task_id}", headers=headers)
    return response.json()
  except Exception as e:
    return {"error": str(e)}

def download_video(url: str, filename: str) -> bool:
  """Download completed video"""
  try:
    response = requests.get(url, stream=True)
    output_path = OUTPUT_DIR / filename
    with open(output_path, 'wb') as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    return True
  except Exception as e:
    print(f"Download error: {e}")
    return False

def main():
  if not API_KEY:
    print("ERROR: PIAPI_KEY environment variable not set")
    sys.exit(1)

  print("=" * 70)
  print("WAN 2.6 API BATCH PRODUCTION - 15 SECOND VIDEOS")
  print(f"Total shots: {len(SHOTS_15S)}")
  print(f"Output: {OUTPUT_DIR}")
  print("=" * 70)

  # Submit all jobs
  jobs = []
  for i, shot in enumerate(SHOTS_15S, 1):
    print(f"\n[{i}/{len(SHOTS_15S)}] Submitting: {shot['label']}")
    result = submit_video(shot)

    if "error" in result:
      print(f"  ERROR: {result['error']}")
      jobs.append({"shot": shot, "status": "failed", "error": result["error"]})
    else:
      task_id = result.get("task_id") or result.get("data", {}).get("task_id")
      print(f"  Task ID: {task_id}")
      jobs.append({"shot": shot, "task_id": task_id, "status": "submitted"})

    time.sleep(1)  # Rate limiting

  # Monitor progress
  print("\n" + "=" * 70)
  print("MONITORING PROGRESS")
  print("=" * 70)

  completed = 0
  while completed < len(jobs):
    for job in jobs:
      if job["status"] in ["completed", "failed"]:
        continue

      task_id = job.get("task_id")
      if not task_id:
        continue

      status = check_status(task_id)
      state = status.get("data", {}).get("status") or status.get("status")

      if state == "completed":
        video_url = status.get("data", {}).get("output", {}).get("video_url")
        if video_url:
          filename = f"wan26_15s_{job['shot']['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
          print(f"\n✅ {job['shot']['label']}: Downloading...")
          if download_video(video_url, filename):
            job["status"] = "completed"
            job["output"] = str(OUTPUT_DIR / filename)
            completed += 1
            print(f"   Saved: {filename}")
      elif state == "failed":
        job["status"] = "failed"
        completed += 1
        print(f"\n❌ {job['shot']['label']}: Failed")

    pending = len([j for j in jobs if j["status"] not in ["completed", "failed"]])
    if pending > 0:
      print(f"\r  Pending: {pending}, Completed: {completed}", end="", flush=True)
      time.sleep(10)

  # Summary
  print("\n\n" + "=" * 70)
  print("PRODUCTION SUMMARY")
  print("=" * 70)

  successful = [j for j in jobs if j["status"] == "completed"]
  failed = [j for j in jobs if j["status"] == "failed"]

  print(f"Total: {len(jobs)} | Success: {len(successful)} | Failed: {len(failed)}")

  if successful:
    print("\nCompleted videos:")
    for j in successful:
      print(f"  ✅ {j['shot']['label']}: {j.get('output', 'N/A')}")

  if failed:
    print("\nFailed videos:")
    for j in failed:
      print(f"  ❌ {j['shot']['label']}: {j.get('error', 'Unknown error')}")

  # Save results
  results_path = OUTPUT_DIR / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  with open(results_path, 'w') as f:
    json.dump(jobs, f, indent=2, default=str)
  print(f"\nResults saved: {results_path}")

if __name__ == "__main__":
  main()
