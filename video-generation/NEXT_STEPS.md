# Video Generation - Recommended Next Steps

**Status:** Root cause identified - MPS incompatibility with Wan 2.2
**Date:** 2025-12-31

---

## Quick Summary

**The Problem:** Wan 2.2 A14B doesn't work with PyTorch MPS backend on Apple Silicon. It produced 4.6 hours of blue noise because MPS doesn't support the data types the model requires (Float8 and complex128).

**The Good News:** This is a known issue with documented workarounds.

**The Bad News:** There's no quick fix for Wan 2.2 + MPS. Need to pivot strategy.

---

## Option Matrix

| Option | Time to Test | Likely Success | Long-term Viable | Cost |
|--------|--------------|----------------|------------------|------|
| **CPU Minimal Test** | 15 min | High | No (too slow) | $0 |
| **HunyuanVideo MLX** | 2-3 hours | Medium-High | Yes | $0 |
| **Cloud Hybrid** | 30 min | Very High | Yes | $1-5/video |
| **Wait for Fix** | Unknown | Medium | Maybe | $0 |
| **GGUF Conversion** | Unknown | Unknown | Maybe | $0 |

---

## Recommended Path

### Path A: "Validate & Pivot" (RECOMMENDED) ⭐

**Goal:** Confirm CPU works, then switch to viable alternative

#### Step 1: CPU Validation Test (15 minutes)
```bash
cd /Users/arthurdell/ARTHUR/video-generation/ComfyUI
source venv/bin/activate
python3 ../scripts/test_cpu_minimal.py
```

**What this does:**
- Tests 128x128, 5 frames, 10 steps on CPU
- Takes ~15 minutes (vs 4.6 hours)
- Validates pipeline works correctly
- Confirms MPS is the issue

**If output shows actual content:** Pipeline works, MPS is the problem → Proceed to Step 2

**If output shows noise:** Deeper issue → Need more investigation

#### Step 2: Test HunyuanVideo with MLX (2-3 hours setup)
**Why:** Has proven Apple Silicon support, similar quality to Wan 2.2

```bash
cd /Users/arthurdell/ARTHUR/video-generation
git clone https://github.com/gaurav-nelson/HunyuanVideo_MLX.git
cd HunyuanVideo_MLX
# Follow setup instructions
# Test with 480p, 5 seconds
```

