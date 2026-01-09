#!/usr/bin/env python3
"""
Veo 3.1 Video Generation - Production Workflow
For product placement shots only (primary = local MLX)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

# Configuration
API_KEY = "AIzaSyDwcBEOsPkFYAodM2RlngMGmx8kEKwkkuI"
MODEL_NAME = "veo-3.1-fast-generate-preview"  # Start with Fast for testing ($0.15/sec)
OUTPUT_DIR = Path("/Users/arthurdell/ARTHUR/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_video(
  prompt: str,
  output_filename: str = None,
  aspect_ratio: str = "16:9",
  duration: int = 8,
  model: str = "veo-3.1-fast-generate-preview"
) -> Path:
  """
  Generate video using Veo 3.1.

  Args:
    prompt: Cinematic prompt using Five-Part Formula
    output_filename: Optional custom filename
    aspect_ratio: 16:9 (landscape) or 9:16 (portrait)
    duration: 4, 6, or 8 seconds
    model: veo-3.1-fast or veo-3.1-standard

  Returns:
    Path to generated video
  """
  # Configure Gemini client
  client = genai.Client(api_key=API_KEY)

  print(f"🎬 Generating video with {model}...")
  print(f"📐 Aspect ratio: {aspect_ratio}")
  print(f"⏱️  Duration: {duration} seconds")
  print(f"💰 Cost estimate: ${duration * (0.15 if 'fast' in model else 0.40):.2f}")
  print(f"📝 Prompt preview: {prompt[:200]}...")
  print()

  try:
    # Prepare video generation config
    config = types.GenerateVideosConfig(
      durationSeconds=duration,
      aspectRatio=aspect_ratio
      # Note: generateAudio not supported via Gemini API (requires Vertex AI)
    )

    # Generate video
    print("⏳ Submitting generation request...")
    operation = client.models.generate_videos(
      model=model,
      prompt=prompt,  # Prompt goes here, not in config
      config=config
    )

    print(f"⏳ Operation ID: {operation.name}")
    print("⏳ Processing (this may take 1-3 minutes)...")

    # Poll for completion
    import time
    max_wait = 600  # 10 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
      # Get operation status
      current_op = client.operations.get(operation)

      if current_op.done:
        print("✅ Generation complete!")
        response = current_op
        break

      # Wait before next poll
      time.sleep(10)
      elapsed = int(time.time() - start_time)
      print(f"⏳ Still processing... ({elapsed}s elapsed)")
    else:
      raise TimeoutError(f"Video generation timed out after {max_wait}s")

    # Save video
    if output_filename is None:
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      output_filename = f"veo_{timestamp}.mp4"

    output_path = OUTPUT_DIR / output_filename

    # Extract video from response
    if response and hasattr(response, 'result') and response.result:
      result = response.result
      if hasattr(result, 'generated_videos') and result.generated_videos:
        video = result.generated_videos[0]
        if hasattr(video, 'video') and video.video:
          video_obj = video.video
          video_uri = video_obj.uri
          print(f"📥 Downloading from: {video_uri}")

          # Download using the API client's internal request method
          # This maintains proper authentication
          http_request = {
            'url': video_uri,
            'method': 'GET'
          }
          video_data = client._api_client.request(http_request, None, stream=False).content

          # Save video data
          with open(output_path, 'wb') as f:
            f.write(video_data)

          print(f"✅ Video saved: {output_path}")
          print(f"📊 Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
          return output_path

    print(f"⚠️ No video in response")
    print(f"Response: {response}")
    return None

  except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    return None


# ============================================================================
# TEST PROMPT: Sun Microsystems Data Center (REVISED - Fixed Lighting)
# ============================================================================

# ORIGINAL ISSUE: "bathes the environment" created nightclub effect
# FIX: Clean white data center lighting with subtle colored status LEDs only

SUN_DATACENTER_PROMPT = """[CINEMATOGRAPHY]: Slow tracking dolly shot through server corridor, wide shot transitioning to medium, camera height at eye level (5.5 feet), smooth stabilized movement following technician, shallow depth of field on foreground servers with background racks softly bokeh, professional documentary cinematography, 24fps cinematic motion

