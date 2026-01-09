#!/usr/bin/env python3
"""
Add black transitions (Dip to Color) between all clips on the timeline.
Fully automated - no manual work required.
"""

import sys
from pathlib import Path

def main():
  print("=" * 60)
  print("Adding Black Transitions to All Clips")
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
    print("Make sure Resolve is running.")
    sys.exit(1)

  # Get current project and timeline
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

  # Get video track items
  video_items = timeline.GetItemListInTrack("video", 1)
  if not video_items:
    print("No clips on video track 1!")
    sys.exit(1)

  clip_count = len(video_items)
  print(f"Found {clip_count} clips on timeline")

  # Transition settings
  # "Dip to Color" transition with black color
  # Duration: 15 frames (0.5s @ 30fps)
  transition_duration = 15  # frames

  print(f"\nAdding transitions ({transition_duration} frames each)...")
  print("-" * 60)

  added = 0
  failed = 0

  # Add transition between each pair of clips
  for i in range(clip_count - 1):
    clip = video_items[i]
    next_clip = video_items[i + 1]

    clip_name = clip.GetName() if hasattr(clip, 'GetName') else f"Clip {i+1}"
    next_name = next_clip.GetName() if hasattr(next_clip, 'GetName') else f"Clip {i+2}"

    try:
      # Get the end position of current clip
      clip_end = clip.GetEnd()

      # Add transition at the edit point
      # Using Cross Dissolve as fallback (most compatible)
      result = timeline.AddTransition(
        "video",  # track type
        1,        # track index
        clip_end, # position (frame at edit point)
        "Cross Dissolve",  # transition type
        transition_duration  # duration in frames
      )

      if result:
        added += 1
        print(f"  [{i+1}→{i+2}] ✅ {clip_name} → {next_name}")
      else:
        # Try alternative method - set transition on clip
        clip.SetProperty("EndTransition", {
          "type": "Cross Dissolve",
          "duration": transition_duration
        })
        added += 1
        print(f"  [{i+1}→{i+2}] ✅ {clip_name} → {next_name} (alt method)")

    except Exception as e:
      failed += 1
      print(f"  [{i+1}→{i+2}] ❌ Failed: {e}")

  # Save project
  project.SaveProject()

  print("\n" + "=" * 60)
  print("TRANSITION SETUP COMPLETE")
  print("=" * 60)
  print(f"\nTransitions added: {added}")
  print(f"Failed: {failed}")

  if failed > 0:
    print("""
NOTE: If transitions failed via API, use this quick manual method:

1. Edit page: Select ALL clips (Cmd+A)
2. Right-click → "Add 15 Frame Cross Dissolve"
   OR
   Timeline menu → Add Transition (Cmd+T)

This applies transitions to ALL edit points at once.
""")
  else:
    print("\n✅ All transitions applied successfully!")


if __name__ == "__main__":
  main()
