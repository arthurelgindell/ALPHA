"""
LinkedIn Carousel Production Workflow

Pipeline:
1. Strategy (DeepSeek) → Content hook, narrative arc, emotional journey
2. Slide Planning (DeepSeek) → Individual slide concepts with text hierarchy
3. Visual Prompts (Nemotron) → Optimized prompts per slide
4. Image Generation → FLUX.1 for backgrounds, Gemini Pro for complex scenes
5. Assembly → Apply design system (charcoal background, amber accents)
6. Output → /Volumes/STUDIO/CAROUSELS/ or local

Text Handling: All text rendered programmatically, NOT by image generation
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
import json

from .base import Workflow, WorkflowResult, WorkflowStatus
from ..llm.router import TaskType
from ..generators.image import ImageBackend
from ..output.manager import OutputType
from ..config import DESIGN

# ============================================================================
# Schemas for Structured LLM Output
# ============================================================================

class SlideStrategy(BaseModel):
  """Strategy for a single slide"""
  slide_number: int = Field(description="Slide number (1-10)")
  slide_type: str = Field(description="Type: cover, message, stat, quote, or closing")
  headline: str = Field(description="Short headline for the slide")
  subheadline: Optional[str] = Field(default=None, description="Optional subheadline")
  key_message: str = Field(description="Main message for this slide")
  emotional_beat: str = Field(description="Emotional tone: curiosity, tension, insight, action")
  visual_concept: str = Field(description="Visual concept for the background image")

class CarouselStrategy(BaseModel):
  """Complete carousel strategy"""
  hook: str = Field(description="Opening hook that captures attention")
  narrative_arc: str = Field(description="Story progression across slides")
  target_audience: str = Field(description="Target audience for this carousel")
  emotional_journey: str = Field(description="Emotional arc across slides")
  slides: List[SlideStrategy] = Field(description="Array of slides for the carousel")  # No min/max - causes LM Studio issues
  cta: str = Field(description="Call to action for final slide")
  linkedin_caption: str = Field(description="LinkedIn post caption")

class ImagePromptOutput(BaseModel):
  """Optimized image prompt for generation"""
  slide_number: int = Field(description="Which slide this prompt is for")
  backend: str = Field(description="Backend: flux-schnell or gemini-pro")
  prompt: str = Field(description="Optimized image generation prompt")
  aspect_ratio: str = Field(default="4:5", description="Aspect ratio for the image")
  style_notes: str = Field(description="Style notes for the image")

class VisualPrompts(BaseModel):
  """All visual prompts for carousel"""
  prompts: List[ImagePromptOutput]

# ============================================================================
# Carousel Workflow
# ============================================================================

class CarouselWorkflow(Workflow):
  """
  LinkedIn Carousel Production Workflow

  Usage:
    workflow = CarouselWorkflow(
      brief="AI is watching your every keystroke",
      slide_count=8
    )
    result = workflow.execute()

    if result.success:
      print(f"Carousel: {result.outputs[0]}")
  """

  def __init__(
    self,
    brief: str,
    slide_count: int = 8,
    style: str = "charcoal-amber",
    output_dir: Optional[Path] = None
  ):
    super().__init__(brief, style, output_dir)
    self.slide_count = slide_count

  def plan(self) -> dict:
    """
    Create carousel strategy using LLM

    Uses DeepSeek for strategy, Nemotron for visual prompts
    """
    self._report_progress("Creating content strategy...", 0.1)

    # Phase 1: Strategy with DeepSeek
    strategy_prompt = f"""Create a LinkedIn carousel strategy.

Topic: {self.brief}
Number of slides: {self.slide_count}

Requirements:
- hook: One compelling sentence to grab attention
- narrative_arc: Brief description of the story flow
- target_audience: Who this is for
- emotional_journey: How readers should feel across slides
- slides: Array with exactly {self.slide_count} slide objects
- cta: Call to action text
- linkedin_caption: Caption for the LinkedIn post

For each slide, provide:
- slide_number (1 to {self.slide_count})
- slide_type (cover, message, or closing)
- headline (short, punchy text)
- key_message (the main point)
- emotional_beat (curiosity, tension, insight, or action)
- visual_concept (what the background image should show)

