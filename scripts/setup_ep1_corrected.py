#!/usr/bin/env python3
"""
DaVinci Resolve Project Setup for CORRECTED Episode 1: Hardware Foundation

This script creates a LinkedIn-optimized 9:16 VERTICAL video showcasing:
- 2× Mac Studio M3 Ultra (Apple stock imagery)
- NVIDIA DGX Spark (NVIDIA stock imagery)
- FLUX-generated infographics
- Reusable abstract AI visualization footage

Prerequisites:
  - DaVinci Resolve Studio must be running
  - All assets downloaded to stock_assets/

Usage:
  python scripts/setup_ep1_corrected.py
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Add arthur module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.resolve.controller import ResolveController, TimelineClip

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_NAME = "LinkedIn_TechStack_EP01_Hardware_CORRECTED"
TIMELINE_NAME = "EP1_Vertical_Main"

# 9:16 VERTICAL format for LinkedIn
TIMELINE_WIDTH = 1080
TIMELINE_HEIGHT = 1920
TIMELINE_FPS = 30.0

# Asset directories
STOCK_ASSETS = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets")
APPLE_DIR = STOCK_ASSETS / "apple"
NVIDIA_DIR = STOCK_ASSETS / "nvidia"
INFOGRAPHICS_DIR = STOCK_ASSETS / "infographics"
ABSTRACT_VIDEO_DIR = Path("/Users/arthurdell/ARTHUR/resolve_projects/ep1_hardware")

# Output directory
OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/exports")

# ============================================================================
# SHOT SEQUENCE (60 seconds total)
# ============================================================================

@dataclass
class Shot:
  """Represents a shot in the storyboard"""
  id: str
  filename: str
  duration_sec: float
  description: str
  text_overlay: Optional[str] = None
  text_position: str = "lower_third"  # lower_third, centered, top
  is_still_image: bool = False  # True = needs Ken Burns motion
  ken_burns: str = "zoom_in"  # zoom_in, zoom_out, pan_left, pan_right


# Part 1: Mac Studio Introduction (0:00-0:20)
SHOTS_PART1 = [
  Shot(
    id="01_title",
    filename="mac_studio_spec_bg.png",
    duration_sec=4.0,
    description="Title card on dark background",
    text_overlay="THE FOUNDATION",
    text_position="centered",
    is_still_image=True,
    ken_burns="none"
  ),
  Shot(
    id="02_mac_hero",
    filename="mac_studio_hero_4k.jpg",
    duration_sec=4.0,
    description="Two Mac Studios side-by-side",
    is_still_image=True,
    ken_burns="zoom_in"
  ),
  Shot(
    id="03_mac_ports",
    filename="mac_studio_ports_4k.jpg",
    duration_sec=4.0,
    description="Ventilation grille / ports macro",
    is_still_image=True,
    ken_burns="pan_right"
  ),
  Shot(
    id="04_mac_spec",
    filename="mac_studio_spec_bg.png",
    duration_sec=4.0,
    description="Spec infographic overlay",
    text_overlay="1TB UNIFIED MEMORY\n160 GPU CORES COMBINED",
    text_position="centered",
    is_still_image=True,
    ken_burns="none"
  ),
  Shot(
    id="05_mac_lifestyle",
    filename="mac_studio_lifestyle_4k.jpg",
    duration_sec=4.0,
    description="Hero lifestyle shot",
    is_still_image=True,
    ken_burns="zoom_out"
  ),
]

# Part 2: DGX Spark Introduction (0:20-0:40)
SHOTS_PART2 = [
  Shot(
    id="06_dgx_hero",
    filename="dgx_product_1.jpg",
    duration_sec=4.0,
    description="DGX Spark reveal, champagne gold",
    text_overlay="NVIDIA DGX SPARK",
    text_position="lower_third",
    is_still_image=True,
    ken_burns="zoom_in"
  ),
  Shot(
    id="07_dgx_scale",
    filename="dgx_product_2.jpg",
    duration_sec=4.0,
    description="Scale comparison",
    is_still_image=True,
    ken_burns="pan_left"
  ),
  Shot(
    id="08_dgx_spec",
    filename="dgx_spark_spec_bg.png",
    duration_sec=4.0,
    description="Spec infographic",
    text_overlay="1 PETAFLOP\n128GB UNIFIED",
    text_position="centered",
    is_still_image=True,
    ken_burns="none"
  ),
  Shot(
    id="09_dgx_detail",
    filename="dgx_product_3.jpg",
    duration_sec=4.0,
    description="Grille detail",
    is_still_image=True,
    ken_burns="zoom_in"
  ),
  Shot(
    id="10_dgx_brand",
    filename="dgx_product_4.jpg",
    duration_sec=4.0,
    description="Branding detail",
    text_overlay="DESKTOP SIZE",
    text_position="lower_third",
    is_still_image=True,
    ken_burns="pan_right"
  ),
]

# Part 3: The Power Duo (0:40-1:00)
SHOTS_PART3 = [
  Shot(
    id="11_power_duo",
    filename="power_duo_comparison_bg.png",
    duration_sec=4.0,
    description="Both devices side by side",
    text_overlay="THE POWER DUO",
    text_position="centered",
    is_still_image=True,
    ken_burns="none"
  ),
  Shot(
    id="12_neural_flow",
    filename="ep1_07_neural_flow.mp4",
    duration_sec=4.0,
    description="Neural flow visualization",
    text_overlay="AI PROCESSING",
    text_position="lower_third",
    is_still_image=False
  ),
  Shot(
    id="13_data_flow",
    filename="data_flow_viz.png",
    duration_sec=4.0,
    description="Data flow infographic",
    text_overlay="1.5+ PETAFLOPS LOCAL",
    text_position="centered",
    is_still_image=True,
    ken_burns="zoom_in"
  ),
  Shot(
    id="14_no_cloud",
    filename="power_duo_comparison_bg.png",
    duration_sec=4.0,
    description="Capability comparison",
    text_overlay="NO CLOUD. NO API COSTS.",
    text_position="centered",
    is_still_image=True,
    ken_burns="none"
  ),
  Shot(
    id="15_cta",
    filename="mac_studio_setup_4k.jpg",
    duration_sec=4.0,
    description="Hero closing + CTA",
    text_overlay="FULL CONTROL → FOLLOW",
    text_position="centered",
    is_still_image=True,
    ken_burns="zoom_out"
  ),
]

ALL_SHOTS = SHOTS_PART1 + SHOTS_PART2 + SHOTS_PART3

# ============================================================================
# TEXT OVERLAY SPECIFICATIONS
# ============================================================================

TEXT_OVERLAYS = {
  "THE FOUNDATION": {
    "timecode": "00:00:00:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Black",
    "size": 96,
    "color": "#f5f5f5",
    "position": "center"
  },
  "1TB UNIFIED MEMORY": {
    "timecode": "00:00:12:00",
    "duration": "00:00:04:00",
    "style": "spec",
    "font": "JetBrains Mono",
    "weight": "Bold",
    "size": 48,
    "color": "#d4a373",
    "position": "center"
  },
  "160 GPU CORES COMBINED": {
    "timecode": "00:00:12:00",
    "duration": "00:00:04:00",
    "style": "spec",
    "font": "JetBrains Mono",
    "weight": "Bold",
    "size": 48,
    "color": "#d4a373",
    "position": "center_below"
  },
  "NVIDIA DGX SPARK": {
    "timecode": "00:00:20:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Black",
    "size": 72,
    "color": "#76b900",
    "position": "lower_third"
  },
  "1 PETAFLOP": {
    "timecode": "00:00:28:00",
    "duration": "00:00:04:00",
    "style": "spec_large",
    "font": "JetBrains Mono",
    "weight": "Bold",
    "size": 72,
    "color": "#d4a373",
    "position": "center"
  },
  "128GB UNIFIED": {
    "timecode": "00:00:28:00",
    "duration": "00:00:04:00",
    "style": "spec",
    "font": "JetBrains Mono",
    "weight": "Bold",
    "size": 48,
    "color": "#d4a373",
    "position": "center_below"
  },
  "DESKTOP SIZE": {
    "timecode": "00:00:36:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Black",
    "size": 48,
    "color": "#f5f5f5",
    "position": "lower_third"
  },
  "THE POWER DUO": {
    "timecode": "00:00:40:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Black",
    "size": 96,
    "color": "#f5f5f5",
    "position": "center"
  },
  "AI PROCESSING": {
    "timecode": "00:00:44:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Bold",
    "size": 60,
    "color": "#f5f5f5",
    "position": "lower_third"
  },
  "1.5+ PETAFLOPS LOCAL": {
    "timecode": "00:00:48:00",
    "duration": "00:00:04:00",
    "style": "spec",
    "font": "JetBrains Mono",
    "weight": "Bold",
    "size": 48,
    "color": "#d4a373",
    "position": "center"
  },
  "NO CLOUD. NO API COSTS.": {
    "timecode": "00:00:52:00",
    "duration": "00:00:04:00",
    "style": "title",
    "font": "Inter",
    "weight": "Black",
    "size": 48,
    "color": "#f5f5f5",
    "position": "center"
  },
  "FULL CONTROL → FOLLOW": {
    "timecode": "00:00:56:00",
    "duration": "00:00:04:00",
    "style": "cta",
    "font": "Inter",
    "weight": "Black",
    "size": 48,
    "color": "#4ecdc4",
    "position": "center"
  },
}

# ============================================================================
# COLOR GRADING SPECIFICATION
# ============================================================================

COLOR_GRADE = {
  "node_1_balance": {
    "lift": 0.0,
    "gamma": 0.98,
    "gain": 1.02,
    "description": "Neutralize source, slight contrast boost"
  },
  "node_2_look": {
    "highlights_hue": "#d4a373",  # Amber
    "shadows_hue": "#1a1a1a",     # Deep charcoal
    "saturation": 0.85,
    "description": "Amber highlights, cool shadows"
  },
  "node_3_vignette": {
    "amount": 0.3,
    "softness": 0.7,
    "description": "Subtle vignette for focus"
  }
}


def get_asset_path(shot: Shot) -> Path:
  """Resolve full path for a shot's asset"""
  # Check each directory for the file
  for directory in [APPLE_DIR, NVIDIA_DIR, INFOGRAPHICS_DIR, ABSTRACT_VIDEO_DIR]:
    path = directory / shot.filename
    if path.exists():
      return path

  # Fallback: check with different extensions
  base = Path(shot.filename).stem
  for directory in [APPLE_DIR, NVIDIA_DIR, INFOGRAPHICS_DIR]:
    for ext in ['.jpg', '.png', '.mp4']:
      path = directory / f"{base}{ext}"
      if path.exists():
        return path

  return None


