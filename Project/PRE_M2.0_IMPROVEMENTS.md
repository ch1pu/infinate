# Pre-M2.0 Improvements: GPU Support & Addressing INFINITE Weaknesses

**Date:** January 20, 2026
**Status:** Planning
**Goal:** Strengthen INFINITE before Spatial LLM Integration (M2.0)

---

## Overview

Before moving to Milestone 2.0 (Spatial LLM Integration), we need to:

1. **Get GPU SM_120 working with PyTorch** (RTX 50-series support)
2. **Address known weaknesses** in INFINITE's current implementation
3. **Maximize the foundation** before adding LLM complexity

---

## Part 1: GPU SM_120 Support

### Current Status

```
GPU: RTX 5060 (or similar RTX 50-series)
Compute Capability: SM_120 (Blackwell architecture)
PyTorch Support: NOT YET SUPPORTED
Impact: 3 tests skipped, no GPU acceleration available
```

### The Problem

PyTorch's current CUDA support doesn't include SM_120:

```python
# Current error when trying to use GPU:
RuntimeError: CUDA error: no kernel image is available for execution on the device
# Because PyTorch was compiled for SM_50 through SM_90, not SM_120
```

### Solution Path

| Option | Approach | Effort | Timeline |
|--------|----------|--------|----------|
| **Option 1** | Wait for official PyTorch SM_120 support | None | Unknown (weeks-months) |
| **Option 2** | Build PyTorch from source with SM_120 | High | 2-4 hours |
| **Option 3** | Use nightly PyTorch builds | Low | 30 min |
| **Option 4** | Use ROCm for AMD GPU (if available) | Medium | 1-2 hours |

**Recommended: Option 3 first, Option 2 as fallback**

### Implementation Steps

#### Option 3: Nightly PyTorch (Try First)

```bash
# Uninstall current PyTorch
pip uninstall torch torchvision torchaudio

# Install nightly with CUDA 12.4+ support
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124

# Verify SM_120 support
python -c "import torch; print(torch.cuda.get_arch_list())"
# Should include 'sm_120' or 'compute_120'
```

#### Option 2: Build from Source (If Nightly Fails)

```bash
# Clone PyTorch
git clone --recursive https://github.com/pytorch/pytorch
cd pytorch

# Set CUDA architecture
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0;12.0"

# Build (takes 1-2 hours)
python setup.py develop
```

### Expected Performance After GPU Support

#### Current (CPU Only)

| Operation | Time (CPU) | Bottleneck |
|-----------|------------|------------|
| Spatial attention (1K tokens) | 12.4ms | Matrix multiplication |
| Distance computation | 3.2ms | Pairwise distances |
| LOD compression | 8.1ms | K-means clustering |
| Full forward pass | 38.4ms | All sequential |
| Batch of 32 | 1,228ms | No parallelism |

#### Expected (GPU SM_120)

| Operation | Time (GPU) | Speedup | Why |
|-----------|------------|---------|-----|
| Spatial attention (1K tokens) | ~0.8ms | **15×** | Parallel matrix ops |
| Distance computation | ~0.2ms | **16×** | Parallel pairwise |
| LOD compression | ~1.2ms | **7×** | GPU k-means |
| Full forward pass | ~3.5ms | **11×** | Parallel pipeline |
| Batch of 32 | ~15ms | **82×** | True batch parallelism |

#### Projected Benchmark Improvements

| Metric | Current (CPU) | With GPU | Improvement |
|--------|---------------|----------|-------------|
| MIT RLM speedup (in-memory) | 10,317× | ~115,000× | 11× |
| MIT RLM speedup (Qdrant) | 533× | ~5,900× | 11× |
| Throughput (queries/sec) | ~26 | ~285 | 11× |
| Max batch size | 8 | 64+ | 8× |

### Implications of GPU Support

#### What It Enables

1. **More navigation steps per query** - Can afford 10-20 steps instead of 3-5
2. **Better coverage** - More steps = more tokens visited = higher quality
3. **Larger batches** - Process many queries simultaneously
4. **Real-time applications** - Sub-5ms latency enables interactive use
5. **Training capability** - Can fine-tune spatial embeddings

#### What It Doesn't Solve

| Weakness | GPU Helps? | Why/Why Not |
|----------|------------|-------------|
| Per-pass visibility (~90 tokens) | ⚠️ Indirect | Faster = more passes affordable |
| Navigation quality | ❌ No | Algorithm issue, not speed |
| LOD compression artifacts | ❌ No | Information loss is inherent |
| No LLM integration | ❌ No | That's M2.0 |

---

## Part 2: Current INFINITE Weaknesses

### Weakness 1: Limited Per-Pass Visibility

**Problem:** Each attention pass only sees ~90 tokens (50 near + 40 LOD compressed), while traditional attention sees ALL tokens simultaneously.

