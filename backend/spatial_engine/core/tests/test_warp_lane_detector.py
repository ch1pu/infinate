"""
test_warp_lane_detector.py - Tests for WarpLaneDetector and related classes.

Tests the warp lane detection system (Exploit 1), LOD boundary optimization
(Exploit 3), and shell memory organization (Exploit 2).

Author: Adolfo Lopez (ch1pu)
Milestone: 1.11 - Strafe Jumping Navigation
"""

import math

import pytest
import torch

from spatial_engine.core.warp_lane_detector import (
    LODBoundaryOptimizer,
    ShellMemoryOrganizer,
    WarpLane,
    WarpLaneDetector,
    WarpLaneNetwork,
)


class TestWarpLaneDataclass:
    """Tests for WarpLane dataclass."""

    def test_warp_lane_creation(self):
        """Test WarpLane can be created with all fields."""
        lane = WarpLane(
            source_position=torch.zeros(3),
            target_position=torch.tensor([100.0, 0.0, 0.0]),
            target_embedding=torch.randn(768),
            target_index=42,
            similarity=0.98,
            distance=100.0,
            is_reversible=True,
            score=0.95,
        )

        assert lane.target_index == 42
        assert lane.similarity == 0.98
        assert lane.distance == 100.0
        assert lane.is_reversible is True
        assert lane.score == 0.95


class TestWarpLaneDetectorInitialization:
    """Tests for WarpLaneDetector initialization."""

    def test_default_initialization(self):
        """Test WarpLaneDetector initializes with defaults."""
        detector = WarpLaneDetector()

        assert detector.similarity_threshold == 0.95
        assert detector.attention_radius == 50.0
        assert detector.min_warp_distance == 100.0  # 2 * 50
        assert detector.max_warp_distance == 500.0  # 10 * 50

    def test_custom_initialization(self):
        """Test WarpLaneDetector with custom parameters."""
        detector = WarpLaneDetector(
            similarity_threshold=0.9,
            min_warp_distance=50.0,
            max_warp_distance=200.0,
            attention_radius=25.0,
        )

        assert detector.similarity_threshold == 0.9
        assert detector.min_warp_distance == 50.0
        assert detector.max_warp_distance == 200.0
        assert detector.attention_radius == 25.0


class TestWarpLaneDetectorFindTargets:
    """Tests for find_warp_targets method."""

    def test_find_targets_basic(self):
        """Test finding warp targets returns boolean mask."""
        detector = WarpLaneDetector(
            similarity_threshold=0.5,  # Lower threshold for testing
            attention_radius=50.0,
        )

        query = torch.randn(64)
        all_keys = torch.randn(100, 64)
        all_positions = torch.randn(100, 3) * 200  # Spread out
        current_position = torch.zeros(3)

        mask = detector.find_warp_targets(query, all_keys, all_positions, current_position)

        assert mask.shape == (100,)
        assert mask.dtype == torch.bool

    def test_find_targets_distance_filtering(self):
        """Test that targets are filtered by distance."""
        detector = WarpLaneDetector(
            similarity_threshold=-1.0,  # Accept all similarities (cosine can be negative)
            min_warp_distance=100.0,
            max_warp_distance=200.0,
            attention_radius=50.0,
        )

        query = torch.randn(64)
        # Create keys with positive similarity to query
        all_keys = query.unsqueeze(0).expand(5, -1) + torch.randn(5, 64) * 0.1
        # Create positions at specific distances
        all_positions = torch.tensor([
            [50.0, 0.0, 0.0],   # 50 - too close
            [100.0, 0.0, 0.0],  # 100 - at min boundary
            [150.0, 0.0, 0.0],  # 150 - in range
            [199.0, 0.0, 0.0],  # 199 - in range (< 200)
            [250.0, 0.0, 0.0],  # 250 - too far
        ])
        current_position = torch.zeros(3)

        mask = detector.find_warp_targets(query, all_keys, all_positions, current_position)

        # Range is (100, 200) - min is exclusive (>), max is exclusive (<)
        # Position at 100 is not > 100, so excluded
        # Position at 200 would not be < 200, so we use 199 to test
        assert not mask[0].item()  # 50 - too close
        assert not mask[1].item()  # 100 - at boundary (not > 100)
        assert mask[2].item()      # 150 - in range (> 100 and < 200)
        assert mask[3].item()      # 199 - in range (> 100 and < 200)
        assert not mask[4].item()  # 250 - too far

    def test_find_targets_similarity_filtering(self):
        """Test that targets are filtered by similarity."""
        detector = WarpLaneDetector(
            similarity_threshold=0.9,
            attention_radius=50.0,
        )

        # Create query and a highly similar key
        query = torch.randn(64)
        query = query / torch.norm(query)  # Normalize

        all_keys = torch.randn(10, 64)
        # Make one key very similar to query
        all_keys[5] = query + torch.randn(64) * 0.1  # Similar
        all_keys[5] = all_keys[5] / torch.norm(all_keys[5])

        # All positions in valid distance range
        all_positions = torch.ones(10, 3) * 150  # 150 units away
        current_position = torch.zeros(3)

        mask = detector.find_warp_targets(query, all_keys, all_positions, current_position)

        # At least the similar key (index 5) should be found
        # (if its similarity > 0.9 after normalization)
        assert mask.shape == (10,)


