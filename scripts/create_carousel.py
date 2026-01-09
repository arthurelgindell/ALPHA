#!/usr/bin/env python3
"""
LinkedIn Carousel Generator
Integrates AI image generation with Slidev for PDF carousel creation
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import shutil
import sys

@dataclass
class Slide:
    """Represents a single carousel slide"""
    layout: str  # 'cover', 'message', 'stat', 'quote', 'closing'
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image: Optional[str] = None
    stat: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    overlay: bool = False  # Text overlay on image
    background: Optional[str] = None  # Gradient background
    cta: Optional[str] = None  # Call-to-action text
    author: Optional[str] = None  # Quote author

class CarouselGenerator:
    def __init__(self,
                 project_root: str = "/Users/arthurdell/ARTHUR",
                 slidev_dir: str = "linkedin-carousels"):
        self.project_root = Path(project_root)
        self.slidev_dir = self.project_root / slidev_dir
        self.images_dir = self.project_root / "images"
        self.carousels_dir = self.project_root / "carousels"
        self.carousels_dir.mkdir(exist_ok=True)

    def generate_images(self, prompts: List[str],
                       model: str = "schnell",
                       preset: str = "1:1") -> List[Path]:
        """Generate AI images for carousel slides"""
        print(f"🎨 Generating {len(prompts)} images with FLUX.1 [{model}]...")

        image_paths = []
        for i, prompt in enumerate(prompts, 1):
            print(f"  [{i}/{len(prompts)}] {prompt[:60]}...")

            output_path = self.images_dir / f"carousel_slide_{i:02d}.png"

            cmd = [
                "python3",
                str(self.project_root / "scripts/generate_image.py"),
                prompt,
                "--model", model,
                "--preset", preset,
                "--output", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                image_paths.append(output_path)
                print(f"  ✅ Generated: {output_path.name}")
            else:
                print(f"  ❌ Failed: {result.stderr}")
                raise Exception(f"Image generation failed: {result.stderr}")

        return image_paths

    def _render_cover_slide(self, slide: Slide) -> List[str]:
        """Render cover slide with optional image"""
        lines = []

        # Title and subtitle
        lines.append(f"# {slide.title}")
        lines.append("")
        if slide.subtitle:
            lines.append(f"**{slide.subtitle}**")
            lines.append("")

        # Brand signature
        lines.append('<div style="position: absolute; bottom: 2rem; right: 2rem; font-size: 1rem; opacity: 0.7;">')
        lines.append('Arthur Dell')
        lines.append('</div>')

        return lines

    def _render_message_slide(self, slide: Slide) -> List[str]:
        """Render message slide with image and overlay"""
        lines = []

        # Image overlay with text
        lines.append('<div style="position: absolute; inset: 0; background: rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 3rem;">')
        lines.append(f'  <h1 style="color: white; font-size: 3rem; text-shadow: 2px 2px 8px rgba(0,0,0,0.8); margin: 0;">{slide.title}</h1>')
        if slide.subtitle:
            lines.append(f'  <p style="color: white; font-size: 1.5rem; margin-top: 1.5rem; text-shadow: 1px 1px 4px rgba(0,0,0,0.8);">{slide.subtitle}</p>')
        lines.append('</div>')
        lines.append('')

        # Brand signature
        lines.append('<div style="position: absolute; bottom: 2rem; right: 2rem; color: white; opacity: 0.8;">')
        lines.append('Arthur Dell')
        lines.append('</div>')

        return lines

    def _render_stat_slide(self, slide: Slide) -> List[str]:
        """Render statistic slide with gradient background"""
        lines = []

        # Gradient background
        gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        if slide.background == "bg-gradient-green":
            gradient = "linear-gradient(135deg, #34a853 0%, #1a73e8 100%)"
        elif slide.background == "bg-gradient-dark":
            gradient = "linear-gradient(135deg, #202124 0%, #5f6368 100%)"

        lines.append(f'<div style="background: {gradient}; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: white;">')
        lines.append('  <div>')
        lines.append(f'    <div style="font-size: 5rem; font-weight: 800; line-height: 1;">{slide.stat}</div>')
        lines.append(f'    <div style="font-size: 1.5rem; margin-top: 1rem; opacity: 0.9;">{slide.label}</div>')
        if slide.description:
            lines.append(f'    <p style="font-size: 1.25rem; margin-top: 2rem; max-width: 600px;">{slide.description}</p>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

        # Brand signature
        lines.append('<div style="position: absolute; bottom: 2rem; right: 2rem; color: white; opacity: 0.8;">')
        lines.append('Arthur Dell')
        lines.append('</div>')

        return lines

    def _render_quote_slide(self, slide: Slide) -> List[str]:
        """Render quote slide"""
        lines = []

        lines.append('<div style="padding: 4rem; max-width: 900px; margin: 0 auto;">')
        lines.append('  <div style="font-size: 2.5rem; font-style: italic; line-height: 1.4; position: relative;">')
        lines.append('    <span style="font-size: 4rem; color: #1a73e8; position: absolute; left: -2rem; top: -1rem;">"</span>')
        lines.append(f'    {slide.title}')
        lines.append('    <span style="font-size: 4rem; color: #1a73e8;">"</span>')
        lines.append('  </div>')
        if slide.author:
            lines.append(f'  <div style="font-size: 1.5rem; color: #5f6368; margin-top: 2rem; font-weight: 500;">— {slide.author}</div>')
        lines.append('</div>')
        lines.append('')

        # Brand signature
        lines.append('<div style="position: absolute; bottom: 2rem; right: 2rem; opacity: 0.7;">')
        lines.append('Arthur Dell')
        lines.append('</div>')

        return lines

    def _render_closing_slide(self, slide: Slide) -> List[str]:
        """Render closing/CTA slide"""
        lines = []

        lines.append('<div style="background: linear-gradient(135deg, #202124 0%, #5f6368 100%); position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: white; padding: 4rem;">')
        lines.append('  <div style="max-width: 800px;">')
        lines.append(f'    <h1 style="color: white; font-size: 3.5rem; margin-bottom: 1.5rem;">{slide.title}</h1>')
        if slide.subtitle:
            lines.append(f'    <p style="font-size: 1.75rem; margin-top: 1.5rem; opacity: 0.9;">{slide.subtitle}</p>')
        if slide.cta:
            lines.append('    <div style="margin-top: 3rem;">')
            lines.append(f'      <div style="display: inline-block; padding: 1rem 2rem; background: #1a73e8; color: white; font-size: 1.25rem; font-weight: 600; border-radius: 0.5rem;">')
            lines.append(f'        {slide.cta}')
            lines.append('      </div>')
            lines.append('    </div>')
        lines.append('  </div>')
        lines.append('</div>')
        lines.append('')

        # Brand signature
        lines.append('<div style="position: absolute; bottom: 2rem; right: 2rem; color: white; opacity: 0.8;">')
        lines.append('Arthur Dell')
        lines.append('</div>')

        return lines

    def create_slides_markdown(self, slides: List[Slide],
                               title: str = "LinkedIn Carousel") -> str:
        """Generate Slidev Markdown from slide definitions"""
        md_content = [
            "---",
            "theme: default",
            "aspectRatio: 1/1",
            "canvasWidth: 1080",
            "background: white",
            f"title: {title}",
            "class: text-center",
            "---",
            "",
            "<style>",
            "@import './styles/arthur-dell-theme.css';",
            "</style>",
            ""
        ]

        for i, slide in enumerate(slides):
            # Handle image copying for message slides
            if slide.image and slide.layout == "message":
                src = Path(slide.image)
                if src.exists():
                    dest = self.slidev_dir / "public" / "images" / src.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, dest)
                    image_path = f"/images/{src.name}"
                else:
                    print(f"⚠️  Warning: Image not found: {src}")
                    image_path = None
            else:
                image_path = None

            # Add slide separator
            md_content.append("---")

            # Determine Slidev layout
            if slide.layout == "message" and image_path:
                md_content.append("layout: image")
                md_content.append(f"image: {image_path}")
                md_content.append("class: text-center")
            elif slide.layout in ["stat", "quote", "closing"]:
                md_content.append("layout: center")
                md_content.append("class: text-center")
            else:  # cover or default
                md_content.append("class: text-center")

            md_content.append("---")
            md_content.append("")

            # Render slide content
            if slide.layout == "cover":
                md_content.extend(self._render_cover_slide(slide))
            elif slide.layout == "message":
                md_content.extend(self._render_message_slide(slide))
            elif slide.layout == "stat":
                md_content.extend(self._render_stat_slide(slide))
            elif slide.layout == "quote":
                md_content.extend(self._render_quote_slide(slide))
            elif slide.layout == "closing":
                md_content.extend(self._render_closing_slide(slide))

            md_content.append("")

        return "\n".join(md_content)

    def export_pdf(self, output_filename: str) -> Path:
        """Export Slidev presentation to PDF"""
        print(f"📄 Exporting to PDF: {output_filename}...")

        output_path = self.carousels_dir / output_filename

        cmd = [
            "npx",
            "slidev",
            "export",
            "--format", "pdf",
            "--output", str(output_path),
            "--timeout", "90000"
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self.slidev_dir),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            file_size = output_path.stat().st_size / 1024
            print(f"✅ PDF exported: {output_path}")
            print(f"📊 File size: {file_size:.1f} KB")
            return output_path
        else:
            print(f"❌ Export failed: {result.stderr}")
            raise Exception(f"PDF export failed: {result.stderr}")

    def create_carousel(self,
                       slides: List[Slide],
                       title: str,
                       output_filename: Optional[str] = None) -> Path:
        """Complete workflow: images → Slidev → PDF"""
        print(f"\n{'='*60}")
        print(f"🎬 Creating LinkedIn Carousel: {title}")
        print(f"{'='*60}\n")

        # 1. Generate Markdown
        print("📝 Generating Slidev Markdown...")
        markdown = self.create_slides_markdown(slides, title)

        # 2. Write to slides.md
        slides_file = self.slidev_dir / "slides.md"
        slides_file.write_text(markdown)
        print(f"✅ Wrote {slides_file}")
        print(f"   ({len(slides)} slides)")

        # 3. Export to PDF
        if output_filename is None:
            output_filename = f"{title.lower().replace(' ', '_')}.pdf"

        pdf_path = self.export_pdf(output_filename)

        print(f"\n{'='*60}")
        print(f"✅ Carousel Complete: {pdf_path}")
        print(f"{'='*60}\n")

        return pdf_path


def example_2026_workforce_carousel():
    """Example: Create 2026 Workforce Transformation carousel using existing images"""
    generator = CarouselGenerator()

    slides = [
        Slide(
            layout="cover",
            title="2026 Workforce Transformation",
            subtitle="The AI Skills Premium"
        ),
        Slide(
            layout="message",
            title="AI-Skilled Workers Earn 56% More",
            subtitle="The 2026 earnings premium is real",
            image="/Users/arthurdell/ARTHUR/images/storyboard_01_56_percent_premium.png",
            overlay=True
        ),
        Slide(
            layout="stat",
            stat="7.5 Hours",
            label="Saved per Week",
            description="AI-fluent professionals save nearly a full workday every week",
            background="bg-gradient-blue"
        ),
        Slide(
            layout="message",
            title="The Time Advantage",
            subtitle="7.5 hours per week = 390 hours per year",
            image="/Users/arthurdell/ARTHUR/images/storyboard_02_time_advantage.png",
            overlay=True
        ),
        Slide(
            layout="message",
            title="The Preparation Gap",
            subtitle="42% expect change, only 17% prepare",
            image="/Users/arthurdell/ARTHUR/images/storyboard_03_the_gap.png",
            overlay=True
        ),
        Slide(
            layout="quote",
            title="The future belongs to those who prepare today"
        ),
        Slide(
            layout="closing",
            title="Which Side Will You Choose?",
            subtitle="Start building AI skills today",
            cta="Connect with Arthur Dell"
        )
    ]

    pdf_path = generator.create_carousel(
        slides=slides,
        title="2026 Workforce Transformation",
        output_filename="2026_workforce_carousel.pdf"
    )

    return pdf_path


if __name__ == "__main__":
    print("\n🎨 LinkedIn Carousel Generator")
    print("="*60)

    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        pdf_path = example_2026_workforce_carousel()
        print(f"\n✅ Example carousel created: {pdf_path}")
    else:
        print("\nUsage:")
        print("  python3 create_carousel.py --example")
        print("  (generates example 2026 Workforce carousel)")
        print("\nOr import and use the CarouselGenerator class in your own scripts.")
        print("\nSee CAROUSEL_CREATION_GUIDE.md for more examples.")
