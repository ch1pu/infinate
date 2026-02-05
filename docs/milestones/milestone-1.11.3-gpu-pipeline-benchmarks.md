<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)

══════════════════════════════════════════════════════════════════════════════
BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
══════════════════════════════════════════════════════════════════════════════
I'm actively seeking software engineering roles. If you're reading this code
and like what you see, let's connect:
  - GitHub: github.com/ch1pu
  - Twitter/X: @2006_adolfo
  - Project: This codebase demonstrates O(k) spatial attention, achieving
    10,317x speedup over standard transformer attention with 89.58% test coverage.
══════════════════════════════════════════════════════════════════════════════
-->

# Milestone 1.11.3: GPU Full Pipeline Benchmarks

**Status:** COMPLETE
**Started:** February 5, 2026
**Completed:** February 5, 2026
**Author:** Adolfo Lopez (ch1pu)
**Dependencies:** M1.11.2 (Full Pipeline E2E Tests, PyTorch 2.10.0+cu128)
**Priority:** HIGH (First GPU benchmark data)
**License:** Apache 2.0

---

## Problem Statement

M1.11.2 upgraded PyTorch to 2.10.0+cu128 and fixed the GPU guard in conftest.py, but:

| Issue | Impact |
|-------|--------|
| All M1.11.2 full pipeline tests run CPU-only | No GPU performance data |
| `test_gpu_memory_scaling` FAILS | NavigationAttention not moved to GPU with `.to(device)` |
| `test_gpu_execution` SKIPPED | Hard-coded `cap[0] >= 12` in test_spatial_attention_lod.py |
| `test_device_placement` SKIPPED | Hard-coded `cap[0] >= 12` in test_spatial_attention.py |
| No GPU vs CPU comparison data | All reported speedup numbers are CPU-only |

---

## Solution

### 1. Fix Hard-Coded GPU Guards (2 existing files)

Replace `cap[0] >= 12` with `check_cuda_compatible()` from conftest.py, which tests actual GPU kernel execution instead of hard-coding architecture limits:

| File | Before | After |
|------|--------|-------|
| `core/tests/test_spatial_attention.py` | `if cap[0] >= 12: pytest.skip(...)` | `is_ok, reason = check_cuda_compatible()` |
| `core/tests/test_spatial_attention_lod.py` | `if cap[0] >= 12: pytest.skip(...)` | `is_ok, reason = check_cuda_compatible()` |

### 2. GPU Benchmark Infrastructure (conftest_m1113.py)

| Component | Purpose |
|-----------|---------|
| `GPUBenchmarkResult` dataclass | Captures timing stats, throughput, GPU memory, navigation metrics |
| `M1113GPUBenchmarkRunner` | Proper GPU timing with `torch.cuda.synchronize()` before/after |
| `gpu_device` fixture | Returns CUDA device, skips if incompatible |
| `m1113_nav_attention_gpu` fixture | NavigationAttention moved to GPU with `.to(device)` |
| `m1113_test_data_factory` fixture | Creates reproducible test data on any device |

### 3. 18 Benchmark Tests (test_m1113_gpu_pipeline_benchmarks.py)

| Class | Tests | Focus |
|-------|-------|-------|
| TestM1113GPUGuardFixes | 3 | Corrected versions of broken/skipped GPU tests |
| TestM1113GPUFullPipeline | 4 | Full pipeline correctness on GPU |
| TestM1113GPUvsCPUBenchmarks | 5 | GPU vs CPU latency, scaling, throughput |
| TestM1113GPUMemoryProfiling | 3 | VRAM scaling, breakdown, cleanup |
| TestM1113GPUNavigationMetrics | 2 | Navigation correctness and CPU/GPU parity |
| TestM1113ResultsSaver | 1 | Writes results to test-results-m1.11.3.md |

---

## Key Design Decisions

### GPU Timing Requires torch.cuda.synchronize()

GPU operations are asynchronous. Without synchronize, you measure kernel launch time (~5us), not execution:

