#!/usr/bin/env python3
"""
Create STORY-DRIVEN infographics for LinkedIn Episode 1.
Not spec sheets - narrative frames that tell WHY this matters.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets/infographics_v3")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1080, 1920

COLORS = {
    "bg": "#0d0d0d",
    "white": "#ffffff",
    "amber": "#d4a373",
    "teal": "#4ecdc4",
    "nvidia": "#76b900",
    "gray": "#888888",
    "dark_gray": "#333333",
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def draw_text_centered(draw, text, y, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=hex_to_rgb(color))

def draw_text_left(draw, text, x, y, font, color):
    draw.text((x, y), text, font=font, fill=hex_to_rgb(color))


# ============================================
# CARD 1: THE HOOK - Problem/Opportunity
# ============================================
def create_hook_card():
    """Opening hook - the problem we're solving"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Main question
    big_font = get_font(64, bold=True)
    draw_text_centered(draw, "WHAT IF YOU COULD", 400, big_font, COLORS["gray"])
    draw_text_centered(draw, "RUN GPT-4 CLASS AI", 490, big_font, COLORS["white"])
    draw_text_centered(draw, "ON YOUR DESK?", 580, big_font, COLORS["amber"])

    # Divider
    draw.rectangle([300, 720, 780, 724], fill=hex_to_rgb(COLORS["amber"]))

    # Pain points crossed out
    pain_font = get_font(42)
    pains = [
        "No cloud latency",
        "No API costs",
        "No rate limits",
        "No data leaving your network",
    ]

    for i, pain in enumerate(pains):
        y = 820 + i * 70
        draw_text_centered(draw, pain, y, pain_font, COLORS["teal"])

    # Bottom teaser
    teaser_font = get_font(36)
    draw_text_centered(draw, "This is my $40K local AI setup.", 1200, teaser_font, COLORS["gray"])

    img.save(OUTPUT_DIR / "01_hook.png")
    print("✅ 01_hook.png - The problem/opportunity")


# ============================================
# CARD 2: MAC STUDIO - What it enables
# ============================================
def create_mac_studio_story():
    """Mac Studio - focused on what it DOES, not specs"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(56, bold=True)
    draw_text_centered(draw, "MAC STUDIO M3 ULTRA", 300, title_font, COLORS["white"])

    subtitle_font = get_font(36)
    draw_text_centered(draw, "× 2 UNITS", 380, subtitle_font, COLORS["amber"])

    # The capability statement (the story)
    draw.rectangle([100, 500, 980, 504], fill=hex_to_rgb(COLORS["amber"]))

    story_font = get_font(48, bold=True)
    draw_text_centered(draw, "RUNS DEEPSEEK R1 671B", 580, story_font, COLORS["white"])
    draw_text_centered(draw, "LOCALLY", 650, story_font, COLORS["amber"])

    # What that means
    meaning_font = get_font(36)
    draw_text_centered(draw, "The largest open-source reasoning model", 780, meaning_font, COLORS["gray"])
    draw_text_centered(draw, "17-18 tokens/second", 840, meaning_font, COLORS["teal"])

    # Key enablers (minimal specs, contextualized)
    draw.rectangle([100, 960, 980, 964], fill=hex_to_rgb(COLORS["dark_gray"]))

    spec_label = get_font(32)
    spec_value = get_font(48, bold=True)

    # Left: Memory
    draw_text_left(draw, "Combined Memory", 120, 1020, spec_label, COLORS["gray"])
    draw_text_left(draw, "1 TB UNIFIED", 120, 1070, spec_value, COLORS["amber"])
    draw_text_left(draw, "Fits 671B parameters", 120, 1140, spec_label, COLORS["gray"])

    # Right: Performance
    draw_text_left(draw, "GPU Cores", 580, 1020, spec_label, COLORS["gray"])
    draw_text_left(draw, "160 CORES", 580, 1070, spec_value, COLORS["amber"])
    draw_text_left(draw, "Real-time inference", 580, 1140, spec_label, COLORS["gray"])

    img.save(OUTPUT_DIR / "02_mac_studio_story.png")
    print("✅ 02_mac_studio_story.png - Mac Studio capability")


# ============================================
# CARD 3: DGX SPARK - What it enables
# ============================================
def create_dgx_spark_story():
    """DGX Spark - focused on what it DOES"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(56, bold=True)
    draw_text_centered(draw, "NVIDIA DGX SPARK", 300, title_font, COLORS["nvidia"])

    subtitle_font = get_font(36)
    draw_text_centered(draw, "GB10 BLACKWELL", 380, subtitle_font, COLORS["white"])

    # The capability statement
    draw.rectangle([100, 500, 980, 504], fill=hex_to_rgb(COLORS["nvidia"]))

    story_font = get_font(48, bold=True)
    draw_text_centered(draw, "FINE-TUNE 70B MODELS", 580, story_font, COLORS["white"])
    draw_text_centered(draw, "ON YOUR DESK", 650, story_font, COLORS["nvidia"])

    # What that means
    meaning_font = get_font(36)
    draw_text_centered(draw, "Train custom AI without cloud costs", 780, meaning_font, COLORS["gray"])
    draw_text_centered(draw, "Inference up to 200B parameters", 840, meaning_font, COLORS["teal"])

    # Key enablers
    draw.rectangle([100, 960, 980, 964], fill=hex_to_rgb(COLORS["dark_gray"]))

    spec_label = get_font(32)
    spec_value = get_font(48, bold=True)

    # Left
    draw_text_left(draw, "AI Performance", 120, 1020, spec_label, COLORS["gray"])
    draw_text_left(draw, "1 PETAFLOP", 120, 1070, spec_value, COLORS["nvidia"])
    draw_text_left(draw, "Training-grade compute", 120, 1140, spec_label, COLORS["gray"])

    # Right
    draw_text_left(draw, "Memory", 580, 1020, spec_label, COLORS["gray"])
    draw_text_left(draw, "128 GB", 580, 1070, spec_value, COLORS["nvidia"])
    draw_text_left(draw, "Unified GPU memory", 580, 1140, spec_label, COLORS["gray"])

    img.save(OUTPUT_DIR / "03_dgx_spark_story.png")
    print("✅ 03_dgx_spark_story.png - DGX Spark capability")


