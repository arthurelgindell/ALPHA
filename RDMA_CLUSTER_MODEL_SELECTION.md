# RDMA Cluster Model Selection Guide

**Date:** 2026-01-02
**Cluster:** ALPHA-BETA Thunderbolt 5 RDMA
**Total Memory:** 768 GB (512 GB ALPHA + 256 GB BETA)
**Status:** Ready for model deployment

---

## Executive Summary

Recommended model configuration for the ARTHUR RDMA cluster optimizes for **coding assistance, research, and content creation** while efficiently utilizing 768 GB unified memory.

**Primary Recommendation: DeepSeek V3 4-bit (378 GB)**
- Best coding model available
- 50% memory utilization (safe margin)
- Tensor parallel via JACCL/RDMA
- 161.5 tokens/sec @ 2 nodes

---

## Cluster Capabilities

### Hardware Configuration
```
┌─────────────────────────────────────────────────────────────┐
│  ALPHA (Master)         BETA (Worker)                       │
│  512 GB RAM             256 GB RAM                          │
│  Mac Studio M3 Ultra    Mac Studio M3 Ultra                │
│  ────────────────────────────────────────────────────────── │
│  Thunderbolt 5 RDMA: 80 Gb/s                                │
│  Total Unified Memory: 768 GB                               │
└─────────────────────────────────────────────────────────────┘
```

### Performance Characteristics
- **RDMA Latency:** <100 μs (target)
- **Bandwidth:** 80 Gb/s Thunderbolt 5
- **Tensor Parallel:** Via JACCL (MLX distributed)
- **Max Model Size:** ~700 GB (92% utilization limit)

---

## Model Tiers

### Tier 1: Essential Models ⭐

#### 1. DeepSeek V3 4-bit (378 GB) - PRIMARY LLM

**Repository:** `mlx-community/DeepSeek-V3-4bit`

**Specifications:**
- Size: 378 GB (671B parameters quantized to 4-bit)
- Memory utilization: 49% of cluster (390 GB buffer)
- Requires tensor parallelism: Yes (automatic via Exo)
- Performance: 161.5 tokens/sec @ 2 nodes

**Why This Model:**
1. **Best Coding Model:** State-of-the-art code generation and understanding
2. **Safe Memory Fit:** 49% utilization leaves comfortable buffer
3. **RDMA Optimized:** Tensor parallel splits work across ALPHA/BETA
4. **Research Capable:** Strong reasoning and knowledge retrieval
5. **Content Creation:** Excellent writing quality

**Use Cases for ARTHUR:**
- Claude Code LLM backend for autonomous coding
- Research and documentation generation
- Content writing for LinkedIn/blog posts
- Code review and architecture planning
- Complex reasoning tasks

**Expected Performance:**
- First token: ~2-3 seconds (model loading + RDMA setup)
- Generation: ~160 tokens/sec sustained
- Context: Up to 64k tokens

**Download Time:** ~30-60 minutes (depending on network)

---

#### 2. Llama 3.2 1B 4-bit (1.24 GB) - TESTING

**Repository:** `mlx-community/Llama-3.2-1B-Instruct-4bit`

**Specifications:**
- Size: 1.24 GB
- Memory utilization: <1% of cluster
- Requires tensor parallelism: No
- Performance: Instant inference

**Why This Model:**
- **Cluster Health Check:** Verify Exo + JACCL before large downloads
- **Quick Testing:** Validate API endpoints and cluster communication
- **Fast Download:** <2 minutes to download

**Use Cases:**
- Cluster health monitoring
- Quick sanity checks before production inference
- Testing new Exo features

**Download Time:** <2 minutes

---

### Tier 2: Optional Performance Models 🚀

#### 3. Llama 3.1 70B 4-bit (38 GB) - FAST FALLBACK

**Repository:** `mlx-community/Meta-Llama-3.1-70B-Instruct-4bit`

**Specifications:**
- Size: 38 GB
- Memory utilization: 5% (can run alongside DeepSeek V3)
- Requires tensor parallelism: Optional (faster with TP)
- Performance: ~10x faster than DeepSeek V3

