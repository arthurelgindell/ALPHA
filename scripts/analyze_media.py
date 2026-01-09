#!/usr/bin/env python3
"""
Vision analysis CLI for ARTHUR media production

Analyze images and videos using GLM-4.6V-Flash vision model via LM Studio.

Usage:
  # Quick analysis
  python3 scripts/analyze_media.py image.png "What device is shown?"

  # Product verification
  python3 scripts/analyze_media.py image.png --verify-product "Mac Studio" --color silver

  # Quality rating
  python3 scripts/analyze_media.py hero.png --quality

  # Video keyframe analysis
  python3 scripts/analyze_media.py promo.mp4 "Describe content" --frames 3

  # JSON output for programmatic use
  python3 scripts/analyze_media.py image.png "Analyze" --json

  # Health check
  python3 scripts/analyze_media.py --health
"""

import argparse
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from arthur.vision import VisionClient, VisionAnalyzer
from arthur.vision.keyframe import get_video_info


def setup_logging(verbose: bool):
  """Configure logging based on verbosity"""
  level = logging.DEBUG if verbose else logging.WARNING
  logging.basicConfig(
    level=level,
    format="%(levelname)s: %(message)s"
  )


def print_result(result, json_output: bool):
  """Print analysis result in requested format"""
  if json_output:
    if hasattr(result, 'to_json'):
      print(result.to_json())
    else:
      print(json.dumps({
        "success": result.success,
        "analysis": result.analysis if hasattr(result, 'analysis') else str(result),
        "error": result.error if hasattr(result, 'error') else None
      }, indent=2))
  else:
    if hasattr(result, 'success'):
      if result.success:
        if hasattr(result, 'summary'):
          print(f"\n✅ {result.summary}")
          if hasattr(result, 'details') and result.details:
            if 'raw_analysis' in result.details:
              print(f"\n{result.details['raw_analysis']}")
            elif 'full_description' in result.details:
              print(f"\n{result.details['full_description']}")
            elif 'scores' in result.details:
              print("\nScores:")
              for k, v in result.details['scores'].items():
                print(f"  {k}: {v}/10")
        elif hasattr(result, 'analysis'):
          print(f"\n{result.analysis}")
      else:
        print(f"\n❌ Error: {result.error}")
    else:
      print(result)


def cmd_health(args):
  """Check vision endpoint health"""
  client = VisionClient()
  health = client.check_health()

  if args.json:
    print(json.dumps(health, indent=2))
  else:
    if health["available"]:
      print("✅ Vision endpoint is available")
      print(f"   Models: {', '.join(health['models'])}")
      if health["vision_capable"]:
        print("   Vision capability: YES")
      else:
        print("   ⚠️  No vision model detected in model list")
    else:
      print(f"❌ Vision endpoint unavailable: {health['error']}")

  return 0 if health["available"] else 1


def cmd_analyze(args):
  """Analyze media with custom prompt"""
  media_path = Path(args.media)

  if not media_path.exists():
    print(f"❌ File not found: {media_path}")
    return 1

  # Check if video or image
  video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
  is_video = media_path.suffix.lower() in video_extensions

  if is_video:
    # Video analysis
    analyzer = VisionAnalyzer()
    result = analyzer.analyze_video(
      media_path,
      args.prompt,
      num_keyframes=args.frames,
      cleanup_frames=not args.keep_frames
    )
  else:
    # Image analysis
    client = VisionClient()
    result = client.analyze_image(media_path, args.prompt, detail=args.detail)

  print_result(result, args.json)
  return 0 if result.success else 1


def cmd_verify_product(args):
  """Verify product in image"""
  media_path = Path(args.media)

  if not media_path.exists():
    print(f"❌ File not found: {media_path}")
    return 1

  analyzer = VisionAnalyzer()

  # Check if video - extract first frame
  video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
  is_video = media_path.suffix.lower() in video_extensions

  if is_video:
    from arthur.vision.keyframe import extract_keyframes
    keyframes = extract_keyframes(media_path, num_frames=1)
    if not keyframes.success:
      print(f"❌ Failed to extract frame from video: {keyframes.error}")
      return 1
    analysis_path = keyframes.frames[0]
  else:
    analysis_path = media_path

  result = analyzer.verify_product(
    analysis_path,
    expected_product=args.verify_product,
    expected_color=args.color,
    expected_setting=args.setting
  )

  # Cleanup video frame
  if is_video:
    keyframes.cleanup()

  print_result(result, args.json)

  # Return code based on verification result
  if result.success:
    details = result.details
    if details.get("product_match") is False or details.get("color_match") is False:
      return 2  # Verification failed
  return 0 if result.success else 1


