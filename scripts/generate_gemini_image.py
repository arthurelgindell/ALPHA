#!/usr/bin/env python3
"""
Gemini Image Generation - Production Workflow (2025)
Uses Gemini 3 Pro Image (Nano Banana Pro) with SCALS framework
"""

import os
import base64
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types

# Configuration
API_KEY = "AIzaSyDwcBEOsPkFYAodM2RlngMGmx8kEKwkkuI"
MODEL_NAME = "gemini-3-pro-image-preview"  # Nano Banana Pro
OUTPUT_DIR = Path("/Users/arthurdell/ARTHUR/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_image(prompt: str, output_filename: str = None, aspect_ratio: str = "16:9") -> Path:
  """
  Generate image using Gemini 3 Pro Image with SCALS-optimized prompts.

  Args:
    prompt: Professional creative brief using SCALS framework
    output_filename: Optional custom filename
    aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)

  Returns:
    Path to generated image
  """
  # Configure Gemini client
  client = genai.Client(api_key=API_KEY)

  print(f"🎨 Generating image with Gemini 3 Pro Image...")
  print(f"📐 Aspect ratio: {aspect_ratio}")
  print(f"📝 Prompt: {prompt[:150]}...")

  try:
    # Generate image
    response = client.models.generate_content(
      model=MODEL_NAME,
      contents=prompt,
      config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
          aspect_ratio=aspect_ratio
        ),
        tools=[types.Tool(google_search=types.GoogleSearch())]  # Enable grounding
      )
    )

    # Save image
    if output_filename is None:
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      output_filename = f"gemini_{timestamp}.png"

    output_path = OUTPUT_DIR / output_filename

    # Extract image from response
    if response.candidates and len(response.candidates) > 0:
      candidate = response.candidates[0]
      if candidate.content and candidate.content.parts:
        for part in candidate.content.parts:
          if hasattr(part, 'inline_data') and part.inline_data:
            # Save image data
            with open(output_path, 'wb') as f:
              f.write(part.inline_data.data)
            print(f"✅ Image saved: {output_path}")
            print(f"📊 Size: {output_path.stat().st_size / 1024:.1f} KB")
            return output_path

    print(f"⚠️ No image in response")
    if hasattr(response, 'text'):
      print(f"Response text: {response.text[:200]}")
    return None

  except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    return None

def create_scals_prompt(
  subject: str,
  composition: str,
  action: str,
  location: str,
  style: str,
  branding: str = ""
) -> str:
  """
  Construct professional prompt using SCALS framework.
  Optimized for Gemini 3 Pro Image reasoning capabilities.
  """
  prompt = f"""Professional photography brief for high-fidelity image generation:

SUBJECT: {subject}

COMPOSITION: {composition}

ACTION: {action}

LOCATION: {location}

STYLE: {style}"""

  if branding:
    prompt += f"\n\nBRANDING: {branding}"

  prompt += """

CRITICAL RENDERING REQUIREMENTS:
- Generate at MAXIMUM resolution with pixel-perfect clarity
- UI elements (interfaces, logos, text) must be RAZOR-SHARP and perfectly legible
- Text on screens must render with perfect anti-aliasing and high contrast
- Logos (Claude, Gemini, NotebookLM) must be crisp vector-quality with no pixelation
- Screen content must be tack-sharp in critical focus, not soft or blurred
- All text must be readable at full resolution - no fuzzy or pixelated characters
- Interface elements should render as if photographed from high-resolution displays
- Commercial photography quality with professional retouching standards
- No compression artifacts, no pixelation, no soft UI elements"""

  return prompt

# ============================================================================
# HYPER-PHOTOREALISTIC PROMPTS: 2026 AI Tools Leadership
# ============================================================================

