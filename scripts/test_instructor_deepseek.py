#!/usr/bin/env python3.11
"""
Test Instructor library with DeepSeek V3.1 on RDMA cluster

This script validates structured LLM outputs using production schemas.
Requires DeepSeek V3.1 instance to be running on Exo cluster.

Usage:
    /opt/homebrew/bin/python3.11 scripts/test_instructor_deepseek.py
"""

import sys
import instructor
from openai import OpenAI
from schemas.content_schemas import VideoScript, ImagePrompt, CarouselPlan, SlideContent

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_status(emoji: str, message: str, color: str = RESET):
    """Print formatted status message"""
    print(f"{color}{emoji} {message}{RESET}")


def test_cluster_connection():
    """Test connection to Exo cluster"""
    print_status("🔍", "Testing cluster connection...", BLUE)

    try:
        import requests
        response = requests.get("http://localhost:52415/cluster/status", timeout=5)
        data = response.json()

        node_count = len(data.get('nodes', []))
        if node_count == 0:
            print_status("⚠️", "WARNING: Cluster shows 0 nodes", YELLOW)
            print("   This means RDMA cluster is not active")
            print("   DeepSeek V3.1 (378GB) requires 2-node cluster")
            return False
        elif node_count == 1:
            print_status("⚠️", f"WARNING: Only {node_count} node detected", YELLOW)
            print("   Expected: 2 nodes (ALPHA + BETA)")
            return False
        else:
            print_status("✅", f"Cluster active: {node_count} nodes", GREEN)
            return True

    except Exception as e:
        print_status("❌", f"Failed to connect to Exo: {e}", RED)
        return False


def init_instructor_client():
    """Initialize Instructor client connected to Exo cluster"""
    print_status("🔧", "Initializing Instructor client...", BLUE)

    try:
        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:52415/v1", api_key="not-needed"),
            mode=instructor.Mode.JSON
        )
        print_status("✅", "Instructor client ready", GREEN)
        return client
    except Exception as e:
        print_status("❌", f"Failed to initialize client: {e}", RED)
        return None


def test_image_prompt(client):
    """Test ImagePrompt schema"""
    print_status("🎨", "Testing ImagePrompt generation...", BLUE)

    try:
        result = client.chat.completions.create(
            model="deepseek-v3.1-4bit",
            response_model=ImagePrompt,
            messages=[{
                "role": "user",
                "content": "Create an image prompt for a professional product photo of an Arthur Dell branded smartwatch on a minimalist desk"
            }],
            max_tokens=1000
        )

        print_status("✅", "ImagePrompt generated successfully", GREEN)
        print(f"\n{BLUE}Generated Prompt:{RESET}")
        print(f"  Subject: {result.subject}")
        print(f"  Style: {result.style}")
        print(f"  Aspect Ratio: {result.aspect_ratio.value}")
        print(f"\n{BLUE}FLUX.1 Prompt:{RESET}")
        print(f"  {result.to_flux_prompt()}")
        print(f"\n{BLUE}Resolution:{RESET} {result.get_resolution()}")
        return True

    except Exception as e:
        print_status("❌", f"ImagePrompt test failed: {e}", RED)
        return False


def test_video_script(client):
    """Test VideoScript schema"""
    print_status("🎬", "Testing VideoScript generation...", BLUE)

    try:
        result = client.chat.completions.create(
            model="deepseek-v3.1-4bit",
            response_model=VideoScript,
            messages=[{
                "role": "user",
                "content": "Create a 15-second LinkedIn video script about '3 AI Tools That Save 10 Hours Per Week'. Make it engaging and actionable."
            }],
            max_tokens=2000
        )

        print_status("✅", "VideoScript generated successfully", GREEN)
        print(f"\n{BLUE}Title:{RESET} {result.title}")
        print(f"{BLUE}Hook:{RESET} {result.hook}")
        print(f"{BLUE}Platform:{RESET} {result.target_platform}")
        print(f"{BLUE}Duration:{RESET} {result.total_duration}s")
        print(f"\n{BLUE}Scenes:{RESET}")
        for i, scene in enumerate(result.scenes, 1):
            print(f"  {i}. [{scene.scene_type.value}] {scene.description[:60]}... ({scene.duration}s)")
        print(f"\n{BLUE}Tags:{RESET} {', '.join(result.tags)}")
        return True

    except Exception as e:
        print_status("❌", f"VideoScript test failed: {e}", RED)
        return False


