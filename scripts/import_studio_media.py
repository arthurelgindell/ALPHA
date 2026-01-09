#!/usr/bin/env python3
"""
Import media from /Volumes/STUDIO into LanceDB with filename-based metadata extraction.

Parses descriptive filenames to extract:
- Subject tags (company names, product names)
- Content type (carousel, storyboard, hero, etc.)
- Episode assignments (ep1, ep2, etc.)
- Generation source (wan26, veo, press_kit, etc.)
"""

import re
import sys
from pathlib import Path

# Add arthur module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.media_db import MediaDatabase


def parse_filename_metadata(filepath: Path) -> dict:
  """Extract metadata from filename patterns."""
  filename = filepath.stem.lower()
  parent_dir = filepath.parent.name.lower()
  grandparent_dir = filepath.parent.parent.name.lower() if filepath.parent.parent else ""

  metadata = {
    "subjects": [],
    "style_tags": [],
    "content_type": None,
    "source": "studio",
    "generation_model": None,
    "episode_assignments": []
  }

  # Press kit detection
  if grandparent_dir == "press_kit" or parent_dir == "press_kit":
    metadata["source"] = "press_kit"
    if parent_dir in ["dgx_spark", "mac_studio"]:
      metadata["subjects"].append(parent_dir)
      metadata["content_type"] = "product_hero"

  # Company/brand detection
  companies = {
    "acsa": "acsa",
    "bmw": "bmw",
    "bsi": "bsi",
    "citrix": "citrix",
    "hp": "hp",
    "ibm": "ibm",
    "sun": "sun_microsystems",
    "symantec": "symantec",
  }
  for key, subject in companies.items():
    if key in filename:
      metadata["subjects"].append(subject)

  # Product detection
  products = ["mac_studio", "dgx_spark", "dgx spark", "macstudio"]
  for product in products:
    if product.replace("_", " ") in filename or product in filename:
      clean_product = product.replace(" ", "_")
      if clean_product not in metadata["subjects"]:
        metadata["subjects"].append(clean_product)

  # AI-generated content
  if filename.startswith("ai ") or filename.startswith("ai_"):
    metadata["style_tags"].append("ai_generated")
    metadata["subjects"].append("ai_concept")

  # Content type detection
  if "carousel" in filename or "carousel_slide" in filename:
    metadata["content_type"] = "carousel"
  elif "storyboard" in filename:
    metadata["content_type"] = "storyboard"
  elif "hero" in filename:
    metadata["content_type"] = "hero"
  elif "profile" in filename or "headshot" in filename:
    metadata["content_type"] = "profile"
  elif "brand" in filename:
    metadata["content_type"] = "brand"
  elif "dashboard" in filename:
    metadata["content_type"] = "dashboard"
  elif "datacenter" in filename or "data_center" in filename:
    metadata["content_type"] = "datacenter"
    metadata["subjects"].append("datacenter")
  elif "office" in filename or "workspace" in filename:
    metadata["content_type"] = "workspace"
  elif "boardroom" in filename:
    metadata["content_type"] = "boardroom"

  # Generation source detection
  if "wan26" in filename:
    metadata["source"] = "wan26_api"
    metadata["generation_model"] = "wan2.6"
  elif "veo" in filename:
    metadata["source"] = "veo"
    metadata["generation_model"] = "veo3.1"
  elif "gemini" in filename:
    metadata["source"] = "gemini"
    metadata["style_tags"].append("ai_generated")

  # Episode detection (ep1, ep2, ep3, ep4, etc.)
  ep_match = re.search(r'ep(\d+)', filename)
  if ep_match:
    ep_num = int(ep_match.group(1))
    if 1 <= ep_num <= 8:
      metadata["episode_assignments"].append(ep_num)

  # Style tags from filename
  style_keywords = {
    "cinematic": "cinematic",
    "hero": "hero_shot",
    "premium": "premium",
    "professional": "professional",
    "neural": "neural_network",
    "holographic": "futuristic",
    "robot": "robotics",
    "humanoid": "robotics",
  }
  for keyword, tag in style_keywords.items():
    if keyword in filename and tag not in metadata["style_tags"]:
      metadata["style_tags"].append(tag)

  # Scene numbers from filename (scene1, scene3, etc.)
  scene_match = re.search(r'scene(\d+)', filename)
  if scene_match:
    metadata["style_tags"].append(f"scene_{scene_match.group(1)}")

  return metadata