**Why Consider This Model:**
1. **Low-Latency Needs:** When speed > quality (e.g., quick queries)
2. **Batch Processing:** Process many requests quickly
3. **Development/Testing:** Fast iteration during development
4. **Parallel Workloads:** Run alongside DeepSeek V3 (416 GB total)

**Use Cases:**
- Quick code formatting and linting
- Fast documentation lookups
- Batch processing of simple tasks
- Development/testing of cluster features

**Trade-off:** 70B model quality vs 10x speed improvement

**Download Time:** ~5-10 minutes

---

#### 4. Llama 3.1 8B 4-bit (4.5 GB) - INSTANT INFERENCE

**Repository:** `mlx-community/Meta-Llama-3.1-8B-Instruct-4bit`

**Specifications:**
- Size: 4.5 GB
- Memory utilization: <1%
- Requires tensor parallelism: No
- Performance: Near-instant inference (<100ms)

**Why Consider This Model:**
- **Instant Response:** Sub-second inference for simple tasks
- **Always Available:** Minimal memory footprint
- **Edge Cases:** When DeepSeek V3 is busy/loading

**Use Cases:**
- Code autocomplete
- Simple Q&A
- Quick reformatting
- Cluster availability testing

**Download Time:** <1 minute

---

### Tier 3: Not Recommended ❌

#### DeepSeek V3 8-bit (712 GB)

**Why NOT recommended:**
- **Too close to limit:** 93% memory utilization (only 56 GB buffer)
- **OOM risk:** No room for model activation/inference overhead
- **Minimal quality gain:** 8-bit vs 4-bit quality difference marginal
- **Same speed:** No performance improvement over 4-bit

**Recommendation:** Use DeepSeek V3 4-bit instead

---

## Memory Utilization Analysis

### Recommended Configuration

| Model            | Size    | Utilization | Remaining | Risk  |
|------------------|---------|-------------|-----------|-------|
| DeepSeek V3 4bit | 378 GB  | 49%         | 390 GB    | ✅ Low |
| + Llama 70B      | +38 GB  | 54%         | 352 GB    | ✅ Low |
| + Llama 8B       | +4.5 GB | 55%         | 347 GB    | ✅ Low |
| + Llama 1B       | +1.2 GB | 55%         | 346 GB    | ✅ Low |

**Total: 422 GB loaded (55% utilization)**

### Memory Budget Breakdown

```
Total Cluster Memory: 768 GB
├─ DeepSeek V3 4bit:  378 GB (49%)
├─ Llama 70B:          38 GB (5%)
├─ Llama 8B:           4.5 GB (<1%)
├─ Llama 1B:           1.2 GB (<1%)
├─ Overhead:          ~50 GB (7%) - OS, buffers, inference
└─ Free Buffer:       296 GB (39%)
```

**Safe Operation Zone:** <70% utilization (537 GB)

---

## Download Strategy

### Phase 1: Testing (Required)
```bash
# Download tiny model to verify cluster
huggingface-cli download mlx-community/Llama-3.2-1B-Instruct-4bit

# Test cluster
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.2-1b", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Phase 2: Production LLM (Recommended)
```bash
# Download DeepSeek V3 4-bit (378 GB, ~30-60 min)
huggingface-cli download mlx-community/DeepSeek-V3-4bit

# Test tensor parallel inference
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-v3-4bit", "messages": [{"role": "user", "content": "Write a Python function to parse JSON"}]}'
```

### Phase 3: Optional Fast Models
```bash
# Llama 70B for fast inference
huggingface-cli download mlx-community/Meta-Llama-3.1-70B-Instruct-4bit

