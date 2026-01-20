"""
navigation_benchmarks.py - Benchmarks for M1.11 Strafe Jumping Navigation.

Measures performance improvements from the 7 validated exploits:
1. Warp Lanes (Exploit 1)
2. Shell Memory (Exploit 2)
3. LOD Hopping (Exploit 3)
6. Bunny Hop Momentum (Exploit 6)
7. Circle Jump (Exploit 7)
8. Temperature Surfing (Exploit 8)
9. Attention Ratchet (Exploit 9)

Expected Performance (Revised After Validation):
- Speed boost: 1.5-1.7× (not 2.1× - diagonal speed invalidated)
- Tokens/step: ~65 (not 70)
- Accuracy: 78-80% (not 82%)

Author: Adolfo Lopez (ch1pu)
Milestone: 1.11 - Strafe Jumping Navigation
"""

import time
from dataclasses import dataclass
from typing import Optional

import torch


@dataclass
class BenchmarkResult:
    """Results from a navigation benchmark.

    Attributes:
        name: Benchmark name
        iterations: Number of iterations run
        total_time_ms: Total time in milliseconds
        avg_time_ms: Average time per iteration
        steps_per_second: Navigation steps per second
        tokens_accessed: Average tokens accessed per step
        accuracy: Accuracy if measured (None otherwise)
        speedup_vs_baseline: Speedup compared to baseline
    """

    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    steps_per_second: float
    tokens_accessed: Optional[float] = None
    accuracy: Optional[float] = None
    speedup_vs_baseline: Optional[float] = None

    def __str__(self) -> str:
        lines = [
            f"=== {self.name} ===",
            f"Iterations: {self.iterations}",
            f"Total time: {self.total_time_ms:.2f}ms",
            f"Avg time: {self.avg_time_ms:.4f}ms/iter",
            f"Steps/sec: {self.steps_per_second:.1f}",
        ]
        if self.tokens_accessed is not None:
            lines.append(f"Tokens/step: {self.tokens_accessed:.1f}")
        if self.accuracy is not None:
            lines.append(f"Accuracy: {self.accuracy:.1%}")
        if self.speedup_vs_baseline is not None:
            lines.append(f"Speedup: {self.speedup_vs_baseline:.2f}×")
        return "\n".join(lines)


def benchmark_momentum_navigator(
    d_model: int = 256,
    num_tokens: int = 1000,
    iterations: int = 100,
    max_steps: int = 10,
) -> BenchmarkResult:
    """Benchmark MomentumNavigator performance.

    Args:
        d_model: Embedding dimension
        num_tokens: Number of context tokens
        iterations: Number of benchmark iterations
        max_steps: Maximum navigation steps per iteration

    Returns:
        BenchmarkResult with timing data
    """
    from spatial_engine.core.momentum_navigator import MomentumNavigator

    nav = MomentumNavigator(d_model=d_model)

    # Create test data
    query = torch.randn(d_model)
    embeddings = torch.randn(num_tokens, d_model)
    positions = torch.randn(num_tokens, 3) * 300

    # Warmup
    for _ in range(5):
        nav.navigate(query, max_steps=max_steps, context_embeddings=embeddings, context_positions=positions)

    # Benchmark
    start = time.perf_counter()
    total_steps = 0

    for _ in range(iterations):
        result = nav.navigate(
            query, max_steps=max_steps, context_embeddings=embeddings, context_positions=positions
        )
        total_steps += result.steps_taken

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        name="MomentumNavigator (all exploits)",
        iterations=iterations,
        total_time_ms=elapsed_ms,
        avg_time_ms=elapsed_ms / iterations,
        steps_per_second=(total_steps / (elapsed_ms / 1000)),
    )


