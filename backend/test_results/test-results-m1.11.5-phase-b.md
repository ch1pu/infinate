<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.5 Phase B: Pipeline Integration Results

**Generated:** 2026-02-06 02:19 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

## Transfer vs GPU-Resident Pipeline

| Tokens | Transfer (O(n)) | Resident (O(k)) | Speedup |
|-------:|:---------------:|:---------------:|:-------:|
| 1,000 | 19.538ms | 31.148ms | **0.63x** |
| 100,000 | 39.838ms | 31.349ms | **1.27x** |
| 1,000,000 | 486.599ms | 26.632ms | **18.27x** |

## GPU-Resident Scaling (should be flat = true O(k))

| Tokens | Resident Time |
|-------:|:------------:|
| 1,000 | 29.147ms |
| 10,000 | 31.517ms |
| 100,000 | 31.337ms |
| 1,000,000 | 28.692ms |

## Test Execution

| Test | Status |
|------|--------|
| test_gpu_index_in_nav_attention | PASS |
| test_backward_compatible | PASS |
| test_query_gpu_resident_returns_valid | PASS |
| test_gpu_resident_matches_brute_force | PASS |
| test_transfer_pipeline_vs_resident_1k | PASS |
| test_transfer_pipeline_vs_resident_100k | PASS |
| test_transfer_pipeline_vs_resident_1m | PASS |
| test_resident_scaling_flat | PASS |

**Total tests:** 8

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
