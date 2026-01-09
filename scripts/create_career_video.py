#!/usr/bin/env python3
"""
Arthur Dell Career Journey Video Production Script

Creates a sequential video representing Arthur Dell's career journey
using media assets from STUDIO volume and DaVinci Resolve Studio.

Usage:
  python3 scripts/create_career_video.py

Requirements:
  - DaVinci Resolve Studio 20+ running
  - STUDIO volume mounted at /Volumes/STUDIO
  - Media assets named appropriately for matching
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add arthur package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.resolve.controller import (
  ResolveController,
  ResolveError,
  TimelineClip,
  TextOverlay,
  RenderPreset
)

# ============================================================================
# Career Timeline Data Structure
# ============================================================================

@dataclass
class CareerPhase:
  """A phase in Arthur Dell's career journey"""
  company: str
  role: str
  years: str
  location: str
  text_overlay: str  # Short text for upper-left corner
  media_files: list[str]  # Media file name patterns to match
  duration_per_clip: float = 5.0  # seconds per clip

# Career timeline in chronological order (earliest first)
CAREER_TIMELINE = [
  CareerPhase(
    company="BMW AG Group",
    role="Systems Engineer",
    years="1991-1994",
    location="South Africa",
    text_overlay="BMW AG Group | 1991-1994",
    media_files=["BMW", "IBM_Mainframe"]
  ),
  CareerPhase(
    company="ACSA",
    role="IT Manager",
    years="1995-1998",
    location="South Africa",
    text_overlay="Airports Company SA | 1995-1998",
    media_files=["ACSA"]
  ),
  CareerPhase(
    company="BSI",
    role="Co-Founder & Director",
    years="1998-2005",
    location="Dubai & South Africa",
    text_overlay="BSI Systems Integration | 1998-2005",
    media_files=["BSI"]
  ),
  CareerPhase(
    company="Sun Microsystems",
    role="Professional Services Leader",
    years="2005-2009",
    location="EMEA & Russia/CIS",
    text_overlay="Sun Microsystems | 2005-2009",
    media_files=["Sun_Microsystems", "sun_datacenter"]
  ),
  CareerPhase(
    company="Hewlett-Packard",
    role="Professional Services Director",
    years="2009-2011",
    location="MEMA",
    text_overlay="HP Software | 2009-2011",
    media_files=["HP"]
  ),
  CareerPhase(
    company="Symantec",
    role="Senior Director",
    years="2013-2014",
    location="EMEA Emerging Markets",
    text_overlay="Symantec Corporation | 2013-2014",
    media_files=["Symantec"]
  ),
  CareerPhase(
    company="Citrix Systems",
    role="Vice President",
    years="2014-2017",
    location="MEA & Turkey",
    text_overlay="Citrix Systems | 2014-2017",
    media_files=["Citrix"]
  ),
  CareerPhase(
    company="Veritas Technologies",
    role="Field Technology Leader",
    years="2017-2024",
    location="Middle East & Africa",
    text_overlay="Veritas Technologies | 2017-2024",
    media_files=["AI brand", "AI Security", "brand_message"]
  ),
  CareerPhase(
    company="AI Ventures",
    role="AI Entrepreneur & Advisor",
    years="2025-Present",
    location="Dubai",
    text_overlay="AI Ventures | 2025",
    media_files=["AI 02_humanoid", "AI 04_ai_research", "AI holographic", "AI neural"]
  ),
  CareerPhase(
    company="The Future",
    role="",
    years="",
    location="",
    text_overlay="The Future is AI",
    media_files=["AI Boardroom", "AI capable", "AI productivity"]
  ),
  CareerPhase(
    company="Connect",
    role="",
    years="",
    location="",
    text_overlay="Connect with Arthur Dell",
    media_files=["Arthur Dell", "Final Close"]
  ),
]

# ============================================================================
# Media Discovery
# ============================================================================

def discover_media(studio_path: Path) -> dict[str, list[Path]]:
  """
  Discover media files on STUDIO volume organized by type

  Returns:
    Dict with 'video' and 'image' keys containing lists of paths
  """
  video_dir = studio_path / "VIDEO"
  image_dir = studio_path / "IMAGES"

  media = {
    "video": [],
    "image": []
  }

  if video_dir.exists():
    media["video"] = sorted([
      f for f in video_dir.iterdir()
      if f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]
    ])

  if image_dir.exists():
    media["image"] = sorted([
      f for f in image_dir.iterdir()
      if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff"]
    ])

  return media

def match_media_to_phase(
  phase: CareerPhase,
  media: dict[str, list[Path]]
) -> list[Path]:
  """
  Match available media files to a career phase

  Returns:
    List of matching media file paths (deduplicated)
  """
  matches = []
  seen = set()

  for pattern in phase.media_files:
    pattern_lower = pattern.lower()

    # Check videos first (preferred)
    for video in media["video"]:
      if pattern_lower in video.name.lower() and video not in seen:
        matches.append(video)
        seen.add(video)

    # Then check images
    for image in media["image"]:
      if pattern_lower in image.name.lower() and image not in seen:
        matches.append(image)
        seen.add(image)

  return matches

# ============================================================================
# Video Production
# ============================================================================