Use plain text only. No HTML, no formatting. Separate words with spaces.
Design: Charcoal backgrounds (#1a1a1a), amber accents (#f59e0b).
"""

    try:
      strategy = self.router.structured_output(
        task_type=TaskType.STRATEGY,
        messages=[
          {"role": "system", "content": "You are a LinkedIn content strategist. Output clean JSON with plain text values. Use spaces between words. No HTML."},
          {"role": "user", "content": strategy_prompt}
        ],
        response_model=CarouselStrategy,
        temperature=0.5
      )
    except Exception as e:
      # Fallback to basic strategy if LLM unavailable
      strategy = self._fallback_strategy()

    self._report_progress("Generating visual prompts...", 0.2)

    # Phase 2: Visual prompts with Nemotron
    prompts_request = f"""Generate optimized image prompts for this carousel:

Strategy:
{strategy.model_dump_json(indent=2)}

For each slide that needs an image, create a prompt optimized for AI image generation.
- Use "flux-schnell" for abstract backgrounds and simple scenes
- Use "gemini-pro" for complex scenes with characters or detailed UI

IMPORTANT: Prompts should NOT include text - text will be added programmatically.
Focus on mood, atmosphere, and visual metaphor.
"""

    try:
      visual_prompts = self.router.structured_output(
        task_type=TaskType.PROMPT_ENGINEERING,
        messages=[
          {"role": "system", "content": "You are an expert at crafting prompts for AI image generation using FLUX.1 and Gemini."},
          {"role": "user", "content": prompts_request}
        ],
        response_model=VisualPrompts
      )
    except Exception as e:
      visual_prompts = self._fallback_prompts(strategy)

    return {
      "strategy": strategy.model_dump() if hasattr(strategy, 'model_dump') else strategy,
      "visual_prompts": visual_prompts.model_dump() if hasattr(visual_prompts, 'model_dump') else visual_prompts
    }

  def _fallback_strategy(self) -> CarouselStrategy:
    """Fallback strategy when LLM unavailable"""
    slides = []
    for i in range(1, self.slide_count + 1):
      if i == 1:
        slide_type = "cover"
      elif i == self.slide_count:
        slide_type = "closing"
      else:
        slide_type = "message"

      slides.append(SlideStrategy(
        slide_number=i,
        slide_type=slide_type,
        headline=f"Slide {i}" if i > 1 else self.brief[:50],
        key_message=self.brief,
        emotional_beat="engage",
        visual_concept="Professional abstract background"
      ))

    return CarouselStrategy(
      hook=self.brief,
      narrative_arc="Introduction → Problem → Solution → CTA",
      target_audience="LinkedIn professionals",
      emotional_journey="Curiosity → Recognition → Insight → Action",
      slides=slides,
      cta="Connect to learn more",
      linkedin_caption=f"🎯 {self.brief}\n\nSwipe through to discover more..."
    )

  def _fallback_prompts(self, strategy) -> VisualPrompts:
    """Fallback prompts when LLM unavailable"""
    prompts = []
    for slide in strategy.slides if hasattr(strategy, 'slides') else []:
      if slide.slide_type in ["cover", "message"]:
        prompts.append(ImagePromptOutput(
          slide_number=slide.slide_number,
          backend="flux-schnell",
          prompt=f"Abstract professional background, {slide.visual_concept}, dark charcoal tones, subtle amber accents, minimalist corporate aesthetic, 8k quality",
          aspect_ratio="4:5",
          style_notes="Use as background with text overlay"
        ))
    return VisualPrompts(prompts=prompts)

  def generate(self, plan: dict) -> List[Path]:
    """Generate images for carousel slides"""
    assets = []
    visual_prompts = plan.get("visual_prompts", {}).get("prompts", [])

    for i, prompt_data in enumerate(visual_prompts):
      self._report_progress(
        f"Generating slide {prompt_data.get('slide_number', i+1)} image...",
        0.3 + (i / len(visual_prompts)) * 0.3
      )

      prompt = prompt_data.get("prompt", "")
      backend_str = prompt_data.get("backend", "flux-schnell")

      try:
        if backend_str == "gemini-pro":
          result = self.image_gen.generate_gemini(
            prompt=prompt,
            aspect_ratio=prompt_data.get("aspect_ratio", "4:5")
          )
        else:
          result = self.image_gen.generate(
            prompt=prompt,
            backend=ImageBackend.FLUX_SCHNELL,
            preset="4:5"
          )

        if result.success and result.path:
          assets.append(result.path)
        else:
          self.result.errors.append(f"Failed to generate slide {prompt_data.get('slide_number')}: {result.error}")

      except Exception as e:
        self.result.errors.append(f"Generation error: {e}")

    return assets

  def assemble(self, assets: List[Path], plan: dict) -> List[Path]:
    """
    Assemble carousel from generated assets

    Applies design system and adds text overlays
    """
    self._report_progress("Assembling carousel...", 0.8)

    strategy = plan.get("strategy", {})

    # Create carousel folder
    carousel_folder = self.output_manager.create_carousel_folder(
      topic=self.brief[:30],
      style=self.style
    )

    # Copy assets with proper naming
    final_outputs = []
    slides_data = strategy.get("slides", [])

    for i, asset in enumerate(assets):
      if i < len(slides_data):
        slide = slides_data[i]
        slide_type = slide.get("slide_type", "message")
        dest_name = f"slide_{i+1:02d}_{slide_type}{asset.suffix}"
      else:
        dest_name = f"slide_{i+1:02d}_image{asset.suffix}"

      dest_path = carousel_folder / dest_name
      import shutil
      shutil.copy2(str(asset), str(dest_path))
      final_outputs.append(dest_path)

    # Save metadata
    metadata_path = carousel_folder / "metadata.json"
    metadata = {
      "topic": self.brief,
      "style": self.style,
      "slide_count": len(final_outputs),
      "strategy": strategy,
      "linkedin_caption": strategy.get("linkedin_caption", "")
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))
    final_outputs.append(metadata_path)

    self._report_progress("Carousel complete!", 1.0)
    return [carousel_folder]  # Return folder path

  def execute(self) -> WorkflowResult:
    """Execute carousel workflow"""
    return super().execute()