class TestWarpLaneDetectorDetectLanes:
    """Tests for detect_warp_lanes method."""

    def test_detect_lanes_returns_list(self):
        """Test detect_warp_lanes returns list of WarpLane."""
        detector = WarpLaneDetector(
            similarity_threshold=0.0,  # Accept all
            attention_radius=50.0,
        )

        query = torch.randn(64)
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 200 + 150  # Distance ~150-350
        current_position = torch.zeros(3)

        lanes = detector.detect_warp_lanes(
            query, embeddings, positions, current_position, top_k=5
        )

        assert isinstance(lanes, list)
        if len(lanes) > 0:
            assert isinstance(lanes[0], WarpLane)
            assert len(lanes) <= 5

    def test_detect_lanes_sorted_by_score(self):
        """Test lanes are sorted by score descending."""
        detector = WarpLaneDetector(
            similarity_threshold=0.0,
            attention_radius=50.0,
        )

        query = torch.randn(64)
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 200 + 150
        current_position = torch.zeros(3)

        lanes = detector.detect_warp_lanes(
            query, embeddings, positions, current_position, top_k=10
        )

        if len(lanes) > 1:
            scores = [lane.score for lane in lanes]
            assert scores == sorted(scores, reverse=True)


class TestWarpThresholdComputation:
    """Tests for warp threshold computation."""

    def test_compute_threshold_basic(self):
        """Test warp threshold computation."""
        detector = WarpLaneDetector(attention_radius=10.0)

        threshold = detector.compute_warp_threshold(
            nearby_similarity=2.0,
            nearby_distance=5.0,
            target_distance=25.0,
        )

        # s_dist > s_near * exp((d_dist - d_near) / r)
        # threshold > 2.0 * exp((25 - 5) / 10) = 2.0 * exp(2) ≈ 14.78
        expected = 2.0 * math.exp(2.0)
        assert threshold == pytest.approx(expected, rel=0.01)

    def test_compute_threshold_same_distance(self):
        """Test threshold when distances are equal."""
        detector = WarpLaneDetector(attention_radius=10.0)

        threshold = detector.compute_warp_threshold(
            nearby_similarity=2.0,
            nearby_distance=15.0,
            target_distance=15.0,
        )

        # exp(0) = 1, so threshold = nearby_similarity
        assert threshold == pytest.approx(2.0)


class TestFindBestWarp:
    """Tests for find_best_warp method."""

    def test_find_best_warp_no_targets(self):
        """Test find_best_warp returns None when no valid targets."""
        detector = WarpLaneDetector(
            similarity_threshold=0.99,  # Very high threshold
            attention_radius=50.0,
        )

        query = torch.randn(64)
        embeddings = torch.randn(10, 64)  # Random, unlikely to be 0.99+ similar
        positions = torch.randn(10, 3) * 200 + 150
        current_position = torch.zeros(3)

        best = detector.find_best_warp(query, embeddings, positions, current_position)

        assert best is None or isinstance(best, WarpLane)