def cmd_quality(args):
  """Rate image quality"""
  media_path = Path(args.media)

  if not media_path.exists():
    print(f"❌ File not found: {media_path}")
    return 1

  analyzer = VisionAnalyzer()

  # Check if video - extract middle frame
  video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
  is_video = media_path.suffix.lower() in video_extensions

  if is_video:
    from arthur.vision.keyframe import extract_keyframes
    keyframes = extract_keyframes(media_path, num_frames=1)
    if not keyframes.success:
      print(f"❌ Failed to extract frame from video: {keyframes.error}")
      return 1
    analysis_path = keyframes.frames[0]
  else:
    analysis_path = media_path

  result = analyzer.rate_quality(
    analysis_path,
    criteria=args.criteria
  )

  # Cleanup video frame
  if is_video:
    keyframes.cleanup()

  print_result(result, args.json)

  # Return code based on quality
  if result.success and result.details.get("overall"):
    if result.details["overall"] < 6:
      return 2  # Quality too low
  return 0 if result.success else 1


def cmd_describe(args):
  """Describe image/video scene"""
  media_path = Path(args.media)

  if not media_path.exists():
    print(f"❌ File not found: {media_path}")
    return 1

  analyzer = VisionAnalyzer()

  # Check if video
  video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
  is_video = media_path.suffix.lower() in video_extensions

  if is_video:
    result = analyzer.analyze_video(
      media_path,
      "Describe what happens in this video in detail",
      num_keyframes=args.frames
    )
  else:
    result = analyzer.describe_scene(media_path, focus=args.focus)

  print_result(result, args.json)
  return 0 if result.success else 1


def cmd_video_info(args):
  """Get video metadata"""
  media_path = Path(args.media)

  if not media_path.exists():
    print(f"❌ File not found: {media_path}")
    return 1

  info = get_video_info(media_path)

  if args.json:
    print(json.dumps(info, indent=2))
  else:
    if info.get("error"):
      print(f"❌ Error: {info['error']}")
      return 1
    print(f"Duration: {info['duration']:.2f}s")
    print(f"Resolution: {info['width']}x{info['height']}")
    print(f"FPS: {info['fps']}")
    print(f"Codec: {info['codec']}")

  return 0 if not info.get("error") else 1


def main():
  parser = argparse.ArgumentParser(
    description="Analyze images and videos with GLM-4.6V-Flash vision model",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Quick analysis
  %(prog)s image.png "What device is shown?"

  # Product verification
  %(prog)s video.mp4 --verify-product "Mac Studio" --color silver

  # Quality rating
  %(prog)s hero.png --quality

  # Video keyframe analysis
  %(prog)s promo.mp4 "Describe key moments" --frames 3

  # Health check
  %(prog)s --health
    """
  )

  # Global options
  parser.add_argument("--json", action="store_true",
            help="Output results as JSON")
  parser.add_argument("--verbose", "-v", action="store_true",
            help="Show detailed debug output")
  parser.add_argument("--health", action="store_true",
            help="Check vision endpoint health and exit")

  # Media argument (optional if --health)
  parser.add_argument("media", nargs="?",
            help="Image or video file to analyze")
  parser.add_argument("prompt", nargs="?",
            help="Analysis prompt/question")

  # Analysis modes
  parser.add_argument("--verify-product", metavar="NAME",
            help="Verify specific product is shown correctly")
  parser.add_argument("--color", metavar="COLOR",
            help="Expected product color (with --verify-product)")
  parser.add_argument("--setting", metavar="SETTING",
            help="Expected setting/environment")

  parser.add_argument("--quality", action="store_true",
            help="Rate image/video quality on standard criteria")
  parser.add_argument("--criteria", nargs="+",
            help="Custom quality criteria (with --quality)")

  parser.add_argument("--describe", action="store_true",
            help="Get detailed scene description")
  parser.add_argument("--focus", metavar="FOCUS",
            help="Focus area for description (with --describe)")

  parser.add_argument("--info", action="store_true",
            help="Get video metadata only (no vision analysis)")

  # Video options
  parser.add_argument("--frames", type=int, default=3,
            help="Number of keyframes to extract from videos (default: 3)")
  parser.add_argument("--keep-frames", action="store_true",
            help="Keep extracted keyframe files after analysis")
  parser.add_argument("--detail", choices=["low", "high"], default="low",
            help="Image analysis detail level (default: low)")

  args = parser.parse_args()

  # Setup logging
  setup_logging(args.verbose)

  # Handle --health
  if args.health:
    return cmd_health(args)

  # Require media path for other commands
  if not args.media:
    parser.print_help()
    return 1

  # Route to appropriate command
  if args.info:
    return cmd_video_info(args)
  elif args.verify_product:
    return cmd_verify_product(args)
  elif args.quality:
    return cmd_quality(args)
  elif args.describe:
    return cmd_describe(args)
  elif args.prompt:
    return cmd_analyze(args)
  else:
    # Default to describe if no prompt
    args.focus = None
    return cmd_describe(args)


if __name__ == "__main__":
  sys.exit(main())
