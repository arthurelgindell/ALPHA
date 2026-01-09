# LinkedIn Carousel V1.0 - Quick Start Guide

**Version:** 1.0 Production
**Status:** ✅ Ready to Use

---

## 🚀 Generate Production Carousel (One Command)

```bash
cd /Users/arthurdell/ARTHUR
python3 scripts/create_production_carousel.py
```

**Output:** Production carousel with 8 images in `carousels/` folder
**Time:** ~20 minutes (12-15 min images + 5 min assembly)

---

## 📋 Production Standards V1.0

| Standard | Value |
|----------|-------|
| **Format** | 1080x1080 (1:1) |
| **Model** | FLUX.1 [dev] 30 steps |
| **Slides** | 8 total |
| **Text Position** | Bottom-aligned (flex-end) |
| **Padding** | 5rem bottom |
| **Branding** | Subtle "Arthur Dell" in images |
| **File Size** | 10-20 MB |

---

## ✅ Quality Checklist

Before uploading to LinkedIn:

- [ ] No blank first page
- [ ] All 8 slides have images
- [ ] Text at bottom of slides
- [ ] Arthur Dell signature on all slides
- [ ] File size 10-20 MB
- [ ] Text readable on mobile

---

## 📁 Key Files

**Production Template:**
```
/ARTHUR/CAROUSEL_PRODUCTION_V1.0_TEMPLATE.md
```

**Production Script:**
```
/ARTHUR/scripts/create_production_carousel.py
```

**Latest Carousel:**
```
/ARTHUR/carousels/2026_PRODUCTION_FINAL.pdf
```

---

## 🔧 Quick Fixes

**Blank First Page?**
- First slide must be in headmatter (no extra `---`)

**Images Not Showing?**
- Check: `linkedin-carousels/public/images/`
- Use CSS `background-image` for first slide

**Text Too Centered?**
- Use `justify-content: flex-end`
- Add `padding-bottom: 5rem`

---

## 📊 8-Slide Structure (Proven)

1. **Cover** - Hook/Title
2. **Data 1** - Key statistic
3. **Data 2** - Supporting stat
4. **Context** - Why it matters
5. **Problem** - Gap/Challenge
6. **Choice** - Decision point
7. **Quote** - Inspiration
8. **CTA** - Clear action

---

**Version:** 1.0
**Last Updated:** 2025-12-31
