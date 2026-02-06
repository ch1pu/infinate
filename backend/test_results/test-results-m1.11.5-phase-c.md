<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0
-->

# M1.11.5 Phase C: Extended LOD Shell Results

**Generated:** 2026-02-06 02:19 UTC
**GPU:** NVIDIA GeForce RTX 5060 Laptop GPU
**PyTorch:** 2.10.0+cu128
**CUDA:** 12.8

## LOD Hierarchy (5 levels)

| Level | Range | Compression | Max Tokens |
|-------|------:|:-----------:|:----------:|
| near | 0-50 | 1:1 | 50 |
| medium | 50-150 | 5:1 | 25 |
| far | 150-500 | 20:1 | 10 |
| beyond | 500-2000 | 100:1 | 5 |
| **horizon** | **2000-inf** | **500:1** | **3** |

## Context Expansion

- **Total tokens:** 93
- **Theoretical context:** 2375
- **Expansion ratio:** 25.54x

## 4-Level vs 5-Level Comparison

- **4-level:** 700 tokens represented
- **5-level:** 2200 tokens represented
- **Improvement:** +1500 tokens

## Test Execution

| Test | Status |
|------|--------|
| test_default_config_has_5_levels | PASS |
| test_horizon_level_properties | PASS |
| test_context_expansion_ratio | PASS |
| test_distance_to_level_mapping | PASS |
| test_lod_with_horizon_gpu | PASS |
| test_gpu_resident_with_extended_lod | PASS |
| test_wider_view_more_context | PASS |

**Total tests:** 7

---

*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*
