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
conftest_m1113.py - M1.11.3 pytest fixtures for GPU Full Pipeline Benchmarks.

Provides GPU device fixtures, GPU-aware NavigationAttention instances,
benchmark runner with proper CUDA timing, and test data factories.

Chains M1.11.2 fixtures for Qdrant adapters and navigation components.

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.3 - GPU Full Pipeline Benchmarks
"""

import statistics
import time
from dataclasses import dataclass, field

import pytest
import torch

from spatial_engine.integration.navigation_attention import (
    NavigationAttention,
    NavigationMetrics,
)
from spatial_engine.tests.conftest import check_cuda_compatible

# Chain M1.11.2 fixtures (which also chains M1.11 fixtures)
pytest_plugins = ["spatial_engine.tests.conftest_m1112"]

# M1.11.3 constants (match M1.11/M1.11.2)
M1113_D_MODEL = 256
M1113_K_NEIGHBORS = 50
M1113_SPATIAL_RADIUS = 50.0


# ---------------------------------------------------------------------------
# Pytest Marker Configuration
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register M1.11.3 markers."""
    config.addinivalue_line("markers", "m1113: M1.11.3 GPU Full Pipeline Benchmark tests")
    config.addinivalue_line("markers", "m1113_gpu: M1.11.3 GPU-specific tests")
    config.addinivalue_line("markers", "m1113_benchmark: M1.11.3 benchmark tests")


# ---------------------------------------------------------------------------
# GPUBenchmarkResult Dataclass
# ---------------------------------------------------------------------------


