#!/usr/bin/env python3
"""
Add text overlays to Episode 1 timeline.
Creates Text+ generators on video track 2 at specified timecodes.
"""

import sys

# Text overlay specifications from storyboard
# Format: (start_frame, duration_frames, text, color_hex, size, position)
# Position: "center" or "lower_third"
TEXT_OVERLAYS = [
  # Shot 1: Title
  (0, 120, "THE FOUNDATION", "#f5f5f5", 0.15, "center"),

  # Shot 4: Mac specs
  (360, 120, "1TB UNIFIED MEMORY", "#d4a373", 0.08, "lower_third"),

  # Shot 5: Mac specs
  (480, 120, "160 GPU CORES COMBINED", "#d4a373", 0.08, "lower_third"),

  # Shot 6: DGX intro
  (600, 120, "NVIDIA DGX SPARK", "#76b900", 0.12, "lower_third"),

  # Shot 8: DGX specs
  (840, 120, "1 PETAFLOP", "#d4a373", 0.12, "center"),

  # Shot 9: DGX specs
  (960, 120, "128GB UNIFIED", "#d4a373", 0.08, "lower_third"),

  # Shot 10: DGX specs
  (1080, 120, "DESKTOP SIZE", "#f5f5f5", 0.08, "lower_third"),

  # Shot 11: Duo reveal
  (1200, 120, "THE POWER DUO", "#f5f5f5", 0.15, "center"),

  # Shot 13: Combined power
  (1440, 120, "1.5+ PETAFLOPS LOCAL", "#d4a373", 0.08, "center"),

  # Shot 14: Value prop
  (1560, 120, "NO CLOUD. NO API COSTS.", "#f5f5f5", 0.08, "center"),

  # Shot 15: CTA
  (1680, 120, "FULL CONTROL → FOLLOW", "#4ecdc4", 0.08, "center"),
]


def hex_to_rgb(hex_color):
  """Convert hex color to RGB tuple (0-1 range)"""
  hex_color = hex_color.lstrip('#')
  r = int(hex_color[0:2], 16) / 255.0
  g = int(hex_color[2:4], 16) / 255.0
  b = int(hex_color[4:6], 16) / 255.0
  return (r, g, b)


def main():
  print("=" * 60)
  print("Adding Text Overlays to Timeline")
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

  # Ensure we have video track 2 for text overlays
  track_count = timeline.GetTrackCount("video")
  if track_count < 2:
    print("Adding video track 2 for text overlays...")
    timeline.AddTrack("video")

  print(f"\nAdding {len(TEXT_OVERLAYS)} text overlays...")
  print("-" * 60)

  added = 0
  failed = 0

  for i, (start_frame, duration, text, color, size, position) in enumerate(TEXT_OVERLAYS):
    try:
      # Create a Fusion Title (Text+) generator
      # Method: Add to media pool then insert to timeline

      # Get the generators bin or create one
      root_folder = media_pool.GetRootFolder()

      # Create generator clip info
      generator_name = f"Text_{i+1}_{text[:15].replace(' ', '_')}"

      # Add Text+ generator to timeline at specific position
      # Using timeline.InsertGeneratorIntoTimeline
      result = timeline.InsertGeneratorIntoTimeline("Text+")

      if result:
        # Get the newly added clip (should be last on track)
        video_items = timeline.GetItemListInTrack("video", 2)
        if video_items:
          new_clip = video_items[-1]

          # Set clip properties
          new_clip.SetProperty("Start", start_frame)
          new_clip.SetProperty("Duration", duration)

          # Access Fusion comp to set text properties
          fusion_comp = new_clip.GetFusionCompByIndex(1)
          if fusion_comp:
            # Find the Text+ tool and configure it
            tools = fusion_comp.GetToolList()
            for tool_name, tool in tools.items():
              if "Text" in tool_name:
                # Set text content
                tool.SetInput("StyledText", text)

                # Set color
                r, g, b = hex_to_rgb(color)
                tool.SetInput("Red1", r)
                tool.SetInput("Green1", g)
                tool.SetInput("Blue1", b)

                # Set size
                tool.SetInput("Size", size)

                # Set position
                if position == "center":
                  tool.SetInput("Center", {"X": 0.5, "Y": 0.5})
                else:  # lower_third
                  tool.SetInput("Center", {"X": 0.5, "Y": 0.15})

                # Set font
                tool.SetInput("Font", "Inter")

                break

          added += 1
          print(f"  [{i+1:2d}] ✅ \"{text}\" @ frame {start_frame}")
        else:
          failed += 1
          print(f"  [{i+1:2d}] ❌ \"{text}\" - clip not found after insert")
      else:
        failed += 1
        print(f"  [{i+1:2d}] ❌ \"{text}\" - generator insert failed")

    except Exception as e:
      failed += 1
      print(f"  [{i+1:2d}] ❌ \"{text}\" - {e}")

  # Try to save
  try:
    project.SaveProject()
  except:
    pass

  print("\n" + "=" * 60)
  print("TEXT OVERLAY SETUP COMPLETE")
  print("=" * 60)
  print(f"\nAdded: {added}")
  print(f"Failed: {failed}")

  if failed > 0:
    print("""
NOTE: Text+ generators may need manual positioning.
Alternative: Use Titles from Effects Library → Toolbox → Titles
""")


if __name__ == "__main__":
  main()
