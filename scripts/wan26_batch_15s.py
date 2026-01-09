#!/usr/bin/env python3
"""
Wan 2.6 API Batch - 15-second videos for 8-minute LinkedIn series
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

# 15-second hero shots
SHOTS = [
  {"id": "ep1_hero", "label": "Mac Studio Hero Reveal", "prompt": "Cinematic product reveal of Apple Mac Studio M3 Ultra, compact silver aluminum desktop box with rounded corners and ventilation holes on top, dramatic lighting sweep from left to right revealing machined aluminum surface, professional studio lighting on seamless dark background, shallow depth of field, smooth camera motion, premium tech product commercial, 8K quality"},
  {"id": "ep1_dual", "label": "Mac Studio Dual Setup", "prompt": "Two Apple Mac Studio computers side by side on premium walnut desk in professional workspace, warm amber accent lighting from above, organized cable management, cinematic slow dolly shot moving right to left, shallow depth of field, professional photography, 8K quality"},
  {"id": "ep1_perf", "label": "M3 Ultra Performance", "prompt": "Abstract visualization of Apple M3 Ultra chip performance, neural engine pathways glowing in amber and electric teal colors, data streams flowing through unified memory architecture, particle effects representing compute power, dark background with subtle grid, cinematic camera push-in"},
  {"id": "ep1_workflow", "label": "Creative Workflow", "prompt": "Professional creative workflow on Mac Studio, multiple 4K video timeline streams, AI model training dashboard with live metrics, smooth transitions between applications, productive workspace aesthetic, modern UI design, screen recording style"},
  {"id": "ep2_unbox", "label": "DGX Spark Unboxing", "prompt": "Cinematic unboxing reveal of NVIDIA DGX Spark desktop supercomputer, champagne gold metallic finish emerging from premium black packaging, dramatic top-down camera angle slowly revealing the device, professional studio lighting with soft shadows, luxury product reveal aesthetic"},
  {"id": "ep2_scale", "label": "DGX Spark Scale", "prompt": "NVIDIA DGX Spark desktop supercomputer next to everyday objects showing compact size - coffee mug, hardcover book, smartphone - demonstrating petaflop AI performance in small form factor, smooth 360 degree camera orbit, clean white surface, professional product photography"},
  {"id": "ep2_ai", "label": "DGX Spark AI Inference", "prompt": "Abstract visualization of AI inference running on NVIDIA DGX Spark, neural network layer activations lighting up in sequence, data flowing through Grace Blackwell architecture, electric teal and amber particle streams, cinematic camera flying through the network"},
  {"id": "ep2_bench", "label": "DGX Spark Benchmarks", "prompt": "Animated benchmark results and performance charts for DGX Spark, bar graphs rising, data visualizations materializing in 3D space, professional infographic animation style, dark background with glowing data points, smooth transitions between metrics"},
  {"id": "ep3_universe", "label": "AI Model Universe", "prompt": "Expansive visualization of AI model ecosystem, floating holographic model cards and neural network architectures arranged in 3D constellation, camera flying through this universe of AI capabilities, stars and connections between models, deep space aesthetic with nebula colors"},
  {"id": "ep3_deepseek", "label": "DeepSeek Architecture", "prompt": "DeepSeek large language model architecture visualization, mixture of experts routing system with tokens flowing to specialized expert modules, attention pattern matrices lighting up, technical diagram transforming into beautiful 3D animation, data flows in amber and teal"},
  {"id": "ep3_multi", "label": "Multi-Model Orchestration", "prompt": "Multiple AI models working together in orchestrated workflow, visual representation of model handoffs and specialization, conductor-style coordination visualization, different model types as distinct glowing nodes, smooth data flow between them, professional infographic aesthetic"},
  {"id": "ep3_output", "label": "AI Output Generation", "prompt": "AI generating creative content in real-time, text appearing character by character, images rendering progressively, code syntax highlighting as it writes, multiple output types emerging simultaneously, productive visualization, dark interface with glowing outputs"},
  {"id": "ep4_term", "label": "Claude Code Terminal", "prompt": "Developer terminal launching Claude Code CLI, command line interface with syntax highlighting appearing, code suggestions scrolling smoothly, professional dark theme terminal, dramatic screen glow illuminating keyboard and desk, cinematic rack focus"},
  {"id": "ep4_code", "label": "Claude Code Generation", "prompt": "Claude Code AI generating production code in real-time, syntax highlighted code appearing line by line, intelligent completions and suggestions showing, split view with file tree navigation, productive professional developer aesthetic"},
  {"id": "ep4_edit", "label": "Multi-File Editing", "prompt": "Claude Code simultaneously editing multiple source files, changes rippling across interconnected codebase, refactoring visualization with connections between files, professional IDE aesthetic, smooth transitions between file views"},
  {"id": "ep4_git", "label": "Git Workflow", "prompt": "Git version control workflow visualization, commit history timeline flowing and branching, pull request creation with diff highlights, merge animations, branch management visualization, professional DevOps aesthetic with glowing connection lines"},
  {"id": "brand_intro", "label": "Series Introduction", "prompt": "The AI-Powered Professional Stack title reveal, premium cinematic typography animation, letters assembling from particles, amber and electric teal accent colors on deep charcoal background, subtle lens flare, professional motion graphics"},
  {"id": "brand_trans", "label": "Episode Transitions", "prompt": "Smooth geometric transition animation, flowing abstract shapes morphing between states, premium motion graphics with amber and teal color palette, particle dissolution and reformation effects, professional broadcast quality"},
  {"id": "brand_outro", "label": "Series Finale", "prompt": "Final brand lockup animation, four episode icons assembling into unified grid, professional signature appearing below, premium ending sequence with subtle particle effects, fade to black, satisfying conclusion"}
]


def main():
  print("=" * 70)
  print("WAN 2.6 API - 15 SECOND VIDEO BATCH")
  print(f"Shots: {len(SHOTS)} | Duration: 15s each | Total: {len(SHOTS)*15}s")
  print(f"Output: {OUTPUT_DIR}")
  print("=" * 70)

  # Initialize client (validates API key)
  try:
    client = Wan26APIClient()
  except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

  jobs = []

  # Submit all
  for i, shot in enumerate(SHOTS, 1):
    print(f"\n[{i}/{len(SHOTS)}] {shot['label']}")

    result = client.text_to_video(
      prompt=shot["prompt"],
      duration=15,
      resolution="720P",
      aspect_ratio="16:9",
      with_audio=False,
      prompt_extend=True
    )

    if result.success:
      print(f"  Submitted: {result.task_id}")
      jobs.append({
        "shot": shot,
        "task_id": result.task_id,
        "status": "pending",
        "cost_estimate": result.cost_estimate
      })
    else:
      print(f"  ERROR: {result.error}")
      jobs.append({"shot": shot, "status": "failed", "error": result.error})

    time.sleep(0.5)  # Rate limit protection

  # Monitor
  print("\n" + "=" * 70)
  print("MONITORING...")
  print("=" * 70)

  pending_jobs = [j for j in jobs if j["status"] == "pending"]

  while pending_jobs:
    for job in pending_jobs:
      status = client.get_task_status(job["task_id"])

      if status.get("status") in ("Completed", "completed") and status.get("video_url"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wan26_15s_{job['shot']['id']}_{ts}.mp4"
        path = OUTPUT_DIR / filename

        print(f"\n✅ {job['shot']['label']}: Downloading...")

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
        print(f"\n❌ {job['shot']['label']}: {job['error']}")

    pending_jobs = [j for j in jobs if j["status"] == "pending"]
    completed = len([j for j in jobs if j["status"] == "completed"])
    failed = len([j for j in jobs if j["status"] in ("failed", "download_failed")])

    print(f"\r  Pending: {len(pending_jobs)} | Completed: {completed} | Failed: {failed}", end="", flush=True)

    if pending_jobs:
      time.sleep(10)

  # Cleanup
  client.close()

  # Summary
  print("\n\n" + "=" * 70)
  print("SUMMARY")
  print("=" * 70)

  ok = [j for j in jobs if j["status"] == "completed"]
  fail = [j for j in jobs if j["status"] in ("failed", "download_failed")]

  print(f"Total: {len(jobs)} | Success: {len(ok)} | Failed: {len(fail)}")

  if ok:
    total_size = sum(j.get("size", 0) for j in ok)
    total_duration = len(ok) * 15
    total_cost = sum(j.get("cost_estimate", 0) for j in ok)
    print(f"Total duration: {total_duration}s ({total_duration/60:.1f} min)")
    print(f"Total size: {total_size:.1f}MB")
    print(f"Est. cost: ${total_cost:.2f}")

  # Save results
  results_path = OUTPUT_DIR / f"batch_15s_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  with open(results_path, 'w') as f:
    json.dump({
      "shots": len(SHOTS),
      "completed": len(ok),
      "failed": len(fail),
      "jobs": jobs
    }, f, indent=2, default=str)
  print(f"\nResults: {results_path}")


if __name__ == "__main__":
  main()