def benchmark_warp_lane_detection(
    d_model: int = 256,
    num_tokens: int = 1000,
    iterations: int = 100,
) -> BenchmarkResult:
    """Benchmark WarpLaneDetector performance.

    Args:
        d_model: Embedding dimension
        num_tokens: Number of tokens to search
        iterations: Number of benchmark iterations

    Returns:
        BenchmarkResult with timing data
    """
    from spatial_engine.core.warp_lane_detector import WarpLaneDetector

    detector = WarpLaneDetector(similarity_threshold=0.5, attention_radius=50.0)

    # Create test data
    query = torch.randn(d_model)
    embeddings = torch.randn(num_tokens, d_model)
    positions = torch.randn(num_tokens, 3) * 300
    current_position = torch.zeros(3)

    # Warmup
    for _ in range(5):
        detector.find_warp_targets(query, embeddings, positions, current_position)

    # Benchmark
    start = time.perf_counter()
    total_warps_found = 0

    for _ in range(iterations):
        mask = detector.find_warp_targets(query, embeddings, positions, current_position)
        total_warps_found += mask.sum().item()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        name="WarpLaneDetector",
        iterations=iterations,
        total_time_ms=elapsed_ms,
        avg_time_ms=elapsed_ms / iterations,
        steps_per_second=iterations / (elapsed_ms / 1000),
        tokens_accessed=total_warps_found / iterations,
    )


def benchmark_lod_optimization(
    num_tokens: int = 1000,
    iterations: int = 100,
) -> BenchmarkResult:
    """Benchmark LODBoundaryOptimizer performance.

    Args:
        num_tokens: Number of tokens to optimize
        iterations: Number of benchmark iterations

    Returns:
        BenchmarkResult with timing data
    """
    from spatial_engine.core.warp_lane_detector import LODBoundaryOptimizer

    optimizer = LODBoundaryOptimizer()

    # Create test data
    positions = torch.randn(num_tokens, 3) * 200
    focus_position = torch.zeros(3)

    # Warmup
    for _ in range(5):
        optimizer.optimize(positions, focus_position)

    # Benchmark
    start = time.perf_counter()

    for _ in range(iterations):
        optimizer.optimize(positions, focus_position)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        name="LODBoundaryOptimizer",
        iterations=iterations,
        total_time_ms=elapsed_ms,
        avg_time_ms=elapsed_ms / iterations,
        steps_per_second=iterations / (elapsed_ms / 1000),
    )


def benchmark_shell_memory(
    d_model: int = 256,
    num_tokens: int = 1000,
    iterations: int = 100,
) -> BenchmarkResult:
    """Benchmark ShellMemoryOrganizer performance.

    Args:
        d_model: Embedding dimension
        num_tokens: Number of tokens to place
        iterations: Number of benchmark iterations

    Returns:
        BenchmarkResult with timing data
    """
    from spatial_engine.core.warp_lane_detector import ShellMemoryOrganizer

    organizer = ShellMemoryOrganizer(attention_radius=50.0)

    # Create test data
    embeddings = torch.randn(num_tokens, d_model)
    priorities = torch.randint(0, 3, (num_tokens,))
    focus_position = torch.zeros(3)

    # Warmup
    for _ in range(5):
        organizer.place_tokens(embeddings, priorities, focus_position)

    # Benchmark
    start = time.perf_counter()

    for _ in range(iterations):
        organizer.place_tokens(embeddings, priorities, focus_position)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        name="ShellMemoryOrganizer",
        iterations=iterations,
        total_time_ms=elapsed_ms,
        avg_time_ms=elapsed_ms / iterations,
        steps_per_second=iterations / (elapsed_ms / 1000),
    )


def benchmark_distance_range_filtering(
    num_tokens: int = 10000,
    iterations: int = 100,
) -> BenchmarkResult:
    """Benchmark distance range filtering (M1.11 spatial_index addition).

    Args:
        num_tokens: Number of tokens to filter
        iterations: Number of benchmark iterations

    Returns:
        BenchmarkResult with timing data
    """
    from spatial_engine.vector_store.spatial_index import find_k_nearest_in_range

    # Create test data
    positions = torch.randn(num_tokens, 3) * 500
    query_position = torch.zeros(3)

    # Warmup
    for _ in range(5):
        find_k_nearest_in_range(query_position, positions, k=50, min_distance=100.0, max_distance=400.0)

    # Benchmark
    start = time.perf_counter()
    total_found = 0

    for _ in range(iterations):
        result_pos, result_idx = find_k_nearest_in_range(
            query_position, positions, k=50, min_distance=100.0, max_distance=400.0
        )
        total_found += len(result_idx)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return BenchmarkResult(
        name="Distance Range Filtering",
        iterations=iterations,
        total_time_ms=elapsed_ms,
        avg_time_ms=elapsed_ms / iterations,
        steps_per_second=iterations / (elapsed_ms / 1000),
        tokens_accessed=total_found / iterations,
    )


