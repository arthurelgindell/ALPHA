#!/usr/bin/env python3
"""
HunyuanVideo MPS Backend for Local Video Generation
Wrapper around HunyuanVideo_MLX for Apple Silicon
"""

import os
import sys
import time
import torch
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging
from datetime import datetime

# Add HunyuanVideo_MLX to path
HUNYUAN_PATH = Path(__file__).parent.parent / "HunyuanVideo_MLX"
sys.path.insert(0, str(HUNYUAN_PATH))

from hyvideo.utils.file_utils import save_videos_grid
from hyvideo.config import parse_args
from hyvideo.inference import HunyuanVideoSampler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HunyuanVideoConfig:
    """Configuration for HunyuanVideo generation"""
    prompt: str
    height: int
    width: int
    video_length: int  # Number of frames
    fps: int = 24
    seed: int = None
    infer_steps: int = 40
    guidance_scale: float = 7.0
    negative_prompt: str = ""
    output_path: Optional[str] = None


class HunyuanBackend:
    """
    Backend wrapper for HunyuanVideo MPS (local generation)

    Uses PyTorch MPS backend for Apple Silicon GPU acceleration.
    Note: This is not pure MLX, but the best local option available.
    """

    def __init__(self,
                 model_path: str = "/Users/arthurdell/ARTHUR/MODELS/hunyuan-video",
                 device: str = "mps"):
        """
        Initialize HunyuanVideo backend

        Args:
            model_path: Path to model files
            device: Device to use (mps for Apple GPU)
        """
        self.model_path = Path(model_path)
        self.device = device
        self.sampler = None

        # Check MPS availability
        if not torch.backends.mps.is_available():
            raise RuntimeError(
                "MPS not available. Check that:\n"
                "1. You're on macOS 12.3+\n"
                "2. PyTorch was built with MPS support\n"
                "3. You have an Apple Silicon Mac"
            )

        logger.info("HunyuanVideo backend initialized (MPS)")
        logger.info(f"Model path: {self.model_path}")

    def _initialize_sampler(self):
        """Lazy load the model (only when needed)"""
        if self.sampler is not None:
            return

        logger.info("Loading HunyuanVideo model (this may take a few minutes)...")
        start_time = time.time()

        # Create minimal args for model loading
        # Save original sys.argv to avoid conflicts with parent script
        import argparse
        orig_argv = sys.argv.copy()
        sys.argv = [sys.argv[0]]  # Keep only script name

        parser = argparse.ArgumentParser()
        args = parse_args(namespace=parser.parse_args([]))

        # Restore original sys.argv
        sys.argv = orig_argv

        # Configure for Apple Silicon
        args.model_base = str(self.model_path)
        args.mmgp_mode = True
        args.precision = "fp32"
        args.vae_precision = "fp32"
        args.text_encoder_precision = "fp32"
        args.disable_autocast = True

        # Load model
        device = torch.device(self.device)
        self.sampler = HunyuanVideoSampler.from_pretrained(
            self.model_path,
            args=args,
            device=device
        )

        duration = time.time() - start_time
        logger.info(f"✅ Model loaded in {duration:.1f}s")

    def generate(self, config: HunyuanVideoConfig) -> Path:
        """
        Generate video using HunyuanVideo

        Args:
            config: Video generation configuration

        Returns:
            Path to generated video file

        Raises:
            Exception: If video generation fails
        """
        logger.info(f"Starting local video generation: {config.prompt[:50]}...")
        logger.info(f"Resolution: {config.width}x{config.height}, Frames: {config.video_length}")

        start_time = time.time()

        try:
            # Initialize model if needed
            self._initialize_sampler()

            # Set seed for reproducibility
            seed = config.seed if config.seed is not None else int(time.time())

            # Generate video
            outputs = self.sampler.predict(
                prompt=config.prompt,
                height=config.height,
                width=config.width,
                video_length=config.video_length,
                seed=seed,
                negative_prompt=config.negative_prompt,
                infer_steps=config.infer_steps,
                guidance_scale=config.guidance_scale,
                num_videos_per_prompt=1,
                flow_shift=7.0,
                batch_size=1,
                embedded_guidance_scale=6.0
            )

            samples = outputs['samples']

            # Prepare output path
            if config.output_path:
                output_path = Path(config.output_path)
            else:
                time_flag = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d-%H:%M:%S")
                safe_prompt = "".join(c for c in config.prompt[:30] if c.isalnum() or c in " _-").strip()
                safe_prompt = safe_prompt.replace(" ", "_").lower()
                output_path = Path(f"video_{time_flag}_{safe_prompt}.mp4")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save video
            sample = samples[0].unsqueeze(0)
            save_videos_grid(sample, str(output_path), fps=config.fps)

            duration = time.time() - start_time
            logger.info(f"✅ Video generated successfully in {duration:.1f}s")
            logger.info(f"Saved to: {output_path}")

            return output_path

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Video generation failed after {duration:.1f}s: {e}")
            raise

    def estimate_time(self, config: HunyuanVideoConfig) -> float:
        """
        Estimate generation time

        Args:
            config: Video generation configuration

        Returns:
            Estimated time in seconds
        """
        # Rough estimates based on resolution and frames
        pixels = config.height * config.width
        frames = config.video_length

        # Base time per megapixel-frame on Apple Silicon
        time_per_mpf = 0.5  # seconds (rough estimate)

        total_mpf = (pixels * frames) / 1_000_000
        estimated = total_mpf * time_per_mpf * (config.infer_steps / 40)

        logger.info(f"Estimated generation time: {estimated/60:.1f} minutes")

        return estimated

    def close(self):
        """Cleanup resources"""
        if self.sampler is not None:
            del self.sampler
            self.sampler = None
            torch.mps.empty_cache()
            logger.info("HunyuanVideo backend closed")
