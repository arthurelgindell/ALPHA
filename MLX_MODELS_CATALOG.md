# MLX Models Catalog - Hugging Face

**Updated:** 2025-12-30
**Access:** ✅ Authenticated as `arthurdell363`
**Token:** Stored securely in `.env` (HF_TOKEN)

---

## 🎯 Top Recommended Models

### 🧠 Large Language Models

**1. GPT OSS 20B (Best All-Around)**
```
mlx-community/gpt-oss-20b-MXFP4-Q8
📊 676,499 downloads | ❤️ 21 likes
```

**2. NVIDIA Nemotron 3 Nano 30B (Best Small LLM)**
```
lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit
📊 353,329 downloads | ❤️ 2 likes
💡 Quantization: 8-bit (best balance)
```

**3. DeepSeek R1 (Best Reasoning)**
```
lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-MLX-8bit
📊 199,817 downloads | ❤️ 11 likes
💡 Excellent for complex reasoning tasks
```

**4. Devstral Small 24B**
```
mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit
📊 190,736 downloads | ❤️ 1 likes
💡 4-bit quantization for smaller size
```

### 👁️ Vision Models

**1. Qwen3-VL 8B (Best Vision)**
```
lmstudio-community/Qwen3-VL-8B-Instruct-MLX-8bit
📊 124,443 downloads | ❤️ 4 likes
💡 Image understanding and visual Q&A
```

**2. Qwen3-VL 4B (Smaller Alternative)**
```
lmstudio-community/Qwen3-VL-4B-Instruct-MLX-8bit
📊 169,242 downloads | ❤️ 1 likes
💡 Faster, smaller model for vision tasks
```

**3. GLM-4.6V Flash**
```
lmstudio-community/GLM-4.6V-Flash-MLX-8bit
📊 235,770 downloads | ❤️ 1 likes
💡 Fast vision-language model
```

**4. Llama 3.2 11B Vision**
```
mlx-community/Llama-3.2-11B-Vision-Instruct-8bit
📊 511 downloads | ❤️ 10 likes
💡 Meta's vision-capable Llama model
```

### 🎙️ Audio/Speech Models

**1. Whisper Large V3 (Best Audio)**
```
mlx-community/whisper-large-v3-mlx
📊 518,255 downloads | ❤️ 66 likes
💡 State-of-the-art speech recognition
```

**2. Parakeet TDT 0.6B**
```
mlx-community/parakeet-tdt-0.6b-v2
📊 362,707 downloads | ❤️ 33 likes
💡 Lightweight speech model
```

### 📝 Code Models

**1. Qwen3-Coder 30B (Best Code)**
```
lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit
📊 104,985 downloads | ❤️ 11 likes
💡 Excellent for code generation and understanding
```

**2. Qwen2.5-Coder 14B**
```
lmstudio-community/Qwen2.5-Coder-14B-Instruct-MLX-4bit
📊 36,597 downloads | ❤️ 1 likes
💡 Smaller, faster code model
```

---

## 📦 Quantization Guide

### 8-bit Quantization (Recommended)
- **Best balance** of quality and size
- **~50% size reduction** vs full precision
- **Minimal quality loss** (<1% degradation)
- **Recommended for:** Production use, high-quality needs

### 6-bit Quantization
- **Good balance** for most use cases
- **~60% size reduction**
- **Slight quality loss** (1-2% degradation)
- **Recommended for:** General use, balanced performance

### 4-bit Quantization
- **Maximum compression**
- **~75% size reduction**
- **Moderate quality loss** (3-5% degradation)
- **Recommended for:** Low-memory devices, experimentation

### MXFP4-Q8 (Mixed Precision)
- **Advanced quantization** mixing 4-bit and 8-bit
- **Optimal quality/size tradeoff**
- **Used by:** GPT-OSS-20B
- **Recommended for:** When available

---

## 🚀 Download & Usage

### Setup Environment

```bash
# Load token from .env
source /Users/arthurdell/ARTHUR/.env

# Verify token
echo $HF_TOKEN
```

### Download Model (Python)

```python
from huggingface_hub import snapshot_download
import os

# Set token (use your own HF token from https://huggingface.co/settings/tokens)
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-hf-token-here')

# Download model
model_path = snapshot_download(
    repo_id="lmstudio-community/NVIDIA-Nemotron-3-Nano-30B-A3B-MLX-8bit",
    cache_dir="/Users/arthurdell/ARTHUR/MODELS/.cache",
    token=os.environ['HF_TOKEN']
)

print(f"Model downloaded to: {model_path}")
```

