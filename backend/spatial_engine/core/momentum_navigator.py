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
momentum_navigator.py - Strafe jumping navigation for spatial attention.

Implements momentum-based semantic navigation inspired by Quake's strafe jump physics.
Exploits 7 validated structures in INFINITE's architecture for faster context traversal:

1. Warp Lanes (Exploit 1) - semantic warping across distance
2. Shell Memory (Exploit 2) - optimal placement at 2.9r boundary
3. LOD Hopping (Exploit 3) - boundary optimization
6. Bunny Hop Momentum (Exploit 6) - velocity accumulation
7. Circle Jump (Exploit 7) - two-phase navigation
8. Temperature Surfing (Exploit 8) - adaptive softmax
9. Attention Ratchet (Exploit 9) - directed warp awareness

NOTE: Exploits 4 (diagonal speed) and 5 (harmonic resonance) were invalidated
during code analysis - see ideas/001-strafe-jumping-navigation.md for details.

Author: Adolfo Lopez (ch1pu)
Milestone: 1.11 - Strafe Jumping Navigation
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class NavigationState:
    """Complete state for momentum-based navigation.

    Tracks position, velocity, temperature, and navigation history
    for the MomentumNavigator.

    Attributes:
        position: Current 3D position in semantic space [3]
        velocity: Current velocity vector [3]
        temperature: Current softmax temperature for attention
        hop_count: Number of momentum hops performed
        warp_count: Number of warp lane jumps performed
        trajectory: History of positions visited
        step: Current navigation step
    """

    position: torch.Tensor
    velocity: torch.Tensor
    temperature: float = 2.0
    hop_count: int = 0
    warp_count: int = 0
    trajectory: list[torch.Tensor] = field(default_factory=list)
    step: int = 0

    def clone(self) -> "NavigationState":
        """Create a deep copy of the navigation state."""
        return NavigationState(
            position=self.position.clone(),
            velocity=self.velocity.clone(),
            temperature=self.temperature,
            hop_count=self.hop_count,
            warp_count=self.warp_count,
            trajectory=[t.clone() for t in self.trajectory],
            step=self.step,
        )


@dataclass
class NavigationResult:
    """Result of a navigation operation.

    Attributes:
        position: Final position reached [3]
        steps_taken: Number of steps to reach position
        hop_count: Number of momentum hops used
        warp_count: Number of warp lanes used
        final_speed: Final velocity magnitude
        trajectory_length: Total distance traveled
        converged: Whether navigation converged
        temperature_schedule: List of temperatures used
    """

    position: torch.Tensor
    steps_taken: int
    hop_count: int
    warp_count: int
    final_speed: float
    trajectory_length: float
    converged: bool
    temperature_schedule: list[float] = field(default_factory=list)


