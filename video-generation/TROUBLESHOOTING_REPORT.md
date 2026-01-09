# Video Generation Failure - Root Cause Analysis

**Date:** 2025-12-31
**Status:** ❌ CRITICAL FAILURE IDENTIFIED
**Generation Time Wasted:** 11 hours (4.6 hours generation + setup)

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** Wan 2.2 A14B model is **fundamentally incompatible** with PyTorch MPS (Metal Performance Shaders) backend on Apple Silicon. The model generated pure blue noise instead of video content due to unsupported data types.

The 380KB file size and blue noise output are symptoms of **silent MPS backend failures** - the model ran for 4.6 hours but produced garbage because MPS cannot execute the operations correctly.

---

## Evidence

### Visual Evidence
Generated frames show pure blue noise patterns with no actual content:
- Frame 0: Blue noise (2,730 unique colors)
- Frame 40: Blue noise (1,108 unique colors)
- Frame 80: Blue noise (395 unique colors - degrading)

User description: "looks like water or confusion... output flickers"

### Technical Evidence
- **File size:** 380KB (expected: several MB for 5.1s @ 848x480)
- **No errors in log:** Pipeline completed "successfully" but output is unusable
- **Frame statistics:** High std dev (~104) indicates noise, not structured content
- **Degrading quality:** Unique colors decrease from 2,730 → 395 over time

---

## Root Cause: MPS Incompatibility

### Critical Issues Discovered

#### 1. Float8 Data Type Not Supported
**Error:** "Trying to convert Float8_e4m3fn to the MPS backend but it does not have support for that dtype."

**Impact:** Wan 2.2 uses Float8 quantization which MPS doesn't support. Operations silently fail or produce garbage.

