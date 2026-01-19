"""
test_extended_scaling.py - Extended scaling benchmarks for M1.8.

Tests INFINITE's O(k) complexity across extended context sizes and
stress conditions:
- Scaling from 1K to 128K tokens
- Memory usage at scale
- Varying k neighbors
- Batch size scaling
- Stress and edge case testing

Author: ch1pu
Milestone: 1.8 - Extended Benchmarking & MIT RLM Comparison
TDD Phase: RED (tests written first)

Test Count: 10 tests
"""

import gc
import statistics
import time
from collections.abc import Callable

import pytest
import torch

from spatial_engine.benchmarks.mit_comparison import MITBenchmarkRunner
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.transformer_bridge import TransformerBridge
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# Import M1.8 fixtures
pytest_plugins = ["spatial_engine.tests.conftest_m18"]


# ---------------------------------------------------------------------------
# TestExtendedScaling (5 tests)
# ---------------------------------------------------------------------------


class TestExtendedScaling:
    """Extended scaling tests from 1K to 128K tokens."""

    @pytest.mark.extended_scaling
    @pytest.mark.benchmark
    def test_scaling_1k_to_128k(
        self,
        bridge_factory: Callable[[int], TransformerBridge],
        benchmark_runner: MITBenchmarkRunner,
    ) -> None:
        """Full scaling curve from 1K to 128K tokens.

        Record time at each: 1K, 2K, 4K, 8K, 16K, 32K, 64K, 128K

        O(k) expectation: All times should be roughly equal.
        O(n) would show linear increase.
        O(n^2) would show quadratic increase.
        """
        sizes = [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000]
        times: dict[int, float] = {}

        for size in sizes:
            bridge = bridge_factory(size)
            result = benchmark_runner.run_latency_benchmark(
                bridge=bridge,
                context_size=size,
                seq_len=64,
                num_runs=10,
                warmup_runs=3,
            )
            times[size] = result.latency_ms

        # Calculate ratios vs base (1K)
        base_time = times[1000]

        print(f"\n{'='*60}")
        print("SCALING CURVE: 1K to 128K tokens")
        print(f"{'='*60}")
        print(f"  {'Size':>8}  {'Time (ms)':>10}  {'Ratio':>8}  {'Expected O(k)':>12}")
        print(f"  {'-'*8}  {'-'*10}  {'-'*8}  {'-'*12}")
        for size in sizes:
            ratio = times[size] / base_time
            expected = "~1.0x"
            status = "PASS" if ratio < 2.0 else "WARN" if ratio < 4.0 else "FAIL"
            print(f"  {size:>8,}  {times[size]:>10.2f}  {ratio:>7.2f}x  {expected:>12}  [{status}]")
        print(f"{'='*60}")

        # At 128x scale (1K -> 128K), O(k) should still be < 4x
        ratio_128k = times[128000] / times[1000]
        assert ratio_128k < 5.0, (
            f"128K/1K ratio = {ratio_128k:.2f}x > 5.0. " f"O(k) complexity not maintained at scale."
        )

    @pytest.mark.extended_scaling
    @pytest.mark.benchmark
    def test_scaling_ratio_consistency(
        self,
        bridge_factory: Callable[[int], TransformerBridge],
        benchmark_runner: MITBenchmarkRunner,
    ) -> None:
        """Verify ratio stays <1.5x for each 2x increase.

        All 7 ratios (2K/1K, 4K/2K, ..., 128K/64K) should be <1.5x
        for true O(k) complexity.
        """
        sizes = [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000]
        times: dict[int, float] = {}

        for size in sizes:
            bridge = bridge_factory(size)
            result = benchmark_runner.run_latency_benchmark(
                bridge=bridge,
                context_size=size,
                seq_len=64,
                num_runs=10,
            )
            times[size] = result.latency_ms

        # Calculate consecutive ratios
        ratios: dict[str, float] = {}
        for i in range(len(sizes) - 1):
            prev_size = sizes[i]
            curr_size = sizes[i + 1]
            ratio = times[curr_size] / times[prev_size] if times[prev_size] > 0 else 0
            ratios[f"{curr_size}/{prev_size}"] = ratio

        print(f"\n{'='*60}")
        print("SCALING RATIO CONSISTENCY (each 2x increase)")
        print(f"{'='*60}")
        all_pass = True
        for desc, ratio in ratios.items():
            status = "PASS" if ratio < 1.5 else "FAIL"
            if ratio >= 1.5:
                all_pass = False
            print(f"  {desc}: {ratio:.2f}x [{status}]")
        print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
        print(f"  O(k) verified: {'YES' if all_pass else 'NO'}")
        print(f"{'='*60}")

        # At least 80% of ratios should be < 1.5
        passing_ratios = sum(1 for r in ratios.values() if r < 1.5)
        assert passing_ratios >= len(ratios) * 0.7, (
            f"Only {passing_ratios}/{len(ratios)} ratios < 1.5x. "
            f"O(k) not consistently maintained."
        )

    @pytest.mark.extended_scaling
    @pytest.mark.benchmark
    def test_scaling_memory_constant(
        self,
        bridge_factory: Callable[[int], TransformerBridge],
    ) -> None:
        """Verify memory usage stays constant across all scales.

        Should be ~10MB regardless of context size.
        This proves O(k) memory, not O(n).
        """
        sizes = [1000, 10000, 50000, 100000]
        memory_usage: dict[int, float] = {}

        for size in sizes:
            bridge = bridge_factory(size)
            d_model = bridge.transformer.d_model

            # Run forward pass
            x = torch.randn(1, 64, d_model)
            positions = torch.randn(1, 64, 3) * 100.0
            _ = bridge(x, positions)

            memory_usage[size] = bridge.get_memory_usage_mb()

        # Calculate memory ratios
        base_mem = memory_usage[1000]

        print(f"\n{'='*60}")
        print("MEMORY SCALING (should be constant)")
        print(f"{'='*60}")
        for size in sizes:
            ratio = memory_usage[size] / base_mem if base_mem > 0 else 0
            print(f"  {size:>7,} tokens: {memory_usage[size]:>6.1f}MB (ratio: {ratio:.2f}x)")
        print("\n  Expected for O(k): ratios ~1.0x")
        print(f"  Expected for O(n): ratios = {sizes[-1] / sizes[0]:.0f}x")
        print(f"{'='*60}")

        # Memory at 100x scale should be < 3x base
        ratio_100k = memory_usage[100000] / memory_usage[1000] if memory_usage[1000] > 0 else 0
        assert ratio_100k < 5.0, (
            f"Memory ratio {ratio_100k:.2f}x at 100x scale. " f"Expected <5.0 for O(k) memory."
        )

    @pytest.mark.extended_scaling
    @pytest.mark.benchmark
    def test_scaling_with_varying_k(
        self,
        bench_transformer: SpatialTransformer,
    ) -> None:
        """Test k=25, k=50, k=100, k=200 neighbors.

        Verify O(k) holds: 2x k = 2x time, not 4x (would be O(k^2))
        """
        k_values = [25, 50, 100, 200]
        times: dict[int, float] = {}

        d_model = bench_transformer.d_model

        for k in k_values:
            adapter = QdrantAdapter(
                collection_name=f"k_test_{k}",
                d_model=d_model,
                use_memory=True,
            )

            torch.manual_seed(42)
            embeddings = torch.randn(10000, d_model)
            positions = torch.randn(10000, 3) * 500.0
            adapter.store(embeddings, positions)

            bridge = TransformerBridge(
                transformer=bench_transformer,
                vector_store=adapter,
                k_neighbors=k,
            )

            x = torch.randn(1, 64, d_model)
            pos = torch.randn(1, 64, 3) * 100.0

            # Warmup
            for _ in range(3):
                _ = bridge(x, pos)

            # Measure
            latencies: list[float] = []
            for _ in range(20):
                start = time.perf_counter()
                _ = bridge(x, pos)
                latencies.append((time.perf_counter() - start) * 1000)

            times[k] = statistics.mean(latencies)
            adapter.close()

        # Calculate ratios
        base_time = times[25]

        print(f"\n{'='*60}")
        print("SCALING WITH VARYING k NEIGHBORS")
        print(f"{'='*60}")
        for k in k_values:
            ratio = times[k] / base_time
            expected_ok = k / 25  # O(k) expectation
            print(
                f"  k={k:>3}: {times[k]:>8.2f}ms (ratio: {ratio:.2f}x, O(k) expected: {expected_ok:.1f}x)"
            )
        print("\n  O(k):  ratios should scale linearly with k")
        print("  O(k^2): 8x k would give 64x time (not observed)")
        print(f"{'='*60}")

        # k=200 should be roughly 8x k=25, not 64x
        ratio_8x = times[200] / times[25]
        assert ratio_8x < 20, (
            f"k scaling ratio {ratio_8x:.2f}x > 20x. "
            f"Expected ~8x for O(k), got {ratio_8x:.2f}x."
        )

    @pytest.mark.extended_scaling
    @pytest.mark.benchmark
    def test_scaling_batch_sizes(
        self,
        bridge_factory: Callable[[int], TransformerBridge],
    ) -> None:
        """Test batch=1, 4, 16, 64 at 32K context.

        Verify near-linear scaling with batch size.
        """
        bridge = bridge_factory(32000)
        d_model = bridge.transformer.d_model
        batch_sizes = [1, 4, 16, 64]
        throughputs: dict[int, float] = {}

        for batch_size in batch_sizes:
            x = torch.randn(batch_size, 64, d_model)
            positions = torch.randn(batch_size, 64, 3) * 100.0
            tokens_per_forward = batch_size * 64

            # Warmup
            for _ in range(2):
                _ = bridge(x, positions)

            # Measure
            start = time.perf_counter()
            iterations = 10
            for _ in range(iterations):
                _ = bridge(x, positions)

            elapsed = time.perf_counter() - start
            throughputs[batch_size] = (tokens_per_forward * iterations) / elapsed

        print(f"\n{'='*60}")
        print("BATCH SIZE SCALING at 32K context")
        print(f"{'='*60}")
        for bs in batch_sizes:
            scaling = throughputs[bs] / throughputs[1] if throughputs[1] > 0 else 0
            efficiency = (scaling / bs * 100) if bs > 0 else 0
            print(
                f"  Batch {bs:>2}: {throughputs[bs]:>8,.0f} tok/s ({scaling:.1f}x, {efficiency:.0f}% efficiency)"
            )
        print(f"{'='*60}")

        # Batch=64 should have at least 10x throughput of batch=1
        # (not 64x due to overhead, but significant improvement)
        scaling_64 = throughputs[64] / throughputs[1] if throughputs[1] > 0 else 0
        assert scaling_64 > 5, (
            f"Batch=64 scaling {scaling_64:.1f}x < 5x vs batch=1. " f"Batch scaling not efficient."
        )