TEST_PROMPTS = {
  "gemini_claude_2026_champions": {
    "prompt": create_scals_prompt(
      subject="A stunning dual-display setup centered on a sleek walnut executive desk with bookmatched grain patterns and brass inlay details. Left display shows Claude's elegant dark-mode interface with the distinctive Claude.ai orange logo clearly visible in the top-left corner, displaying a complex code refactoring session with syntax-highlighted Python code and intelligent suggestions appearing in real-time with perfect text clarity. Right display shows Gemini's vibrant multimodal interface with the colorful Gemini sparkle logo prominently displayed, showing image generation in progress at 73%, scientific data visualization with crisp charts, and multiple chat threads active simultaneously with crystal-clear text rendering. Between the displays sits a tactile mechanical keyboard with custom keycaps, a precision-machined titanium pen holder containing Montblanc pens, and a small succulent in a matte black ceramic pot. A premium Italian leather portfolio lies partially open showing embossed pages with strategic planning notes written in sharp, legible handwriting. A minimalist water glass with condensation droplets catches the light. In the bottom foreground corner, subtly out of focus, a frosted glass business card holder shows 'ARTHUR DELL' cards with the text barely readable but present.",
      composition="Shot with cinema-grade 50mm lens at f/1.8 creating razor-sharp center focus on both displays with smooth focus falloff to desk edges, captured from a straight-on eye-level angle optimized for square format, balanced centered composition with both interfaces equally prominent and filling the frame, professional commercial photography with meticulous attention to screen clarity, text legibility, and material rendering, displays angled 10 degrees toward camera ensuring zero glare and maximum UI visibility with perfect text sharpness",
      action="Both AI interfaces are mid-workflow showing active intelligence - Claude's cursor blinking as code suggestions populate with smooth text animations, all code text rendering in perfect monospace font clarity, Gemini's image generation progress bar at 73% with preview thumbnail evolving in real-time showing tack-sharp interface elements, notification badges subtly pulsing on both interfaces indicating new insights ready, subtle screen glow illuminating keyboard creating authentic interaction lighting, displays emanating soft light that interacts with desk surface creating realistic screen light bounce and reflection on walnut grain",
      location="Photographed in a corner office during golden hour with floor-to-ceiling windows 8 feet behind the desk creating natural rim lighting and subtle lens flare, primary illumination from a large north-facing window camera-left providing soft wrapping light at 5600K color temperature ensuring even illumination across both screens, subtle warm practical light from a Artemide Tolomeo desk lamp at 3200K positioned camera-right creating dimensional modeling on desk objects, background showing soft bokeh of downtown San Francisco skyline with Salesforce Tower identifiable but dreamlike in the upper portion of the frame, environmental atmosphere suggesting late afternoon productivity peak, professional studio-quality lighting balanced between natural and practical sources creating authentic depth",
      style="Hyper-photorealistic commercial photography aesthetic inspired by Apple's 'Shot on iPhone' campaign and Wired magazine editorial spreads, captured on medium format digital with Hasselblad color science emphasizing accurate skin tones and material fidelity, Kodak Portra 400 color grading with rich but natural saturation, subtle film halation on highlights, professional retouching maintaining texture authenticity while ensuring all UI text and logos are pixel-perfect sharp, tack-sharp hero elements (screens) with creamy bokeh transition to background, cinematic color grading with warm-cool contrast between screen light and natural light, aspirational yet authentic mood suggesting peak professional performance and technological sophistication, CRITICAL: all screen text, logos, and UI elements must render with magazine-quality clarity",
      branding="'ARTHUR DELL' appears only on business cards visible through frosted glass holder in bottom foreground corner (slightly out of focus but text still readable), creating subliminal brand association without disrupting the AI tools narrative - product placement philosophy: brand presence felt rather than announced"
    ),
    "aspect_ratio": "1:1"
  },

  "notebooklm_meeting_room": {
    "prompt": create_scals_prompt(
      subject="An intimate strategy meeting in a modern glass-walled conference room with three diverse professionals gathered around a live-edge walnut conference table with black steel legs, composed in a square frame. The focal professional is presenting from a 16-inch MacBook Pro with NotebookLM's interface prominently displayed - the distinctive NotebookLM logo clearly visible at the top with its notebook and sparkle icon, showing an auto-generated audio summary waveform visualization with crystal-clear text labels, source document thumbnails arranged in a knowledge graph with perfectly legible titles, and AI-synthesized insights with highlighted key findings rendered in sharp, readable text. A large 4K display screen mounted on the charcoal felt-paneled wall behind them mirrors the presentation with annotations appearing in real-time, all text elements rendering with magazine-quality clarity. The table surface holds scattered research papers with highlighted sections and readable text, moleskine notebooks with visible sketches and notes, a carafe of ice water with condensation, brushed stainless steel water tumblers, and wireless presentation clickers. On the window ledge at the top of the frame, a small indoor plant adds organic warmth. In the background through the glass wall at the top of the square composition, blurred silhouettes of other professionals are softly visible. A subtle detail: a coffee cup on the table's near edge has a barely-visible embossed 'AD' pattern in the ceramic texture.",
      composition="Captured with cinematic 35mm lens at f/2.2 optimized for square format, positioned at seated eye-level (approximately 4.5 feet height) creating viewer immersion as if participating in the meeting, centered composition with NotebookLM interface as the hero element in the middle of the frame, three professionals balanced symmetrically around the square composition, moderate depth of field keeping the NotebookLM screen in critical tack-sharp focus with all UI text perfectly legible while conference room environment falls into gentle bokeh at edges, professional documentary-editorial photography style with authentic moment capture, laptop screen angled 12 degrees toward camera ensuring zero glare and maximum interface legibility with pixel-perfect text rendering",
      action="The presenter's hand is gesturing toward the NotebookLM screen mid-explanation - caught in natural motion pointing to the 'source graph' feature with connecting lines between research documents that are sharp and clear, the other two professionals are leaning in with engaged body language showing authentic collaboration and discovery, one colleague is taking notes in a leather journal with visible pen movement, NotebookLM's interface shows the audio summary feature with waveform visualization and crisp text labels, subtle screen glow illuminating the presenter's face showing authentic interaction lighting, background display shows the same content with perfect clarity at larger scale, demonstrating the AI's real-time organization of research materials",
      location="Located in a modern downtown high-rise office building's premium conference room on approximately the 25th floor, photographed during late morning with abundant natural illumination streaming through floor-to-ceiling glass walls providing even, soft ambient fill light at 6000K ensuring perfect screen visibility without washout, additional practical lighting from recessed LED panels in the architectural soffit providing 4000K accent illumination creating subtle dimensional modeling on faces without harsh shadows, background showing soft-focus cityscape with glass office towers visible at the top of the square frame, interior design features charcoal acoustic panels, white oak architectural details, and brushed aluminum fixtures creating sophisticated minimalist aesthetic, professional architectural photography lighting quality with perfect balance between natural and artificial sources optimized for screen clarity",
      style="Hyper-photorealistic corporate editorial photography aesthetic inspired by Harvard Business Review feature articles and Dropbox's 'Creative Work' campaign, shot on full-frame mirrorless with Sony color science emphasizing natural skin tones across diverse complexions and authentic material rendering, Cinestill 800T color grading creating slight warm-cool interplay between screen light and natural daylight with subtle halation on window highlights, professional color grading maintaining documentary authenticity while elevating production value, CRITICAL: razor-sharp focus on NotebookLM interface with all text, logos, and UI elements rendering at maximum clarity as if photographed from a retina display, gentle bokeh transition on background elements, environmental portraiture style that balances technology showcase with human collaboration narrative, mood suggesting breakthrough moment when AI-augmented research synthesis creates tangible business insight, all screen elements must be magazine-quality sharp",
      branding="Extremely subtle: 'AD' embossed pattern in ceramic glaze on coffee cup at table near edge (barely perceptible, appears decorative rather than logo), creating whisper-level brand presence that rewards close observation without interrupting narrative - branding philosophy: ambient presence rather than placement"
    ),
    "aspect_ratio": "1:1"
  }
}