def verify_assets() -> tuple[List[Shot], List[Shot]]:
  """Verify all assets exist and categorize them"""
  found = []
  missing = []

  for shot in ALL_SHOTS:
    path = get_asset_path(shot)
    if path and path.exists():
      found.append(shot)
    else:
      missing.append(shot)

  return found, missing


def main():
  print("=" * 70)
  print("LinkedIn Episode 1: Hardware Foundation - CORRECTED Setup")
  print("=" * 70)
  print(f"\nFormat: {TIMELINE_WIDTH}×{TIMELINE_HEIGHT} @ {TIMELINE_FPS}fps (9:16 VERTICAL)")
  print(f"Duration: {len(ALL_SHOTS) * 4} seconds ({len(ALL_SHOTS)} shots × 4s each)")

  # Verify assets
  print("\n" + "-" * 70)
  print("ASSET VERIFICATION")
  print("-" * 70)

  found, missing = verify_assets()

  print(f"\n✅ Found: {len(found)}/{len(ALL_SHOTS)} assets")
  for shot in found:
    path = get_asset_path(shot)
    print(f"   [{shot.id}] {shot.filename}")

  if missing:
    print(f"\n❌ Missing: {len(missing)} assets")
    for shot in missing:
      print(f"   [{shot.id}] {shot.filename} - {shot.description}")
    print("\nPlease download missing assets before continuing.")
    sys.exit(1)

  # Connect to Resolve
  print("\n" + "-" * 70)
  print("DAVINCI RESOLVE CONNECTION")
  print("-" * 70)

  try:
    print("\nConnecting to DaVinci Resolve...")
    resolve = ResolveController()
    resolve.connect()
    print(f"  ✅ Connected! Version: {resolve.get_version()}")
  except Exception as e:
    print(f"\n❌ Error: Could not connect to DaVinci Resolve")
    print(f"   {e}")
    print("\n   Make sure:")
    print("   1. DaVinci Resolve Studio is running")
    print("   2. Scripting enabled: Preferences > System > General")
    sys.exit(1)

  # Create project
  print("\n" + "-" * 70)
  print("PROJECT SETUP")
  print("-" * 70)

  print(f"\nCreating project: {PROJECT_NAME}")
  try:
    resolve.create_project(PROJECT_NAME)
    print("  ✅ Project created!")
  except Exception as e:
    print(f"  ⚠️ {e}")
    print("  Attempting to open existing project...")
    try:
      resolve.open_project(PROJECT_NAME)
      print("  ✅ Opened existing project!")
    except Exception as e2:
      print(f"  ❌ Error: {e2}")
      sys.exit(1)

  # Import media
  print("\nImporting media files...")
  asset_paths = [get_asset_path(shot) for shot in ALL_SHOTS if get_asset_path(shot)]

  try:
    items = resolve.import_media(asset_paths)
    print(f"  ✅ Imported {len(items)} clips")
  except Exception as e:
    print(f"  ❌ Error importing media: {e}")
    sys.exit(1)

  # Create timeline (9:16 VERTICAL)
  print(f"\nCreating timeline: {TIMELINE_NAME}")
  try:
    resolve.create_timeline(
      name=TIMELINE_NAME,
      width=TIMELINE_WIDTH,
      height=TIMELINE_HEIGHT,
      fps=TIMELINE_FPS
    )
    print(f"  ✅ Timeline created ({TIMELINE_WIDTH}×{TIMELINE_HEIGHT} @ {TIMELINE_FPS}fps)")
  except Exception as e:
    print(f"  ❌ Error creating timeline: {e}")
    sys.exit(1)

  # Add clips in sequence
  print("\nAdding clips to timeline...")
  clips = []
  for shot in ALL_SHOTS:
    path = get_asset_path(shot)
    if path:
      clips.append(TimelineClip(media_path=path))
      print(f"  + [{shot.id}] {shot.filename} ({shot.duration_sec}s)")

  try:
    resolve.add_clips_to_timeline(clips)
    print(f"\n  ✅ Added {len(clips)} clips to timeline")
  except Exception as e:
    print(f"  ❌ Error adding clips: {e}")

  # Save project
  print("\nSaving project...")
  resolve.save_project()
  print("  ✅ Project saved!")

  # Print manual instructions
  print("\n" + "=" * 70)
  print("PROJECT SETUP COMPLETE!")
  print("=" * 70)

  print(f"""
Project: {PROJECT_NAME}
Timeline: {TIMELINE_NAME}
Format: {TIMELINE_WIDTH}×{TIMELINE_HEIGHT} @ {TIMELINE_FPS}fps (9:16 VERTICAL)
Duration: {len(ALL_SHOTS) * 4} seconds
Clips: {len(clips)}
""")

  print("-" * 70)
  print("MANUAL STEPS REQUIRED IN DAVINCI RESOLVE")
  print("-" * 70)

  print("""
1. SWITCH TO EDIT PAGE
   - Verify all 15 clips are loaded in timeline
   - Each clip should be exactly 4 seconds (120 frames @ 30fps)

2. APPLY KEN BURNS TO STILL IMAGES
   For each still image clip (shots 01-05, 06-10, 11, 13-15):

   a) Select clip → Inspector → Transform
   b) Set keyframes at start and end for Zoom and Position:

   | Shot | Effect     | Start    | End      |
   |------|------------|----------|----------|
   | zoom_in  | Zoom 1.0 → 1.15, slight position drift |
   | zoom_out | Zoom 1.15 → 1.0 |
   | pan_left | Position X: 0 → -50, Zoom 1.1 |
   | pan_right| Position X: 0 → +50, Zoom 1.1 |

   c) Set ease-in/ease-out on keyframes for smooth motion

3. ADD TEXT OVERLAYS IN FUSION
   For each text overlay:

   a) Select clip → Right-click → Open in Fusion Page
   b) Add Text+ node between MediaIn and MediaOut
   c) IMPORTANT: Connect through Merge node!
      MediaIn → Merge (Background)
      Text+ → Merge (Foreground)
      Merge → MediaOut

   Text Specifications:
""")

  for text, spec in TEXT_OVERLAYS.items():
    print(f"   {spec['timecode']}: \"{text}\"")
    print(f"      Font: {spec['font']} {spec['weight']}, {spec['size']}pt")
    print(f"      Color: {spec['color']}")
    print()

  print("""
4. COLOR GRADING (Color Page)
   Apply 3-node grade:

   Node 1: Balance
     - Lift: 0.0, Gamma: 0.98, Gain: 1.02

   Node 2: Look
     - Add amber (#d4a373) to highlights
     - Keep shadows neutral/cool
     - Saturation: 85%

   Node 3: Vignette (optional)
     - Amount: 0.3, Softness: 0.7

5. AUDIO (Fairlight Page)
   - No voiceover needed (text-only narrative)
   - Add ambient electronic music at -14dB
   - Fade in first 2 seconds
   - Fade out last 2 seconds

6. EXPORT (Deliver Page)
   - Format: MP4 (H.264)
   - Resolution: 1080×1920
   - Frame Rate: 30fps
   - Quality: High
   - Output: /Volumes/STUDIO/VIDEO/linkedin_series/exports/

7. VERIFICATION CHECKLIST
   [ ] Video is 9:16 VERTICAL (not 16:9)
   [ ] All 11 text overlays visible
   [ ] Hardware images are official stock (not AI-generated)
   [ ] DGX Spark shows champagne gold color
   [ ] Ken Burns motion smooth on all stills
   [ ] Total duration: 60 seconds
   [ ] No black screens or compositing errors
""")

  print("-" * 70)
  print("TEXT OVERLAY COLOR REFERENCE")
  print("-" * 70)
  print("""
| Color Name    | Hex     | Usage                    |
|---------------|---------|--------------------------|
| Off-White     | #f5f5f5 | Primary text (titles)    |
| Amber Gold    | #d4a373 | Specs, accent highlights |
| Electric Teal | #4ecdc4 | CTA, secondary accent    |
| NVIDIA Green  | #76b900 | NVIDIA branding          |
| Deep Charcoal | #1a1a1a | Background               |
""")

  print("\n✅ Setup complete! Open DaVinci Resolve to continue.")


if __name__ == "__main__":
  main()
