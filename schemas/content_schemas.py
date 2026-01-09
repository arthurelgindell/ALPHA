"""
Production Pydantic Schemas for Structured LLM Outputs

These schemas work with the Instructor library to ensure type-safe,
validated outputs from LLMs like DeepSeek V3.1.

Usage:
    import instructor
    from openai import OpenAI
    from schemas.content_schemas import VideoScript, CarouselPlan, ImagePrompt

    client = instructor.from_openai(
        OpenAI(base_url="http://localhost:52415/v1", api_key="not-needed"),
        mode=instructor.Mode.JSON
    )

    script = client.chat.completions.create(
        model="deepseek-v3.1-4bit",
        response_model=VideoScript,
        messages=[{"role": "user", "content": "Create video about AI"}]
    )
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from enum import Enum


# ============================================================================
# Video Generation Schemas
# ============================================================================

class SceneType(str, Enum):
    """Type of scene in video"""
    INTRO = "intro"
    CONTENT = "content"
    TRANSITION = "transition"
    CTA = "cta"  # Call to action
    OUTRO = "outro"


class Scene(BaseModel):
    """Individual scene in a video"""
    scene_type: SceneType = Field(description="Type of scene")
    description: str = Field(
        description="Visual description of what happens in this scene",
        min_length=10,
        max_length=500
    )
    duration: int = Field(
        description="Duration of scene in seconds",
        ge=2,
        le=10
    )
    camera_movement: Optional[str] = Field(
        default=None,
        description="Camera movement (e.g., 'zoom in', 'pan left', 'static')"
    )
    voiceover: Optional[str] = Field(
        default=None,
        description="Optional voiceover text for this scene",
        max_length=200
    )

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is clear and actionable"""
        if len(v.split()) < 5:
            raise ValueError("Description must be at least 5 words")
        return v.strip()


