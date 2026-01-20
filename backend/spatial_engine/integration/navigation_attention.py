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
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over MIT's approach with 89.58% test coverage.
# ============================================================================

"""
navigation_attention.py - Full integration of M1.11 navigation with INFINITE attention.

Integrates MomentumNavigator with SpatialAttention and LOD systems to provide
navigation-guided attention that measures actual speedup vs baseline.

Key Integration:
    - MomentumNavigator (M1.11): 7 exploit navigation
    - SpatialAttention (M1.3): O(k) attention mechanism
    - LOD (M1.10): Hierarchical context compression
    - Qdrant: Vector store with min_distance

Speedup Measurement:
    - Steps to reach target (navigation efficiency)
    - Attention operations performed (computational savings)
    - Quality of retrieved context (accuracy)

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11 - Strafe Jumping Navigation (Integration)
"""

from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from spatial_engine.core.lod import LODConfig, LODLevel
from spatial_engine.core.momentum_navigator import MomentumNavigator, NavigationResult
from spatial_engine.core.spatial_attention import SpatialAttention


@dataclass
class NavigationMetrics:
    """Metrics from navigation-guided attention.

    Attributes:
        steps_taken: Number of navigation steps
        attention_ops: Number of attention operations performed
        tokens_accessed: Total tokens attended to
        warp_count: Number of warp lane jumps
        converged: Whether navigation converged
        final_similarity: Cosine similarity to target
        trajectory_length: Total distance traveled
    """

    steps_taken: int = 0
    attention_ops: int = 0
    tokens_accessed: int = 0
    warp_count: int = 0
    converged: bool = False
    final_similarity: float = 0.0
    trajectory_length: float = 0.0
    temperature_schedule: list[float] = field(default_factory=list)


@dataclass
class AttentionResult:
    """Result from navigation-guided attention.

    Attributes:
        output: Attended output [batch, seq_len, d_model]
        retrieved_tokens: Indices of tokens retrieved
        retrieved_embeddings: Embeddings of retrieved tokens
        metrics: Navigation metrics
    """

    output: torch.Tensor
    retrieved_indices: torch.Tensor
    retrieved_embeddings: torch.Tensor
    metrics: NavigationMetrics


