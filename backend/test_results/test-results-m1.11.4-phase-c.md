<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.4 Phase C: Full Pipeline Extreme-Scale Benchmarks

**Generated:** 2026-02-06 02:18 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

---

## Pipeline Scaling Curve (O(k) Constant Complexity)

| Context Size | Latency |
|-------------:|:-------:|
|     1,000 | 18.541ms |
|     5,000 | 19.907ms |
|    10,000 | 19.994ms |
|    25,000 | 23.768ms |
|    50,000 | 28.064ms |
|   100,000 | 40.604ms |
|   500,000 | 133.376ms |
| 1,000,000 | 377.348ms |

## Baseline Scaling Curve (O(n^2) Quadratic)

| Context Size | Latency |
|-------------:|:-------:|
|     1,000 | 0.370ms |
|     5,000 | 5.086ms |
|    10,000 | 20.180ms |
|    25,000 | 128.182ms |
|    50,000 | 89173.562ms |

## Head-to-Head Speed Comparison

| Context Size | Pipeline (O(k)) | Baseline (O(n^2)) | Speedup |
|-------------:|:----------------:|:-----------------:|:-------:|
|     1,000 | 20.839ms | 0.356ms | **0.02x** |
|     5,000 | 22.066ms | 5.174ms | **0.23x** |
|    10,000 | 25.056ms | 19.928ms | **0.80x** |
|    25,000 | 24.719ms | 128.628ms | **5.20x** |

## Memory Scaling

### Pipeline (O(k) attention, linear transfer)

| Context Size | Peak GPU Memory |
|-------------:|:---------------:|
|     1,000 | 22.30 MB |
|    10,000 | 76.80 MB |
|   100,000 | 606.70 MB |
| 1,000,000 | 5899.66 MB |

### Baseline (O(n^2) attention matrix)

| Context Size | Peak GPU Memory |
|-------------:|:---------------:|
|     1,000 | 22.39 MB |
|     5,000 | 226.29 MB |
|    10,000 | 823.64 MB |

## Extreme Scale (Pipeline Only)

| Context Size | Latency | Status |
|-------------:|:-------:|:------:|
|   500,000 | 140.483ms | PASS |
| 1,000,000 | 440.819ms | PASS |

## Test Execution

| Test | Status |
|------|--------|
| test_pipeline_scaling_curve | PASS |
| test_baseline_scaling_curve | PASS |
| test_head_to_head_comparison | PASS |
| test_pipeline_wins_at_scale | PASS |
| test_pipeline_memory_ok | PASS |
| test_baseline_memory_quadratic | PASS |
| test_pipeline_500k_tokens | PASS |
| test_pipeline_1m_tokens | PASS |

**Total tests:** 8

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