class VideoScript(BaseModel):
    """Complete video script with scenes"""
    title: str = Field(
        description="Engaging video title",
        min_length=5,
        max_length=100
    )
    hook: str = Field(
        description="Opening hook that captures attention in first 3 seconds",
        min_length=10,
        max_length=200
    )
    scenes: List[Scene] = Field(
        description="List of scenes in chronological order",
        min_length=3,
        max_length=8
    )
    total_duration: int = Field(
        description="Total video duration in seconds",
        ge=5,
        le=60
    )
    target_platform: Literal["linkedin", "youtube_shorts", "instagram_reels", "general"] = Field(
        default="linkedin",
        description="Target social media platform"
    )
    tags: List[str] = Field(
        description="Relevant hashtags or keywords (without #)",
        max_length=10
    )

    @field_validator('total_duration')
    @classmethod
    def validate_total_duration(cls, v: int, info) -> int:
        """Ensure total duration matches sum of scenes"""
        # Note: This validator runs before scenes are fully populated
        # Use root_validator for cross-field validation if needed
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags are lowercase and alphanumeric"""
        return [tag.lower().replace('#', '').strip() for tag in v]


# ============================================================================
# Carousel/Image Generation Schemas
# ============================================================================

class SlideContent(BaseModel):
    """Content for a single carousel slide"""
    slide_number: int = Field(description="Slide position (1-indexed)", ge=1, le=10)
    heading: str = Field(
        description="Main heading for the slide",
        min_length=3,
        max_length=80
    )
    subheading: Optional[str] = Field(
        default=None,
        description="Optional subheading",
        max_length=120
    )
    bullet_points: List[str] = Field(
        description="Key points on this slide (1-5 bullets)",
        min_length=1,
        max_length=5
    )
    image_prompt: str = Field(
        description="Detailed FLUX.1 prompt for slide background image (SCALS format)",
        min_length=20,
        max_length=500
    )
    visual_style: Literal["professional", "modern", "minimalist", "bold", "tech"] = Field(
        default="professional",
        description="Visual style for this slide"
    )

    @field_validator('bullet_points')
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        """Ensure bullets are concise"""
        validated = []
        for bullet in v:
            bullet = bullet.strip()
            if len(bullet.split()) > 20:
                raise ValueError(f"Bullet too long (max 20 words): {bullet[:50]}...")
            validated.append(bullet)
        return validated

    @field_validator('image_prompt')
    @classmethod
    def validate_image_prompt(cls, v: str) -> str:
        """Ensure image prompt follows SCALS format (Subject, Composition, Action, Location, Style)"""
        # Basic validation - check for key components
        v = v.strip()
        if ',' not in v:
            raise ValueError("Image prompt should be comma-separated (SCALS format)")
        return v


class CarouselPlan(BaseModel):
    """Complete LinkedIn carousel content plan"""
    title: str = Field(
        description="Carousel title (appears on first slide)",
        min_length=5,
        max_length=100
    )
    subtitle: str = Field(
        description="Subtitle explaining value proposition (10 words or less)",
        max_length=100
    )
    target_audience: str = Field(
        description="Who this carousel is for",
        max_length=200
    )
    slides: List[SlideContent] = Field(
        description="List of slides (5-10 recommended for LinkedIn)",
        min_length=3,
        max_length=10
    )
    color_scheme: str = Field(
        default="professional blue and white",
        description="Color scheme for carousel design"
    )
    cta_slide: str = Field(
        description="Call-to-action text for final slide",
        max_length=200
    )
    linkedin_caption: str = Field(
        description="LinkedIn post caption to accompany carousel",
        min_length=50,
        max_length=1500
    )

    @field_validator('subtitle')
    @classmethod
    def validate_subtitle_length(cls, v: str) -> str:
        """Ensure subtitle is concise"""
        word_count = len(v.split())
        if word_count > 15:
            raise ValueError(f"Subtitle too long ({word_count} words, max 15)")
        return v.strip()

    @field_validator('slides')
    @classmethod
    def validate_slide_numbers(cls, v: List[SlideContent]) -> List[SlideContent]:
        """Ensure slides are numbered consecutively"""
        for i, slide in enumerate(v, start=1):
            if slide.slide_number != i:
                slide.slide_number = i  # Auto-correct numbering
        return v


# ============================================================================
# Image Generation Schemas
# ============================================================================

class ImageAspectRatio(str, Enum):
    """Supported aspect ratios for FLUX.1"""
    SQUARE = "1:1"  # 1024x1024
    LANDSCAPE = "16:9"  # 1920x1088
    PORTRAIT = "9:16"  # 1088x1920
    WIDE = "21:9"  # 2176x928
    ULTRA_WIDE = "32:9"  # 2176x608


class ImagePrompt(BaseModel):
    """Structured image generation prompt for FLUX.1"""
    subject: str = Field(
        description="Main subject of the image",
        min_length=3,
        max_length=200
    )
    composition: str = Field(
        description="How the subject is framed (e.g., 'close-up', 'wide shot')",
        max_length=100
    )
    action: Optional[str] = Field(
        default=None,
        description="What is happening in the image",
        max_length=150
    )
    location: str = Field(
        description="Setting or environment",
        max_length=150
    )
    style: str = Field(
        description="Artistic style (e.g., 'photorealistic', 'minimalist', 'cinematic')",
        max_length=150
    )
    aspect_ratio: ImageAspectRatio = Field(
        default=ImageAspectRatio.LANDSCAPE,
        description="Image aspect ratio"
    )
    additional_details: Optional[str] = Field(
        default=None,
        description="Additional details (lighting, mood, colors, etc.)",
        max_length=300
    )
    negative_prompt: Optional[str] = Field(
        default="blurry, low quality, distorted, watermark",
        description="What to avoid in the image",
        max_length=200
    )

    def to_flux_prompt(self) -> str:
        """Convert structured prompt to FLUX.1-compatible string"""
        parts = [
            self.subject,
            self.composition,
        ]

        if self.action:
            parts.append(self.action)

        parts.extend([self.location, self.style])

        if self.additional_details:
            parts.append(self.additional_details)

        return ", ".join(parts)

    def get_resolution(self) -> tuple[int, int]:
        """Get pixel resolution for aspect ratio"""
        resolutions = {
            ImageAspectRatio.SQUARE: (1024, 1024),
            ImageAspectRatio.LANDSCAPE: (1920, 1088),
            ImageAspectRatio.PORTRAIT: (1088, 1920),
            ImageAspectRatio.WIDE: (2176, 928),
            ImageAspectRatio.ULTRA_WIDE: (2176, 608),
        }
        return resolutions[self.aspect_ratio]

    @field_validator('subject', 'composition', 'location', 'style')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty"""
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Video Script
    script = VideoScript(
        title="5 AI Tools That Will Change Your Workflow",
        hook="Stop wasting 10 hours a week on repetitive tasks",
        scenes=[
            Scene(
                scene_type=SceneType.INTRO,
                description="Dynamic text animation showing '10 hours wasted per week'",
                duration=3,
                camera_movement="zoom in"
            ),
            Scene(
                scene_type=SceneType.CONTENT,
                description="Screen recording showing AI tool #1 in action",
                duration=5,
                voiceover="First up: AI-powered code completion that actually understands context"
            ),
            Scene(
                scene_type=SceneType.CTA,
                description="Call-to-action overlay with 'Try these tools today'",
                duration=3
            ),
        ],
        total_duration=11,
        target_platform="linkedin",
        tags=["ai", "productivity", "automation", "tech"]
    )
    print("✅ VideoScript example:", script.title)

    # Example: Image Prompt
    image = ImagePrompt(
        subject="Arthur Dell branded smartwatch on wooden desk",
        composition="close-up product shot, 45-degree angle",
        action="displaying AI interface on screen",
        location="modern minimalist office with natural lighting",
        style="photorealistic, commercial photography, high-end product photo",
        aspect_ratio=ImageAspectRatio.LANDSCAPE,
        additional_details="soft shadows, warm tones, shallow depth of field"
    )
    print("✅ ImagePrompt example:", image.to_flux_prompt()[:80] + "...")

    # Example: Carousel Plan
    carousel = CarouselPlan(
        title="5 Mistakes Killing Your Productivity",
        subtitle="And how to fix them today",
        target_audience="Busy professionals and entrepreneurs",
        slides=[
            SlideContent(
                slide_number=1,
                heading="Welcome!",
                bullet_points=["You're wasting 10 hours per week", "Here's why"],
                image_prompt="Professional office background, clean modern design, blue and white color scheme"
            ),
        ],
        cta_slide="Ready to 10x your productivity? Follow for more tips",
        linkedin_caption="Most people waste hours on tasks AI could handle. Here are 5 common mistakes..."
    )
    print("✅ CarouselPlan example:", carousel.title)
