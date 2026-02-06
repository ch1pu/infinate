# Copyright 2025-2026 Adolfo Lopez (ch1pu)
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
# Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)
#
# ============================================================================
# BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
# ============================================================================
# I'm actively seeking software engineering roles. If you're reading this code
# and like what you see, let's connect:
#   - GitHub: github.com/ch1pu
#   - Twitter/X: @2006_adolfo
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over standard transformer attention with 89.58% test coverage.
# ============================================================================

"""
test_m1115_phase_c_extended_lod.py - Extended LOD Shell with Horizon Level.

Tests the new 5-level LOD hierarchy: near/medium/far/beyond/horizon.
The "horizon" level at 2000-inf with 500:1 compression and 3 max tokens
expands theoretical context from 9.7x to 25.5x.

8 tests across 3 classes:
- TestM1115ExtendedLODConfig (4): 5 levels, horizon properties, expansion ratio,
  distance-to-level mapping
- TestM1115ExtendedLODBenchmarks (3): Horizon on GPU, GPU-resident + extended LOD,
  wider view comparison
- TestM1115PhaseCResultsSaver (1): Save results to markdown

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.5 - GPU-Resident Vector Store (Phase C)
"""

import os
from datetime import UTC, datetime

import pytest
import torch

from spatial_engine.core.lod import LODConfig, LODLevel
from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.navigation_attention import NavigationAttention
from spatial_engine.tests.conftest_m1114 import (
    M1114_D_MODEL,
    M1114_K_NEIGHBORS,
    M1114_SPATIAL_RADIUS,
)
from spatial_engine.tests.conftest_m1115 import M1115_CELL_SIZE, M1115_VRAM_BUDGET_GB
from spatial_engine.tests.test_m1115_phase_b_pipeline_integration import (
    run_full_pipeline_gpu_resident,
)
from spatial_engine.vector_store.gpu_spatial_index import GPUSpatialIndex

# Load M1.11.5 fixtures
pytest_plugins = ["spatial_engine.tests.conftest_m1115"]

# Module-level results collector
_benchmark_results: list[dict] = []


# ---------------------------------------------------------------------------
# Class 1: TestM1115ExtendedLODConfig (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
class TestM1115ExtendedLODConfig:
    """Verify the new 5-level LOD configuration."""

    def test_default_config_has_5_levels(self) -> None:
        """Default LODConfig now has 5 levels: near/medium/far/beyond/horizon."""
        config = LODConfig()

        assert len(config.levels) == 5
        names = [level.name for level in config.levels]
        assert names == ["near", "medium", "far", "beyond", "horizon"]

        print(f"\n5-level LOD: {names}")

        _benchmark_results.append(
            {
                "test": "test_default_config_has_5_levels",
                "status": "PASS",
                "levels": names,
            }
        )

    def test_horizon_level_properties(self) -> None:
        """Horizon level: min=2000, max=inf, ratio=500, max_tokens=3."""
        config = LODConfig()
        horizon = config.levels[4]

        assert horizon.name == "horizon"
        assert horizon.min_radius == 2000.0
        assert horizon.max_radius == float("inf")
        assert horizon.compression_ratio == 500
        assert horizon.max_tokens == 3

        print(
            f"\nHorizon: {horizon.min_radius}-{horizon.max_radius}, "
            f"ratio={horizon.compression_ratio}, max_tokens={horizon.max_tokens}"
        )

        _benchmark_results.append(
            {
                "test": "test_horizon_level_properties",
                "status": "PASS",
                "min_radius": horizon.min_radius,
                "max_radius": str(horizon.max_radius),
                "compression_ratio": horizon.compression_ratio,
                "max_tokens": horizon.max_tokens,
            }
        )

    def test_context_expansion_ratio(self) -> None:
        """Theoretical expansion ~25.5x (up from 9.7x with 4 levels)."""
        config = LODConfig()

        total_tokens = config.total_tokens
        theoretical_context = config.theoretical_context
        ratio = theoretical_context / total_tokens

        # 50*1 + 25*5 + 10*20 + 5*100 + 3*500 = 2375
        # 50 + 25 + 10 + 5 + 3 = 93
        # 2375 / 93 ≈ 25.54
        assert total_tokens == 93
        assert theoretical_context == 2375
        assert 25.0 < ratio < 26.0

        print(
            f"\nExpansion: {theoretical_context} / {total_tokens} = {ratio:.2f}x " f"(up from 9.7x)"
        )

        _benchmark_results.append(
            {
                "test": "test_context_expansion_ratio",
                "status": "PASS",
                "total_tokens": total_tokens,
                "theoretical_context": theoretical_context,
                "expansion_ratio": round(ratio, 2),
            }
        )

    def test_distance_to_level_mapping(self) -> None:
        """Verify distances map to correct levels."""
        config = LODConfig()

        test_cases = [
            (25.0, "near"),
            (100.0, "medium"),
            (300.0, "far"),
            (1000.0, "beyond"),
            (3000.0, "horizon"),
        ]

        for distance, expected_name in test_cases:
            level = config.get_level_by_distance(distance)
            assert (
                level.name == expected_name
            ), f"Distance {distance} → {level.name}, expected {expected_name}"

        print("\nDistance mapping: 25→near, 100→medium, 300→far, 1000→beyond, 3000→horizon")

        _benchmark_results.append(
            {
                "test": "test_distance_to_level_mapping",
                "status": "PASS",
                "mappings": {str(d): n for d, n in test_cases},
            }
        )


