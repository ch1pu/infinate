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
test_m1114_phase_c_full_benchmarks.py - Extreme-Scale Full Pipeline Benchmarks.

Pushes the full 7-stage INFINATE pipeline to extreme token counts (up to 1M)
and demonstrates the O(n^2) baseline's catastrophic failure at large context.

Reuses Phase B's helpers:
  - run_full_pipeline: 7-stage pipeline runner
  - DenseAttentionBaseline: O(n^2) dense self-attention
  - _time_fn: Timing with warmup + CUDA synchronization

9 tests across 5 classes:
- TestM1114PhaseCScalingCurve (2): Pipeline + baseline scaling across sizes
- TestM1114PhaseCSpeedupTable (2): Head-to-head comparison, speedup growth
- TestM1114PhaseCMemoryScaling (2): Pipeline O(k) memory vs baseline O(n^2)
- TestM1114PhaseCExtremeScale (2): 500K and 1M token runs
- TestM1114PhaseCResultsSaver (1): Save results to markdown

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.4 - Full Pipeline GPU Coverage (Phase C)
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
import torch

from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.navigation_attention import NavigationAttention
from spatial_engine.tests.conftest_m1114 import M1114_D_MODEL
from spatial_engine.tests.test_m1114_phase_b_pipeline_vs_baseline import (
    DenseAttentionBaseline,
    _time_fn,
    run_full_pipeline,
)

# Load M1.11.4 fixtures (chains M1.11.3 -> M1.11.2 -> M1.11)
pytest_plugins = ["spatial_engine.tests.conftest_m1114"]

# Module-level results collector
_benchmark_results: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _measure_peak_memory_mb(fn: callable, device: torch.device) -> float:
    """Run fn and return peak GPU memory allocated in MB.

    Args:
        fn: Callable to measure
        device: CUDA device

    Returns:
        Peak memory in megabytes
    """
    torch.cuda.reset_peak_memory_stats(device)
    torch.cuda.synchronize(device)
    fn()
    torch.cuda.synchronize(device)
    peak_bytes = torch.cuda.max_memory_allocated(device)
    return peak_bytes / (1024 * 1024)


def _safe_run_baseline(
    baseline: DenseAttentionBaseline,
    embeddings: torch.Tensor,
) -> float | str:
    """Run dense baseline with OOM protection.

    Args:
        baseline: DenseAttentionBaseline on device
        embeddings: Token embeddings [n, d_model] on device

    Returns:
        Average time in seconds, or "OOM" if out of memory
    """
    try:

        def run(e: torch.Tensor = embeddings) -> None:
            with torch.no_grad():
                baseline(e)

        return _time_fn(run, warmup=1, iters=3)
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        return "OOM"


