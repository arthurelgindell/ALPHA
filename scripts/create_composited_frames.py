#!/usr/bin/env python3
"""
Create composited frames: Product photos + text overlays burned in.
Text ON the footage, not black screens.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path

OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets/composited_frames")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets")

# Target size: 9:16 vertical
WIDTH, HEIGHT = 1080, 1920

COLORS = {
    "white": "#ffffff",
    "amber": "#d4a373",
    "teal": "#4ecdc4",
    "nvidia": "#76b900",
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def load_and_crop_to_vertical(image_path):
    """Load image and crop/resize to 9:16 vertical"""
    img = Image.open(image_path)

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    orig_w, orig_h = img.size
    target_ratio = WIDTH / HEIGHT  # 9:16 = 0.5625
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        # Image is wider - crop sides
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        # Image is taller - crop top/bottom
        new_h = int(orig_w / target_ratio)
        top = (orig_h - new_h) // 2
        img = img.crop((0, top, orig_w, top + new_h))

    # Resize to target
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    return img

def add_gradient_overlay(img, opacity=0.4):
    """Add dark gradient at bottom for text readability"""
    gradient = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    # Bottom gradient (for lower-third text)
    for y in range(HEIGHT // 2, HEIGHT):
        alpha = int(255 * opacity * (y - HEIGHT // 2) / (HEIGHT // 2))
        draw.rectangle([0, y, WIDTH, y + 1], fill=(0, 0, 0, alpha))

    # Top gradient (subtle)
    for y in range(0, HEIGHT // 4):
        alpha = int(255 * opacity * 0.3 * (HEIGHT // 4 - y) / (HEIGHT // 4))
        draw.rectangle([0, y, WIDTH, y + 1], fill=(0, 0, 0, alpha))

    img = img.convert('RGBA')
    return Image.alpha_composite(img, gradient)

def draw_text_with_shadow(draw, text, x, y, font, color, shadow_color=(0,0,0), shadow_offset=3):
    """Draw text with drop shadow for readability"""
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color + (180,))
    # Main text
    draw.text((x, y), text, font=font, fill=hex_to_rgb(color) + (255,))

def draw_centered_text(draw, text, y, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw_text_with_shadow(draw, text, x, y, font, color)


# ============================================
# FRAME 1: Hook - on Mac Studio hero
# ============================================
def create_frame_hook():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "apple" / "mac_studio_hero_4k.jpg")
    bg = add_gradient_overlay(bg, opacity=0.6)
    draw = ImageDraw.Draw(bg)

    # Darken slightly for text contrast
    enhancer = ImageEnhance.Brightness(bg)
    bg = enhancer.enhance(0.7)
    draw = ImageDraw.Draw(bg)

    big_font = get_font(56, bold=True)
    draw_centered_text(draw, "WHAT IF YOU COULD RUN", 700, big_font, "white")
    draw_centered_text(draw, "GPT-4 CLASS AI", 780, big_font, "amber")
    draw_centered_text(draw, "ON YOUR DESK?", 860, big_font, "white")

    small_font = get_font(36)
    draw_centered_text(draw, "No cloud. No API costs. Full control.", 1000, small_font, "teal")

    bg.convert('RGB').save(OUTPUT_DIR / "01_hook_composite.jpg", quality=95)
    print("✅ 01_hook_composite.jpg")


# ============================================
# FRAME 2: Mac Studio capability
# ============================================
def create_frame_mac_studio():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "apple" / "mac_studio_lifestyle_4k.jpg")
    bg = add_gradient_overlay(bg, opacity=0.5)
    draw = ImageDraw.Draw(bg)

    # Upper text
    title_font = get_font(48, bold=True)
    draw_centered_text(draw, "MAC STUDIO M3 ULTRA × 2", 200, title_font, "white")

    # Main capability - lower third
    big_font = get_font(52, bold=True)
    draw_centered_text(draw, "RUNS DEEPSEEK R1 671B", 1450, big_font, "white")
    draw_centered_text(draw, "LOCALLY", 1520, big_font, "amber")

    spec_font = get_font(36)
    draw_centered_text(draw, "1TB unified memory · 160 GPU cores", 1620, spec_font, "teal")
    draw_centered_text(draw, "17-18 tokens/second", 1680, spec_font, "white")

    bg.convert('RGB').save(OUTPUT_DIR / "02_mac_studio_composite.jpg", quality=95)
    print("✅ 02_mac_studio_composite.jpg")


# ============================================
# FRAME 3: Mac Studio specs overlay
# ============================================
def create_frame_mac_specs():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "apple" / "mac_studio_ports_4k.jpg")
    bg = add_gradient_overlay(bg, opacity=0.5)
    draw = ImageDraw.Draw(bg)

    # Specs as lower third
    big_font = get_font(72, bold=True)
    draw_centered_text(draw, "1 TB", 1400, big_font, "amber")

    label_font = get_font(36)
    draw_centered_text(draw, "UNIFIED MEMORY", 1490, label_font, "white")

    spec_font = get_font(42, bold=True)
    draw_centered_text(draw, "160 GPU CORES COMBINED", 1620, spec_font, "teal")

    bg.convert('RGB').save(OUTPUT_DIR / "03_mac_specs_composite.jpg", quality=95)
    print("✅ 03_mac_specs_composite.jpg")


# ============================================
# FRAME 4: DGX Spark hero
# ============================================
def create_frame_dgx_hero():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "nvidia" / "dgx_product_1.jpg")
    bg = add_gradient_overlay(bg, opacity=0.5)
    draw = ImageDraw.Draw(bg)

    # Title at top
    title_font = get_font(52, bold=True)
    draw_centered_text(draw, "NVIDIA DGX SPARK", 200, title_font, "nvidia")

    # Main capability
    big_font = get_font(52, bold=True)
    draw_centered_text(draw, "TRAIN YOUR OWN", 1450, big_font, "white")
    draw_centered_text(draw, "AI MODELS", 1520, big_font, "nvidia")

    spec_font = get_font(36)
    draw_centered_text(draw, "Fine-tune 70B parameters on your desk", 1620, spec_font, "teal")

    bg.convert('RGB').save(OUTPUT_DIR / "04_dgx_hero_composite.jpg", quality=95)
    print("✅ 04_dgx_hero_composite.jpg")


# ============================================
# FRAME 5: DGX Spark specs
# ============================================
def create_frame_dgx_specs():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "nvidia" / "dgx_product_2.jpg")
    bg = add_gradient_overlay(bg, opacity=0.5)
    draw = ImageDraw.Draw(bg)

    big_font = get_font(72, bold=True)
    draw_centered_text(draw, "1 PETAFLOP", 1400, big_font, "nvidia")

    label_font = get_font(36)
    draw_centered_text(draw, "AI COMPUTE POWER", 1490, label_font, "white")

    spec_font = get_font(42, bold=True)
    draw_centered_text(draw, "128 GB UNIFIED MEMORY", 1620, spec_font, "teal")

    bg.convert('RGB').save(OUTPUT_DIR / "05_dgx_specs_composite.jpg", quality=95)
    print("✅ 05_dgx_specs_composite.jpg")


# ============================================
# FRAME 6: Combined power
# ============================================
def create_frame_combined():
    # Use setup shot showing workspace
    bg = load_and_crop_to_vertical(ASSETS_DIR / "apple" / "mac_studio_setup_4k.jpg")
    bg = add_gradient_overlay(bg, opacity=0.6)
    draw = ImageDraw.Draw(bg)

    title_font = get_font(48, bold=True)
    draw_centered_text(draw, "THE POWER DUO", 250, title_font, "white")

    big_font = get_font(80, bold=True)
    draw_centered_text(draw, "1.5+ PFLOPS", 1350, big_font, "teal")

    label_font = get_font(36)
    draw_centered_text(draw, "OF LOCAL AI PROCESSING", 1460, label_font, "white")

    benefits_font = get_font(32, bold=True)
    draw_centered_text(draw, "INSTANT · UNLIMITED · PRIVATE · YOURS", 1600, benefits_font, "amber")

    bg.convert('RGB').save(OUTPUT_DIR / "06_combined_composite.jpg", quality=95)
    print("✅ 06_combined_composite.jpg")


# ============================================
# FRAME 7: CTA
# ============================================
def create_frame_cta():
    bg = load_and_crop_to_vertical(ASSETS_DIR / "nvidia" / "dgx_product_3.jpg")
    bg = add_gradient_overlay(bg, opacity=0.6)
    draw = ImageDraw.Draw(bg)

    # Main message
    big_font = get_font(52, bold=True)
    draw_centered_text(draw, "FULL CONTROL", 1300, big_font, "white")
    draw_centered_text(draw, "OVER YOUR AI", 1370, big_font, "white")

    # CTA
    cta_font = get_font(48, bold=True)
    draw_centered_text(draw, "FOLLOW →", 1520, cta_font, "teal")

    series_font = get_font(32)
    draw_centered_text(draw, "Episode 1 of 8: The Hardware Foundation", 1650, series_font, "amber")

    bg.convert('RGB').save(OUTPUT_DIR / "07_cta_composite.jpg", quality=95)
    print("✅ 07_cta_composite.jpg")


def main():
    print("=" * 60)
    print("Creating Composited Frames (Text ON Footage)")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 60)

    create_frame_hook()
    create_frame_mac_studio()
    create_frame_mac_specs()
    create_frame_dgx_hero()
    create_frame_dgx_specs()
    create_frame_combined()
    create_frame_cta()

    print("-" * 60)
    print("✅ All composited frames created")
    print("   Text burned into product photography")
    print("   9:16 vertical orientation")


if __name__ == "__main__":
    main()
