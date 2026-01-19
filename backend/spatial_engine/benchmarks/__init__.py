"""
benchmarks - MIT RLM comparison and extended benchmarking utilities.

Milestone: 1.8 - Extended Benchmarking & MIT RLM Comparison
Author: ch1pu

Provides utilities for:
- Comparison against MIT Recursive Language Models (arXiv 2512.24601)
- Extended scaling benchmarks up to 128K tokens
- Determinism and variance testing
- Memory and throughput analysis
"""

from spatial_engine.benchmarks.mit_comparison import (
    BenchmarkResult,
    MITBenchmarkRunner,
    MITComparison,
    MITReference,
)

__all__ = [
    "BenchmarkResult",
    "MITBenchmarkRunner",
    "MITComparison",
    "MITReference",
]