# ---------------------------------------------------------------------------
# Class 2: TestM1115ExtendedLODBenchmarks (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
@pytest.mark.m1115_gpu
class TestM1115ExtendedLODBenchmarks:
    """Benchmark extended LOD with GPU-resident data."""

    def test_lod_with_horizon_gpu(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Spread 10K tokens over large radius, verify horizon level populated."""
        torch.manual_seed(42)
        n = 10_000
        d_model = M1114_D_MODEL

        # Spread tokens from 0 to 5000 units — some will land in horizon (>2000)
        _embeddings = torch.randn(n, d_model, device=gpu_device)  # noqa: F841
        positions = torch.randn(n, 3, device=gpu_device) * 2500.0

        query_pos = torch.zeros(3, device=gpu_device)

        # Count tokens per LOD level
        config = LODConfig()
        distances = torch.norm(positions - query_pos.unsqueeze(0), dim=-1)

        level_counts: dict[str, int] = {}
        for level in config.levels:
            mask = (distances >= level.min_radius) & (distances < level.max_radius)
            level_counts[level.name] = mask.sum().item()

        # Horizon should have tokens (distance > 2000)
        assert level_counts["horizon"] > 0, f"No tokens in horizon level: {level_counts}"

        print("\nLOD level distribution (10K tokens, spread ±2500):")
        for name, count in level_counts.items():
            print(f"  {name}: {count}")

        _benchmark_results.append(
            {
                "test": "test_lod_with_horizon_gpu",
                "status": "PASS",
                "level_counts": level_counts,
            }
        )

    def test_gpu_resident_with_extended_lod(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Full pipeline (GPU-resident) with horizon level works end-to-end."""
        torch.manual_seed(42)
        n = 10_000

        # Spread tokens widely so horizon level is populated
        embeddings = torch.randn(n, M1114_D_MODEL)
        positions = torch.randn(n, 3) * 2500.0

        gpu_index = GPUSpatialIndex(
            cell_size=M1115_CELL_SIZE,
            vram_budget_gb=M1115_VRAM_BUDGET_GB,
            device=gpu_device,
        )
        gpu_index.load(embeddings, positions)

        spatial_encoding = SpatialPositionEncoding(d_model=M1114_D_MODEL).to(gpu_device)
        nav_attention = NavigationAttention(
            d_model=M1114_D_MODEL,
            spatial_radius=M1114_SPATIAL_RADIUS,
            k_neighbors=M1114_K_NEIGHBORS,
            enable_navigation=True,
            enable_lod=True,
            gpu_index=gpu_index,
        ).to(gpu_device)
        spatial_transformer = SpatialTransformer(
            n_layers=2,
            d_model=M1114_D_MODEL,
            n_heads=8,
            d_ff=1024,
            spatial_radius=M1114_SPATIAL_RADIUS,
            dropout=0.1,
        ).to(gpu_device)

        with torch.no_grad():
            output, metrics = run_full_pipeline_gpu_resident(
                gpu_index=gpu_index,
                spatial_encoding=spatial_encoding,
                nav_attention=nav_attention,
                spatial_transformer=spatial_transformer,
                device=gpu_device,
            )

        assert torch.isfinite(output).all(), "Output contains NaN/Inf"
        assert output.shape[-1] == M1114_D_MODEL
        assert metrics.attention_ops == 1

        print(
            f"\nGPU-resident + extended LOD: shape={output.shape}, "
            f"tokens_accessed={metrics.tokens_accessed}"
        )

        _benchmark_results.append(
            {
                "test": "test_gpu_resident_with_extended_lod",
                "status": "PASS",
                "output_shape": list(output.shape),
                "tokens_accessed": metrics.tokens_accessed,
            }
        )

    def test_wider_view_more_context(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Compare 4-level vs 5-level on same data: 5-level sees more tokens."""
        torch.manual_seed(42)
        n = 10_000
        d_model = M1114_D_MODEL

        _embeddings = torch.randn(n, d_model, device=gpu_device)  # noqa: F841
        positions = torch.randn(n, 3, device=gpu_device) * 2500.0
        query_pos = torch.zeros(3, device=gpu_device)

        # 4-level config (old default)
        config_4 = LODConfig(
            levels=[
                LODLevel("near", 0.0, 50.0, 1, 50),
                LODLevel("medium", 50.0, 150.0, 5, 25),
                LODLevel("far", 150.0, 500.0, 20, 10),
                LODLevel("beyond", 500.0, float("inf"), 100, 5),
            ]
        )

        # 5-level config (new default)
        config_5 = LODConfig()

        # Count theoretical tokens represented by each config
        distances = torch.norm(positions - query_pos.unsqueeze(0), dim=-1)

        tokens_4 = 0
        for level in config_4.levels:
            mask = (distances >= level.min_radius) & (distances < level.max_radius)
            count = mask.sum().item()
            tokens_4 += min(count, level.max_tokens) * level.compression_ratio

        tokens_5 = 0
        for level in config_5.levels:
            mask = (distances >= level.min_radius) & (distances < level.max_radius)
            count = mask.sum().item()
            tokens_5 += min(count, level.max_tokens) * level.compression_ratio

        # 5-level should represent more tokens than 4-level
        assert (
            tokens_5 >= tokens_4
        ), f"5-level ({tokens_5}) should represent >= 4-level ({tokens_4}) tokens"

        print(
            f"\n4-level represents: {tokens_4} tokens"
            f"\n5-level represents: {tokens_5} tokens"
            f"\nImprovement: {tokens_5 - tokens_4} more tokens "
            f"({tokens_5 / max(tokens_4, 1):.2f}x)"
        )

        _benchmark_results.append(
            {
                "test": "test_wider_view_more_context",
                "status": "PASS",
                "tokens_4_level": tokens_4,
                "tokens_5_level": tokens_5,
                "improvement": tokens_5 - tokens_4,
            }
        )


# ---------------------------------------------------------------------------
# Class 3: TestM1115PhaseCResultsSaver (1 test)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
class TestM1115PhaseCResultsSaver:
    """Save Phase C results to markdown."""

    def test_z_save_phase_c_results(self) -> None:
        """Write collected results to test-results-m1.11.5-phase-c.md."""
        if not _benchmark_results:
            pytest.skip("No results to save (other tests may have been skipped)")

        results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, "test-results-m1.11.5-phase-c.md")

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

        gpu_name = "N/A"
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)

        # Build all test rows
        test_rows = []
        for r in _benchmark_results:
            test_rows.append(f"| {r['test']} | {r['status']} |")

        # Extract expansion ratio
        expansion_row = ""
        for r in _benchmark_results:
            if r["test"] == "test_context_expansion_ratio":
                expansion_row = (
                    f"- **Total tokens:** {r.get('total_tokens', 'N/A')}\n"
                    f"- **Theoretical context:** {r.get('theoretical_context', 'N/A')}\n"
                    f"- **Expansion ratio:** {r.get('expansion_ratio', 'N/A')}x"
                )

        # Extract wider view comparison
        wider_row = ""
        for r in _benchmark_results:
            if r["test"] == "test_wider_view_more_context":
                wider_row = (
                    f"- **4-level:** {r.get('tokens_4_level', 'N/A')} tokens represented\n"
                    f"- **5-level:** {r.get('tokens_5_level', 'N/A')} tokens represented\n"
                    f"- **Improvement:** +{r.get('improvement', 'N/A')} tokens"
                )

        lines = [
            "<!--",
            "Copyright 2025-2026 Adolfo Lopez (ch1pu)",
            "SPDX-License-Identifier: Apache-2.0",
            "-->",
            "",
            "# M1.11.5 Phase C: Extended LOD Shell Results",
            "",
            f"**Generated:** {now}",
            f"**GPU:** {gpu_name}",
            f"**PyTorch:** {torch.__version__}",
            f"**CUDA:** {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
            "",
            "## LOD Hierarchy (5 levels)",
            "",
            "| Level | Range | Compression | Max Tokens |",
            "|-------|------:|:-----------:|:----------:|",
            "| near | 0-50 | 1:1 | 50 |",
            "| medium | 50-150 | 5:1 | 25 |",
            "| far | 150-500 | 20:1 | 10 |",
            "| beyond | 500-2000 | 100:1 | 5 |",
            "| **horizon** | **2000-inf** | **500:1** | **3** |",
            "",
            "## Context Expansion",
            "",
            expansion_row,
            "",
            "## 4-Level vs 5-Level Comparison",
            "",
            wider_row,
            "",
            "## Test Execution",
            "",
            "| Test | Status |",
            "|------|--------|",
            *test_rows,
            "",
            f"**Total tests:** {len(_benchmark_results)}",
            "",
            "---",
            "",
            "*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*",
            "",
        ]

        with open(results_path, "w") as f:
            f.write("\n".join(lines))

        print(f"\nPhase C results saved to: {results_path}")
        print(f"Total results recorded: {len(_benchmark_results)}")
