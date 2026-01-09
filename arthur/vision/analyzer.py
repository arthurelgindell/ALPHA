"""
High-level Vision Analyzer for content verification
Combines VisionClient with domain-specific analysis templates
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
import json
import logging
import re

from .client import VisionClient, VisionResult
from .keyframe import extract_keyframes, KeyframeResult

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
  """Pre-defined analysis types"""
  PRODUCT_VERIFICATION = "product"
  QUALITY_CHECK = "quality"
  CONTENT_ACCURACY = "accuracy"
  SCENE_DESCRIPTION = "scene"
  CUSTOM = "custom"


@dataclass
class MediaAnalysis:
  """Complete media analysis result"""
  success: bool
  media_path: Path
  media_type: Literal["image", "video"]
  analysis_type: AnalysisType
  summary: str
  details: dict = field(default_factory=dict)
  keyframes: Optional[list[Path]] = None
  frame_analyses: Optional[list[VisionResult]] = None
  error: Optional[str] = None

  def to_dict(self) -> dict:
    """Convert to dictionary for JSON serialization"""
    return {
      "success": self.success,
      "media_path": str(self.media_path),
      "media_type": self.media_type,
      "analysis_type": self.analysis_type.value,
      "summary": self.summary,
      "details": self.details,
      "error": self.error,
      "keyframes": [str(k) for k in self.keyframes] if self.keyframes else None,
      "frame_count": len(self.frame_analyses) if self.frame_analyses else 0
    }

  def to_json(self, indent: int = 2) -> str:
    """Convert to JSON string"""
    return json.dumps(self.to_dict(), indent=indent)


class VisionAnalyzer:
  """
  Domain-specific vision analysis for ARTHUR media production

  Usage:
    analyzer = VisionAnalyzer()

    # Quick product check
    result = analyzer.verify_product(
      image_path="output.png",
      expected_product="Mac Studio",
      expected_color="silver"
    )

    # Quality rating
    result = analyzer.rate_quality(
      image_path="hero_shot.png",
      criteria=["lighting", "composition", "focus", "cinematic"]
    )

    # Video content analysis
    result = analyzer.analyze_video(
      video_path="promo.mp4",
      prompt="Describe the key moments and verify product placement"
    )
  """

  def __init__(self, client: Optional[VisionClient] = None):
    """Initialize with optional custom client"""
    self.client = client or VisionClient()

  def verify_product(
    self,
    image_path: Path | str,
    expected_product: str,
    expected_color: Optional[str] = None,
    expected_setting: Optional[str] = None
  ) -> MediaAnalysis:
    """
    Verify product accuracy in generated image

    Args:
      image_path: Path to image
      expected_product: Product name (e.g., "Mac Studio", "iPad Pro")
      expected_color: Expected color/finish (e.g., "silver", "champagne-gold")
      expected_setting: Expected environment/context

    Returns:
      MediaAnalysis with verification details
    """
    image_path = Path(image_path)

    # Build verification prompt
    prompt_parts = [
      f"Analyze this image and answer the following questions:",
      f"1. What product or device is shown in this image? Be specific about the form factor.",
      f"2. Is this a '{expected_product}'? Answer YES or NO and explain why.",
    ]

    if expected_color:
      prompt_parts.append(
        f"3. What color/finish is the product? Is it '{expected_color}'? Answer YES or NO."
      )

    if expected_setting:
      prompt_parts.append(
        f"4. Describe the setting/environment. Does it match '{expected_setting}'?"
      )

    prompt_parts.append(
      "\nProvide a brief summary at the end stating if the image matches expectations."
    )

    prompt = "\n".join(prompt_parts)

    # Analyze image
    result = self.client.analyze_image(image_path, prompt, detail="high")

    if not result.success:
      return MediaAnalysis(
        success=False,
        media_path=image_path,
        media_type="image",
        analysis_type=AnalysisType.PRODUCT_VERIFICATION,
        summary="Analysis failed",
        error=result.error
      )

    # Parse response for verification results
    analysis_text = result.analysis.lower()

    # Check for product match
    product_match = None
    if "yes" in analysis_text[:500] and expected_product.lower() in analysis_text:
      product_match = True
    elif "no" in analysis_text[:500]:
      product_match = False

    # Check for color match
    color_match = None
    if expected_color:
      if expected_color.lower() in analysis_text:
        color_match = True
      # Common mismatches
      wrong_colors = ["black", "dark", "grey", "gray"] if expected_color.lower() in ["silver", "champagne", "gold"] else []
      if any(c in analysis_text for c in wrong_colors):
        color_match = False

    details = {
      "expected_product": expected_product,
      "expected_color": expected_color,
      "expected_setting": expected_setting,
      "product_match": product_match,
      "color_match": color_match,
      "raw_analysis": result.analysis
    }

    # Generate summary
    issues = []
    if product_match is False:
      issues.append(f"Product mismatch (expected {expected_product})")
    if color_match is False:
      issues.append(f"Color mismatch (expected {expected_color})")

    if issues:
      summary = f"VERIFICATION FAILED: {'; '.join(issues)}"
    elif product_match is True:
      summary = f"Product verified: {expected_product}"
      if color_match is True:
        summary += f" ({expected_color})"
    else:
      summary = "Verification inconclusive - manual review recommended"

    return MediaAnalysis(
      success=True,
      media_path=image_path,
      media_type="image",
      analysis_type=AnalysisType.PRODUCT_VERIFICATION,
      summary=summary,
      details=details
    )

  def rate_quality(
    self,
    image_path: Path | str,
    criteria: Optional[list[str]] = None
  ) -> MediaAnalysis:
    """
    Rate image quality on multiple criteria

    Args:
      image_path: Path to image
      criteria: List of criteria to rate (default: lighting, composition, focus, realism)

    Returns:
      MediaAnalysis with scores per criterion (1-10)
    """
    image_path = Path(image_path)

    if criteria is None:
      criteria = ["lighting", "composition", "focus", "cinematic_feel", "realism"]

    criteria_str = ", ".join(criteria)

    prompt = f"""Rate this image on the following criteria using a scale of 1-10:
{criteria_str}

