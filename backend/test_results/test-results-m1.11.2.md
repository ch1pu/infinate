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
-->

# Milestone 1.11.2: Full Pipeline E2E Tests - Test Results

**Status:** COMPLETE
**Date:** 2026-02-05 20:02 UTC
**Author:** Adolfo Lopez (ch1pu)
**License:** Apache 2.0 - Open Source

---

## Executive Summary

Milestone 1.11.2 corrects the M1.11 end-to-end tests to exercise the
**full pipeline** (Qdrant -> Navigator -> LOD -> SpatialAttention -> Output)
instead of stopping at the Navigator step.

### Key Metrics

| Metric | Value |
|--------|-------|
| Full Pipeline Tests | 2 |
| Full Pipeline Mean Latency | 146.31ms |
| Partial Pipeline Mean Latency | 87.69ms |
| Full Pipeline Overhead | 1.67x |
| Output Shape Verified | (256,) |

---

## Test Execution Results

| Test | Status |
|------|--------|
| test_full_navigation_pipeline | PASS |
| test_warp_lane_assisted_full_pipeline | PASS |
| test_combined_full_pipeline_benchmark | PASS |

---

## Full Navigation Pipeline Results

| Metric | Value |
|--------|-------|
| Qdrant tokens retrieved | 1000 |
| Output shape | (256,) |
| Navigation steps | 10 |
| Attention operations | 1 |
| Tokens accessed (LOD) | 998 |
| Warp count | 0 |
| Converged | False |
| Final similarity | 0.0862 |
| Trajectory length | 72.88 |

---

## Warp Lane Assisted Pipeline Results

| Metric | Value |
|--------|-------|
| Nearby tokens | 500 |
| Warp candidate tokens | 100 |
| Combined context | 600 |
| Output shape | (256,) |
| Attention operations | 1 |
| Tokens accessed (LOD) | 590 |
| Warp count | 0 |
| Converged | False |
| Final similarity | -0.0399 |

---

## Benchmark Comparison: Partial vs Full Pipeline

**Tokens:** 2000 | **Iterations:** 50

| Pipeline | Mean (ms) | p50 (ms) | p95 (ms) |
|----------|-----------|----------|----------|
| Partial (Nav only) | 87.69 | 85.33 | 139.66 |
| Full (Nav+LOD+Attn) | 146.31 | 146.73 | 152.50 |

**Full Pipeline Overhead:** 1.67x

### Navigation Metrics (Last Run)

| Metric | Value |
|--------|-------|
| Steps | 10 |
| Warps | 0 |
| Attention Ops | 1 |
| Tokens Accessed (LOD) | 57 |
| Converged | False |
| Final Similarity | 0.0107 |
| Trajectory Length | 142.68 |

---

## GPU Test Results (RTX 5060 SM_120)

After upgrading PyTorch to 2.10.0+cu128 and fixing the GPU compatibility guard,
existing GPU tests were run (`poetry run pytest -k "gpu or cuda" -v -s`):

| Test | Status | Detail |
|------|--------|--------|
| `test_gpu_utilization_comparison` | **PASS** | 14,557 tokens/sec on RTX 5060 |
| `test_gpu_memory_scaling` | **FAIL** | Device mismatch — model on CPU, input on CUDA |
| `test_gpu_execution` | **SKIP** | Old hard-coded SM check (not using updated guard) |

**First GPU test to ever pass in this project.**

### GPU Failure Analysis

- `test_gpu_memory_scaling`: `NavigationAttention()` model weights stay on CPU.
  Test needs `.to(device)` on the model before passing CUDA tensors. Test-level bug.
- `test_gpu_execution`: Has its own SM architecture skip in `test_spatial_attention_lod.py`,
  not using the updated `check_cuda_compatible()` runtime test.

---

## Conclusion

M1.11.2 successfully corrects the E2E test gap from M1.11 by running
the **complete** NavigationAttention.query() pipeline. All tests verify
that the output tensor has the correct shape, that attention was actually
computed (not just navigation), and that LOD compression processed tokens.

GPU support was restored (PyTorch 2.10.0+cu128, SM_120) with the first GPU
test passing at 14,557 tokens/sec. Two remaining GPU tests need fixes in M1.11.3.

---

**Status:** COMPLETE
**Date:** 2026-02-05 20:02 UTC
**Author:** Adolfo Lopez (ch1pu)
**License:** Apache 2.0 - Open Source
