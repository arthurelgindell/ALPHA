#!/usr/bin/env python3
"""
Import text overlay PNGs to DaVinci Resolve timeline track 2.
"""

import sys
from pathlib import Path

# Text overlays with their timeline positions (in frames @ 30fps)
# (filename, start_frame, duration_frames)
OVERLAY_POSITIONS = [
    ("01_the_foundation.png", 0, 120),        # Shot 1: 0:00-0:04
    ("02_1tb_memory.png", 360, 120),          # Shot 4: 0:12-0:16
    ("03_160_cores.png", 480, 120),           # Shot 5: 0:16-0:20
    ("04_dgx_spark.png", 600, 120),           # Shot 6: 0:20-0:24
    ("05_1_petaflop.png", 840, 120),          # Shot 8: 0:28-0:32
    ("06_128gb.png", 960, 120),               # Shot 9: 0:32-0:36
    ("07_desktop_size.png", 1080, 120),       # Shot 10: 0:36-0:40
    ("08_power_duo.png", 1200, 120),          # Shot 11: 0:40-0:44
    ("09_petaflops.png", 1440, 120),          # Shot 13: 0:48-0:52
    ("10_no_cloud.png", 1560, 120),           # Shot 14: 0:52-0:56
    ("11_cta.png", 1680, 120),                # Shot 15: 0:56-1:00
]

OVERLAY_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets/text_overlays")


def main():
    print("=" * 60)
    print("Importing Text Overlays to Timeline")
    print("=" * 60)

    # Connect to Resolve
    try:
        sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp("Resolve")
    except Exception as e:
        print(f"Error connecting to Resolve: {e}")
        sys.exit(1)

    if not resolve:
        print("Could not connect to DaVinci Resolve!")
        sys.exit(1)

    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()

    if not project:
        print("No project open!")
        sys.exit(1)

    timeline = project.GetCurrentTimeline()
    if not timeline:
        print("No timeline open!")
        sys.exit(1)

    media_pool = project.GetMediaPool()

    print(f"\nProject: {project.GetName()}")
    print(f"Timeline: {timeline.GetName()}")
    print(f"Source: {OVERLAY_DIR}")

    # Ensure we have video track 2
    track_count = timeline.GetTrackCount("video")
    while track_count < 2:
        print("Adding video track...")
        timeline.AddTrack("video")
        track_count = timeline.GetTrackCount("video")

    # Get or create a bin for text overlays
    root_folder = media_pool.GetRootFolder()

    # Find or create "Text Overlays" bin
    subfolders = root_folder.GetSubFolderList()
    text_bin = None
    for folder in subfolders:
        if folder.GetName() == "Text Overlays":
            text_bin = folder
            break

    if not text_bin:
        text_bin = media_pool.AddSubFolder(root_folder, "Text Overlays")
        print("Created 'Text Overlays' bin")

    media_pool.SetCurrentFolder(text_bin)

    # Import all overlay PNGs
    print(f"\nImporting {len(OVERLAY_POSITIONS)} text overlay files...")
    print("-" * 60)

    overlay_files = [str(OVERLAY_DIR / filename) for filename, _, _ in OVERLAY_POSITIONS]
    imported = media_pool.ImportMedia(overlay_files)

    if not imported:
        print("❌ Failed to import media files")
        sys.exit(1)

    print(f"Imported {len(imported)} files to media pool")

    # Create a mapping of filename to media pool item
    clip_map = {}
    for clip in imported:
        clip_name = clip.GetName()
        clip_map[clip_name] = clip

    # Add each overlay to timeline at correct position
    print(f"\nAdding overlays to video track 2...")
    print("-" * 60)

    added = 0
    failed = 0

    for filename, start_frame, duration in OVERLAY_POSITIONS:
        clip_name = filename.replace(".png", "")

        # Find the clip in our imported items
        clip = None
        for name, c in clip_map.items():
            if clip_name in name or filename in name:
                clip = c
                break

        if not clip:
            print(f"  ❌ {filename} - not found in media pool")
            failed += 1
            continue

        try:
            # Create clip info for AppendToTimeline
            clip_info = {
                "mediaPoolItem": clip,
                "startFrame": 0,
                "endFrame": duration,
                "trackIndex": 2,
                "recordFrame": start_frame,
            }

            # Append to timeline
            result = media_pool.AppendToTimeline([clip_info])

            if result:
                added += 1
                print(f"  ✅ {filename} @ frame {start_frame}")
            else:
                failed += 1
                print(f"  ❌ {filename} - append failed")

        except Exception as e:
            failed += 1
            print(f"  ❌ {filename} - {e}")

    # Save project
    try:
        project.SaveProject()
    except:
        pass

    print("\n" + "=" * 60)
    print("TEXT OVERLAY IMPORT COMPLETE")
    print("=" * 60)
    print(f"\nAdded: {added}")
    print(f"Failed: {failed}")

    if added > 0:
        print("\n✅ Text overlays added to video track 2")
        print("   They will composite over the video clips automatically.")


if __name__ == "__main__":
    main()
