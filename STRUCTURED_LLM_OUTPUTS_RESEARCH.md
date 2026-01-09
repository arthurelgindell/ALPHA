# Structured LLM Outputs - Deep Research Report

**Date:** 2026-01-02
**Context:** Production media facility automation for ARTHUR
**Question:** How to achieve Apple's @Generable/@Guide functionality in Python?

---

## 🔍 Key Finding: Instructor Python Library

**The Python ecosystem has a BETTER solution than waiting for Apple bindings.**

---

## Part 1: Apple's Foundation Models Framework Status

### What Apple Provides

**Swift-Only Runtime:**
- [@Generable/@Guide macros](https://developer.apple.com/documentation/FoundationModels) for type-safe LLM outputs
- Streaming support with PartiallyGenerated snapshots
- Swift-native integration with iOS/macOS apps
- **Status:** No Python runtime bindings announced

**Python Adapter Training Toolkit:**
- [Python toolkit for training adapters](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates)
- Compatible with Python 3.11+
- Exports .fmadapter packages for Foundation Models framework
- **Purpose:** Training only, not inference/structured outputs

**Verdict:** Apple's structured output features remain Swift-exclusive for app development.

**Sources:**
- [Updates to Apple's On-Device and Server Foundation Language Models](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates)
- [Foundation Models Framework Documentation](https://developer.apple.com/documentation/FoundationModels)
- [Meet the Foundation Models framework - WWDC25](https://developer.apple.com/videos/play/wwdc2025/286/)

---

## Part 2: Python Ecosystem - Instructor Library

### Overview

**[Instructor](https://python.useinstructor.com/)** is the industry-standard Python library for structured LLM outputs.

**Stats:**
- **3 million downloads/month**
- **11,000+ GitHub stars**
- **100+ contributors**
- **Production deployments:** London Stock Exchange Group (LSEG) uses it for AI-driven market surveillance

**Architecture:**
- Built on Pydantic (Python's type-safe data validation)
- Lightweight patch over official LLM SDKs
- Provider-agnostic (OpenAI, Anthropic, DeepSeek, Ollama, etc.)

---

## Part 3: Instructor + DeepSeek V3 Integration

### Official Support

**[DeepSeek V3 is officially supported](https://python.useinstructor.com/integrations/deepseek/)** by Instructor:

- Native JSON mode (`json_object`)
- OpenAI-compatible function calling
- Streaming structured outputs
- Automatic validation and retries

### Implementation Example

```python
import instructor
from pydantic import BaseModel, Field
from openai import OpenAI

# Initialize with DeepSeek V3
client = instructor.from_openai(
    OpenAI(
        api_key="your-deepseek-key",
        base_url="https://api.deepseek.com/v1"  # Or your Exo cluster URL
    ),
    mode=instructor.Mode.JSON
)

# Define schema (equivalent to Apple's @Generable)
class VideoScript(BaseModel):
    title: str = Field(description="Engaging video title")
    hook: str = Field(description="Opening line, max 10 words", max_length=60)
    scenes: list[Scene] = Field(min_length=3, max_length=5)  # Like @Guide(.count(3...5))
    duration: int = Field(ge=5, le=60)  # Like @Guide(.range(5...60))

class Scene(BaseModel):
    description: str
    duration: int = Field(ge=2, le=15)
    camera_angle: str = Field(description="Wide, medium, or close-up")

# Get structured output (zero JSON parsing!)
script = client.chat.completions.create(
    model="deepseek-v3-4bit",  # Or your Exo model ID
    response_model=VideoScript,
    messages=[
        {"role": "user", "content": "Create a product demo script for a smartwatch"}
    ]
)

# script is a validated VideoScript object, ready to use
print(script.title)  # Type-safe!
print(script.scenes[0].camera_angle)  # No JSON parsing errors!
```

---

## Part 4: Streaming Support (Apple's PartiallyGenerated Equivalent)

### Partial Objects

```python
from instructor import Partial

# Stream progressive updates
for partial_script in client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=Partial[VideoScript],
    messages=[{"role": "user", "content": "Create video script"}],
    stream=True
):
    # UI updates in real-time as LLM generates
    if partial_script.title:
        print(f"Title: {partial_script.title}")
    if partial_script.scenes:
        print(f"Scenes so far: {len(partial_script.scenes)}")

# Final object is fully populated and validated
```

### Streaming Lists (Iterable)

```python
from typing import Iterable

class Slide(BaseModel):
    heading: str
    image_prompt: str = Field(description="SCALS format for FLUX.1")
    bullets: list[str] = Field(min_length=1, max_length=3)

# Stream slides as they're generated
for slide in client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=Iterable[Slide],
    messages=[{"role": "user", "content": "Create 5 LinkedIn carousel slides about AI"}],
    stream=True
):
    # Process each slide immediately (don't wait for all 5)
    print(f"Generated slide: {slide.heading}")
    # Could trigger FLUX.1 image generation here
    generate_image(slide.image_prompt)
```

**Sources:**
- [Instructor - Multi-Language Library](https://python.useinstructor.com/)
- [Streaming Lists Documentation](https://python.useinstructor.com/learning/streaming/lists/)
- [DeepSeek Integration Guide](https://python.useinstructor.com/integrations/deepseek/)

---

## Part 5: ARTHUR Production Use Cases

### Use Case 1: Video Script Generation

```python
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI

# Connect to Exo cluster running DeepSeek V3
client = instructor.from_openai(
    OpenAI(base_url="http://localhost:52415/v1"),
    mode=instructor.Mode.JSON
)

class VideoScript(BaseModel):
    """LinkedIn video script with product placement"""
    hook: str = Field(
        description="Attention-grabbing first line",
        max_length=60
    )
    problem: str = Field(description="Pain point the product solves")
    solution: str = Field(description="How the product helps")
    call_to_action: str = Field(description="What viewer should do next")

    arthur_dell_branding: str = Field(
        description="Natural product placement mentioning Arthur Dell",
        pattern=".*Arthur Dell.*"  # Ensures brand name appears
    )

    duration: int = Field(
        ge=5, le=15,
        description="Total video duration in seconds"
    )

# Generate with validation
script = client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=VideoScript,
    messages=[
        {"role": "system", "content": "You create engaging LinkedIn video scripts with subtle product placement."},
        {"role": "user", "content": "Video about productivity tools for remote teams"}
    ]
)

# Guaranteed valid, type-safe output
print(f"Hook: {script.hook}")
print(f"Duration: {script.duration}s")

# Generate video on GAMMA
generate_video_on_gamma(
    prompt=f"{script.hook}. {script.problem}. {script.solution}.",
    duration=script.duration
)
```

### Use Case 2: Carousel Content Planning with FLUX.1 Integration

```python
class CarouselSlide(BaseModel):
    heading: str = Field(max_length=40, description="Short, punchy heading")
    subheading: str = Field(max_length=80)

    flux_prompt: str = Field(
        description="Image prompt following SCALS format: Subject, Composition, Action, Location, Style"
    )

    bullets: list[str] = Field(
        min_length=2, max_length=3,
        description="Key points, each max 60 chars"
    )

class CarouselPlan(BaseModel):
    title: str = Field(description="Carousel main topic")
    slides: list[CarouselSlide] = Field(
        min_length=5, max_length=10,
        description="Individual slides"
    )

# Generate carousel plan
carousel = client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=CarouselPlan,
    messages=[
        {"role": "user", "content": "LinkedIn carousel: 'AI in Healthcare 2026'"}
    ]
)

# Execute production pipeline
for i, slide in enumerate(carousel.slides):
    # Generate image with FLUX.1
    image_path = generate_flux_image(
        prompt=slide.flux_prompt,
        output=f"carousel_slide_{i+1}.png"
    )

    # Compose text overlay
    create_carousel_image(
        background=image_path,
        heading=slide.heading,
        subheading=slide.subheading,
        bullets=slide.bullets,
        output=f"carousel_final_{i+1}.png"
    )

print(f"✅ Generated {len(carousel.slides)} carousel images")
```

### Use Case 3: Automated Content Workflow

```python
class ContentPipeline(BaseModel):
    """Complete content production pipeline"""

    class ImageGeneration(BaseModel):
        prompt: str = Field(description="SCALS-formatted FLUX.1 prompt")
        preset: str = Field(pattern="^(square|16:9-large|9:16-story)$")
        output_filename: str

    class VideoGeneration(BaseModel):
        prompt: str = Field(description="HunyuanVideo cinematic description")
        quality: str = Field(pattern="^(test|medium|high|maximum)$")
        num_frames: int = Field(ge=25, le=97)

    content_type: str = Field(pattern="^(image|video|carousel)$")
    image: ImageGeneration | None = None
    video: VideoGeneration | None = None

    post_caption: str = Field(
        max_length=3000,
        description="LinkedIn post text with hashtags"
    )

# AI generates the entire pipeline
pipeline = client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=ContentPipeline,
    messages=[
        {"role": "user", "content": "Create content for 'Remote Work Best Practices' - decide if image or video is better"}
    ]
)

# Execute pipeline
if pipeline.content_type == "image" and pipeline.image:
    generate_flux_image(
        prompt=pipeline.image.prompt,
        preset=pipeline.image.preset,
        output=pipeline.image.output_filename
    )
elif pipeline.content_type == "video" and pipeline.video:
    generate_gamma_video(
        prompt=pipeline.video.prompt,
        quality=pipeline.video.quality,
        num_frames=pipeline.video.num_frames
    )

# Post to LinkedIn with caption
publish_to_linkedin(
    media=pipeline.image.output_filename if pipeline.image else None,
    caption=pipeline.post_caption
)
```

---

## Part 6: Advanced Features vs Apple's Framework

### Feature Comparison

| Feature | Apple @Generable | Instructor (Python) | Winner |
|---------|------------------|---------------------|--------|
| **Type Safety** | ✅ Swift types | ✅ Pydantic models | Tie |
| **Validation** | ✅ @Guide constraints | ✅ Field validators | Tie |
| **Streaming** | ✅ PartiallyGenerated | ✅ Partial[T] + Iterable[T] | Tie |
| **Multi-Provider** | ❌ Apple models only | ✅ 15+ providers | **Instructor** |
| **Retries** | ❌ Manual | ✅ Automatic with Tenacity | **Instructor** |
| **Local Inference** | ✅ On-device | ✅ Via Exo/Ollama | Tie |
| **Production Ready** | ⚠️ Swift apps only | ✅ Python scripts/APIs | **Instructor** |
| **Open Source** | ❌ Proprietary | ✅ MIT license | **Instructor** |

### Instructor-Exclusive Features

**1. Automatic Retries with Validation**
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def generate_with_retry(prompt: str) -> VideoScript:
    return client.chat.completions.create(
        model="deepseek-v3-4bit",
        response_model=VideoScript,
        messages=[{"role": "user", "content": prompt}]
    )
    # Automatically retries on validation failures
```

**2. Observability/Tracing**
```python
from langfuse import Langfuse

# Track all LLM calls in production
langfuse = Langfuse()
client = instructor.from_openai(
    OpenAI(base_url="http://localhost:52415/v1"),
    mode=instructor.Mode.JSON
)
# All structured outputs logged to Langfuse dashboard
```

**3. Union Types (Multiple Valid Schemas)**
```python
from typing import Union

class ImageContent(BaseModel):
    type: str = "image"
    prompt: str
    preset: str

class VideoContent(BaseModel):
    type: str = "video"
    prompt: str
    quality: str

# Let LLM decide which type to return
content = client.chat.completions.create(
    model="deepseek-v3-4bit",
    response_model=Union[ImageContent, VideoContent],
    messages=[{"role": "user", "content": "Create content about AI"}]
)

# Type-safe discriminated union
if isinstance(content, ImageContent):
    generate_flux_image(content.prompt)
elif isinstance(content, VideoContent):
    generate_gamma_video(content.prompt)
```

---

## Part 7: Alternatives Comparison

### Other Python Libraries

| Library | Best For | Pros | Cons |
|---------|----------|------|------|
| **[Instructor](https://python.useinstructor.com/)** | Production APIs | Mature, multi-provider, great docs | Requires API/Exo |
| **[Outlines](https://github.com/outlines-dev/outlines)** | Self-hosted models | Fastest (constrained generation) | Complex setup |
| **[Guidance (llguidance)](https://github.com/guidance-ai/llguidance)** | Complex grammars | Most flexible | Steep learning curve |
| **OpenAI Structured Outputs** | OpenAI-only | Native integration | Vendor lock-in |
| **Pydantic AI** | Simple use cases | Lightweight | Limited features |

**Recommendation for ARTHUR:** **Instructor** (works with Exo cluster, battle-tested, excellent documentation)

**Sources:**
- [The best library for structured LLM output](https://simmering.dev/blog/structured_output/)
- [Python libraries for LLM structured outputs](https://medium.com/@docherty/python-libraries-for-llm-structured-outputs-beyond-langchain-621225e48399)
- [Why Instructor is the Best Library](https://python.useinstructor.com/blog/2024/03/05/zero-cost-abstractions/)

---

## Part 8: Implementation Plan for ARTHUR

### Phase 1: Install and Test (Today)

```bash
# Install Instructor
pip install instructor

# Test with Exo cluster
python3 << 'EOF'
import instructor
from pydantic import BaseModel, Field
from openai import OpenAI

client = instructor.from_openai(
    OpenAI(base_url="http://localhost:52415/v1", api_key="not-needed"),
    mode=instructor.Mode.JSON
)

class TestOutput(BaseModel):
    response: str = Field(max_length=50)

result = client.chat.completions.create(
    model="llama-3.2-1b",
    response_model=TestOutput,
    messages=[{"role": "user", "content": "Say hello"}]
)

print(f"✅ Structured output working: {result.response}")
EOF
```

### Phase 2: Create Reusable Schemas (This Week)

**File:** `/Users/arthurdell/ARTHUR/schemas/content_schemas.py`

```python
"""Type-safe schemas for ARTHUR production workflows"""
from pydantic import BaseModel, Field
from typing import Literal

class FluxImagePrompt(BaseModel):
    """SCALS-formatted image generation prompt"""
    subject: str = Field(description="Materiality with specificity")
    composition: str = Field(description="Lens focal length, camera angle")
    action: str = Field(description="Active verbs, physical interactions")
    location: str = Field(description="Lighting sources, environment")
    style: str = Field(description="Artistic era, media type")

    @property
    def full_prompt(self) -> str:
        return f"{self.subject}, {self.composition}, {self.action}, {self.location}, {self.style}"

class VideoScript(BaseModel):
    """HunyuanVideo cinematic video script"""
    cinematography: str = Field(description="Shot type, movement")
    subject: str = Field(description="Main subject description")
    action: str = Field(description="What's happening")
    context: str = Field(description="Environment, setting")
    style: str = Field(description="Mood, ambiance, audio")

    quality: Literal["test", "medium", "high", "maximum"] = "high"
    num_frames: int = Field(ge=25, le=97, default=61)

class CarouselSlide(BaseModel):
    """Individual carousel slide"""
    heading: str = Field(max_length=40)
    subheading: str = Field(max_length=80)
    image_prompt: FluxImagePrompt
    bullets: list[str] = Field(min_length=2, max_length=3)

class CarouselPlan(BaseModel):
    """Complete carousel with 5-10 slides"""
    title: str
    subtitle: str = Field(max_length=100)
    slides: list[CarouselSlide] = Field(min_length=5, max_length=10)

    post_caption: str = Field(
        max_length=3000,
        description="LinkedIn post text with hashtags"
    )
```

### Phase 3: Integrate with Production Scripts (Next Week)

Update existing scripts to use structured outputs:

```python
# scripts/create_carousel_ai.py
import instructor
from openai import OpenAI
from schemas.content_schemas import CarouselPlan
from generate_image import generate_flux_image

client = instructor.from_openai(
    OpenAI(base_url="http://localhost:52415/v1", api_key="not-needed"),
    mode=instructor.Mode.JSON
)

def create_carousel_from_topic(topic: str) -> str:
    """Generate entire carousel from topic using AI"""

    # Get structured plan
    plan = client.chat.completions.create(
        model="deepseek-v3-4bit",
        response_model=CarouselPlan,
        messages=[
            {"role": "system", "content": "You create engaging LinkedIn carousels with SCALS-formatted image prompts."},
            {"role": "user", "content": f"Create carousel about: {topic}"}
        ]
    )

    # Execute production pipeline
    for i, slide in enumerate(plan.slides):
        # Generate image with FLUX.1
        generate_flux_image(
            prompt=slide.image_prompt.full_prompt,
            output=f"carousel_{i+1}.png"
        )

    print(f"✅ Generated {len(plan.slides)} slides")
    print(f"LinkedIn caption:\n{plan.post_caption}")

    return plan.post_caption

# Usage
if __name__ == "__main__":
    create_carousel_from_topic("AI Video Generation in 2026")
```

---

## Conclusion

### Key Findings

1. **Apple's Foundation Models:** Swift-only for structured outputs (no Python runtime)
2. **Python Solution:** Instructor library is production-ready and superior
3. **DeepSeek V3 Support:** Official integration with Instructor
4. **ARTHUR Integration:** Can use with Exo cluster today

### Recommendations

✅ **Adopt Instructor immediately** - No need to wait for Apple bindings

**Benefits over waiting for Apple:**
- Works today with DeepSeek V3 on Exo cluster
- Multi-provider (can switch between DeepSeek, Claude, etc.)
- Open source (MIT license)
- Production-proven (LSEG uses it)
- Better features (automatic retries, observability)

**Implementation:**
1. Install: `pip install instructor`
2. Test with Llama 3.2 1B (today)
3. Create schemas (this week)
4. Integrate with production scripts (next week)

---

## Sources

### Apple Documentation
- [Updates to Apple Foundation Models (2025)](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates)
- [Foundation Models Framework](https://developer.apple.com/documentation/FoundationModels)
- [WWDC25 - Meet Foundation Models](https://developer.apple.com/videos/play/wwdc2025/286/)

### Instructor Library
- [Instructor Homepage](https://python.useinstructor.com/)
- [GitHub Repository](https://github.com/567-labs/instructor)
- [DeepSeek Integration Guide](https://python.useinstructor.com/integrations/deepseek/)
- [Streaming Documentation](https://python.useinstructor.com/learning/streaming/lists/)

### Comparisons & Analysis
- [Best library for structured LLM output](https://simmering.dev/blog/structured_output/)
- [Python libraries beyond LangChain](https://medium.com/@docherty/python-libraries-for-llm-structured-outputs-beyond-langchain-621225e48399)
- [Why Instructor is Best](https://python.useinstructor.com/blog/2024/03/05/zero-cost-abstractions/)

---

**Status:** Ready for immediate implementation with Exo cluster
**Next Action:** Install Instructor and test with DeepSeek V3
