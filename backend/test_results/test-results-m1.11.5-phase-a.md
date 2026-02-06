<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.5 Phase A: GPU Spatial Hash Index Results

**Generated:** 2026-02-06 02:19 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

## Loading Screen Times

| Tokens | Load Time |
|-------:|:---------:|
| 1,000 | 0.001s |
| 10,000 | 0.006s |
| 100,000 | 0.018s |
| 500,000 | 0.068s |
| 1,000,000 | 0.125s |

## Query Performance (after 1M load)

| Tokens | Avg | P50 | P99 |
|-------:|:---:|:---:|:---:|
| 1,000,000 | 4.546ms | 4.429ms | 5.821ms |

## VRAM Usage

| Tokens | VRAM |
|-------:|:----:|
| 1,000 | 17.0 MB |
| 10,000 | 26.0 MB |
| 100,000 | 116.3 MB |
| 500,000 | 517.6 MB |
| 1,000,000 | 1019.3 MB |

## Test Execution

| Test | Status |
|------|--------|
| test_index_creation | PASS |
| test_load_1k_tokens | PASS |
| test_vram_budget_enforced | PASS |
| test_query_returns_k_neighbors | PASS |
| test_query_finds_nearest | PASS |
| test_query_respects_locality | PASS |
| test_query_empty_region | PASS |
| test_load_time_scaling | PASS |
| test_query_time_constant | PASS |
| test_vram_usage_scaling | PASS |

**Total tests:** 10

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
