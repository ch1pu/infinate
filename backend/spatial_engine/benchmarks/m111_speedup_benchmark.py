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
m111_speedup_benchmark.py - Comprehensive speedup benchmarks for M1.11 navigation.

Measures actual speedup of strafe jumping navigation vs baseline by comparing:
1. Steps to reach target
2. Attention operations performed
3. Quality of retrieved context (similarity to target)
4. End-to-end latency

Test scenarios:
- Semantic clusters (related tokens grouped spatially)
- Warp lane scenarios (distant high-similarity tokens)
- Random distributions
- Various scales (1K, 10K, 100K tokens)

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11 - Strafe Jumping Navigation
"""

import statistics
import time
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn.functional as F


@dataclass
class SemanticCluster:
    """A cluster of semantically related tokens.

    Attributes:
        center_embedding: The semantic center of this cluster
        center_position: The spatial center of this cluster
        tokens: Number of tokens in the cluster
        spread: Spatial spread of tokens around center
    """

    center_embedding: torch.Tensor
    center_position: torch.Tensor
    tokens: int
    spread: float


@dataclass
class TestScenario:
    """A test scenario with context and target.

    Attributes:
        name: Scenario name
        context_embeddings: All context token embeddings
        context_positions: All context token positions
        target_embedding: What we're looking for
        target_position: Where the target is (for ground truth)
        target_indices: Indices of target-related tokens
        description: Human-readable description
    """

    name: str
    context_embeddings: torch.Tensor
    context_positions: torch.Tensor
    target_embedding: torch.Tensor
    target_position: torch.Tensor
    target_indices: torch.Tensor
    description: str = ""


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run.

    Attributes:
        scenario: Name of the scenario
        method: Navigation method used
        steps_taken: Number of navigation steps
        attention_ops: Number of attention operations
        tokens_accessed: Total tokens attended
        final_similarity: Cosine similarity to target
        latency_ms: End-to-end latency in milliseconds
        converged: Whether navigation converged
        warp_count: Number of warps (M1.11 only)
        target_found: Whether target tokens were in retrieved set
    """

    scenario: str
    method: str
    steps_taken: int
    attention_ops: int
    tokens_accessed: int
    final_similarity: float
    latency_ms: float
    converged: bool
    warp_count: int = 0
    target_found: bool = False


@dataclass
class SpeedupResult:
    """Comparison result between M1.11 and baseline.

    Attributes:
        scenario: Name of the scenario
        m111_results: Results from M1.11 navigation
        baseline_results: Results from baseline
        steps_speedup: Ratio of baseline steps / M1.11 steps
        latency_speedup: Ratio of baseline latency / M1.11 latency
        quality_improvement: M1.11 similarity - baseline similarity
    """

    scenario: str
    m111_results: BenchmarkResult
    baseline_results: BenchmarkResult
    steps_speedup: float = 0.0
    latency_speedup: float = 0.0
    quality_improvement: float = 0.0

    def __post_init__(self) -> None:
        if self.baseline_results.steps_taken > 0:
            self.steps_speedup = (
                self.baseline_results.steps_taken / max(1, self.m111_results.steps_taken)
            )
        if self.baseline_results.latency_ms > 0:
            self.latency_speedup = (
                self.baseline_results.latency_ms / max(0.001, self.m111_results.latency_ms)
            )
        self.quality_improvement = (
            self.m111_results.final_similarity - self.baseline_results.final_similarity
        )


