#!/usr/bin/env python3
"""
DaVinci Resolve Project Setup for Episode 1: Hardware Foundation

Prerequisites:
  - DaVinci Resolve Studio must be running
  - Assets exported to resolve_projects/ep1_hardware/

Usage:
  python scripts/setup_resolve_ep1.py

This script:
  1. Creates a new project "LinkedIn_EP1_Hardware_Foundation"
  2. Imports all Episode 1 assets
  3. Creates a 1080p 30fps timeline
  4. Adds clips in the recommended shot order
"""

import sys
from pathlib import Path

# Add arthur module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.resolve.controller import ResolveController, TimelineClip, RenderPreset

ASSETS_DIR = Path("/Users/arthurdell/ARTHUR/resolve_projects/ep1_hardware")
PROJECT_NAME = "LinkedIn_EP1_Hardware_Foundation"
TIMELINE_NAME = "EP1_Main"

# Shot sequence for Episode 1 (120-second storyboard-aligned)
# 11 shots across 4 acts, 100 seconds of generated video
SHOT_SEQUENCE = [
  # ACT 1: THE SETUP (0:00 - 0:25)
  "ep1_01_workspace_establish.mp4",   # 1. Opening - Professional context (10s)
  "ep1_02_mac_studio_reveal.mp4",     # 2. Mac Studio hero introduction (10s)
  "ep1_03_mac_studio_ports.mp4",      # 3. Mac Studio connectivity (5s)

  # ACT 2: THE REVEAL (0:25 - 0:50)
  "ep1_04_dgx_spark_unbox.mp4",       # 4. DGX Spark dramatic reveal (10s)
  "ep1_05_dgx_spark_detail.mp4",      # 5. DGX Spark craftsmanship (5s)
  "ep1_06_side_by_side.mp4",          # 6. Direct comparison - the power duo (10s)

  # ACT 3: THE CAPABILITY (0:50 - 1:20)
  "ep1_07_neural_flow.mp4",           # 7. AI processing visualization (10s)
  "ep1_08_unified_memory.mp4",        # 8. Unified memory advantage (10s)
  "ep1_09_petaflop_viz.mp4",          # 9. PFLOP power visualization (10s)

  # ACT 4: THE INTEGRATION (1:20 - 2:00)
  "ep1_10_dual_workflow.mp4",         # 10. Dual system workflow (10s)
  "ep1_11_hero_closing.mp4",          # 11. Closing hero shot (10s)
]


def main():
  print("=" * 60)
  print("DaVinci Resolve - Episode 1 Project Setup")
  print("=" * 60)

  # Check assets exist
  if not ASSETS_DIR.exists():
    print(f"\nError: Assets directory not found: {ASSETS_DIR}")
    print("Run: python scripts/export_episode_assets.py --episode 1")
    sys.exit(1)

  available_assets = list(ASSETS_DIR.glob("*"))
  print(f"\nFound {len(available_assets)} assets in {ASSETS_DIR}")

  # Connect to Resolve
  print("\nConnecting to DaVinci Resolve...")
  try:
    resolve = ResolveController()
    resolve.connect()
    print(f"  Connected! Resolve version: {resolve.get_version()}")
  except Exception as e:
    print(f"\nError: Could not connect to DaVinci Resolve")
    print(f"  {e}")
    print("\nMake sure:")
    print("  1. DaVinci Resolve Studio is running")
    print("  2. Scripting is enabled in Preferences > System > General")
    sys.exit(1)

  # Create project
  print(f"\nCreating project: {PROJECT_NAME}")
  try:
    resolve.create_project(PROJECT_NAME)
    print("  Project created!")
  except Exception as e:
    print(f"  Warning: {e}")
    print("  Trying to open existing project...")
    try:
      resolve.open_project(PROJECT_NAME)
      print("  Opened existing project!")
    except Exception as e2:
      print(f"  Error: {e2}")
      sys.exit(1)

  # Import media
  print("\nImporting media files...")
  asset_paths = [ASSETS_DIR / name for name in SHOT_SEQUENCE if (ASSETS_DIR / name).exists()]
  try:
    items = resolve.import_media(asset_paths)
    print(f"  Imported {len(items)} clips")
  except Exception as e:
    print(f"  Error importing media: {e}")
    sys.exit(1)

  # Create timeline (1080p 30fps for LinkedIn)
  print(f"\nCreating timeline: {TIMELINE_NAME}")
  try:
    resolve.create_timeline(
      name=TIMELINE_NAME,
      width=1920,
      height=1080,
      fps=30.0
    )
    print("  Timeline created (1920x1080 @ 30fps)")
  except Exception as e:
    print(f"  Error creating timeline: {e}")
    sys.exit(1)

  # Add clips in sequence
  print("\nAdding clips to timeline...")
  clips = []
  for name in SHOT_SEQUENCE:
    path = ASSETS_DIR / name
    if path.exists():
      clips.append(TimelineClip(media_path=path))
      print(f"  + {name}")

  try:
    resolve.add_clips_to_timeline(clips)
    print(f"\n  Added {len(clips)} clips to timeline")
  except Exception as e:
    print(f"  Error adding clips: {e}")

  # Save project
  print("\nSaving project...")
  resolve.save_project()

  print("\n" + "=" * 60)
  print("PROJECT SETUP COMPLETE!")
  print("=" * 60)
  print(f"\nProject: {PROJECT_NAME}")
  print(f"Timeline: {TIMELINE_NAME}")
  print(f"Resolution: 1920x1080 @ 30fps")
  print(f"Clips: {len(clips)}")
  print("\nNext steps in DaVinci Resolve:")
  print("  1. Switch to Edit page - verify 11 clips loaded")
  print("  2. Clips are pre-timed (100s total) - add 20s of padding/transitions for 120s")
  print("  3. Add transitions (0.3-0.5s cross dissolves between acts)")
  print("  4. Switch to Fusion for text overlays (see PRODUCTION_GUIDE.md)")
  print("  5. Add Text+ nodes with Inter Bold font, amber (#f59e0b) accent")
  print("  6. Switch to Color for grading (4-node tree)")
  print("  7. Add 2-minute ambient music track in Fairlight (-14dB)")
  print("  8. Final review: 120 seconds, no gaps, text at correct timecodes")
  print("  9. Render via Deliver page (1080p, H.264, 30fps)")


if __name__ == "__main__":
  main()