class MomentumNavigator(nn.Module):
    """Momentum-based semantic navigation with strafe jump physics.

    Implements 7 validated exploits for faster context traversal:
    - Warp lanes through high-similarity distant tokens
    - Shell memory organization at optimal distances
    - LOD boundary awareness
    - Bunny hop momentum accumulation
    - Circle jump initialization
    - Temperature surfing
    - Attention ratchet (directed warp awareness)

    Args:
        d_model: Embedding dimension (default: 768)
        momentum: Momentum coefficient for velocity accumulation (default: 0.9)
        initial_temperature: Starting temperature for exploration (default: 2.0)
        final_temperature: Ending temperature for exploitation (default: 0.5)
        warp_threshold: Minimum similarity for warp lanes (default: 0.95)
        max_speed: Maximum per-axis velocity (default: 10.0)
        attention_radius: Base attention radius (default: 50.0)
        convergence_threshold: Movement threshold for convergence (default: 0.1)

    Example:
        ```python
        navigator = MomentumNavigator(d_model=768)

        # Reset to starting position
        navigator.reset(torch.zeros(3))

        # Navigate with a query
        query = torch.randn(768)
        context = torch.randn(768)
        new_pos, info = navigator.step(query, context)

        # Full navigation
        result = navigator.navigate(query, max_steps=10)
        ```
    """

    # LOD boundaries from lod.py (validated in research)
    LOD_BOUNDARIES = [50.0, 150.0, 500.0]

    # Shell radii for optimal token placement (just inside boundaries)
    SHELL_RADII = [0.9, 1.9, 2.9]  # Relative to attention radius

    def __init__(
        self,
        d_model: int = 768,
        momentum: float = 0.9,
        initial_temperature: float = 2.0,
        final_temperature: float = 0.5,
        warp_threshold: float = 0.95,
        max_speed: float = 10.0,
        attention_radius: float = 50.0,
        convergence_threshold: float = 0.1,
    ):
        """Initialize the momentum navigator."""
        super().__init__()

        self.d_model = d_model
        self.momentum = momentum
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.warp_threshold = warp_threshold
        self.max_speed = max_speed
        self.attention_radius = attention_radius
        self.convergence_threshold = convergence_threshold

        # Learned components for direction and speed prediction
        self.direction_predictor = nn.Linear(d_model, 3)
        self.speed_predictor = nn.Linear(d_model, 1)

        # Query broadener for circle jump (Exploit 7)
        self.query_broadener = nn.Linear(d_model, d_model)

        # Navigation state (initialized on reset)
        self._state: Optional[NavigationState] = None

        # Exploit tracking for adaptive disabling
        self._exploit_success: dict[str, deque] = {
            "warp_lanes": deque(maxlen=100),
            "shell_memory": deque(maxlen=100),
            "lod_hopping": deque(maxlen=100),
            "bunny_hop": deque(maxlen=100),
            "circle_jump": deque(maxlen=100),
            "temp_surfing": deque(maxlen=100),
            "attention_ratchet": deque(maxlen=100),
        }
        self._exploit_enabled: dict[str, bool] = {
            "warp_lanes": True,
            "shell_memory": True,
            "lod_hopping": True,
            "bunny_hop": True,
            "circle_jump": True,
            "temp_surfing": True,
            "attention_ratchet": True,
        }

    @property
    def state(self) -> Optional[NavigationState]:
        """Get current navigation state."""
        return self._state

    def reset(
        self,
        start_position: Optional[torch.Tensor] = None,
        device: Optional[torch.device] = None,
    ) -> None:
        """Reset navigator to starting position.

        Args:
            start_position: Initial position [3] (default: origin)
            device: Device for tensors (default: CPU)
        """
        if device is None:
            device = start_position.device if start_position is not None else torch.device("cpu")

        if start_position is None:
            start_position = torch.zeros(3, device=device)
        else:
            start_position = start_position.to(device)

        self._state = NavigationState(
            position=start_position.clone(),
            velocity=torch.zeros(3, device=device),
            temperature=self.initial_temperature,
            hop_count=0,
            warp_count=0,
            trajectory=[start_position.clone()],
            step=0,
        )

    def step(
        self,
        query: torch.Tensor,
        context_summary: Optional[torch.Tensor] = None,
        max_steps: int = 10,
    ) -> tuple[torch.Tensor, dict]:
        """Perform a single navigation step.

        Applies momentum-based physics with bunny hop accumulation.

        Args:
            query: Query embedding [d_model]
            context_summary: Optional context embedding [d_model]
            max_steps: Maximum steps for temperature scheduling

        Returns:
            new_position: Updated position [3]
            info: Navigation metadata dict
        """
        if self._state is None:
            self.reset(device=query.device)

        assert self._state is not None  # Type narrowing

        # EXPLOIT 8: Temperature Surfing
        if self._exploit_enabled["temp_surfing"]:
            self._state.temperature = self._schedule_temperature(
                self._state.step, max_steps
            )

        # Predict navigation direction from query
        direction = self._predict_direction(query)

        # Predict speed from query
        speed = self._predict_speed(query)

        # EXPLOIT 6: Bunny Hop Momentum
        if self._exploit_enabled["bunny_hop"]:
            # Accumulate momentum instead of resetting
            new_velocity = (
                self.momentum * self._state.velocity
                + (1 - self.momentum) * direction * speed
            )
        else:
            new_velocity = direction * speed

        # Per-axis velocity capping (not total magnitude)
        new_velocity = torch.clamp(new_velocity, -self.max_speed, self.max_speed)

        # Update state
        self._state.velocity = new_velocity
        self._state.position = self._state.position + self._state.velocity
        self._state.hop_count += 1
        self._state.step += 1
        self._state.trajectory.append(self._state.position.clone())

        # Build info dict
        info = {
            "speed": torch.norm(self._state.velocity).item(),
            "temperature": self._state.temperature,
            "hop_count": self._state.hop_count,
            "step": self._state.step,
            "velocity": self._state.velocity.detach().cpu().numpy().tolist(),
        }

        return self._state.position.clone(), info

    def navigate(
        self,
        query: torch.Tensor,
        max_steps: int = 10,
        use_circle_jump: bool = True,
        context_embeddings: Optional[torch.Tensor] = None,
        context_positions: Optional[torch.Tensor] = None,
    ) -> NavigationResult:
        """Full navigation with all enabled exploits.

        Args:
            query: Query embedding [d_model]
            max_steps: Maximum navigation steps
            use_circle_jump: Whether to use warm-up query (Exploit 7)
            context_embeddings: Optional token embeddings [n, d_model]
            context_positions: Optional token positions [n, 3]

        Returns:
            NavigationResult with final position and metrics
        """
        if self._state is None:
            self.reset(device=query.device)

        assert self._state is not None  # Type narrowing

        temperature_schedule: list[float] = []

        # EXPLOIT 7: Circle Jump Initialization
        if use_circle_jump and self._exploit_enabled["circle_jump"]:
            broad_query = self._broaden_query(query)
            warmup_position = self._initial_jump(
                broad_query, context_embeddings, context_positions
            )
            if warmup_position is not None:
                self._state.position = warmup_position
                self._state.trajectory.append(warmup_position.clone())

        converged = False
        for step in range(max_steps):
            # EXPLOIT 8: Temperature Surfing
            if self._exploit_enabled["temp_surfing"]:
                self._state.temperature = self._schedule_temperature(step, max_steps)
            temperature_schedule.append(self._state.temperature)

            # Perform navigation step
            _, _ = self.step(query, max_steps=max_steps)

            # EXPLOIT 1: Check for Warp Lanes
            if (
                self._exploit_enabled["warp_lanes"]
                and context_embeddings is not None
                and context_positions is not None
            ):
                warp_target = self._find_warp_lane(
                    query, context_embeddings, context_positions
                )
                if warp_target is not None:
                    # EXPLOIT 9: Check reversibility
                    if self._exploit_enabled["attention_ratchet"]:
                        if self._is_reversible_warp(warp_target):
                            self._state.position = warp_target
                            self._state.warp_count += 1
                            self._state.trajectory.append(warp_target.clone())
                        else:
                            # One-way warp - only use if confident
                            if self._should_commit_warp(
                                context_embeddings, context_positions, warp_target
                            ):
                                self._state.position = warp_target
                                self._state.warp_count += 1
                                self._state.trajectory.append(warp_target.clone())
                    else:
                        self._state.position = warp_target
                        self._state.warp_count += 1
                        self._state.trajectory.append(warp_target.clone())

            # EXPLOIT 2 & 3: Shell memory and LOD boundary optimization
            if self._exploit_enabled["shell_memory"]:
                self._state.position = self._snap_to_shell(self._state.position)

            if self._exploit_enabled["lod_hopping"]:
                self._state.position = self._respect_lod_boundaries(self._state.position)

            # Check convergence
            if self._has_converged():
                converged = True
                break

        # Calculate trajectory length
        trajectory_length = 0.0
        for i in range(len(self._state.trajectory) - 1):
            trajectory_length += torch.norm(
                self._state.trajectory[i + 1] - self._state.trajectory[i]
            ).item()

        return NavigationResult(
            position=self._state.position.clone(),
            steps_taken=self._state.step,
            hop_count=self._state.hop_count,
            warp_count=self._state.warp_count,
            final_speed=torch.norm(self._state.velocity).item(),
            trajectory_length=trajectory_length,
            converged=converged,
            temperature_schedule=temperature_schedule,
        )

    def _schedule_temperature(self, step: int, max_steps: int) -> float:
        """EXPLOIT 8: Anneal temperature from exploration to exploitation.

        Args:
            step: Current step
            max_steps: Maximum steps

        Returns:
            Scheduled temperature value
        """
        if max_steps <= 0:
            return self.initial_temperature

        progress = min(step / max_steps, 1.0)
        return (
            self.initial_temperature * (1 - progress)
            + self.final_temperature * progress
        )

    def _predict_direction(self, query: torch.Tensor) -> torch.Tensor:
        """Predict navigation direction from query embedding.

        Args:
            query: Query embedding [d_model]

        Returns:
            Normalized direction vector [3]
        """
        direction = self.direction_predictor(query)
        # Normalize to unit vector
        norm = torch.norm(direction)
        if norm > 1e-6:
            direction = direction / norm
        return direction

    def _predict_speed(self, query: torch.Tensor) -> torch.Tensor:
        """Predict navigation speed from query embedding.

        Args:
            query: Query embedding [d_model]

        Returns:
            Speed scalar (0 to max_speed)
        """
        raw_speed = self.speed_predictor(query)
        return torch.sigmoid(raw_speed) * self.max_speed

    def _broaden_query(self, query: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 7: Create broad version of query for circle jump.

        Args:
            query: Specific query embedding [d_model]

        Returns:
            Broadened query embedding [d_model]
        """
        broad = self.query_broadener(query)
        # Mix with original to maintain relevance
        return 0.7 * broad + 0.3 * query

    def _initial_jump(
        self,
        broad_query: torch.Tensor,
        embeddings: Optional[torch.Tensor],
        positions: Optional[torch.Tensor],
    ) -> Optional[torch.Tensor]:
        """EXPLOIT 7: Find good starting position with broad query.

        Args:
            broad_query: Broadened query embedding [d_model]
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]

        Returns:
            Centroid position of top matches, or None
        """
        if embeddings is None or positions is None:
            return None

        if len(embeddings) == 0:
            return None

        # Compute similarities
        similarities = F.cosine_similarity(
            broad_query.unsqueeze(0), embeddings, dim=-1
        )

        # Get top-k results (up to 10)
        k = min(10, len(embeddings))
        _, top_indices = torch.topk(similarities, k)

        # Return centroid of top positions
        top_positions = positions[top_indices]
        return top_positions.mean(dim=0)

    def _find_warp_lane(
        self,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
    ) -> Optional[torch.Tensor]:
        """EXPLOIT 1: Find distant high-similarity tokens for warping.

        Args:
            query: Query embedding [d_model]
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]

        Returns:
            Position of warp target, or None
        """
        if self._state is None:
            return None

        # Compute distances from current position
        distances = torch.norm(positions - self._state.position, dim=-1)

        # Find tokens beyond normal attention range
        min_warp_distance = 2 * self.attention_radius
        max_warp_distance = 10 * self.attention_radius
        distant_mask = (distances > min_warp_distance) & (distances < max_warp_distance)

        if not distant_mask.any():
            return None

        # Filter to distant tokens
        distant_embeddings = embeddings[distant_mask]
        distant_positions = positions[distant_mask]

        # Compute similarities
        similarities = F.cosine_similarity(
            query.unsqueeze(0), distant_embeddings, dim=-1
        )

        # Find high-similarity warp targets
        warp_mask = similarities > self.warp_threshold

        if not warp_mask.any():
            return None

        # Return position of highest similarity target
        warp_similarities = similarities[warp_mask]
        warp_positions = distant_positions[warp_mask]
        best_idx = torch.argmax(warp_similarities)

        return warp_positions[best_idx]

    def _is_reversible_warp(self, target_position: torch.Tensor) -> bool:
        """EXPLOIT 9: Check if warp can be reversed.

        Args:
            target_position: Target position [3]

        Returns:
            True if warp is geometrically reversible
        """
        if self._state is None:
            return False

        distance = torch.norm(target_position - self._state.position).item()
        # Geometrically reversible if within 3r from both ends
        return distance < 3 * self.attention_radius

    def _should_commit_warp(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        target_position: torch.Tensor,
    ) -> bool:
        """EXPLOIT 9: Decide whether to take a one-way warp.

        Args:
            embeddings: Token embeddings [n, d_model]
            positions: Token positions [n, 3]
            target_position: Target position [3]

        Returns:
            True if target region is rich enough to commit
        """
        # Count tokens near target
        distances = torch.norm(positions - target_position, dim=-1)
        nearby_count = (distances < self.attention_radius).sum().item()

        # Commit if target region is rich (>20 nearby tokens)
        return nearby_count > 20

    def _snap_to_shell(self, position: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 2: Snap to optimal shell distances.

        Shell radii are positioned just inside attention boundaries
        to maximize token visibility.

        Args:
            position: Current position [3]

        Returns:
            Position snapped to nearest shell (or unchanged)
        """
        if self._state is None:
            return position

        # Calculate distance from origin (or could be from focus point)
        origin = torch.zeros_like(position)
        distance = torch.norm(position - origin).item()

        if distance < 1e-6:
            return position

        # Check if near a shell boundary
        shell_tolerance = 0.2 * self.attention_radius

        for i, shell_radius in enumerate(self.SHELL_RADII):
            actual_radius = shell_radius * self.attention_radius
            if abs(distance - actual_radius) < shell_tolerance:
                # Already near a shell, return unchanged
                return position

        # Find nearest shell
        min_diff = float("inf")
        target_radius = distance  # Default: no change

        for shell_radius in self.SHELL_RADII:
            actual_radius = shell_radius * self.attention_radius
            diff = abs(distance - actual_radius)
            if diff < min_diff:
                min_diff = diff
                target_radius = actual_radius

        # Only snap if we're close to a shell
        if min_diff < self.attention_radius:
            # Scale position to shell radius
            direction = position / distance
            return direction * target_radius

        return position

    def _respect_lod_boundaries(self, position: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 3: Stay inside beneficial LOD boundaries.

        If position is just past an LOD boundary, pull it back
        to maintain higher fidelity.

        Args:
            position: Current position [3]

        Returns:
            Position adjusted to respect LOD boundaries
        """
        origin = torch.zeros_like(position)
        distance = torch.norm(position - origin).item()

        if distance < 1e-6:
            return position

        # Check each LOD boundary
        boundary_tolerance = 5.0  # Pull back if within 5 units past boundary

        for boundary in self.LOD_BOUNDARIES:
            if boundary < distance < boundary + boundary_tolerance:
                # Pull back to just inside boundary
                direction = position / distance
                return direction * (boundary - 0.1)

        return position

    def _has_converged(self) -> bool:
        """Check if navigation has converged.

        Returns:
            True if recent movement is below threshold
        """
        if self._state is None or len(self._state.trajectory) < 2:
            return False

        recent_movement = torch.norm(
            self._state.trajectory[-1] - self._state.trajectory[-2]
        ).item()

        return recent_movement < self.convergence_threshold

    def update_exploit_success(self, exploit_name: str, success: bool) -> None:
        """Track exploit success for adaptive disabling.

        Args:
            exploit_name: Name of the exploit
            success: Whether the exploit helped
        """
        if exploit_name not in self._exploit_success:
            return

        self._exploit_success[exploit_name].append(success)

        # Check if exploit should be disabled
        history = self._exploit_success[exploit_name]
        if len(history) >= 50:
            success_rate = sum(history) / len(history)
            if success_rate < 0.1:  # Less than 10% success
                self._exploit_enabled[exploit_name] = False

    def enable_exploit(self, exploit_name: str) -> None:
        """Manually enable an exploit.

        Args:
            exploit_name: Name of the exploit to enable
        """
        if exploit_name in self._exploit_enabled:
            self._exploit_enabled[exploit_name] = True

    def disable_exploit(self, exploit_name: str) -> None:
        """Manually disable an exploit.

        Args:
            exploit_name: Name of the exploit to disable
        """
        if exploit_name in self._exploit_enabled:
            self._exploit_enabled[exploit_name] = False

    def get_enabled_exploits(self) -> list[str]:
        """Get list of currently enabled exploits.

        Returns:
            List of enabled exploit names
        """
        return [name for name, enabled in self._exploit_enabled.items() if enabled]

    def forward(
        self,
        query: torch.Tensor,
        context_embeddings: Optional[torch.Tensor] = None,
        context_positions: Optional[torch.Tensor] = None,
        max_steps: int = 10,
    ) -> torch.Tensor:
        """Forward pass for training.

        Args:
            query: Query embedding [batch, d_model] or [d_model]
            context_embeddings: Optional [batch, n, d_model] or [n, d_model]
            context_positions: Optional [batch, n, 3] or [n, 3]
            max_steps: Maximum navigation steps

        Returns:
            Final position [batch, 3] or [3]
        """
        # Handle batched input
        if query.dim() == 2:
            batch_size = query.size(0)
            results = []
            for i in range(batch_size):
                self.reset(device=query.device)
                ctx_emb = context_embeddings[i] if context_embeddings is not None else None
                ctx_pos = context_positions[i] if context_positions is not None else None
                result = self.navigate(
                    query[i],
                    max_steps=max_steps,
                    context_embeddings=ctx_emb,
                    context_positions=ctx_pos,
                )
                results.append(result.position)
            return torch.stack(results)

        # Single query
        self.reset(device=query.device)
        result = self.navigate(
            query,
            max_steps=max_steps,
            context_embeddings=context_embeddings,
            context_positions=context_positions,
        )
        return result.position
