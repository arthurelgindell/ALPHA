# Veo 3.1 Quick Start - Product Placement Video Generation

**Purpose:** Paid video generation for product placement shots in ARTHUR productions
**Primary Engine:** Local MLX (free, unlimited) | **Secondary:** Veo 3.1 (paid, <10% of content)

---

## Quick Generation

### Option 1: Use Production Script
```bash
python3 /Users/arthurdell/ARTHUR/scripts/generate_veo_video.py
```

Edit the `SUN_DATACENTER_PROMPT` in the script to your prompt, or create custom prompts.

### Option 2: Direct Python Usage
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyDwcBEOsPkFYAodM2RlngMGmx8kEKwkkuI")

# Configure generation
config = types.GenerateVideosConfig(
    durationSeconds=8,
    aspectRatio="16:9"
)

# Generate
operation = client.models.generate_videos(
    model="veo-3.1-fast-generate-preview",  # or "veo-3.1-generate-preview"
    prompt="YOUR DETAILED PROMPT HERE",
    config=config
)

# Wait for completion
import time
while True:
    current_op = client.operations.get(operation)
    if current_op.done:
        break
    time.sleep(10)

# Download
result = current_op.result
video = result.generated_videos[0]
download_url = f"{video.video.download_uri}&key=AIzaSyDwcBEOsPkFYAodM2RlngMGmx8kEKwkkuI"

import requests
response = requests.get(download_url)
with open("output.mp4", "wb") as f:
    f.write(response.content)
```

---

## Prompt Formula (Five-Part)

```
[CINEMATOGRAPHY]: Shot type, camera movement, lens, angle
[SUBJECT]: Detailed description, what/who, materials, specifics
[ACTION]: What's happening, movements, interactions
[CONTEXT]: Environment, location, time, lighting, setting
[STYLE & AMBIANCE]: Aesthetic, mood, color palette, audio

CRITICAL for lighting: Be explicit about light sources and color
- GOOD: "Bright white fluorescent lighting from ceiling panels"
- BAD: "Signature purple lighting bathes the environment" (creates nightclub effect)
```

### Example: Product Placement
```
[CINEMATOGRAPHY]: Close-up dolly shot, 50mm lens at f/2.8, slow push-in

[SUBJECT]: Sleek smartwatch with "ARTHUR DELL" logo engraved on clasp,
sitting on polished walnut desk, stainless steel finish with sapphire crystal

[ACTION]: Watch face lights up showing notification, screen displays
"Meeting in 5 minutes," subtle haptic animation pulse

[CONTEXT]: Modern executive office, natural window light from camera left
at 5600K, warm desk lamp at 3200K from right creating depth, clean
minimal background with blurred bookshelf

[STYLE & AMBIANCE]: Commercial product photography aesthetic, Apple-style
clean and premium, Kodak Portra 400 color grading, aspirational mood.
Audio: Soft notification chime, ambient office sounds very quiet, NO MUSIC.
```

---

## Models & Pricing

| Model | Use Case | Cost/Sec | 8-Sec Cost |
|-------|----------|----------|------------|
| `veo-3.1-fast-generate-preview` | Prototyping, iterations | $0.15 | $1.20 |
| `veo-3.1-generate-preview` | Final production quality | $0.40 | $3.20 |

**Strategy:** Prototype with Fast, finalize with Standard

---

## Common Issues & Solutions

### Issue: Nightclub/Disco Lighting
**Symptom:** Colored ambient lighting instead of professional look
**Fix:** Explicitly state primary light source, add "(NOT environmental lighting)" for colored accents

```
BEFORE: "Purple and orange lighting bathes the room"
AFTER: "Bright white fluorescent ceiling lighting provides primary illumination,
small purple/orange status LEDs provide subtle accent glow (NOT environmental lighting)"
```

### Issue: Download Fails (403/400)
**Solution:** Use `download_uri` not regular `uri`:
```python
download_url = f"{file_obj.download_uri}&key={API_KEY}"  # Correct
# NOT: file_obj.uri  # Wrong
```

### Issue: Rate Limit (429)
**Solution:** Wait 5-10 minutes between bursts of generations

---

## Workflow: Product Placement Integration

1. **Generate base video** with local MLX (free)
2. **Identify placement opportunities** (3-5 second inserts)
3. **Prototype with Veo Fast** ($0.15/sec) - iterate on prompt
4. **Finalize with Veo Standard** ($0.40/sec) - single production shot
5. **Composite in post** - merge with MLX-generated content

**Cost Example:**
- 60-second video, 10 seconds product placement
- MLX: 50 seconds = $0
- Veo Standard: 10 seconds = $4.00
- **Total: $4.00** (vs $24 for entire video on Veo)

---

## File Locations

**Script:** `/Users/arthurdell/ARTHUR/scripts/generate_veo_video.py`
**Output:** `/Users/arthurdell/ARTHUR/videos/`
**Guide:** `/Users/arthurdell/ARTHUR/VEO_3.1_PROMPTING_GUIDE.md` (complete)
**API Key:** Already configured in scripts

---

## Quick Test

```bash
# Generate 8-second test video ($1.20)
python3 /Users/arthurdell/ARTHUR/scripts/generate_veo_video.py

# Check output
ls -lh /Users/arthurdell/ARTHUR/videos/
```

---

**Status:** ✅ Tested and operational (5 Sun Microsystems videos generated)
**Last Updated:** 2026-01-01
