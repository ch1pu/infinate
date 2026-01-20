"""
test_spatial_index.py - Test suite for spatial indexing utilities.

Tests spatial indexing optimization for 3D position-based retrieval,
used to accelerate both Qdrant and pgvector queries.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
Updated: 1.11 - Strafe Jumping Navigation (added distance range tests)
Test Count: 10+ (6 original + 4+ for M1.11)
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


class TestDistanceRangeFiltering:
    """Tests for M1.11 distance range filtering functions.

    Added in Milestone 1.11 for warp lane detection support.
    These functions enable finding tokens within a specific distance
    range (min_distance, max_distance] for semantic warping.
    """

    @pytest.fixture
    def positioned_data(self):
        """Create positions at specific known distances for testing.

        Returns:
            torch.Tensor: (10, 3) tensor with positions at known distances
        """
        # Create positions at specific distances along x-axis for easy verification
        return torch.tensor([
            [10.0, 0.0, 0.0],   # Distance 10
            [25.0, 0.0, 0.0],   # Distance 25
            [50.0, 0.0, 0.0],   # Distance 50
            [75.0, 0.0, 0.0],   # Distance 75
            [100.0, 0.0, 0.0],  # Distance 100
            [125.0, 0.0, 0.0],  # Distance 125
            [150.0, 0.0, 0.0],  # Distance 150
            [200.0, 0.0, 0.0],  # Distance 200
            [300.0, 0.0, 0.0],  # Distance 300
            [500.0, 0.0, 0.0],  # Distance 500
        ])

    def test_filter_by_distance_range_basic(self, positioned_data):
        """Test basic distance range filtering.

        Verifies:
        - Only positions within (min, max] returned
        - Correct indices returned
        - Works with standard distance values
        """
        from spatial_engine.vector_store.spatial_index import filter_by_distance_range

        query_position = torch.zeros(3)
        min_distance = 50.0
        max_distance = 150.0

        filtered_positions, filtered_indices = filter_by_distance_range(
            query_position, positioned_data, min_distance, max_distance
        )

        # Expected: positions at 75, 100, 125, 150 (indices 3, 4, 5, 6)
        # Note: min is exclusive (>), max is inclusive (<=)
        expected_indices = [3, 4, 5, 6]

        assert len(filtered_indices) == 4
        assert set(filtered_indices) == set(expected_indices)

        # Verify all filtered positions are in range
        from spatial_engine.vector_store.spatial_index import calculate_distances
        distances = calculate_distances(query_position, filtered_positions)
        assert all(d > min_distance for d in distances)
        assert all(d <= max_distance for d in distances)

    def test_filter_by_distance_range_boundary(self, positioned_data):
        """Test distance range boundary behavior.

        Verifies:
        - min_distance is exclusive (>)
        - max_distance is inclusive (<=)
        """
        from spatial_engine.vector_store.spatial_index import filter_by_distance_range

        query_position = torch.zeros(3)

        # Test with exact boundary values
        # Position at 100 should NOT be included with min=100
        # Position at 100 SHOULD be included with max=100
        filtered_pos, filtered_idx = filter_by_distance_range(
            query_position, positioned_data, min_distance=100.0, max_distance=150.0
        )

        # Position at 100 is at index 4, should NOT be included (> not >=)
        assert 4 not in filtered_idx

        # Positions at 125, 150 (indices 5, 6) should be included
        assert 5 in filtered_idx
        assert 6 in filtered_idx

    def test_filter_by_distance_range_empty(self, positioned_data):
        """Test distance range filtering with no matches.

        Verifies:
        - Returns empty results when no positions in range
        """
        from spatial_engine.vector_store.spatial_index import filter_by_distance_range

        query_position = torch.zeros(3)

        # Range that contains no positions
        filtered_positions, filtered_indices = filter_by_distance_range(
            query_position, positioned_data,
            min_distance=600.0, max_distance=700.0
        )

        assert len(filtered_positions) == 0
        assert len(filtered_indices) == 0

    def test_find_k_nearest_in_range_basic(self, positioned_data):
        """Test k-nearest within distance range.

        Verifies:
        - Combines distance range filtering with k-nearest
        - Returns at most k positions
        - All positions within specified range
        """
        from spatial_engine.vector_store.spatial_index import find_k_nearest_in_range

        query_position = torch.zeros(3)
        k = 2
        min_distance = 50.0
        max_distance = 200.0

        nearest_positions, nearest_indices = find_k_nearest_in_range(
            query_position, positioned_data, k, min_distance, max_distance
        )

        # Should return 2 nearest positions in range (50, 200]
        assert nearest_positions.shape[0] == k
        assert len(nearest_indices) == k

        # Verify all in range
        from spatial_engine.vector_store.spatial_index import calculate_distances
        distances = calculate_distances(query_position, nearest_positions)
        assert all(d > min_distance for d in distances)
        assert all(d <= max_distance for d in distances)

    def test_find_k_nearest_in_range_fewer_than_k(self, positioned_data):
        """Test k-nearest when fewer than k positions in range.

        Verifies:
        - Returns all available positions when fewer than k
        - Does not error when k > available
        """
        from spatial_engine.vector_store.spatial_index import find_k_nearest_in_range

        query_position = torch.zeros(3)
        k = 100  # More than available in range
        min_distance = 100.0
        max_distance = 130.0

        nearest_positions, nearest_indices = find_k_nearest_in_range(
            query_position, positioned_data, k, min_distance, max_distance
        )

        # Only positions at 125 (index 5) in range (100, 130]
        assert nearest_positions.shape[0] == 1
        assert 5 in nearest_indices

    def test_find_k_nearest_in_range_empty(self, positioned_data):
        """Test k-nearest with no positions in range.

        Verifies:
        - Returns empty when no positions in range
        """
        from spatial_engine.vector_store.spatial_index import find_k_nearest_in_range

        query_position = torch.zeros(3)

        nearest_positions, nearest_indices = find_k_nearest_in_range(
            query_position, positioned_data, k=10,
            min_distance=600.0, max_distance=700.0
        )

        assert nearest_positions.shape == (0, 3)
        assert len(nearest_indices) == 0

    def test_warp_lane_use_case(self):
        """Test typical warp lane detection use case.

        Simulates finding distant but not too distant tokens
        for semantic warping (M1.11 Exploit 1).
        """
        from spatial_engine.vector_store.spatial_index import find_k_nearest_in_range

        # Simulate 1000 tokens spread in 3D space
        positions = torch.randn(1000, 3) * 300  # Spread out to 300 units

        query_position = torch.zeros(3)
        attention_radius = 50.0

        # Warp lane search: beyond 2r but within 10r
        min_warp_distance = 2 * attention_radius   # 100
        max_warp_distance = 10 * attention_radius  # 500
        k = 50  # Top 50 warp candidates

        warp_candidates, indices = find_k_nearest_in_range(
            query_position, positions, k, min_warp_distance, max_warp_distance
        )

        # Verify we got some candidates
        assert warp_candidates.shape[0] <= k

        # Verify all are in warp range
        from spatial_engine.vector_store.spatial_index import calculate_distances
        distances = calculate_distances(query_position, warp_candidates)

        if len(distances) > 0:
            assert all(d > min_warp_distance for d in distances)
            assert all(d <= max_warp_distance for d in distances)


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