class SemanticDataGenerator:
    """Generator for semantic test data with realistic structure.

    Creates test scenarios with:
    - Semantic clusters (related tokens grouped spatially)
    - Warp lane opportunities (distant high-similarity tokens)
    - Noise tokens (random embeddings)
    - Target tokens (what navigation should find)
    """

    def __init__(
        self,
        d_model: int = 768,
        device: Optional[torch.device] = None,
    ) -> None:
        self.d_model = d_model
        self.device = device or torch.device("cpu")

    def _create_cluster(
        self,
        base_embedding: torch.Tensor,
        center_position: torch.Tensor,
        n_tokens: int,
        semantic_noise: float = 0.1,
        spatial_spread: float = 30.0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Create a cluster of semantically similar tokens.

        Args:
            base_embedding: Semantic center [d_model]
            center_position: Spatial center [3]
            n_tokens: Number of tokens to create
            semantic_noise: How much to vary embeddings
            spatial_spread: Spatial radius of cluster

        Returns:
            (embeddings [n, d_model], positions [n, 3])
        """
        # Create semantically similar embeddings
        noise = torch.randn(n_tokens, self.d_model, device=self.device) * semantic_noise
        embeddings = base_embedding.unsqueeze(0) + noise
        embeddings = F.normalize(embeddings, dim=-1)

        # Create spatially clustered positions
        offsets = torch.randn(n_tokens, 3, device=self.device) * spatial_spread
        positions = center_position.unsqueeze(0) + offsets

        return embeddings, positions

    def create_clustered_scenario(
        self,
        n_clusters: int = 5,
        tokens_per_cluster: int = 100,
        noise_tokens: int = 500,
        world_size: float = 500.0,
    ) -> TestScenario:
        """Create scenario with semantic clusters.

        One cluster is the 'target' - navigation should find it.
        """
        all_embeddings = []
        all_positions = []
        target_start_idx = 0

        # Create base embeddings for clusters (orthogonal-ish)
        cluster_bases = torch.randn(n_clusters, self.d_model, device=self.device)
        cluster_bases = F.normalize(cluster_bases, dim=-1)

        # Create cluster positions spread across world
        cluster_centers = torch.randn(n_clusters, 3, device=self.device) * (world_size / 2)

        for i in range(n_clusters):
            if i == 0:
                target_start_idx = sum(len(e) for e in all_embeddings)

            emb, pos = self._create_cluster(
                cluster_bases[i],
                cluster_centers[i],
                tokens_per_cluster,
                semantic_noise=0.1,
                spatial_spread=30.0,
            )
            all_embeddings.append(emb)
            all_positions.append(pos)

        # Add noise tokens
        noise_emb = torch.randn(noise_tokens, self.d_model, device=self.device)
        noise_emb = F.normalize(noise_emb, dim=-1)
        noise_pos = torch.randn(noise_tokens, 3, device=self.device) * world_size
        all_embeddings.append(noise_emb)
        all_positions.append(noise_pos)

        context_embeddings = torch.cat(all_embeddings, dim=0)
        context_positions = torch.cat(all_positions, dim=0)

        # Target is the first cluster
        target_embedding = cluster_bases[0]
        target_position = cluster_centers[0]
        target_indices = torch.arange(
            target_start_idx, target_start_idx + tokens_per_cluster
        )

        return TestScenario(
            name=f"clustered_{n_clusters}c_{tokens_per_cluster}t",
            context_embeddings=context_embeddings,
            context_positions=context_positions,
            target_embedding=target_embedding,
            target_position=target_position,
            target_indices=target_indices,
            description=f"{n_clusters} semantic clusters, {tokens_per_cluster} tokens each, "
                       f"{noise_tokens} noise tokens",
        )

    def create_warp_lane_scenario(
        self,
        n_tokens: int = 1000,
        n_warp_targets: int = 10,
        warp_distance: float = 300.0,
        world_size: float = 500.0,
    ) -> TestScenario:
        """Create scenario with warp lane opportunities.

        Places high-similarity tokens far from query position,
        testing M1.11's warp lane detection.
        """
        # Create main context (random)
        context_emb = torch.randn(n_tokens - n_warp_targets, self.d_model, device=self.device)
        context_emb = F.normalize(context_emb, dim=-1)
        context_pos = torch.randn(n_tokens - n_warp_targets, 3, device=self.device) * world_size

        # Create target embedding
        target_embedding = torch.randn(self.d_model, device=self.device)
        target_embedding = F.normalize(target_embedding, dim=0)

        # Place warp targets (high similarity) far from origin
        warp_emb = target_embedding.unsqueeze(0).expand(n_warp_targets, -1)
        warp_emb = warp_emb + torch.randn(n_warp_targets, self.d_model, device=self.device) * 0.05
        warp_emb = F.normalize(warp_emb, dim=-1)

        # Position warp targets at distance
        directions = torch.randn(n_warp_targets, 3, device=self.device)
        directions = F.normalize(directions, dim=-1)
        warp_pos = directions * warp_distance

        # Combine
        all_emb = torch.cat([context_emb, warp_emb], dim=0)
        all_pos = torch.cat([context_pos, warp_pos], dim=0)

        target_indices = torch.arange(n_tokens - n_warp_targets, n_tokens)
        target_position = warp_pos.mean(dim=0)

        return TestScenario(
            name=f"warp_lane_{n_warp_targets}t_d{int(warp_distance)}",
            context_embeddings=all_emb,
            context_positions=all_pos,
            target_embedding=target_embedding,
            target_position=target_position,
            target_indices=target_indices,
            description=f"{n_warp_targets} high-similarity tokens at distance {warp_distance}",
        )

    def create_scale_scenario(
        self,
        n_tokens: int,
        target_distance: float = 200.0,
    ) -> TestScenario:
        """Create scenario at specific scale for scaling tests."""
        # Random context
        context_emb = torch.randn(n_tokens, self.d_model, device=self.device)
        context_emb = F.normalize(context_emb, dim=-1)
        context_pos = torch.randn(n_tokens, 3, device=self.device) * 500.0

        # Target embedding
        target_embedding = torch.randn(self.d_model, device=self.device)
        target_embedding = F.normalize(target_embedding, dim=0)

        # Place some similar tokens at target distance
        n_targets = max(10, n_tokens // 100)
        target_indices = torch.randperm(n_tokens)[:n_targets]

        # Make these tokens similar to target
        context_emb[target_indices] = target_embedding + torch.randn(
            n_targets, self.d_model, device=self.device
        ) * 0.1
        context_emb[target_indices] = F.normalize(context_emb[target_indices], dim=-1)

        # Position them at target distance
        directions = torch.randn(n_targets, 3, device=self.device)
        directions = F.normalize(directions, dim=-1)
        context_pos[target_indices] = directions * target_distance

        target_position = context_pos[target_indices].mean(dim=0)

        return TestScenario(
            name=f"scale_{n_tokens}",
            context_embeddings=context_emb,
            context_positions=context_pos,
            target_embedding=target_embedding,
            target_position=target_position,
            target_indices=target_indices,
            description=f"Scale test with {n_tokens} tokens",
        )


class M111SpeedupBenchmark:
    """Comprehensive benchmark suite for M1.11 speedup measurement.

    Compares NavigationAttention (M1.11) vs BaselineAttention across
    multiple scenarios and scales.
    """

    def __init__(
        self,
        d_model: int = 768,
        device: Optional[torch.device] = None,
    ) -> None:
        self.d_model = d_model
        self.device = device or torch.device("cpu")
        self.data_generator = SemanticDataGenerator(d_model, device)

        # Import here to avoid circular imports
        from spatial_engine.integration.navigation_attention import (
            BaselineAttention,
            NavigationAttention,
        )

        self.nav_attention = NavigationAttention(
            d_model=d_model,
            enable_navigation=True,
            enable_lod=True,
        ).to(self.device)

        self.baseline_greedy = BaselineAttention(
            d_model=d_model,
            method="greedy",
        ).to(self.device)

        self.baseline_static = BaselineAttention(
            d_model=d_model,
            method="static",
        ).to(self.device)

    def run_single_benchmark(
        self,
        scenario: TestScenario,
        method: str,
        attention_module,
        iterations: int = 10,
    ) -> BenchmarkResult:
        """Run benchmark for a single method on a scenario."""
        latencies = []
        total_steps = 0
        total_ops = 0
        total_tokens = 0
        total_similarity = 0.0
        total_converged = 0
        total_warps = 0

        query = scenario.target_embedding
        start_pos = torch.zeros(3, device=self.device)

        for _ in range(iterations):
            torch.cuda.synchronize() if self.device.type == "cuda" else None
            start = time.perf_counter()

            output, metrics = attention_module.query(
                query=query,
                context_embeddings=scenario.context_embeddings,
                context_positions=scenario.context_positions,
                target_embedding=scenario.target_embedding,
                start_position=start_pos,
            )

            torch.cuda.synchronize() if self.device.type == "cuda" else None
            end = time.perf_counter()

            latencies.append((end - start) * 1000)
            total_steps += metrics.steps_taken
            total_ops += metrics.attention_ops
            total_tokens += metrics.tokens_accessed
            total_similarity += metrics.final_similarity
            if metrics.converged:
                total_converged += 1
            total_warps += metrics.warp_count

        return BenchmarkResult(
            scenario=scenario.name,
            method=method,
            steps_taken=total_steps // iterations,
            attention_ops=total_ops // iterations,
            tokens_accessed=total_tokens // iterations,
            final_similarity=total_similarity / iterations,
            latency_ms=statistics.mean(latencies),
            converged=total_converged > iterations // 2,
            warp_count=total_warps // iterations,
        )

    def compare_methods(
        self,
        scenario: TestScenario,
        iterations: int = 10,
    ) -> SpeedupResult:
        """Compare M1.11 vs baseline on a scenario."""
        m111_result = self.run_single_benchmark(
            scenario, "m111_navigation", self.nav_attention, iterations
        )
        baseline_result = self.run_single_benchmark(
            scenario, "baseline_greedy", self.baseline_greedy, iterations
        )

        return SpeedupResult(
            scenario=scenario.name,
            m111_results=m111_result,
            baseline_results=baseline_result,
        )

    def run_full_benchmark(
        self,
        iterations: int = 10,
    ) -> list[SpeedupResult]:
        """Run full benchmark suite across all scenarios."""
        results = []

        # Scenario 1: Clustered semantic data
        print("\n" + "=" * 70)
        print("SCENARIO 1: Semantic Clusters")
        print("=" * 70)
        scenario = self.data_generator.create_clustered_scenario(
            n_clusters=5, tokens_per_cluster=100, noise_tokens=500
        )
        result = self.compare_methods(scenario, iterations)
        results.append(result)
        self._print_result(result)

        # Scenario 2: Warp lane opportunities
        print("\n" + "=" * 70)
        print("SCENARIO 2: Warp Lane Targets")
        print("=" * 70)
        scenario = self.data_generator.create_warp_lane_scenario(
            n_tokens=1000, n_warp_targets=10, warp_distance=300.0
        )
        result = self.compare_methods(scenario, iterations)
        results.append(result)
        self._print_result(result)

        # Scenario 3-5: Scale tests
        for n_tokens in [1000, 5000, 10000]:
            print("\n" + "=" * 70)
            print(f"SCENARIO: Scale Test ({n_tokens} tokens)")
            print("=" * 70)
            scenario = self.data_generator.create_scale_scenario(n_tokens)
            result = self.compare_methods(scenario, iterations)
            results.append(result)
            self._print_result(result)

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY: M1.11 vs Baseline")
        print("=" * 70)
        self._print_summary(results)

        return results

    def _print_result(self, result: SpeedupResult) -> None:
        """Print a single comparison result."""
        print(f"\nScenario: {result.scenario}")
        print("-" * 50)
        print(f"{'Metric':<25} {'M1.11':<15} {'Baseline':<15} {'Speedup':<10}")
        print("-" * 50)
        print(
            f"{'Steps':<25} {result.m111_results.steps_taken:<15} "
            f"{result.baseline_results.steps_taken:<15} {result.steps_speedup:.2f}x"
        )
        print(
            f"{'Latency (ms)':<25} {result.m111_results.latency_ms:<15.2f} "
            f"{result.baseline_results.latency_ms:<15.2f} {result.latency_speedup:.2f}x"
        )
        print(
            f"{'Similarity':<25} {result.m111_results.final_similarity:<15.3f} "
            f"{result.baseline_results.final_similarity:<15.3f} "
            f"{'+' if result.quality_improvement >= 0 else ''}{result.quality_improvement:.3f}"
        )
        print(
            f"{'Warps':<25} {result.m111_results.warp_count:<15} "
            f"{'N/A':<15} {'-':<10}"
        )

    def _print_summary(self, results: list[SpeedupResult]) -> None:
        """Print summary of all results."""
        avg_steps_speedup = statistics.mean(r.steps_speedup for r in results)
        avg_latency_speedup = statistics.mean(r.latency_speedup for r in results)
        avg_quality_improvement = statistics.mean(r.quality_improvement for r in results)

        print(f"\nAverage Steps Speedup:    {avg_steps_speedup:.2f}x")
        print(f"Average Latency Speedup:  {avg_latency_speedup:.2f}x")
        print(f"Average Quality Change:   {'+' if avg_quality_improvement >= 0 else ''}"
              f"{avg_quality_improvement:.3f}")
        print("\nConclusion:", end=" ")
        if avg_steps_speedup > 1.0:
            print(f"M1.11 navigation provides {avg_steps_speedup:.1f}x speedup")
        else:
            print("Baseline performs better in these scenarios")


def run_quick_benchmark() -> list[SpeedupResult]:
    """Run quick benchmark with fewer iterations."""
    print("\n" + "=" * 70)
    print("M1.11 SPEEDUP BENCHMARK (Quick Mode)")
    print("=" * 70)

    benchmark = M111SpeedupBenchmark(d_model=256)
    return benchmark.run_full_benchmark(iterations=5)


def run_full_benchmark() -> list[SpeedupResult]:
    """Run full benchmark suite."""
    print("\n" + "=" * 70)
    print("M1.11 SPEEDUP BENCHMARK (Full Mode)")
    print("=" * 70)

    benchmark = M111SpeedupBenchmark(d_model=768)
    return benchmark.run_full_benchmark(iterations=20)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_benchmark()
    else:
        run_full_benchmark()