For each criterion, provide:
- Score (1-10)
- Brief explanation

Format your response as:
CRITERION: SCORE/10 - explanation

End with an OVERALL score averaging all criteria."""

    result = self.client.analyze_image(image_path, prompt, detail="high")

    if not result.success:
      return MediaAnalysis(
        success=False,
        media_path=image_path,
        media_type="image",
        analysis_type=AnalysisType.QUALITY_CHECK,
        summary="Quality rating failed",
        error=result.error
      )

    # Parse scores from response
    scores = {}
    for criterion in criteria:
      # Look for patterns like "lighting: 8/10" or "LIGHTING: 8/10"
      pattern = rf"{criterion}[:\s]+(\d+)/10"
      match = re.search(pattern, result.analysis, re.IGNORECASE)
      if match:
        scores[criterion] = int(match.group(1))

    # Calculate overall
    if scores:
      overall = sum(scores.values()) / len(scores)
    else:
      # Try to find overall score
      overall_match = re.search(r"overall[:\s]+(\d+)/10", result.analysis, re.IGNORECASE)
      overall = int(overall_match.group(1)) if overall_match else None

    details = {
      "criteria": criteria,
      "scores": scores,
      "overall": round(overall, 1) if overall else None,
      "raw_analysis": result.analysis
    }

    # Generate summary
    if overall:
      if overall >= 8:
        quality_label = "Excellent"
      elif overall >= 6:
        quality_label = "Good"
      elif overall >= 4:
        quality_label = "Fair"
      else:
        quality_label = "Poor"

      summary = f"Quality: {quality_label} ({overall:.1f}/10)"

      # Note low scores
      low_scores = [k for k, v in scores.items() if v < 6]
      if low_scores:
        summary += f" - Needs improvement: {', '.join(low_scores)}"
    else:
      summary = "Quality scores could not be parsed - see raw analysis"

    return MediaAnalysis(
      success=True,
      media_path=image_path,
      media_type="image",
      analysis_type=AnalysisType.QUALITY_CHECK,
      summary=summary,
      details=details
    )

  def analyze_video(
    self,
    video_path: Path | str,
    prompt: str,
    num_keyframes: int = 3,
    analyze_each_frame: bool = True,
    cleanup_frames: bool = True
  ) -> MediaAnalysis:
    """
    Analyze video by extracting and analyzing keyframes

    Args:
      video_path: Path to video
      prompt: Analysis prompt
      num_keyframes: Number of frames to extract (1-5)
      analyze_each_frame: Analyze each frame individually
      cleanup_frames: Delete extracted frames after analysis

    Returns:
      MediaAnalysis with keyframe analyses
    """
    video_path = Path(video_path)
    num_keyframes = min(max(num_keyframes, 1), 5)

    # Extract keyframes
    keyframe_result = extract_keyframes(
      video_path,
      num_frames=num_keyframes,
      strategy="uniform"
    )

    if not keyframe_result.success:
      return MediaAnalysis(
        success=False,
        media_path=video_path,
        media_type="video",
        analysis_type=AnalysisType.CUSTOM,
        summary="Failed to extract keyframes",
        error=keyframe_result.error
      )

    frame_analyses = []

    if analyze_each_frame:
      # Analyze each frame individually
      for i, frame_path in enumerate(keyframe_result.frames):
        frame_prompt = f"[Frame {i+1}/{len(keyframe_result.frames)}] {prompt}"
        result = self.client.analyze_image(frame_path, frame_prompt)
        frame_analyses.append(result)
        logger.info(f"Analyzed frame {i+1}/{len(keyframe_result.frames)}")
    else:
      # Compare all frames in single request
      comparison_prompt = f"""Analyze these {len(keyframe_result.frames)} frames from a video:

{prompt}

Describe what happens across the frames and provide a summary."""

      result = self.client.compare_images(
        keyframe_result.frames,
        comparison_prompt
      )
      frame_analyses.append(result)

    # Clean up frames if requested
    if cleanup_frames:
      keyframe_result.cleanup()
      stored_keyframes = None
    else:
      stored_keyframes = keyframe_result.frames

    # Compile results
    successful_analyses = [r for r in frame_analyses if r.success]

    if not successful_analyses:
      return MediaAnalysis(
        success=False,
        media_path=video_path,
        media_type="video",
        analysis_type=AnalysisType.CUSTOM,
        summary="All frame analyses failed",
        error="No frames could be analyzed"
      )

    # Generate summary
    if analyze_each_frame:
      summaries = [r.analysis[:200] for r in successful_analyses]
      combined = "\n---\n".join([
        f"Frame {i+1}: {s}..." for i, s in enumerate(summaries)
      ])
      summary = f"Analyzed {len(successful_analyses)} keyframes"
    else:
      combined = successful_analyses[0].analysis
      summary = "Video analysis complete"

    details = {
      "duration": keyframe_result.duration,
      "fps": keyframe_result.fps,
      "resolution": keyframe_result.resolution,
      "frames_analyzed": len(successful_analyses),
      "combined_analysis": combined
    }

    return MediaAnalysis(
      success=True,
      media_path=video_path,
      media_type="video",
      analysis_type=AnalysisType.CUSTOM,
      summary=summary,
      details=details,
      keyframes=stored_keyframes,
      frame_analyses=frame_analyses
    )

  def describe_scene(
    self,
    image_path: Path | str,
    focus: Optional[str] = None
  ) -> MediaAnalysis:
    """
    Get detailed scene description

    Args:
      image_path: Path to image
      focus: Optional focus area (e.g., "products", "lighting", "composition")

    Returns:
      MediaAnalysis with scene description
    """
    image_path = Path(image_path)

    if focus:
      prompt = f"Describe this image in detail, focusing on: {focus}"
    else:
      prompt = """Describe this image in detail including:
1. Main subject and its characteristics
2. Setting/environment
3. Lighting and mood
4. Composition and framing
5. Any text or branding visible
6. Overall quality and style"""

    result = self.client.analyze_image(image_path, prompt, detail="high")

    if not result.success:
      return MediaAnalysis(
        success=False,
        media_path=image_path,
        media_type="image",
        analysis_type=AnalysisType.SCENE_DESCRIPTION,
        summary="Scene description failed",
        error=result.error
      )

    return MediaAnalysis(
      success=True,
      media_path=image_path,
      media_type="image",
      analysis_type=AnalysisType.SCENE_DESCRIPTION,
      summary=result.analysis[:100] + "...",
      details={"full_description": result.analysis}
    )