# Llama 8B for instant queries
huggingface-cli download mlx-community/Meta-Llama-3.1-8B-Instruct-4bit
```

---

## Integration with ARTHUR Ecosystem

### Current ARTHUR Stack

```
┌─────────────────────────────────────────────────────────────┐
│  ARTHUR AI Content Creation Ecosystem                       │
├─────────────────────────────────────────────────────────────┤
│  ALPHA (Mac Studio 512GB)                                   │
│  ├─ Image Generation: FLUX.1 [schnell] (15-30s/image)      │
│  ├─ Orchestration: Claude Code API tier                    │
│  └─ LLM Inference: RDMA Cluster (NEW)                      │
│                                                             │
│  BETA (Mac Studio 256GB)                                    │
│  ├─ Research: Claude Code Max tier (web search)            │
│  ├─ RDMA Worker: Tensor parallel node                      │
│  └─ Extended Context: 200k tokens                          │
│                                                             │
│  GAMMA (DGX GB10)                                           │
│  └─ Video Generation: HunyuanVideo-1.5 ($0/video)          │
└─────────────────────────────────────────────────────────────┘
```

### Use Case: Autonomous Coding with DeepSeek V3

**Scenario:** Claude Code needs to generate a complex feature

**Workflow:**
1. Claude Code dispatches code generation to DeepSeek V3 on RDMA cluster
2. ALPHA+BETA tensor parallel via JACCL (RDMA acceleration)
3. DeepSeek V3 generates high-quality code in seconds
4. Claude Code reviews and applies changes

**Advantages:**
- **Cost:** $0/request (vs Claude API $15/1M tokens)
- **Privacy:** 100% local inference
- **Latency:** ~160 tokens/sec (acceptable for background tasks)
- **Quality:** State-of-the-art coding model

### Use Case: Content Creation Pipeline

**Scenario:** Generate LinkedIn post with image

**Workflow:**
1. DeepSeek V3: Write engaging post text (10-20 seconds)
2. FLUX.1 on ALPHA: Generate image (15-30 seconds)
3. (Optional) HunyuanVideo on GAMMA: Generate video (5-85 min)

**Total time:** <1 minute for text+image, <90 min with video

---

## Performance Benchmarks

### Expected Inference Speed

| Model            | Tokens/Sec | First Token | 500 Token Response |
|------------------|------------|-------------|--------------------|
| DeepSeek V3 4bit | 161.5      | 2-3s        | ~6s                |
| Llama 70B 4bit   | ~1500      | <1s         | <1s                |
| Llama 8B 4bit    | ~3000      | <0.5s       | <0.5s              |
| Llama 1B 4bit    | ~5000      | <0.1s       | <0.1s              |

*Note: Benchmarks are estimates based on exo reference data*

### RDMA Impact on DeepSeek V3

**Without RDMA (TCP):**
- Tensor transfer latency: ~0.7 ms
- Effective bandwidth: ~10 Gb/s
- Model parallelism overhead: ~30-40%

**With RDMA (Thunderbolt 5):**
- Tensor transfer latency: <100 μs (7x faster)
- Effective bandwidth: 80 Gb/s (8x faster)
- Model parallelism overhead: ~10-15%

**Performance gain:** ~2-3x speedup for large models

---

## Cost Analysis

### Cloud API Comparison

| Service              | Cost             | DeepSeek V3 Equivalent |
|----------------------|------------------|------------------------|
| Claude API (Sonnet)  | $3/$15 per 1M    | 1M tokens = $15        |
| GPT-4                | $2.50/$10 per 1M | 1M tokens = $10        |
| DeepSeek API         | $0.27/$1.10/1M   | 1M tokens = $1.10      |
| **RDMA Cluster**     | **$0**           | **Unlimited**          |

**ROI Calculation:**
- Cluster cost: $0 (existing hardware)
- Electricity: ~$0.50/hour (2x Mac Studios + DGX)
- **Savings:** $10-15 per 1M tokens vs cloud APIs
- **Break-even:** Immediate (hardware already owned)

**Annual savings (100M tokens/year):** $1,000-$1,500

---

## Recommended Action Plan

### Step 1: Download Models on ALPHA (30-90 min)
```bash
cd /Users/arthurdell/ARTHUR
./scripts/download_cluster_models.sh
```

**Interactive prompts will ask:**
1. Download DeepSeek V3? → **YES** (primary LLM)
2. Download Llama 70B? → **YES** (fast fallback)
3. Download Llama 8B? → **OPTIONAL** (if you want instant queries)

### Step 2: Start Cluster
```bash
# On ALPHA
~/start-exo-cluster.sh