def main():
  """Test Gemini image generation with hyper-photorealistic AI leadership prompts."""
  print("=" * 80)
  print("🚀 GEMINI 3 PRO IMAGE - HYPER-PHOTOREALISTIC GENERATION")
  print("   Model: Nano Banana Pro (gemini-3-pro-image-preview)")
  print("   Concepts:")
  print("     1. Gemini & Claude: 2026 AI Champions")
  print("     2. NotebookLM: Meeting Room Strategy Session")
  print("   Brand: ARTHUR DELL (Whisper-level Subtle Placement)")
  print("   Framework: SCALS + Professional Photography Language")
  print("=" * 80)
  print()

  results = {}

  for name, config in TEST_PROMPTS.items():
    print(f"\n📸 Generating: {name}")
    print("-" * 80)

    output_path = generate_image(
      config["prompt"],
      f"arthur_dell_{name}.png",
      config["aspect_ratio"]
    )
    results[name] = output_path

    if output_path:
      print(f"✅ SUCCESS: {output_path}")
    else:
      print(f"❌ FAILED: {name}")

    print()

  print("=" * 80)
  print("📊 GENERATION SUMMARY")
  print("=" * 80)

  success_count = sum(1 for path in results.values() if path)
  print(f"✅ Generated: {success_count}/{len(results)} images")
  print()

  for name, path in results.items():
    status = "✅" if path else "❌"
    print(f"{status} {name}")
    if path:
      print(f"   → {path}")

  print()
  print("🎯 Next Steps:")
  print("   1. Review images in:", OUTPUT_DIR)
  print("   2. Verify 'ARTHUR DELL' brand placement quality and readability")
  print("   3. Check SCALS framework effectiveness (composition, lighting, style)")
  print("   4. Validate AI interface visibility (Claude & Gemini)")
  print("   5. Iterate prompts if needed for production use")
  print()
  print("💰 Cost Optimization:")
  print("   - Using 2K resolution (balance of quality vs cost)")
  print("   - Google Search grounding enabled for accuracy")
  print("   - Free tier: 500 images/day")

if __name__ == "__main__":
  main()