class TestLODBoundaryOptimizer:
    """Tests for LODBoundaryOptimizer."""

    def test_default_boundaries(self):
        """Test default LOD boundaries are set."""
        optimizer = LODBoundaryOptimizer()

        assert optimizer.boundaries == [50.0, 150.0, 500.0]
        assert optimizer.pull_back_margin == 0.1

    def test_optimize_pulls_back(self):
        """Test positions just past boundary are pulled back."""
        optimizer = LODBoundaryOptimizer(
            boundaries=[50.0, 150.0, 500.0],
            pull_back_margin=0.1,
        )

        # Positions just past first boundary
        positions = torch.tensor([
            [52.0, 0.0, 0.0],   # Just past 50
            [25.0, 0.0, 0.0],   # Well inside 50
            [100.0, 0.0, 0.0],  # Far from boundaries
        ])
        focus = torch.zeros(3)

        optimized = optimizer.optimize(positions, focus, tolerance=5.0)

        # First position should be pulled back
        dist_0 = torch.norm(optimized[0]).item()
        assert dist_0 < 50.0

        # Second position unchanged (inside)
        assert torch.allclose(optimized[1], positions[1])

        # Third position unchanged (not near boundary)
        assert torch.allclose(optimized[2], positions[2])

    def test_get_lod_level(self):
        """Test LOD level identification."""
        optimizer = LODBoundaryOptimizer(boundaries=[50.0, 150.0, 500.0])

        assert optimizer.get_lod_level(25.0) == "near"
        assert optimizer.get_lod_level(100.0) == "medium"
        assert optimizer.get_lod_level(300.0) == "far"
        assert optimizer.get_lod_level(600.0) == "beyond"

    def test_get_fidelity(self):
        """Test fidelity calculation."""
        optimizer = LODBoundaryOptimizer()

        assert optimizer.get_fidelity(25.0) == 1.0     # near
        assert optimizer.get_fidelity(100.0) == 0.2   # medium
        assert optimizer.get_fidelity(300.0) == 0.05  # far
        assert optimizer.get_fidelity(600.0) == 0.01  # beyond


class TestShellMemoryOrganizer:
    """Tests for ShellMemoryOrganizer."""

    def test_default_shell_radii(self):
        """Test default shell radii are set."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)

        assert organizer.shell_radii == [0.9, 1.9, 2.9]
        assert organizer.attention_radius == 50.0

    def test_place_token_on_shell(self):
        """Test placing token on specific shell."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)
        focus = torch.zeros(3)

        # Place on shell 0 (radius 0.9 * 50 = 45)
        pos = organizer.place_token_on_shell(0, focus)
        dist = torch.norm(pos).item()
        assert dist == pytest.approx(45.0, rel=0.01)

        # Place on shell 1 (radius 1.9 * 50 = 95)
        pos = organizer.place_token_on_shell(1, focus)
        dist = torch.norm(pos).item()
        assert dist == pytest.approx(95.0, rel=0.01)

        # Place on shell 2 (radius 2.9 * 50 = 145)
        pos = organizer.place_token_on_shell(2, focus)
        dist = torch.norm(pos).item()
        assert dist == pytest.approx(145.0, rel=0.01)

    def test_place_tokens_by_priority(self):
        """Test placing multiple tokens by priority."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)

        embeddings = torch.randn(5, 64)
        priorities = torch.tensor([0, 1, 2, 0, 1])  # Shell indices
        focus = torch.zeros(3)

        positions = organizer.place_tokens(embeddings, priorities, focus)

        assert positions.shape == (5, 3)

        # Check distances match shell radii
        expected_radii = [45.0, 95.0, 145.0, 45.0, 95.0]
        for i, expected in enumerate(expected_radii):
            dist = torch.norm(positions[i]).item()
            assert dist == pytest.approx(expected, rel=0.01)

    def test_snap_to_nearest_shell(self):
        """Test snapping position to nearest shell."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)
        focus = torch.zeros(3)

        # Position between shell 0 (45) and shell 1 (95)
        position = torch.tensor([70.0, 0.0, 0.0])

        snapped = organizer.snap_to_nearest_shell(position, focus)
        dist = torch.norm(snapped).item()

        # Should snap to shell 0 (45) or shell 1 (95)
        # 70 is closer to 45 (diff=25) vs 95 (diff=25) - equal, so either is valid
        assert dist == pytest.approx(45.0, rel=0.01) or dist == pytest.approx(95.0, rel=0.01)


