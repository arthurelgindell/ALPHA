#!/usr/bin/env python3
"""
Remove audio tracks from the current DaVinci Resolve timeline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.resolve.controller import ResolveController

def main():
  print("Connecting to DaVinci Resolve...")
  resolve = ResolveController()
  resolve.connect()

  # Get current timeline
  timeline = resolve.get_current_timeline()
  if not timeline:
    print("No timeline open!")
    return

  print(f"Timeline: {timeline.GetName()}")

  # Get audio track count
  audio_track_count = timeline.GetTrackCount("audio")
  print(f"Audio tracks found: {audio_track_count}")

  if audio_track_count == 0:
    print("No audio tracks to remove.")
    return

  # Delete items from each audio track
  for track_num in range(1, audio_track_count + 1):
    items = timeline.GetItemListInTrack("audio", track_num)
    if items:
      print(f"  Track {track_num}: {len(items)} items")
      for item in items:
        # Delete the item
        timeline.DeleteClips([item])
        print(f"    Deleted: {item.GetName() if hasattr(item, 'GetName') else 'clip'}")
    else:
      print(f"  Track {track_num}: empty")

  # Try to delete the audio tracks themselves
  # Note: Resolve API may not support track deletion directly
  print("\nAudio items removed. Empty tracks may remain (delete manually if needed).")

  resolve.save_project()
  print("✅ Done!")

if __name__ == "__main__":
  main()
