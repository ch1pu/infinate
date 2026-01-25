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
warp_lane_detector.py - Detect semantic warp lanes for faster traversal.

Implements Exploit 1 (Warp Lanes) from the strafe jumping navigation system.
Finds distant tokens with high semantic similarity that can be "warped" to
despite spatial distance, exploiting the semantic×spatial multiplication
in INFINITE's attention mechanism.

Key insight: combined_scores = semantic_scores * spatial_mask
- Semantic scores are unbounded before softmax
- A query highly aligned with a distant key can have semantic score >> 1.0
- This overwhelms the 0.01 spatial decay factor
- Creates "warp lanes" through semantic space

Author: Adolfo Lopez (ch1pu)
Milestone: 1.11 - Strafe Jumping Navigation
"""

from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class WarpLane:
    """Represents a warp lane to a distant token.

    Attributes:
        source_position: Starting position [3]
        target_position: Destination position [3]
        target_embedding: Embedding at destination [d_model]
        target_index: Index in the original token list
        similarity: Cosine similarity to query
        distance: Euclidean distance from source
        is_reversible: Whether the warp can be reversed
        score: Combined warp quality score
    """

    source_position: torch.Tensor
    target_position: torch.Tensor
    target_embedding: torch.Tensor
    target_index: int
    similarity: float
    distance: float
    is_reversible: bool
    score: float


@dataclass
class WarpLaneNetwork:
    """Collection of discovered warp lanes.

    Attributes:
        lanes: List of discovered warp lanes
        attractors: Positions that are warp destinations (many warps in, few out)
        sources: Positions that are warp sources (many warps out, few in)
        dead_ends: Positions with warps in but no warps out
    """

    lanes: list[WarpLane]
    attractors: list[torch.Tensor]
    sources: list[torch.Tensor]
    dead_ends: list[torch.Tensor]


class WarpLaneDetector(nn.Module):
    """Detect semantic warp lanes for faster traversal.

    Finds distant tokens with high semantic similarity that can
    be "warped" to despite spatial distance, exploiting the
    semantic×spatial multiplication in attention.

    Mathematical basis:
    For a warp lane to be useful, the distant token D must compete
    with nearby token N in softmax:
        s_dist * m(d_dist) > s_near * m(d_near)
        s_dist > s_near * exp((d_dist - d_near) / r)

    For typical parameters, this requires ~15× similarity.

    Args:
        similarity_threshold: Minimum cosine similarity for warp (default: 0.95)
        min_warp_distance: Minimum distance for warp target (default: None, uses 2*radius)
        max_warp_distance: Maximum distance for warp target (default: None, uses 10*radius)
        attention_radius: Base attention radius (default: 50.0)

    Example:
        ```python
        detector = WarpLaneDetector(similarity_threshold=0.95)

        # Find warp targets
        query = torch.randn(768)
        embeddings = torch.randn(1000, 768)
        positions = torch.randn(1000, 3) * 200
        current_pos = torch.zeros(3)

        warp_mask = detector.find_warp_targets(
            query, embeddings, positions, current_pos
        )

        # Get full warp lanes
        lanes = detector.detect_warp_lanes(
            query, embeddings, positions, current_pos
        )
        ```
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        min_warp_distance: Optional[float] = None,
        max_warp_distance: Optional[float] = None,
        attention_radius: float = 50.0,
    ):
        """Initialize the warp lane detector."""
        super().__init__()

        self.similarity_threshold = similarity_threshold
        self.attention_radius = attention_radius

        # Default distance bounds based on attention radius
        self._min_warp_distance = min_warp_distance
        self._max_warp_distance = max_warp_distance

    @property
    def min_warp_distance(self) -> float:
        """Minimum distance for warp targets."""
        if self._min_warp_distance is not None:
            return self._min_warp_distance
        return 2 * self.attention_radius

    @property
    def max_warp_distance(self) -> float:
        """Maximum distance for warp targets."""
        if self._max_warp_distance is not None:
            return self._max_warp_distance
        return 10 * self.attention_radius

    def find_warp_targets(
        self,
        query: torch.Tensor,
        all_keys: torch.Tensor,
        all_positions: torch.Tensor,
        current_position: torch.Tensor,
    ) -> torch.Tensor:
        """Find distant tokens that can be reached via semantic warp.

        Args:
            query: Query embedding [d_model]
            all_keys: Token embeddings [n, d_model]
            all_positions: Token positions [n, 3]
            current_position: Current position [3]

        Returns:
            Boolean mask of warpable tokens [n]
        """
        # Compute distances from current position
        distances = torch.norm(all_positions - current_position, dim=-1)

        # Compute semantic similarities
        similarities = F.cosine_similarity(query.unsqueeze(0), all_keys, dim=-1)

        # Warp targets: beyond normal range but high similarity
        beyond_range = (distances > self.min_warp_distance) & (
            distances < self.max_warp_distance
        )
        high_similarity = similarities > self.similarity_threshold

        warp_mask = beyond_range & high_similarity

        return warp_mask

    def detect_warp_lanes(
        self,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        current_position: torch.Tensor,
        top_k: int = 10,
    ) -> list[WarpLane]:
        """Detect warp lanes with full metadata.

        Args:
            query: Query embedding [d_model]
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]
            current_position: Current position [3]
            top_k: Maximum number of warp lanes to return

        Returns:
            List of WarpLane objects sorted by score
        """
        # Find warp targets
        warp_mask = self.find_warp_targets(query, embeddings, positions, current_position)

        if not warp_mask.any():
            return []

        # Get indices of warp targets
        warp_indices = torch.where(warp_mask)[0]

        # Compute similarities and distances for warp targets
        warp_embeddings = embeddings[warp_indices]
        warp_positions = positions[warp_indices]

        similarities = F.cosine_similarity(query.unsqueeze(0), warp_embeddings, dim=-1)
        distances = torch.norm(warp_positions - current_position, dim=-1)

        # Build warp lanes
        lanes = []
        for i, idx in enumerate(warp_indices):
            sim = similarities[i].item()
            dist = distances[i].item()

            # Check reversibility (within 3r)
            is_reversible = dist < 3 * self.attention_radius

            # Compute score: high similarity, moderate distance preferred
            # Score = similarity * distance_factor
            # distance_factor peaks at 3r and decays for very far targets
            optimal_distance = 3 * self.attention_radius
            distance_factor = 1.0 - abs(dist - optimal_distance) / (
                self.max_warp_distance - self.min_warp_distance
            )
            distance_factor = max(0.1, distance_factor)  # Floor at 0.1

            score = sim * distance_factor

            lane = WarpLane(
                source_position=current_position.clone(),
                target_position=warp_positions[i].clone(),
                target_embedding=warp_embeddings[i].clone(),
                target_index=idx.item(),
                similarity=sim,
                distance=dist,
                is_reversible=is_reversible,
                score=score,
            )
            lanes.append(lane)

        # Sort by score descending
        lanes.sort(key=lambda x: x.score, reverse=True)

        # Return top-k
        return lanes[:top_k]

    def compute_warp_threshold(
        self,
        nearby_similarity: float,
        nearby_distance: float,
        target_distance: float,
    ) -> float:
        """Compute minimum similarity needed for a warp lane.

        Based on the mathematical proof:
        s_dist > s_near * exp((d_dist - d_near) / r)

        Args:
            nearby_similarity: Similarity to nearby token
            nearby_distance: Distance to nearby token
            target_distance: Distance to potential warp target

        Returns:
            Minimum similarity threshold for warp
        """
        import math

        distance_diff = target_distance - nearby_distance
        threshold = nearby_similarity * math.exp(distance_diff / self.attention_radius)

        return threshold

    def analyze_warp_network(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        sample_positions: Optional[torch.Tensor] = None,
        sample_size: int = 100,
    ) -> WarpLaneNetwork:
        """Analyze the warp lane network topology.

        Maps attractors (many warps in, few out), sources (many warps out),
        and dead ends (warps in, no warps out).

        Args:
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]
            sample_positions: Optional specific positions to analyze
            sample_size: Number of random positions to sample if not specified

        Returns:
            WarpLaneNetwork with topology analysis
        """
        if sample_positions is None:
            # Sample random positions
            n = len(positions)
            if n <= sample_size:
                sample_indices = torch.arange(n)
            else:
                sample_indices = torch.randperm(n)[:sample_size]
            sample_positions = positions[sample_indices]

        # Count in-degree and out-degree for each position
        in_counts: dict[int, int] = {}
        out_counts: dict[int, int] = {}
        all_lanes: list[WarpLane] = []

        for i, pos in enumerate(sample_positions):
            # Use the embedding at this position as the query
            # Find closest embedding
            dists = torch.norm(positions - pos, dim=-1)
            closest_idx = torch.argmin(dists).item()
            query = embeddings[closest_idx]

            # Detect warp lanes from this position
            lanes = self.detect_warp_lanes(query, embeddings, positions, pos, top_k=50)

            out_counts[i] = len(lanes)

            for lane in lanes:
                all_lanes.append(lane)
                target_idx = lane.target_index
                in_counts[target_idx] = in_counts.get(target_idx, 0) + 1

        # Identify attractors, sources, and dead ends
        attractors = []
        sources = []
        dead_ends = []

        for i, pos in enumerate(sample_positions):
            in_deg = in_counts.get(i, 0)
            out_deg = out_counts.get(i, 0)

            if in_deg > 2 * out_deg and in_deg > 5:
                attractors.append(pos)
            elif out_deg > 2 * in_deg and out_deg > 5:
                sources.append(pos)
            elif in_deg > 3 and out_deg == 0:
                dead_ends.append(pos)

        return WarpLaneNetwork(
            lanes=all_lanes,
            attractors=attractors,
            sources=sources,
            dead_ends=dead_ends,
        )

    def find_best_warp(
        self,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        current_position: torch.Tensor,
        prefer_reversible: bool = True,
    ) -> Optional[WarpLane]:
        """Find the best warp lane for a query.

        Args:
            query: Query embedding [d_model]
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]
            current_position: Current position [3]
            prefer_reversible: Whether to prefer reversible warps

        Returns:
            Best WarpLane, or None if no suitable warp found
        """
        lanes = self.detect_warp_lanes(query, embeddings, positions, current_position)

        if not lanes:
            return None

        if prefer_reversible:
            # First try to find a reversible warp
            reversible = [l for l in lanes if l.is_reversible]
            if reversible:
                return reversible[0]  # Already sorted by score

        # Return best overall
        return lanes[0]

    def forward(
        self,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        current_position: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass returning warp target mask.

        Args:
            query: Query embedding [d_model] or [batch, d_model]
            embeddings: Token embeddings [n, d_model] or [batch, n, d_model]
            positions: Token positions [n, 3] or [batch, n, 3]
            current_position: Current position [3] or [batch, 3]

        Returns:
            Warp target mask [n] or [batch, n]
        """
        # Handle batched input
        if query.dim() == 2:
            batch_size = query.size(0)
            results = []
            for i in range(batch_size):
                mask = self.find_warp_targets(
                    query[i], embeddings[i], positions[i], current_position[i]
                )
                results.append(mask)
            return torch.stack(results)

        return self.find_warp_targets(query, embeddings, positions, current_position)


class LODBoundaryOptimizer(nn.Module):
    """Optimize token positions relative to LOD boundaries.

    Implements Exploit 3 (LOD Hopping) from strafe jumping navigation.
    Keeps critical tokens just inside LOD boundaries to maximize fidelity.

    LOD Boundaries (from lod.py):
    - NEAR: 0-50 (100% fidelity)
    - MEDIUM: 50-150 (20% fidelity, 80% CLIFF!)
    - FAR: 150-500 (5% fidelity)
    - BEYOND: 500+ (1% fidelity)

    Args:
        boundaries: LOD boundary distances (default: [50, 150, 500])
        pull_back_margin: Distance to pull back inside boundary (default: 0.1)

    Example:
        ```python
        optimizer = LODBoundaryOptimizer()

        positions = torch.randn(100, 3) * 200
        focus_position = torch.zeros(3)

        optimized = optimizer.optimize(positions, focus_position)
        ```
    """

    DEFAULT_BOUNDARIES = [50.0, 150.0, 500.0]

    def __init__(
        self,
        boundaries: Optional[list[float]] = None,
        pull_back_margin: float = 0.1,
    ):
        """Initialize the LOD boundary optimizer."""
        super().__init__()

        self.boundaries = boundaries if boundaries is not None else self.DEFAULT_BOUNDARIES
        self.pull_back_margin = pull_back_margin

    def optimize(
        self,
        positions: torch.Tensor,
        focus_position: torch.Tensor,
        tolerance: float = 5.0,
    ) -> torch.Tensor:
        """Optimize token positions relative to LOD boundaries.

        Tokens just past a boundary are pulled back to maximize fidelity.

        Args:
            positions: Token positions [n, 3]
            focus_position: Reference position for distance calculation [3]
            tolerance: How far past a boundary to consider for pull-back

        Returns:
            Optimized positions [n, 3]
        """
        optimized = positions.clone()

        # Compute distances from focus
        distances = torch.norm(positions - focus_position, dim=-1)

        for i, distance in enumerate(distances):
            dist_val = distance.item()

            # Check each boundary
            for boundary in self.boundaries:
                if boundary < dist_val < boundary + tolerance:
                    # Pull back to just inside boundary
                    direction = (positions[i] - focus_position) / dist_val
                    optimized[i] = focus_position + direction * (boundary - self.pull_back_margin)
                    break

        return optimized

    def get_lod_level(self, distance: float) -> str:
        """Get LOD level name for a distance.

        Args:
            distance: Distance from focus position

        Returns:
            LOD level name: "near", "medium", "far", or "beyond"
        """
        if distance < self.boundaries[0]:
            return "near"
        elif distance < self.boundaries[1]:
            return "medium"
        elif distance < self.boundaries[2]:
            return "far"
        else:
            return "beyond"

    def get_fidelity(self, distance: float) -> float:
        """Get fidelity percentage for a distance.

        Args:
            distance: Distance from focus position

        Returns:
            Fidelity as percentage (0.0 to 1.0)
        """
        level = self.get_lod_level(distance)
        fidelity_map = {
            "near": 1.0,
            "medium": 0.2,
            "far": 0.05,
            "beyond": 0.01,
        }
        return fidelity_map.get(level, 0.01)

    def forward(
        self,
        positions: torch.Tensor,
        focus_position: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass for optimization.

        Args:
            positions: Token positions [n, 3] or [batch, n, 3]
            focus_position: Focus position [3] or [batch, 3]

        Returns:
            Optimized positions, same shape as input
        """
        if positions.dim() == 3:
            batch_size = positions.size(0)
            results = []
            for i in range(batch_size):
                opt = self.optimize(positions[i], focus_position[i])
                results.append(opt)
            return torch.stack(results)

        return self.optimize(positions, focus_position)


class ShellMemoryOrganizer(nn.Module):
    """Organize tokens in concentric shells at optimal distances.

    Implements Exploit 2 (Shell Memory) from strafe jumping navigation.
    Places tokens just inside attention boundaries (2.9r) to maximize
    the number of visible tokens.

    Shell radii are positioned at 0.9r, 1.9r, 2.9r (where r = attention radius)
    to stay just inside the hard 3r cutoff.

    Args:
        attention_radius: Base attention radius (default: 50.0)
        shell_radii: Relative shell radii (default: [0.9, 1.9, 2.9])

    Example:
        ```python
        organizer = ShellMemoryOrganizer(attention_radius=50.0)

        # Place tokens on shells based on priority
        tokens = torch.randn(100, 768)
        priorities = torch.randint(0, 3, (100,))
        focus_position = torch.zeros(3)

        positions = organizer.place_tokens(tokens, priorities, focus_position)
        ```
    """

    DEFAULT_SHELL_RADII = [0.9, 1.9, 2.9]

    def __init__(
        self,
        attention_radius: float = 50.0,
        shell_radii: Optional[list[float]] = None,
    ):
        """Initialize the shell memory organizer."""
        super().__init__()

        self.attention_radius = attention_radius
        self.shell_radii = shell_radii if shell_radii is not None else self.DEFAULT_SHELL_RADII

    def place_token_on_shell(
        self,
        shell_index: int,
        focus_position: torch.Tensor,
        direction: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Place a token on a specific shell.

        Args:
            shell_index: Index of shell (0, 1, or 2)
            focus_position: Center position [3]
            direction: Optional direction from focus (random if None)

        Returns:
            Position on shell surface [3]
        """
        shell_index = min(shell_index, len(self.shell_radii) - 1)
        shell_index = max(shell_index, 0)

        radius = self.shell_radii[shell_index] * self.attention_radius

        if direction is None:
            # Random direction on unit sphere
            direction = torch.randn(3, device=focus_position.device)
            direction = direction / torch.norm(direction)

        return focus_position + direction * radius

    def place_tokens(
        self,
        embeddings: torch.Tensor,
        priorities: torch.Tensor,
        focus_position: torch.Tensor,
    ) -> torch.Tensor:
        """Place tokens on shells based on priority.

        Lower priority = closer shell (higher visibility).

        Args:
            embeddings: Token embeddings [n, d_model]
            priorities: Priority values [n] (0, 1, 2 for shells)
            focus_position: Center position [3]

        Returns:
            Positions on shell surfaces [n, 3]
        """
        n = len(embeddings)
        positions = torch.zeros(n, 3, device=embeddings.device)

        # Generate random directions for variety
        directions = torch.randn(n, 3, device=embeddings.device)
        directions = directions / torch.norm(directions, dim=-1, keepdim=True)

        for i in range(n):
            shell_idx = int(priorities[i].item())
            positions[i] = self.place_token_on_shell(
                shell_idx, focus_position, directions[i]
            )

        return positions

    def snap_to_nearest_shell(
        self,
        position: torch.Tensor,
        focus_position: torch.Tensor,
    ) -> torch.Tensor:
        """Snap a position to the nearest shell.

        Args:
            position: Current position [3]
            focus_position: Center position [3]

        Returns:
            Position snapped to nearest shell [3]
        """
        direction = position - focus_position
        distance = torch.norm(direction).item()

        if distance < 1e-6:
            # At focus, place on innermost shell with random direction
            direction = torch.randn(3, device=position.device)
            direction = direction / torch.norm(direction)
            return focus_position + direction * (self.shell_radii[0] * self.attention_radius)

        # Find nearest shell
        min_diff = float("inf")
        target_radius = distance

        for shell_radius in self.shell_radii:
            actual_radius = shell_radius * self.attention_radius
            diff = abs(distance - actual_radius)
            if diff < min_diff:
                min_diff = diff
                target_radius = actual_radius

        # Scale to shell radius
        direction = direction / distance
        return focus_position + direction * target_radius

    def forward(
        self,
        embeddings: torch.Tensor,
        priorities: torch.Tensor,
        focus_position: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass for token placement.

        Args:
            embeddings: Token embeddings [n, d_model] or [batch, n, d_model]
            priorities: Priority values [n] or [batch, n]
            focus_position: Center position [3] or [batch, 3]

        Returns:
            Positions on shell surfaces, same batch shape as input
        """
        if embeddings.dim() == 3:
            batch_size = embeddings.size(0)
            results = []
            for i in range(batch_size):
                pos = self.place_tokens(embeddings[i], priorities[i], focus_position[i])
                results.append(pos)
            return torch.stack(results)

        return self.place_tokens(embeddings, priorities, focus_position)