def create_career_video(
  output_path: Optional[Path] = None,
  project_name: str = "Arthur_Dell_Career_Journey"
) -> bool:
  """
  Create the career journey video in DaVinci Resolve

  Args:
    output_path: Where to render the final video
    project_name: Name for the Resolve project

  Returns:
    True if successful
  """
  print("\n" + "=" * 60)
  print("  ARTHUR DELL CAREER JOURNEY VIDEO PRODUCTION")
  print("=" * 60 + "\n")

  # Check STUDIO volume
  studio_path = Path("/Volumes/STUDIO")
  if not studio_path.exists():
    print("ERROR: STUDIO volume not mounted at /Volumes/STUDIO")
    print("Mount with: mount_smbfs //beta/STUDIO /Volumes/STUDIO")
    return False

  # Discover media
  print("Discovering media files...")
  media = discover_media(studio_path)
  print(f"  Found {len(media['video'])} videos")
  print(f"  Found {len(media['image'])} images")

  # Build shot list
  print("\nBuilding shot list from career timeline...")
  shot_list = []
  text_overlays = []
  clip_index = 0

  for phase in CAREER_TIMELINE:
    matches = match_media_to_phase(phase, media)

    if matches:
      print(f"  {phase.company}: {len(matches)} asset(s)")
      for match in matches:
        shot_list.append(match)
        text_overlays.append({
          "clip_index": clip_index,
          "text": phase.text_overlay,
          "company": phase.company
        })
        clip_index += 1
    else:
      print(f"  {phase.company}: No matching assets (skipping)")

  if not shot_list:
    print("\nERROR: No media matched to career phases!")
    return False

  print(f"\nTotal clips for timeline: {len(shot_list)}")

  # Connect to DaVinci Resolve
  print("\nConnecting to DaVinci Resolve Studio...")
  controller = ResolveController()

  try:
    controller.connect()
    print(f"  Connected to Resolve {controller.get_version()}")
  except ResolveError as e:
    print(f"ERROR: {e}")
    print("\nEnsure DaVinci Resolve Studio is running.")
    return False

  # Check if project exists, create if not
  print(f"\nSetting up project: {project_name}")
  existing_projects = controller.list_projects()

  if project_name in existing_projects:
    print(f"  Opening existing project...")
    controller.open_project(project_name)
  else:
    print(f"  Creating new project...")
    controller.create_project(project_name)

  # Import all media
  print("\nImporting media to Media Pool...")
  try:
    imported = controller.import_media(shot_list)
    print(f"  Imported {len(imported)} clips")
  except ResolveError as e:
    print(f"  Warning: {e}")

  # Create timeline
  timeline_name = "Career_Journey_Timeline"
  print(f"\nCreating timeline: {timeline_name}")

  try:
    controller.create_timeline_from_clips(
      name=timeline_name,
      clip_paths=shot_list,
      width=1920,
      height=1080,
      fps=24.0
    )
    print("  Timeline created with all clips")
  except ResolveError as e:
    print(f"ERROR: {e}")
    return False

  # Add text overlays
  print("\nAdding text overlays...")
  for overlay_info in text_overlays:
    try:
      overlay = TextOverlay(
        text=overlay_info["text"],
        position=(0.05, 0.9),  # Upper-left corner (x=5%, y=90% from bottom)
        font="Inter",
        font_size=0.04,
        color=(1.0, 1.0, 1.0)  # White text
      )
      controller.add_text_overlay(overlay, overlay_info["clip_index"])
      print(f"  Added: {overlay_info['text']}")
    except ResolveError as e:
      print(f"  Warning: Could not add overlay for {overlay_info['company']}: {e}")

  # Save project
  print("\nSaving project...")
  try:
    controller.save_project()
    print("  Project saved")
  except Exception as e:
    print(f"  Note: Auto-save may handle this ({e})")

  # Set up render
  if output_path is None:
    output_path = Path.home() / "Movies"

  print(f"\nSetting up render to: {output_path}")
  try:
    controller.render(
      output_path=output_path,
      preset=RenderPreset.YOUTUBE_1080P,
      filename="Arthur_Dell_Career_Journey"
    )
    print("  Render job added to queue")
    print("\n  To render: Go to Deliver page in Resolve and click 'Render All'")
  except ResolveError as e:
    print(f"  Warning: {e}")

  # Summary
  print("\n" + "=" * 60)
  print("  PRODUCTION COMPLETE")
  print("=" * 60)
  print(f"\nProject: {project_name}")
  print(f"Timeline: {timeline_name}")
  print(f"Total clips: {len(shot_list)}")
  print(f"\nNext steps:")
  print("  1. Open DaVinci Resolve")
  print("  2. Review timeline and adjust as needed")
  print("  3. Add transitions between clips")
  print("  4. Fine-tune text overlays in Fusion")
  print("  5. Render from Deliver page")

  controller.close()
  return True

# ============================================================================
# CLI Interface
# ============================================================================

def print_media_mapping():
  """Print the career-to-media mapping for review"""
  studio_path = Path("/Volumes/STUDIO")

  if not studio_path.exists():
    print("STUDIO not mounted")
    return

  media = discover_media(studio_path)

  print("\n" + "=" * 70)
  print("  CAREER TIMELINE TO MEDIA MAPPING")
  print("=" * 70)

  for phase in CAREER_TIMELINE:
    print(f"\n{phase.company} ({phase.years})")
    print(f"  Role: {phase.role}")
    print(f"  Text overlay: '{phase.text_overlay}'")
    print(f"  Patterns: {phase.media_files}")

    matches = match_media_to_phase(phase, media)
    if matches:
      print("  Matched files:")
      for m in matches:
        print(f"    - {m.name}")
    else:
      print("  NO MATCHES FOUND")

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(
    description="Create Arthur Dell career journey video"
  )
  parser.add_argument(
    "--preview",
    action="store_true",
    help="Preview media mapping without creating video"
  )
  parser.add_argument(
    "--output",
    type=Path,
    default=None,
    help="Output directory for rendered video"
  )

  args = parser.parse_args()

  if args.preview:
    print_media_mapping()
  else:
    success = create_career_video(output_path=args.output)
    sys.exit(0 if success else 1)
