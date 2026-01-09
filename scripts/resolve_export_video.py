#!/usr/bin/env python3
"""
Export Episode 1 video from DaVinci Resolve.
Format: 1080x1920 (9:16 vertical), H.264, 30fps
"""

import sys
from pathlib import Path
from datetime import datetime


def main():
    print("=" * 60)
    print("Exporting Episode 1 Video")
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

    # Export settings
    export_dir = Path("/Volumes/STUDIO/VIDEO/linkedin_series/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"EP01_Hardware_Foundation_{timestamp}"
    export_path = export_dir / f"{export_filename}.mp4"

    print(f"\nExport path: {export_path}")
    print("-" * 60)

    # Set up render job
    project.SetCurrentRenderMode(0)  # Individual clips mode = 0, Single clip = 1

    # Get the render preset or set custom settings
    render_settings = {
        "SelectAllFrames": True,
        "TargetDir": str(export_dir),
        "CustomName": export_filename,
        "ExportVideo": True,
        "ExportAudio": False,  # No audio in this video
        "FormatWidth": 1080,
        "FormatHeight": 1920,
        "FrameRate": "30",
        # H.264 settings
        "VideoCodec": "h264_main",
        "VideoBitrate": "20000",  # 20 Mbps for high quality
        "AudioCodec": "",
    }

    print("Render settings:")
    for key, value in render_settings.items():
        print(f"  {key}: {value}")

    # Apply render settings
    project.SetRenderSettings(render_settings)

    # Add render job to queue
    print("\nAdding render job to queue...")
    job_id = project.AddRenderJob()

    if not job_id:
        print("❌ Failed to add render job")
        print("\nTry manual export:")
        print("1. File → Deliver page")
        print("2. Select 'YouTube' preset (or custom 1080x1920)")
        print("3. Click 'Add to Render Queue'")
        print("4. Click 'Render All'")
        sys.exit(1)

    print(f"✅ Render job added: {job_id}")

    # Start render
    print("\nStarting render...")
    project.StartRendering([job_id])

    # Wait for render to complete
    print("Rendering in progress...")

    import time
    while project.IsRenderingInProgress():
        # Get progress
        status = project.GetRenderJobStatus(job_id)
        if status:
            progress = status.get("CompletionPercentage", 0)
            print(f"  Progress: {progress}%", end="\r")
        time.sleep(1)

    print("\n")

    # Check result
    status = project.GetRenderJobStatus(job_id)
    if status and status.get("JobStatus") == "Complete":
        print("=" * 60)
        print("EXPORT COMPLETE")
        print("=" * 60)
        print(f"\n✅ Video exported to: {export_path}")

        # Get file size
        if export_path.exists():
            size_mb = export_path.stat().st_size / (1024 * 1024)
            print(f"   File size: {size_mb:.1f} MB")
    else:
        print("=" * 60)
        print("EXPORT STATUS")
        print("=" * 60)
        print(f"\nRender job status: {status}")
        print(f"\nCheck Resolve's Deliver page for details.")


if __name__ == "__main__":
    main()
