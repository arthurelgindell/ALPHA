"""
ARTHUR CLI - Media Production Facility Command Line Interface

Usage:
  arthur carousel "AI is watching your every keystroke"
  arthur video --duration 30 "The hidden truth about task mining"
  arthur status
  arthur outputs --type video --last 7d
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from . import __version__
from .config import PATHS, ALPHA_LM, BETA_LM, GAMMA_VIDEO
from .llm.clients import check_all_endpoints
from .generators.video import VideoGenerator
from .output.manager import OutputManager, OutputType
from .workflows.carousel import CarouselWorkflow
from .workflows.short_video import ShortVideoWorkflow

def print_header():
  """Print ARTHUR header"""
  print("""
╔═══════════════════════════════════════════════════════════════╗
║  ARTHUR Media Production Facility v{version:<25}║
║  Autonomous Workflow Automation                               ║
╚═══════════════════════════════════════════════════════════════╝
""".format(version=__version__))

def cmd_status(args):
  """Show system status"""
  print_header()
  print("🔍 Checking infrastructure status...\n")

  # LM Studio endpoints
  print("📡 LLM Endpoints:")
  llm_status = check_all_endpoints()

  for name, info in llm_status.items():
    status = "✅" if info.get("available") else "⚪"
    print(f"  {status} {name.upper()}: {info.get('name')} ({info.get('role')})")
    print(f"      URL: {info.get('url')}")
    if info.get("available"):
      models = info.get("models", [])
      if models:
        print(f"      Models: {', '.join(models[:3])}")
    else:
      print(f"      Status: Offline (start LM Studio)")

  # GAMMA video
  print("\n🎬 Video Generation:")
  video_gen = VideoGenerator()
  gamma_health = video_gen.check_gamma()

  if gamma_health.get("status") == "healthy":
    print(f"  ✅ GAMMA: HunyuanVideo-1.5")
    print(f"      GPU: {gamma_health.get('gpu_name')}")
    print(f"      Memory: {gamma_health.get('gpu_memory_free_gb', 0):.1f}GB free")
    print(f"      Model loaded: {gamma_health.get('model_loaded')}")
  else:
    print(f"  ❌ GAMMA: Offline")
    if "error" in gamma_health:
      print(f"      Error: {gamma_health['error']}")

  # Storage
  print("\n💾 Storage:")
  output_manager = OutputManager()

  if output_manager.studio_available():
    print(f"  ✅ STUDIO: Mounted at {PATHS.studio_mount}")
  else:
    print(f"  ⚪ STUDIO: Not mounted (mount BETA storage for sync)")

  print(f"  📁 Local images: {PATHS.images_dir}")
  print(f"  📁 Local videos: {PATHS.videos_dir}")
  print(f"  📁 Local carousels: {PATHS.carousels_dir}")

  # Recent outputs
  print("\n📊 Recent Outputs (7 days):")
  for output_type in [OutputType.IMAGE, OutputType.VIDEO, OutputType.CAROUSEL]:
    outputs = output_manager.list_outputs(output_type=output_type, days=7, limit=5)
    if outputs:
      print(f"\n  {output_type.value.upper()}S ({len(outputs)} recent):")
      for output in outputs[:3]:
        print(f"    • {output['filename']}")
        print(f"      {output['size_mb']:.1f}MB | {output['created'][:16]}")

def cmd_carousel(args):
  """Create LinkedIn carousel"""
  print_header()
  print(f"🎨 Creating carousel: {args.topic}\n")

  workflow = CarouselWorkflow(
    brief=args.topic,
    slide_count=args.slides,
    style=args.style
  )

  # Progress callback
  def on_progress(msg, pct):
    bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
    print(f"\r[{bar}] {pct*100:.0f}% {msg}", end="", flush=True)

  workflow.on_progress(on_progress)

  result = workflow.execute()
  print()  # New line after progress

  if result.success:
    print(f"\n✅ Carousel created successfully!")
    for output in result.outputs:
      print(f"   📁 {output}")

    if result.duration:
      print(f"\n⏱️  Duration: {result.duration:.1f} seconds")
  else:
    print(f"\n❌ Carousel creation failed!")
    for error in result.errors:
      print(f"   ⚠️  {error}")

def cmd_video(args):
  """Create short-form video"""
  print_header()
  print(f"🎬 Creating video: {args.topic}\n")
  print(f"   Duration: {args.duration}s | Platform: {args.platform}")

  workflow = ShortVideoWorkflow(
    brief=args.topic,
    duration=args.duration,
    style=args.style,
    platform=args.platform,
    use_resolve=not args.no_resolve
  )

  # Progress callback
  def on_progress(msg, pct):
    bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
    print(f"\r[{bar}] {pct*100:.0f}% {msg}", end="", flush=True)

  workflow.on_progress(on_progress)

  result = workflow.execute()
  print()  # New line after progress

  if result.success:
    print(f"\n✅ Video created successfully!")
    for output in result.outputs:
      print(f"   📁 {output}")

    if result.duration:
      print(f"\n⏱️  Duration: {result.duration:.1f} seconds")
  else:
    print(f"\n❌ Video creation failed!")
    for error in result.errors:
      print(f"   ⚠️  {error}")

def cmd_outputs(args):
  """List recent outputs"""
  print_header()

  output_manager = OutputManager()

  # Parse output type
  output_type = None
  if args.type:
    type_map = {
      "image": OutputType.IMAGE,
      "video": OutputType.VIDEO,
      "carousel": OutputType.CAROUSEL
    }
    output_type = type_map.get(args.type.lower())

  # Parse days
  days = 7
  if args.last:
    if args.last.endswith('d'):
      days = int(args.last[:-1])
    elif args.last.endswith('w'):
      days = int(args.last[:-1]) * 7

  outputs = output_manager.list_outputs(
    output_type=output_type,
    days=days,
    limit=args.limit
  )

  if not outputs:
    print(f"No outputs found in the last {days} days.")
    return

  print(f"📊 Recent Outputs ({len(outputs)} files, last {days} days):\n")

  for output in outputs:
    type_emoji = {
      "img": "🖼️",
      "vid": "🎬",
      "carousel": "📱"
    }.get(output["type"], "📄")

    print(f"{type_emoji} {output['filename']}")
    print(f"   Size: {output['size_mb']:.1f}MB | Created: {output['created'][:16]}")

    if output.get("metadata"):
      meta = output["metadata"]
      if meta.get("topic"):
        print(f"   Topic: {meta['topic']}")
      if meta.get("model"):
        print(f"   Model: {meta['model']}")
    print()

def cmd_sync(args):
  """Sync outputs to STUDIO volume"""
  print_header()

  output_manager = OutputManager()

  if not output_manager.studio_available():
    print("❌ STUDIO volume not mounted.")
    print("   Mount BETA storage first: mount_smbfs //beta/STUDIO /Volumes/STUDIO")
    return

  print("📤 Syncing to STUDIO volume...")

  # Parse output type
  output_type = None
  if args.type:
    type_map = {
      "image": OutputType.IMAGE,
      "video": OutputType.VIDEO,
      "carousel": OutputType.CAROUSEL
    }
    output_type = type_map.get(args.type.lower())

  synced = output_manager.sync_to_studio(output_type=output_type)

  if synced:
    print(f"\n✅ Synced {len(synced)} files:")
    for path in synced[:10]:
      print(f"   • {path.name}")
    if len(synced) > 10:
      print(f"   ... and {len(synced) - 10} more")
  else:
    print("\n✅ Already in sync (no new files)")

def main():
  """Main CLI entry point"""
  parser = argparse.ArgumentParser(
    description="ARTHUR Media Production Facility",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  arthur carousel "AI is watching your every keystroke"
  arthur video --duration 30 "The hidden truth about task mining"
  arthur status
  arthur outputs --type video --last 7d
  arthur sync
"""
  )

  parser.add_argument('--version', action='version', version=f'ARTHUR {__version__}')

  subparsers = parser.add_subparsers(dest='command', help='Commands')

  # Status command
  status_parser = subparsers.add_parser('status', help='Show system status')
  status_parser.set_defaults(func=cmd_status)

  # Carousel command
  carousel_parser = subparsers.add_parser('carousel', help='Create LinkedIn carousel')
  carousel_parser.add_argument('topic', help='Carousel topic/brief')
  carousel_parser.add_argument('--slides', type=int, default=8, help='Number of slides (default: 8)')
  carousel_parser.add_argument('--style', default='charcoal-amber', help='Visual style')
  carousel_parser.set_defaults(func=cmd_carousel)

  # Video command
  video_parser = subparsers.add_parser('video', help='Create short-form video')
  video_parser.add_argument('topic', help='Video topic/brief')
  video_parser.add_argument('--duration', type=int, default=30, help='Target duration in seconds')
  video_parser.add_argument('--platform', choices=['linkedin', 'youtube_shorts', 'instagram_reels'],
                           default='linkedin', help='Target platform')
  video_parser.add_argument('--style', default='documentary', help='Visual style')
  video_parser.add_argument('--no-resolve', action='store_true', help='Skip DaVinci Resolve assembly')
  video_parser.set_defaults(func=cmd_video)

  # Outputs command
  outputs_parser = subparsers.add_parser('outputs', help='List recent outputs')
  outputs_parser.add_argument('--type', choices=['image', 'video', 'carousel'], help='Filter by type')
  outputs_parser.add_argument('--last', default='7d', help='Time range (e.g., 7d, 2w)')
  outputs_parser.add_argument('--limit', type=int, default=50, help='Max results')
  outputs_parser.set_defaults(func=cmd_outputs)

  # Sync command
  sync_parser = subparsers.add_parser('sync', help='Sync outputs to STUDIO volume')
  sync_parser.add_argument('--type', choices=['image', 'video', 'carousel'], help='Filter by type')
  sync_parser.set_defaults(func=cmd_sync)

  args = parser.parse_args()

  if args.command is None:
    parser.print_help()
    sys.exit(1)

  try:
    args.func(args)
  except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user")
    sys.exit(1)
  except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
  main()