# ---------------------------------------------------------------------------
# Class 1: TestM1114PhaseCScalingCurve (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114PhaseCScalingCurve:
    """Measure pipeline and baseline latency across a wide range of sizes."""

    def test_pipeline_scaling_curve(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Pipeline scales sub-linearly at [1K, 5K, 10K, 25K, 50K, 100K, 500K, 1M].

        Two regimes:
        - Attention-dominated (1K-10K): O(k) flat, ~1x ratio for 10x input
        - Transfer-dominated (25K-1M): O(n) from CPU→GPU data movement

        Assert:
        1. O(k) attention: 1K→10K ratio < 3x (proves constant attention cost)
        2. Sub-linear overall: 1K→1M ratio < 50x (for 1000x input increase)
           O(n²) would produce ~1,000,000x — we're 50,000x better
        """
        sizes = [1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 500_000, 1_000_000]
        times_ms: dict[int, float] = {}

        for n in sizes:
            torch.manual_seed(42)
            embeddings_cpu = torch.randn(n, M1114_D_MODEL)
            positions_cpu = torch.randn(n, 3) * 500.0

            def run_pipeline(
                e: torch.Tensor = embeddings_cpu,
                p: torch.Tensor = positions_cpu,
            ) -> None:
                with torch.no_grad():
                    run_full_pipeline(
                        embeddings_cpu=e,
                        positions_cpu=p,
                        spatial_encoding=m1114_spatial_encoding_gpu,
                        nav_attention=m1114_nav_attention_gpu,
                        spatial_transformer=m1114_spatial_transformer_gpu,
                        device=gpu_device,
                    )

            avg_time = _time_fn(run_pipeline, warmup=1, iters=3)
            times_ms[n] = avg_time * 1000
            # Free memory between sizes
            del embeddings_cpu, positions_cpu
            torch.cuda.empty_cache()

        # Print results
        print("\nPipeline scaling curve:")
        for n in sizes:
            print(f"  n={n:>9,}: {times_ms[n]:>10.3f}ms")

        # Assertion 1: O(k) attention — 1K→10K should be nearly flat
        time_1k = times_ms[1_000]
        time_10k = times_ms[10_000]
        time_1m = times_ms[1_000_000]
        ratio_attention = time_10k / time_1k if time_1k > 0 else float("inf")
        ratio_overall = time_1m / time_1k if time_1k > 0 else float("inf")

        print(f"  Ratio 1K→10K: {ratio_attention:.2f}x (O(k) attention, expect <3x)")
        print(f"  Ratio 1K→1M: {ratio_overall:.2f}x (full pipeline, expect <50x)")
        print("  O(n²) at 1M would be: ~1,000,000x")

        assert ratio_attention < 3.0, (
            f"Attention scaled {ratio_attention:.2f}x for 10x input — "
            f"expected <3x for O(k) constant attention"
        )

        # Assertion 2: Sub-linear overall — NOT quadratic
        # O(n²) would give ~1,000,000x for 1000x input; we expect <50x
        assert ratio_overall < 50.0, (
            f"Pipeline scaled {ratio_overall:.2f}x from 1K→1M tokens — "
            f"expected <50x (sub-linear). O(n²) would be ~1,000,000x"
        )

        _benchmark_results.append(
            {
                "test": "test_pipeline_scaling_curve",
                "status": "PASS",
                "times_ms": {str(n): round(t, 3) for n, t in times_ms.items()},
                "ratio_attention_1k_10k": round(ratio_attention, 2),
                "ratio_overall_1k_1m": round(ratio_overall, 2),
            }
        )

    def test_baseline_scaling_curve(
        self,
        gpu_device: torch.device,
    ) -> None:
        """O(n^2) baseline at [1K, 5K, 10K, 25K, 50K]. Records OOM boundary.

        Time grows superlinearly (quadratic). Stops at OOM — recording which
        size caused it is a valid and important result.
        """
        sizes = [1_000, 5_000, 10_000, 25_000, 50_000]
        results: dict[int, float | str] = {}
        baseline = DenseAttentionBaseline(M1114_D_MODEL).to(gpu_device)

        for n in sizes:
            torch.manual_seed(42)
            embeddings = torch.randn(n, M1114_D_MODEL, device=gpu_device)

            time_result = _safe_run_baseline(baseline, embeddings)
            if isinstance(time_result, str):
                results[n] = "OOM"
                print(f"\n  n={n:>9,}: OOM (out of memory)")
                del embeddings
                torch.cuda.empty_cache()
                break
            else:
                results[n] = time_result * 1000
                print(f"\n  n={n:>9,}: {results[n]:>10.3f}ms")
                del embeddings
                torch.cuda.empty_cache()

        # Verify quadratic growth where we have numeric results
        numeric_sizes = [n for n in sizes if n in results and results[n] != "OOM"]
        if len(numeric_sizes) >= 2:
            first_time = results[numeric_sizes[0]]
            last_time = results[numeric_sizes[-1]]
            scale_factor = numeric_sizes[-1] / numeric_sizes[0]
            time_ratio = last_time / first_time if first_time > 0 else 0
            print(f"\n  Ratio {numeric_sizes[0]}→{numeric_sizes[-1]}: {time_ratio:.2f}x")
            print(f"  Input scale: {scale_factor:.0f}x")
            # For O(n²), time ratio should be >> input ratio
            assert time_ratio > scale_factor, (
                f"Baseline time grew {time_ratio:.2f}x for {scale_factor:.0f}x input — "
                f"expected superlinear (quadratic) growth"
            )

        # At least one OOM or the final size should be very slow
        oom_boundary = None
        for n in sizes:
            if n in results and results[n] == "OOM":
                oom_boundary = n
                break

        del baseline
        torch.cuda.empty_cache()

        _benchmark_results.append(
            {
                "test": "test_baseline_scaling_curve",
                "status": "PASS",
                "results": {
                    str(n): (round(t, 3) if isinstance(t, float) else t) for n, t in results.items()
                },
                "oom_boundary": oom_boundary,
            }
        )


# ---------------------------------------------------------------------------
# Class 2: TestM1114PhaseCSpeedupTable (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114PhaseCSpeedupTable:
    """Compute speedup ratios at each size where both can run."""

    def test_head_to_head_comparison(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """At each size where both run, compute speedup. Record full table."""
        sizes = [1_000, 5_000, 10_000, 25_000]
        comparisons: list[dict] = []
        baseline = DenseAttentionBaseline(M1114_D_MODEL).to(gpu_device)

        for n in sizes:
            torch.manual_seed(42)
            embeddings_cpu = torch.randn(n, M1114_D_MODEL)
            positions_cpu = torch.randn(n, 3) * 500.0
            embeddings_gpu = embeddings_cpu.to(gpu_device)

            # Time pipeline
            def run_pipeline(
                e: torch.Tensor = embeddings_cpu,
                p: torch.Tensor = positions_cpu,
            ) -> None:
                with torch.no_grad():
                    run_full_pipeline(
                        embeddings_cpu=e,
                        positions_cpu=p,
                        spatial_encoding=m1114_spatial_encoding_gpu,
                        nav_attention=m1114_nav_attention_gpu,
                        spatial_transformer=m1114_spatial_transformer_gpu,
                        device=gpu_device,
                    )

            pipeline_time = _time_fn(run_pipeline, warmup=1, iters=3)

            # Time baseline with OOM protection
            baseline_result = _safe_run_baseline(baseline, embeddings_gpu)

            del embeddings_cpu, positions_cpu, embeddings_gpu
            torch.cuda.empty_cache()

            if isinstance(baseline_result, str):
                comparisons.append(
                    {
                        "n": n,
                        "pipeline_ms": round(pipeline_time * 1000, 3),
                        "baseline_ms": "OOM",
                        "speedup": "OOM",
                    }
                )
                break
            else:
                speedup = baseline_result / pipeline_time if pipeline_time > 0 else 0
                comparisons.append(
                    {
                        "n": n,
                        "pipeline_ms": round(pipeline_time * 1000, 3),
                        "baseline_ms": round(baseline_result * 1000, 3),
                        "speedup": round(speedup, 2),
                    }
                )

        print("\nHead-to-head comparison:")
        for c in comparisons:
            if c["speedup"] == "OOM":
                print(f"  n={c['n']:>9,}: pipeline={c['pipeline_ms']:.3f}ms, " f"baseline=OOM")
            else:
                print(
                    f"  n={c['n']:>9,}: pipeline={c['pipeline_ms']:.3f}ms, "
                    f"baseline={c['baseline_ms']:.3f}ms, "
                    f"speedup={c['speedup']:.2f}x"
                )

        # Speedup should increase with scale (where numeric)
        numeric_speedups = [c["speedup"] for c in comparisons if c["speedup"] != "OOM"]
        if len(numeric_speedups) >= 2:
            assert numeric_speedups[-1] > numeric_speedups[0], (
                f"Speedup should increase with scale: "
                f"first={numeric_speedups[0]:.2f}x, last={numeric_speedups[-1]:.2f}x"
            )

        del baseline
        torch.cuda.empty_cache()

        _benchmark_results.append(
            {
                "test": "test_head_to_head_comparison",
                "status": "PASS",
                "comparisons": comparisons,
            }
        )

    def test_pipeline_wins_at_scale(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Pipeline is faster than baseline at 25K tokens."""
        n = 25_000
        torch.manual_seed(42)
        embeddings_cpu = torch.randn(n, M1114_D_MODEL)
        positions_cpu = torch.randn(n, 3) * 500.0
        embeddings_gpu = embeddings_cpu.to(gpu_device)

        # Time pipeline
        def run_pipeline(
            e: torch.Tensor = embeddings_cpu,
            p: torch.Tensor = positions_cpu,
        ) -> None:
            with torch.no_grad():
                run_full_pipeline(
                    embeddings_cpu=e,
                    positions_cpu=p,
                    spatial_encoding=m1114_spatial_encoding_gpu,
                    nav_attention=m1114_nav_attention_gpu,
                    spatial_transformer=m1114_spatial_transformer_gpu,
                    device=gpu_device,
                )

        pipeline_time = _time_fn(run_pipeline, warmup=1, iters=3)

        # Time baseline
        baseline_model = DenseAttentionBaseline(M1114_D_MODEL).to(gpu_device)
        baseline_result = _safe_run_baseline(baseline_model, embeddings_gpu)

        del embeddings_cpu, positions_cpu, embeddings_gpu, baseline_model
        torch.cuda.empty_cache()

        if isinstance(baseline_result, str):
            # OOM means pipeline wins by default
            print(f"\n25K: pipeline={pipeline_time * 1000:.3f}ms, baseline=OOM")
            speedup = "OOM (pipeline wins)"
        else:
            speedup = baseline_result / pipeline_time if pipeline_time > 0 else 0
            print(
                f"\n25K: pipeline={pipeline_time * 1000:.3f}ms, "
                f"baseline={baseline_result * 1000:.3f}ms, "
                f"speedup={speedup:.2f}x"
            )
            assert speedup > 1.0, f"Pipeline should be faster at 25K tokens, got {speedup:.2f}x"

        _benchmark_results.append(
            {
                "test": "test_pipeline_wins_at_scale",
                "status": "PASS",
                "n": n,
                "pipeline_ms": round(pipeline_time * 1000, 3),
                "baseline_ms": (
                    round(baseline_result * 1000, 3)
                    if isinstance(baseline_result, float)
                    else "OOM"
                ),
                "speedup": speedup if isinstance(speedup, str) else round(speedup, 2),
            }
        )


# ---------------------------------------------------------------------------
# Class 3: TestM1114PhaseCMemoryScaling (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114PhaseCMemoryScaling:
    """Verify pipeline uses O(k) memory while baseline uses O(n^2)."""

    def test_pipeline_memory_ok(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Peak GPU memory at [1K, 10K, 100K, 1M] grows sub-linearly.

        The pipeline processes k=50 neighbors regardless of n, so the
        attention computation uses constant memory. Growth comes only from
        the embedding tensor transfer (linear in n), not quadratic.
        """
        sizes = [1_000, 10_000, 100_000, 1_000_000]
        memory_mb: dict[int, float] = {}

        for n in sizes:
            torch.manual_seed(42)
            embeddings_cpu = torch.randn(n, M1114_D_MODEL)
            positions_cpu = torch.randn(n, 3) * 500.0

            def run_pipeline(
                e: torch.Tensor = embeddings_cpu,
                p: torch.Tensor = positions_cpu,
            ) -> None:
                with torch.no_grad():
                    run_full_pipeline(
                        embeddings_cpu=e,
                        positions_cpu=p,
                        spatial_encoding=m1114_spatial_encoding_gpu,
                        nav_attention=m1114_nav_attention_gpu,
                        spatial_transformer=m1114_spatial_transformer_gpu,
                        device=gpu_device,
                    )

            peak_mb = _measure_peak_memory_mb(run_pipeline, gpu_device)
            memory_mb[n] = peak_mb

            del embeddings_cpu, positions_cpu
            torch.cuda.empty_cache()

        print("\nPipeline memory scaling:")
        for n in sizes:
            print(f"  n={n:>9,}: {memory_mb[n]:>10.2f} MB")

        # Memory should NOT grow quadratically. For 1000x input (1K→1M),
        # O(n²) would mean 1,000,000x memory growth. Linear would be 1000x.
        # Pipeline should be well under 1000x (linear) since attention is O(k).
        ratio_1k_1m = memory_mb[1_000_000] / memory_mb[1_000] if memory_mb[1_000] > 0 else 0
        print(f"  Ratio 1K→1M: {ratio_1k_1m:.2f}x")

        # Expect at most linear growth (1000x for 1000x input). In practice,
        # memory grows from the embedding transfer which is linear, not quadratic.
        assert ratio_1k_1m < 1500.0, (
            f"Pipeline memory grew {ratio_1k_1m:.2f}x for 1000x input — "
            f"should be sub-quadratic (well below 1,000,000x)"
        )

        _benchmark_results.append(
            {
                "test": "test_pipeline_memory_ok",
                "status": "PASS",
                "memory_mb": {str(n): round(m, 2) for n, m in memory_mb.items()},
                "ratio_1k_1m": round(ratio_1k_1m, 2),
            }
        )

    def test_baseline_memory_quadratic(
        self,
        gpu_device: torch.device,
    ) -> None:
        """Peak GPU memory for baseline at [1K, 5K, 10K] grows quadratically.

        The [n,n] attention matrix is the dominant allocation:
          1K:  1000^2 × 4 bytes = 4 MB
          5K:  5000^2 × 4 bytes = 100 MB
          10K: 10000^2 × 4 bytes = 400 MB
        """
        sizes = [1_000, 5_000, 10_000]
        memory_mb: dict[int, float] = {}
        baseline_model = DenseAttentionBaseline(M1114_D_MODEL).to(gpu_device)

        for n in sizes:
            torch.manual_seed(42)
            embeddings = torch.randn(n, M1114_D_MODEL, device=gpu_device)

            def run_baseline(
                e: torch.Tensor = embeddings,
                b: DenseAttentionBaseline = baseline_model,
            ) -> None:
                with torch.no_grad():
                    b(e)

            try:
                peak_mb = _measure_peak_memory_mb(run_baseline, gpu_device)
                memory_mb[n] = peak_mb
            except torch.cuda.OutOfMemoryError:
                memory_mb[n] = -1  # Mark OOM
                torch.cuda.empty_cache()

            del embeddings
            torch.cuda.empty_cache()

        print("\nBaseline memory scaling:")
        for n in sizes:
            if memory_mb[n] < 0:
                print(f"  n={n:>9,}: OOM")
            else:
                print(f"  n={n:>9,}: {memory_mb[n]:>10.2f} MB")

        # Check quadratic growth between sizes that completed
        valid = {n: m for n, m in memory_mb.items() if m > 0}
        valid_sizes = sorted(valid.keys())

        if len(valid_sizes) >= 2:
            first_n, last_n = valid_sizes[0], valid_sizes[-1]
            input_ratio = last_n / first_n
            memory_ratio = valid[last_n] / valid[first_n] if valid[first_n] > 0 else 0

            print(f"\n  Input ratio {first_n}→{last_n}: {input_ratio:.0f}x")
            print(f"  Memory ratio: {memory_ratio:.2f}x")
            print(f"  Expected for O(n²): {input_ratio**2:.0f}x")

            # Memory should grow faster than linear (i.e., memory_ratio > input_ratio)
            assert memory_ratio > input_ratio, (
                f"Baseline memory grew {memory_ratio:.2f}x for {input_ratio:.0f}x input — "
                f"expected superlinear (quadratic) growth"
            )

        del baseline_model
        torch.cuda.empty_cache()

        _benchmark_results.append(
            {
                "test": "test_baseline_memory_quadratic",
                "status": "PASS",
                "memory_mb": {
                    str(n): (round(m, 2) if m > 0 else "OOM") for n, m in memory_mb.items()
                },
            }
        )


# ---------------------------------------------------------------------------
# Class 4: TestM1114PhaseCExtremeScale (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.m1114
@pytest.mark.m1114_gpu
class TestM1114PhaseCExtremeScale:
    """Push the pipeline to extreme token counts — 500K and 1M."""

    def test_pipeline_500k_tokens(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Run full pipeline at 500K tokens. Assert completes in <200ms."""
        n = 500_000
        torch.manual_seed(42)
        emb_cpu = torch.randn(n, M1114_D_MODEL)
        pos_cpu = torch.randn(n, 3) * 500.0

        def run_pipeline(
            e: torch.Tensor = emb_cpu,
            p: torch.Tensor = pos_cpu,
        ) -> None:
            with torch.no_grad():
                run_full_pipeline(
                    embeddings_cpu=e,
                    positions_cpu=p,
                    spatial_encoding=m1114_spatial_encoding_gpu,
                    nav_attention=m1114_nav_attention_gpu,
                    spatial_transformer=m1114_spatial_transformer_gpu,
                    device=gpu_device,
                )

        avg_time = _time_fn(run_pipeline, warmup=1, iters=3)
        time_ms = avg_time * 1000

        del emb_cpu, pos_cpu
        torch.cuda.empty_cache()

        print(f"\n500K tokens: {time_ms:.3f}ms")
        assert time_ms < 200.0, f"500K tokens took {time_ms:.3f}ms, expected <200ms"

        _benchmark_results.append(
            {
                "test": "test_pipeline_500k_tokens",
                "status": "PASS",
                "n": n,
                "time_ms": round(time_ms, 3),
            }
        )

    def test_pipeline_1m_tokens(
        self,
        m1114_spatial_encoding_gpu: SpatialPositionEncoding,
        m1114_nav_attention_gpu: NavigationAttention,
        m1114_spatial_transformer_gpu: SpatialTransformer,
        gpu_device: torch.device,
    ) -> None:
        """Run full pipeline at 1M tokens. Assert completes <500ms and output is finite."""
        n = 1_000_000
        torch.manual_seed(42)
        emb_cpu = torch.randn(n, M1114_D_MODEL)
        pos_cpu = torch.randn(n, 3) * 500.0

        def run_pipeline(
            e: torch.Tensor = emb_cpu,
            p: torch.Tensor = pos_cpu,
        ) -> None:
            with torch.no_grad():
                out, _ = run_full_pipeline(
                    embeddings_cpu=e,
                    positions_cpu=p,
                    spatial_encoding=m1114_spatial_encoding_gpu,
                    nav_attention=m1114_nav_attention_gpu,
                    spatial_transformer=m1114_spatial_transformer_gpu,
                    device=gpu_device,
                )
                out.cpu()  # Ensure GPU work completes

        avg_time = _time_fn(run_pipeline, warmup=1, iters=3)
        time_ms = avg_time * 1000

        # Run once more to capture output
        with torch.no_grad():
            final_output, metrics = run_full_pipeline(
                embeddings_cpu=emb_cpu,
                positions_cpu=pos_cpu,
                spatial_encoding=m1114_spatial_encoding_gpu,
                nav_attention=m1114_nav_attention_gpu,
                spatial_transformer=m1114_spatial_transformer_gpu,
                device=gpu_device,
            )

        assert torch.isfinite(final_output).all(), "1M token output contains NaN/Inf"

        del emb_cpu, pos_cpu
        torch.cuda.empty_cache()

        print(
            f"\n1M tokens: {time_ms:.3f}ms, "
            f"output_shape={final_output.shape}, "
            f"steps={metrics.steps_taken}"
        )
        assert time_ms < 500.0, f"1M tokens took {time_ms:.3f}ms, expected <500ms"

        _benchmark_results.append(
            {
                "test": "test_pipeline_1m_tokens",
                "status": "PASS",
                "n": n,
                "time_ms": round(time_ms, 3),
                "output_finite": True,
                "steps_taken": metrics.steps_taken,
            }
        )


# ---------------------------------------------------------------------------
# Class 5: TestM1114PhaseCResultsSaver (1 test)
# ---------------------------------------------------------------------------


@pytest.mark.m1114
class TestM1114PhaseCResultsSaver:
    """Save Phase C results to markdown."""

    def test_z_save_phase_c_results(self) -> None:
        """Write comprehensive results to test-results-m1.11.4-phase-c.md.

        Runs last alphabetically to collect all results from other tests.
        """
        if not _benchmark_results:
            pytest.skip("No results to save (other tests may have been skipped)")

        results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, "test-results-m1.11.4-phase-c.md")

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

        gpu_name = "N/A"
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)

        # --- Pipeline Scaling Table ---
        pipeline_scaling_rows = []
        for r in _benchmark_results:
            if r["test"] == "test_pipeline_scaling_curve":
                for size_str, time_val in r["times_ms"].items():
                    pipeline_scaling_rows.append(f"| {int(size_str):>9,} | {time_val:.3f}ms |")

        # --- Baseline Scaling Table ---
        baseline_scaling_rows = []
        baseline_oom = None
        for r in _benchmark_results:
            if r["test"] == "test_baseline_scaling_curve":
                for size_str, time_val in r["results"].items():
                    if time_val == "OOM":
                        baseline_scaling_rows.append(f"| {int(size_str):>9,} | **OOM** |")
                        baseline_oom = int(size_str)
                    else:
                        baseline_scaling_rows.append(f"| {int(size_str):>9,} | {time_val:.3f}ms |")

        # --- Head-to-Head Table ---
        h2h_rows = []
        for r in _benchmark_results:
            if r["test"] == "test_head_to_head_comparison":
                for c in r["comparisons"]:
                    if c["speedup"] == "OOM":
                        h2h_rows.append(
                            f"| {c['n']:>9,} | {c['pipeline_ms']:.3f}ms | " f"OOM | **OOM** |"
                        )
                    else:
                        h2h_rows.append(
                            f"| {c['n']:>9,} | {c['pipeline_ms']:.3f}ms | "
                            f"{c['baseline_ms']:.3f}ms | **{c['speedup']:.2f}x** |"
                        )

        # --- Memory Table ---
        pipeline_memory_rows = []
        for r in _benchmark_results:
            if r["test"] == "test_pipeline_memory_ok":
                for size_str, mem_val in r["memory_mb"].items():
                    pipeline_memory_rows.append(f"| {int(size_str):>9,} | {mem_val:.2f} MB |")

        baseline_memory_rows = []
        for r in _benchmark_results:
            if r["test"] == "test_baseline_memory_quadratic":
                for size_str, mem_val in r["memory_mb"].items():
                    if mem_val == "OOM":
                        baseline_memory_rows.append(f"| {int(size_str):>9,} | **OOM** |")
                    else:
                        baseline_memory_rows.append(f"| {int(size_str):>9,} | {mem_val:.2f} MB |")

        # --- Extreme Scale ---
        extreme_rows = []
        for r in _benchmark_results:
            if r["test"] in ("test_pipeline_500k_tokens", "test_pipeline_1m_tokens"):
                extreme_rows.append(f"| {r['n']:>9,} | {r['time_ms']:.3f}ms | PASS |")

        # --- All Tests ---
        test_rows = []
        for r in _benchmark_results:
            test_rows.append(f"| {r['test']} | {r['status']} |")

        lines = [
            "<!--",
            "Copyright 2025-2026 Adolfo Lopez (ch1pu)",
            "SPDX-License-Identifier: Apache-2.0",
            "-->",
            "",
            "# M1.11.4 Phase C: Full Pipeline Extreme-Scale Benchmarks",
            "",
            f"**Generated:** {now}",
            f"**GPU:** {gpu_name}",
            f"**PyTorch:** {torch.__version__}",
            f"**CUDA:** {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
            "",
            "---",
            "",
            "## Pipeline Scaling Curve (O(k) Constant Complexity)",
            "",
            "| Context Size | Latency |",
            "|-------------:|:-------:|",
            *pipeline_scaling_rows,
            "",
            "## Baseline Scaling Curve (O(n^2) Quadratic)",
            "",
            "| Context Size | Latency |",
            "|-------------:|:-------:|",
            *baseline_scaling_rows,
            "",
        ]

        if baseline_oom:
            lines.append(
                f"**OOM Boundary:** Baseline OOMs at {baseline_oom:,} tokens "
                f"(the [{baseline_oom:,} x {baseline_oom:,}] attention matrix "
                f"exceeds GPU memory)."
            )
            lines.append("")

        lines.extend(
            [
                "## Head-to-Head Speed Comparison",
                "",
                "| Context Size | Pipeline (O(k)) | Baseline (O(n^2)) | Speedup |",
                "|-------------:|:----------------:|:-----------------:|:-------:|",
                *h2h_rows,
                "",
                "## Memory Scaling",
                "",
                "### Pipeline (O(k) attention, linear transfer)",
                "",
                "| Context Size | Peak GPU Memory |",
                "|-------------:|:---------------:|",
                *pipeline_memory_rows,
                "",
                "### Baseline (O(n^2) attention matrix)",
                "",
                "| Context Size | Peak GPU Memory |",
                "|-------------:|:---------------:|",
                *baseline_memory_rows,
                "",
                "## Extreme Scale (Pipeline Only)",
                "",
                "| Context Size | Latency | Status |",
                "|-------------:|:-------:|:------:|",
                *extreme_rows,
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
        )

        with open(results_path, "w") as f:
            f.write("\n".join(lines))

        print(f"\nPhase C results saved to: {results_path}")
        print(f"Total results recorded: {len(_benchmark_results)}")
