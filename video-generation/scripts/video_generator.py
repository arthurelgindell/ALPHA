#!/usr/bin/env python3
"""
Video Generator - Replicate API Backend
High-level interface for generating videos via Replicate API
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from replicate_backend import ReplicateBackend, ReplicateVideoConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoFormat:
    """Video format specifications"""
    width: int
    height: int
    fps: int
    name: str


# Standard formats
LINKEDIN_SQUARE = VideoFormat(1080, 1080, 24, "LinkedIn Square")
LINKEDIN_WIDE = VideoFormat(1920, 1080, 24, "LinkedIn Wide")
YOUTUBE_SHORTS = VideoFormat(1080, 1920, 30, "YouTube Shorts")


@dataclass
class VideoConfig:
    """Configuration for video generation"""
    prompt: str
    duration: int  # seconds
    format: VideoFormat
    quality_density: str = "medium"  # high, medium, low
    output_filename: Optional[str] = None


class VideoGenerator:
    """
    High-level interface for video generation via Replicate API

    Handles quality optimization and multi-format support
    """

    def __init__(self,
                 api_token: Optional[str] = None,
                 output_dir: str = "/Users/arthurdell/ARTHUR/videos/raw"):
        """
        Initialize video generator

        Args:
            api_token: Replicate API token (or set REPLICATE_API_TOKEN env var)
            output_dir: Output directory for videos
        """
        self.backend = ReplicateBackend(api_token=api_token)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Video Generator initialized (Replicate backend)")

    def _map_quality_to_steps(self, quality: str) -> int:
        """Map quality density to inference steps"""
        steps_map = {
            "high": 30,     # High quality, slower
            "medium": 20,   # Balanced
            "low": 15       # Fast preview
        }
        return steps_map.get(quality.lower(), 20)

    def generate(self, config: VideoConfig) -> Path:
        """
        Generate video

        Args:
            config: Video configuration

        Returns:
            Path to generated video

        Raises:
            Exception: If video generation fails
        """
        logger.info("="*60)
        logger.info("STARTING VIDEO GENERATION")
        logger.info("="*60)
        logger.info(f"Prompt: {config.prompt}")
        logger.info(f"Format: {config.format.name} ({config.format.width}x{config.format.height})")
        logger.info(f"Duration: {config.duration}s")
        logger.info(f"Quality: {config.quality_density}")
        logger.info("")

        # Calculate frame count
        num_frames = config.duration * config.format.fps

        # Create output filename
        if config.output_filename:
            output_path = self.output_dir / config.output_filename
        else:
            safe_prompt = "".join(c for c in config.prompt[:30] if c.isalnum() or c in " _-").strip()
            safe_prompt = safe_prompt.replace(" ", "_").lower()
            output_path = self.output_dir / f"{safe_prompt}_{config.format.width}x{config.format.height}.mp4"

        # Create Replicate config
        replicate_config = ReplicateVideoConfig(
            prompt=config.prompt,
            height=config.format.height,
            width=config.format.width,
            num_frames=num_frames,
            fps=config.format.fps,
            num_inference_steps=self._map_quality_to_steps(config.quality_density),
            guidance_scale=4.0,
            output_path=str(output_path)
        )

        # Estimate cost
        estimated_cost = self.backend.estimate_cost(replicate_config)
        logger.info(f"Estimated cost: ${estimated_cost:.2f}")

        # Generate video
        video_path = self.backend.generate(replicate_config)

        logger.info("")
        logger.info("="*60)
        logger.info("✅ VIDEO GENERATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Location: {video_path}")
        logger.info(f"Cost: ~${estimated_cost:.2f}")
        logger.info("")

        return video_path

    def generate_linkedin_video(self,
                                topic: str,
                                duration: int = 10,
                                format_type: str = "square",
                                message_density: str = "high") -> Path:
        """
        Generate LinkedIn video

        Args:
            topic: Video topic/prompt
            duration: Duration in seconds
            format_type: "square" (1:1) or "wide" (16:9)
            message_density: "high", "medium", or "low"

        Returns:
            Path to generated video
        """
        format_map = {
            "square": LINKEDIN_SQUARE,
            "wide": LINKEDIN_WIDE
        }

        video_format = format_map.get(format_type, LINKEDIN_SQUARE)

        config = VideoConfig(
            prompt=topic,
            duration=duration,
            format=video_format,
            quality_density=message_density
        )

        return self.generate(config)

    def generate_youtube_short(self,
                              hook: str,
                              content: str,
                              cta: str,
                              duration: int = 30,
                              message_density: str = "medium") -> Path:
        """
        Generate YouTube Short

        Args:
            hook: Opening hook
            content: Main content
            cta: Call to action
            duration: Duration in seconds
            message_density: "high", "medium", or "low"

        Returns:
            Path to generated video
        """
        # Combine into single prompt
        full_prompt = f"{hook}. {content}. {cta}"

        config = VideoConfig(
            prompt=full_prompt,
            duration=duration,
            format=YOUTUBE_SHORTS,
            quality_density=message_density
        )

        return self.generate(config)

    def close(self):
        """Cleanup resources"""
        logger.info("Video generator closed")
