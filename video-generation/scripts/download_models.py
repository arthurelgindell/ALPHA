#!/usr/bin/env python3
"""
Model Downloader
Downloads Wan 2.2 and other video generation models from HuggingFace
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

try:
  from huggingface_hub import hf_hub_download, snapshot_download
  HF_HUB_AVAILABLE = True
except ImportError:
  HF_HUB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """
    Download video generation models from HuggingFace

    Uses HuggingFace CLI for authenticated downloads
    """

    def __init__(self,
                 models_dir: str = "/Users/arthurdell/ARTHUR/video-generation/ComfyUI/models"):
        """
        Initialize downloader

        Args:
            models_dir: Base directory for models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Check for HuggingFace CLI
        self.has_hf_cli = self._check_hf_cli()

        logger.info(f"Model Downloader initialized: {self.models_dir}")

    def _check_hf_cli(self) -> bool:
        """Check if HuggingFace CLI is installed"""
        try:
            result = subprocess.run(
                ["huggingface-cli", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"HuggingFace CLI available: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            logger.warning("HuggingFace CLI not found")

        return False

    def install_hf_cli(self):
        """Install HuggingFace CLI"""
        logger.info("Installing HuggingFace CLI...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "huggingface_hub[cli]"
        ], check=True)
        self.has_hf_cli = True
        logger.info("✅ HuggingFace CLI installed")

    def download_wan22_models(self):
        """
        Download Wan 2.2 A14B models

        Downloads from Wan-AI/Wan2.2-T2V-A14B repository
        Repository structure:
        - high_noise_model/ (57 GB - 6 sharded safetensors files)
        - low_noise_model/ (similar size)
        - Wan2.1_VAE.pth (508 MB)
        - models_t5_umt5-xxl-enc-bf16.pth (11.4 GB)
        Total: ~126 GB
        """
        if not HF_HUB_AVAILABLE:
            logger.error("huggingface_hub not available. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            logger.info("✅ huggingface_hub installed. Please restart the script.")
            sys.exit(0)

        from huggingface_hub import snapshot_download

        logger.info("Downloading Wan 2.2 A14B models...")
        logger.info("This will download ~126GB of models:")
        logger.info("  - High noise expert model: 57 GB")
        logger.info("  - Low noise expert model: ~57 GB")
        logger.info("  - VAE: 508 MB")
        logger.info("  - T5-XXL encoder: 11.4 GB")
        logger.info("")
        logger.info("Expected download time: 1-2 hours on fast connection")
        logger.info("")

        # Create Wan models directory
        wan_dir = self.models_dir / "wan" / "Wan2.2-T2V-A14B"
        wan_dir.parent.mkdir(exist_ok=True)

        repo_id = "Wan-AI/Wan2.2-T2V-A14B"

        # Check if already downloaded
        if wan_dir.exists() and (wan_dir / "high_noise_model").exists():
            logger.info(f"✅ Model already exists at: {wan_dir}")
            logger.info("Verifying files...")

            required_files = [
                "high_noise_model/config.json",
                "low_noise_model/config.json",
                "Wan2.1_VAE.pth",
                "models_t5_umt5-xxl-enc-bf16.pth"
            ]

            all_present = all((wan_dir / f).exists() for f in required_files)

            if all_present:
                logger.info("✅ All required files present")
                return wan_dir
            else:
                logger.warning("⚠️  Some files missing, re-downloading...")

        try:
            # Download entire repository
            logger.info(f"📥 Downloading complete repository to: {wan_dir}")
            logger.info("This may take 1-2 hours...")

            downloaded_path = snapshot_download(
                repo_id=repo_id,
                local_dir=str(wan_dir),
                local_dir_use_symlinks=False,
                ignore_patterns=["*.git*", "assets/*", "google/*", "nohup.out"]  # Skip non-model files
            )

            logger.info(f"✅ Downloaded to: {downloaded_path}")

        except Exception as e:
            logger.error(f"❌ Failed to download models: {e}")
            raise

        logger.info("✅ All Wan 2.2 models downloaded successfully!")
        return wan_dir

    def _estimate_time(self, filename: str) -> str:
        """Estimate download time based on file size"""
        size_estimates = {
            "wan2.2_t2v_a14b_bf16.safetensors": "~30 minutes on fast connection",
            "wan_vae_bf16.safetensors": "~10 minutes",
            "t5_xxl_bf16.safetensors": "~20 minutes",
            "clip_g14_bf16.safetensors": "~5 minutes",
            "config.json": "<1 minute",
            "README.md": "<1 minute"
        }
        return size_estimates.get(filename, "Unknown")

    def download_hunyuanvideo_models(self):
        """
        Download HunyuanVideo 1.5 models (alternative/experimental)
        """
        if not self.has_hf_cli:
            self.install_hf_cli()

        logger.info("Downloading HunyuanVideo 1.5 models...")

        hunyuan_dir = self.models_dir / "hunyuan"
        hunyuan_dir.mkdir(exist_ok=True)

        repo_id = "tencent/HunyuanVideo-1.5"

        # Key files
        files_to_download = [
            "hunyuanvideo_1.5_bf16.safetensors",
            "hunyuan_vae_bf16.safetensors",
            "config.json"
        ]

        for filename in files_to_download:
            output_path = hunyuan_dir / filename

            if output_path.exists():
                logger.info(f"✅ Already downloaded: {filename}")
                continue

            logger.info(f"📥 Downloading: {filename}")

            try:
                cmd = [
                    "huggingface-cli",
                    "download",
                    repo_id,
                    filename,
                    "--local-dir", str(hunyuan_dir),
                    "--local-dir-use-symlinks", "False"
                ]

                subprocess.run(cmd, check=True)
                logger.info(f"✅ Downloaded: {filename}")

            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to download {filename}: {e}")
                # Non-fatal - continue

        logger.info("✅ HunyuanVideo models downloaded")
        return hunyuan_dir

    def verify_models(self) -> Dict[str, bool]:
        """
        Verify all required models are present

        Returns:
            Dict of model status
        """
        wan_dir = self.models_dir / "wan"

        required_files = {
            "wan2.2_main": wan_dir / "wan2.2_t2v_a14b_bf16.safetensors",
            "wan_vae": wan_dir / "wan_vae_bf16.safetensors",
            "t5_encoder": wan_dir / "t5_xxl_bf16.safetensors",
            "clip_encoder": wan_dir / "clip_g14_bf16.safetensors"
        }

        status = {}
        for name, path in required_files.items():
            exists = path.exists()
            status[name] = exists

            if exists:
                size_mb = path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ {name}: {size_mb:.1f} MB")
            else:
                logger.warning(f"❌ {name}: Missing")

        all_present = all(status.values())

        if all_present:
            logger.info("✅ All required models present")
        else:
            logger.warning("⚠️  Some models are missing")

        return status


def main():
    """Main download script"""
    downloader = ModelDownloader()

    logger.info("="*60)
    logger.info("VIDEO GENERATION MODELS DOWNLOADER")
    logger.info("="*60)
    logger.info("")

    # Download Wan 2.2 (primary model)
    logger.info("1. Downloading Wan 2.2 A14B (Production Model)")
    logger.info("   Expected size: ~100GB")
    logger.info("   Expected time: ~1 hour on fast connection")
    logger.info("")

    try:
        wan_dir = downloader.download_wan22_models()
        logger.info(f"✅ Wan 2.2 models saved to: {wan_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to download Wan 2.2: {e}")
        sys.exit(1)

    # Verify
    logger.info("")
    logger.info("2. Verifying models...")
    status = downloader.verify_models()

    if all(status.values()):
        logger.info("")
        logger.info("="*60)
        logger.info("✅ ALL MODELS DOWNLOADED SUCCESSFULLY")
        logger.info("="*60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start ComfyUI: python main.py --highvram")
        logger.info("2. Test video generation: python wan22_generator.py")
    else:
        logger.error("❌ Some models failed to download")
        sys.exit(1)


if __name__ == "__main__":
    main()
