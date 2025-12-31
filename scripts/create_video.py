#!/usr/bin/env python3
"""
Production Video Creator
User-facing interface for video generation
"""

import sys
import logging
from pathlib import Path

# Add video-generation scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "video-generation" / "scripts"))

from video_generator import VideoGenerator, VideoConfig
from model_registry import ModelRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_linkedin_video(
    topic: str,
    duration: int = 10,
    format_type: str = "square",
    message_density: str = "high"
):
    """
    Create LinkedIn video

    Args:
        topic: Video topic
        duration: Duration in seconds (5-30)
        format_type: "square" (1:1) or "wide" (16:9)
        message_density: "high", "medium", or "low"
    """
    logger.info("="*60)
    logger.info("CREATING LINKEDIN VIDEO")
    logger.info("="*60)
    logger.info(f"Topic: {topic}")
    logger.info(f"Duration: {duration}s")
    logger.info(f"Format: {format_type}")
    logger.info(f"Quality: {message_density} density")
    logger.info("")

    generator = VideoGenerator()

    try:
        video_path = generator.generate_linkedin_video(
            topic=topic,
            duration=duration,
            format_type=format_type,
            message_density=message_density
        )

        logger.info("")
        logger.info("="*60)
        logger.info("✅ VIDEO GENERATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Location: {video_path}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Review video")
        logger.info("2. Upload to LinkedIn")
        logger.info("3. Track engagement metrics")

        return video_path

    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        raise
    finally:
        generator.close()


def create_youtube_short(
    hook: str,
    content: str,
    cta: str,
    duration: int = 30,
    message_density: str = "medium"
):
    """
    Create YouTube Short (9:16 vertical)

    Args:
        hook: Opening hook
        content: Main content
        cta: Call to action
        duration: Duration in seconds (10-60)
        message_density: "high", "medium", or "low"
    """
    logger.info("="*60)
    logger.info("CREATING YOUTUBE SHORT")
    logger.info("="*60)
    logger.info(f"Hook: {hook}")
    logger.info(f"Content: {content}")
    logger.info(f"CTA: {cta}")
    logger.info(f"Duration: {duration}s")
    logger.info(f"Quality: {message_density} density")
    logger.info("")

    generator = VideoGenerator()

    try:
        video_path = generator.generate_youtube_short(
            hook=hook,
            content=content,
            cta=cta,
            duration=duration,
            message_density=message_density
        )

        logger.info("")
        logger.info("="*60)
        logger.info("✅ YOUTUBE SHORT COMPLETE")
        logger.info("="*60)
        logger.info(f"Location: {video_path}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Review video")
        logger.info("2. Upload to YouTube Shorts")
        logger.info("3. Track performance")

        return video_path

    except Exception as e:
        logger.error(f"❌ Video generation failed: {e}")
        raise
    finally:
        generator.close()


def show_model_status():
    """Display model registry status"""
    registry = ModelRegistry()
    print(registry.generate_report())


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="ARTHUR Video Generation System")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # LinkedIn video
    linkedin_parser = subparsers.add_parser("linkedin", help="Create LinkedIn video")
    linkedin_parser.add_argument("topic", help="Video topic")
    linkedin_parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    linkedin_parser.add_argument("--format", choices=["square", "wide"], default="square")
    linkedin_parser.add_argument("--quality", choices=["high", "medium", "low"], default="high")

    # YouTube Short
    youtube_parser = subparsers.add_parser("youtube", help="Create YouTube Short")
    youtube_parser.add_argument("--hook", required=True, help="Opening hook")
    youtube_parser.add_argument("--content", required=True, help="Main content")
    youtube_parser.add_argument("--cta", required=True, help="Call to action")
    youtube_parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    youtube_parser.add_argument("--quality", choices=["high", "medium", "low"], default="medium")

    # Model status
    subparsers.add_parser("models", help="Show model registry status")

    args = parser.parse_args()

    if args.command == "linkedin":
        create_linkedin_video(
            topic=args.topic,
            duration=args.duration,
            format_type=args.format,
            message_density=args.quality
        )

    elif args.command == "youtube":
        create_youtube_short(
            hook=args.hook,
            content=args.content,
            cta=args.cta,
            duration=args.duration,
            message_density=args.quality
        )

    elif args.command == "models":
        show_model_status()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
