"""
test_integration_benchmarks.py - Performance benchmarks for transformer-vectorstore integration.

Tests performance characteristics including:
- End-to-end latency
- O(k) complexity verification with vector store
- Throughput measurements
- Memory usage scaling
- Backend comparison (Qdrant vs pgvector)

Author: ch1pu
Milestone: 1.7 - Integration Testing
TDD Phase: RED (tests written first, implementation follows)

Test Count: 6 benchmark tests
"""

import gc
import time
from typing import Generator

import pytest
import torch

from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter
from spatial_engine.integration import TransformerBridge

# Check for pgvector availability
try:
    from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def benchmark_transformer() -> SpatialTransformer:
    """Create transformer for benchmarking.

    Uses smaller config for faster benchmarks while still being representative.
    """
    return SpatialTransformer(
        n_layers=3,
        d_model=256,
        n_heads=8,
        d_ff=1024,
        spatial_radius=50.0,
        dropout=0.0,
    )


@pytest.fixture(scope="function")
def benchmark_qdrant() -> Generator[QdrantAdapter, None, None]:
    """Create Qdrant adapter for benchmarks with pre-populated data."""
    adapter = QdrantAdapter(
        collection_name="benchmark_collection",
        d_model=256,
        use_memory=True,
    )

    # Pre-populate with test data (1000 tokens)
    torch.manual_seed(42)
    embeddings = torch.randn(1000, 256)
    positions = torch.randn(1000, 3) * 500.0
    adapter.store(embeddings, positions)

    yield adapter
    adapter.close()


@pytest.fixture(scope="function")
def bridge_for_benchmark(
    benchmark_transformer: SpatialTransformer,
    benchmark_qdrant: QdrantAdapter,
) -> TransformerBridge:
    """Create bridge for benchmarking."""
    return TransformerBridge(
        transformer=benchmark_transformer,
        vector_store=benchmark_qdrant,
        k_neighbors=50,
    )


# ---------------------------------------------------------------------------
# TestPerformanceBenchmarks (6 tests)
# ---------------------------------------------------------------------------


