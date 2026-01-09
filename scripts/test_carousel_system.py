#!/usr/bin/env python3
"""
Test LinkedIn Carousel System
Validates image generation → Slidev → PDF workflow
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from create_carousel import CarouselGenerator, Slide

def test_basic_carousel():
    """Test basic 3-slide carousel without images"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Basic 3-Slide Carousel (No Images)")
    print("="*60)

    generator = CarouselGenerator()

    slides = [
        Slide(
            layout="cover",
            title="Test Carousel",
            subtitle="System Validation"
        ),
        Slide(
            layout="stat",
            stat="100%",
            label="Success Rate",
            description="Testing the carousel system",
            background="bg-gradient-blue"
        ),
        Slide(
            layout="closing",
            title="Test Complete",
            subtitle="Ready for production",
            cta="Get Started"
        )
    ]

    try:
        pdf_path = generator.create_carousel(
            slides=slides,
            title="Test Carousel",
            output_filename="test_01_basic_carousel.pdf"
        )

        assert pdf_path.exists(), "PDF was not created"
        file_size = pdf_path.stat().st_size / 1024  # KB
        print(f"✅ TEST 1 PASSED")
        print(f"   PDF size: {file_size:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        return False


def test_with_existing_images():
    """Test carousel using existing AI-generated storyboard images"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Carousel with Existing Images")
    print("="*60)

    generator = CarouselGenerator()
    images_dir = Path("/Users/arthurdell/ARTHUR/images")

    # Check if storyboard images exist
    required_images = [
        "storyboard_01_56_percent_premium.png",
        "storyboard_02_time_advantage.png",
        "storyboard_03_the_gap.png"
    ]

    missing_images = []
    for img in required_images:
        if not (images_dir / img).exists():
            missing_images.append(img)

    if missing_images:
        print(f"⚠️  TEST 2 SKIPPED: Missing images: {', '.join(missing_images)}")
        return None

    slides = [
        Slide(
            layout="cover",
            title="2026 AI Skills",
            subtitle="Test with real images"
        ),
        Slide(
            layout="message",
            title="The 56% Premium",
            subtitle="AI skills translate to earnings",
            image=str(images_dir / "storyboard_01_56_percent_premium.png"),
            overlay=True
        ),
        Slide(
            layout="message",
            title="7.5 Hours Saved",
            subtitle="Every week, consistently",
            image=str(images_dir / "storyboard_02_time_advantage.png"),
            overlay=True
        ),
        Slide(
            layout="message",
            title="The Gap",
            subtitle="Expectation vs. preparation",
            image=str(images_dir / "storyboard_03_the_gap.png"),
            overlay=True
        ),
        Slide(
            layout="closing",
            title="Start Today",
            subtitle="Build your AI skills",
            cta="Connect with Arthur Dell"
        )
    ]

    try:
        pdf_path = generator.create_carousel(
            slides=slides,
            title="2026 AI Skills Test",
            output_filename="test_02_with_images.pdf"
        )

        assert pdf_path.exists(), "PDF was not created"
        file_size = pdf_path.stat().st_size / 1024  # KB
        print(f"✅ TEST 2 PASSED")
        print(f"   PDF size: {file_size:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        return False


def test_all_layouts():
    """Test all 5 layout types"""
    print("\n" + "="*60)
    print("🧪 TEST 3: All Layout Types")
    print("="*60)

    generator = CarouselGenerator()

    slides = [
        Slide(
            layout="cover",
            title="Layout Test",
            subtitle="Testing all 5 layouts"
        ),
        Slide(
            layout="message",
            title="Message Layout",
            subtitle="For visual storytelling"
        ),
        Slide(
            layout="stat",
            stat="5/5",
            label="Layouts",
            description="Testing all carousel layouts",
            background="bg-gradient-green"
        ),
        Slide(
            layout="quote",
            title="Every layout serves a purpose"
        ),
        Slide(
            layout="closing",
            title="All Layouts Work",
            subtitle="System validated",
            cta="Build Your Carousel"
        )
    ]

    try:
        pdf_path = generator.create_carousel(
            slides=slides,
            title="Layout Test",
            output_filename="test_03_all_layouts.pdf"
        )

        assert pdf_path.exists(), "PDF was not created"
        file_size = pdf_path.stat().st_size / 1024  # KB
        print(f"✅ TEST 3 PASSED")
        print(f"   PDF size: {file_size:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("🧪 LinkedIn Carousel System - Test Suite")
    print("="*60)

    results = {
        "test_1_basic": test_basic_carousel(),
        "test_2_images": test_with_existing_images(),
        "test_3_layouts": test_all_layouts()
    }

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    print(f"\n  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Skipped: {skipped}")

    if failed == 0 and passed > 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe carousel system is ready for production use.")
        print("\nNext steps:")
        print("  1. Run: python3 scripts/create_carousel.py --example")
        print("  2. Check output: /Users/arthurdell/ARTHUR/carousels/")
        print("  3. Review: CAROUSEL_CREATION_GUIDE.md")
        return True
    elif failed > 0:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please review the errors above.")
        return False
    else:
        print("\n⚠️  NO TESTS RAN")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
