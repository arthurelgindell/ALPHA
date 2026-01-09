# Image Generation for World-Class Media Production

**Status:** ✅ Deployed and tested
**Primary Model:** FLUX.1 [schnell] (Apache 2.0, commercial-friendly)
**Framework:** mflux (MLX-optimized for Apple Silicon)
**Resolutions:** Up to 2K (2176x960 max)

---

## 🚀 Quick Start

### Generate an image (simple):
```bash
python3 scripts/generate_image.py "a cinematic sunset over mountains" --preset 16:9-large
```

### Generate an image (custom):
```bash
python3 scripts/generate_image.py "professional product photography" \
  --width 1920 --height 1088 \
  --steps 4 \
  --model schnell \
  --seed 42
```

---

## 📐 Available Presets

| Preset | Resolution | Aspect Ratio | Use Case |
|--------|------------|--------------|----------|
| `1:1` | 1024x1024 | Square | Social media, profile pics |
| `4:3` | 1152x896 | Standard | Traditional displays |
| `3:2` | 1216x832 | Photo | Camera format |
| `16:9` | 1344x768 | HD | Standard widescreen |
| **`16:9-large`** ⭐ | 1920x1088 | Full HD | **Production media** |
| `21:9` | 1536x640 | Ultrawide | Cinematic |
| `21:9-large` | 2176x960 | Ultra-wide | Epic landscapes |
| `9:16` | 768x1344 | Vertical | Mobile/Stories |
| `4:5` | 1024x1280 | Portrait | Instagram posts |

---

## 🎨 Models Available

### FLUX.1 [schnell] (DEFAULT) ⭐
- **Speed:** Fast (15-30 seconds)
- **Quality:** Good (production-ready)
- **License:** Apache 2.0 (commercial use OK)
- **Steps:** 2-4 (recommended: 4)
- **Best for:** Production, commercial projects, fast iteration

```bash
python3 scripts/generate_image.py "prompt" --model schnell --steps 4
```