@dataclass
class GPUBenchmarkResult:
    """Captures per-benchmark metrics for GPU pipeline benchmarks.

    Stores timing statistics, throughput, GPU memory usage, and
    navigation metrics from the last run.
    """

    name: str = ""
    device: str = "cpu"
    n_tokens: int = 0
    iterations: int = 0
    warmup: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    tokens_per_sec: float = 0.0
    gpu_memory_allocated_mb: float = 0.0
    gpu_memory_peak_mb: float = 0.0
    last_metrics: NavigationMetrics = field(default_factory=NavigationMetrics)

    def compute_stats(self) -> None:
        """Compute statistics from latencies_ms list."""
        if not self.latencies_ms:
            return
        self.mean_ms = statistics.mean(self.latencies_ms)
        sorted_lat = sorted(self.latencies_ms)
        n = len(sorted_lat)
        self.p50_ms = sorted_lat[n // 2]
        self.p95_ms = sorted_lat[int(n * 0.95)]
        self.p99_ms = sorted_lat[int(n * 0.99)]
        self.min_ms = sorted_lat[0]
        self.max_ms = sorted_lat[-1]
        if self.mean_ms > 0:
            self.tokens_per_sec = self.n_tokens / (self.mean_ms / 1000.0)


# ---------------------------------------------------------------------------
# M1113GPUBenchmarkRunner
# ---------------------------------------------------------------------------


class M1113GPUBenchmarkRunner:
    """Runs pipeline benchmarks with proper GPU timing.

    Uses torch.cuda.synchronize() for accurate GPU timing and
    tracks GPU memory usage via torch.cuda.max_memory_allocated().
    """

    def run_pipeline_benchmark(
        self,
        nav_attention: NavigationAttention,
        query: torch.Tensor,
        context_embeddings: torch.Tensor,
        context_positions: torch.Tensor,
        *,
        name: str = "benchmark",
        iterations: int = 50,
        warmup: int = 10,
    ) -> GPUBenchmarkResult:
        """Run a pipeline benchmark with proper timing.

        Args:
            nav_attention: The NavigationAttention instance to benchmark
            query: Query embedding [d_model]
            context_embeddings: Context embeddings [n, d_model]
            context_positions: Context positions [n, 3]
            name: Benchmark name for reporting
            iterations: Number of timed iterations
            warmup: Number of warmup iterations (not timed)

        Returns:
            GPUBenchmarkResult with timing and memory statistics
        """
        device = query.device
        is_cuda = device.type == "cuda"

        # Warmup phase
        with torch.no_grad():
            for _ in range(warmup):
                nav_attention.query(
                    query=query,
                    context_embeddings=context_embeddings,
                    context_positions=context_positions,
                )

        # Reset GPU memory tracking
        if is_cuda:
            torch.cuda.reset_peak_memory_stats(device)

        # Timed iterations
        latencies: list[float] = []
        last_metrics = NavigationMetrics()

        with torch.no_grad():
            for _ in range(iterations):
                if is_cuda:
                    torch.cuda.synchronize(device)
                start = time.perf_counter()

                output, metrics = nav_attention.query(
                    query=query,
                    context_embeddings=context_embeddings,
                    context_positions=context_positions,
                )

                if is_cuda:
                    torch.cuda.synchronize(device)
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
                last_metrics = metrics

        # Collect GPU memory
        gpu_allocated_mb = 0.0
        gpu_peak_mb = 0.0
        if is_cuda:
            gpu_allocated_mb = torch.cuda.memory_allocated(device) / (1024 * 1024)
            gpu_peak_mb = torch.cuda.max_memory_allocated(device) / (1024 * 1024)

        result = GPUBenchmarkResult(
            name=name,
            device=str(device),
            n_tokens=len(context_embeddings),
            iterations=iterations,
            warmup=warmup,
            latencies_ms=latencies,
            gpu_memory_allocated_mb=gpu_allocated_mb,
            gpu_memory_peak_mb=gpu_peak_mb,
            last_metrics=last_metrics,
        )
        result.compute_stats()
        return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gpu_device() -> torch.device:
    """Return CUDA device, skip if GPU not compatible.

    Returns:
        torch.device("cuda") if GPU is available and compatible
    """
    is_ok, reason = check_cuda_compatible()
    if not is_ok:
        pytest.skip(reason)
    return torch.device("cuda")


@pytest.fixture
def cpu_device() -> torch.device:
    """Return CPU device.

    Returns:
        torch.device("cpu")
    """
    return torch.device("cpu")


@pytest.fixture
def m1113_nav_attention_gpu(gpu_device: torch.device) -> NavigationAttention:
    """NavigationAttention on GPU for M1.11.3 benchmarks.

    Args:
        gpu_device: CUDA device fixture

    Returns:
        NavigationAttention moved to GPU
    """
    return NavigationAttention(
        d_model=M1113_D_MODEL,
        n_heads=8,
        k_neighbors=M1113_K_NEIGHBORS,
        spatial_radius=M1113_SPATIAL_RADIUS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    ).to(gpu_device)


@pytest.fixture
def m1113_nav_attention_cpu() -> NavigationAttention:
    """NavigationAttention on CPU for M1.11.3 benchmarks.

    Returns:
        NavigationAttention on CPU
    """
    return NavigationAttention(
        d_model=M1113_D_MODEL,
        n_heads=8,
        k_neighbors=M1113_K_NEIGHBORS,
        spatial_radius=M1113_SPATIAL_RADIUS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    )


_CPU_DEVICE = torch.device("cpu")


@pytest.fixture
def m1113_test_data_factory():  # type: ignore[no-untyped-def]
    """Factory for creating test data on a specific device.

    Returns:
        TestDataFactory instance with create() method
    """

    class TestDataFactory:
        """Creates reproducible test data on a specified device."""

        def create(
            self,
            n_tokens: int,
            d_model: int = M1113_D_MODEL,
            device: torch.device = _CPU_DEVICE,
            seed: int = 42,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """Create query, embeddings, and positions on device.

            Args:
                n_tokens: Number of context tokens
                d_model: Embedding dimension
                device: Target device
                seed: Random seed for reproducibility

            Returns:
                (query, embeddings, positions) all on device
            """
            torch.manual_seed(seed)
            query = torch.randn(d_model, device=device)
            embeddings = torch.randn(n_tokens, d_model, device=device)
            positions = torch.randn(n_tokens, 3, device=device) * 500.0
            return query, embeddings, positions

    return TestDataFactory()


@pytest.fixture
def m1113_benchmark_runner() -> M1113GPUBenchmarkRunner:
    """Return M1113GPUBenchmarkRunner instance.

    Returns:
        Benchmark runner with proper GPU timing
    """
    return M1113GPUBenchmarkRunner()
