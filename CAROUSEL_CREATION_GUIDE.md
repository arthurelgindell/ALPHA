# LinkedIn PDF Carousel Creation Guide

**System:** ARTHUR Image Generation + Slidev Carousel Assembly
**Status:** Production Ready ✅
**Date:** 2025-12-30

---

## Quick Start

Create a LinkedIn-ready PDF carousel in 3 simple steps:

### 1. Plan Your Carousel
```bash
cd /Users/arthurdell/ARTHUR
python3 scripts/carousel_planner.py --example
```

### 2. Create Carousel from Existing Images
```python
from scripts.create_carousel import CarouselGenerator, Slide

generator = CarouselGenerator()

slides = [
    Slide(layout="cover", title="Your Title", subtitle="Your Subtitle"),
    Slide(layout="message", title="Key Message", image="path/to/image.png", overlay=True),
    Slide(layout="stat", stat="56%", label="Growth", description="Your description"),
    Slide(layout="closing", title="Call to Action", cta="Connect")
]

pdf_path = generator.create_carousel(slides, "Your Carousel Title", "output.pdf")
```

### 3. Upload to LinkedIn
- Open LinkedIn → Create post
- Click "Add a document" → Upload PDF
- Add post copy
- Publish

---

## System Architecture

### Complete Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Content Planning                                    │
│     → Topic selection                                   │
│     → Message definition (storyboard methodology)       │
│     → Slide breakdown (8-10 recommended)               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. AI Image Generation (Optional)                      │
│     → FLUX.1 [schnell] for speed (30s/image)          │
│     → FLUX.1 [dev] for quality (90s/image)            │
│     → Output: /ARTHUR/images/*.png                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Carousel Assembly (Python)                          │
│     → create_carousel.py generates slides.md           │
│     → Applies Arthur Dell brand theme                  │
│     → Copies images to Slidev public folder            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. PDF Export (Slidev + Playwright)                   │
│     → Renders slides in Chromium                       │
│     → Exports multi-page PDF                           │
│     → Output: /ARTHUR/carousels/*.pdf                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  5. LinkedIn Upload                                     │
│     → Manual upload or future automation               │
└─────────────────────────────────────────────────────────┘
```

---

## Slide Layout Options

### Available Layouts

| Layout | Purpose | Best For | Image Required |
|--------|---------|----------|----------------|
| `cover` | Title slide with hero image | First slide, introduction | Optional |
| `message` | Image + text overlay | Visual storytelling, key messages | Yes |
| `stat` | Large statistic display | Data-driven insights, numbers | No |
| `quote` | Highlighted quote | Testimonials, key insights | No |
| `closing` | Call-to-action | Final slide, next steps | No |

### Layout Details

#### 1. Cover Layout
```python
Slide(
    layout="cover",
    title="Your Main Title",
    subtitle="Compelling subtitle here",
    image="/path/to/hero-image.png"  # Optional
)
```

**When to use:**
- First slide of every carousel
- Sets tone and expectations
- Grabs attention immediately

**Tips:**
- Keep title under 6 words
- Subtitle provides context (1-2 lines)
- Use high-impact hero image

---

#### 2. Message Layout
```python
Slide(
    layout="message",
    title="Your Key Message",
    subtitle="Supporting detail",
    image="/path/to/image.png",
    overlay=True  # Text overlays on image
)
```

**When to use:**
- Visual storytelling
- Illustrating concepts
- Showing real-world examples

**Tips:**
- Image should support the message
- Set `overlay=True` for text on image
- Keep message focused (one idea per slide)

---

#### 3. Stat Layout
```python
Slide(
    layout="stat",
    stat="56%",
    label="Earnings Premium",
    description="AI-skilled workers earn significantly more",
    background="bg-gradient-blue"  # Optional
)
```

**When to use:**
- Highlighting key statistics
- Data-driven insights
- Creating visual impact with numbers

**Background options:**
- `bg-gradient-blue` (default)
- `bg-gradient-green`
- `bg-gradient-dark`

**Tips:**
- Make stat large and prominent
- Label provides context
- Description explains significance

---

#### 4. Quote Layout
```python
Slide(
    layout="quote",
    title="Your impactful quote here",
    author="Optional attribution"  # Optional
)
```

**When to use:**
- Testimonials
- Inspirational messages
- Key insights or principles

**Tips:**
- Keep quote concise (under 20 words)
- Author attribution adds credibility
- Use for emotional impact

---

#### 5. Closing Layout
```python
Slide(
    layout="closing",
    title="Take Action Today",
    subtitle="What's your next step?",
    cta="Connect with Arthur Dell",
    background="bg-gradient-dark"  # Optional
)
```

**When to use:**
- Final slide (always)
- Call-to-action
- Next steps for audience

**Tips:**
- Clear, specific CTA
- Creates urgency
- Makes engagement easy

---

## Complete Examples

### Example 1: Thought Leadership Carousel

```python
from scripts.create_carousel import CarouselGenerator, Slide

generator = CarouselGenerator()

slides = [
    # Slide 1: Cover
    Slide(
        layout="cover",
        title="2026 AI Trends",
        subtitle="What You Need to Know",
        image="/Users/arthurdell/ARTHUR/images/hero_ai_trends.png"
    ),

    # Slide 2: Intro message
    Slide(
        layout="message",
        title="AI Adoption Accelerates",
        subtitle="56% of companies investing heavily",
        image="/Users/arthurdell/ARTHUR/images/ai_adoption.png",
        overlay=True
    ),

    # Slide 3: Key stat
    Slide(
        layout="stat",
        stat="3.2x",
        label="Productivity Gain",
        description="Organizations using AI see triple productivity",
        background="bg-gradient-blue"
    ),

    # Slide 4: Second message
    Slide(
        layout="message",
        title="The Skills Gap Widens",
        subtitle="17% ready vs. 42% affected",
        image="/Users/arthurdell/ARTHUR/images/skills_gap.png",
        overlay=True
    ),

    # Slide 5: Quote
    Slide(
        layout="quote",
        title="The future belongs to those who prepare today"
    ),

    # Slide 6: Closing CTA
    Slide(
        layout="closing",
        title="Ready to Lead?",
        subtitle="Don't get left behind",
        cta="Connect with Arthur Dell"
    )
]

pdf = generator.create_carousel(
    slides=slides,
    title="2026 AI Trends",
    output_filename="ai_trends_2026.pdf"
)
```

---

### Example 2: Service Showcase

```python
slides = [
    Slide(layout="cover", title="AI Transformation Services", subtitle="Your Partner in Innovation"),

    Slide(layout="message", title="Strategy & Planning",
          subtitle="Roadmap to AI excellence",
          image="service_strategy.png", overlay=True),

    Slide(layout="message", title="Team Training",
          subtitle="Upskill your workforce",
          image="service_training.png", overlay=True),

    Slide(layout="message", title="Implementation",
          subtitle="End-to-end execution",
          image="service_implementation.png", overlay=True),

    Slide(layout="stat", stat="10x", label="ROI",
          description="Average client return on investment"),

    Slide(layout="closing", title="Let's Work Together",
          subtitle="Transform your business with AI",
          cta="Schedule Consultation")
]

generator.create_carousel(slides, "AI Services", "ai_services_showcase.pdf")
```

---

### Example 3: Case Study

```python
slides = [
    Slide(layout="cover", title="Client Success Story",
          subtitle="Fortune 500 Transformation"),

    Slide(layout="message", title="The Challenge",
          subtitle="Legacy systems holding back growth",
          image="case_before.png", overlay=True),

    Slide(layout="message", title="The Solution",
          subtitle="AI-powered modernization",
          image="case_solution.png", overlay=True),

    Slide(layout="stat", stat="300%", label="ROI",
          description="Achieved within 6 months"),

    Slide(layout="stat", stat="50%", label="Time Saved",
          description="On routine operations"),

    Slide(layout="quote",
          title="Arthur Dell transformed our entire approach to operations",
          author="CTO, Fortune 500 Company"),

    Slide(layout="closing", title="Your Turn",
          subtitle="Start your transformation journey",
          cta="Get Started")
]

generator.create_carousel(slides, "Case Study", "client_case_study.pdf")
```

---

## Best Practices

### LinkedIn Optimization

**Slide Count:**
- Sweet spot: 8-10 slides
- Minimum: 5 slides (maintains interest)
- Maximum: 12 slides (avoid attention drop)

**Dimensions:**
- Format: 1080x1080 (square)
- LinkedIn compatible
- Instagram compatible

**File Size:**
- Target: < 5 MB
- LinkedIn limit: 100 MB
- Smaller files = faster loading

**First Slide:**
- Clear value proposition
- Users decide in 3 seconds
- High-impact visuals

**Last Slide:**
- Strong CTA
- Clear next step
- Easy engagement

### Content Strategy

**One Message Per Slide:**
- Follow storyboard methodology
- Single focused idea
- Avoid information overload

**Readable Text:**
- Minimum 24pt equivalent
- High contrast with background
- Test on mobile device

**Progressive Narrative:**
- Build story across slides
- Logical flow
- Clear beginning, middle, end

**Brand Consistency:**
- Arthur Dell signature on every slide
- Consistent color scheme
- Professional typography

### Image Quality

**For Speed:**
- Use FLUX.1 [schnell]
- 30 seconds per image
- Good for iteration

**For Quality:**
- Use FLUX.1 [dev]
- 90 seconds per image
- Use for final deliverables

**Format:**
- Preset: `1:1` for LinkedIn
- Resolution: 1024x1024 or higher
- Format: PNG (supports transparency)

**Text in Images:**
- Avoid complex text in AI-generated images
- Use Slidev overlays for text
- Guarantees spelling accuracy

---

## Advanced Usage

### Generating Images + Carousel Together

```python
from scripts.create_carousel import CarouselGenerator, Slide

generator = CarouselGenerator()

# 1. Generate images for new topic
prompts = [
    "Professional presenting AI strategy to executives, modern boardroom, photorealistic, 8k",
    "Data scientist analyzing AI models on multiple screens, tech office, photorealistic, 8k",
    "Corporate team collaborating with AI tools, innovative workspace, photorealistic, 8k"
]

images = generator.generate_images(prompts, model="schnell", preset="1:1")

# 2. Create slides with generated images
slides = [
    Slide(layout="cover", title="AI Strategy 2026", subtitle="Executive Roadmap"),
    Slide(layout="message", title="Leadership Buy-In", image=str(images[0]), overlay=True),
    Slide(layout="message", title="Data-Driven Decisions", image=str(images[1]), overlay=True),
    Slide(layout="message", title="Team Enablement", image=str(images[2]), overlay=True),
    Slide(layout="closing", title="Start Your Journey", cta="Contact Us")
]

# 3. Export PDF
generator.create_carousel(slides, "AI Strategy 2026", "ai_strategy_2026.pdf")
```

### Using Carousel Planner

```python
from scripts.carousel_planner import CarouselPlanner

planner = CarouselPlanner()

# Create structured plan
plan = planner.create_plan(
    topic="Future of Work 2026",
    slide_count=8,
    messages=[
        "Remote work becomes the default",
        "AI handles 40% of knowledge work",
        "Upskilling is mandatory, not optional",
        "Companies compete on culture, not location"
    ]
)

# Print summary
planner.print_plan_summary(plan)

# Validate against methodology
issues = planner.validate_against_methodology(plan)
for issue in issues:
    print(issue)

# Save for reference
planner.save_plan(plan, "future_of_work_plan")
```

---

## Troubleshooting

### Issue: PDF Not Generating

**Symptoms:**
- Command completes but no PDF file
- Error: "Export failed"

**Solutions:**
1. Check Slidev installation:
   ```bash
   cd /Users/arthurdell/ARTHUR/linkedin-carousels
   npm run build
   ```

2. Verify Playwright installed:
   ```bash
   npx playwright install chromium
   ```

3. Check for syntax errors in slides.md:
   ```bash
   cat /Users/arthurdell/ARTHUR/linkedin-carousels/slides.md
   ```

---

### Issue: Images Not Appearing in PDF

**Symptoms:**
- PDF generates but images missing
- Blank spaces where images should be

**Solutions:**
1. Verify image paths are correct:
   ```python
   from pathlib import Path
   img_path = Path("/Users/arthurdell/ARTHUR/images/your_image.png")
   print(f"Exists: {img_path.exists()}")
   ```

2. Check images copied to Slidev public folder:
   ```bash
   ls /Users/arthurdell/ARTHUR/linkedin-carousels/public/images/
   ```

3. Check image file size (very large images may timeout):
   ```bash
   ls -lh /Users/arthurdell/ARTHUR/images/*.png
   ```

---

### Issue: Text Overlay Not Visible

**Symptoms:**
- Text blends with background
- Hard to read on certain images

**Solutions:**
1. Increase overlay opacity in CSS:
   ```css
   /* arthur-dell-theme.css */
   .text-overlay {
     background: rgba(0, 0, 0, 0.6); /* Increase from 0.4 */
   }
   ```

2. Add stronger text shadow:
   ```css
   .text-overlay h1 {
     text-shadow: 3px 3px 12px rgba(0, 0, 0, 1);
   }
   ```

3. Test on mobile view (LinkedIn preview)

---

### Issue: PDF File Too Large

**Symptoms:**
- PDF > 10 MB
- Slow LinkedIn upload

**Solutions:**
1. Reduce image resolution before adding to carousel
2. Use JPEG instead of PNG for photos (smaller)
3. Reduce number of high-resolution images

---

### Issue: Export Times Out

**Symptoms:**
- Command hangs
- Timeout error after 90 seconds

**Solutions:**
1. Increase timeout in create_carousel.py:
   ```python
   cmd = [
       "npx", "slidev", "export",
       "--timeout", "180000"  # 3 minutes
   ]
   ```

2. Reduce number of slides
3. Use smaller images

---

## File Locations

### Key Directories

```
/Users/arthurdell/ARTHUR/
│
├── linkedin-carousels/          # Slidev project
│   ├── slides.md                # Generated by create_carousel.py
│   ├── styles/
│   │   └── arthur-dell-theme.css
│   ├── layouts/
│   │   ├── cover.vue
│   │   ├── message.vue
│   │   ├── stat.vue
│   │   ├── quote.vue
│   │   └── closing.vue
│   ├── components/
│   │   ├── BrandSignature.vue
│   │   └── ProgressIndicator.vue
│   └── public/
│       └── images/              # Images copied here automatically
│
├── scripts/
│   ├── generate_image.py        # AI image generation
│   ├── create_carousel.py       # Carousel automation
│   ├── carousel_planner.py      # Content planning
│   └── test_carousel_system.py  # Testing
│
├── images/                       # Source images
│   ├── storyboard_*.png         # Production storyboard images
│   └── carousel_slide_*.png     # Carousel-specific images
│
├── carousels/                    # Output PDFs
│   ├── *.pdf                    # LinkedIn-ready carousels
│   └── *.json                   # Carousel plans
│
├── STORYBOARD_METHODOLOGY.md     # Quality standards
├── CAROUSEL_CREATION_GUIDE.md    # This guide
└── IMAGE_GENERATION_README.md    # AI image generation guide
```

---

## Command Reference

### Testing

```bash
# Run full test suite
python3 scripts/test_carousel_system.py

