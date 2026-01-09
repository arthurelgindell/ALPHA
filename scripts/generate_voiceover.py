#!/usr/bin/env python3
"""
Generate Voiceover Narration
Uses F5-TTS-MLX on BETA for high-quality voice synthesis.

Usage:
  python scripts/generate_voiceover.py "Your text here" -o output.wav
  python scripts/generate_voiceover.py --segments segments.txt -o output_dir/
  python scripts/generate_voiceover.py --check
"""

import sys
import argparse
from pathlib import Path

# Add arthur package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.generators.voice import VoiceGenerator, mux_audio


def main():
  parser = argparse.ArgumentParser(
    description="Generate voiceover narration using F5-TTS on BETA"
  )

  # Input options
  parser.add_argument("text", nargs="?", help="Text to convert to speech")
  parser.add_argument(
    "--segments", "-s",
    type=Path,
    help="File with text segments (one per line)"
  )

  # Output options
  parser.add_argument(
    "--output", "-o",
    type=Path,
    default=Path("voiceover.wav"),
    help="Output file path (or directory for segments)"
  )

  # Muxing options
  parser.add_argument(
    "--mux-video",
    type=Path,
    help="Video file to combine with generated audio"
  )
  parser.add_argument(
    "--mux-output",
    type=Path,
    help="Output path for muxed video (default: video_with_audio.mp4)"
  )

  # Other options
  parser.add_argument(
    "--check",
    action="store_true",
    help="Check BETA connection and exit"
  )
  parser.add_argument(
    "--prefix",
    default="narration",
    help="Filename prefix for segments (default: narration)"
  )

  args = parser.parse_args()

  # Initialize generator
  gen = VoiceGenerator()

  # Check connection mode
  if args.check:
    print("Checking BETA connection...")
    if gen.check_connection():
      print("BETA is reachable")
      sys.exit(0)
    else:
      print("BETA is not reachable")
      sys.exit(1)

  # Validate input
  if not args.text and not args.segments:
    parser.error("Either text or --segments is required (or use --check)")

  if args.segments and args.text:
    parser.error("Cannot specify both text and --segments")

  # Multi-segment mode
  if args.segments:
    if not args.segments.exists():
      print(f"Segments file not found: {args.segments}")
      sys.exit(1)

    segments = [
      line.strip()
      for line in args.segments.read_text().splitlines()
      if line.strip()
    ]

    if not segments:
      print("No segments found in file")
      sys.exit(1)

    print(f"Generating {len(segments)} segments...")
    output_dir = args.output if args.output.suffix == "" else args.output.parent

    results = gen.generate_narration(
      segments=segments,
      output_dir=output_dir,
      prefix=args.prefix
    )

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"\nResults: {len(successful)}/{len(results)} successful")

    if successful:
      total_time = sum(r.generation_time or 0 for r in successful)
      total_size = sum(r.file_size or 0 for r in successful)
      print(f"Total time: {total_time:.1f}s")
      print(f"Total size: {total_size / 1024:.1f} KB")

    if failed:
      print("\nFailed segments:")
      for r in failed:
        print(f"  - \"{r.text[:50]}...\": {r.error}")

  # Single text mode
  else:
    print(f"Generating voice: \"{args.text[:60]}{'...' if len(args.text) > 60 else ''}\"")

    result = gen.generate(args.text, args.output)

    if result.success:
      print(f"Generated: {result.path}")
      print(f"  Time: {result.generation_time:.1f}s")
      print(f"  Size: {result.file_size / 1024:.1f} KB")

      # Mux with video if requested
      if args.mux_video:
        mux_output = args.mux_output or args.mux_video.with_stem(
          args.mux_video.stem + "_with_audio"
        )

        print(f"\nMuxing with video: {args.mux_video}")
        try:
          output = mux_audio(args.mux_video, result.path, mux_output)
          print(f"Muxed video: {output}")
        except Exception as e:
          print(f"Muxing failed: {e}")
          sys.exit(1)

    else:
      print(f"Generation failed: {result.error}")
      sys.exit(1)


if __name__ == "__main__":
  main()