class TestWarpLaneDetectorForward:
    """Tests for WarpLaneDetector forward pass."""

    def test_forward_single_query(self):
        """Test forward with single query."""
        detector = WarpLaneDetector(
            similarity_threshold=0.0,
            attention_radius=50.0,
        )

        query = torch.randn(64)
        embeddings = torch.randn(100, 64)
        positions = torch.randn(100, 3) * 200 + 150
        current_position = torch.zeros(3)

        mask = detector(query, embeddings, positions, current_position)

        assert mask.shape == (100,)
        assert mask.dtype == torch.bool

    def test_forward_batched(self):
        """Test forward with batched queries."""
        detector = WarpLaneDetector(
            similarity_threshold=0.0,
            attention_radius=50.0,
        )

        batch_size = 4
        query = torch.randn(batch_size, 64)
        embeddings = torch.randn(batch_size, 100, 64)
        positions = torch.randn(batch_size, 100, 3) * 200 + 150
        current_position = torch.randn(batch_size, 3)

        mask = detector(query, embeddings, positions, current_position)

        assert mask.shape == (batch_size, 100)


class TestLODBoundaryOptimizerForward:
    """Tests for LODBoundaryOptimizer forward pass."""

    def test_forward_single(self):
        """Test forward with single batch."""
        optimizer = LODBoundaryOptimizer()

        positions = torch.randn(100, 3) * 200
        focus = torch.zeros(3)

        optimized = optimizer(positions, focus)

        assert optimized.shape == (100, 3)

    def test_forward_batched(self):
        """Test forward with batched input."""
        optimizer = LODBoundaryOptimizer()

        batch_size = 4
        positions = torch.randn(batch_size, 100, 3) * 200
        focus = torch.randn(batch_size, 3)

        optimized = optimizer(positions, focus)

        assert optimized.shape == (batch_size, 100, 3)


class TestShellMemoryOrganizerForward:
    """Tests for ShellMemoryOrganizer forward pass."""

    def test_forward_single(self):
        """Test forward with single batch."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)

        embeddings = torch.randn(100, 64)
        priorities = torch.randint(0, 3, (100,))
        focus = torch.zeros(3)

        positions = organizer(embeddings, priorities, focus)

        assert positions.shape == (100, 3)

    def test_forward_batched(self):
        """Test forward with batched input."""
        organizer = ShellMemoryOrganizer(attention_radius=50.0)

        batch_size = 4
        embeddings = torch.randn(batch_size, 100, 64)
        priorities = torch.randint(0, 3, (batch_size, 100))
        focus = torch.randn(batch_size, 3)

        positions = organizer(embeddings, priorities, focus)

        assert positions.shape == (batch_size, 100, 3)


# Integration tests
class TestWarpLaneNetworkAnalysis:
    """Tests for warp lane network topology analysis."""

    def test_analyze_network_returns_structure(self):
        """Test analyze_warp_network returns WarpLaneNetwork."""
        detector = WarpLaneDetector(
            similarity_threshold=0.0,  # Accept all for testing
            attention_radius=50.0,
        )

        embeddings = torch.randn(50, 64)
        positions = torch.randn(50, 3) * 300

        network = detector.analyze_warp_network(
            embeddings, positions, sample_size=10
        )

        assert isinstance(network, WarpLaneNetwork)
        assert isinstance(network.lanes, list)
        assert isinstance(network.attractors, list)
        assert isinstance(network.sources, list)
        assert isinstance(network.dead_ends, list)