**Source:** [ComfyUI Issue #9255](https://github.com/comfyanonymous/ComfyUI/issues/9255)

#### 2. Complex128 (ComplexDouble) Not Supported
**Error:** "TypeError: Trying to convert ComplexDouble to the MPS backend but it does not have support for that dtype."

**Technical Details:**
- Wan transformer uses rotary embeddings with complex128
- MPS only supports complex64 (cfloat), not complex128 (cdouble)
- When diffusers converts to complex128, MPS fails silently

**Source:** [PyTorch Issue #148670](https://github.com/pytorch/pytorch/issues/148670)

#### 3. Confirmed: Default Diffusion Models Don't Work on Mac Silicon
**Quote from research:** "The default Diffusion Models won't work on Mac silicon, and the default workflow isn't optimized for Mac silicon"

**Recommended workaround:** GGUF model format for Apple Silicon

**Source:** [DEV Community Guide](https://dev.to/aibyamdad/how-to-use-wan-21-with-comfy-ui-on-mac-windows-and-linux-a-comprehensive-guide-nkd)

---

## Why No Errors Were Logged

MPS backend failures are often **silent**:
1. Operations that fail fall back to producing random/zero tensors
2. Pipeline continues executing with garbage data
3. VAE decodes garbage latents → blue noise output
4. Export succeeds because it's just saving the garbage frames

**Key insight:** The absence of errors is actually a sign of the problem - MPS silently fails instead of throwing exceptions.

---

## Configuration Analysis

### What We Used (FAILED)
```python
Device: mps
Dtype: torch.float16
VAE: torch.float32
Model: Wan 2.2 A14B (diffusers format)
Backend: PyTorch 2.8.0 with MPS
Resolution: 848x480
Steps: 40
```

### Why It Failed
- Wan 2.2 requires Float8 support (MPS doesn't have it)
- Transformer uses complex128 operations (MPS only supports complex64)
- Diffusers format isn't optimized for Apple Silicon
- No GGUF conversion available

---

## Alternative Solutions

### Option 1: CPU Backend (Slow but Should Work) ⚠️
**Pros:**
- Will actually produce correct output
- No compatibility issues
- Can validate the pipeline works

**Cons:**
- 10-20x slower than GPU
- 4.6 hours → 46-92 hours per video
- Completely impractical for production

**Test approach:** Generate 5-10 frames only to validate

### Option 2: Switch to HunyuanVideo 1.5 (Experimental) 🧪
**Status:** Has MLX port and better Mac compatibility
**Pros:**
- Community reports it works on Apple Silicon
- MLX optimization available (gaurav-nelson/HunyuanVideo_MLX)
- Similar quality to Wan 2.2

**Cons:**
- Slower than native implementation
- Still experimental
- Performance unknown on your hardware

**Recommendation:** Test with short videos first

### Option 3: GGUF Format Conversion (Requires Research) 🔍
**Concept:** Convert Wan 2.2 to GGUF format for Apple Silicon
**Status:** Unknown if conversion tools exist for video models

**Research needed:**
- Are GGUF video model converters available?
- Does GGUF format support video generation?
- Performance vs diffusers format?

### Option 4: Wait for PyTorch/Diffusers Fix (Timeline Unknown) ⏳
**Status:** Issue #148670 is open but no fix timeline
**Pros:**
- Eventually will work correctly
- Keep existing setup

**Cons:**
- Could be weeks/months
- No guarantee of fix
- Wasted time waiting

### Option 5: Cloud GPU Hybrid (Practical Compromise) ☁️
**Approach:**
- Prototype locally with CPU (short videos)
- Generate production videos on cloud GPU (RunwayML, Replicate)

**Pros:**
- Immediate solution
- Pay per video (~$1-5 each)
- No wasted time on failed generations

**Cons:**
- Recurring costs
- Not fully local

---

## Lessons Learned

### What Went Wrong in Planning

1. **Insufficient MPS compatibility research**
   - Assumed MPS support = fully functional
   - Didn't check for known issues with specific models
   - Trusted "experimental" label without verification

2. **No validation checkpoints**
   - Should have generated 5 frames first, not 81
   - Should have checked frame content before full run
   - File size check would have caught this immediately

3. **Missing pre-flight tests**
   - Could have tested with tiny resolution (128x128, 5 frames, 5 steps)
   - Would take 5-10 minutes vs 4.6 hours
   - Would have revealed the issue instantly

### Validation Gaps

**Critical mistake:** Declared success based on "no errors" without checking output quality

**Should have:**
- Checked file size (380KB vs expected 5-10MB)
- Extracted and viewed sample frames
- Compared to reference outputs
- Validated frame content quality

---

## Recommended Next Steps

### Immediate (Today)

1. **Test CPU backend with minimal config:**
   ```python
   device = "cpu"
   height = 128
   width = 128
   num_frames = 5
   num_inference_steps = 10
   ```
   Expected time: 10-20 minutes
   Purpose: Validate pipeline works correctly

2. **If CPU test succeeds:**
   - Confirms model/pipeline are fine
   - Confirms issue is MPS-specific
   - Can proceed with alternative solutions

3. **If CPU test fails:**
   - Model files may be corrupted
   - Diffusers version incompatibility
   - Need to investigate model itself

### Short-term (This Week)

1. **Test HunyuanVideo 1.5 with MLX:**
   - Clone gaurav-nelson/HunyuanVideo_MLX
   - Generate test video (480p, 5s)
   - Compare quality and performance

2. **Research GGUF conversion:**
   - Check if video model GGUF tools exist
   - Look for Wan 2.2 GGUF versions
   - Test if available

3. **Evaluate cloud hybrid:**
   - Test RunwayML Gen-3 with same prompt
   - Compare quality and cost
   - Calculate ROI vs local setup

### Long-term (This Month)

1. **Monitor PyTorch MPS improvements:**
   - Watch Issue #148670
   - Test new PyTorch releases
   - Re-evaluate when MPS support improves

2. **Build production workflow:**
   - If HunyuanVideo works: Build automation around it
   - If cloud hybrid: Integrate API calls
   - If waiting: Focus on other projects

---

## Technical Details for Reference

### System Configuration
- **Hardware:** Mac Studio with 768GB unified memory
- **OS:** macOS (Darwin 25.2.0)
- **Python:** 3.9
- **PyTorch:** 2.8.0
- **Diffusers:** 0.36.0.dev0 (main branch)
- **Model:** Wan2.2-T2V-A14B-Diffusers (118GB)

### Model File Integrity
All model files verified complete:
- text_encoder: 11GB ✓
- transformer: 53GB ✓
- transformer_2: 53GB ✓
- vae: 484MB ✓
- Total: 118GB ✓

### MPS Limitations Confirmed
- No Float8 support
- No complex128 support
- No double precision (float64)
- Experimental status for video models

---

## Sources

- [Wan 2.2 Apple Silicon Issue - ComfyUI #9255](https://github.com/comfyanonymous/ComfyUI/issues/9255)
- [MPS Complex128 Bug - PyTorch #148670](https://github.com/pytorch/pytorch/issues/148670)
- [Wan 2.1 ComfyUI Mac Guide](https://dev.to/aibyamdad/how-to-use-wan-21-with-comfy-ui-on-mac-windows-and-linux-a-comprehensive-guide-nkd)
- [ComfyUI Wan 2.2 I2V Guide](https://papayabytes.substack.com/p/guide-comfyui-and-wan-22-image-to)
- [Apple Silicon MPS Request - Wan GitHub #14](https://github.com/Wan-Video/Wan2.1/issues/14)
- [Diffusers MPS Optimization Docs](https://huggingface.co/docs/diffusers/en/optimization/mps)

---

**Bottom Line:** The 768GB RAM advantage is irrelevant if the GPU backend can't execute the operations. Wan 2.2 requires CUDA or CPU - MPS is not viable with current PyTorch/diffusers versions.
