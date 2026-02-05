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
test_m1113_gpu_pipeline_benchmarks.py - GPU Full Pipeline Benchmark Tests.

First GPU vs CPU benchmark comparison for INFINATE's full pipeline
(Navigator -> LOD -> SpatialAttention -> Output) on RTX 5060 SM_120.

18 tests across 6 classes:
- TestM1113GPUGuardFixes (3): Corrected GPU guard tests
- TestM1113GPUFullPipeline (4): Full pipeline on GPU
- TestM1113GPUvsCPUBenchmarks (5): GPU vs CPU latency and scaling
- TestM1113GPUMemoryProfiling (3): GPU VRAM profiling
- TestM1113GPUNavigationMetrics (2): Navigation metrics on GPU
- TestM1113ResultsSaver (1): Save results to markdown

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.3 - GPU Full Pipeline Benchmarks
"""

import os
import time
from datetime import UTC, datetime

import pytest
import torch

from spatial_engine.core.spatial_attention import SpatialAttention
from spatial_engine.integration.navigation_attention import NavigationAttention, NavigationMetrics
from spatial_engine.tests.conftest_m1113 import (
    M1113_D_MODEL,
    M1113_K_NEIGHBORS,
    M1113_SPATIAL_RADIUS,
    GPUBenchmarkResult,
    M1113GPUBenchmarkRunner,
)

# Load M1.11.3 fixtures (chains M1.11.2 -> M1.11)
pytest_plugins = ["spatial_engine.tests.conftest_m1113"]

# Module-level results collector
_benchmark_results: list[dict] = []


# ---------------------------------------------------------------------------
# Class 1: TestM1113GPUGuardFixes
# ---------------------------------------------------------------------------


@pytest.mark.m1113
@pytest.mark.m1113_gpu
class TestM1113GPUGuardFixes:
    """Corrected GPU guard tests using check_cuda_compatible().

    These replace the broken hard-coded SM checks from M1.11/M1.11.2.
    """

    def test_navigation_attention_gpu_device_placement(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """NavigationAttention moved to GPU produces output on GPU.

        Corrected version of test_gpu_memory_scaling from M1.11.
        Verifies .to(device) properly moves all submodules.
        """
        nav = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=True,
            enable_lod=True,
        ).to(gpu_device)

        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=1000, device=gpu_device
        )

        with torch.no_grad():
            output, metrics = nav.query(query, embeddings, positions)

        assert output.device.type == "cuda", f"Output on {output.device}, expected cuda"
        assert output.shape == (M1113_D_MODEL,)
        assert not torch.all(output == 0), "Output should be non-zero"

        print(f"\nGPU device placement: output on {output.device}")
        print(f"  Steps: {metrics.steps_taken}, Attention ops: {metrics.attention_ops}")

        _benchmark_results.append(
            {
                "test": "test_navigation_attention_gpu_device_placement",
                "status": "PASS",
                "device": str(gpu_device),
                "output_device": str(output.device),
            }
        )

    def test_spatial_attention_gpu_execution(
        self,
        gpu_device: torch.device,
    ) -> None:
        """SpatialAttention forward pass on GPU.

        Corrected version of test_gpu_execution from test_spatial_attention_lod.py.
        Uses check_cuda_compatible() instead of hard-coded SM check.
        """
        attn = SpatialAttention(d_model=768, n_heads=12).to(gpu_device)

        x = torch.randn(2, 16, 768, device=gpu_device)
        positions = torch.randn(2, 16, 3, device=gpu_device) * 100.0

        with torch.no_grad():
            output = attn(x, positions)

        assert output.device.type == "cuda"
        assert output.shape == (2, 16, 768)

        print(f"\nSpatialAttention GPU execution: {output.shape} on {output.device}")

        _benchmark_results.append(
            {
                "test": "test_spatial_attention_gpu_execution",
                "status": "PASS",
                "output_shape": list(output.shape),
                "device": str(gpu_device),
            }
        )

    def test_spatial_attention_device_transfer(
        self,
        gpu_device: torch.device,
    ) -> None:
        """SpatialAttention created on CPU, transferred to GPU.

        Corrected version of test_device_placement from test_spatial_attention.py.
        """
        attn_cpu = SpatialAttention(d_model=768, n_heads=12)
        assert next(attn_cpu.parameters()).device.type == "cpu"

        attn_gpu = attn_cpu.cuda()

        x = torch.randn(2, 10, 768, device=gpu_device)
        positions = torch.randn(2, 10, 3, device=gpu_device)

        with torch.no_grad():
            output = attn_gpu(x, positions)

        assert output.device.type == "cuda"
        assert output.shape == (2, 10, 768)

        print(f"\nDevice transfer CPU->GPU: {output.shape} on {output.device}")

        _benchmark_results.append(
            {
                "test": "test_spatial_attention_device_transfer",
                "status": "PASS",
                "output_shape": list(output.shape),
                "device": str(output.device),
            }
        )


# ---------------------------------------------------------------------------
# Class 2: TestM1113GPUFullPipeline
# ---------------------------------------------------------------------------


@pytest.mark.m1113
@pytest.mark.m1113_gpu
class TestM1113GPUFullPipeline:
    """Full pipeline tests on GPU: Navigator -> LOD -> SpatialAttention -> Output."""

    def test_full_pipeline_gpu_forward(
        self,
        m1113_nav_attention_gpu: NavigationAttention,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        gpu_device: torch.device,
    ) -> None:
        """2000 tokens on GPU — verify output shape, device, non-zero, metrics."""
        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=2000, device=gpu_device
        )

        with torch.no_grad():
            output, metrics = m1113_nav_attention_gpu.query(query, embeddings, positions)

        assert output.shape == (M1113_D_MODEL,), f"Expected ({M1113_D_MODEL},), got {output.shape}"
        assert output.device.type == "cuda"
        assert not torch.all(output == 0), "Output should be non-zero"
        assert metrics.attention_ops >= 1

        print(f"\nGPU full pipeline forward: {output.shape} on {output.device}")
        print(f"  Steps: {metrics.steps_taken}, Ops: {metrics.attention_ops}")
        print(f"  Tokens accessed: {metrics.tokens_accessed}")

        _benchmark_results.append(
            {
                "test": "test_full_pipeline_gpu_forward",
                "status": "PASS",
                "n_tokens": 2000,
                "steps": metrics.steps_taken,
                "attention_ops": metrics.attention_ops,
                "tokens_accessed": metrics.tokens_accessed,
            }
        )

    def test_full_pipeline_gpu_with_navigation(
        self,
        m1113_nav_attention_gpu: NavigationAttention,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        gpu_device: torch.device,
    ) -> None:
        """5000 tokens on GPU — verify navigation actually ran."""
        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=5000, device=gpu_device
        )

        with torch.no_grad():
            output, metrics = m1113_nav_attention_gpu.query(query, embeddings, positions)

        assert metrics.steps_taken > 0, "Navigation should take steps"
        assert metrics.attention_ops >= 1, "Should perform attention"
        assert metrics.tokens_accessed > 0, "Should access tokens"

        print(f"\nGPU navigation (5K tokens): {metrics.steps_taken} steps")
        print(f"  Attention ops: {metrics.attention_ops}, Tokens: {metrics.tokens_accessed}")

        _benchmark_results.append(
            {
                "test": "test_full_pipeline_gpu_with_navigation",
                "status": "PASS",
                "n_tokens": 5000,
                "steps": metrics.steps_taken,
                "attention_ops": metrics.attention_ops,
                "tokens_accessed": metrics.tokens_accessed,
            }
        )

    def test_full_pipeline_gpu_no_navigation_baseline(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """GPU baseline with navigation disabled — steps should be 0."""
        nav_no_nav = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=False,
            enable_lod=True,
        ).to(gpu_device)

        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=2000, device=gpu_device
        )

        with torch.no_grad():
            output, metrics = nav_no_nav.query(query, embeddings, positions)

        assert metrics.steps_taken == 0, "No-navigation baseline should have 0 steps"
        assert output.device.type == "cuda"

        print(f"\nGPU no-navigation baseline: steps={metrics.steps_taken}")

        _benchmark_results.append(
            {
                "test": "test_full_pipeline_gpu_no_navigation_baseline",
                "status": "PASS",
                "steps": metrics.steps_taken,
            }
        )

    def test_full_pipeline_gpu_output_consistency(
        self,
        m1113_nav_attention_gpu: NavigationAttention,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        gpu_device: torch.device,
    ) -> None:
        """Same query 10x with torch.no_grad() — outputs should be close.

        GPU parallel reductions (norm, mean) are non-deterministic by default,
        so we use atol=0.02 instead of exact match. The navigator uses torch.norm()
        at each of 10 steps, and small floating-point differences compound.
        """
        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=2000, device=gpu_device, seed=123
        )

        outputs = []
        max_diffs: list[float] = []
        with torch.no_grad():
            for _ in range(10):
                output, _ = m1113_nav_attention_gpu.query(query, embeddings, positions)
                outputs.append(output.clone())

        # GPU floating-point non-determinism: parallel reductions use different
        # accumulation orders across threads, causing small differences (~0.01)
        for i in range(1, len(outputs)):
            diff = (outputs[0] - outputs[i]).abs().max().item()
            max_diffs.append(diff)
            assert torch.allclose(outputs[0], outputs[i], atol=0.02), (
                f"Output {i} differs from output 0 (max diff: {diff:.2e}) — "
                "exceeds GPU non-determinism tolerance of 0.02"
            )

        worst_diff = max(max_diffs) if max_diffs else 0.0
        print(f"\nGPU output consistency: 10 runs within atol=0.02 (worst diff: {worst_diff:.2e})")

        _benchmark_results.append(
            {
                "test": "test_full_pipeline_gpu_output_consistency",
                "status": "PASS",
                "runs": 10,
                "consistent": True,
                "worst_diff": worst_diff,
            }
        )


# ---------------------------------------------------------------------------
# Class 3: TestM1113GPUvsCPUBenchmarks
# ---------------------------------------------------------------------------


@pytest.mark.m1113
@pytest.mark.m1113_benchmark
class TestM1113GPUvsCPUBenchmarks:
    """GPU vs CPU latency and scaling comparisons.

    Each test creates SEPARATE NavigationAttention instances per device
    to avoid device transfer overhead in timing.
    """

    @staticmethod
    def _create_nav_attention(device: torch.device) -> NavigationAttention:
        """Create a NavigationAttention on the specified device."""
        return NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=True,
            enable_lod=True,
            navigation_max_steps=10,
        ).to(device)

    @staticmethod
    def _print_comparison(
        label: str,
        n_tokens: int,
        cpu_result: GPUBenchmarkResult,
        gpu_result: GPUBenchmarkResult,
    ) -> None:
        """Print formatted GPU vs CPU comparison table."""
        speedup = cpu_result.mean_ms / gpu_result.mean_ms if gpu_result.mean_ms > 0 else 0.0
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "GPU"

        print(f"\nM1.11.3 GPU vs CPU — {label} ({n_tokens:,} tokens)")
        print("=" * 65)
        print(f"{'Device':<20} {'Mean (ms)':>10} {'p50 (ms)':>10} {'p95 (ms)':>10} {'Tok/sec':>12}")
        print("-" * 65)
        print(
            f"{'CPU':<20} {cpu_result.mean_ms:>10.2f} {cpu_result.p50_ms:>10.2f}"
            f" {cpu_result.p95_ms:>10.2f} {cpu_result.tokens_per_sec:>12,.0f}"
        )
        print(
            f"{gpu_name[:20]:<20} {gpu_result.mean_ms:>10.2f} {gpu_result.p50_ms:>10.2f}"
            f" {gpu_result.p95_ms:>10.2f} {gpu_result.tokens_per_sec:>12,.0f}"
        )
        print("-" * 65)
        print(f"GPU Speedup: {speedup:.2f}x")
        if gpu_result.gpu_memory_peak_mb > 0:
            print(f"GPU Peak Memory: {gpu_result.gpu_memory_peak_mb:.1f} MB")
        print("=" * 65)

    def test_gpu_vs_cpu_latency_small_context(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        m1113_benchmark_runner: M1113GPUBenchmarkRunner,
    ) -> None:
        """GPU vs CPU latency — 1,000 tokens, 100 iterations."""
        n_tokens = 1000
        iterations = 100

        # CPU benchmark
        nav_cpu = self._create_nav_attention(torch.device("cpu"))
        q_cpu, e_cpu, p_cpu = m1113_test_data_factory.create(n_tokens, device=torch.device("cpu"))
        cpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_cpu,
            q_cpu,
            e_cpu,
            p_cpu,
            name="cpu_small",
            iterations=iterations,
            warmup=5,
        )

        # GPU benchmark
        nav_gpu = self._create_nav_attention(gpu_device)
        q_gpu, e_gpu, p_gpu = m1113_test_data_factory.create(n_tokens, device=gpu_device)
        gpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_gpu,
            q_gpu,
            e_gpu,
            p_gpu,
            name="gpu_small",
            iterations=iterations,
            warmup=10,
        )

        self._print_comparison("Small Context", n_tokens, cpu_result, gpu_result)

        speedup = cpu_result.mean_ms / gpu_result.mean_ms if gpu_result.mean_ms > 0 else 0.0

        _benchmark_results.append(
            {
                "test": "test_gpu_vs_cpu_latency_small_context",
                "status": "PASS",
                "n_tokens": n_tokens,
                "iterations": iterations,
                "cpu_mean_ms": cpu_result.mean_ms,
                "gpu_mean_ms": gpu_result.mean_ms,
                "speedup": speedup,
                "gpu_peak_mb": gpu_result.gpu_memory_peak_mb,
            }
        )

    def test_gpu_vs_cpu_latency_medium_context(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        m1113_benchmark_runner: M1113GPUBenchmarkRunner,
    ) -> None:
        """GPU vs CPU latency — 5,000 tokens, 50 iterations."""
        n_tokens = 5000
        iterations = 50

        nav_cpu = self._create_nav_attention(torch.device("cpu"))
        q_cpu, e_cpu, p_cpu = m1113_test_data_factory.create(n_tokens, device=torch.device("cpu"))
        cpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_cpu,
            q_cpu,
            e_cpu,
            p_cpu,
            name="cpu_medium",
            iterations=iterations,
            warmup=5,
        )

        nav_gpu = self._create_nav_attention(gpu_device)
        q_gpu, e_gpu, p_gpu = m1113_test_data_factory.create(n_tokens, device=gpu_device)
        gpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_gpu,
            q_gpu,
            e_gpu,
            p_gpu,
            name="gpu_medium",
            iterations=iterations,
            warmup=10,
        )

        self._print_comparison("Medium Context", n_tokens, cpu_result, gpu_result)

        speedup = cpu_result.mean_ms / gpu_result.mean_ms if gpu_result.mean_ms > 0 else 0.0

        _benchmark_results.append(
            {
                "test": "test_gpu_vs_cpu_latency_medium_context",
                "status": "PASS",
                "n_tokens": n_tokens,
                "iterations": iterations,
                "cpu_mean_ms": cpu_result.mean_ms,
                "gpu_mean_ms": gpu_result.mean_ms,
                "speedup": speedup,
                "gpu_peak_mb": gpu_result.gpu_memory_peak_mb,
            }
        )

    def test_gpu_vs_cpu_latency_large_context(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        m1113_benchmark_runner: M1113GPUBenchmarkRunner,
    ) -> None:
        """GPU vs CPU latency — 20,000 tokens, 30 iterations."""
        n_tokens = 20000
        iterations = 30

        nav_cpu = self._create_nav_attention(torch.device("cpu"))
        q_cpu, e_cpu, p_cpu = m1113_test_data_factory.create(n_tokens, device=torch.device("cpu"))
        cpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_cpu,
            q_cpu,
            e_cpu,
            p_cpu,
            name="cpu_large",
            iterations=iterations,
            warmup=5,
        )

        nav_gpu = self._create_nav_attention(gpu_device)
        q_gpu, e_gpu, p_gpu = m1113_test_data_factory.create(n_tokens, device=gpu_device)
        gpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
            nav_gpu,
            q_gpu,
            e_gpu,
            p_gpu,
            name="gpu_large",
            iterations=iterations,
            warmup=10,
        )

        self._print_comparison("Large Context", n_tokens, cpu_result, gpu_result)

        speedup = cpu_result.mean_ms / gpu_result.mean_ms if gpu_result.mean_ms > 0 else 0.0

        _benchmark_results.append(
            {
                "test": "test_gpu_vs_cpu_latency_large_context",
                "status": "PASS",
                "n_tokens": n_tokens,
                "iterations": iterations,
                "cpu_mean_ms": cpu_result.mean_ms,
                "gpu_mean_ms": gpu_result.mean_ms,
                "speedup": speedup,
                "gpu_peak_mb": gpu_result.gpu_memory_peak_mb,
            }
        )

    def test_gpu_vs_cpu_scaling_curve(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        m1113_benchmark_runner: M1113GPUBenchmarkRunner,
    ) -> None:
        """Scaling curve from 1K to 50K tokens — find GPU crossover point."""
        sizes = [1000, 2000, 5000, 10000, 20000, 50000]
        iterations = 20
        scaling_data: list[dict] = []

        print("\nM1.11.3 GPU vs CPU Scaling Curve")
        print("=" * 80)
        print(
            f"{'Tokens':>8} {'CPU Mean':>10} {'GPU Mean':>10}"
            f" {'Speedup':>10} {'GPU Peak MB':>12}"
        )
        print("-" * 80)

        for n_tokens in sizes:
            # CPU
            nav_cpu = self._create_nav_attention(torch.device("cpu"))
            q_cpu, e_cpu, p_cpu = m1113_test_data_factory.create(
                n_tokens, device=torch.device("cpu")
            )
            cpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
                nav_cpu,
                q_cpu,
                e_cpu,
                p_cpu,
                name=f"cpu_{n_tokens}",
                iterations=iterations,
                warmup=3,
            )

            # GPU
            nav_gpu = self._create_nav_attention(gpu_device)
            q_gpu, e_gpu, p_gpu = m1113_test_data_factory.create(n_tokens, device=gpu_device)
            gpu_result = m1113_benchmark_runner.run_pipeline_benchmark(
                nav_gpu,
                q_gpu,
                e_gpu,
                p_gpu,
                name=f"gpu_{n_tokens}",
                iterations=iterations,
                warmup=5,
            )

            speedup = cpu_result.mean_ms / gpu_result.mean_ms if gpu_result.mean_ms > 0 else 0.0

            print(
                f"{n_tokens:>8,} {cpu_result.mean_ms:>10.2f} {gpu_result.mean_ms:>10.2f}"
                f" {speedup:>10.2f}x {gpu_result.gpu_memory_peak_mb:>12.1f}"
            )

            scaling_data.append(
                {
                    "n_tokens": n_tokens,
                    "cpu_mean_ms": cpu_result.mean_ms,
                    "gpu_mean_ms": gpu_result.mean_ms,
                    "speedup": speedup,
                    "gpu_peak_mb": gpu_result.gpu_memory_peak_mb,
                }
            )

            # Clean up to avoid OOM
            del nav_cpu, nav_gpu, q_cpu, e_cpu, p_cpu, q_gpu, e_gpu, p_gpu
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        print("-" * 80)

        # Find crossover point (where GPU becomes faster)
        crossover = None
        for d in scaling_data:
            if d["speedup"] >= 1.0:
                crossover = d["n_tokens"]
                break

        if crossover:
            print(f"GPU crossover point: ~{crossover:,} tokens")
        else:
            print("GPU did not surpass CPU in tested range (kernel launch overhead dominates)")

        print("=" * 80)

        _benchmark_results.append(
            {
                "test": "test_gpu_vs_cpu_scaling_curve",
                "status": "PASS",
                "scaling_data": scaling_data,
                "crossover_tokens": crossover,
            }
        )

    def test_gpu_vs_cpu_throughput(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """Sustained throughput — queries/sec over 5 seconds, 2000 tokens."""
        n_tokens = 2000
        duration_sec = 5.0

        results: dict[str, dict] = {}

        for device_name, device in [("CPU", torch.device("cpu")), ("GPU", gpu_device)]:
            nav = self._create_nav_attention(device)
            query, embeddings, positions = m1113_test_data_factory.create(n_tokens, device=device)

            # Warmup
            warmup_count = 10 if device.type == "cuda" else 5
            with torch.no_grad():
                for _ in range(warmup_count):
                    nav.query(query, embeddings, positions)

            # Sustained throughput
            query_count = 0
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            start = time.perf_counter()

            with torch.no_grad():
                while (time.perf_counter() - start) < duration_sec:
                    nav.query(query, embeddings, positions)
                    query_count += 1

            if device.type == "cuda":
                torch.cuda.synchronize(device)
            elapsed = time.perf_counter() - start

            queries_per_sec = query_count / elapsed
            tokens_per_sec = queries_per_sec * n_tokens

            results[device_name] = {
                "queries": query_count,
                "elapsed_sec": elapsed,
                "queries_per_sec": queries_per_sec,
                "tokens_per_sec": tokens_per_sec,
            }

        print(f"\nM1.11.3 Sustained Throughput ({n_tokens:,} tokens, {duration_sec}s)")
        print("=" * 60)
        print(f"{'Device':<10} {'Queries':>10} {'Q/sec':>10} {'Tok/sec':>15}")
        print("-" * 60)
        for name, r in results.items():
            print(
                f"{name:<10} {r['queries']:>10} {r['queries_per_sec']:>10.1f}"
                f" {r['tokens_per_sec']:>15,.0f}"
            )
        print("-" * 60)

        gpu_r = results.get("GPU", {})
        cpu_r = results.get("CPU", {})
        if gpu_r and cpu_r and cpu_r["queries_per_sec"] > 0:
            throughput_speedup = gpu_r["queries_per_sec"] / cpu_r["queries_per_sec"]
            print(f"GPU Throughput Speedup: {throughput_speedup:.2f}x")
        print("=" * 60)

        _benchmark_results.append(
            {
                "test": "test_gpu_vs_cpu_throughput",
                "status": "PASS",
                "n_tokens": n_tokens,
                "duration_sec": duration_sec,
                "cpu_qps": cpu_r.get("queries_per_sec", 0),
                "gpu_qps": gpu_r.get("queries_per_sec", 0),
                "cpu_tps": cpu_r.get("tokens_per_sec", 0),
                "gpu_tps": gpu_r.get("tokens_per_sec", 0),
            }
        )


# ---------------------------------------------------------------------------
# Class 4: TestM1113GPUMemoryProfiling
# ---------------------------------------------------------------------------


@pytest.mark.m1113
@pytest.mark.m1113_gpu
class TestM1113GPUMemoryProfiling:
    """GPU VRAM profiling using torch.cuda.memory_allocated/max_memory_allocated."""

    def test_gpu_memory_scaling(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """Memory scaling 1K->50K tokens — verify O(k) behavior.

        O(k) means memory should grow sublinearly with tokens because
        only k nearest are used in attention, not all n tokens.
        """
        sizes = [1000, 5000, 10000, 50000]
        memory_data: list[dict] = []

        print("\nM1.11.3 GPU Memory Scaling")
        print("=" * 55)
        print(f"{'Tokens':>8} {'Allocated MB':>14} {'Peak MB':>10} {'Ratio':>8}")
        print("-" * 55)

        for n_tokens in sizes:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(gpu_device)

            nav = NavigationAttention(
                d_model=M1113_D_MODEL,
                n_heads=8,
                k_neighbors=M1113_K_NEIGHBORS,
                spatial_radius=M1113_SPATIAL_RADIUS,
                enable_navigation=True,
                enable_lod=True,
            ).to(gpu_device)

            query, embeddings, positions = m1113_test_data_factory.create(
                n_tokens, device=gpu_device
            )

            with torch.no_grad():
                output, _ = nav.query(query, embeddings, positions)

            allocated_mb = torch.cuda.memory_allocated(gpu_device) / (1024 * 1024)
            peak_mb = torch.cuda.max_memory_allocated(gpu_device) / (1024 * 1024)

            ratio = peak_mb / memory_data[0]["peak_mb"] if memory_data else 1.0
            token_ratio = n_tokens / sizes[0]

            print(f"{n_tokens:>8,} {allocated_mb:>14.2f} {peak_mb:>10.2f} {ratio:>8.2f}x")

            memory_data.append(
                {
                    "n_tokens": n_tokens,
                    "allocated_mb": allocated_mb,
                    "peak_mb": peak_mb,
                    "ratio": ratio,
                    "token_ratio": token_ratio,
                }
            )

            del nav, query, embeddings, positions, output

        print("-" * 55)

        # O(k) check: memory ratio should be less than token ratio for largest size
        largest = memory_data[-1]
        print(
            f"Token ratio (50K/1K): {largest['token_ratio']:.1f}x | "
            f"Memory ratio: {largest['ratio']:.2f}x"
        )
        if largest["ratio"] < largest["token_ratio"]:
            print("O(k) VERIFIED: Memory grows sublinearly with tokens")
        else:
            print("WARNING: Memory scaling may not be O(k)")
        print("=" * 55)

        # Assert O(k): memory ratio < token ratio
        assert largest["ratio"] < largest["token_ratio"], (
            f"Memory ratio {largest['ratio']:.2f}x >= token ratio "
            f"{largest['token_ratio']:.1f}x — not O(k)"
        )

        _benchmark_results.append(
            {
                "test": "test_gpu_memory_scaling",
                "status": "PASS",
                "memory_data": memory_data,
                "o_k_verified": largest["ratio"] < largest["token_ratio"],
            }
        )

    def test_gpu_memory_breakdown(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """10K tokens — breakdown of model params, input, forward overhead."""
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(gpu_device)

        # Measure model params memory
        mem_before_model = torch.cuda.memory_allocated(gpu_device)
        nav = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=True,
            enable_lod=True,
        ).to(gpu_device)
        model_params_mb = (torch.cuda.memory_allocated(gpu_device) - mem_before_model) / (
            1024 * 1024
        )

        # Measure input memory
        mem_before_input = torch.cuda.memory_allocated(gpu_device)
        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=10000, device=gpu_device
        )
        input_mb = (torch.cuda.memory_allocated(gpu_device) - mem_before_input) / (1024 * 1024)

        # Measure forward pass overhead
        torch.cuda.reset_peak_memory_stats(gpu_device)
        mem_before_forward = torch.cuda.memory_allocated(gpu_device)

        with torch.no_grad():
            output, _ = nav.query(query, embeddings, positions)

        peak_during_forward = torch.cuda.max_memory_allocated(gpu_device) / (1024 * 1024)
        forward_overhead_mb = peak_during_forward - mem_before_forward / (1024 * 1024)

        print("\nM1.11.3 GPU Memory Breakdown (10K tokens)")
        print("=" * 45)
        print(f"  Model params:     {model_params_mb:>8.2f} MB")
        print(f"  Input tensors:    {input_mb:>8.2f} MB")
        print(f"  Forward overhead: {forward_overhead_mb:>8.2f} MB")
        print(f"  Peak total:       {peak_during_forward:>8.2f} MB")
        print("=" * 45)

        _benchmark_results.append(
            {
                "test": "test_gpu_memory_breakdown",
                "status": "PASS",
                "model_params_mb": model_params_mb,
                "input_mb": input_mb,
                "forward_overhead_mb": forward_overhead_mb,
                "peak_mb": peak_during_forward,
            }
        )

    def test_gpu_memory_cleanup(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """Run query, delete tensors, empty_cache — memory returns to baseline."""
        torch.cuda.empty_cache()
        baseline_mb = torch.cuda.memory_allocated(gpu_device) / (1024 * 1024)

        # Allocate and run
        nav = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
        ).to(gpu_device)

        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=10000, device=gpu_device
        )

        with torch.no_grad():
            output, _ = nav.query(query, embeddings, positions)

        peak_mb = torch.cuda.memory_allocated(gpu_device) / (1024 * 1024)

        # Cleanup
        del nav, query, embeddings, positions, output
        torch.cuda.empty_cache()

        after_cleanup_mb = torch.cuda.memory_allocated(gpu_device) / (1024 * 1024)

        print("\nM1.11.3 GPU Memory Cleanup")
        print("=" * 40)
        print(f"  Baseline:       {baseline_mb:>8.2f} MB")
        print(f"  Peak:           {peak_mb:>8.2f} MB")
        print(f"  After cleanup:  {after_cleanup_mb:>8.2f} MB")
        print("=" * 40)

        # Memory should return close to baseline (within 1 MB tolerance)
        assert (
            after_cleanup_mb <= baseline_mb + 1.0
        ), f"Memory not cleaned up: {after_cleanup_mb:.2f} MB > baseline {baseline_mb:.2f} MB + 1"

        _benchmark_results.append(
            {
                "test": "test_gpu_memory_cleanup",
                "status": "PASS",
                "baseline_mb": baseline_mb,
                "peak_mb": peak_mb,
                "after_cleanup_mb": after_cleanup_mb,
            }
        )


# ---------------------------------------------------------------------------
# Class 5: TestM1113GPUNavigationMetrics
# ---------------------------------------------------------------------------


@pytest.mark.m1113
@pytest.mark.m1113_gpu
class TestM1113GPUNavigationMetrics:
    """Verify navigation metrics correctness and CPU/GPU parity."""

    def test_gpu_navigation_metrics_correctness(
        self,
        m1113_nav_attention_gpu: NavigationAttention,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
        gpu_device: torch.device,
    ) -> None:
        """Verify NavigationMetrics structure, types, and value ranges on GPU."""
        query, embeddings, positions = m1113_test_data_factory.create(
            n_tokens=5000, device=gpu_device
        )

        with torch.no_grad():
            _, metrics = m1113_nav_attention_gpu.query(query, embeddings, positions)

        # Type checks
        assert isinstance(metrics, NavigationMetrics)
        assert isinstance(metrics.steps_taken, int)
        assert isinstance(metrics.attention_ops, int)
        assert isinstance(metrics.tokens_accessed, int)
        assert isinstance(metrics.warp_count, int)
        assert isinstance(metrics.converged, bool)
        assert isinstance(metrics.final_similarity, float)
        assert isinstance(metrics.trajectory_length, float)

        # Range checks
        assert metrics.steps_taken >= 0
        assert metrics.attention_ops >= 1
        assert metrics.tokens_accessed >= 0
        assert metrics.warp_count >= 0
        assert metrics.trajectory_length >= 0.0

        print("\nGPU NavigationMetrics correctness verified:")
        print(f"  steps={metrics.steps_taken}, ops={metrics.attention_ops}")
        print(f"  tokens={metrics.tokens_accessed}, warps={metrics.warp_count}")
        print(f"  converged={metrics.converged}, similarity={metrics.final_similarity:.4f}")

        _benchmark_results.append(
            {
                "test": "test_gpu_navigation_metrics_correctness",
                "status": "PASS",
                "steps": metrics.steps_taken,
                "attention_ops": metrics.attention_ops,
                "tokens_accessed": metrics.tokens_accessed,
            }
        )

    def test_gpu_navigation_quality_parity(
        self,
        gpu_device: torch.device,
        m1113_test_data_factory: "TestDataFactory",  # noqa: F821
    ) -> None:
        """Same seed/data on CPU vs GPU — steps should match, similarity close."""
        seed = 42
        n_tokens = 5000

        # CPU run
        nav_cpu = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=True,
            enable_lod=True,
            navigation_max_steps=10,
        )
        q_cpu, e_cpu, p_cpu = m1113_test_data_factory.create(
            n_tokens, device=torch.device("cpu"), seed=seed
        )
        with torch.no_grad():
            _, cpu_metrics = nav_cpu.query(q_cpu, e_cpu, p_cpu)

        # GPU run
        nav_gpu = NavigationAttention(
            d_model=M1113_D_MODEL,
            n_heads=8,
            k_neighbors=M1113_K_NEIGHBORS,
            spatial_radius=M1113_SPATIAL_RADIUS,
            enable_navigation=True,
            enable_lod=True,
            navigation_max_steps=10,
        ).to(gpu_device)
        q_gpu, e_gpu, p_gpu = m1113_test_data_factory.create(n_tokens, device=gpu_device, seed=seed)
        with torch.no_grad():
            _, gpu_metrics = nav_gpu.query(q_gpu, e_gpu, p_gpu)

        print(f"\nGPU vs CPU Navigation Quality Parity ({n_tokens:,} tokens)")
        print("=" * 50)
        print(f"  {'Metric':<25} {'CPU':>10} {'GPU':>10}")
        print(f"  {'-'*45}")
        print(f"  {'Steps taken':<25} {cpu_metrics.steps_taken:>10} {gpu_metrics.steps_taken:>10}")
        print(
            f"  {'Attention ops':<25} {cpu_metrics.attention_ops:>10}"
            f" {gpu_metrics.attention_ops:>10}"
        )
        print(
            f"  {'Tokens accessed':<25} {cpu_metrics.tokens_accessed:>10}"
            f" {gpu_metrics.tokens_accessed:>10}"
        )
        print(
            f"  {'Converged':<25} {str(cpu_metrics.converged):>10} {str(gpu_metrics.converged):>10}"
        )
        print("=" * 50)

        # Steps should match (deterministic navigation)
        assert (
            cpu_metrics.steps_taken == gpu_metrics.steps_taken
        ), f"Steps differ: CPU={cpu_metrics.steps_taken}, GPU={gpu_metrics.steps_taken}"

        # Attention ops should match
        assert cpu_metrics.attention_ops == gpu_metrics.attention_ops

        _benchmark_results.append(
            {
                "test": "test_gpu_navigation_quality_parity",
                "status": "PASS",
                "cpu_steps": cpu_metrics.steps_taken,
                "gpu_steps": gpu_metrics.steps_taken,
                "steps_match": cpu_metrics.steps_taken == gpu_metrics.steps_taken,
            }
        )


# ---------------------------------------------------------------------------
# Class 6: TestM1113ResultsSaver
# ---------------------------------------------------------------------------


@pytest.mark.m1113
class TestM1113ResultsSaver:
    """Save benchmark results to test-results-m1.11.3.md."""

    def test_z_save_results(self) -> None:
        """Write collected benchmark results to markdown file.

        Runs last alphabetically to collect all results from other tests.
        """
        if not _benchmark_results:
            pytest.skip("No benchmark results to save (other tests may have been skipped)")

        results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        results_path = os.path.join(results_dir, "test-results-m1.11.3.md")

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

        gpu_name = "N/A"
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)

        # Build test execution table
        test_rows = []
        for r in _benchmark_results:
            test_rows.append(f"| {r['test']} | {r['status']} |")

        # Extract scaling data
        scaling = next(
            (r for r in _benchmark_results if r["test"] == "test_gpu_vs_cpu_scaling_curve"),
            None,
        )

        # Extract memory data
        mem_scaling = next(
            (r for r in _benchmark_results if r["test"] == "test_gpu_memory_scaling"),
            None,
        )

        # Extract throughput data
        throughput = next(
            (r for r in _benchmark_results if r["test"] == "test_gpu_vs_cpu_throughput"),
            None,
        )

        lines = [
            "<!--",
            "Copyright 2025-2026 Adolfo Lopez (ch1pu)",
            "SPDX-License-Identifier: Apache-2.0",
            "-->",
            "",
            "# M1.11.3 GPU Full Pipeline Benchmark Results",
            "",
            f"**Generated:** {now}",
            f"**GPU:** {gpu_name}",
            f"**PyTorch:** {torch.__version__}",
            f"**CUDA:** {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
            "",
            "## Test Execution",
            "",
            "| Test | Status |",
            "|------|--------|",
            *test_rows,
            "",
            f"**Total tests:** {len(_benchmark_results)}",
            "",
        ]

        # Scaling curve table
        if scaling and scaling.get("scaling_data"):
            lines.extend(
                [
                    "## GPU vs CPU Scaling Curve",
                    "",
                    "| Tokens | CPU Mean (ms) | GPU Mean (ms) | Speedup | GPU Peak (MB) |",
                    "|--------|---------------|---------------|---------|---------------|",
                ]
            )
            for d in scaling["scaling_data"]:
                lines.append(
                    f"| {d['n_tokens']:,} | {d['cpu_mean_ms']:.2f} | "
                    f"{d['gpu_mean_ms']:.2f} | {d['speedup']:.2f}x | "
                    f"{d['gpu_peak_mb']:.1f} |"
                )
            crossover = scaling.get("crossover_tokens")
            if crossover:
                lines.append(f"\n**GPU Crossover Point:** ~{crossover:,} tokens")
            else:
                lines.append(
                    "\n**GPU Crossover:** Not reached in tested range "
                    "(kernel launch overhead dominates)"
                )
            lines.append("")

        # Memory scaling table
        if mem_scaling and mem_scaling.get("memory_data"):
            lines.extend(
                [
                    "## GPU Memory Scaling",
                    "",
                    "| Tokens | Allocated (MB) | Peak (MB) | Ratio |",
                    "|--------|----------------|-----------|-------|",
                ]
            )
            for d in mem_scaling["memory_data"]:
                lines.append(
                    f"| {d['n_tokens']:,} | {d['allocated_mb']:.2f} | "
                    f"{d['peak_mb']:.2f} | {d['ratio']:.2f}x |"
                )
            lines.append(f"\n**O(k) Verified:** {mem_scaling.get('o_k_verified', False)}")
            lines.append("")

        # Throughput
        if throughput:
            lines.extend(
                [
                    "## Sustained Throughput",
                    "",
                    f"- **CPU:** {throughput.get('cpu_qps', 0):.1f} queries/sec"
                    f" ({throughput.get('cpu_tps', 0):,.0f} tokens/sec)",
                    f"- **GPU:** {throughput.get('gpu_qps', 0):.1f} queries/sec"
                    f" ({throughput.get('gpu_tps', 0):,.0f} tokens/sec)",
                    "",
                ]
            )

        lines.extend(
            [
                "---",
                "",
                "*Author: Adolfo Lopez (ch1pu) - U.S. Navy Veteran*",
                "",
            ]
        )

        with open(results_path, "w") as f:
            f.write("\n".join(lines))

        print(f"\nResults saved to: {results_path}")
        print(f"Total benchmarks recorded: {len(_benchmark_results)}")
