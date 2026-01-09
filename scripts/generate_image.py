#!/usr/bin/env python3
"""
Production image generation tool for ARTHUR media facility

Usage:
    python3 scripts/generate_image.py "your prompt" --width 1920 --height 1088
    python3 scripts/generate_image.py "your prompt" --preset 16:9
    python3 scripts/generate_image.py "your prompt" --model schnell --steps 4
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

# Preset resolutions (FLUX-optimized, divisible by 64)
PRESETS = {
    "1:1": (1024, 1024),      # Square
    "4:3": (1152, 896),       # Standard
    "3:2": (1216, 832),       # Photo
    "16:9": (1344, 768),      # HD
    "16:9-large": (1920, 1088), # Full HD (1088 not 1080 - divisible by 64)
    "21:9": (1536, 640),      # Ultrawide
    "21:9-large": (2176, 960),  # Ultra-ultrawide
    "9:16": (768, 1344),      # Vertical/mobile
    "4:5": (1024, 1280),      # Portrait
}

# Available models
MODELS = {
    "dev": {
        "name": "FLUX.1 [dev]",
        "description": "Highest quality, 12B parameters",
        "default_steps": 25,
    },
    "schnell": {
        "name": "FLUX.1 [schnell]",
        "description": "Fast generation, Apache 2.0 license",
        "default_steps": 4,
    },
    "z-image-turbo": {
        "name": "Z-Image Turbo",
        "description": "Ultra-fast, sub-3 seconds",
        "default_steps": 8,
    }
}

def main():
    parser = argparse.ArgumentParser(
        description="Generate images with FLUX models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 1080p image
  python3 scripts/generate_image.py "cinematic cityscape at sunset" --preset 16:9-large

  # Quick generation with schnell
  python3 scripts/generate_image.py "red apple on table" --model schnell

  # Custom dimensions with seed
  python3 scripts/generate_image.py "portrait" --width 1024 --height 1280 --seed 42

  # Maximum quality
  python3 scripts/generate_image.py "landscape" --model dev --steps 30 --quantize 8
        """
    )
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("--preset", choices=list(PRESETS.keys()),
                       help="Resolution preset")
    parser.add_argument("--width", type=int, help="Custom width (must be divisible by 64)")
    parser.add_argument("--height", type=int, help="Custom height (must be divisible by 64)")
    parser.add_argument("--steps", type=int,
                       help="Number of steps (default varies by model)")
    parser.add_argument("--model", choices=list(MODELS.keys()), default="schnell",
                       help="Model to use (default: schnell)")
    parser.add_argument("--seed", type=int,
                       help="Seed for reproducibility")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--quantize", "-q", type=int, default=4,
                       choices=[3, 4, 5, 6, 8],
                       help="Quantization bits (default: 4)")

    args = parser.parse_args()

    # Get model info
    model_info = MODELS[args.model]

    # Determine resolution
    if args.preset:
        width, height = PRESETS[args.preset]
    elif args.width and args.height:
        width, height = args.width, args.height
        # Validate divisible by 64
        if width % 64 != 0 or height % 64 != 0:
            print(f"❌ Error: Width and height must be divisible by 64")
            print(f"   Current: {width}x{height}")
            print(f"   Nearest valid: {(width//64)*64}x{(height//64)*64}")
            sys.exit(1)
    else:
        width, height = 1024, 1024  # Default square

    # Determine steps
    if args.steps:
        steps = args.steps
    else:
        steps = model_info["default_steps"]

    # Generate output filename
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("/Users/arthurdell/ARTHUR/generated_images")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{args.model}_{width}x{height}_{timestamp}.png"

    # Set Hugging Face token from .env
    env_file = Path("/Users/arthurdell/ARTHUR/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    token = line.strip().split("=", 1)[1]
                    os.environ["HUGGING_FACE_HUB_TOKEN"] = token
                    break

    # Build command based on model
    if args.model in ["dev", "schnell"]:
        cmd = [
            "/opt/homebrew/bin/mflux-generate",
            "--model", args.model,
            "--prompt", args.prompt,
            "--steps", str(steps),
            "--height", str(height),
            "--width", str(width),
            "--quantize", str(args.quantize),
            "--output", str(output_file)
        ]
    elif args.model == "z-image-turbo":
        cmd = [
            "/opt/homebrew/bin/mflux-generate-z-image-turbo",
            "--prompt", args.prompt,
            "--steps", str(steps),
            "--height", str(height),
            "--width", str(width),
            "--output", str(output_file)
        ]

    if args.seed:
        cmd.extend(["--seed", str(args.seed)])

    # Display generation info
    print(f"\n{'='*60}")
    print(f"🎨 {model_info['name']} Image Generation")
    print(f"{'='*60}")
    print(f"Prompt: {args.prompt}")
    print(f"Model: {model_info['name']}")
    print(f"Resolution: {width}x{height} ({width*height/1_000_000:.1f}MP)")
    print(f"Steps: {steps}")
    if args.model in ["dev", "schnell"]:
        print(f"Quantization: {args.quantize}-bit")
    if args.seed:
        print(f"Seed: {args.seed}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")

    # Generate
    print(f"🔄 Generating...")
    if args.model == "dev" and steps >= 25:
        print(f"   (High-quality generation may take 60-90 seconds)\n")
    elif args.model == "schnell":
        print(f"   (Fast generation, ~10-30 seconds)\n")
    elif args.model == "z-image-turbo":
        print(f"   (Ultra-fast, ~3-10 seconds)\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n✅ Image generated successfully!")
        print(f"📁 Saved to: {output_file}")

        # Show file size
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"📊 File size: {size_kb:.1f} KB")
    else:
        print(f"\n❌ Generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
