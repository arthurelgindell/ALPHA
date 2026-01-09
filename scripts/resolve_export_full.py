#!/usr/bin/env python3
"""
Export full timeline from DaVinci Resolve with proper settings.
"""

import sys
import time
from pathlib import Path
from datetime import datetime


def main():
    print("=" * 60)
    print("Full Timeline Export")
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

    print(f"\nProject: {project.GetName()}")
    print(f"Timeline: {timeline.GetName()}")

    # Get timeline info
    fps = timeline.GetSetting("timelineFrameRate")
    duration = timeline.GetEndFrame() - timeline.GetStartFrame()
    print(f"Duration: {duration} frames @ {fps} fps")

    # Export settings
    export_dir = Path("/Volumes/STUDIO/VIDEO/linkedin_series/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"EP01_Hardware_{timestamp}"

    print(f"\nExport directory: {export_dir}")
    print(f"Filename: {export_filename}.mp4")
    print("-" * 60)

    # Delete any existing render jobs
    project.DeleteAllRenderJobs()
    print("Cleared existing render jobs")

    # Load YouTube preset (good for LinkedIn vertical)
    presets = project.GetRenderPresetList()
    print(f"Available presets: {presets}")

    # Set render format to H.264
    # Use SetRenderSettings with the correct parameters
    render_settings = {
        "SelectAllFrames": 1,
        "MarkIn": timeline.GetStartFrame(),
        "MarkOut": timeline.GetEndFrame(),
        "TargetDir": str(export_dir),
        "CustomName": export_filename,
        "UniqueFilenameStyle": 0,  # Don't add frame numbers
        "ExportVideo": True,
        "ExportAudio": True,  # Include audio track even if empty
        "FormatWidth": 1080,
        "FormatHeight": 1920,
        "FrameRate": str(fps) if fps else "30",
    }

    print("\nApplying render settings...")
    result = project.SetRenderSettings(render_settings)
    print(f"SetRenderSettings result: {result}")

    # Load a preset that works well
    # Try to use H.264 Master preset
    preset_loaded = project.LoadRenderPreset("H.264 Master")
    if not preset_loaded:
        preset_loaded = project.LoadRenderPreset("YouTube - 1080p")
    print(f"Preset loaded: {preset_loaded}")

    # Re-apply our custom settings after loading preset
    project.SetRenderSettings({
        "TargetDir": str(export_dir),
        "CustomName": export_filename,
        "FormatWidth": 1080,
        "FormatHeight": 1920,
    })

    # Add render job
    print("\nAdding render job...")
    job_id = project.AddRenderJob()

    if not job_id:
        print("❌ Failed to add render job via API")
        print("\nPlease export manually from Deliver page:")
        print("1. Ensure 'Entire Timeline' is selected")
        print("2. Set Format: MP4, Codec: H.264")
        print("3. Resolution: 1080x1920")
        print("4. Click 'Add to Render Queue' then 'Render All'")
        sys.exit(1)

    print(f"✅ Render job added: {job_id}")

    # Start render
    print("\nStarting render...")
    render_started = project.StartRendering([job_id])
    print(f"Render started: {render_started}")

    # Monitor progress
    print("\nRendering...")
    last_progress = -1
    while project.IsRenderingInProgress():
        status = project.GetRenderJobStatus(job_id)
        if status:
            progress = status.get("CompletionPercentage", 0)
            if progress != last_progress:
                print(f"  Progress: {progress}%")
                last_progress = progress
        time.sleep(0.5)

    # Final status
    status = project.GetRenderJobStatus(job_id)
    print(f"\nFinal status: {status}")

    # Find the exported file
    print("\nLooking for exported file...")
    for f in export_dir.glob(f"{export_filename}*"):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  Found: {f.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