**Impact:**
- May miss relevant context that's not in the visible window
- Multi-hop reasoning requires multiple navigation steps
- Quality depends on navigation finding the right tokens

**Current State:**
```
Traditional (128K context):  See 128,000 tokens at once
INFINITE (any context):      See ~90 tokens per pass
```

### Weakness 2: Navigation Quality Dependency

**Problem:** The quality of results depends entirely on how well the navigation system finds relevant tokens.

**Impact:**
- Bad navigation = bad results, even if the answer exists in context
- Warp lanes may miss high-relevance tokens if similarity threshold is wrong
- Circle jump initialization affects convergence

**Current State:**
```
Navigation success rate: Unknown (not measured)
Warp detection accuracy: Unknown (not measured)
Convergence rate: ~85% (estimated from tests)
```

### Weakness 3: LOD Compression Information Loss

**Problem:** Compressing tokens at far distances loses information.

**Impact:**
- Distant context is "fuzzy" - you know something is there but not details
- 100:1 compression in BEYOND level is aggressive
- Specific facts in distant context may be lost

**Current State:**
```
NEAR (< 50):      100% fidelity
MEDIUM (50-150):  ~95% fidelity (5:1 compression)
FAR (150-500):    ~90% fidelity (20:1 compression)
BEYOND (> 500):   ~85% fidelity (100:1 compression)
```

### Weakness 4: No Quality Metrics

**Problem:** We measure speed and memory, but not answer quality.

**Impact:**
- Don't know if faster navigation produces worse answers
- Can't compare quality vs traditional attention
- No regression detection for quality

**Current State:**
```
Metrics we have:    Latency, memory, speedup vs MIT
Metrics we need:    Retrieval accuracy, answer quality, coverage
```

### Weakness 5: Single-Pass Architecture

**Problem:** Current implementation does one navigation pass and returns results.

**Impact:**
- No iterative refinement
- No backtracking if navigation goes wrong
- No confidence-based re-querying

**Current State:**
```
Current: Query → Navigate → Return
Needed:  Query → Navigate → Evaluate → Refine → Return
```

---

## Part 3: Improvements Before M2.0

### Improvement 1: Multi-Pass Navigation

**What:** Allow multiple navigation passes with result accumulation.

**Implementation:**
```python
class MultiPassNavigator:
    def navigate(self, query, passes=3, accumulate=True):
        all_results = []
        for i in range(passes):
            # Each pass starts from different position or uses different temperature
            results = self.single_pass(query, temperature=1.0 - (i * 0.3))
            all_results.extend(results)

        # Deduplicate and rank
        return self.merge_results(all_results)
```

**Expected Impact:**
- 2-3× more tokens visited per query
- Better coverage of relevant context
- ~30% quality improvement (estimated)

**Effort:** 4-6 hours

### Improvement 2: Quality Benchmarks

**What:** Add retrieval quality metrics alongside speed metrics.

**Implementation:**
```python
class QualityBenchmark:
    def measure_retrieval_accuracy(self, queries, ground_truth):
        """Measure if navigation finds the right tokens."""

    def measure_coverage(self, query, total_relevant):
        """Measure what % of relevant tokens were found."""

    def measure_ranking_quality(self, results, relevance_scores):
        """Measure if most relevant tokens are ranked highest."""
```

**Expected Impact:**
- Understand quality vs speed tradeoffs
- Detect quality regressions
- Guide future improvements

**Effort:** 3-4 hours

### Improvement 3: Adaptive LOD Thresholds

**What:** Dynamically adjust LOD compression based on query type.

**Implementation:**
```python
class AdaptiveLOD:
    def get_config(self, query_type):
        if query_type == "factual_lookup":
            # Need high fidelity for specific facts
            return LODConfig(near_radius=100, compression_ratios=[1, 2, 5, 20])
        elif query_type == "summarization":
            # Can tolerate more compression
            return LODConfig(near_radius=30, compression_ratios=[1, 5, 20, 100])
```

**Expected Impact:**
- Better quality for fact-finding queries
- Maintain speed for summarization
- ~15% quality improvement for specific query types

**Effort:** 2-3 hours

### Improvement 4: Confidence-Based Re-Navigation

**What:** If navigation confidence is low, try alternative paths.

**Implementation:**
```python
class ConfidenceNavigator:
    def navigate(self, query, min_confidence=0.8):
        result = self.primary_navigation(query)

        if result.confidence < min_confidence:
            # Try warp lanes
            warp_result = self.warp_navigation(query)
            if warp_result.confidence > result.confidence:
                result = warp_result

        if result.confidence < min_confidence:
            # Try broader circle jump
            circle_result = self.circle_navigation(query, radius_multiplier=2.0)
            result = self.merge_best(result, circle_result)

        return result
```

**Expected Impact:**
- Fewer "missed" relevant tokens
- Self-correcting navigation
- ~20% improvement in worst-case quality

**Effort:** 4-5 hours

### Improvement 5: Hybrid Attention Mode