```python
torch.cuda.synchronize()
start = time.perf_counter()
output, metrics = nav_attention.query(query, embeddings, positions)
torch.cuda.synchronize()
elapsed_ms = (time.perf_counter() - start) * 1000
```

### Separate Model Instances Per Device

GPU vs CPU comparison creates two NavigationAttention instances, not one moved between devices. This avoids polluting timing with device transfer overhead.

### GPU Floating-Point Non-Determinism

GPU parallel reductions (norm, mean) use different accumulation orders across threads, causing small output differences (~0.01) between identical runs. The output consistency test uses `atol=0.02` to account for this — not a bug, a hardware characteristic.

### Small Contexts: CPU Faster Than GPU

CUDA kernel launch overhead (~5-20us per op) dominates for small contexts. The scaling curve test identifies the crossover point where GPU becomes faster.

---

## Files Modified

| File | Change |
|------|--------|
| `backend/spatial_engine/core/tests/test_spatial_attention.py` | Replace hard-coded SM check with `check_cuda_compatible()` |
| `backend/spatial_engine/core/tests/test_spatial_attention_lod.py` | Replace hard-coded SM check with `check_cuda_compatible()` |
| `backend/pyproject.toml` | Add `m1113`, `m1113_gpu`, `m1113_benchmark` markers |

## Files Created

| File | Purpose |
|------|---------|
| `backend/spatial_engine/tests/conftest_m1113.py` | GPU fixtures, benchmark runner, dataclass |
| `backend/spatial_engine/tests/test_m1113_gpu_pipeline_benchmarks.py` | 18 GPU benchmark tests |
| `docs/milestones/milestone-1.11.3-gpu-pipeline-benchmarks.md` | This file |
| `Project/MILESTONE_1.11.3_COMPLETE.md` | Completion report with actual numbers |

---

## Running the Tests

```bash
cd /home/ch1pu/infinate/backend && source .venv/bin/activate

# M1.11.3 suite only (18 tests)
poetry run pytest spatial_engine/tests/test_m1113_gpu_pipeline_benchmarks.py -v -s --no-cov

# By marker
poetry run pytest -m m1113 -v -s --no-cov

# GPU tests only
poetry run pytest -m m1113_gpu -v -s --no-cov

# Benchmark tests only
poetry run pytest -m m1113_benchmark -v -s --no-cov

# Full regression check
poetry run pytest --cov=spatial_engine --cov-fail-under=89
```

---

## Verification Steps and Results

### Step 1: GPU Guard Fixes Verified

```bash
poetry run pytest spatial_engine/core/tests/test_spatial_attention.py::TestSpatialAttention::test_device_placement -v -s --no-cov
poetry run pytest spatial_engine/core/tests/test_spatial_attention_lod.py::TestDevicePlacement::test_gpu_execution -v -s --no-cov
```

| Test | Before M1.11.3 | After M1.11.3 |
|------|----------------|---------------|
| `test_device_placement` | SKIPPED (hard-coded `cap[0] >= 12`) | PASSED |
| `test_gpu_execution` | SKIPPED (hard-coded `cap[0] >= 12`) | PASSED |

### Step 2: M1.11.3 Suite (18 tests)

```bash
poetry run pytest spatial_engine/tests/test_m1113_gpu_pipeline_benchmarks.py -v -s --no-cov
```

**Result:** 18/18 passed in 23.95s

### Step 3: Full Regression

```bash
poetry run pytest --cov=spatial_engine --cov-fail-under=89
```

| Metric | Value |
|--------|-------|
| Total tests | 394 |
| Passed | 394 (after pre-existing bug fix) |
| Failed | 0 |
| Coverage | 90.53% (threshold: 89%) |
| Duration | 1100.86s (18:20) |

**Pre-existing bug found and fixed:** `test_m111_navigation_benchmarks.py::TestMemoryComplexity::test_gpu_memory_scaling`
had `NavigationAttention` created without `.to(device)`. Was hidden by the old `cap[0] >= 12` skip guard.
Fixed by adding `.to(device)` — test now passes and confirms O(k) memory on GPU (3.50x for 10x tokens).

### Step 4: Code Quality

