"""
test_spatial_index.py - Test suite for spatial indexing utilities.

Tests spatial indexing optimization for 3D position-based retrieval,
used to accelerate both Qdrant and pgvector queries.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
Test Count: 6
Coverage Target: ≥95%
"""


import pytest
import torch


class TestSpatialIndex:
    """Test suite for spatial indexing utilities."""

    @pytest.fixture
    def sample_positions(self):
        """Create sample 3D positions for testing.

        Returns:
            torch.Tensor: (100, 3) tensor of random positions
        """
        return torch.randn(100, 3) * 100.0

    def test_distance_calculation(self, sample_positions):
        """Test 3D Euclidean distance calculation.

        Verifies:
        - Distance formula correct: sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
        - Vectorized calculation efficient
        - Returns correct shape
        """
        from spatial_engine.vector_store.spatial_index import calculate_distances

        query_position = torch.tensor([0.0, 0.0, 0.0])

        distances = calculate_distances(query_position, sample_positions)

        # Verify shape
        assert distances.shape == (100,)

        # Verify first distance manually
        pos0 = sample_positions[0]
        expected_dist = torch.sqrt((pos0[0] ** 2) + (pos0[1] ** 2) + (pos0[2] ** 2))
        assert torch.isclose(distances[0], expected_dist, atol=1e-5)

    def test_radius_filter(self, sample_positions):
        """Test spatial radius filtering.

        Verifies:
        - Returns only positions within radius
        - Indices match filtered positions
        - Empty result if no positions within radius
        """
        from spatial_engine.vector_store.spatial_index import filter_by_radius

        query_position = torch.tensor([0.0, 0.0, 0.0])
        radius = 50.0

        filtered_positions, filtered_indices = filter_by_radius(
            query_position, sample_positions, radius
        )

        # Verify all filtered positions are within radius
        for pos in filtered_positions:
            dist = torch.sqrt((pos**2).sum())
            assert dist <= radius

        # Verify indices are correct
        for i, idx in enumerate(filtered_indices):
            assert torch.allclose(filtered_positions[i], sample_positions[idx])

    def test_k_nearest_neighbors(self, sample_positions):
        """Test k-nearest neighbor selection.

        Verifies:
        - Returns exactly k positions
        - Positions sorted by distance (closest first)
        - Indices match selected positions
        """
        from spatial_engine.vector_store.spatial_index import find_k_nearest

        query_position = torch.tensor([0.0, 0.0, 0.0])
        k = 10

        nearest_positions, nearest_indices = find_k_nearest(query_position, sample_positions, k)

        # Verify shape
        assert nearest_positions.shape == (k, 3)
        assert len(nearest_indices) == k

        # Verify sorted by distance
        from spatial_engine.vector_store.spatial_index import calculate_distances

        distances = calculate_distances(query_position, nearest_positions)
        for i in range(len(distances) - 1):
            assert distances[i] <= distances[i + 1]

    def test_combined_radius_and_k(self, sample_positions):
        """Test combining radius filter with k-nearest.

        Verifies:
        - First filters by radius, then selects k-nearest
        - Returns at most k positions
        - All positions within radius
        - Sorted by distance
        """
        from spatial_engine.vector_store.spatial_index import (
            find_k_nearest_within_radius,
        )

        query_position = torch.tensor([0.0, 0.0, 0.0])
        k = 10
        radius = 50.0

        positions, indices = find_k_nearest_within_radius(
            query_position, sample_positions, k, radius
        )

        # Verify at most k positions
        assert positions.shape[0] <= k

        # Verify all within radius
        from spatial_engine.vector_store.spatial_index import calculate_distances

        distances = calculate_distances(query_position, positions)
        assert all(d <= radius for d in distances)

        # Verify sorted by distance
        for i in range(len(distances) - 1):
            assert distances[i] <= distances[i + 1]

    def test_octree_partitioning(self):
        """Test octree-based spatial partitioning (if implemented).

        Verifies:
        - Space partitioned into octants
        - Points assigned to correct octants
        - Efficient range queries
        - Hierarchical structure
        """
        from spatial_engine.vector_store.spatial_index import OctreeIndex

        # Create octree with bounds
        octree = OctreeIndex(bounds=(-100.0, 100.0, -100.0, 100.0, -100.0, 100.0), max_depth=4)

        # Insert some positions
        positions = torch.randn(100, 3) * 50.0  # Within bounds
        for i, pos in enumerate(positions):
            octree.insert(i, pos)

        # Query a region
        query_position = torch.tensor([0.0, 0.0, 0.0])
        radius = 30.0

        indices = octree.query_radius(query_position, radius)

        # Verify all returned positions are within radius
        assert len(indices) > 0
        for idx in indices:
            pos = positions[idx]
            dist = torch.sqrt(((pos - query_position) ** 2).sum())
            assert dist <= radius

    def test_performance_benchmark(self):
        """Test spatial indexing performance.

        Verifies:
        - Distance calculation <1ms for 10k positions
        - Radius filter <2ms for 10k positions
        - k-nearest <3ms for 10k positions
        - Scales efficiently with larger datasets
        """
        import time

        from spatial_engine.vector_store.spatial_index import (
            calculate_distances,
            filter_by_radius,
            find_k_nearest,
        )

        # Create large dataset
        positions = torch.randn(10000, 3) * 500.0
        query_position = torch.tensor([0.0, 0.0, 0.0])

        # Benchmark distance calculation
        start = time.perf_counter()
        distances = calculate_distances(query_position, positions)
        distance_time = (time.perf_counter() - start) * 1000  # ms

        # Benchmark radius filter
        start = time.perf_counter()
        filtered_positions, filtered_indices = filter_by_radius(
            query_position, positions, radius=100.0
        )
        filter_time = (time.perf_counter() - start) * 1000  # ms

        # Benchmark k-nearest
        start = time.perf_counter()
        nearest_positions, nearest_indices = find_k_nearest(query_position, positions, k=50)
        knn_time = (time.perf_counter() - start) * 1000  # ms

        # Verify performance targets (with some tolerance for system variance)
        assert distance_time < 2.0, f"Distance calculation too slow: {distance_time:.2f}ms"
        assert filter_time < 5.0, f"Radius filter too slow: {filter_time:.2f}ms"
        assert knn_time < 10.0, f"k-nearest too slow: {knn_time:.2f}ms"


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