[SUBJECT]: Male technician in late 30s wearing Sun Microsystems branded polo shirt (purple Sun logo on chest), dark trousers, professional posture, wearing lanyard badge clearly reading "Arthur Dell — Professional Services Leader" with Sun sunburst logo, carrying diagnostic tablet, confident stride

[ACTION]: Technician walks purposefully through endless server corridor, occasionally glancing at server status displays, pauses briefly to check a rack-mounted display showing system metrics, continues walking as camera tracks alongside him, server status LEDs blink in synchronized patterns, subtle heat shimmer rises from cooling exhaust vents

[CONTEXT]: Massive enterprise data center interior, 2007-era Sun Microsystems facility, cathedral-like scale with endless rows of server racks stretching to vanishing point creating dramatic perspective, raised floor with perforated tiles, meticulously organized cable management visible overhead, bright clean white fluorescent lighting from ceiling panels provides primary illumination ensuring professional visibility, server racks feature period-accurate Sun Fire and Sun Blade systems, small purple and orange status LEDs on server fronts provide subtle accent glow (NOT environmental lighting), Sun Microsystems sunburst logos visible on rack badges and server faceplates - iconic purple and red sunburst design, hyper-clean environment suggesting precision engineering

[STYLE & AMBIANCE]: Hyper-photorealistic professional data center documentary aesthetic, inspired by enterprise technology photography and IBM/Sun corporate media from mid-2000s, shot on professional cinema camera with natural color grading emphasizing clean whites and metallic server finishes, subtle purple/orange only from small status LEDs not as ambient wash, lighting is bright and professional (NOT moody or colored), conveys technological cathedral - massive scale meeting precision engineering, mood is corporate confidence and infrastructure power

AUDIO: Deep harmonic server hum creating almost musical drone at 60Hz, layered cooling system airflow (white noise texture), subtle electronic processing sounds and hard drive seeks, technician's footsteps on raised floor panels creating hollow metallic sound, occasional quiet beep from status alerts, NO MUSIC."""

def main():
  """Test Veo 3.1 with Sun Microsystems data center prompt."""
  print("=" * 80)
  print("🎬 VEO 3.1 VIDEO GENERATION TEST")
  print("   Model: veo-3.1-fast (prototyping)")
  print("   Scene: Sun Microsystems Data Center 2007")
  print("   Branding: Arthur Dell (Professional Services Leader)")
  print("   Fix: Toned down lighting (clean white, not nightclub)")
  print("=" * 80)
  print()

  output_path = generate_video(
    SUN_DATACENTER_PROMPT,
    "sun_datacenter_arthur_dell.mp4",
    aspect_ratio="16:9",
    duration=8,
    model="veo-3.1-fast-generate-preview"  # Use Fast for testing
  )

  if output_path:
    print()
    print("=" * 80)
    print("✅ GENERATION COMPLETE")
    print("=" * 80)
    print(f"📹 Video: {output_path}")
    print(f"🎯 Key Changes from Original Prompt:")
    print("   - Primary: Bright white fluorescent lighting (professional)")
    print("   - Accent: Subtle purple/orange from status LEDs ONLY")
    print("   - Removed: 'bathes the environment' and 'colored lighting reflects'")
    print("   - Added: Explicit 'NOT moody or colored' lighting direction")
    print()
    print("💡 If still too colorful, next iteration:")
    print("   - Further emphasize 'clinical white lighting'")
    print("   - Add 'status LEDs barely visible'")
    print("   - Reference specific data center photography")
  else:
    print()
    print("❌ Generation failed - see error above")

if __name__ == "__main__":
  main()