# ============================================
# CARD 4: THE PAYOFF - Combined power
# ============================================
def create_payoff_card():
    """The combined value - what you GET"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(72, bold=True)
    draw_text_centered(draw, "TOGETHER", 350, title_font, COLORS["white"])

    # Big number
    big_font = get_font(120, bold=True)
    draw_text_centered(draw, "1.5+ PFLOPS", 500, big_font, COLORS["teal"])

    subtitle = get_font(42)
    draw_text_centered(draw, "of local AI processing power", 650, subtitle, COLORS["gray"])

    # Divider
    draw.rectangle([200, 750, 880, 754], fill=hex_to_rgb(COLORS["teal"]))

    # Value props - what you GAIN
    gain_font = get_font(48, bold=True)
    gains = [
        ("INSTANT", "responses, no API latency"),
        ("UNLIMITED", "inference, no per-token costs"),
        ("PRIVATE", "data never leaves your network"),
        ("YOURS", "full control, forever"),
    ]

    y = 850
    label_font = get_font(32)
    for keyword, description in gains:
        draw_text_centered(draw, keyword, y, gain_font, COLORS["amber"])
        draw_text_centered(draw, description, y + 55, label_font, COLORS["gray"])
        y += 130

    img.save(OUTPUT_DIR / "04_payoff.png")
    print("✅ 04_payoff.png - The combined payoff")


# ============================================
# CARD 5: CTA - What's next
# ============================================
def create_cta_card():
    """Call to action - follow for more"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # The transformation
    before_font = get_font(42)
    draw_text_centered(draw, "FROM: Paying per token, waiting for APIs", 500, before_font, COLORS["gray"])

    arrow_font = get_font(72, bold=True)
    draw_text_centered(draw, "↓", 600, arrow_font, COLORS["amber"])

    after_font = get_font(48, bold=True)
    draw_text_centered(draw, "TO: Unlimited local AI power", 700, after_font, COLORS["teal"])

    # Divider
    draw.rectangle([200, 850, 880, 854], fill=hex_to_rgb(COLORS["amber"]))

    # CTA
    cta_font = get_font(56, bold=True)
    draw_text_centered(draw, "THIS IS EPISODE 1", 950, cta_font, COLORS["white"])

    series_font = get_font(36)
    draw_text_centered(draw, "The Hardware Foundation", 1030, series_font, COLORS["amber"])

    # Button
    draw.rectangle([300, 1150, 780, 1250], fill=hex_to_rgb(COLORS["teal"]))
    button_font = get_font(48, bold=True)
    draw.text((370, 1175), "FOLLOW FOR MORE", font=button_font, fill=hex_to_rgb(COLORS["bg"]))

    # Series preview
    preview_font = get_font(28)
    episodes = [
        "Ep 2: The AI Frameworks",
        "Ep 3: The Development Stack",
        "Ep 4: The Automation Layer",
    ]
    for i, ep in enumerate(episodes):
        draw_text_centered(draw, ep, 1350 + i * 50, preview_font, COLORS["gray"])

    img.save(OUTPUT_DIR / "05_cta.png")
    print("✅ 05_cta.png - Call to action")


def main():
    print("=" * 60)
    print("Creating STORY-DRIVEN Infographics")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 60)

    create_hook_card()
    create_mac_studio_story()
    create_dgx_spark_story()
    create_payoff_card()
    create_cta_card()

    print("-" * 60)
    print("✅ Story-driven infographics complete")
    print("\nNARRATIVE ARC:")
    print("  1. Hook: What if you could run GPT-4 class AI on your desk?")
    print("  2. Mac Studio: Runs DeepSeek R1 671B locally")
    print("  3. DGX Spark: Fine-tune 70B models on your desk")
    print("  4. Payoff: 1.5+ PFLOPS, instant, unlimited, private, yours")
    print("  5. CTA: Follow for the full 8-episode series")


if __name__ == "__main__":
    main()
