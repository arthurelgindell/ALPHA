#!/usr/bin/env python3
"""
Generate additional Episode 1 videos via Wan 2.6 API

Storyboard-aligned shots for 120-second LinkedIn video:
- Mac Studio M3 Ultra + NVIDIA DGX Spark
- Hardware Foundation narrative

Cost estimate: ~$6-8 for 80 seconds of additional footage
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.generators.wan26_api import Wan26APIClient

OUTPUT_DIR = Path("/Users/arthurdell/ARTHUR/resolve_projects/ep1_hardware")

# Episode 1 Shot List - Storyboard Aligned
# Each shot maps to a specific narrative beat
EP1_SHOTS = [
  # ═══════════════════════════════════════════════════════════════════
  # ACT 1: THE SETUP (0:00 - 0:30) - Establishing credibility
  # ═══════════════════════════════════════════════════════════════════
  {
    "id": "ep1_01_workspace_establish",
    "prompt": "Cinematic establishing shot of premium home office workspace, morning light streaming through windows, sleek desk setup with multiple monitors, executive chair, dark wood and metal aesthetic, professional tech environment, shallow depth of field, 4K quality",
    "duration": 10,
    "narrative": "Opening - Establish the professional context"
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
    "narrative": "Mac Studio connectivity and capability"
  },

  # ═══════════════════════════════════════════════════════════════════
  # ACT 2: THE REVEAL (0:30 - 1:00) - DGX Spark introduction
  # ═══════════════════════════════════════════════════════════════════
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
    "narrative": "DGX Spark craftsmanship details"
  },
  {
    "id": "ep1_06_side_by_side",
    "prompt": "Two premium desktop computers side by side on executive desk, silver aluminum cube and champagne gold compact unit, coffee mug for scale reference, symmetrical composition, premium office environment, professional product photography",
    "duration": 10,
    "narrative": "Direct comparison - the power duo"
  },

  # ═══════════════════════════════════════════════════════════════════
  # ACT 3: THE CAPABILITY (1:00 - 1:40) - What they can do
  # ═══════════════════════════════════════════════════════════════════
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

  # ═══════════════════════════════════════════════════════════════════
  # ACT 4: THE INTEGRATION (1:40 - 2:00) - Working together
  # ═══════════════════════════════════════════════════════════════════
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
    "narrative": "Closing hero shot - the complete foundation"
  },
]

def generate_episode_1_videos():
  """Generate all Episode 1 videos via Wan 2.6 API"""

  print("=" * 70)
  print("EPISODE 1: HARDWARE FOUNDATION - VIDEO GENERATION")
  print("=" * 70)

  # Calculate totals
  total_duration = sum(s["duration"] for s in EP1_SHOTS)
  total_cost = total_duration * 0.08  # 720P pricing

  print(f"\nPlanned shots: {len(EP1_SHOTS)}")
  print(f"Total duration: {total_duration} seconds")
  print(f"Estimated cost: ${total_cost:.2f} (720P)")

  # Check which shots already exist
  existing = []
  to_generate = []

  for shot in EP1_SHOTS:
    expected_file = OUTPUT_DIR / f"{shot['id']}.mp4"
    if expected_file.exists():
      existing.append(shot)
    else:
      to_generate.append(shot)

  print(f"\nAlready generated: {len(existing)}")
  print(f"To generate: {len(to_generate)}")

  if not to_generate:
    print("\n✅ All shots already generated!")
    return

  gen_duration = sum(s["duration"] for s in to_generate)
  gen_cost = gen_duration * 0.08
  print(f"\nThis run: {gen_duration}s, ~${gen_cost:.2f}")

  # Confirm
  confirm = input("\nProceed with generation? [y/N] ").strip().lower()
  if confirm != 'y':
    print("Cancelled.")
    return

  # Initialize API client
  print("\nInitializing Wan 2.6 API client...")
  try:
    client = Wan26APIClient()
  except ValueError as e:
    print(f"Error: {e}")
    print("\nSet WAN26_API_KEY environment variable:")
    print("  export WAN26_API_KEY='your-api-key'")
    return

  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

  # Generate each shot
  results = []
  for i, shot in enumerate(to_generate, 1):
    print(f"\n{'─' * 70}")
    print(f"Shot {i}/{len(to_generate)}: {shot['id']}")
    print(f"Narrative: {shot['narrative']}")
    print(f"Duration: {shot['duration']}s")
    print(f"{'─' * 70}")

    # Submit generation
    print(f"Submitting: {shot['prompt'][:80]}...")
    result = client.text_to_video(
      prompt=shot["prompt"],
      duration=shot["duration"],
      resolution="720P",
      aspect_ratio="16:9",
      with_audio=False,  # We'll add music in DaVinci
      prompt_extend=True
    )

    if not result.success:
      print(f"❌ Failed to submit: {result.error}")
      continue

    print(f"Task ID: {result.task_id}")
    print(f"Waiting for completion...")

    # Wait for completion
    video_url = client.wait_for_completion(
      result.task_id,
      timeout=300,
      poll_interval=10
    )

    if not video_url:
      print(f"❌ Generation failed or timed out")
      continue

    # Download video
    output_path = OUTPUT_DIR / f"{shot['id']}.mp4"
    print(f"Downloading to {output_path}...")

    if client.download_video(result.task_id, output_path):
      size_mb = output_path.stat().st_size / (1024 * 1024)
      print(f"✅ Saved: {output_path.name} ({size_mb:.2f} MB)")
      results.append({
        "shot": shot["id"],
        "path": str(output_path),
        "duration": shot["duration"],
        "narrative": shot["narrative"]
      })
    else:
      print(f"❌ Download failed")

    # Brief pause between generations
    if i < len(to_generate):
      print("Waiting 5s before next generation...")
      time.sleep(5)

  # Summary
  print("\n" + "=" * 70)
  print("GENERATION COMPLETE")
  print("=" * 70)
  print(f"\nSuccessfully generated: {len(results)}/{len(to_generate)}")

  if results:
    print("\nGenerated shots:")
    for r in results:
      print(f"  ✓ {r['shot']} ({r['duration']}s) - {r['narrative']}")

    total_new = sum(r["duration"] for r in results)
    print(f"\nNew footage: {total_new} seconds")
    print(f"Actual cost: ~${total_new * 0.08:.2f}")

  client.close()


if __name__ == "__main__":
  generate_episode_1_videos()
