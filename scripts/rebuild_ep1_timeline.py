#!/usr/bin/env python3
"""
Rebuild Episode 1 timeline from scratch with correct assets.
- Proper Pillow infographics (readable text)
- Official stock photos only
- No AI-generated comparison images
"""

import sys
from pathlib import Path

# Asset paths
ASSETS_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets")
INFOGRAPHICS_DIR = ASSETS_DIR / "infographics_v2"
APPLE_DIR = ASSETS_DIR / "apple"
NVIDIA_DIR = ASSETS_DIR / "nvidia"
TEXT_DIR = ASSETS_DIR / "text_overlays"

# Shot list - using ONLY proper assets
# Format: (filename, directory, duration_frames)
SHOTS = [
    # Opening
    ("title_card.png", INFOGRAPHICS_DIR, 120),              # 0:00-0:04 THE FOUNDATION

    # Mac Studio section
    ("mac_studio_hero_4k.jpg", APPLE_DIR, 120),             # 0:04-0:08 Hero shot
    ("mac_studio_ports_4k.jpg", APPLE_DIR, 120),            # 0:08-0:12 Ports
    ("mac_studio_spec_card.png", INFOGRAPHICS_DIR, 120),    # 0:12-0:16 Specs
    ("mac_studio_lifestyle_4k.jpg", APPLE_DIR, 120),        # 0:16-0:20 Lifestyle

    # DGX Spark section
    ("dgx_product_1.jpg", NVIDIA_DIR, 120),                 # 0:20-0:24 DGX Hero
    ("dgx_product_2.jpg", NVIDIA_DIR, 120),                 # 0:24-0:28 DGX angle
    ("dgx_spark_spec_card.png", INFOGRAPHICS_DIR, 120),     # 0:28-0:32 DGX Specs
    ("dgx_product_3.jpg", NVIDIA_DIR, 120),                 # 0:32-0:36 DGX detail

    # Combined section
    ("power_duo_comparison.png", INFOGRAPHICS_DIR, 120),    # 0:36-0:40 Comparison
    ("mac_studio_setup_4k.jpg", APPLE_DIR, 120),            # 0:40-0:44 Setup shot
    ("dgx_product_4.jpg", NVIDIA_DIR, 120),                 # 0:44-0:48 DGX final

    # Closing
    ("cta_card.png", INFOGRAPHICS_DIR, 120),                # 0:48-0:52 CTA
]

# Text overlays for track 2 - only on product shots (infographics have built-in text)
TEXT_OVERLAYS = [
    # (text_file, start_frame)
    ("02_1tb_memory.png", 120),       # On mac_studio_hero
    ("03_160_cores.png", 240),        # On mac_studio_ports
    ("04_dgx_spark.png", 600),        # On dgx_product_1
    ("06_128gb.png", 840),            # On dgx_product_2
    ("07_desktop_size.png", 960),     # On dgx_product_3
]


def main():
    print("=" * 60)
    print("Rebuilding Episode 1 Timeline")
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

    # Create new project
    project_name = "LinkedIn_EP01_Hardware_v2"
    project = project_manager.CreateProject(project_name)

    if not project:
        # Project might exist, try to load it
        project = project_manager.LoadProject(project_name)
        if not project:
            print(f"Could not create or load project: {project_name}")
            sys.exit(1)

    print(f"\nProject: {project.GetName()}")

    # Set project settings for 9:16 vertical
    project.SetSetting("timelineResolutionWidth", "1080")
    project.SetSetting("timelineResolutionHeight", "1920")
    project.SetSetting("timelineFrameRate", "30")

    media_pool = project.GetMediaPool()

    # Clear existing timelines
    for i in range(project.GetTimelineCount()):
        tl = project.GetTimelineByIndex(i + 1)
        if tl:
            media_pool.DeleteTimelines([tl])

    # Create new timeline
    timeline = media_pool.CreateEmptyTimeline("EP01_Hardware_Final")
    if not timeline:
        print("Failed to create timeline!")
        sys.exit(1)

    project.SetCurrentTimeline(timeline)
    print(f"Timeline: {timeline.GetName()}")

    # Import all shot files
    print(f"\nImporting {len(SHOTS)} shots...")
    print("-" * 60)

    shot_files = []
    for filename, directory, _ in SHOTS:
        filepath = directory / filename
        if filepath.exists():
            shot_files.append(str(filepath))
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ MISSING: {filepath}")

    # Import to media pool
    root_folder = media_pool.GetRootFolder()
    media_pool.SetCurrentFolder(root_folder)

    imported = media_pool.ImportMedia(shot_files)
    if not imported:
        print("Failed to import media!")
        sys.exit(1)

    print(f"\nImported {len(imported)} clips to media pool")

    # Create filename to clip mapping
    clip_map = {}
    for clip in imported:
        name = clip.GetName()
        clip_map[name] = clip

    # Add shots to timeline in order
    print(f"\nAdding shots to timeline...")
    print("-" * 60)

    for i, (filename, directory, duration) in enumerate(SHOTS):
        # Find clip by name (without extension for some)
        clip = None
        for name, c in clip_map.items():
            if filename in name or filename.replace(".png", "") in name or filename.replace(".jpg", "") in name:
                clip = c
                break

        if not clip:
            print(f"  [{i+1:2d}] ✗ {filename} - not found")
            continue

        # Set still image duration
        clip.SetClipProperty("End", duration)

        # Add to timeline
        clip_info = {
            "mediaPoolItem": clip,
            "startFrame": 0,
            "endFrame": duration,
        }

        result = media_pool.AppendToTimeline([clip_info])
        if result:
            print(f"  [{i+1:2d}] ✓ {filename} ({duration} frames)")
        else:
            print(f"  [{i+1:2d}] ✗ {filename} - append failed")

    # Add text overlays to track 2
    print(f"\nAdding text overlays...")
    print("-" * 60)

    # Import text overlay files
    text_files = [str(TEXT_DIR / f) for f, _ in TEXT_OVERLAYS if (TEXT_DIR / f).exists()]
    if text_files:
        text_clips = media_pool.ImportMedia(text_files)
        if text_clips:
            print(f"Imported {len(text_clips)} text overlays")

            # Ensure track 2 exists
            while timeline.GetTrackCount("video") < 2:
                timeline.AddTrack("video")

            # Add each to track 2 at correct position
            for clip in text_clips:
                name = clip.GetName()
                # Find position
                for text_file, start_frame in TEXT_OVERLAYS:
                    if text_file.replace(".png", "") in name:
                        clip_info = {
                            "mediaPoolItem": clip,
                            "startFrame": 0,
                            "endFrame": 120,
                            "trackIndex": 2,
                            "recordFrame": start_frame,
                        }
                        media_pool.AppendToTimeline([clip_info])
                        print(f"  ✓ {name} @ frame {start_frame}")
                        break

    # Save project
    try:
        project.SaveProject()
    except:
        pass

    print("\n" + "=" * 60)
    print("TIMELINE REBUILT")
    print("=" * 60)
    print(f"\nProject: {project.GetName()}")
    print(f"Timeline: {timeline.GetName()}")
    print(f"Shots: {len(SHOTS)}")
    print(f"Duration: {sum(d for _, _, d in SHOTS)} frames ({sum(d for _, _, d in SHOTS) // 30}s)")
    print("\nNext: Add transitions and export")


if __name__ == "__main__":
    main()