### FLUX.1 [dev] (MAXIMUM QUALITY)
- **Speed:** Medium (60-90 seconds)
- **Quality:** Excellent (#2 on leaderboards)
- **License:** Non-commercial (requires license for commercial use)
- **Steps:** 20-50 (recommended: 25)
- **Best for:** Highest quality requirements, non-commercial projects

```bash
python3 scripts/generate_image.py "prompt" --model dev --steps 25
```

**Note:** You must accept the license at https://huggingface.co/black-forest-labs/FLUX.1-dev before using this model.

### Z-Image Turbo (ULTRA-FAST)
- **Speed:** Very fast (<3 seconds)
- **Quality:** Excellent (photorealistic)
- **Best for:** Rapid iteration, quick previews

```bash
python3 scripts/generate_image.py "prompt" --model z-image-turbo --steps 8
```

---

## 💡 Prompt Engineering Guide

### Structure of a Great Prompt:
1. **Subject:** What is the main focus?
2. **Style:** What aesthetic or genre?
3. **Quality keywords:** photorealistic, 8k, professional, etc.
4. **Lighting:** natural light, studio lighting, golden hour, etc.
5. **Composition:** close-up, wide shot, aerial view, etc.
6. **Atmosphere:** mood, time of day, weather

### Example Prompts:

**Landscape:**
```
"Epic mountain landscape at golden hour, dramatic clouds,
ultra-wide panorama, professional photography, 8k quality"
```

**Product Photography:**
```
"Professional product photography of a luxury watch on marble surface,
studio lighting, shallow depth of field, commercial quality, 8k"
```

**Portrait:**
```
"Editorial fashion portrait, natural window lighting, soft shadows,
magazine quality, professional photography, high detail"
```

**Architecture:**
```
"Modern minimalist architecture, clean lines, natural light,
architectural photography, professional quality, sharp focus"
```

**Cityscape:**
```
"Cinematic shot of futuristic cityscape at sunset, neon lights
reflecting on wet streets, photorealistic, 8k quality, dramatic composition"
```

---

## ⚙️ Command Line Options

```bash
python3 scripts/generate_image.py PROMPT [OPTIONS]
```

**Options:**
- `--preset PRESET` - Use a resolution preset (see table above)
- `--width WIDTH` - Custom width (must be divisible by 64)
- `--height HEIGHT` - Custom height (must be divisible by 64)
- `--model MODEL` - Model choice: schnell (default), dev, z-image-turbo
- `--steps STEPS` - Generation steps (default: 4 for schnell, 25 for dev)
- `--seed SEED` - Seed for reproducible results
- `--quantize BITS` - Quantization: 3, 4 (default), 5, 6, 8
- `--output PATH` - Custom output path

---

## 🧪 Testing

### Run comprehensive test suite:
```bash
python3 scripts/test_flux_generations.py
```

This will generate test images at 6 different resolutions:
- 1080p 16:9 (Full HD)
- 1024x1024 (Square)
- 1024x1280 (Portrait 4:5)
- 2176x960 (Ultra-wide 21:9)
- 768x1344 (Vertical 9:16)
- 1344x768 (Standard HD)

Results saved to: `/Users/arthurdell/ARTHUR/generated_images/tests/`

---

## 📊 Performance Benchmarks

**Apple M2/M3 (16-32GB RAM):**
- 1024x1024 @ 4 steps: ~15-20 seconds
- 1920x1088 @ 4 steps: ~20-30 seconds
- 2176x960 @ 4 steps: ~25-35 seconds

**Quality vs Speed:**
- **Steps 4:** Fast, good quality (recommended for schnell)
- **Steps 20:** Good quality, faster than 25
- **Steps 25:** Balanced (recommended for dev)
- **Steps 30:** High quality, slower
- **Steps 50:** Maximum quality, very slow

---

## 🔧 Troubleshooting

### Issue: "Out of memory" error
**Solutions:**
1. Use 4-bit quantization (default): `--quantize 4`
2. Reduce resolution: use `--preset 16:9` instead of `16:9-large`
3. Close other applications
4. Restart terminal to clear memory

### Issue: Generation too slow
**Solutions:**
1. Use FLUX.1 [schnell] instead of [dev]: `--model schnell`
2. Reduce steps: `--steps 4`
3. Use smaller resolution for testing
4. Consider Z-Image Turbo for ultra-fast generation

### Issue: Quality not meeting expectations
**Solutions:**
1. Switch to FLUX.1 [dev]: `--model dev --steps 25`
2. Increase steps: `--steps 30` or `--steps 50`
3. Refine prompt with more specific keywords
4. Add quality keywords: "photorealistic", "8k", "professional"
5. Try different seeds: `--seed 42`, `--seed 123`, etc.

### Issue: Wrong aspect ratio
**Remember:** FLUX requires dimensions divisible by 64

**Correct:**
- 1920x1088 ✓ (not 1920x1080)
- 1024x1024 ✓
- 1344x768 ✓

**Incorrect:**
- 1920x1080 ✗ (use 1088 instead)
- 1000x1000 ✗ (use 1024 instead)

### Issue: License error for FLUX.1 [dev]
**Solution:**
- Accept the license at: https://huggingface.co/black-forest-labs/FLUX.1-dev
- Or use FLUX.1 [schnell] (Apache 2.0, no restrictions): `--model schnell`

---

## 💻 System Requirements

### Minimum:
- **CPU:** Apple M1 chip or better
- **RAM:** 8GB
- **Storage:** ~40GB free (for models and cache)
- **OS:** macOS with Apple Silicon

### Recommended:
- **CPU:** Apple M2 Pro/Max or better
- **RAM:** 16GB+
- **Storage:** ~60GB free
- **OS:** Latest macOS

### Optimal:
- **CPU:** Apple M3 Max/Ultra or M4/M5
- **RAM:** 32GB+
- **Storage:** ~100GB free SSD
- **OS:** Latest macOS

---

## 📁 File Locations

**Generated Images:**
- Default: `/Users/arthurdell/ARTHUR/generated_images/`
- Test suite: `/Users/arthurdell/ARTHUR/generated_images/tests/`

**Scripts:**
- Generation: `/Users/arthurdell/ARTHUR/scripts/generate_image.py`
- Testing: `/Users/arthurdell/ARTHUR/scripts/test_flux_generations.py`

**Models:**
- Cache: `~/.cache/huggingface/hub/`
- FLUX.1 schnell: ~31GB
- FLUX.1 dev: ~24-31GB

**Configuration:**
- HF Token: `/Users/arthurdell/ARTHUR/.env`

---

## 📚 Additional Resources

- **Full model catalog:** See `MLX_MODELS_CATALOG.md`
- **mflux documentation:** https://github.com/filipstrand/mflux
- **FLUX.1 model cards:** https://huggingface.co/black-forest-labs
- **Black Forest Labs:** https://bfl.ai/

---

## 🎯 Common Workflows

### Quick preview (5-10 seconds):
```bash
python3 scripts/generate_image.py "test prompt" --preset 1:1 --steps 4
```

### Production image (15-30 seconds):
```bash
python3 scripts/generate_image.py "detailed prompt" --preset 16:9-large --steps 4
```

### Maximum quality (60-90 seconds):
```bash
python3 scripts/generate_image.py "detailed prompt" \
  --preset 16:9-large \
  --model dev \
  --steps 30 \
  --quantize 8
```

### Batch generation (use seed for variations):
```bash
for i in {1..10}; do
  python3 scripts/generate_image.py "prompt" \
    --preset 16:9-large \
    --seed $i
done
```

### Reproducible generation:
```bash
python3 scripts/generate_image.py "prompt" \
  --preset 16:9-large \
  --seed 42 \
  --model schnell \
  --steps 4
```

---

**✅ System Status:** Deployed and operational
**📅 Last Updated:** 2025-12-30
**🎨 Total Generated:** Check `generated_images/` directory

For questions or issues, see `MLX_MODELS_CATALOG.md` or check the mflux documentation.
