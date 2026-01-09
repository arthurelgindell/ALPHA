#!/usr/bin/env python3
"""
Minimal CPU test to validate Wan 2.2 pipeline works correctly
Tests with tiny config: 128x128, 5 frames, 10 steps
Expected time: 10-20 minutes
"""

import torch
import time
import logging
from pathlib import Path
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cpu_minimal():
    """Test Wan 2.2 on CPU with minimal configuration"""

    # Configuration - MINIMAL for quick validation
    model_path = "/Users/arthurdell/ARTHUR/video-generation/ComfyUI/models/wan/diffusers/Wan2.2-T2V-A14B-Diffusers"
    output_dir = Path("/Users/arthurdell/ARTHUR/videos/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Force CPU
    device = "cpu"
    dtype = torch.float32  # CPU supports float32

    logger.info("=" * 60)
    logger.info("WAN 2.2 MINIMAL CPU TEST")
    logger.info("=" * 60)
    logger.info(f"Device: {device}")
    logger.info(f"Dtype: {dtype}")
    logger.info("This test validates the pipeline works correctly")
    logger.info("Expected time: 10-20 minutes")
    logger.info("=" * 60)

    # Load VAE
    logger.info("Loading VAE...")
    vae = AutoencoderKLWan.from_pretrained(
        model_path,
        subfolder="vae",
        torch_dtype=dtype
    )

    # Load pipeline
    logger.info("Loading Wan Pipeline...")
    pipe = WanPipeline.from_pretrained(
        model_path,
        vae=vae,
        torch_dtype=dtype
    )

    # Move to CPU
    logger.info(f"Moving pipeline to {device}...")
    pipe = pipe.to(device)

    # MINIMAL parameters for quick test
    height = 128
    width = 128
    num_frames = 5  # Just 5 frames
    fps = 16
    num_inference_steps = 10  # Reduced from 40

    # Simple test prompt
    prompt = "A blue sphere rotating on a white background"
    negative_prompt = "blurry, low quality"

    logger.info("")
    logger.info("TEST PARAMETERS:")
    logger.info(f"  Resolution: {width}x{height}")
    logger.info(f"  Frames: {num_frames}")
    logger.info(f"  Steps: {num_inference_steps}")
    logger.info(f"  Prompt: {prompt}")
    logger.info("")

    # Generate
    logger.info("🎬 Starting minimal test generation...")
    logger.info("This will take 10-20 minutes on CPU...")

    start_time = time.time()

    try:
        output = pipe(
            prompt=prompt.strip(),
            negative_prompt=negative_prompt.strip(),
            height=height,
            width=width,
            num_frames=num_frames,
            guidance_scale=4.0,
            guidance_scale_2=3.0,
            num_inference_steps=num_inference_steps,
        ).frames[0]

        generation_time = time.time() - start_time

        # Export
        output_path = output_dir / f"cpu_test_minimal_{int(time.time())}.mp4"
        logger.info(f"💾 Exporting video to: {output_path}")
        export_to_video(output, str(output_path), fps=fps)

        # Check file size
        file_size_kb = output_path.stat().st_size / 1024

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ CPU TEST COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Output: {output_path}")
        logger.info(f"File size: {file_size_kb:.1f} KB")
        logger.info(f"Generation time: {generation_time/60:.1f} minutes")
        logger.info(f"Speed: {generation_time/num_frames:.2f}s per frame")
        logger.info("")

        # Validation
        if file_size_kb < 50:
            logger.warning("⚠️  WARNING: File size very small - may indicate issues")
        else:
            logger.info("✓ File size looks reasonable")

        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. View the output video")
        logger.info("2. If it shows actual content (sphere): Pipeline works, MPS is the problem")
        logger.info("3. If it shows noise: Deeper model/config issue")
        logger.info("=" * 60)

        return output_path

    except Exception as e:
        logger.error(f"❌ CPU test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    test_cpu_minimal()
