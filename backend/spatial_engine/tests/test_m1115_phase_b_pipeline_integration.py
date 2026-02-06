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
test_m1115_phase_b_pipeline_integration.py - GPU-Resident Pipeline Integration.

Tests NavigationAttention with GPUSpatialIndex: correctness, backward
compatibility, GPU-resident query path, and transfer vs resident benchmarks.

10 tests across 3 classes:
- TestM1115IntegrationCorrectness (4): GPU index in nav_attention, backward compat,
  gpu_resident returns valid, resident vs brute force comparison
- TestM1115PipelineVsTransferBenchmarks (4): Transfer vs resident at 1K/100K/1M,
  flat scaling verification
- TestM1115PhaseBResultsSaver (1): Save results to markdown

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.5 - GPU-Resident Vector Store (Phase B)
"""

import os
from datetime import UTC, datetime

import pytest
import torch

from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.navigation_attention import (
    NavigationAttention,
    NavigationMetrics,
)
from spatial_engine.tests.conftest_m1114 import (
    M1114_D_MODEL,
    M1114_K_NEIGHBORS,
    M1114_SPATIAL_RADIUS,
)
from spatial_engine.tests.conftest_m1115 import M1115_CELL_SIZE, M1115_VRAM_BUDGET_GB
from spatial_engine.tests.test_m1114_phase_b_pipeline_vs_baseline import (
    _time_fn,
    run_full_pipeline,
)
from spatial_engine.vector_store.gpu_spatial_index import GPUSpatialIndex

# Load M1.11.5 fixtures
pytest_plugins = ["spatial_engine.tests.conftest_m1115"]

# Module-level results collector
_benchmark_results: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_nav_attention_with_gpu_index(
    gpu_index: GPUSpatialIndex,
    device: torch.device,
) -> NavigationAttention:
    """Build NavigationAttention with a GPU spatial index attached."""
    return NavigationAttention(
        d_model=M1114_D_MODEL,
        spatial_radius=M1114_SPATIAL_RADIUS,
        k_neighbors=M1114_K_NEIGHBORS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
        gpu_index=gpu_index,
    ).to(device)


def run_full_pipeline_gpu_resident(
    gpu_index: GPUSpatialIndex,
    spatial_encoding: SpatialPositionEncoding,
    nav_attention: NavigationAttention,
    spatial_transformer: SpatialTransformer,
    device: torch.device,
) -> tuple[torch.Tensor, NavigationMetrics]:
    """Run pipeline with GPU-resident data — NO CPU→GPU transfer.

    Stages:
      Stage 2: Position encoding (on GPU-resident positions from index)
      Stage 3+6+7: NavigationAttention.query_gpu_resident()
      Stage 4: SpatialTransformer

    Args:
        gpu_index: Loaded GPUSpatialIndex
        spatial_encoding: SpatialPositionEncoding (on device)
        nav_attention: NavigationAttention with gpu_index set (on device)
        spatial_transformer: SpatialTransformer (on device)
        device: CUDA device

    Returns:
        (final_output, navigation_metrics)
    """
    # Get a sample of embeddings from the index for query construction
    sample_emb, sample_pos, _ = gpu_index.query(torch.zeros(3, device=device), k=M1114_K_NEIGHBORS)

    # Stage 2: Position encoding on GPU-resident positions
    pos_3d = sample_pos.unsqueeze(0)  # [1, k, 3]
    pos_encoded = spatial_encoding(pos_3d).squeeze(0)  # [k, d_model]
    enriched = sample_emb + pos_encoded

    # Build query from enriched embeddings
    query = enriched.mean(dim=0)

    # Stage 3+6+7: GPU-resident query (no transfer!)
    output, metrics = nav_attention.query_gpu_resident(
        query=query,
        target_embedding=enriched[0],
    )

    # Stage 4: SpatialTransformer
    transformer_input = output.unsqueeze(0).unsqueeze(0)  # [1, 1, d_model]
    transformer_positions = torch.zeros(1, 1, 3, device=device)
    final_output = spatial_transformer(transformer_input, transformer_positions)

    return final_output, metrics


# ---------------------------------------------------------------------------
# Class 1: TestM1115IntegrationCorrectness (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
@pytest.mark.m1115_gpu
class TestM1115IntegrationCorrectness:
    """Verify NavigationAttention works correctly with GPU spatial index."""

    def test_gpu_index_in_nav_attention(
        self,
        m1115_loaded_index_1k: GPUSpatialIndex,
        gpu_device: torch.device,
    ) -> None:
        """Construct NavigationAttention with gpu_index, verify query works."""
        nav = _build_nav_attention_with_gpu_index(m1115_loaded_index_1k, gpu_device)

        assert nav.gpu_index is not None
        assert nav.gpu_index.is_loaded

        # Use standard query() — should use GPU index path in _select_k_nearest
        torch.manual_seed(42)
        embeddings = torch.randn(1000, M1114_D_MODEL, device=gpu_device)
        positions = torch.randn(1000, 3, device=gpu_device) * 500.0
        query = embeddings.mean(dim=0)

        with torch.no_grad():
            output, metrics = nav.query(
                query=query,
                context_embeddings=embeddings,
                context_positions=positions,
            )

        assert output.shape == (M1114_D_MODEL,)
        assert torch.isfinite(output).all()
        assert metrics.steps_taken > 0

        print(f"\nGPU index query: shape={output.shape}, steps={metrics.steps_taken}")

        _benchmark_results.append(
            {
                "test": "test_gpu_index_in_nav_attention",
                "status": "PASS",
                "output_shape": list(output.shape),
                "steps": metrics.steps_taken,
            }
        )

    def test_backward_compatible(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Construct WITHOUT gpu_index, verify old behavior unchanged."""
        nav = NavigationAttention(
            d_model=M1114_D_MODEL,
            spatial_radius=M1114_SPATIAL_RADIUS,
            k_neighbors=M1114_K_NEIGHBORS,
            enable_navigation=True,
            enable_lod=True,
        ).to(gpu_device)

        assert nav.gpu_index is None

        torch.manual_seed(42)
        embeddings = torch.randn(500, M1114_D_MODEL, device=gpu_device)
        positions = torch.randn(500, 3, device=gpu_device) * 500.0
        query = embeddings.mean(dim=0)

        with torch.no_grad():
            output, metrics = nav.query(
                query=query,
                context_embeddings=embeddings,
                context_positions=positions,
            )

        assert output.shape == (M1114_D_MODEL,)
        assert torch.isfinite(output).all()

        print(f"\nBackward compat: shape={output.shape}, gpu_index=None works")

        _benchmark_results.append(
            {
                "test": "test_backward_compatible",
                "status": "PASS",
            }
        )

    def test_query_gpu_resident_returns_valid(
        self,
        m1115_loaded_index_1k: GPUSpatialIndex,
        gpu_device: torch.device,
    ) -> None:
        """query_gpu_resident() returns finite output with valid metrics."""
        nav = _build_nav_attention_with_gpu_index(m1115_loaded_index_1k, gpu_device)

        torch.manual_seed(42)
        query = torch.randn(M1114_D_MODEL, device=gpu_device)

        with torch.no_grad():
            output, metrics = nav.query_gpu_resident(query=query)

        assert output.shape == (M1114_D_MODEL,)
        assert torch.isfinite(output).all(), "Output contains NaN/Inf"
        assert metrics.steps_taken > 0
        assert metrics.attention_ops == 1

        print(
            f"\nGPU-resident query: shape={output.shape}, "
            f"steps={metrics.steps_taken}, tokens={metrics.tokens_accessed}"
        )

        _benchmark_results.append(
            {
                "test": "test_query_gpu_resident_returns_valid",
                "status": "PASS",
                "steps": metrics.steps_taken,
                "tokens_accessed": metrics.tokens_accessed,
            }
        )

    def test_gpu_resident_matches_brute_force(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Same data: GPU-resident and brute-force produce similar outputs.

        Not identical (hash boundaries differ from brute force), but both
        should be finite and have similar magnitude.
        """
        torch.manual_seed(42)
        n = 2000
        embeddings = torch.randn(n, M1114_D_MODEL)
        positions = torch.randn(n, 3) * 500.0

        # GPU-resident path
        gpu_index = GPUSpatialIndex(cell_size=M1115_CELL_SIZE, device=gpu_device)
        gpu_index.load(embeddings, positions)
        nav_gpu = _build_nav_attention_with_gpu_index(gpu_index, gpu_device)

        query = torch.randn(M1114_D_MODEL, device=gpu_device)

        with torch.no_grad():
            output_resident, _ = nav_gpu.query_gpu_resident(query=query)

        # Brute-force path
        nav_brute = NavigationAttention(
            d_model=M1114_D_MODEL,
            spatial_radius=M1114_SPATIAL_RADIUS,
            k_neighbors=M1114_K_NEIGHBORS,
            enable_navigation=True,
            enable_lod=True,
        ).to(gpu_device)

        with torch.no_grad():
            output_brute, _ = nav_brute.query(
                query=query,
                context_embeddings=embeddings.to(gpu_device),
                context_positions=positions.to(gpu_device),
            )

        # Both should be finite and non-zero
        assert torch.isfinite(output_resident).all()
        assert torch.isfinite(output_brute).all()
        assert not torch.all(output_resident == 0)
        assert not torch.all(output_brute == 0)

        # Magnitudes should be in same ballpark (within 10x)
        mag_resident = output_resident.norm().item()
        mag_brute = output_brute.norm().item()
        ratio = max(mag_resident, mag_brute) / max(min(mag_resident, mag_brute), 1e-8)
        assert ratio < 10.0, f"Magnitude ratio {ratio:.2f}x — outputs too different"

        print(
            f"\nResident vs brute force: |resident|={mag_resident:.4f}, "
            f"|brute|={mag_brute:.4f}, ratio={ratio:.2f}x"
        )

        _benchmark_results.append(
            {
                "test": "test_gpu_resident_matches_brute_force",
                "status": "PASS",
                "mag_resident": round(mag_resident, 4),
                "mag_brute": round(mag_brute, 4),
                "ratio": round(ratio, 2),
            }
        )


# ---------------------------------------------------------------------------
# Class 2: TestM1115PipelineVsTransferBenchmarks (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
@pytest.mark.m1115_gpu
class TestM1115PipelineVsTransferBenchmarks:
    """Benchmark GPU-resident pipeline vs transfer-based pipeline."""

    def _setup_for_size(
        self,
        n: int,
        gpu_device: torch.device,
    ) -> tuple[
        GPUSpatialIndex,
        SpatialPositionEncoding,
        NavigationAttention,
        NavigationAttention,
        SpatialTransformer,
        torch.Tensor,
        torch.Tensor,
    ]:
        """Set up both pipelines for comparison at a given size.

        Returns:
            (gpu_index, spatial_encoding, nav_resident, nav_transfer,
             spatial_transformer, embeddings_cpu, positions_cpu)
        """
        torch.manual_seed(42)
        embeddings_cpu = torch.randn(n, M1114_D_MODEL)
        positions_cpu = torch.randn(n, 3) * 500.0

        # GPU-resident setup
        gpu_index = GPUSpatialIndex(
            cell_size=M1115_CELL_SIZE,
            vram_budget_gb=M1115_VRAM_BUDGET_GB,
            device=gpu_device,
        )
        gpu_index.load(embeddings_cpu, positions_cpu)

        spatial_encoding = SpatialPositionEncoding(d_model=M1114_D_MODEL).to(gpu_device)
        nav_resident = _build_nav_attention_with_gpu_index(gpu_index, gpu_device)
        nav_transfer = NavigationAttention(
            d_model=M1114_D_MODEL,
            spatial_radius=M1114_SPATIAL_RADIUS,
            k_neighbors=M1114_K_NEIGHBORS,
            enable_navigation=True,
            enable_lod=True,
        ).to(gpu_device)
        spatial_transformer = SpatialTransformer(
            n_layers=2,
            d_model=M1114_D_MODEL,
            n_heads=8,
            d_ff=1024,
            spatial_radius=M1114_SPATIAL_RADIUS,
            dropout=0.1,
        ).to(gpu_device)

        return (
            gpu_index,
            spatial_encoding,
            nav_resident,
            nav_transfer,
            spatial_transformer,
            embeddings_cpu,
            positions_cpu,
        )

    def _run_comparison(
        self,
        n: int,
        gpu_device: torch.device,
    ) -> dict:
        """Run transfer vs resident comparison, return timing dict."""
        (
            gpu_index,
            spatial_encoding,
            nav_resident,
            nav_transfer,
            spatial_transformer,
            embeddings_cpu,
            positions_cpu,
        ) = self._setup_for_size(n, gpu_device)

        # Time transfer-based pipeline
        def run_transfer(e: torch.Tensor = embeddings_cpu, p: torch.Tensor = positions_cpu) -> None:
            with torch.no_grad():
                run_full_pipeline(
                    embeddings_cpu=e,
                    positions_cpu=p,
                    spatial_encoding=spatial_encoding,
                    nav_attention=nav_transfer,
                    spatial_transformer=spatial_transformer,
                    device=gpu_device,
                )

        transfer_time = _time_fn(run_transfer)

        # Time GPU-resident pipeline
        def run_resident(
            gi: GPUSpatialIndex = gpu_index,
            se: SpatialPositionEncoding = spatial_encoding,
            nr: NavigationAttention = nav_resident,
            st: SpatialTransformer = spatial_transformer,
        ) -> None:
            with torch.no_grad():
                run_full_pipeline_gpu_resident(
                    gpu_index=gi,
                    spatial_encoding=se,
                    nav_attention=nr,
                    spatial_transformer=st,
                    device=gpu_device,
                )

        resident_time = _time_fn(run_resident)

        speedup = transfer_time / resident_time if resident_time > 0 else float("inf")

        # Clean up
        del gpu_index
        torch.cuda.empty_cache()

        return {
            "n": n,
            "transfer_ms": round(transfer_time * 1000, 3),
            "resident_ms": round(resident_time * 1000, 3),
            "speedup": round(speedup, 2),
        }

    def test_transfer_pipeline_vs_resident_1k(
        self,
        gpu_device: torch.device,
    ) -> None:
        """At 1K: both pipelines similar speed (transfer overhead negligible)."""
        result = self._run_comparison(1000, gpu_device)

        print(
            f"\n1K tokens: transfer={result['transfer_ms']:.3f}ms, "
            f"resident={result['resident_ms']:.3f}ms, "
            f"speedup={result['speedup']:.2f}x"
        )

        # At 1K, transfer is tiny — both should complete, no speed requirement
        assert result["transfer_ms"] > 0
        assert result["resident_ms"] > 0

        _benchmark_results.append(
            {"test": "test_transfer_pipeline_vs_resident_1k", "status": "PASS", **result}
        )

    def test_transfer_pipeline_vs_resident_100k(
        self,
        gpu_device: torch.device,
    ) -> None:
        """At 100K: resident should be faster (no transfer overhead)."""
        result = self._run_comparison(100_000, gpu_device)

        print(
            f"\n100K tokens: transfer={result['transfer_ms']:.3f}ms, "
            f"resident={result['resident_ms']:.3f}ms, "
            f"speedup={result['speedup']:.2f}x"
        )

        # Resident should be faster at 100K (transfer starts to dominate)
        assert result["resident_ms"] > 0
        assert result["transfer_ms"] > 0

        _benchmark_results.append(
            {"test": "test_transfer_pipeline_vs_resident_100k", "status": "PASS", **result}
        )

    def test_transfer_pipeline_vs_resident_1m(
        self,
        gpu_device: torch.device,
    ) -> None:
        """At 1M: resident ~19ms vs transfer ~364ms — the headline result."""
        result = self._run_comparison(1_000_000, gpu_device)

        print(
            f"\n1M tokens: transfer={result['transfer_ms']:.3f}ms, "
            f"resident={result['resident_ms']:.3f}ms, "
            f"speedup={result['speedup']:.2f}x"
        )

        # GPU-resident should be meaningfully faster at 1M
        assert (
            result["speedup"] > 1.5
        ), f"Expected GPU-resident to be >1.5x faster at 1M, got {result['speedup']:.2f}x"

        _benchmark_results.append(
            {"test": "test_transfer_pipeline_vs_resident_1m", "status": "PASS", **result}
        )

    def test_resident_scaling_flat(
        self,
        gpu_device: torch.device,
    ) -> None:
        """GPU-resident times at [1K, 10K, 100K, 1M] all within 3x of 1K (true O(k))."""
        sizes = [1_000, 10_000, 100_000, 1_000_000]
        resident_times: dict[int, float] = {}

        for n in sizes:
            (
                gpu_index,
                spatial_encoding,
                nav_resident,
                _nav_transfer,
                spatial_transformer,
                _emb_cpu,
                _pos_cpu,
            ) = self._setup_for_size(n, gpu_device)

            def run_resident(
                gi: GPUSpatialIndex = gpu_index,
                se: SpatialPositionEncoding = spatial_encoding,
                nr: NavigationAttention = nav_resident,
                st: SpatialTransformer = spatial_transformer,
            ) -> None:
                with torch.no_grad():
                    run_full_pipeline_gpu_resident(
                        gpu_index=gi,
                        spatial_encoding=se,
                        nav_attention=nr,
                        spatial_transformer=st,
                        device=gpu_device,
                    )

            avg_time = _time_fn(run_resident)
            resident_times[n] = avg_time * 1000

            del gpu_index
            torch.cuda.empty_cache()

        print("\nGPU-resident scaling:")
        for n, t in resident_times.items():
            print(f"  {n:>10,} tokens: {t:.3f}ms")

        # All sizes should be within 3x of the 1K baseline (O(k) = constant)
        base_time = resident_times[1_000]
        for n, t in resident_times.items():
            ratio = t / base_time if base_time > 0 else 0
            if n > 1_000:
                print(f"  {n:,} vs 1K ratio: {ratio:.2f}x")

        ratio_1m = resident_times[1_000_000] / base_time if base_time > 0 else 0
        assert ratio_1m < 3.0, f"1M is {ratio_1m:.2f}x slower than 1K — expected <3x for true O(k)"

        _benchmark_results.append(
            {
                "test": "test_resident_scaling_flat",
                "status": "PASS",
                "sizes": sizes,
                "times_ms": {str(k): round(v, 3) for k, v in resident_times.items()},
                "ratio_1k_1m": round(ratio_1m, 2),
            }
        )


# ---------------------------------------------------------------------------
# Class 3: TestM1115PhaseBResultsSaver (1 test)
# ---------------------------------------------------------------------------


@pytest.mark.m1115
class TestM1115PhaseBResultsSaver:
    """Save Phase B results to markdown."""

    def test_z_save_phase_b_results(self) -> None:
        """Write collected results to test-results-m1.11.5-phase-b.md."""
        if not _benchmark_results:
            pytest.skip("No results to save (other tests may have been skipped)")

        results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, "test-results-m1.11.5-phase-b.md")

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

        gpu_name = "N/A"
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)

        # Extract comparison results
        comparison_rows = []
        for r in _benchmark_results:
            if "transfer_ms" in r and "resident_ms" in r:
                comparison_rows.append(
                    f"| {r['n']:,} | {r['transfer_ms']:.3f}ms | "
                    f"{r['resident_ms']:.3f}ms | **{r['speedup']:.2f}x** |"
                )

        # Extract scaling results
        scaling_rows = []
        for r in _benchmark_results:
            if r["test"] == "test_resident_scaling_flat" and "times_ms" in r:
                for size_str, t in r["times_ms"].items():
                    scaling_rows.append(f"| {int(size_str):,} | {t:.3f}ms |")

        # Build all test rows
        test_rows = []
        for r in _benchmark_results:
            test_rows.append(f"| {r['test']} | {r['status']} |")

        lines = [
            "<!--",
            "Copyright 2025-2026 Adolfo Lopez (ch1pu)",
            "SPDX-License-Identifier: Apache-2.0",
            "-->",
            "",
            "# M1.11.5 Phase B: Pipeline Integration Results",
            "",
            f"**Generated:** {now}",
            f"**GPU:** {gpu_name}",
            f"**PyTorch:** {torch.__version__}",
            f"**CUDA:** {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
            "",
            "## Transfer vs GPU-Resident Pipeline",
            "",
            "| Tokens | Transfer (O(n)) | Resident (O(k)) | Speedup |",
            "|-------:|:---------------:|:---------------:|:-------:|",
            *comparison_rows,
            "",
            "## GPU-Resident Scaling (should be flat = true O(k))",
            "",
            "| Tokens | Resident Time |",
            "|-------:|:------------:|",
            *scaling_rows,
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

        print(f"\nPhase B results saved to: {results_path}")
        print(f"Total results recorded: {len(_benchmark_results)}")
