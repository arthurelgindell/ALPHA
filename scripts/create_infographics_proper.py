#!/usr/bin/env python3
"""
Create proper infographics for LinkedIn Episode 1 using Pillow.
NO AI image generation - just clean, readable typography.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/Volumes/STUDIO/VIDEO/linkedin_series/stock_assets/infographics_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Canvas size (9:16 vertical for LinkedIn)
WIDTH, HEIGHT = 1080, 1920

# Design system colors
COLORS = {
    "bg": "#1a1a1a",           # Deep charcoal
    "white": "#f5f5f5",        # Off-white text
    "amber": "#d4a373",        # Amber gold accent
    "teal": "#4ecdc4",         # Electric teal
    "nvidia": "#76b900",       # NVIDIA green
    "gray": "#666666",         # Secondary text
}

def hex_to_rgb(hex_color):
    """Convert hex to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    """Load a good system font"""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()

def draw_centered_text(draw, text, y, font, color):
    """Draw text centered horizontally"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=hex_to_rgb(color))
    return bbox[3] - bbox[1]  # Return height

def create_mac_studio_spec():
    """Mac Studio M3 Ultra specification card"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(72, bold=True)
    draw_centered_text(draw, "MAC STUDIO", 200, title_font, COLORS["white"])

    subtitle_font = get_font(48, bold=True)
    draw_centered_text(draw, "M3 ULTRA", 290, subtitle_font, COLORS["amber"])

    # Horizontal line
    draw.rectangle([200, 380, 880, 384], fill=hex_to_rgb(COLORS["amber"]))

    # Specs
    spec_font = get_font(42, bold=True)
    value_font = get_font(64, bold=True)

    specs = [
        ("UNIFIED MEMORY", "512 GB", COLORS["amber"]),
        ("GPU CORES", "80", COLORS["amber"]),
        ("CPU CORES", "32", COLORS["white"]),
        ("NEURAL ENGINE", "32-CORE", COLORS["white"]),
        ("MEMORY BANDWIDTH", "819 GB/s", COLORS["teal"]),
    ]

    y_start = 480
    for i, (label, value, color) in enumerate(specs):
        y = y_start + i * 180
        # Label (smaller, gray)
        draw_centered_text(draw, label, y, spec_font, COLORS["gray"])
        # Value (larger, colored)
        draw_centered_text(draw, value, y + 55, value_font, color)

    # Footer
    footer_font = get_font(36)
    draw_centered_text(draw, "× 2 UNITS = 1TB UNIFIED MEMORY", 1600, footer_font, COLORS["amber"])
    draw_centered_text(draw, "160 GPU CORES COMBINED", 1660, footer_font, COLORS["amber"])

    # Save
    out_path = OUTPUT_DIR / "mac_studio_spec_card.png"
    img.save(out_path, "PNG")
    print(f"✅ {out_path.name}")
    return out_path

