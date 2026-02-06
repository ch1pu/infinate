<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.4 Phase B: Full Pipeline vs O(n²) Baseline Results

**Generated:** 2026-02-06 02:14 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

## Pipeline vs Baseline Speed Comparison

| Context Size | Pipeline (O(k)) | Baseline (O(n²)) | Speedup |
|-------------:|:----------------:|:-----------------:|:-------:|
| 1,000 | 18.667ms | 0.348ms | **0.02x** |
| 5,000 | 20.141ms | 5.249ms | **0.26x** |
| 10,000 | 19.512ms | 20.140ms | **1.03x** |

## Scaling Behavior (1K → 10K tokens = 10x input)

| System | 1K Time | 10K Time | Ratio |
|--------|:-------:|:--------:|:-----:|
| Pipeline (O(k)) | 18.237ms | 19.317ms | 1.06x |
| Baseline (O(n²)) | 0.356ms | 20.176ms | 56.73x |

**O(k) verification:** Pipeline ratio should be <5x for 10x input increase
**O(n²) confirmation:** Baseline ratio should be >5x for 10x input increase

## Test Execution

| Test | Status |
|------|--------|
| test_dense_baseline_forward_on_gpu | PASS |
| test_dense_baseline_processes_all_tokens | PASS |
| test_full_pipeline_all_stages_on_gpu | PASS |
| test_full_pipeline_metrics_populated | PASS |
| test_full_pipeline_output_is_finite | PASS |
| test_pipeline_vs_baseline_1k | PASS |
| test_pipeline_vs_baseline_5k | PASS |
| test_pipeline_faster_than_baseline_10k | PASS |
| test_speedup_increases_with_scale | PASS |
| test_pipeline_ok_scaling | PASS |
| test_baseline_quadratic_scaling | PASS |

**Total tests:** 11

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
