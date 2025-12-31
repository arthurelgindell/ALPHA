#!/usr/bin/env python3
"""
Replicate API Backend for Video Generation
Cloud-based video generation using Replicate API
"""

import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging

try:
    import replicate
except ImportError:
    raise ImportError("Replicate SDK not installed. Run: pip install replicate")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReplicateVideoConfig:
    """Configuration for Replicate video generation"""
    prompt: str
    height: int
    width: int
    num_frames: int
    fps: int = 16
    num_inference_steps: int = 30
    guidance_scale: float = 4.0
    output_path: Optional[str] = None
    model: str = "minimax/video-01"  # Default model


class ReplicateBackend:
    """
    Backend wrapper for Replicate API video generation

    Supports multiple video generation models:
    - minimax/video-01: High-quality, commercial-friendly
    - tencent/hunyuanvideo: Alternative option
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Replicate backend

        Args:
            api_token: Replicate API token (or set REPLICATE_API_TOKEN env var)
        """
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")

        if not self.api_token:
            raise ValueError(
                "Replicate API token required. Set REPLICATE_API_TOKEN environment "
                "variable or pass api_token parameter. Get token at: "
                "https://replicate.com/account/api-tokens"
            )

        # Set token for replicate library
        os.environ["REPLICATE_API_TOKEN"] = self.api_token

        logger.info("Replicate backend initialized")

    def generate(self, config: ReplicateVideoConfig) -> Path:
        """
        Generate video using Replicate API

        Args:
            config: Video generation configuration

        Returns:
            Path to downloaded video file

        Raises:
            Exception: If video generation fails
        """
        logger.info(f"Starting video generation via Replicate: {config.prompt[:50]}...")
        logger.info(f"Resolution: {config.width}x{config.height}, Frames: {config.num_frames}")

        start_time = time.time()

        try:
            # Run video generation via Replicate API
            output = replicate.run(
                config.model,
                input={
                    "prompt": config.prompt,
                    "aspect_ratio": f"{config.width}:{config.height}",
                    "num_frames": config.num_frames,
                    "guidance_scale": config.guidance_scale,
                    "num_inference_steps": config.num_inference_steps,
                }
            )

            # Output is a URL to the generated video
            video_url = output if isinstance(output, str) else output[0]

            # Download video
            output_path = config.output_path or f"video_{int(time.time())}.mp4"
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading video from: {video_url}")

            import requests
            response = requests.get(video_url, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            duration = time.time() - start_time
            logger.info(f"✅ Video generated successfully in {duration:.1f}s")
            logger.info(f"Saved to: {output_path}")

            return output_path

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Video generation failed after {duration:.1f}s: {e}")
            raise

    def estimate_cost(self, config: ReplicateVideoConfig) -> float:
        """
        Estimate cost for video generation

        Args:
            config: Video generation configuration

        Returns:
            Estimated cost in USD
        """
        # MiniMax Video-01 pricing (approximate)
        # ~$0.05 per second of video
        duration_seconds = config.num_frames / config.fps
        cost_per_second = 0.05

        estimated_cost = duration_seconds * cost_per_second

        logger.info(f"Estimated cost: ${estimated_cost:.2f} for {duration_seconds:.1f}s video")

        return estimated_cost

    def list_available_models(self) -> list[str]:
        """List available video generation models on Replicate"""
        return [
            "minimax/video-01",           # High-quality, commercial-friendly
            "tencent/hunyuanvideo",       # Alternative option
            "lucataco/animate-diff",      # Animation-focused
        ]


def test_replicate_backend():
    """Test function for Replicate backend"""
    logger.info("Testing Replicate backend...")

    try:
        backend = ReplicateBackend()

        # Test with minimal config
        config = ReplicateVideoConfig(
            prompt="A blue sphere rotating slowly",
            height=480,
            width=480,
            num_frames=25,  # ~1.5 seconds at 16fps
            fps=16,
            num_inference_steps=20,
            output_path="/Users/arthurdell/ARTHUR/videos/test_replicate.mp4"
        )

        # Estimate cost
        backend.estimate_cost(config)

        # Generate video
        video_path = backend.generate(config)

        logger.info(f"✅ Test successful! Video at: {video_path}")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    test_replicate_backend()
