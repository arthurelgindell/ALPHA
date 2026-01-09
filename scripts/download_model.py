#!/usr/bin/env python3
"""
Helper script to download MLX models from Hugging Face

Usage:
    python3 scripts/download_model.py <model_id>
    python3 scripts/download_model.py --list
    python3 scripts/download_model.py --recommended

Examples:
    python3 scripts/download_model.py mlx-community/gpt-oss-20b-MXFP4-Q8
    python3 scripts/download_model.py lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, HfApi

# Configuration - get token from environment variable
TOKEN = os.getenv("HF_TOKEN", "")
CACHE_DIR = Path("/Users/arthurdell/ARTHUR/MODELS/.cache")
MODELS_DIR = Path("/Users/arthurdell/ARTHUR/MODELS")

# Recommended models
RECOMMENDED = {
    "llm": "lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit",
    "vision": "lmstudio-community/Qwen3-VL-8B-Instruct-MLX-8bit",
    "audio": "mlx-community/whisper-large-v3-mlx",
    "code": "lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit",
    "reasoning": "lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-MLX-8bit",
    "large": "mlx-community/gpt-oss-20b-MXFP4-Q8",
}

def show_recommended():
    """Show recommended models"""
    print("\n🌟 RECOMMENDED MLX MODELS:\n")
    print(f"{'Category':<12} {'Model ID'}")
    print("-" * 80)

    for category, model_id in RECOMMENDED.items():
        print(f"{category:<12} {model_id}")

    print("\n💡 Usage:")
    print(f"   python3 {sys.argv[0]} <model_id>")
    print(f"\n📚 Full catalog: See MLX_MODELS_CATALOG.md")

def download_model(model_id: str):
    """Download a model from Hugging Face"""

    print(f"\n📦 Downloading: {model_id}")
    print(f"📁 Cache directory: {CACHE_DIR}")
    print("-" * 80)

    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Get model info
        api = HfApi(token=TOKEN)
        model_info = api.model_info(model_id)

        # Show model details
        print(f"\n✨ Model: {model_info.id}")
        if hasattr(model_info, 'downloads'):
            print(f"📊 Downloads: {model_info.downloads:,}")
        if hasattr(model_info, 'likes'):
            print(f"❤️  Likes: {model_info.likes}")

        # Calculate size
        if hasattr(model_info, 'siblings') and model_info.siblings:
            total_size = sum(
                getattr(file, 'size', 0)
                for file in model_info.siblings
            )
            size_gb = total_size / (1024**3)
            print(f"💾 Size: {size_gb:.2f} GB")

        print("\n⬇️  Downloading...")

        # Download model
        local_path = snapshot_download(
            repo_id=model_id,
            cache_dir=str(CACHE_DIR),
            token=TOKEN,
            resume_download=True
        )

        print(f"\n✅ Download complete!")
        print(f"📁 Model path: {local_path}")

        # Create symlink in MODELS directory
        org, name = model_id.split('/')
        symlink_dir = MODELS_DIR / org
        symlink_dir.mkdir(parents=True, exist_ok=True)

        symlink_path = symlink_dir / name
        if not symlink_path.exists():
            symlink_path.symlink_to(local_path)
            print(f"🔗 Symlink created: {symlink_path}")

        print("\n💡 Usage example:")
        print(f"""
from mlx_lm import load, generate

model, tokenizer = load("{model_id}")
response = generate(model, tokenizer, prompt="Hello!", max_tokens=100)
print(response)
        """)

        return True

    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_downloaded():
    """List already downloaded models"""
    print("\n📦 DOWNLOADED MODELS:\n")

    if not CACHE_DIR.exists():
        print("   No models downloaded yet.")
        return

    # Look for models in cache
    models_found = []
    for item in CACHE_DIR.rglob("*.safetensors"):
        # Get model path
        rel_path = item.relative_to(CACHE_DIR)
        parts = rel_path.parts

        if len(parts) >= 3:
            org = parts[0]
            name = parts[1]
            model_id = f"{org}/{name}"
            if model_id not in models_found:
                models_found.append(model_id)

                # Get size
                size_bytes = sum(
                    f.stat().st_size
                    for f in (CACHE_DIR / org / name).rglob("*")
                    if f.is_file()
                )
                size_gb = size_bytes / (1024**3)

                print(f"   ✓ {model_id} ({size_gb:.2f} GB)")

    if not models_found:
        print("   No models found in cache.")
    else:
        print(f"\n   Total: {len(models_found)} models")

def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <model_id>         Download a model")
        print(f"  {sys.argv[0]} --list            List downloaded models")
        print(f"  {sys.argv[0]} --recommended     Show recommended models")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--list":
        list_downloaded()
    elif arg == "--recommended":
        show_recommended()
    elif arg.startswith("--"):
        print(f"Unknown option: {arg}")
        sys.exit(1)
    else:
        # Download model
        model_id = arg
        success = download_model(model_id)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