def create_dgx_spark_spec():
    """NVIDIA DGX Spark specification card"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(72, bold=True)
    draw_centered_text(draw, "DGX SPARK", 200, title_font, COLORS["nvidia"])

    subtitle_font = get_font(48, bold=True)
    draw_centered_text(draw, "GB10 BLACKWELL", 290, subtitle_font, COLORS["white"])

    # Horizontal line
    draw.rectangle([200, 380, 880, 384], fill=hex_to_rgb(COLORS["nvidia"]))

    # Specs
    spec_font = get_font(42, bold=True)
    value_font = get_font(64, bold=True)

    specs = [
        ("UNIFIED MEMORY", "128 GB", COLORS["nvidia"]),
        ("AI PERFORMANCE", "1 PFLOP", COLORS["amber"]),
        ("ARCHITECTURE", "BLACKWELL", COLORS["white"]),
        ("FORM FACTOR", "DESKTOP", COLORS["white"]),
        ("CONNECTIVITY", "USB-C / ETH", COLORS["teal"]),
    ]

    y_start = 480
    for i, (label, value, color) in enumerate(specs):
        y = y_start + i * 180
        draw_centered_text(draw, label, y, spec_font, COLORS["gray"])
        draw_centered_text(draw, value, y + 55, value_font, color)

    # Footer
    footer_font = get_font(36)
    draw_centered_text(draw, "TRAIN 200B PARAMETER MODELS", 1600, footer_font, COLORS["nvidia"])
    draw_centered_text(draw, "FINE-TUNE 70B LOCALLY", 1660, footer_font, COLORS["nvidia"])

    out_path = OUTPUT_DIR / "dgx_spark_spec_card.png"
    img.save(out_path, "PNG")
    print(f"✅ {out_path.name}")
    return out_path

def create_power_duo_card():
    """Combined power comparison card"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(80, bold=True)
    draw_centered_text(draw, "THE POWER DUO", 180, title_font, COLORS["white"])

    # Horizontal line
    draw.rectangle([200, 300, 880, 304], fill=hex_to_rgb(COLORS["amber"]))

    # Left column: Mac Studio
    col_title_font = get_font(48, bold=True)
    spec_font = get_font(36)
    value_font = get_font(48, bold=True)

    # Mac Studio side
    draw.text((100, 400), "MAC STUDIO", font=col_title_font, fill=hex_to_rgb(COLORS["white"]))
    draw.text((100, 460), "M3 ULTRA × 2", font=spec_font, fill=hex_to_rgb(COLORS["gray"]))

    mac_specs = [
        ("Memory", "1 TB"),
        ("GPU Cores", "160"),
        ("Performance", "~0.5 PFLOP"),
    ]

    for i, (label, value) in enumerate(mac_specs):
        y = 540 + i * 80
        draw.text((100, y), label, font=spec_font, fill=hex_to_rgb(COLORS["gray"]))
        draw.text((100, y + 35), value, font=value_font, fill=hex_to_rgb(COLORS["amber"]))

    # Vertical divider
    draw.rectangle([535, 400, 545, 900], fill=hex_to_rgb(COLORS["gray"]))

    # DGX Spark side
    draw.text((580, 400), "DGX SPARK", font=col_title_font, fill=hex_to_rgb(COLORS["nvidia"]))
    draw.text((580, 460), "GB10 BLACKWELL", font=spec_font, fill=hex_to_rgb(COLORS["gray"]))

    dgx_specs = [
        ("Memory", "128 GB"),
        ("Architecture", "Blackwell"),
        ("Performance", "1.0 PFLOP"),
    ]

    for i, (label, value) in enumerate(dgx_specs):
        y = 540 + i * 80
        draw.text((580, y), label, font=spec_font, fill=hex_to_rgb(COLORS["gray"]))
        draw.text((580, y + 35), value, font=value_font, fill=hex_to_rgb(COLORS["nvidia"]))

    # Combined stats
    draw.rectangle([100, 950, 980, 954], fill=hex_to_rgb(COLORS["teal"]))

    combined_font = get_font(56, bold=True)
    draw_centered_text(draw, "COMBINED POWER", 1020, combined_font, COLORS["white"])

    big_font = get_font(96, bold=True)
    draw_centered_text(draw, "1.5+ PETAFLOPS", 1120, big_font, COLORS["teal"])

    # Value props
    props = [
        "NO CLOUD LATENCY",
        "NO API COSTS",
        "FULL CONTROL",
    ]

    prop_font = get_font(42, bold=True)
    for i, prop in enumerate(props):
        draw_centered_text(draw, prop, 1350 + i * 70, prop_font, COLORS["amber"])

    # Footer
    footer_font = get_font(36)
    draw_centered_text(draw, "LOCAL AI INFRASTRUCTURE", 1700, footer_font, COLORS["gray"])

    out_path = OUTPUT_DIR / "power_duo_comparison.png"
    img.save(out_path, "PNG")
    print(f"✅ {out_path.name}")
    return out_path

def create_title_card():
    """Opening title card"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Main title
    title_font = get_font(120, bold=True)
    draw_centered_text(draw, "THE", 700, title_font, COLORS["gray"])
    draw_centered_text(draw, "FOUNDATION", 840, title_font, COLORS["white"])

    # Subtitle
    subtitle_font = get_font(48)
    draw_centered_text(draw, "Episode 1: Hardware", 1050, subtitle_font, COLORS["amber"])

    # Horizontal accent line
    draw.rectangle([340, 1150, 740, 1158], fill=hex_to_rgb(COLORS["amber"]))

    # Series name
    series_font = get_font(36)
    draw_centered_text(draw, "THE AI-POWERED PROFESSIONAL STACK", 1250, series_font, COLORS["gray"])

    out_path = OUTPUT_DIR / "title_card.png"
    img.save(out_path, "PNG")
    print(f"✅ {out_path.name}")
    return out_path

def create_cta_card():
    """Closing CTA card"""
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(COLORS["bg"]))
    draw = ImageDraw.Draw(img)

    # Main message
    title_font = get_font(72, bold=True)
    draw_centered_text(draw, "FULL CONTROL", 700, title_font, COLORS["white"])
    draw_centered_text(draw, "OVER YOUR AI", 800, title_font, COLORS["white"])

    # Value props
    prop_font = get_font(48, bold=True)
    props = [
        ("NO CLOUD", COLORS["amber"]),
        ("NO API COSTS", COLORS["amber"]),
        ("NO LIMITS", COLORS["amber"]),
    ]

    for i, (prop, color) in enumerate(props):
        draw_centered_text(draw, prop, 980 + i * 70, prop_font, color)

    # CTA
    draw.rectangle([300, 1250, 780, 1350], fill=hex_to_rgb(COLORS["teal"]))
    cta_font = get_font(56, bold=True)
    draw.text((380, 1270), "FOLLOW →", font=cta_font, fill=hex_to_rgb(COLORS["bg"]))

    # Series info
    series_font = get_font(36)
    draw_centered_text(draw, "Episode 1 of 8", 1450, series_font, COLORS["gray"])
    draw_centered_text(draw, "The AI-Powered Professional Stack", 1510, series_font, COLORS["gray"])

    out_path = OUTPUT_DIR / "cta_card.png"
    img.save(out_path, "PNG")
    print(f"✅ {out_path.name}")
    return out_path

def main():
    print("=" * 60)
    print("Creating Proper Infographics (Pillow - No AI)")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print("-" * 60)

    create_title_card()
    create_mac_studio_spec()
    create_dgx_spark_spec()
    create_power_duo_card()
    create_cta_card()

    print("-" * 60)
    print("✅ All infographics created with readable text")

if __name__ == "__main__":
    main()