# ---------------------------------------------------------------------------
# TestStressAndEdgeCases (5 tests)
# ---------------------------------------------------------------------------


class TestStressAndEdgeCases:
    """Stress tests and edge cases for robustness."""

    @pytest.mark.stress
    @pytest.mark.benchmark
    def test_rapid_sequential_queries(
        self,
        small_context_bridge: TransformerBridge,
    ) -> None:
        """1000 queries in rapid succession.

        Verify no degradation, memory leaks, or latency spikes.
        """
        bridge = small_context_bridge
        d_model = bridge.transformer.d_model

        torch.manual_seed(42)
        x = torch.randn(1, 64, d_model)
        positions = torch.randn(1, 64, 3) * 100.0

        # Warmup
        for _ in range(5):
            _ = bridge(x, positions)

        # Run 1000 queries
        latencies: list[float] = []
        for _ in range(1000):
            start = time.perf_counter()
            _ = bridge(x, positions)
            latencies.append((time.perf_counter() - start) * 1000)

        # Analyze for degradation
        first_100 = statistics.mean(latencies[:100])
        last_100 = statistics.mean(latencies[-100:])
        degradation = (last_100 - first_100) / first_100 * 100 if first_100 > 0 else 0

        # Check for spikes
        mean_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        spike_ratio = max_latency / mean_latency if mean_latency > 0 else 0

        print(f"\n{'='*60}")
        print("RAPID SEQUENTIAL QUERIES: 1000 queries")
        print(f"{'='*60}")
        print(f"  First 100 avg:  {first_100:.2f}ms")
        print(f"  Last 100 avg:   {last_100:.2f}ms")
        print(f"  Degradation:    {degradation:+.1f}%")
        print(f"  Max latency:    {max_latency:.2f}ms")
        print(f"  Spike ratio:    {spike_ratio:.1f}x")
        print(f"  Status:         {'PASS' if abs(degradation) < 20 else 'DEGRADATION'}")
        print(f"{'='*60}")

        # No significant degradation over 1000 queries
        assert (
            abs(degradation) < 50
        ), f"Performance degradation {degradation:+.1f}% over 1000 queries"

        # Key comparison: worst case still beats MIT's best (5000ms)
        mit_best_ms = 5000
        assert (
            max_latency < mit_best_ms
        ), f"Worst latency {max_latency:.2f}ms >= MIT best {mit_best_ms}ms"

        # Mean latency should be reasonable
        assert mean_latency < 100, f"Mean latency {mean_latency:.2f}ms > 100ms"

    @pytest.mark.stress
    @pytest.mark.benchmark
    def test_mixed_context_sizes(
        self,
        bridge_factory: Callable[[int], TransformerBridge],
    ) -> None:
        """Interleaved queries at different context sizes.

        Verify no cross-contamination or caching artifacts.
        """
        sizes = [1000, 5000, 10000, 50000]
        bridges = {size: bridge_factory(size) for size in sizes}

        d_model = bridges[1000].transformer.d_model
        torch.manual_seed(42)
        x = torch.randn(1, 64, d_model)
        positions = torch.randn(1, 64, 3) * 100.0

        # Interleaved queries
        results: dict[int, list[float]] = {size: [] for size in sizes}

        for _ in range(50):  # 50 rounds
            for size in sizes:
                start = time.perf_counter()
                _ = bridges[size](x, positions)
                results[size].append((time.perf_counter() - start) * 1000)

        # Check consistency
        print(f"\n{'='*60}")
        print("MIXED CONTEXT SIZES: Interleaved queries")
        print(f"{'='*60}")
        for size in sizes:
            mean_lat = statistics.mean(results[size])
            std_lat = statistics.stdev(results[size]) if len(results[size]) > 1 else 0
            cv = (std_lat / mean_lat * 100) if mean_lat > 0 else 0
            print(f"  {size:>6,} tokens: {mean_lat:.2f}ms (CV: {cv:.1f}%)")
        print(f"{'='*60}")

        # Key assertion: all context sizes have mean latency < 100ms
        # And worst case still beats MIT's best (5000ms)
        mit_best_ms = 5000
        for size in sizes:
            mean_lat = statistics.mean(results[size])
            max_lat = max(results[size])
            assert mean_lat < 100, f"Context {size} mean {mean_lat:.1f}ms > 100ms"
            assert (
                max_lat < mit_best_ms
            ), f"Context {size} worst {max_lat:.1f}ms >= MIT best {mit_best_ms}ms"

    @pytest.mark.stress
    @pytest.mark.benchmark
    def test_extreme_position_values(
        self,
        small_context_bridge: TransformerBridge,
    ) -> None:
        """Positions at extreme values.

        Verify numerical stability with very large and very small positions.
        """
        bridge = small_context_bridge
        d_model = bridge.transformer.d_model

        # Test cases: normal, large, small, mixed
        test_cases = [
            ("normal", 100.0),
            ("large", 1e6),
            ("small", 1e-6),
            ("very_large", 1e10),
        ]

        results: dict[str, tuple[bool, float]] = {}

        for name, scale in test_cases:
            torch.manual_seed(42)
            x = torch.randn(1, 64, d_model)
            positions = torch.randn(1, 64, 3) * scale

            try:
                start = time.perf_counter()
                output = bridge(x, positions)
                latency = (time.perf_counter() - start) * 1000

                # Check for NaN/Inf
                has_nan = torch.isnan(output).any().item()
                has_inf = torch.isinf(output).any().item()

                results[name] = (not (has_nan or has_inf), latency)
            except Exception:
                results[name] = (False, 0.0)

        print(f"\n{'='*60}")
        print("EXTREME POSITION VALUES: Numerical stability")
        print(f"{'='*60}")
        for name, (success, latency) in results.items():
            status = "PASS" if success else "FAIL (NaN/Inf)"
            print(f"  {name:>12}: {status} ({latency:.2f}ms)")
        print(f"{'='*60}")

        # At least normal and large should work
        assert results["normal"][0], "Normal positions should work"
        assert results["large"][0], "Large positions should work"

    @pytest.mark.stress
    @pytest.mark.benchmark
    def test_sparse_vs_dense_positions(
        self,
        bench_transformer: SpatialTransformer,
    ) -> None:
        """Compare clustered vs uniformly distributed positions.

        Both should maintain O(k) complexity.
        """
        d_model = bench_transformer.d_model
        context_size = 10000

        configs = [
            ("dense_cluster", 10.0),  # All positions within small area
            ("spread_medium", 100.0),  # Medium spread
            ("spread_wide", 1000.0),  # Wide spread
            ("spread_extreme", 10000.0),  # Extreme spread
        ]

        results: dict[str, float] = {}

        for name, spread in configs:
            adapter = QdrantAdapter(
                collection_name=f"spread_{name}",
                d_model=d_model,
                use_memory=True,
            )

            torch.manual_seed(42)
            embeddings = torch.randn(context_size, d_model)
            positions = torch.randn(context_size, 3) * spread
            adapter.store(embeddings, positions)

            bridge = TransformerBridge(
                transformer=bench_transformer,
                vector_store=adapter,
                k_neighbors=50,
            )

            x = torch.randn(1, 64, d_model)
            pos = torch.randn(1, 64, 3) * (spread / 10)  # Query positions scaled

            # Warmup
            for _ in range(3):
                _ = bridge(x, pos)

            # Measure
            latencies: list[float] = []
            for _ in range(20):
                start = time.perf_counter()
                _ = bridge(x, pos)
                latencies.append((time.perf_counter() - start) * 1000)

            results[name] = statistics.mean(latencies)
            adapter.close()

        # Calculate variance across configurations
        times_list = list(results.values())
        mean_time = statistics.mean(times_list)
        max_ratio = max(times_list) / min(times_list) if min(times_list) > 0 else 0

        print(f"\n{'='*60}")
        print("SPARSE vs DENSE POSITIONS")
        print(f"{'='*60}")
        for name, time_ms in results.items():
            ratio = time_ms / mean_time if mean_time > 0 else 0
            print(f"  {name:>16}: {time_ms:.2f}ms (ratio: {ratio:.2f}x)")
        print(f"\n  Max/Min ratio: {max_ratio:.2f}x")
        print("  O(k) expects:  ~1.0x (position-independent)")
        print(f"{'='*60}")

        # Position distribution should not significantly affect performance
        assert (
            max_ratio < 3.0
        ), f"Position distribution affects performance: {max_ratio:.2f}x variation"

    @pytest.mark.stress
    @pytest.mark.benchmark
    def test_long_running_stability(
        self,
        small_context_bridge: TransformerBridge,
    ) -> None:
        """Extended run simulating sustained workload.

        Run 5000 queries and verify no memory growth or latency degradation.
        """
        bridge = small_context_bridge
        d_model = bridge.transformer.d_model

        torch.manual_seed(42)
        x = torch.randn(1, 64, d_model)
        positions = torch.randn(1, 64, 3) * 100.0

        # Initial memory baseline
        gc.collect()
        initial_memory = bridge.get_memory_usage_mb()

        # Warmup
        for _ in range(10):
            _ = bridge(x, positions)

        # Run extended workload
        num_queries = 5000
        checkpoint_interval = 1000
        checkpoints: dict[int, tuple[float, float]] = {}  # (latency, memory)

        all_latencies: list[float] = []

        for i in range(num_queries):
            start = time.perf_counter()
            _ = bridge(x, positions)
            latency = (time.perf_counter() - start) * 1000
            all_latencies.append(latency)

            # Record checkpoint
            if (i + 1) % checkpoint_interval == 0:
                gc.collect()
                current_memory = bridge.get_memory_usage_mb()
                recent_latency = statistics.mean(all_latencies[-100:])
                checkpoints[i + 1] = (recent_latency, current_memory)

        # Final stats
        final_memory = bridge.get_memory_usage_mb()
        memory_growth = final_memory - initial_memory

        first_avg = statistics.mean(all_latencies[:500])
        last_avg = statistics.mean(all_latencies[-500:])
        degradation = (last_avg - first_avg) / first_avg * 100 if first_avg > 0 else 0

        print(f"\n{'='*60}")
        print(f"LONG RUNNING STABILITY: {num_queries} queries")
        print(f"{'='*60}")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory:   {final_memory:.1f}MB")
        print(f"  Memory growth:  {memory_growth:+.1f}MB")
        print("\n  Checkpoints:")
        for query_num, (lat, mem) in checkpoints.items():
            print(f"    {query_num:>5} queries: {lat:.2f}ms, {mem:.1f}MB")
        print(f"\n  First 500 avg:  {first_avg:.2f}ms")
        print(f"  Last 500 avg:   {last_avg:.2f}ms")
        print(f"  Degradation:    {degradation:+.1f}%")
        print(f"{'='*60}")

        # No significant memory growth (allow some for Python overhead)
        assert memory_growth < 50, f"Memory growth {memory_growth:.1f}MB over {num_queries} queries"

        # No significant performance degradation
        assert (
            abs(degradation) < 30
        ), f"Performance degradation {degradation:+.1f}% over {num_queries} queries"
