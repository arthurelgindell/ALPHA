# RDMA Cluster Quick Start Guide

**Goal:** Validate ALPHA-BETA cluster with proven-compatible models
**Strategy:** Test incrementally, small to large
**Total Time:** 15-30 minutes (including downloads)

---

## Step 1: Quick Cluster Health Check (2 minutes)

```bash
cd /Users/arthurdell/ARTHUR
./scripts/test_rdma_cluster.sh
```

**What this does:**
- Verifies RDMA devices are PORT_ACTIVE
- Checks Exo cluster is running (2 nodes, 768 GB)
- Downloads Llama 3.2 1B if needed (1.24 GB)
- Runs quick inference test
- Confirms system ready for production models

**Expected output:**
```
✅ RDMA device rdma_en4 is PORT_ACTIVE
✅ Exo API is responsive
✅ Cluster: 2 nodes, 768 GB
✅ Llama 3.2 1B model found
✅ Inference successful!

Model response: 2+2 equals 4.
```

---

## Step 2: Download Production Models (30-90 minutes)

After cluster health check passes:

```bash
cd /Users/arthurdell/ARTHUR
./scripts/download_cluster_models.sh
```

**Interactive prompts:**
1. ✅ Llama 3.2 1B (1.24 GB) - Already downloaded in Step 1
2. **❓ Continue with DeepSeek V3 (378 GB)?** → YES
3. **❓ Download Llama 70B (38 GB)?** → YES (recommended)
4. **❓ Download Llama 8B (4.5 GB)?** → Optional

**Recommended selections:**
- DeepSeek V3 4-bit: **YES** (primary LLM, ~30-60 min download)
- Llama 70B 4-bit: **YES** (fast fallback, ~5-10 min download)
- Llama 8B 4-bit: **Optional** (instant queries, ~1 min download)

**Total download:** ~422 GB (~55% cluster utilization)

---

## Step 3: Test Tensor Parallelism (5 minutes)

After DeepSeek V3 downloads:

```bash
# Test DeepSeek V3 (should trigger JACCL/RDMA)
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3-4bit",
    "messages": [{
      "role": "user",
      "content": "Write a Python function to implement binary search. Include docstring and type hints."
    }],
    "max_tokens": 500
  }'
```

**Monitor JACCL activation:**
```bash
# In another terminal
tail -f /tmp/exo-alpha.log | grep -E "JACCL|RDMA|IBV|distributed"
```

**Expected log entries:**
```
INFO: JACCL coordinator initialized
INFO: IBV device matrix constructed: rdma_en4
INFO: MLX distributed backend: jaccl
INFO: Tensor parallel inference started
```

---

## Step 4: Validate Performance (5 minutes)

```bash
# Test different models, compare speeds

# 1. Small model (instant)
time curl -s -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.2-1b", "messages": [{"role": "user", "content": "Hello"}]}'

# 2. Medium model (fast)
time curl -s -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-70b", "messages": [{"role": "user", "content": "Hello"}]}'

# 3. Large model (tensor parallel)
time curl -s -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-v3-4bit", "messages": [{"role": "user", "content": "Hello"}]}'
```

**Expected timings:**
- Llama 1B: <1 second
- Llama 70B: ~2-3 seconds
- DeepSeek V3: ~5-10 seconds (first token), then ~160 tokens/sec

---

## Troubleshooting

### Issue: Cluster not running
```bash
# Start on ALPHA
~/start-exo-cluster.sh

# Wait for bootstrap command, then run on BETA
# (Command will be displayed by ALPHA startup script)
```

### Issue: Model not found
```bash
# List available models
curl -s http://localhost:52415/models

# Check model cache
ls -lh ~/.cache/huggingface/hub/
```

### Issue: Slow inference
```bash
# Check RDMA device status
/usr/bin/ibv_devinfo -d rdma_en4

# Check GPU utilization
sudo powermetrics --samplers gpu_power -i 1000 -n 5

# Verify 2 nodes in cluster
curl -s http://localhost:52415/state | python3 -c "import sys,json; print(json.load(sys.stdin).get('nodeProfiles',{}))"
```

---

## Success Criteria

✅ **Cluster Validated:**
- RDMA devices PORT_ACTIVE on both nodes
- Exo cluster shows 2 nodes, 768 GB total memory
- Llama 1B inference completes in <5 seconds

✅ **Production Ready:**
- DeepSeek V3 downloaded successfully (378 GB)
- Inference works with tensor parallelism
- JACCL/RDMA activity visible in logs
- Performance: ~160 tokens/sec for DeepSeek V3

✅ **Optional Enhancements:**
- Llama 70B available for fast fallback
- Llama 8B for instant queries
- Multiple models can run concurrently

---

## Next Steps After Validation

1. **Integrate with Claude Code**
   - Create wrapper script for LLM queries
   - Add to autonomous coding workflow
   - Use for code generation, review, research

2. **Optimize Performance**
   - Benchmark different batch sizes
   - Test concurrent requests
   - Monitor memory usage patterns

3. **Production Hardening**
   - Set up auto-restart on failure
   - Add monitoring dashboard
   - Configure log rotation

---

## Quick Reference

**Start cluster:**
```bash
~/start-exo-cluster.sh  # On ALPHA
```

**Health check:**
```bash
curl -s http://localhost:52415/state | python3 -c "import sys,json; d=json.load(sys.stdin); profiles=d.get('nodeProfiles',{}); print(f'Nodes: {len(profiles)}'); total=sum(p.get('memory',{}).get('ramTotal',{}).get('inBytes',0) for p in profiles.values()); print(f'Total memory: {total/(1024**3):.0f} GB')"
```

**Test inference:**
```bash
curl -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-v3-4bit", "messages": [{"role": "user", "content": "Test"}]}'
```

---

**Total Time:** 15-30 minutes for full validation
**Download Size:** 1.24 GB (test) + 378 GB (primary) + 38 GB (fallback) = ~417 GB
**Result:** Production-ready LLM inference cluster with $0 per query