def test_carousel_plan(client):
    """Test CarouselPlan schema"""
    print_status("📊", "Testing CarouselPlan generation...", BLUE)

    try:
        result = client.chat.completions.create(
            model="deepseek-v3.1-4bit",
            response_model=CarouselPlan,
            messages=[{
                "role": "user",
                "content": "Create a 5-slide LinkedIn carousel about 'RDMA Cluster Setup for AI Engineers'. Target audience: ML engineers and data scientists."
            }],
            max_tokens=3000
        )

        print_status("✅", "CarouselPlan generated successfully", GREEN)
        print(f"\n{BLUE}Title:{RESET} {result.title}")
        print(f"{BLUE}Subtitle:{RESET} {result.subtitle}")
        print(f"{BLUE}Target Audience:{RESET} {result.target_audience}")
        print(f"\n{BLUE}Slides ({len(result.slides)}):{RESET}")
        for slide in result.slides:
            print(f"\n  Slide {slide.slide_number}: {slide.heading}")
            print(f"  Style: {slide.visual_style}")
            print(f"  Bullets: {len(slide.bullet_points)}")
        print(f"\n{BLUE}CTA:{RESET} {result.cta_slide}")
        print(f"{BLUE}Caption Preview:{RESET} {result.linkedin_caption[:100]}...")
        return True

    except Exception as e:
        print_status("❌", f"CarouselPlan test failed: {e}", RED)
        return False


def test_streaming(client):
    """Test streaming structured outputs"""
    print_status("🔄", "Testing streaming with Partial[ImagePrompt]...", BLUE)

    try:
        from instructor import Partial

        print("Streaming updates:")
        for partial in client.chat.completions.create(
            model="deepseek-v3.1-4bit",
            response_model=Partial[ImagePrompt],
            messages=[{
                "role": "user",
                "content": "Create an image prompt for a futuristic office with AI assistants"
            }],
            stream=True,
            max_tokens=1000
        ):
            if partial.subject:
                sys.stdout.write(f"\r  Subject: {partial.subject[:60]}")
                sys.stdout.flush()

        print()  # Newline after streaming
        print_status("✅", "Streaming test successful", GREEN)
        return True

    except Exception as e:
        print_status("❌", f"Streaming test failed: {e}", RED)
        return False


def main():
    """Run all Instructor tests"""
    print("\n" + "="*70)
    print(f"{BLUE}🧪 INSTRUCTOR + DEEPSEEK V3.1 TEST SUITE{RESET}")
    print("="*70 + "\n")

    # Test cluster connectivity
    if not test_cluster_connection():
        print_status("❌", "ABORT: Cluster not ready", RED)
        print("\nRequired actions:")
        print("  1. Ensure BETA Exo node is running")
        print("  2. Verify RDMA connectivity (check rdma_en4 status)")
        print("  3. Wait for cluster discovery (1-2 minutes)")
        print("  4. Check cluster status: curl -s http://localhost:52415/cluster/status")
        sys.exit(1)

    # Initialize Instructor client
    client = init_instructor_client()
    if not client:
        sys.exit(1)

    print()

    # Run tests
    results = {
        "ImagePrompt": test_image_prompt(client),
        "VideoScript": test_video_script(client),
        "CarouselPlan": test_carousel_plan(client),
        "Streaming": test_streaming(client),
    }

    # Summary
    print("\n" + "="*70)
    print(f"{BLUE}📊 TEST RESULTS{RESET}")
    print("="*70 + "\n")

    for test_name, passed in results.items():
        status = f"{GREEN}✅ PASS" if passed else f"{RED}❌ FAIL"
        print(f"  {test_name:20} {status}{RESET}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n{BLUE}Total:{RESET} {passed}/{total} tests passed")

    if passed == total:
        print_status("🎉", "ALL TESTS PASSED!", GREEN)
        print("\n✨ Instructor + DeepSeek V3.1 integration is operational")
        print("   Ready for production use with ARTHUR workflows")
        sys.exit(0)
    else:
        print_status("⚠️", f"{total - passed} tests failed", YELLOW)
        sys.exit(1)


if __name__ == "__main__":
    main()