def run_all_benchmarks(verbose: bool = True) -> list[BenchmarkResult]:
    """Run all M1.11 navigation benchmarks.

    Args:
        verbose: Whether to print results

    Returns:
        List of BenchmarkResult objects
    """
    results = []

    if verbose:
        print("\n" + "=" * 60)
        print("M1.11 STRAFE JUMPING NAVIGATION BENCHMARKS")
        print("=" * 60 + "\n")

    # Run each benchmark
    benchmarks = [
        ("MomentumNavigator", benchmark_momentum_navigator),
        ("WarpLaneDetector", benchmark_warp_lane_detection),
        ("LODBoundaryOptimizer", benchmark_lod_optimization),
        ("ShellMemoryOrganizer", benchmark_shell_memory),
        ("Distance Range Filtering", benchmark_distance_range_filtering),
    ]

    for name, benchmark_fn in benchmarks:
        if verbose:
            print(f"Running {name}...")
        result = benchmark_fn()
        results.append(result)
        if verbose:
            print(result)
            print()

    if verbose:
        print("=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        for result in results:
            print(f"{result.name}: {result.avg_time_ms:.4f}ms/iter")

    return results


def compare_with_baseline(
    d_model: int = 256,
    num_tokens: int = 1000,
    iterations: int = 50,
) -> dict:
    """Compare MomentumNavigator with baseline navigation.

    Baseline = simple gradient descent without exploits.

    Args:
        d_model: Embedding dimension
        num_tokens: Number of context tokens
        iterations: Number of benchmark iterations

    Returns:
        Dict with comparison metrics
    """
    from spatial_engine.core.momentum_navigator import MomentumNavigator

    nav = MomentumNavigator(d_model=d_model)

    query = torch.randn(d_model)
    embeddings = torch.randn(num_tokens, d_model)
    positions = torch.randn(num_tokens, 3) * 300

    # Run with all exploits enabled
    start = time.perf_counter()
    total_steps_all = 0
    total_warps_all = 0

    for _ in range(iterations):
        result = nav.navigate(
            query, max_steps=10, context_embeddings=embeddings, context_positions=positions
        )
        total_steps_all += result.steps_taken
        total_warps_all += result.warp_count

    time_all = (time.perf_counter() - start) * 1000

    # Run with minimal exploits (disable warp lanes, circle jump)
    nav.disable_exploit("warp_lanes")
    nav.disable_exploit("circle_jump")
    nav.disable_exploit("attention_ratchet")

    start = time.perf_counter()
    total_steps_min = 0

    for _ in range(iterations):
        result = nav.navigate(
            query, max_steps=10, use_circle_jump=False, context_embeddings=embeddings, context_positions=positions
        )
        total_steps_min += result.steps_taken

    time_min = (time.perf_counter() - start) * 1000

    return {
        "all_exploits_time_ms": time_all,
        "minimal_exploits_time_ms": time_min,
        "speedup": time_min / time_all if time_all > 0 else 1.0,
        "avg_warps_per_iter": total_warps_all / iterations,
        "steps_per_iter_all": total_steps_all / iterations,
        "steps_per_iter_min": total_steps_min / iterations,
    }


# Main entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run M1.11 navigation benchmarks")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmarks (fewer iterations)")
    args = parser.parse_args()

    iterations = 20 if args.quick else 100

    # Run all benchmarks
    results = run_all_benchmarks(verbose=True)

    # Run comparison
    print("\n" + "=" * 60)
    print("BASELINE COMPARISON")
    print("=" * 60)

    comparison = compare_with_baseline(iterations=iterations // 2)
    print(f"All exploits time: {comparison['all_exploits_time_ms']:.2f}ms")
    print(f"Minimal exploits time: {comparison['minimal_exploits_time_ms']:.2f}ms")
    print(f"Speedup with exploits: {comparison['speedup']:.2f}×")
    print(f"Average warps per iteration: {comparison['avg_warps_per_iter']:.1f}")