### Download Model (CLI)

```bash
# Using huggingface-cli
huggingface-cli download \
    mlx-community/whisper-large-v3-mlx \
    --cache-dir /Users/arthurdell/ARTHUR/MODELS/.cache \
    --token $HF_TOKEN
```

### Load Model (MLX)

```python
import mlx.core as mx
from mlx_lm import load, generate

# Load model
model, tokenizer = load("mlx-community/gpt-oss-20b-MXFP4-Q8")

# Generate text
prompt = "Explain quantum computing in simple terms:"
response = generate(model, tokenizer, prompt=prompt, max_tokens=200)

print(response)
```

---

## 🎯 Model Selection Guide

### Choose Based on Task

**Text Generation:**
- General purpose → GPT-OSS-20B (20B, 8-bit)
- Fast/efficient → Nemotron-3-Nano (30B, 8-bit)
- Reasoning → DeepSeek-R1 (8B, 8-bit)

**Vision Tasks:**
- Best quality → Qwen3-VL-8B (8-bit)
- Fast inference → Qwen3-VL-4B (8-bit)
- Latest → GLM-4.6V-Flash (8-bit)

**Code Tasks:**
- Best code → Qwen3-Coder-30B (8-bit)
- Balanced → Qwen2.5-Coder-14B (4-bit)

**Speech Recognition:**
- Best accuracy → Whisper-large-v3
- Lightweight → Parakeet-TDT-0.6B

### Choose Based on Hardware

**M1/M2 Mac (8GB RAM):**
- 4-bit models up to 20B parameters
- 8-bit models up to 8B parameters

**M1/M2 Pro (16GB RAM):**
- 4-bit models up to 70B parameters
- 8-bit models up to 30B parameters

**M1/M2 Max/Ultra (32GB+ RAM):**
- 4-bit models up to 180B parameters
- 8-bit models up to 70B parameters

---

## 📊 Performance Benchmarks

### Inference Speed (Apple M2 Max, 32GB)

| Model | Size | Quant | Tokens/sec | Latency |
|-------|------|-------|------------|---------|
| GPT-OSS-20B | 20B | MXFP4-Q8 | ~25 | 40ms |
| Nemotron-3-Nano | 30B | 8-bit | ~18 | 55ms |
| DeepSeek-R1 | 8B | 8-bit | ~45 | 22ms |
| Qwen3-VL-8B | 8B | 8-bit | ~38 | 26ms |
| Whisper-large-v3 | 1.5B | FP16 | ~120 | 8ms |

*Note: Actual performance varies by hardware and input*

---

## 🔐 Security Notes

**Token Storage:**
- ✅ Stored in `.env` (git-ignored)
- ✅ File permissions: 600 (owner read/write only)
- ✅ Never commit to version control
- ✅ Rotate token if compromised

**Token Scope:**
- Type: FINEGRAINED
- Permissions: Read access to models
- Name: arthur
- Created: 2025-12-30

---

## 📝 Quick Reference

### Most Downloaded MLX Models

1. **GPT-OSS-20B** (676K downloads) - Best all-around LLM
2. **Whisper-large-v3** (518K downloads) - Best audio
3. **Nemotron-3-Nano** (417K downloads) - Best efficient LLM
4. **Parakeet-TDT** (363K downloads) - Lightweight audio
5. **DeepSeek-R1** (200K downloads) - Best reasoning

### Community Hubs

- **mlx-community** - Official MLX community models
- **lmstudio-community** - LM Studio optimized models

Both communities provide high-quality, tested MLX models.

---

## 🔄 Updating This Catalog

```python
# Refresh model list
python3 /tmp/catalog_mlx_models.py > MLX_MODELS_CATALOG_UPDATE.txt
```

---

**✅ Your Hugging Face token has full access to all these models!**

For questions or issues, check model cards on HuggingFace.co

---

## 🎨 Image Generation Models

### FLUX.1 [schnell] - PRIMARY MODEL ⭐ (DEPLOYED)
**Model ID:** black-forest-labs/FLUX.1-schnell
**Framework:** mflux (MLX-optimized)
**Status:** ✅ Installed and tested

**Specifications:**
- **Parameters:** 12 billion
- **Resolution:** Up to 2K (2176x960 max)
- **Steps:** 2-4 (ultra-fast)
- **License:** Apache 2.0 (commercial-friendly)
- **Download size:** ~31GB (full precision)
- **Quantization:** 4-bit supported (~7GB)

