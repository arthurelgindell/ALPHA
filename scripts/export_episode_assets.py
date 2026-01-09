#!/usr/bin/env python3
"""
Export Episode assets from LanceDB to DaVinci Resolve working folder.

Usage:
  python scripts/export_episode_assets.py --episode 1
  python scripts/export_episode_assets.py --episode 1 --output /path/to/folder
"""

import argparse
import requests
from pathlib import Path
import sys

API_BASE = "http://localhost:8422"
DEFAULT_OUTPUT = Path("/Users/arthurdell/ARTHUR/resolve_projects")


def export_episode_assets(episode: int, output_dir: Path) -> list[Path]:
  """Export all assets for an episode from LanceDB."""

  episode_dir = output_dir / f"ep{episode}_hardware"
  episode_dir.mkdir(parents=True, exist_ok=True)

  print(f"Exporting Episode {episode} assets to: {episode_dir}")
  print("=" * 60)

  # Collect all asset IDs (deduplicated)
  all_assets = {}

  # Get episode-tagged assets
  print(f"\nFetching Episode {episode} tagged assets...")
  r = requests.get(f"{API_BASE}/search/episode/{episode}")
  if r.status_code == 200:
    for asset in r.json()["assets"]:
      all_assets[asset["id"]] = asset
    print(f"  Found {len(r.json()['assets'])} episode-tagged assets")

  # Episode 1 specific: Mac Studio + DGX Spark
  if episode == 1:
    print("\nFetching Mac Studio assets...")
    r = requests.get(f"{API_BASE}/search/subject/mac_studio")
    if r.status_code == 200:
      for asset in r.json()["assets"]:
        all_assets[asset["id"]] = asset
      print(f"  Found {len(r.json()['assets'])} Mac Studio assets")

    print("\nFetching DGX Spark assets...")
    r = requests.get(f"{API_BASE}/search/subject/dgx_spark")
    if r.status_code == 200:
      for asset in r.json()["assets"]:
        all_assets[asset["id"]] = asset
      print(f"  Found {len(r.json()['assets'])} DGX Spark assets")

  print(f"\nTotal unique assets to export: {len(all_assets)}")
  print("-" * 60)

  exported_paths = []
  for asset_id, asset in all_assets.items():
    filename = asset["filename"]
    media_type = asset["media_type"]
    output_path = episode_dir / filename

    # Skip if already exported
    if output_path.exists():
      print(f"  [skip] {filename} (already exists)")
      exported_paths.append(output_path)
      continue

    # Download content
    print(f"  [{media_type}] {filename}...", end=" ", flush=True)
    try:
      content_r = requests.get(f"{API_BASE}/asset/{asset_id}/content")
      if content_r.status_code == 200:
        output_path.write_bytes(content_r.content)
        size_mb = len(content_r.content) / (1024 * 1024)
        print(f"OK ({size_mb:.2f} MB)")
        exported_paths.append(output_path)
      else:
        print(f"FAILED (HTTP {content_r.status_code})")
    except Exception as e:
      print(f"ERROR: {e}")

  print("-" * 60)
  print(f"\nExported {len(exported_paths)} assets to: {episode_dir}")

  # List exported files
  print("\nExported files:")
  images = [p for p in exported_paths if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
  videos = [p for p in exported_paths if p.suffix.lower() in ['.mp4', '.mov', '.webm']]

  print(f"\n  Images ({len(images)}):")
  for p in sorted(images):
    print(f"    {p.name}")

  print(f"\n  Videos ({len(videos)}):")
  for p in sorted(videos):
    print(f"    {p.name}")

  return exported_paths


def main():
  parser = argparse.ArgumentParser(description="Export episode assets from LanceDB")
  parser.add_argument("--episode", "-e", type=int, required=True, help="Episode number (1-8)")
  parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output directory")
  args = parser.parse_args()

  if not 1 <= args.episode <= 8:
    print("Error: Episode must be between 1 and 8")
    sys.exit(1)

  # Check API is running
  try:
    r = requests.get(f"{API_BASE}/health", timeout=5)
    if r.status_code != 200:
      print(f"Error: Media API not healthy (status {r.status_code})")
      sys.exit(1)
  except requests.exceptions.RequestException as e:
    print(f"Error: Cannot connect to Media API at {API_BASE}")
    print(f"  Make sure media_api.py is running: python -m arthur.media_api")
    sys.exit(1)

  export_episode_assets(args.episode, args.output)


if __name__ == "__main__":
  main()