# Generate example carousel
python3 scripts/create_carousel.py --example

# Generate example plan
python3 scripts/carousel_planner.py --example
```

### Image Generation

```bash
# Generate single image (square format for LinkedIn)
python3 scripts/generate_image.py "your prompt" --preset 1:1 --model schnell

# High quality (use dev model)
python3 scripts/generate_image.py "your prompt" --preset 1:1 --model dev --steps 30
```

### Carousel Assembly

```python
# In Python script or interactive session
from scripts.create_carousel import CarouselGenerator, Slide

generator = CarouselGenerator()
# ... define slides ...
pdf = generator.create_carousel(slides, "Title", "output.pdf")
```

---

## Performance Metrics

### Expected Timings

| Task | Model/Tool | Duration |
|------|------------|----------|
| Single image (fast) | FLUX.1 schnell | 30s |
| Single image (quality) | FLUX.1 dev | 90s |
| Carousel assembly | Python | 2-5s |
| PDF export (3 slides) | Slidev | 10-15s |
| PDF export (8 slides) | Slidev | 20-30s |
| **Total (existing images)** | **8-slide carousel** | **30-40s** |
| **Total (new images + carousel)** | **3 new images + carousel** | **2-3 min** |

### File Sizes

| Content Type | Typical Size |
|-------------|--------------|
| Text-only slide | 1-2 KB |
| Slide with image | 5-10 KB |
| Full carousel (8 slides, 3 images) | 15-30 KB |
| Source image (PNG, 1024x1024) | 1-2 MB |

---

## Quality Checklist

Before publishing to LinkedIn:

- [ ] **Content Quality**
  - [ ] Each slide tells one clear story
  - [ ] Progressive narrative throughout
  - [ ] Strong opening (slide 1)
  - [ ] Clear CTA (final slide)

- [ ] **Visual Quality**
  - [ ] Images are high resolution
  - [ ] Text is readable on mobile
  - [ ] Brand signature on all slides
  - [ ] Consistent color scheme

- [ ] **Technical Quality**
  - [ ] PDF exports successfully
  - [ ] File size < 5 MB
  - [ ] All images display correctly
  - [ ] Text overlays visible

- [ ] **LinkedIn Optimization**
  - [ ] 8-10 slides (ideal range)
  - [ ] 1080x1080 format
  - [ ] First slide grabs attention
  - [ ] Last slide has clear CTA

---

## Integration with Existing Workflow

This carousel system integrates seamlessly with your existing ARTHUR image generation infrastructure:

1. **Image Generation** (Already operational)
   - FLUX.1 models via MLX
   - Storyboard methodology
   - Production-quality outputs

2. **Carousel Assembly** (New - This system)
   - Python automation
   - Slidev + Playwright
   - Brand-consistent layouts

3. **LinkedIn Publishing** (Manual or future automation)
   - Direct PDF upload
   - Post copy generation
   - Analytics tracking

---

## Next Steps

### Immediate Actions:
1. Generate your first production carousel:
   ```bash
   python3 scripts/create_carousel.py --example
   ```

2. Review output in `/Users/arthurdell/ARTHUR/carousels/`

3. Upload to LinkedIn and track engagement

### Short-term (Week 1):
1. Create 3 different carousel types (thought leadership, service showcase, case study)
2. Test different layouts and messages
3. Track which formats perform best

### Long-term (Month 1+):
1. Build library of 15-20 carousel templates
2. Create content calendar
3. Develop metrics dashboard
4. Consider API automation for posting

---

## Support & Resources

### Documentation:
- **This Guide:** `/Users/arthurdell/ARTHUR/CAROUSEL_CREATION_GUIDE.md`
- **Image Generation:** `/Users/arthurdell/ARTHUR/IMAGE_GENERATION_README.md`
- **Storyboard Methodology:** `/Users/arthurdell/ARTHUR/STORYBOARD_METHODOLOGY.md`

### Example Scripts:
- **create_carousel.py:** Complete carousel generation
- **carousel_planner.py:** Content planning helper
- **test_carousel_system.py:** Validation testing

### External Resources:
- [Slidev Documentation](https://sli.dev)
- [FLUX.1 Models](https://blackforestlabs.ai)
- [LinkedIn Carousel Best Practices](https://www.linkedin.com/business/marketing/blog/content-marketing/carousel-posts)

---

## Frequently Asked Questions

### Can I customize the brand colors?

Yes! Edit `/Users/arthurdell/ARTHUR/linkedin-carousels/styles/arthur-dell-theme.css`:

```css
:root {
  --ad-primary: #YOUR_COLOR;
  --ad-secondary: #YOUR_COLOR;
  --ad-accent: #YOUR_COLOR;
}
```

### Can I create custom layouts?

Yes! Add new Vue components in `/Users/arthurdell/ARTHUR/linkedin-carousels/layouts/`:

```vue
<!-- custom-layout.vue -->
<template>
  <div class="custom-layout">
    <!-- Your layout design -->
  </div>
</template>
```

### Can I automate LinkedIn posting?

LinkedIn's API has limitations, but you can:
1. Use LinkedIn's official API (requires app approval)
2. Use browser automation (Selenium/Playwright)
3. Manual upload is often most reliable

### How do I track carousel performance?

LinkedIn provides analytics:
- Views
- Clicks
- Engagement rate
- Demographics

Access via LinkedIn post insights.

---

**Status:** Production Ready ✅
**Version:** 1.0
**Last Updated:** 2025-12-30
**System:** ARTHUR Image Generation + Slidev Carousel Assembly