```bash
poetry run black --check <m1113 files>   # All clean
poetry run ruff check <m1113 files>      # All clean
```

---

## Hardware

| Component | Spec |
|-----------|------|
| GPU | NVIDIA GeForce RTX 5060 (SM_120, Blackwell) |
| APU | AMD AI Max 350 (Zen 5 CPU, Radeon 890M iGPU, XDNA 2 NPU) |
| RAM | 64 GB DDR5 |
| OS | WSL2 Ubuntu on Windows 11 |
| PyTorch | 2.10.0+cu128 |
| CUDA | 12.8 |

---

## M1.11.3 Shortcomings

M1.11.3 answered the question "does GPU help?" — yes, above ~20K tokens. But it left
several gaps:

### Not the Full Pipeline

M1.11.3 only benchmarks `NavigationAttention.query()` — 3 of 7 README pipeline stages:

| Stage | GPU Tested? |
|-------|-------------|
| SpatialToken | No — raw tensors used |
| SpatialEncoding | No — raw 3D coords used |
| **SpatialAttention O(k)** | **Yes** |
| SpatialTransformer (stacked) | No — single layer only |
| VectorStore (Qdrant/pgvector) | No — in-memory only |
| **LOD System** | **Yes** |
| **Strafe Jump Navigation** | **Yes** |

Future milestones should benchmark the true end-to-end pipeline including token
creation, spatial encoding, transformer stacking, and vector store retrieval.

### Other Gaps

1. **Manual device selection** — No code automatically picks CPU vs GPU.
2. **GPU penalty at small contexts** — 4.2x slower than CPU at 1K tokens.
3. **CPU bottleneck at large contexts** — 3.9x slower than GPU at 50K tokens.
4. **Double memory for both paths** — Separate CPU and GPU instances required.
5. **Crossover point is documentation-only** — ~20K threshold not in code.

---

## Next: M1.11.4 — Full Pipeline GPU Benchmarks + Hybrid Router

M1.11.3 only benchmarks `NavigationAttention.query()` — 3 of 7 README pipeline stages.
M1.11.4 closes this gap with 4 phases:

| Phase | Goal |
|-------|------|
| **A** | Get all 7 pipeline stages running and verified on GPU |
| **B** | Full pipeline O(n²) baseline comparison (like M1.8 but with complete pipeline) |
| **C** | Hybrid CPU/GPU router with auto-calibrate threshold (~15K default) |
| **D** | Full pipeline GPU vs CPU comparison to find true crossover point |

### Phase A: Full Pipeline GPU Coverage

| Stage | Component | M1.11.3 Status | M1.11.4 Goal |
|-------|-----------|----------------|--------------|
| 1 | SpatialToken | Not tested | Verify on GPU |
| 2 | SpatialEncoding | Not tested | Verify on GPU |
| 3 | SpatialAttention O(k) | **Tested** | Confirm via full pipeline |
| 4 | SpatialTransformer (stacked) | Not tested | Multi-layer on GPU |
| 5 | VectorStore (Qdrant/pgvector) | Not tested | In-memory on GPU tensors |
| 6 | LOD System | **Tested** | Confirm via full pipeline |
| 7 | Strafe Jump Navigation | **Tested** | Confirm via full pipeline |

### Phase B: Full Pipeline O(n²) Baseline Comparison

M1.8 compared O(k) vs O(n²) but only with `SpatialAttention` alone. M1.11.4 repeats
that comparison with the true end-to-end pipeline (all 7 stages), producing the first
honest "full pipeline speedup" numbers.

### Phase C: Hybrid CPU/GPU Router

`HybridNavigationAttention` wrapper with two upfront instances (CPU + GPU), auto-calibrate
threshold (default ~15K), Option C data placement (accept any device, move if needed),
same `.query()` API. See `Project/MILESTONE_1.11.3_COMPLETE.md` for M1.11.3 benchmark
data tables showing the crossover.

### Phase D: Full Pipeline GPU vs CPU Comparison

Benchmark all 7 stages on both devices (1K → 50K tokens) to find the true full-pipeline
crossover point, which may differ from the NavigationAttention-only ~20K crossover.