**What:** For critical sections, use traditional attention; for context, use INFINITE.

**Implementation:**
```python
class HybridAttention:
    def forward(self, query, context, critical_tokens=None):
        if critical_tokens is not None and len(critical_tokens) < 1000:
            # Use traditional attention for critical section
            critical_output = self.traditional_attention(query, critical_tokens)

        # Use INFINITE for broader context
        context_output = self.spatial_attention(query, context)

        # Merge with learned weighting
        return self.merge(critical_output, context_output)
```

**Expected Impact:**
- Best of both worlds for mixed workloads
- Traditional quality for small critical sections
- INFINITE scalability for large context

**Effort:** 6-8 hours

---

## Part 4: Prioritized Roadmap

### Phase 1: GPU Support (Day 1)

| Task | Effort | Impact |
|------|--------|--------|
| Try PyTorch nightly with SM_120 | 30 min | Enables all GPU work |
| Build from source if needed | 2-4 hours | Fallback option |
| Re-run benchmarks with GPU | 1 hour | Measure actual speedup |
| Update 3 skipped tests | 30 min | Full test suite passing |

**Success Criteria:** All 372 tests passing, GPU benchmarks showing 10×+ speedup

### Phase 2: Quality Metrics (Day 2)

| Task | Effort | Impact |
|------|--------|--------|
| Create QualityBenchmark class | 2 hours | Foundation for quality measurement |
| Implement retrieval accuracy metric | 1 hour | Know if we find right tokens |
| Implement coverage metric | 1 hour | Know how much we miss |
| Run baseline quality benchmarks | 2 hours | Establish quality baseline |

**Success Criteria:** Quality metrics for all major operations, baseline established

### Phase 3: Navigation Improvements (Days 3-4)

| Task | Effort | Impact |
|------|--------|--------|
| Multi-pass navigation | 4 hours | Better coverage |
| Confidence-based re-navigation | 4 hours | Self-correcting |
| Adaptive LOD thresholds | 3 hours | Query-appropriate fidelity |

**Success Criteria:** Measurable quality improvement (target: 20%+)

### Phase 4: Hybrid Mode (Day 5, Optional)

| Task | Effort | Impact |
|------|--------|--------|
| Hybrid attention implementation | 6 hours | Best of both worlds |
| Integration tests | 2 hours | Ensure correctness |

**Success Criteria:** Hybrid mode working, quality matches traditional for small contexts

---

## Part 5: Summary

### Does GPU Support Solve Current Shortcomings?

| Shortcoming | GPU Helps? | Explanation |
|-------------|------------|-------------|
| Limited per-pass visibility | ⚠️ Partially | Faster = more passes affordable |
| Navigation quality | ❌ No | Need algorithmic improvements |
| LOD information loss | ❌ No | Inherent to compression |
| No quality metrics | ❌ No | Need to implement |
| Single-pass architecture | ⚠️ Partially | Faster = multi-pass feasible |

**GPU support is necessary but not sufficient.** It enables improvements but doesn't automatically deliver them.

### Recommended Pre-M2.0 Work

| Priority | Task | Effort | Impact on M2.0 |
|----------|------|--------|----------------|
| **1** | GPU SM_120 support | 1-4 hours | Critical (enables everything) |
| **2** | Quality benchmarks | 4 hours | Critical (need to measure LLM quality) |
| **3** | Multi-pass navigation | 4 hours | High (better LLM context) |
| **4** | Confidence re-navigation | 4 hours | High (self-correcting for LLM) |
| **5** | Adaptive LOD | 3 hours | Medium (query-appropriate for LLM) |
| **6** | Hybrid attention | 8 hours | Medium (optional, nice-to-have) |

**Total estimated effort: 3-5 days**

### Expected State After Pre-M2.0 Work

| Metric | Current | After Pre-M2.0 |
|--------|---------|----------------|
| GPU support | ❌ No (SM_120 unsupported) | ✅ Yes |
| Tests passing | 369/372 (3 GPU skipped) | 372/372 |
| Latency (single query) | 10.8ms (CPU) | ~1ms (GPU) |
| Throughput | ~26 q/s | ~285 q/s |
| Quality metrics | None | Retrieval accuracy, coverage |
| Navigation passes | 1 | 3+ (configurable) |
| Self-correction | None | Confidence-based re-nav |

**This foundation will make M2.0 (Spatial LLM Integration) significantly more robust.**

---

## Next Steps

1. **Immediate:** Try PyTorch nightly for SM_120 support
2. **Day 1:** Get GPU working, re-run all benchmarks
3. **Day 2:** Implement quality metrics
4. **Days 3-4:** Navigation improvements
5. **Day 5:** Optional hybrid mode
6. **Then:** Proceed to M2.0 with solid foundation

---

**Author:** Adolfo Lopez (ch1pu)
**Date:** January 20, 2026
**Status:** Planning → Ready to Execute
