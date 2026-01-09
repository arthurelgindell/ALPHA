#!/usr/bin/env python3
"""
Production LinkedIn Carousel - 2026 Workforce Transformation
Generates complete carousel with custom images for every slide
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from create_carousel import CarouselGenerator, Slide

def generate_production_carousel():
    """
    Create production-quality carousel with images on every slide
    Topic: 2026 Workforce Transformation / AI Skills Premium
    """

    generator = CarouselGenerator()

    print("\n" + "="*60)
    print("🎬 PRODUCTION CAROUSEL GENERATION")
    print("="*60)
    print("\nTopic: 2026 Workforce Transformation")
    print("Style: Hyper-photorealistic futuristic themes")
    print("Branding: Subtle 'Arthur Dell' product placement")
    print("Model: FLUX.1 [dev] - Maximum quality (30 steps)")
    print("="*60 + "\n")

    # Step 1: Generate images with embedded branding
    print("🎨 STEP 1: Generating Images with Arthur Dell Branding\n")

    prompts = [
        # Slide 1: Cover - Corporate minimal professional
        "Modern minimalist corporate boardroom with floor-to-ceiling windows overlooking futuristic city skyline at golden hour, sleek conference table with holographic displays showing 'Workforce 2026' data, small elegant brass nameplate on table reading 'Arthur Dell', professional lighting, hyper-photorealistic, 8k quality, cinematic composition, 1:1 aspect ratio optimized",

        # Slide 2: 56% Premium - AI research environment
        "Cutting-edge AI research laboratory with data visualization walls displaying earnings growth charts and '56% Premium' metrics, young diverse professional in business attire analyzing holographic financial projections, subtle book spine visible on desk reading 'Arthur Dell - AI Economics', warm professional lighting, hyper-photorealistic, 8k quality, futuristic corporate aesthetic, 1:1 square format",

        # Slide 3: 7.5 Hours - Productivity/Time theme
        "Futuristic executive workspace with dual curved holographic displays showing automated workflow dashboards and time analytics, professional reviewing productivity metrics with AI assistant interface, elegant desk with subtle engraved pen holder 'Arthur Dell 2026', natural light through smart glass windows, hyper-photorealistic, 8k quality, productivity focus, 1:1 format",

        # Slide 4: Time Advantage - Holographic interface
        "Professional using advanced holographic interface displaying time-saving automation tools and calendar optimization, futuristic office environment with ambient blue lighting, small holographic badge on desk showing 'Arthur Dell - Productivity Systems', clean modern aesthetic, hyper-photorealistic, 8k quality, technology focus, square composition",

        # Slide 5: The Gap - Training contrast
        "Corporate training center with large projection screen displaying AI skills gap statistics '42% vs 17%', mostly empty modern chairs suggesting low attendance, single concerned executive in foreground reviewing training materials, whiteboard in background with subtle signature 'Arthur Dell 2026' in corner, dramatic professional lighting, hyper-photorealistic, 8k quality, documentary style, 1:1 format",

        # Slide 6: The Choice - Decision moment
        "Split composition showing two paths: left side with traditional manual work environment (dim, outdated), right side with AI-augmented workspace (bright, futuristic), professional standing at crossroads decision point, subtle digital signage reading 'Arthur Dell - Choose Your Path', cinematic lighting contrast, hyper-photorealistic, 8k quality, metaphorical storytelling, square format",

        # Slide 7: Quote background - Inspirational subtle
        "Minimalist modern office with soft golden hour lighting through large windows, inspirational workspace with subtle motivational elements, elegant desk setup with leather notebook embossed 'Arthur Dell', clean professional aesthetic, bokeh background effect, hyper-photorealistic, 8k quality, aspirational mood, 1:1 composition",

        # Slide 8: Closing - Professional connection
        "Modern professional networking lounge with comfortable seating and warm ambient lighting, diverse executives in confident poses suggesting collaboration and connection, subtle digital display on wall reading 'Connect with Arthur Dell', welcoming atmosphere, hyper-photorealistic, 8k quality, relationship-focused, square format optimized for LinkedIn"
    ]

    print(f"Generating {len(prompts)} high-quality images...")
    print("This will take approximately 12-15 minutes (90s per image)\n")

    # Generate with FLUX.1 dev for maximum quality
    image_paths = generator.generate_images(
        prompts=prompts,
        model="dev",  # Maximum quality
        preset="1:1"   # Square format for LinkedIn
    )

    print("\n✅ All images generated successfully!\n")

    # Step 2: Create carousel with all images
    print("="*60)
    print("🎨 STEP 2: Assembling Carousel")
    print("="*60 + "\n")

    slides = [
        # Slide 1: Cover with branded image
        Slide(
            layout="message",  # Use image layout for cover
            title="2026 Workforce Transformation",
            subtitle="The AI Skills Premium",
            image=str(image_paths[0]),
            overlay=True
        ),

        # Slide 2: 56% Premium
        Slide(
            layout="message",
            title="AI-Skilled Workers Earn 56% More",
            subtitle="The premium is real and growing",
            image=str(image_paths[1]),
            overlay=True
        ),

        # Slide 3: 7.5 Hours Stat - with image background
        Slide(
            layout="message",
            title="7.5 Hours Saved Every Week",
            subtitle="AI-fluent professionals gain nearly a full workday",
            image=str(image_paths[2]),
            overlay=True
        ),

        # Slide 4: Time Advantage detail
        Slide(
            layout="message",
            title="The Compounding Effect",
            subtitle="390 hours per year. 7,800 hours over 20 years.",
            image=str(image_paths[3]),
            overlay=True
        ),

        # Slide 5: The Gap
        Slide(
            layout="message",
            title="The Preparation Gap",
            subtitle="42% expect change. Only 17% are preparing.",
            image=str(image_paths[4]),
            overlay=True
        ),

        # Slide 6: The Choice
        Slide(
            layout="message",
            title="Two Paths Diverge",
            subtitle="Which future will you choose?",
            image=str(image_paths[5]),
            overlay=True
        ),

        # Slide 7: Quote with subtle background
        Slide(
            layout="message",
            title="The future belongs to those who prepare today",
            subtitle="",  # No subtitle for quote
            image=str(image_paths[6]),
            overlay=True
        ),

        # Slide 8: Closing CTA with connection image
        Slide(
            layout="message",
            title="Ready to Lead the Transformation?",
            subtitle="Connect with Arthur Dell",
            image=str(image_paths[7]),
            overlay=True
        )
    ]

    # Create the carousel
    pdf_path = generator.create_carousel(
        slides=slides,
        title="2026 Workforce Transformation - Production",
        output_filename="2026_workforce_transformation_PRODUCTION.pdf"
    )

    # Final summary
    print("\n" + "="*60)
    print("🎉 PRODUCTION CAROUSEL COMPLETE")
    print("="*60)
    print(f"\n✅ PDF: {pdf_path}")
    print(f"✅ Images: {len(image_paths)} high-quality images generated")
    print(f"✅ Slides: {len(slides)} slides with strategic branding")
    print(f"✅ Quality: FLUX.1 [dev] - 30 steps per image")
    print(f"✅ Format: 1080x1080 LinkedIn optimized")
    print("\n📊 Image locations:")
    for i, img in enumerate(image_paths, 1):
        print(f"   {i}. {img.name}")

    print("\n🚀 Next steps:")
    print("   1. Review PDF: open " + str(pdf_path))
    print("   2. Upload to LinkedIn")
    print("   3. Track engagement metrics")
    print("\n" + "="*60 + "\n")

    return pdf_path, image_paths


if __name__ == "__main__":
    pdf_path, images = generate_production_carousel()