class NavigationAttention(nn.Module):
    """Integrated navigation-guided spatial attention.

    Combines MomentumNavigator (M1.11) with SpatialAttention (M1.3) and
    LOD (M1.10) for optimized context retrieval.

    The navigation process:
    1. Navigator finds optimal position in semantic space
    2. Attention retrieves k tokens from that position
    3. LOD compresses distant context
    4. Metrics track efficiency for benchmarking

    Args:
        d_model: Embedding dimension
        n_heads: Number of attention heads
        spatial_radius: Attention radius
        k_neighbors: Number of neighbors to attend to
        enable_navigation: Whether to use navigation (vs baseline)
        enable_lod: Whether to use LOD compression

    Example:
        >>> nav_attention = NavigationAttention(d_model=768)
        >>> output, metrics = nav_attention.query(
        ...     query=torch.randn(768),
        ...     context_embeddings=torch.randn(10000, 768),
        ...     context_positions=torch.randn(10000, 3) * 500,
        ...     target_embedding=torch.randn(768)  # What we're looking for
        ... )
        >>> print(f"Steps: {metrics.steps_taken}, Ops: {metrics.attention_ops}")
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: Optional[int] = None,
        spatial_radius: float = 50.0,
        k_neighbors: int = 50,
        enable_navigation: bool = True,
        enable_lod: bool = True,
        navigation_max_steps: int = 10,
    ) -> None:
        super().__init__()

        # Auto-compute n_heads if not provided
        if n_heads is None:
            # Find largest divisor that's reasonable (4-16 heads)
            for h in [12, 8, 6, 4]:
                if d_model % h == 0:
                    n_heads = h
                    break
            else:
                n_heads = 1  # Fallback

        self.d_model = d_model
        self.n_heads = n_heads
        self.spatial_radius = spatial_radius
        self.k_neighbors = k_neighbors
        self.enable_navigation = enable_navigation
        self.enable_lod = enable_lod
        self.navigation_max_steps = navigation_max_steps

        # Core attention mechanism (M1.3)
        self.attention = SpatialAttention(
            d_model=d_model,
            n_heads=n_heads,
            spatial_radius=spatial_radius,
            distance_decay="exponential",
        )

        # Navigator (M1.11)
        self.navigator = MomentumNavigator(
            d_model=d_model,
            momentum=0.9,
            initial_temperature=2.0,
            final_temperature=0.5,
            warp_threshold=0.95,
            max_speed=10.0,
            attention_radius=spatial_radius,
        )

        # LOD configuration (M1.10)
        self.lod_config = LODConfig()

    def get_lod_level(self, distance: float) -> LODLevel:
        """Get LOD level for a distance."""
        return self.lod_config.get_level_by_distance(distance)

    def _select_k_nearest(
        self,
        query_position: torch.Tensor,
        positions: torch.Tensor,
        embeddings: torch.Tensor,
        k: int,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Select k nearest tokens to query position.

        Returns:
            (selected_embeddings, selected_positions, selected_indices)
        """
        # Compute distances
        distances = torch.norm(positions - query_position.unsqueeze(0), dim=-1)

        # Get k nearest
        k = min(k, len(distances))
        _, indices = torch.topk(distances, k, largest=False)

        return embeddings[indices], positions[indices], indices

    def _apply_lod_compression(
        self,
        query_position: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, int]:
        """Apply LOD compression to context.

        Returns:
            (compressed_embeddings, compressed_positions, tokens_represented)
        """
        if not self.enable_lod:
            return embeddings, positions, len(embeddings)

        # Compute distances from query
        distances = torch.norm(positions - query_position.unsqueeze(0), dim=-1)

        compressed_emb_list = []
        compressed_pos_list = []
        tokens_represented = 0

        for level in self.lod_config.levels:
            # Find tokens in this level
            mask = (distances >= level.min_radius) & (distances < level.max_radius)
            level_emb = embeddings[mask]
            level_pos = positions[mask]

            if len(level_emb) == 0:
                continue

            # Compress if needed
            if level.compression_ratio > 1 and len(level_emb) > level.max_tokens:
                # Simple compression: average groups
                n_groups = min(level.max_tokens, len(level_emb) // level.compression_ratio)
                if n_groups > 0:
                    # Reshape and average
                    group_size = len(level_emb) // n_groups
                    compressed_emb = level_emb[: n_groups * group_size].view(
                        n_groups, group_size, -1
                    ).mean(dim=1)
                    compressed_pos = level_pos[: n_groups * group_size].view(
                        n_groups, group_size, -1
                    ).mean(dim=1)
                    tokens_represented += n_groups * group_size
                else:
                    compressed_emb = level_emb[:level.max_tokens]
                    compressed_pos = level_pos[:level.max_tokens]
                    tokens_represented += len(compressed_emb)
            else:
                # No compression needed
                compressed_emb = level_emb[:level.max_tokens]
                compressed_pos = level_pos[:level.max_tokens]
                tokens_represented += len(compressed_emb)

            compressed_emb_list.append(compressed_emb)
            compressed_pos_list.append(compressed_pos)

        if compressed_emb_list:
            return (
                torch.cat(compressed_emb_list, dim=0),
                torch.cat(compressed_pos_list, dim=0),
                tokens_represented,
            )
        return embeddings[:0], positions[:0], 0

    def query(
        self,
        query: torch.Tensor,
        context_embeddings: torch.Tensor,
        context_positions: torch.Tensor,
        target_embedding: Optional[torch.Tensor] = None,
        start_position: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, NavigationMetrics]:
        """Query context using navigation-guided attention.

        Args:
            query: Query embedding [d_model]
            context_embeddings: Context token embeddings [n, d_model]
            context_positions: Context token positions [n, 3]
            target_embedding: Target we're looking for (for metrics)
            start_position: Starting position (default: origin)

        Returns:
            (attended_output, metrics)
        """
        device = query.device
        metrics = NavigationMetrics()

        # Initialize position
        if start_position is None:
            start_position = torch.zeros(3, device=device)

        if self.enable_navigation:
            # Use M1.11 navigator
            self.navigator.reset(device=device)
            self.navigator._state.position = start_position.clone()

            nav_result = self.navigator.navigate(
                query=query,
                max_steps=self.navigation_max_steps,
                use_circle_jump=True,
                context_embeddings=context_embeddings,
                context_positions=context_positions,
            )

            query_position = nav_result.position
            metrics.steps_taken = nav_result.steps_taken
            metrics.warp_count = nav_result.warp_count
            metrics.converged = nav_result.converged
            metrics.trajectory_length = nav_result.trajectory_length
            metrics.temperature_schedule = nav_result.temperature_schedule
        else:
            # Baseline: stay at start position
            query_position = start_position
            metrics.steps_taken = 0

        # Apply LOD compression
        compressed_emb, compressed_pos, tokens_represented = self._apply_lod_compression(
            query_position, context_embeddings, context_positions
        )
        metrics.tokens_accessed = tokens_represented

        # Select k nearest from current position
        if len(compressed_emb) > 0:
            selected_emb, selected_pos, indices = self._select_k_nearest(
                query_position, compressed_pos, compressed_emb, self.k_neighbors
            )
        else:
            selected_emb = context_embeddings[:self.k_neighbors]
            selected_pos = context_positions[:self.k_neighbors]
            indices = torch.arange(min(self.k_neighbors, len(context_embeddings)))

        # Perform attention operation
        if len(selected_emb) > 0:
            # Reshape for attention: [1, k, d_model]
            x = selected_emb.unsqueeze(0)
            pos = selected_pos.unsqueeze(0)

            # Count attention operation
            metrics.attention_ops = 1

            # Run attention
            attended = self.attention(x, pos)
            output = attended.squeeze(0).mean(dim=0)  # Average pool to [d_model]
        else:
            output = torch.zeros(self.d_model, device=device)

        # Compute similarity to target if provided
        if target_embedding is not None:
            metrics.final_similarity = F.cosine_similarity(
                output.unsqueeze(0), target_embedding.unsqueeze(0)
            ).item()

        return output, metrics


class BaselineNavigator(nn.Module):
    """Baseline navigator for comparison (no M1.11 exploits).

    Simple greedy nearest-neighbor navigation without any of the
    strafe jumping optimizations. Used as comparison baseline.

    Navigation methods:
        - greedy: Move to nearest high-similarity token
        - random: Random walk
        - static: Stay at start position

    Args:
        d_model: Embedding dimension
        spatial_radius: Attention radius
        method: Navigation method ('greedy', 'random', 'static')
    """

    def __init__(
        self,
        d_model: int = 768,
        spatial_radius: float = 50.0,
        method: str = "greedy",
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.spatial_radius = spatial_radius
        self.method = method

    def navigate(
        self,
        query: torch.Tensor,
        context_embeddings: torch.Tensor,
        context_positions: torch.Tensor,
        start_position: torch.Tensor,
        max_steps: int = 10,
    ) -> tuple[torch.Tensor, int]:
        """Navigate to find relevant context.

        Returns:
            (final_position, steps_taken)
        """
        position = start_position.clone()
        steps = 0

        if self.method == "static":
            return position, 0

        for step in range(max_steps):
            steps += 1

            if self.method == "greedy":
                # Find highest similarity token within radius
                distances = torch.norm(
                    context_positions - position.unsqueeze(0), dim=-1
                )
                within_radius = distances <= self.spatial_radius * 3

                if within_radius.sum() == 0:
                    break

                # Compute similarities
                similarities = F.cosine_similarity(
                    context_embeddings, query.unsqueeze(0), dim=-1
                )
                similarities[~within_radius] = -float("inf")

                # Move toward best token
                best_idx = similarities.argmax()
                target = context_positions[best_idx]

                # Move partway toward target
                direction = target - position
                step_size = min(self.spatial_radius, torch.norm(direction).item())
                if torch.norm(direction) > 0:
                    position = position + direction / torch.norm(direction) * step_size

            elif self.method == "random":
                # Random step
                direction = torch.randn(3, device=position.device)
                direction = direction / torch.norm(direction) * self.spatial_radius
                position = position + direction

        return position, steps


class BaselineAttention(nn.Module):
    """Baseline attention without navigation (for comparison).

    Same as NavigationAttention but without M1.11 navigator.
    Uses simple greedy or static positioning.
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: Optional[int] = None,
        spatial_radius: float = 50.0,
        k_neighbors: int = 50,
        method: str = "greedy",
    ) -> None:
        super().__init__()

        # Auto-compute n_heads if not provided
        if n_heads is None:
            for h in [12, 8, 6, 4]:
                if d_model % h == 0:
                    n_heads = h
                    break
            else:
                n_heads = 1

        self.d_model = d_model
        self.spatial_radius = spatial_radius
        self.k_neighbors = k_neighbors

        self.attention = SpatialAttention(
            d_model=d_model,
            n_heads=n_heads,
            spatial_radius=spatial_radius,
        )

        self.navigator = BaselineNavigator(
            d_model=d_model,
            spatial_radius=spatial_radius,
            method=method,
        )

    def query(
        self,
        query: torch.Tensor,
        context_embeddings: torch.Tensor,
        context_positions: torch.Tensor,
        target_embedding: Optional[torch.Tensor] = None,
        start_position: Optional[torch.Tensor] = None,
        max_steps: int = 10,
    ) -> tuple[torch.Tensor, NavigationMetrics]:
        """Query context using baseline navigation."""
        device = query.device
        metrics = NavigationMetrics()

        if start_position is None:
            start_position = torch.zeros(3, device=device)

        # Navigate
        final_position, steps = self.navigator.navigate(
            query=query,
            context_embeddings=context_embeddings,
            context_positions=context_positions,
            start_position=start_position,
            max_steps=max_steps,
        )
        metrics.steps_taken = steps

        # Select k nearest
        distances = torch.norm(
            context_positions - final_position.unsqueeze(0), dim=-1
        )
        k = min(self.k_neighbors, len(distances))
        _, indices = torch.topk(distances, k, largest=False)

        selected_emb = context_embeddings[indices]
        selected_pos = context_positions[indices]
        metrics.tokens_accessed = k

        # Attention
        if len(selected_emb) > 0:
            x = selected_emb.unsqueeze(0)
            pos = selected_pos.unsqueeze(0)
            metrics.attention_ops = 1
            attended = self.attention(x, pos)
            output = attended.squeeze(0).mean(dim=0)
        else:
            output = torch.zeros(self.d_model, device=device)

        # Similarity
        if target_embedding is not None:
            metrics.final_similarity = F.cosine_similarity(
                output.unsqueeze(0), target_embedding.unsqueeze(0)
            ).item()

        return output, metrics
