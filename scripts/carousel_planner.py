#!/usr/bin/env python3
"""
Carousel Content Planner
Helps structure carousel content following storyboard methodology
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
import sys

class CarouselPlanner:
    """Interactive carousel planning tool"""

    def __init__(self):
        self.methodology_path = Path("/Users/arthurdell/ARTHUR/STORYBOARD_METHODOLOGY.md")
        self.carousels_dir = Path("/Users/arthurdell/ARTHUR/carousels")
        self.carousels_dir.mkdir(exist_ok=True)

    def create_plan(self,
                   topic: str,
                   slide_count: int = 8,
                   messages: Optional[List[str]] = None) -> Dict:
        """Create structured carousel plan"""

        plan = {
            "topic": topic,
            "slide_count": slide_count,
            "slides": []
        }

        # Slide 1: Cover (always)
        plan["slides"].append({
            "number": 1,
            "type": "cover",
            "title": topic,
            "subtitle": "Add compelling subtitle",
            "image_needed": True,
            "ai_prompt": f"Professional corporate cover image for {topic}, photorealistic, 8k quality, modern office environment, cinematic lighting"
        })

        # Middle slides: Content
        if messages:
            for i, message in enumerate(messages, 2):
                plan["slides"].append({
                    "number": i,
                    "type": "message",
                    "core_message": message,
                    "image_needed": True,
                    "ai_prompt": f"Photo-realistic scene illustrating: {message}, professional corporate environment, 8k quality, cinematic lighting, clear composition"
                })

        # Add stat slide if we have enough slides
        if slide_count >= 7:
            plan["slides"].append({
                "number": len(plan["slides"]) + 1,
                "type": "stat",
                "stat_value": "[Insert statistic]",
                "stat_label": "[Label for stat]",
                "description": "[Context for the statistic]",
                "image_needed": False
            })

        # Add quote slide if we have enough slides
        if slide_count >= 8:
            plan["slides"].append({
                "number": len(plan["slides"]) + 1,
                "type": "quote",
                "quote_text": "[Powerful quote related to topic]",
                "image_needed": False
            })

        # Last slide: CTA
        plan["slides"].append({
            "number": slide_count,
            "type": "closing",
            "title": "Take Action Today",
            "subtitle": "What's your strategy?",
            "call_to_action": "Connect with Arthur Dell",
            "image_needed": False
        })

        return plan

    def save_plan(self, plan: Dict, filename: str):
        """Save plan as JSON for reference"""
        output_path = self.carousels_dir / f"{filename}.json"
        output_path.write_text(json.dumps(plan, indent=2))
        print(f"✅ Saved plan: {output_path}")
        return output_path

    def validate_against_methodology(self, plan: Dict) -> List[str]:
        """Check plan against storyboard methodology"""
        issues = []

        # Check slide count
        if plan["slide_count"] < 5:
            issues.append("⚠️  Carousel should have at least 5 slides for impact")
        if plan["slide_count"] > 12:
            issues.append("⚠️  More than 12 slides may lose audience attention")

        # Check for one-story rule in each slide
        for slide in plan["slides"]:
            if slide["type"] == "message":
                if "core_message" in slide:
                    words = slide["core_message"].split()
                    if len(words) > 12:
                        issues.append(f"⚠️  Slide {slide['number']}: Message should be ≤12 words (currently {len(words)} words)")

        # Check for variety
        slide_types = [s["type"] for s in plan["slides"]]
        if slide_types.count("message") == len(slide_types) - 2:  # All slides except cover and closing
            issues.append("⚠️  Consider adding variety with stat or quote slides")

        return issues if issues else ["✅ Plan follows methodology"]

    def print_plan_summary(self, plan: Dict):
        """Print a formatted summary of the plan"""
        print(f"\n{'='*60}")
        print(f"📋 Carousel Plan: {plan['topic']}")
        print(f"{'='*60}\n")
        print(f"Total slides: {plan['slide_count']}")
        print(f"\nSlide breakdown:")

        for slide in plan["slides"]:
            print(f"\n  {slide['number']}. [{slide['type'].upper()}]")
            if "title" in slide:
                print(f"     Title: {slide['title']}")
            if "core_message" in slide:
                print(f"     Message: {slide['core_message']}")
            if "stat_value" in slide:
                print(f"     Stat: {slide['stat_value']}")
            if "image_needed" in slide:
                status = "✅ Yes" if slide["image_needed"] else "❌ No"
                print(f"     Image needed: {status}")
            if "ai_prompt" in slide:
                print(f"     AI Prompt: {slide['ai_prompt'][:60]}...")


def example_ai_skills_plan():
    """Example: Create plan for AI Skills Premium carousel"""
    planner = CarouselPlanner()

    plan = planner.create_plan(
        topic="2026 AI Skills Premium",
        slide_count=8,
        messages=[
            "AI-skilled workers earn 56% more in 2026",
            "AI saves 7.5 hours per week for professionals",
            "42% expect job changes, only 17% actively prepare",
            "The choice: Elevate your skills or fall behind"
        ]
    )

    # Print summary
    planner.print_plan_summary(plan)

    # Validate
    print("\n📊 Validation:")
    validation = planner.validate_against_methodology(plan)
    for item in validation:
        print(f"  {item}")

    # Save plan
    plan_path = planner.save_plan(plan, "2026_ai_skills_plan")

    return plan, plan_path


if __name__ == "__main__":
    print("\n📋 LinkedIn Carousel Planner")
    print("="*60)

    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        # Run example plan
        plan, plan_path = example_ai_skills_plan()
        print(f"\n✅ Example plan created: {plan_path}")
    else:
        print("\nUsage:")
        print("  python3 carousel_planner.py --example")
        print("  (generates example AI Skills plan)")
        print("\nOr import and use the CarouselPlanner class in your own scripts.")
        print("\nExample:")
        print("""
from carousel_planner import CarouselPlanner

planner = CarouselPlanner()
plan = planner.create_plan(
    topic="Your Topic",
    slide_count=8,
    messages=["Message 1", "Message 2", "Message 3"]
)
planner.print_plan_summary(plan)
planner.save_plan(plan, "your_plan_name")
        """)
