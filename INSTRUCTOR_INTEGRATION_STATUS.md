# Instructor Library Integration Status

**Date:** 2026-01-02
**Status:** ✅ Installed, ⏸️ Testing blocked by cluster availability

---

## Installation

### Python 3.11 Required
- **Issue:** Instructor requires Python 3.10+ (uses `str | Path` union syntax)
- **Solution:** Installed via `/opt/homebrew/bin/python3.11`
- **Status:** ✅ COMPLETE

```bash
/opt/homebrew/bin/python3.11 -m pip install --user instructor
# Successfully installed instructor-1.13.0
```

---

## Testing Status

### ❌ Llama 3.2 1B (Small Model)
**Issue:** Small models struggle with structured JSON output
- Model outputs JSON schema instead of instance
- Validation errors: "Field required"
- **Root cause:** 1B model lacks capacity for reliable structured outputs

**Error Example:**
```
1 validation error for SimpleGreeting
greeting
  Field required [type=missing, input_value={'properties': {'greeting'...}, input_type=dict]
```

The model returned the schema definition rather than a valid JSON object.

### ⏸️ DeepSeek V3.1 4-bit (Production Model)
**Status:** Downloaded but cluster unavailable

**Current Blocker:**
```
Error: No cycles found with sufficient memory
```

**Diagnosis:**
- DeepSeek V3.1 4-bit: 378 GB
- Cluster status: 0 nodes (RDMA cluster not active)
- Exo running in force-master mode (standalone)
- BETA node not connected to cluster

**Required Actions:**
1. Ensure BETA Exo node is running
2. Verify RDMA connectivity between ALPHA-BETA
3. Wait for cluster discovery (can take 1-2 minutes)
4. Create DeepSeek instance on 2-node cluster (768GB total)

---

## Production Schemas Created

Location: `/Users/arthurdell/ARTHUR/schemas/content_schemas.py`

### Available Schemas:
1. **VideoScript** - Video generation with scenes
2. **CarouselPlan** - LinkedIn carousel content
3. **ImagePrompt** - FLUX.1 image generation prompts
4. **SlideContent** - Individual carousel slides

See file for complete implementation with validation.

---

## Next Steps (When Cluster Available)

### 1. Verify Cluster Status
```bash
curl -s "http://localhost:52415/cluster/status" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Nodes: {len(data.get(\"nodes\", []))}')
print(f'Expected: 2 (ALPHA + BETA)')
"
```

### 2. Create DeepSeek Instance
```bash
# Get placement preview
curl -s "http://localhost:52415/instance/previews?model_id=deepseek-v3.1-4bit" \
  | python3 -c "import sys,json; ..." > /tmp/deepseek_instance.json

# Create instance (spans ALPHA + BETA via RDMA)
curl -X POST http://localhost:52415/instance \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/deepseek_instance.json

# Wait 30-60 seconds for tensor parallel initialization
```

### 3. Test Instructor with DeepSeek
```bash
/opt/homebrew/bin/python3.11 /Users/arthurdell/ARTHUR/scripts/test_instructor_deepseek.py
```

### 4. Validate Production Schemas
- Test VideoScript generation
- Test CarouselPlan generation
- Test ImagePrompt generation
- Verify validation rules work correctly

### 5. Integrate with Existing Scripts
- Update `generate_image.py` to use structured prompts
- Create `generate_carousel_structured.py`
- Add streaming UI for real-time updates

---

## Technical Notes

### Instructor Modes
- **MODE.JSON** - Used for Exo/OpenAI-compatible endpoints
- **MODE.TOOLS** - For function calling (not tested yet)
- **MODE.MD_JSON** - For markdown-wrapped JSON

### Current Configuration
```python
client = instructor.from_openai(
    OpenAI(base_url="http://localhost:52415/v1", api_key="not-needed"),
    mode=instructor.Mode.JSON
)
```

### Validation Features
- Automatic retries (3 attempts by default)
- Field-level validation via Pydantic
- Type coercion and normalization
- Detailed error messages with generation context

---

## Model Compatibility

| Model | Size | Structured Output Quality | Status |
|-------|------|--------------------------|--------|
| **Llama 3.2 1B** | 0.7 GB | ❌ Poor (schema confusion) | Not recommended |
| **Llama 3.1 8B** | 4.5 GB | ⚠️ Fair (simple schemas only) | Not tested |
| **Llama 3.1 70B** | 38 GB | ✅ Good | Not tested |
| **DeepSeek V3.1 4-bit** | 378 GB | ✅ Excellent | **RECOMMENDED** |
| **DeepSeek V3.1 8-bit** | 713 GB | ✅ Excellent | Not needed (4-bit sufficient) |

### Recommendation
Use **DeepSeek V3.1 4-bit** for production:
- Official Instructor support
- Excellent structured output quality
- 378GB fits in 768GB cluster (50% utilization)
- 37B active parameters (671B total with MoE)

---

## Troubleshooting

### Issue: "No cycles found with sufficient memory"
**Cause:** Model too large for available memory
**Solutions:**
1. Ensure RDMA cluster is active (check node count)
2. Stop other model instances to free memory
3. Use smaller model (Llama 70B instead of DeepSeek V3)

### Issue: Python version errors
**Cause:** Instructor requires Python 3.10+
**Solution:** Use `/opt/homebrew/bin/python3.11` explicitly

### Issue: Validation errors with small models
**Cause:** Model outputs schema definition instead of instance
**Solution:** Use larger model (70B+ parameters recommended)

---

## References

- **Instructor Documentation:** https://python.useinstructor.com/
- **DeepSeek V3 Integration:** https://python.useinstructor.com/integrations/openai-compatible/
- **Pydantic Validation:** https://docs.pydantic.dev/

---

**Status Summary:**
- ✅ Instructor installed (Python 3.11)
- ✅ Production schemas created
- ❌ Small model testing (failed as expected)
- ⏸️ DeepSeek testing (waiting for cluster)
- 📋 Ready to proceed when cluster available
