"""
ARTHUR Vision Module
Image and video analysis using GLM-4.6V-Flash vision-language model

Usage:
  from arthur.vision import VisionClient, VisionAnalyzer

  # Quick image analysis
  client = VisionClient()
  result = client.analyze_image("image.png", "What device is shown?")

  # High-level analysis
  analyzer = VisionAnalyzer()
  result = analyzer.verify_product("image.png", "Mac Studio", color="silver")
"""

from .client import VisionClient, VisionResult
from .analyzer import VisionAnalyzer, MediaAnalysis, AnalysisType
from .keyframe import extract_keyframes, get_video_info, KeyframeResult

__all__ = [
  "VisionClient",
  "VisionResult",
  "VisionAnalyzer",
  "MediaAnalysis",
  "AnalysisType",
  "extract_keyframes",
  "get_video_info",
  "KeyframeResult",
]
