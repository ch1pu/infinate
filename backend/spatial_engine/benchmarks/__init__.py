"""
benchmarks - MIT RLM comparison, M1.11 navigation benchmarks, and extended utilities.

Milestones:
- 1.8 - Extended Benchmarking & MIT RLM Comparison
- 1.11 - Strafe Jumping Navigation Benchmarks

Author: ch1pu

Provides utilities for:
- Comparison against MIT Recursive Language Models (arXiv 2512.24601)
- Extended scaling benchmarks up to 128K tokens
- Determinism and variance testing
- Memory and throughput analysis
- M1.11: Navigation benchmarks (momentum, warp lanes, LOD, shell memory)
"""

from spatial_engine.benchmarks.mit_comparison import (
    BenchmarkResult,
    MITBenchmarkRunner,
    MITComparison,
    MITReference,
)
from spatial_engine.benchmarks.navigation_benchmarks import (
    benchmark_distance_range_filtering,
    benchmark_lod_optimization,
    benchmark_momentum_navigator,
    benchmark_shell_memory,
    benchmark_warp_lane_detection,
    compare_with_baseline,
    run_all_benchmarks,
)

__all__ = [
    # MIT comparison (M1.8)
    "BenchmarkResult",
    "MITBenchmarkRunner",
    "MITComparison",
    "MITReference",
    # Navigation benchmarks (M1.11)
    "benchmark_distance_range_filtering",
    "benchmark_lod_optimization",
    "benchmark_momentum_navigator",
    "benchmark_shell_memory",
    "benchmark_warp_lane_detection",
    "compare_with_baseline",
    "run_all_benchmarks",
]