def import_studio_media(dry_run: bool = False):
  """Import all media from /Volumes/STUDIO into database."""

  studio_path = Path("/Volumes/STUDIO")
  if not studio_path.exists():
    print("ERROR: /Volumes/STUDIO not mounted")
    return

  # Initialize database
  print("Initializing database...")
  db = MediaDatabase()

  # Get existing filenames to avoid duplicates
  existing = set()
  try:
    df = db.assets_table.search().limit(10000).to_pandas()
    existing = set(df['filename'].tolist())
    print(f"Found {len(existing)} existing assets in database")
  except Exception as e:
    print(f"Note: Could not check existing assets: {e}")

  # Collect files to import
  image_extensions = {'.png', '.jpg', '.jpeg', '.webp'}
  video_extensions = {'.mp4', '.mov', '.webm'}

  images_to_import = []
  videos_to_import = []

  # Scan IMAGES directory
  images_dir = studio_path / "IMAGES"
  if images_dir.exists():
    for f in images_dir.rglob("*"):
      if f.is_file() and f.suffix.lower() in image_extensions:
        if f.name not in existing:
          images_to_import.append(f)
        else:
          print(f"  Skip (exists): {f.name}")

  # Scan VIDEO directory
  video_dir = studio_path / "VIDEO"
  if video_dir.exists():
    for f in video_dir.rglob("*"):
      if f.is_file() and f.suffix.lower() in video_extensions:
        if f.name not in existing:
          videos_to_import.append(f)
        else:
          print(f"  Skip (exists): {f.name}")

  print(f"\nFound {len(images_to_import)} new images to import")
  print(f"Found {len(videos_to_import)} new videos to import")

  if dry_run:
    print("\n=== DRY RUN - No changes made ===")
    print("\nImages:")
    for f in images_to_import[:10]:
      meta = parse_filename_metadata(f)
      print(f"  {f.name}")
      print(f"    subjects: {meta['subjects']}, source: {meta['source']}, type: {meta['content_type']}")
    if len(images_to_import) > 10:
      print(f"  ... and {len(images_to_import) - 10} more")

    print("\nVideos:")
    for f in videos_to_import[:10]:
      meta = parse_filename_metadata(f)
      print(f"  {f.name}")
      print(f"    subjects: {meta['subjects']}, source: {meta['source']}, episodes: {meta['episode_assignments']}")
    if len(videos_to_import) > 10:
      print(f"  ... and {len(videos_to_import) - 10} more")
    return

  # Import images
  print("\n=== Importing Images ===")
  imported_images = 0
  for f in images_to_import:
    try:
      meta = parse_filename_metadata(f)
      asset_id = db.add_image(
        str(f),
        source=meta["source"],
        content_type=meta["content_type"],
        subjects=meta["subjects"] if meta["subjects"] else None,
        style_tags=meta["style_tags"] if meta["style_tags"] else None,
        episode_assignments=meta["episode_assignments"] if meta["episode_assignments"] else None
      )
      imported_images += 1
      print(f"  ✓ {f.name} → {asset_id[:8]}...")
    except Exception as e:
      print(f"  ✗ {f.name}: {e}")

  # Import videos
  print("\n=== Importing Videos ===")
  imported_videos = 0
  for f in videos_to_import:
    try:
      meta = parse_filename_metadata(f)
      asset_id = db.add_video(
        str(f),
        source=meta["source"],
        generation_model=meta["generation_model"],
        content_type=meta["content_type"],
        subjects=meta["subjects"] if meta["subjects"] else None,
        style_tags=meta["style_tags"] if meta["style_tags"] else None,
        episode_assignments=meta["episode_assignments"] if meta["episode_assignments"] else None
      )
      imported_videos += 1
      print(f"  ✓ {f.name} → {asset_id[:8]}...")
    except Exception as e:
      print(f"  ✗ {f.name}: {e}")

  # Summary
  print("\n" + "=" * 50)
  print("IMPORT COMPLETE")
  print("=" * 50)
  print(f"Images imported: {imported_images}")
  print(f"Videos imported: {imported_videos}")
  print(f"Total new assets: {imported_images + imported_videos}")

  # Show updated stats
  stats = db.stats()
  print(f"\nDatabase now contains:")
  print(f"  Total assets: {stats['total_assets']}")
  print(f"  Images: {stats['images']}")
  print(f"  Videos: {stats['videos']}")
  print(f"  Total size: {stats['total_size_mb']:.1f} MB")


if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description="Import STUDIO media into LanceDB")
  parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without making changes")
  args = parser.parse_args()

  import_studio_media(dry_run=args.dry_run)