# On BETA (after ALPHA provides bootstrap command)
# Command will be displayed by ALPHA startup script
```

### Step 3: Verify JACCL Tensor Parallel
```bash
# Test DeepSeek V3 (should trigger JACCL/RDMA)
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3-4bit",
    "messages": [{"role": "user", "content": "Write a Python function to implement binary search"}],
    "max_tokens": 500
  }'

# Monitor logs for JACCL activation
tail -f /tmp/exo-alpha.log | grep -E "JACCL|RDMA|IBV|distributed"
```

### Step 4: Integration with Claude Code
Create wrapper script for Claude Code to use DeepSeek V3:
```bash
# scripts/llm_query.sh
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"deepseek-v3-4bit\", \"messages\": [{\"role\": \"user\", \"content\": \"$1\"}]}"
```

---

## Monitoring and Maintenance

### Health Checks
```bash
# Cluster status
curl -s http://localhost:52415/state | python3 -c "
import sys, json
d = json.load(sys.stdin)
profiles = d.get('nodeProfiles', {})
print(f'Nodes: {len(profiles)}')
for nid, p in profiles.items():
    name = p.get('friendlyName', nid[:20])
    mem = p.get('memory',{}).get('ramTotal',{}).get('inBytes',0)/(1024**3)
    print(f'  - {name}: {mem:.0f} GB')
"

# RDMA status
/usr/bin/ibv_devinfo -d rdma_en4

# Exo logs
tail -100 /tmp/exo-alpha.log | grep -E "error|Error|ERROR|JACCL|distributed"
```

### Performance Monitoring
```bash
# Monitor GPU usage on ALPHA
sudo powermetrics --samplers gpu_power -i 1000 -n 10

# Check memory pressure
memory_pressure

# Network throughput (during inference)
nettop -m tcp -P -L 1
```

---

## Troubleshooting

### Issue: Model Not Found
**Symptom:** `Model 'deepseek-v3-4bit' not found`

**Solution:**
```bash
# Check downloaded models
ls -lh ~/.cache/huggingface/hub/

# Verify model naming in Exo
curl -s http://localhost:52415/models
```

### Issue: JACCL Not Activating
**Symptom:** DeepSeek V3 inference slow, no RDMA activity

**Solution:**
```bash
# Check RDMA device status
/usr/bin/ibv_devinfo -d rdma_en4

# Verify MLX environment
python3 -c "import mlx.core as mx; print(mx.metal.is_available())"

# Check Exo logs
grep "JACCL" /tmp/exo-alpha.log
```

### Issue: Out of Memory
**Symptom:** Inference crashes with OOM error

**Solution:**
1. Check total memory usage: `memory_pressure`
2. Restart Exo cluster to clear memory
3. Remove large models if needed
4. Use smaller model (Llama 70B instead of DeepSeek V3)

---

## Future Enhancements

### Potential Additions (Post-Initial Setup)

1. **Qwen2.5-Coder-32B** (18 GB) - Alternative coding model
2. **Mistral Large** (67 GB) - European alternative
3. **Mixtral 8x22B** (87 GB) - MoE architecture (sparse inference)

### Model Router (Future)
Route requests to optimal model based on task:
- **Coding:** DeepSeek V3
- **Quick queries:** Llama 8B
- **Fast inference:** Llama 70B
- **Testing:** Llama 1B

---

## Summary

**Recommended Download:**
1. ✅ Llama 3.2 1B (1.24 GB) - Testing
2. ✅ DeepSeek V3 4-bit (378 GB) - Primary LLM
3. ✅ Llama 3.1 70B (38 GB) - Fast fallback
4. ⚠️ Llama 3.1 8B (4.5 GB) - Optional instant queries

**Total:** ~422 GB (55% utilization)

**Next Step:** Run `./scripts/download_cluster_models.sh` on ALPHA

---

**Status:** ✅ Ready for model deployment
**Expected Setup Time:** 1-2 hours (including downloads)
**Production Ready:** After DeepSeek V3 download completes