**If HunyuanVideo works well:**
- Build production automation around it
- Similar to Wan 2.2 quality (VBench #2)
- MLX-optimized for Apple Silicon
- Can leverage your 768GB RAM

#### Step 3: Build Production System
Use HunyuanVideo for actual production work while monitoring Wan 2.2 MPS fix progress.

---

### Path B: "Cloud Hybrid" (PRAGMATIC) 💼

**Goal:** Get working system TODAY, optimize cost over time

#### Immediate Setup (30 minutes)
1. Sign up for RunwayML or Replicate
2. Test Wan 2.2 or similar model on their infrastructure
3. Integrate API into existing scripts

**Advantages:**
- Working solution in 30 minutes
- Uses actual CUDA GPUs (no compatibility issues)
- Pay per video (~$1-5 each)
- Can prototype locally with CPU

**Ongoing:**
- Generate 20-50 videos/month: ~$20-250/month
- No wasted time on failed generations
- Can still explore local solutions in parallel

**Integration Example:**
```python
# /Users/arthurdell/ARTHUR/video-generation/scripts/cloud_wan22.py
import requests

def generate_video_cloud(prompt: str) -> Path:
    # Call RunwayML/Replicate API
    # Download result
    # Save to /videos/raw/
    pass
```

---

### Path C: "Research & Wait" (RISKY) ⏳

**Only choose this if:**
- Not urgent to have working video generation
- Want to wait for PyTorch MPS fixes
- Willing to check back in 1-3 months

**Actions:**
- Monitor PyTorch Issue #148670
- Test new PyTorch releases as they come out
- Focus on other projects in meantime

**Risk:** Could wait months with no guarantee of fix

---

## Decision Framework

### Choose Path A (Validate & Pivot) if:
- ✅ You want local generation
- ✅ You're willing to try HunyuanVideo instead of Wan 2.2
- ✅ You have time for 2-3 hours of setup today
- ✅ You want to leverage your 768GB RAM advantage

### Choose Path B (Cloud Hybrid) if:
- ✅ You need working solution TODAY
- ✅ Budget allows $20-250/month
- ✅ You want guaranteed quality
- ✅ You prefer proven infrastructure over experiments

### Choose Path C (Research & Wait) if:
- ✅ Video generation is not urgent
- ✅ You specifically want Wan 2.2 (not alternatives)
- ✅ You're willing to wait months
- ❌ You can't accept any other solution

---

## Immediate Action Items

### Today (Next 2 Hours)

1. **Read the troubleshooting report:**
   ```
   /Users/arthurdell/ARTHUR/video-generation/TROUBLESHOOTING_REPORT.md
   ```

2. **Decide on a path** (A, B, or C)

3. **If Path A:** Run CPU minimal test
   ```bash
   cd /Users/arthurdell/ARTHUR/video-generation/ComfyUI
   source venv/bin/activate
   python3 ../scripts/test_cpu_minimal.py
   ```

4. **If Path B:** Research cloud providers
   - RunwayML Gen-3
   - Replicate
   - Hugging Face Inference API

5. **If Path C:** Set calendar reminder for monthly checks

### This Week

**If pursuing Path A:**
- Setup HunyuanVideo MLX
- Test generation quality
- Compare to Wan 2.2 expectations
- Build automation if acceptable

**If pursuing Path B:**
- Integrate cloud API
- Test production workflow
- Calculate actual costs
- Set up monitoring

---

## Cost-Benefit Analysis

### Path A: HunyuanVideo MLX
**Setup time:** 2-3 hours
**Generation time:** ~15-20 min per 5s video (estimated)
**Cost per video:** $0 (electricity only)
**Risk:** May not work perfectly on Apple Silicon

**Break-even:** Immediate (after setup)

### Path B: Cloud Hybrid
**Setup time:** 30 minutes
**Generation time:** ~2-5 minutes per video
**Cost per video:** $1-5
**Risk:** Ongoing costs

**Break-even:** After ~50-100 videos vs Path A
**But:** Working solution TODAY vs potential days of troubleshooting

### Path C: Wait for Fix
**Setup time:** 0
**Generation time:** N/A (not available)
**Cost:** $0
**Risk:** May never be fixed, or could take months

**Opportunity cost:** Lost time that could be spent creating content

---

## My Recommendation

**Start with Path A, have Path B as backup:**

1. **Today:** Run CPU minimal test (15 min) to validate pipeline
2. **Today/Tomorrow:** Test HunyuanVideo MLX (2-3 hours)
3. **If HunyuanVideo works:** Build production system around it
4. **If HunyuanVideo fails:** Fall back to Path B (cloud hybrid)

**Why this approach:**
- Low time investment to validate (15 min)
- HunyuanVideo has good success reports on Mac
- Cloud backup available if local doesn't work
- Leverages your 768GB RAM if HunyuanVideo succeeds
- Avoids wasting more time on broken Wan 2.2 + MPS

---

## Questions to Consider

1. **How urgent is video generation?**
   - Very urgent → Path B (cloud)
   - Can wait a few days → Path A (HunyuanVideo)
   - Not urgent → Path C (wait)

2. **What's your monthly video volume?**
   - <10 videos → Cloud costs negligible (~$10-50/mo)
   - 10-50 videos → Cloud costs moderate (~$50-250/mo)
   - >50 videos → Local essential for cost control

3. **Is Wan 2.2 specifically required?**
   - Yes, must be Wan 2.2 → Path C (wait for fix)
   - No, quality matters most → Path A or B
   - Flexibility → Path A (try HunyuanVideo)

4. **Budget for video generation?**
   - $0/month → Must be local (Path A or C)
   - $50-250/month → Cloud viable (Path B)
   - Unlimited → Cloud is easiest (Path B)

---

## Files Created

1. **Troubleshooting Report:**
   `/Users/arthurdell/ARTHUR/video-generation/TROUBLESHOOTING_REPORT.md`
   - Complete root cause analysis
   - Technical evidence
   - MPS compatibility issues

2. **CPU Test Script:**
   `/Users/arthurdell/ARTHUR/video-generation/scripts/test_cpu_minimal.py`
   - Quick validation test (15 min)
   - Minimal config to confirm pipeline works

3. **This Document:**
   `/Users/arthurdell/ARTHUR/video-generation/NEXT_STEPS.md`
   - Decision framework
   - Action items
   - Cost analysis

---

## Support Resources

### MPS Issues
- [PyTorch MPS Complex128 Bug](https://github.com/pytorch/pytorch/issues/148670)
- [ComfyUI Wan 2.2 Apple Silicon Issue](https://github.com/comfyanonymous/ComfyUI/issues/9255)

### Alternative Models
- [HunyuanVideo MLX Port](https://github.com/gaurav-nelson/HunyuanVideo_MLX)
- [Diffusers MPS Optimization Guide](https://huggingface.co/docs/diffusers/en/optimization/mps)

### Cloud Providers
- [RunwayML Gen-3](https://runwayml.com/)
- [Replicate](https://replicate.com/)
- [Hugging Face Inference API](https://huggingface.co/inference-api)

---

**Bottom line:** Wan 2.2 + MPS doesn't work due to fundamental PyTorch limitations. Test CPU to confirm, then pivot to HunyuanVideo (local) or cloud (fast). Don't waste more time on the broken path.