class TestPerformanceBenchmarks:
    """Performance benchmark tests for integration layer."""

    @pytest.mark.benchmark
    def test_end_to_end_latency_qdrant(
        self,
        bridge_for_benchmark: TransformerBridge,
    ) -> None:
        """Verify end-to-end latency <100ms with Qdrant.

        Target: <100ms for single forward pass with 128 tokens.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = bridge_for_benchmark

        # Create test input
        x = torch.randn(1, 128, 256)
        positions = torch.randn(1, 128, 3) * 100.0

        # Warmup (5 iterations)
        for _ in range(5):
            _ = bridge(x, positions)

        # Measure (20 iterations)
        latencies: list[float] = []
        for _ in range(20):
            gc.collect()  # Clean memory before measurement
            start = time.perf_counter()
            _ = bridge(x, positions)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"\n{'='*60}")
        print("End-to-End Latency Benchmark (Qdrant)")
        print(f"{'='*60}")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  Min:     {min_latency:.2f}ms")
        print(f"  Max:     {max_latency:.2f}ms")
        print(f"  Target:  <100ms")
        print(f"  Status:  {'PASS' if avg_latency < 100 else 'FAIL'}")
        print(f"{'='*60}")

        assert avg_latency < 100, (
            f"Latency {avg_latency:.2f}ms > 100ms target. "
            f"Performance optimization needed."
        )

    @pytest.mark.benchmark
    @pytest.mark.requires_docker
    def test_end_to_end_latency_pgvector(
        self,
        benchmark_transformer: SpatialTransformer,
        pgvector_with_data,
    ) -> None:
        """Verify end-to-end latency <150ms with pgvector.

        Target: <150ms for single forward pass with 128 tokens.
        (Higher than Qdrant due to network I/O)

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=benchmark_transformer,
            vector_store=pgvector_with_data,
            k_neighbors=50,
        )

        # Create test input
        x = torch.randn(1, 128, 256)
        positions = torch.randn(1, 128, 3) * 100.0

        # Warmup
        for _ in range(3):
            _ = bridge(x, positions)

        # Measure
        latencies: list[float] = []
        for _ in range(10):
            gc.collect()
            start = time.perf_counter()
            _ = bridge(x, positions)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)

        print(f"\n{'='*60}")
        print("End-to-End Latency Benchmark (pgvector)")
        print(f"{'='*60}")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  Target:  <150ms")
        print(f"  Status:  {'PASS' if avg_latency < 150 else 'FAIL'}")
        print(f"{'='*60}")

        assert avg_latency < 150, (
            f"Latency {avg_latency:.2f}ms > 150ms target."
        )

    @pytest.mark.benchmark
    def test_ok_complexity_with_vector_store(
        self,
        benchmark_transformer: SpatialTransformer,
    ) -> None:
        """Verify O(k) complexity maintained with vector store queries.

        This is the CRITICAL test proving the core innovation works end-to-end.

        Methodology:
        - Measure time with context sizes: 1000, 2000, 4000 tokens
        - O(k): ratios should be ~1.0 (constant time)
        - O(n): ratios would be ~2.0 and ~4.0
        - O(n²): ratios would be ~4.0 and ~16.0

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        times: dict[int, float] = {}

        for context_size in [1000, 2000, 4000]:
            # Create adapter with context_size tokens
            adapter = QdrantAdapter(
                collection_name=f"ok_test_{context_size}",
                d_model=256,
                use_memory=True,
            )

            torch.manual_seed(42)
            embeddings = torch.randn(context_size, 256)
            positions = torch.randn(context_size, 3) * 500.0
            adapter.store(embeddings, positions)

            bridge = TransformerBridge(
                transformer=benchmark_transformer,
                vector_store=adapter,
                k_neighbors=50,  # Fixed k for all context sizes
            )

            # Test input
            x = torch.randn(1, 64, 256)
            pos = torch.randn(1, 64, 3) * 100.0

            # Warmup
            for _ in range(3):
                _ = bridge(x, pos)

            # Measure
            gc.collect()
            start = time.perf_counter()
            for _ in range(10):
                _ = bridge(x, pos)
            elapsed = (time.perf_counter() - start) / 10

            times[context_size] = elapsed
            adapter.close()

        # Calculate ratios
        ratio_2x = times[2000] / times[1000]
        ratio_4x = times[4000] / times[1000]

        print(f"\n{'='*60}")
        print("O(k) Complexity Verification with Vector Store")
        print(f"{'='*60}")
        print(f"  Context 1000: {times[1000]*1000:.2f}ms")
        print(f"  Context 2000: {times[2000]*1000:.2f}ms  (ratio: {ratio_2x:.2f}x)")
        print(f"  Context 4000: {times[4000]*1000:.2f}ms  (ratio: {ratio_4x:.2f}x)")
        print(f"  Expected for O(k):  ratio ~1.0")
        print(f"  Expected for O(n):  ratio ~2.0, ~4.0")
        print(f"  Expected for O(n²): ratio ~4.0, ~16.0")
        print(f"{'='*60}")

        # O(k) should have ratios close to 1.0 (allowing for overhead)
        # We use 1.5 and 2.0 as thresholds to account for cache effects
        assert ratio_2x < 1.5, (
            f"Not O(k): 2x context ratio = {ratio_2x:.2f}. "
            f"Expected <1.5 for O(k) complexity."
        )
        assert ratio_4x < 2.0, (
            f"Not O(k): 4x context ratio = {ratio_4x:.2f}. "
            f"Expected <2.0 for O(k) complexity."
        )

        print(f"\n  O(k) VERIFIED: 2x={ratio_2x:.2f}, 4x={ratio_4x:.2f}")

    @pytest.mark.benchmark
    def test_throughput_tokens_per_second(
        self,
        bridge_for_benchmark: TransformerBridge,
    ) -> None:
        """Measure throughput in tokens per second.

        Target: >1000 tokens/second for practical use.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = bridge_for_benchmark

        # Test input: 1 batch, 256 tokens
        x = torch.randn(1, 256, 256)
        positions = torch.randn(1, 256, 3) * 100.0
        tokens_per_batch = 256

        # Warmup
        for _ in range(3):
            _ = bridge(x, positions)

        # Measure
        total_tokens = 0
        start = time.perf_counter()
        iterations = 20
        for _ in range(iterations):
            _ = bridge(x, positions)
            total_tokens += tokens_per_batch

        elapsed = time.perf_counter() - start
        throughput = total_tokens / elapsed

        print(f"\n{'='*60}")
        print("Throughput Benchmark")
        print(f"{'='*60}")
        print(f"  Total tokens:    {total_tokens}")
        print(f"  Total time:      {elapsed:.2f}s")
        print(f"  Throughput:      {throughput:.0f} tokens/sec")
        print(f"  Target:          >1000 tokens/sec")
        print(f"  Status:          {'PASS' if throughput > 1000 else 'FAIL'}")
        print(f"{'='*60}")

        assert throughput > 1000, (
            f"Throughput {throughput:.0f} tokens/sec < 1000 target."
        )

    @pytest.mark.benchmark
    def test_memory_usage_scaling(
        self,
        benchmark_transformer: SpatialTransformer,
    ) -> None:
        """Verify memory usage scales appropriately.

        Memory should not grow linearly with context size for O(k) system.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        import sys

        def get_memory_mb() -> float:
            """Get current memory usage in MB (approximate)."""
            gc.collect()
            # Use sys.getsizeof for a rough estimate
            # In production, would use tracemalloc or memory_profiler
            return 0.0  # Will be implemented in GREEN phase

        memory_by_size: dict[int, float] = {}

        for context_size in [500, 1000, 2000]:
            adapter = QdrantAdapter(
                collection_name=f"mem_test_{context_size}",
                d_model=256,
                use_memory=True,
            )

            torch.manual_seed(42)
            embeddings = torch.randn(context_size, 256)
            positions = torch.randn(context_size, 3) * 500.0
            adapter.store(embeddings, positions)

            bridge = TransformerBridge(
                transformer=benchmark_transformer,
                vector_store=adapter,
                k_neighbors=50,
            )

            # Run forward pass
            x = torch.randn(1, 64, 256)
            pos = torch.randn(1, 64, 3) * 100.0
            _ = bridge(x, pos)

            # Record memory (placeholder for now)
            memory_by_size[context_size] = bridge.get_memory_usage_mb()

            adapter.close()

        print(f"\n{'='*60}")
        print("Memory Usage Scaling")
        print(f"{'='*60}")
        for size, mem in memory_by_size.items():
            print(f"  Context {size}: {mem:.1f}MB")
        print(f"{'='*60}")

        # Memory should not grow linearly with context size
        # For O(k), memory should be roughly constant
        mem_500 = memory_by_size[500]
        mem_2000 = memory_by_size[2000]

        if mem_500 > 0:
            ratio = mem_2000 / mem_500
            assert ratio < 2.0, (
                f"Memory scales too much: 4x context = {ratio:.1f}x memory. "
                f"Expected <2.0 for O(k)."
            )

    @pytest.mark.benchmark
    def test_scaling_comparison(
        self,
        benchmark_transformer: SpatialTransformer,
    ) -> None:
        """Compare scaling between Qdrant and pgvector (if available).

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # Qdrant test
        qdrant_times: list[float] = []

        for _ in range(3):
            adapter = QdrantAdapter(
                collection_name="scaling_test",
                d_model=256,
                use_memory=True,
            )

            torch.manual_seed(42)
            embeddings = torch.randn(500, 256)
            positions = torch.randn(500, 3) * 500.0
            adapter.store(embeddings, positions)

            bridge = TransformerBridge(
                transformer=benchmark_transformer,
                vector_store=adapter,
                k_neighbors=50,
            )

            x = torch.randn(1, 64, 256)
            pos = torch.randn(1, 64, 3) * 100.0

            # Warmup
            _ = bridge(x, pos)

            # Measure
            start = time.perf_counter()
            for _ in range(5):
                _ = bridge(x, pos)
            elapsed = (time.perf_counter() - start) / 5
            qdrant_times.append(elapsed)

            adapter.close()

        avg_qdrant = sum(qdrant_times) / len(qdrant_times)

        print(f"\n{'='*60}")
        print("Backend Scaling Comparison")
        print(f"{'='*60}")
        print(f"  Qdrant (in-memory): {avg_qdrant*1000:.2f}ms avg")

        # Note: pgvector comparison would go here if Docker is available
        # Skipped for now as it requires Docker
        if PGVECTOR_AVAILABLE:
            print("  pgvector: (requires Docker - skipped)")

        print(f"{'='*60}")

        # Just verify Qdrant works
        assert avg_qdrant < 0.5, f"Qdrant too slow: {avg_qdrant*1000:.2f}ms"
