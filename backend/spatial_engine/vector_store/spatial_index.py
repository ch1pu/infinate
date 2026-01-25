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
spatial_index.py - Spatial indexing utilities for 3D position-based retrieval.

Provides efficient spatial queries including distance calculation, radius filtering,
k-nearest neighbors, and octree-based spatial partitioning.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
"""

from typing import Optional

import torch


def calculate_distances(query_position: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
    """Calculate 3D Euclidean distances from query to all positions.

    Uses vectorized PyTorch operations for efficiency.

    Args:
        query_position: (3,) tensor of query position (x, y, z)
        positions: (n, 3) tensor of positions to compare

    Returns:
        (n,) tensor of distances

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(100, 3) * 50.0
        distances = calculate_distances(query, positions)
        assert distances.shape == (100,)
        ```
    """
    # Compute squared differences: (n, 3)
    diff = positions - query_position

    # Sum squared differences and take sqrt: (n,)
    distances = torch.sqrt((diff**2).sum(dim=1))

    return distances


def filter_by_radius(
    query_position: torch.Tensor, positions: torch.Tensor, radius: float
) -> tuple[torch.Tensor, list[int]]:
    """Filter positions to only those within a spatial radius.

    Args:
        query_position: (3,) tensor of query position
        positions: (n, 3) tensor of positions to filter
        radius: Maximum distance from query position

    Returns:
        Tuple of (filtered_positions, filtered_indices):
        - filtered_positions: (m, 3) tensor where m <= n
        - filtered_indices: List of original indices

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(100, 3) * 200.0
        radius = 50.0

        filtered_pos, indices = filter_by_radius(query, positions, radius)
        # All filtered positions are within 50 units of origin
        ```
    """
    # Calculate distances
    distances = calculate_distances(query_position, positions)

    # Find indices within radius
    mask = distances <= radius
    indices = torch.where(mask)[0].tolist()

    # Filter positions
    filtered_positions = positions[mask]

    return filtered_positions, indices


def find_k_nearest(
    query_position: torch.Tensor, positions: torch.Tensor, k: int
) -> tuple[torch.Tensor, list[int]]:
    """Find k-nearest neighbors by spatial distance.

    Args:
        query_position: (3,) tensor of query position
        positions: (n, 3) tensor of positions
        k: Number of nearest neighbors to return

    Returns:
        Tuple of (nearest_positions, nearest_indices):
        - nearest_positions: (k, 3) tensor sorted by distance
        - nearest_indices: List of k original indices

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(100, 3) * 100.0
        k = 10

        nearest_pos, indices = find_k_nearest(query, positions, k)
        assert nearest_pos.shape == (10, 3)
        ```
    """
    # Calculate distances
    distances = calculate_distances(query_position, positions)

    # Find k smallest distances
    k_actual = min(k, len(positions))
    _, indices_tensor = torch.topk(distances, k_actual, largest=False, sorted=True)
    indices = indices_tensor.tolist()

    # Get corresponding positions
    nearest_positions = positions[indices_tensor]

    return nearest_positions, indices


def find_k_nearest_within_radius(
    query_position: torch.Tensor, positions: torch.Tensor, k: int, radius: float
) -> tuple[torch.Tensor, list[int]]:
    """Find k-nearest neighbors within a spatial radius.

    Combines radius filtering with k-nearest selection:
    1. Filter positions to those within radius
    2. Select k-nearest from filtered results

    Args:
        query_position: (3,) tensor of query position
        positions: (n, 3) tensor of positions
        k: Number of nearest neighbors to return
        radius: Maximum distance from query position

    Returns:
        Tuple of (nearest_positions, nearest_indices):
        - nearest_positions: (m, 3) tensor where m <= k
        - nearest_indices: List of m original indices

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(100, 3) * 200.0
        k = 10
        radius = 50.0

        nearest_pos, indices = find_k_nearest_within_radius(
            query, positions, k, radius
        )
        # Returns at most 10 positions, all within 50 units
        ```
    """
    # First, filter by radius
    filtered_positions, filtered_indices = filter_by_radius(query_position, positions, radius)

    # If no positions within radius, return empty
    if len(filtered_positions) == 0:
        return torch.empty(0, 3), []

    # Then, find k-nearest from filtered results
    # Use query_position relative to filtered positions
    nearest_positions, relative_indices = find_k_nearest(query_position, filtered_positions, k)

    # Map back to original indices
    original_indices = [filtered_indices[i] for i in relative_indices]

    return nearest_positions, original_indices


def filter_by_distance_range(
    query_position: torch.Tensor,
    positions: torch.Tensor,
    min_distance: float,
    max_distance: float,
) -> tuple[torch.Tensor, list[int]]:
    """Filter positions to those within a distance range.

    Added in M1.11 for warp lane detection - enables finding distant
    but not too distant tokens for semantic warping.

    Args:
        query_position: (3,) tensor of query position
        positions: (n, 3) tensor of positions to filter
        min_distance: Minimum distance from query position (exclusive lower bound)
        max_distance: Maximum distance from query position (inclusive upper bound)

    Returns:
        Tuple of (filtered_positions, filtered_indices):
        - filtered_positions: (m, 3) tensor where m <= n
        - filtered_indices: List of original indices

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(100, 3) * 200.0
        min_dist = 100.0  # Beyond normal attention radius
        max_dist = 500.0  # But not too far

        filtered_pos, indices = filter_by_distance_range(
            query, positions, min_dist, max_dist
        )
        # Returns positions between 100 and 500 units from query
        ```
    """
    # Calculate distances
    distances = calculate_distances(query_position, positions)

    # Find indices within range (min_distance < distance <= max_distance)
    mask = (distances > min_distance) & (distances <= max_distance)
    indices = torch.where(mask)[0].tolist()

    # Filter positions
    filtered_positions = positions[mask]

    return filtered_positions, indices


def find_k_nearest_in_range(
    query_position: torch.Tensor,
    positions: torch.Tensor,
    k: int,
    min_distance: float,
    max_distance: float,
) -> tuple[torch.Tensor, list[int]]:
    """Find k-nearest neighbors within a distance range.

    Added in M1.11 for warp lane detection. Combines distance range
    filtering with k-nearest selection for efficient warp target search.

    Args:
        query_position: (3,) tensor of query position
        positions: (n, 3) tensor of positions
        k: Number of nearest neighbors to return
        min_distance: Minimum distance from query position
        max_distance: Maximum distance from query position

    Returns:
        Tuple of (nearest_positions, nearest_indices):
        - nearest_positions: (m, 3) tensor where m <= k
        - nearest_indices: List of m original indices

    Example:
        ```python
        query = torch.tensor([0.0, 0.0, 0.0])
        positions = torch.randn(1000, 3) * 500.0
        k = 50
        min_dist = 100.0   # Beyond 2r
        max_dist = 500.0   # Within 10r

        # Find distant tokens for warp lane candidates
        nearest_pos, indices = find_k_nearest_in_range(
            query, positions, k, min_dist, max_dist
        )
        ```
    """
    # First, filter by distance range
    filtered_positions, filtered_indices = filter_by_distance_range(
        query_position, positions, min_distance, max_distance
    )

    # If no positions in range, return empty
    if len(filtered_positions) == 0:
        return torch.empty(0, 3), []

    # Then, find k-nearest from filtered results
    # Note: "nearest" here means closest to min_distance bound
    nearest_positions, relative_indices = find_k_nearest(
        query_position, filtered_positions, k
    )

    # Map back to original indices
    original_indices = [filtered_indices[i] for i in relative_indices]

    return nearest_positions, original_indices


class OctreeIndex:
    """Octree-based spatial partitioning for efficient range queries.

    Divides 3D space hierarchically into octants, enabling fast spatial lookups
    by reducing the search space.

    Args:
        bounds: (x_min, x_max, y_min, y_max, z_min, z_max) spatial bounds
        max_depth: Maximum tree depth (controls granularity)

    Example:
        ```python
        octree = OctreeIndex(
            bounds=(-100.0, 100.0, -100.0, 100.0, -100.0, 100.0),
            max_depth=4
        )

        # Insert positions
        positions = torch.randn(100, 3) * 50.0
        for i, pos in enumerate(positions):
            octree.insert(i, pos)

        # Query a region
        query_pos = torch.tensor([0.0, 0.0, 0.0])
        indices = octree.query_radius(query_pos, radius=30.0)
        ```
    """

    def __init__(
        self,
        bounds: tuple[float, float, float, float, float, float],
        max_depth: int = 4,
    ):
        """Initialize octree with spatial bounds.

        Args:
            bounds: (x_min, x_max, y_min, y_max, z_min, z_max)
            max_depth: Maximum tree depth
        """
        self.bounds = bounds
        self.max_depth = max_depth
        self.root = OctreeNode(bounds, depth=0, max_depth=max_depth)

    def insert(self, index: int, position: torch.Tensor) -> None:
        """Insert a position into the octree.

        Args:
            index: Original index of this position
            position: (3,) tensor of (x, y, z) position
        """
        pos_tuple = (position[0].item(), position[1].item(), position[2].item())
        self.root.insert(index, pos_tuple)

    def query_radius(self, query_position: torch.Tensor, radius: float) -> list[int]:
        """Query all positions within a radius.

        Args:
            query_position: (3,) tensor of query position
            radius: Search radius

        Returns:
            List of indices within radius
        """
        query_tuple = (
            query_position[0].item(),
            query_position[1].item(),
            query_position[2].item(),
        )
        return self.root.query_radius(query_tuple, radius)


class OctreeNode:
    """Single node in the octree structure.

    Each node represents a cubic region of space and can be subdivided
    into 8 child octants.
    """

    def __init__(
        self,
        bounds: tuple[float, float, float, float, float, float],
        depth: int,
        max_depth: int,
    ):
        """Initialize octree node.

        Args:
            bounds: (x_min, x_max, y_min, y_max, z_min, z_max)
            depth: Current depth in tree
            max_depth: Maximum allowed depth
        """
        self.bounds = bounds
        self.depth = depth
        self.max_depth = max_depth
        self.children: Optional[list["OctreeNode"]] = None
        self.indices: list[int] = []
        self.positions: list[tuple[float, float, float]] = []

    def insert(self, index: int, position: tuple[float, float, float]) -> None:
        """Insert a position into this node.

        Args:
            index: Original index
            position: (x, y, z) tuple
        """
        # If we've reached max depth, store here
        if self.depth >= self.max_depth:
            self.indices.append(index)
            self.positions.append(position)
            return

        # If we have children, insert into appropriate child
        if self.children is not None:
            child_idx = self._get_octant(position)
            self.children[child_idx].insert(index, position)
            return

        # Otherwise, store here
        self.indices.append(index)
        self.positions.append(position)

        # If we have too many items (e.g., >8), subdivide
        if len(self.indices) > 8 and self.depth < self.max_depth:
            self._subdivide()

    def _get_octant(self, position: tuple[float, float, float]) -> int:
        """Determine which octant a position belongs to.

        Args:
            position: (x, y, z) tuple

        Returns:
            Octant index (0-7)
        """
        x_min, x_max, y_min, y_max, z_min, z_max = self.bounds
        x_mid = (x_min + x_max) / 2
        y_mid = (y_min + y_max) / 2
        z_mid = (z_min + z_max) / 2

        x, y, z = position

        octant = 0
        if x >= x_mid:
            octant |= 1
        if y >= y_mid:
            octant |= 2
        if z >= z_mid:
            octant |= 4

        return octant

    def _subdivide(self) -> None:
        """Subdivide this node into 8 children."""
        x_min, x_max, y_min, y_max, z_min, z_max = self.bounds
        x_mid = (x_min + x_max) / 2
        y_mid = (y_min + y_max) / 2
        z_mid = (z_min + z_max) / 2

        # Create 8 child octants
        self.children = []
        for i in range(8):
            child_x_min = x_min if (i & 1) == 0 else x_mid
            child_x_max = x_mid if (i & 1) == 0 else x_max
            child_y_min = y_min if (i & 2) == 0 else y_mid
            child_y_max = y_mid if (i & 2) == 0 else y_max
            child_z_min = z_min if (i & 4) == 0 else z_mid
            child_z_max = z_mid if (i & 4) == 0 else z_max

            child_bounds = (
                child_x_min,
                child_x_max,
                child_y_min,
                child_y_max,
                child_z_min,
                child_z_max,
            )
            child = OctreeNode(child_bounds, self.depth + 1, self.max_depth)
            self.children.append(child)

        # Move existing items to children
        for idx, pos in zip(self.indices, self.positions, strict=False):
            child_idx = self._get_octant(pos)
            self.children[child_idx].insert(idx, pos)

        # Clear this node's storage
        self.indices = []
        self.positions = []

    def query_radius(self, query_position: tuple[float, float, float], radius: float) -> list[int]:
        """Query all positions within radius of query position.

        Args:
            query_position: (x, y, z) tuple
            radius: Search radius

        Returns:
            List of indices within radius
        """
        # Check if this node's bounds intersect the query sphere
        if not self._intersects_sphere(query_position, radius):
            return []

        results = []

        # If we have children, query them
        if self.children is not None:
            for child in self.children:
                results.extend(child.query_radius(query_position, radius))
        else:
            # Check each position in this node
            for idx, pos in zip(self.indices, self.positions, strict=False):
                dist = (
                    (pos[0] - query_position[0]) ** 2
                    + (pos[1] - query_position[1]) ** 2
                    + (pos[2] - query_position[2]) ** 2
                ) ** 0.5
                if dist <= radius:
                    results.append(idx)

        return results

    def _intersects_sphere(self, center: tuple[float, float, float], radius: float) -> bool:
        """Check if this node's bounds intersect a sphere.

        Args:
            center: Sphere center (x, y, z)
            radius: Sphere radius

        Returns:
            True if bounds intersect sphere
        """
        x_min, x_max, y_min, y_max, z_min, z_max = self.bounds
        cx, cy, cz = center

        # Find closest point on bounds to sphere center
        closest_x = max(x_min, min(cx, x_max))
        closest_y = max(y_min, min(cy, y_max))
        closest_z = max(z_min, min(cz, z_max))

        # Calculate distance from sphere center to closest point
        dist = ((closest_x - cx) ** 2 + (closest_y - cy) ** 2 + (closest_z - cz) ** 2) ** 0.5

        return bool(dist <= radius)
