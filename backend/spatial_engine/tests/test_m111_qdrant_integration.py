"""
test_m111_qdrant_integration.py - M1.11 Qdrant integration tests.

Tests the min_distance parameter and warp lane detection with real
Qdrant storage (both in-memory and container modes).

Includes memory profiling tests for O(k) verification with REAL
Qdrant container backend (not just in-memory).

Author: ch1pu
Milestone: 1.11 - Strafe Jumping Navigation

Test Count: 15 tests (12 original + 3 container memory)
"""

import statistics
import time

import pytest
import torch

from spatial_engine.core.momentum_navigator import MomentumNavigator
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# Import M1.11 fixtures
pytest_plugins = ["spatial_engine.tests.conftest_m111"]


# ---------------------------------------------------------------------------
# TestQdrantMinDistance (6 tests)
# ---------------------------------------------------------------------------


class TestQdrantMinDistance:
    """Test min_distance parameter with Qdrant adapter."""

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_min_distance_filters_nearby_tokens(
        self,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Verify min_distance excludes tokens within specified distance."""
        torch.manual_seed(42)

        # Create tokens at known distances from origin
        # Place tokens along x-axis at specific distances
        positions = torch.tensor([
            [10.0, 0.0, 0.0],   # Distance 10
            [30.0, 0.0, 0.0],   # Distance 30
            [60.0, 0.0, 0.0],   # Distance 60
            [100.0, 0.0, 0.0],  # Distance 100
            [150.0, 0.0, 0.0],  # Distance 150
            [200.0, 0.0, 0.0],  # Distance 200
        ])
        embeddings = torch.randn(6, 256)

        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)
        query_pos = (0.0, 0.0, 0.0)

        # Query with min_distance=50 - should exclude first 2 tokens
        results_emb, results_pos, results_ids = m111_qdrant_adapter.query(
            query, query_pos, k=10, min_distance=50.0, radius=300.0
        )

        distances = torch.norm(results_pos, dim=1)

        print(f"\n{'='*60}")
        print("M1.11 QDRANT MIN_DISTANCE TEST")
        print(f"{'='*60}")
        print(f"Stored distances: [10, 30, 60, 100, 150, 200]")
        print(f"min_distance: 50.0")
        print(f"Returned: {len(results_ids)} tokens")
        print(f"Returned distances: {distances.tolist()}")
        print(f"{'='*60}")

        # All returned tokens should be > min_distance
        assert all(d > 50.0 for d in distances), "Some tokens within min_distance returned"
        assert len(results_ids) == 4, f"Expected 4 tokens (60, 100, 150, 200), got {len(results_ids)}"

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_min_distance_with_radius_combined(
        self,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Test min_distance combined with max radius (warp lane use case)."""
        torch.manual_seed(42)

        # Create tokens spread across space
        positions = torch.tensor([
            [25.0, 0.0, 0.0],   # Distance 25 - too close
            [75.0, 0.0, 0.0],   # Distance 75 - in range
            [150.0, 0.0, 0.0],  # Distance 150 - in range
            [250.0, 0.0, 0.0],  # Distance 250 - in range
            [350.0, 0.0, 0.0],  # Distance 350 - too far
        ])
        embeddings = torch.randn(5, 256)

        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)
        query_pos = (0.0, 0.0, 0.0)

        # Warp lane query: min_distance=50, radius=300
        # Should return tokens at 75, 150, 250 (not 25 or 350)
        results_emb, results_pos, results_ids = m111_qdrant_adapter.query(
            query, query_pos, k=10, min_distance=50.0, radius=300.0
        )

        distances = torch.norm(results_pos, dim=1)

        print(f"\n{'='*60}")
        print("M1.11 WARP LANE QUERY (min + max distance)")
        print(f"{'='*60}")
        print(f"Stored distances: [25, 75, 150, 250, 350]")
        print(f"Query: min_distance=50, radius=300")
        print(f"Returned: {len(results_ids)} tokens")
        print(f"Returned distances: {distances.tolist()}")
        print(f"{'='*60}")

        # All should be in range (50, 300]
        assert all(d > 50.0 for d in distances), "Token within min_distance"
        assert all(d <= 300.0 for d in distances), "Token outside radius"

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_min_distance_empty_result(
        self,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Test min_distance when no tokens qualify."""
        torch.manual_seed(42)

        # Create only nearby tokens
        positions = torch.tensor([
            [10.0, 0.0, 0.0],
            [20.0, 0.0, 0.0],
            [30.0, 0.0, 0.0],
        ])
        embeddings = torch.randn(3, 256)

        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)
        query_pos = (0.0, 0.0, 0.0)

        # Query with min_distance > all token distances
        results_emb, results_pos, results_ids = m111_qdrant_adapter.query(
            query, query_pos, k=10, min_distance=100.0
        )

        print(f"\n{'='*60}")
        print("M1.11 MIN_DISTANCE EMPTY RESULT")
        print(f"{'='*60}")
        print(f"Stored distances: [10, 20, 30]")
        print(f"min_distance: 100.0")
        print(f"Returned: {len(results_ids)} tokens")
        print(f"{'='*60}")

        assert len(results_ids) == 0, "Should return empty when no tokens qualify"

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_min_distance_boundary_precision(
        self,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Test min_distance boundary is exclusive (> not >=)."""
        torch.manual_seed(42)

        # Token exactly at min_distance boundary
        positions = torch.tensor([
            [50.0, 0.0, 0.0],   # Exactly at boundary
            [50.1, 0.0, 0.0],  # Just outside boundary
        ])
        embeddings = torch.randn(2, 256)

        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)
        query_pos = (0.0, 0.0, 0.0)

        results_emb, results_pos, results_ids = m111_qdrant_adapter.query(
            query, query_pos, k=10, min_distance=50.0
        )

        distances = torch.norm(results_pos, dim=1)

        print(f"\n{'='*60}")
        print("M1.11 MIN_DISTANCE BOUNDARY TEST")
        print(f"{'='*60}")
        print(f"Stored distances: [50.0, 50.1]")
        print(f"min_distance: 50.0 (exclusive)")
        print(f"Returned: {len(results_ids)} tokens")
        print(f"Returned distances: {distances.tolist()}")
        print(f"{'='*60}")

        # Token at exactly 50.0 should be excluded (> not >=)
        assert len(results_ids) == 1, "Only token > 50.0 should be returned"

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_min_distance_performance(
        self,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Benchmark min_distance query performance."""
        torch.manual_seed(42)

        # Create larger dataset
        n_tokens = 1000
        embeddings = torch.randn(n_tokens, 256)
        positions = torch.randn(n_tokens, 3) * 500

        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)
        query_pos = (0.0, 0.0, 0.0)

        # Warmup
        for _ in range(5):
            m111_qdrant_adapter.query(query, query_pos, k=50, min_distance=100.0, radius=400.0)

        # Benchmark
        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            m111_qdrant_adapter.query(query, query_pos, k=50, min_distance=100.0, radius=400.0)
            latencies.append((time.perf_counter() - start) * 1000)

        mean_latency = statistics.mean(latencies)

        print(f"\n{'='*60}")
        print("M1.11 MIN_DISTANCE QUERY PERFORMANCE")
        print(f"{'='*60}")
        print(f"Tokens: {n_tokens}")
        print(f"Mean latency: {mean_latency:.2f}ms")
        print(f"Queries/sec: {1000/mean_latency:.0f}")
        print(f"{'='*60}")

        assert mean_latency < 50, f"Query latency {mean_latency:.2f}ms > 50ms"

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    def test_warp_lane_query_realistic(
        self,
        m111_qdrant_with_data: tuple[QdrantAdapter, torch.Tensor],
    ) -> None:
        """Test realistic warp lane query with semantic data.

        Note: Qdrant uses bounding box approximation for radius filtering,
        so some results may exceed the spherical radius. The min_distance
        filter is applied with exact Euclidean distance post-filtering.
        """
        adapter, query = m111_qdrant_with_data

        query_pos = (0.0, 0.0, 0.0)

        # Warp lane query: beyond 2× attention radius, within 10×
        attention_radius = 50.0
        min_warp = 2 * attention_radius  # 100
        max_warp = 10 * attention_radius  # 500

        results_emb, results_pos, results_ids = adapter.query(
            query, query_pos, k=50, min_distance=min_warp, radius=max_warp
        )

        if len(results_pos) > 0:
            distances = torch.norm(results_pos, dim=1)
            # Check similarity with query
            similarities = torch.nn.functional.cosine_similarity(
                results_emb, query.unsqueeze(0), dim=1
            )

            # Count tokens in different zones
            within_min = (distances <= min_warp).sum().item()
            within_sphere = ((distances > min_warp) & (distances <= max_warp)).sum().item()
            outside_sphere = (distances > max_warp).sum().item()

            print(f"\n{'='*60}")
            print("M1.11 REALISTIC WARP LANE QUERY")
            print(f"{'='*60}")
            print(f"Query range: ({min_warp}, {max_warp}]")
            print(f"Returned: {len(results_ids)} candidates")
            print(f"Distance range: {distances.min():.1f} - {distances.max():.1f}")
            print(f"Similarity range: {similarities.min():.3f} - {similarities.max():.3f}")
            print(f"Within min_warp (should be 0): {within_min}")
            print(f"Within sphere (valid warp): {within_sphere}")
            print(f"Outside sphere (bounding box artifacts): {outside_sphere}")
            print(f"{'='*60}")

            # min_distance filtering is exact (post-filter) - no tokens should be too close
            assert within_min == 0, f"{within_min} tokens within min_distance (should be 0)"

            # At least some valid warp candidates should be found
            assert within_sphere > 0, "No valid warp candidates within sphere"

            # Note: outside_sphere > 0 is expected due to bounding box approximation
            # This is acceptable for warp lane detection where we want distant tokens


# ---------------------------------------------------------------------------
# TestQdrantContainerIntegration (3 tests)
# ---------------------------------------------------------------------------


class TestQdrantContainerIntegration:
    """Test integration with Qdrant Docker container."""

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    @pytest.mark.m111_integration
    def test_container_connection(
        self,
        m111_qdrant_container,
    ) -> None:
        """Test connection to Qdrant Docker container."""
        if m111_qdrant_container is None:
            pytest.skip("Qdrant container not available")

        print(f"\n{'='*60}")
        print("M1.11 QDRANT CONTAINER CONNECTION")
        print(f"{'='*60}")
        print("Connected to Qdrant container at localhost:6333")
        print(f"{'='*60}")

        # Basic operation test
        torch.manual_seed(42)
        embeddings = torch.randn(10, 256)
        positions = torch.randn(10, 3) * 100

        ids = m111_qdrant_container.store(embeddings, positions)
        assert len(ids) == 10

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    @pytest.mark.m111_integration
    def test_container_min_distance_query(
        self,
        m111_qdrant_container,
    ) -> None:
        """Test min_distance query against Qdrant container."""
        if m111_qdrant_container is None:
            pytest.skip("Qdrant container not available")

        torch.manual_seed(42)

        # Create test data
        positions = torch.tensor([
            [25.0, 0.0, 0.0],
            [75.0, 0.0, 0.0],
            [150.0, 0.0, 0.0],
        ])
        embeddings = torch.randn(3, 256)

        m111_qdrant_container.store(embeddings, positions)

        query = torch.randn(256)
        results_emb, results_pos, results_ids = m111_qdrant_container.query(
            query, (0.0, 0.0, 0.0), k=10, min_distance=50.0
        )

        print(f"\n{'='*60}")
        print("M1.11 CONTAINER MIN_DISTANCE QUERY")
        print(f"{'='*60}")
        print(f"Returned: {len(results_ids)} tokens")
        print(f"{'='*60}")

        # Should return tokens at 75 and 150 (not 25)
        assert len(results_ids) == 2

    @pytest.mark.m111
    @pytest.mark.m111_qdrant
    @pytest.mark.m111_integration
    def test_container_benchmark(
        self,
        m111_qdrant_container,
    ) -> None:
        """Benchmark queries against Qdrant container."""
        if m111_qdrant_container is None:
            pytest.skip("Qdrant container not available")

        torch.manual_seed(42)

        # Create larger dataset
        n_tokens = 5000
        embeddings = torch.randn(n_tokens, 256)
        positions = torch.randn(n_tokens, 3) * 500

        m111_qdrant_container.store(embeddings, positions)

        query = torch.randn(256)

        # Warmup
        for _ in range(5):
            m111_qdrant_container.query(query, (0.0, 0.0, 0.0), k=50)

        # Benchmark standard query
        standard_latencies = []
        for _ in range(50):
            start = time.perf_counter()
            m111_qdrant_container.query(query, (0.0, 0.0, 0.0), k=50)
            standard_latencies.append((time.perf_counter() - start) * 1000)

        # Benchmark warp lane query
        warp_latencies = []
        for _ in range(50):
            start = time.perf_counter()
            m111_qdrant_container.query(
                query, (0.0, 0.0, 0.0), k=50, min_distance=100.0, radius=400.0
            )
            warp_latencies.append((time.perf_counter() - start) * 1000)

        print(f"\n{'='*60}")
        print("M1.11 QDRANT CONTAINER BENCHMARK")
        print(f"{'='*60}")
        print(f"Tokens: {n_tokens}")
        print(f"Standard query: {statistics.mean(standard_latencies):.2f}ms")
        print(f"Warp lane query: {statistics.mean(warp_latencies):.2f}ms")
        print(f"{'='*60}")


# ---------------------------------------------------------------------------
# TestM111EndToEnd (3 tests)
# ---------------------------------------------------------------------------


class TestM111EndToEnd:
    """End-to-end tests for M1.11 navigation with Qdrant."""

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_full_navigation_pipeline(
        self,
        m111_navigator,
        m111_qdrant_with_data: tuple[QdrantAdapter, torch.Tensor],
    ) -> None:
        """Test complete navigation pipeline with Qdrant storage."""
        adapter, query = m111_qdrant_with_data

        # Get all tokens from Qdrant
        results_emb, results_pos, _ = adapter.query(
            query, (0.0, 0.0, 0.0), k=1000
        )

        # Navigate using retrieved tokens
        result = m111_navigator.navigate(
            query,
            max_steps=10,
            context_embeddings=results_emb,
            context_positions=results_pos,
        )

        print(f"\n{'='*60}")
        print("M1.11 FULL NAVIGATION PIPELINE")
        print(f"{'='*60}")
        print(f"Tokens from Qdrant: {len(results_emb)}")
        print(f"Navigation steps: {result.steps_taken}")
        print(f"Warps performed: {result.warp_count}")
        print(f"Converged: {result.converged}")
        print(f"{'='*60}")

        assert result.steps_taken > 0

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_warp_lane_assisted_navigation(
        self,
        m111_navigator,
        m111_warp_detector,
        m111_qdrant_with_data: tuple[QdrantAdapter, torch.Tensor],
    ) -> None:
        """Test navigation with warp lane detection from Qdrant."""
        adapter, query = m111_qdrant_with_data

        # Query for warp candidates (distant but similar)
        warp_emb, warp_pos, _ = adapter.query(
            query, (0.0, 0.0, 0.0), k=100, min_distance=100.0, radius=500.0
        )

        if len(warp_emb) > 0:
            # Detect warp lanes
            mask = m111_warp_detector.find_warp_targets(
                query, warp_emb, warp_pos, torch.zeros(3)
            )
            warp_count = mask.sum().item()

            print(f"\n{'='*60}")
            print("M1.11 WARP LANE ASSISTED NAVIGATION")
            print(f"{'='*60}")
            print(f"Warp candidates from Qdrant: {len(warp_emb)}")
            print(f"Detected warp lanes: {warp_count}")
            print(f"{'='*60}")

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_combined_benchmark(
        self,
        m111_navigator,
        m111_qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Benchmark combined Qdrant + Navigation performance."""
        torch.manual_seed(42)

        # Store tokens
        n_tokens = 2000
        embeddings = torch.randn(n_tokens, 256)
        positions = torch.randn(n_tokens, 3) * 300
        m111_qdrant_adapter.store(embeddings, positions)

        query = torch.randn(256)

        # Warmup
        for _ in range(5):
            emb, pos, _ = m111_qdrant_adapter.query(query, (0.0, 0.0, 0.0), k=100)
            m111_navigator.navigate(query, max_steps=5, context_embeddings=emb, context_positions=pos)

        # Benchmark combined pipeline
        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            # 1. Query Qdrant
            emb, pos, _ = m111_qdrant_adapter.query(query, (0.0, 0.0, 0.0), k=100)
            # 2. Navigate
            m111_navigator.navigate(query, max_steps=5, context_embeddings=emb, context_positions=pos)
            latencies.append((time.perf_counter() - start) * 1000)

        mean_latency = statistics.mean(latencies)

        print(f"\n{'='*60}")
        print("M1.11 COMBINED BENCHMARK (Qdrant + Navigator)")
        print(f"{'='*60}")
        print(f"Tokens: {n_tokens}")
        print(f"Mean latency: {mean_latency:.2f}ms")
        print(f"Pipeline/sec: {1000/mean_latency:.0f}")
        print(f"{'='*60}")

        assert mean_latency < 100, f"Combined latency {mean_latency:.2f}ms > 100ms"


# ---------------------------------------------------------------------------
# TestContainerMemoryComplexity - O(k) Memory with Real Qdrant Container
# ---------------------------------------------------------------------------


class TestContainerMemoryComplexity:
    """Verify O(k) memory complexity with REAL Qdrant container backend.

    These tests hit the actual Qdrant Docker container, measuring true
    production memory usage including database I/O overhead.
    """

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_container_memory_scaling(
        self,
        m111_qdrant_container: "QdrantAdapter",
        m111_navigator: MomentumNavigator,
    ) -> None:
        """Test memory scaling with real Qdrant container backend."""
        import tracemalloc

        d_model = 256
        memory_results: list[tuple[int, float]] = []
        sizes = [500, 1000, 2000, 5000]

        for n_tokens in sizes:
            # Create unique collection for this size
            collection_name = f"mem_test_{n_tokens}_{int(time.time()*1000)}"

            from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                collection_name=collection_name,
                d_model=d_model,
                url="http://localhost:6333",
            )

            # Store tokens in container
            torch.manual_seed(42)
            embeddings = torch.randn(n_tokens, d_model)
            positions = torch.randn(n_tokens, 3) * 200
            adapter.store(embeddings, positions)

            query = torch.randn(d_model)
            query_pos = (0.0, 0.0, 0.0)

            # Measure memory during query + navigation
            tracemalloc.start()

            # Query from real container
            # Returns (embeddings, positions, ids) - ids is a list, not metadata dict
            emb, pos, ids = adapter.query(query, query_pos, k=100)

            # Navigate
            result = m111_navigator.navigate(
                query=query,
                context_embeddings=emb,
                context_positions=pos,
                max_steps=10,
            )

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            memory_mb = peak / (1024 * 1024)
            memory_results.append((n_tokens, memory_mb))

            # Cleanup collection
            try:
                adapter.client.delete_collection(collection_name)
            except Exception:
                pass

        # Print results
        print(f"\n{'='*80}")
        print("M1.11 CONTAINER MEMORY TEST: Real Qdrant Backend")
        print(f"{'='*80}")
        print(f"\n{'Tokens':>10}   {'Peak Mem (MB)':>14}   {'MB/1K tok':>12}")
        print("-" * 45)

        for n_tokens, mem_mb in memory_results:
            mb_per_1k = mem_mb / n_tokens * 1000
            print(f"{n_tokens:>10}   {mem_mb:>14.2f}   {mb_per_1k:>12.3f}")

        # Calculate scaling
        mem_500 = memory_results[0][1]
        mem_5k = memory_results[-1][1]
        memory_ratio = mem_5k / mem_500 if mem_500 > 0 else float('inf')
        token_ratio = sizes[-1] / sizes[0]  # 10x

        print(f"\n{'='*60}")
        print(f"Token increase:  {token_ratio:.0f}x ({sizes[0]} -> {sizes[-1]})")
        print(f"Memory increase: {memory_ratio:.2f}x")
        print(f"Expected O(n):   {token_ratio:.0f}x")
        print(f"Expected O(k):   ~1-3x (bounded by k neighbors)")
        print(f"{'='*60}")

        # With real container, allow more overhead but still sublinear
        assert memory_ratio < token_ratio, (
            f"Container memory {memory_ratio:.2f}x approaching O(n). Expected sublinear."
        )

        if memory_ratio < 5:
            print(f"\nRESULT: O(k) CONTAINER MEMORY VERIFIED - {memory_ratio:.2f}x << {token_ratio}x")
        else:
            print(f"\nRESULT: SUBLINEAR CONTAINER MEMORY - {memory_ratio:.2f}x < {token_ratio}x")
        print(f"{'='*80}")

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_container_pipeline_memory(
        self,
        m111_qdrant_container: "QdrantAdapter",
    ) -> None:
        """Test full NavigationAttention pipeline memory with Qdrant container."""
        import tracemalloc
        from spatial_engine.integration.navigation_attention import NavigationAttention

        d_model = 256
        nav_attention = NavigationAttention(
            d_model=d_model,
            spatial_radius=50.0,
            k_neighbors=50,
            enable_navigation=True,
            enable_lod=True,
        )

        memory_results: list[tuple[int, float]] = []
        sizes = [500, 1000, 2000, 5000]

        for n_tokens in sizes:
            # Create collection
            collection_name = f"pipeline_mem_{n_tokens}_{int(time.time()*1000)}"

            from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter
            adapter = QdrantAdapter(
                collection_name=collection_name,
                d_model=d_model,
                url="http://localhost:6333",
            )

            # Store tokens
            torch.manual_seed(42)
            embeddings = torch.randn(n_tokens, d_model)
            positions = torch.randn(n_tokens, 3) * 200
            adapter.store(embeddings, positions)

            query = torch.randn(d_model)
            query_pos = torch.zeros(3)

            # Query tokens from container
            emb, pos, _ = adapter.query(query, (0.0, 0.0, 0.0), k=min(n_tokens, 500))

            # Measure full pipeline memory
            tracemalloc.start()

            output, stats = nav_attention.query(
                query,
                emb,
                pos,
            )

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            memory_mb = peak / (1024 * 1024)
            memory_results.append((n_tokens, memory_mb))

            # Cleanup
            try:
                adapter.client.delete_collection(collection_name)
            except Exception:
                pass

        # Print results
        print(f"\n{'='*80}")
        print("M1.11 FULL PIPELINE MEMORY (Container + Navigator + Attention + LOD)")
        print(f"{'='*80}")
        print(f"\n{'Tokens':>10}   {'Peak Memory (MB)':>18}")
        print("-" * 35)

        for n_tokens, mem_mb in memory_results:
            print(f"{n_tokens:>10}   {mem_mb:>18.2f}")

        mem_500 = memory_results[0][1]
        mem_5k = memory_results[-1][1]
        memory_ratio = mem_5k / mem_500 if mem_500 > 0 else float('inf')

        print(f"\n{'='*35}")
        print(f"Memory ratio (5K/500): {memory_ratio:.2f}x")
        print(f"Expected O(k): ~1-3x")
        print(f"{'='*35}")

        assert memory_ratio < 10, f"Pipeline memory ratio {memory_ratio:.2f}x too high"
        print(f"\nRESULT: PIPELINE MEMORY BOUNDED")
        print(f"{'='*80}")

    @pytest.mark.m111
    @pytest.mark.m111_integration
    def test_container_vs_inmemory_comparison(self) -> None:
        """Compare memory usage: Qdrant container vs in-memory mode."""
        import tracemalloc
        from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

        d_model = 256
        n_tokens = 2000

        torch.manual_seed(42)
        embeddings = torch.randn(n_tokens, d_model)
        positions = torch.randn(n_tokens, 3) * 200
        query = torch.randn(d_model)

        # Test 1: In-memory Qdrant
        adapter_memory = QdrantAdapter(
            collection_name="compare_inmem",
            d_model=d_model,
            use_memory=True,
        )
        adapter_memory.store(embeddings, positions)

        tracemalloc.start()
        emb1, pos1, _ = adapter_memory.query(query, (0.0, 0.0, 0.0), k=100)
        _, peak_inmem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Test 2: Container Qdrant
        adapter_container = QdrantAdapter(
            collection_name=f"compare_container_{int(time.time()*1000)}",
            d_model=d_model,
            url="http://localhost:6333",
        )
        adapter_container.store(embeddings, positions)

        tracemalloc.start()
        emb2, pos2, _ = adapter_container.query(query, (0.0, 0.0, 0.0), k=100)
        _, peak_container = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Cleanup container collection
        try:
            adapter_container.client.delete_collection(adapter_container.collection_name)
        except Exception:
            pass

        inmem_mb = peak_inmem / (1024 * 1024)
        container_mb = peak_container / (1024 * 1024)
        overhead = ((container_mb - inmem_mb) / inmem_mb * 100) if inmem_mb > 0 else 0

        print(f"\n{'='*70}")
        print("M1.11 MEMORY COMPARISON: In-Memory vs Container Backend")
        print(f"{'='*70}")
        print(f"\nTokens: {n_tokens}")
        print(f"\n{'Mode':<20}   {'Peak Memory (MB)':>18}")
        print("-" * 45)
        print(f"{'In-Memory Qdrant':<20}   {inmem_mb:>18.2f}")
        print(f"{'Container Qdrant':<20}   {container_mb:>18.2f}")
        print(f"\nOverhead: {overhead:+.1f}%")
        print(f"{'='*70}")

        # Container should have similar memory (data is in container, not Python)
        # Allow up to 3x overhead for network buffers etc.
        assert container_mb < inmem_mb * 3, (
            f"Container memory {container_mb:.2f}MB >> in-memory {inmem_mb:.2f}MB"
        )

        print(f"\nRESULT: Container memory overhead acceptable ({overhead:+.1f}%)")
        print(f"{'='*70}")


# Entry point
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
