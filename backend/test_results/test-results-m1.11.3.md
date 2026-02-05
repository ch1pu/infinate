<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.3 GPU Full Pipeline Benchmark Results

**Generated:** 2026-02-05 21:28 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

## Test Execution

| Test | Status |
|------|--------|
| test_navigation_attention_gpu_device_placement | PASS |
| test_spatial_attention_gpu_execution | PASS |
| test_spatial_attention_device_transfer | PASS |
| test_full_pipeline_gpu_forward | PASS |
| test_full_pipeline_gpu_with_navigation | PASS |
| test_full_pipeline_gpu_no_navigation_baseline | PASS |
| test_full_pipeline_gpu_output_consistency | PASS |
| test_gpu_vs_cpu_latency_small_context | PASS |
| test_gpu_vs_cpu_latency_medium_context | PASS |
| test_gpu_vs_cpu_latency_large_context | PASS |
| test_gpu_vs_cpu_scaling_curve | PASS |
| test_gpu_vs_cpu_throughput | PASS |
| test_gpu_memory_scaling | PASS |
| test_gpu_memory_breakdown | PASS |
| test_gpu_memory_cleanup | PASS |
| test_gpu_navigation_metrics_correctness | PASS |
| test_gpu_navigation_quality_parity | PASS |

**Total tests:** 17

## GPU vs CPU Scaling Curve

| Tokens | CPU Mean (ms) | GPU Mean (ms) | Speedup | GPU Peak (MB) |
|--------|---------------|---------------|---------|---------------|
| 1,000 | 6.18 | 17.66 | 0.35x | 14.3 |
| 2,000 | 4.95 | 16.81 | 0.29x | 19.2 |
| 5,000 | 7.89 | 16.70 | 0.47x | 30.0 |
| 10,000 | 11.02 | 16.61 | 0.66x | 50.6 |
| 20,000 | 27.34 | 17.50 | 1.56x | 90.8 |
| 50,000 | 60.68 | 21.13 | 2.87x | 206.8 |

**GPU Crossover Point:** ~20,000 tokens

## GPU Memory Scaling

| Tokens | Allocated (MB) | Peak (MB) | Ratio |
|--------|----------------|-----------|-------|
| 1,000 | 11.38 | 14.32 | 1.00x |
| 5,000 | 15.33 | 30.04 | 2.10x |
| 10,000 | 20.27 | 50.62 | 3.54x |
| 50,000 | 59.79 | 206.85 | 14.45x |

**O(k) Verified:** True

## Sustained Throughput

- **CPU:** 168.5 queries/sec (336,984 tokens/sec)
- **GPU:** 57.5 queries/sec (115,094 tokens/sec)

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