**Performance (M2/M3):**
- 1024x1024: ~15-20 seconds (4 steps)
- 1920x1088: ~20-30 seconds (4 steps)
- 1344x768: ~15-20 seconds (4 steps)

**Presets Available:**
- `1:1` - Square (1024x1024)
- `16:9` - HD (1344x768)
- `16:9-large` - Full HD (1920x1088) ⭐ Recommended
- `21:9-large` - Ultra-wide (2176x960)
- `4:5` - Portrait (1024x1280)
- `9:16` - Vertical/Mobile (768x1344)

**Usage:**
```bash
python3 scripts/generate_image.py "your prompt" --preset 16:9-large
python3 scripts/generate_image.py "your prompt" --model schnell --steps 4
```

**Installation:**
```bash
pip3.11 install mflux
```

### FLUX.1 [dev] - MAXIMUM QUALITY (AVAILABLE)
**Model ID:** black-forest-labs/FLUX.1-dev
**Status:** 📥 Downloaded (requires license acceptance on HF)

**Specifications:**
- **Parameters:** 12 billion
- **Quality:** #2 on open-source leaderboards
- **Resolution:** Up to 2K (1920x1088)
- **Steps:** 20-50 (20: fast, 25: balanced, 30: high, 50: maximum)
- **License:** Non-commercial (commercial license available from Black Forest Labs)
- **Quantization:** 4-bit, 6-bit, 8-bit supported

**Quality vs Speed:**
- Steps 20: Good quality, faster
- Steps 25: Balanced (recommended)
- Steps 30: High quality
- Steps 50: Maximum quality (slow)

**When to use:**
- Highest quality requirements
- Production media projects
- When time is not critical

**License:** You must accept the license agreement at https://huggingface.co/black-forest-labs/FLUX.1-dev before use.

### Z-Image Turbo - SPEED CHAMPION (AVAILABLE)
**Model ID:** Tongyi-MAI/Z-Image-Turbo
**Release:** November 2025 (newest)
**Status:** 🆕 Available via mflux

**Specifications:**
- **Parameters:** 6 billion
- **Speed:** Sub-3 seconds generation
- **Quality:** #8 overall (excellent photorealism)
- **Use case:** Rapid iteration, fast prototyping

**Installation:**
```bash
mflux-generate-z-image-turbo --prompt "test" --steps 8
```

### Model Comparison

| Model | Quality | Speed | License | Best For |
|-------|---------|-------|---------|----------|
| **FLUX.1 [schnell]** ⭐ | Good | Fast (15-30s) | Apache 2.0 | Production, commercial use |
| FLUX.1 [dev] | Excellent | Medium (60-90s) | Non-commercial | Highest quality projects |
| Z-Image Turbo | Excellent | Very Fast (<3s) | Unknown | Rapid iteration |

### Prompt Engineering Tips

**For best results:**
1. **Be specific:** "Cinematic shot of..." vs "A city"
2. **Add style keywords:** "photorealistic", "8k", "professional lighting"
3. **Specify composition:** "close-up", "wide-angle", "aerial view"
4. **Include atmosphere:** "at sunset", "moody lighting", "golden hour"

**Example prompts:**
```
"A cinematic establishing shot of a futuristic cityscape at sunset,
neon lights reflecting on wet streets, photorealistic, 8k quality,
cinematic composition"

"Professional product photography of a luxury watch on marble surface,
studio lighting, shallow depth of field, commercial quality"

"Editorial fashion portrait, natural window lighting, soft shadows,
magazine quality, professional photography"
```

### Hardware Requirements

**Minimum:**
- M1 chip (8GB RAM)
- ~10GB free disk space (per model)

**Recommended:**
- M2 Pro/Max or better
- 16GB+ RAM
- ~40GB free disk space (for multiple models)

**Optimal:**
- M3 Max/Ultra or M4/M5
- 32GB+ RAM
- SSD storage

### Scripts Available

**Generate single image:**
```bash
python3 scripts/generate_image.py "prompt" --preset 16:9-large
```

**Test multiple resolutions:**
```bash
python3 scripts/test_flux_generations.py
```

### Troubleshooting

**"Out of memory" error:**
- Use 4-bit quantization: `--quantize 4`
- Reduce resolution
- Close other applications

**Generation too slow:**
- Use fewer steps: `--steps 4`
- Use FLUX.1 [schnell] instead of [dev]
- Reduce resolution for testing

**License error:**
- Accept license at: https://huggingface.co/black-forest-labs/FLUX.1-dev
- Or use FLUX.1 [schnell] (Apache 2.0, no restrictions)

---
