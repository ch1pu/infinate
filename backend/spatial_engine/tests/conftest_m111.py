"""
conftest_m111.py - M1.11 pytest fixtures for Strafe Jumping Navigation.

Provides:
- MomentumNavigator fixtures with configurable exploits
- WarpLaneDetector fixtures
- Qdrant integration fixtures for warp lane queries
- Benchmark utilities for navigation performance
- Trimmed statistics for stable benchmarking

Author: ch1pu
Milestone: 1.11 - Strafe Jumping Navigation
"""

import statistics
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Optional

import pytest
import torch

from spatial_engine.core.momentum_navigator import MomentumNavigator, NavigationResult
from spatial_engine.core.warp_lane_detector import (
    LODBoundaryOptimizer,
    ShellMemoryOrganizer,
    WarpLaneDetector,
)
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# M1.11 benchmark configuration
M111_D_MODEL = 256
M111_ATTENTION_RADIUS = 50.0
M111_MOMENTUM = 0.9
M111_WARP_THRESHOLD = 0.95


# ---------------------------------------------------------------------------
# Data Classes for M1.11 Benchmarks
# ---------------------------------------------------------------------------


@dataclass
class NavigationBenchmarkResult:
    """Results from a navigation benchmark run.

    Attributes:
        name: Benchmark name
        iterations: Number of iterations run
        total_steps: Total navigation steps taken
        total_warps: Total warps performed
        latencies_ms: List of latencies in milliseconds
        mean_latency_ms: Mean latency
        max_latency_ms: Max latency
        steps_per_second: Navigation throughput
        warps_per_iteration: Average warps per navigation
        speedup_vs_baseline: Speedup compared to baseline (if measured)
    """

    name: str
    iterations: int
    total_steps: int
    total_warps: int
    latencies_ms: list[float]
    mean_latency_ms: float
    max_latency_ms: float
    steps_per_second: float
    warps_per_iteration: float
    speedup_vs_baseline: Optional[float] = None

    def __str__(self) -> str:
        lines = [
            f"=== {self.name} ===",
            f"Iterations: {self.iterations}",
            f"Mean latency: {self.mean_latency_ms:.2f}ms",
            f"Max latency: {self.max_latency_ms:.2f}ms",
            f"Steps/sec: {self.steps_per_second:.1f}",
            f"Warps/iter: {self.warps_per_iteration:.2f}",
        ]
        if self.speedup_vs_baseline is not None:
            lines.append(f"Speedup: {self.speedup_vs_baseline:.2f}x")
        return "\n".join(lines)


@dataclass
class WarpLaneBenchmarkResult:
    """Results from warp lane detection benchmark.

    Attributes:
        name: Benchmark name
        iterations: Number of iterations
        total_warps_found: Total warp candidates found
        latencies_ms: Detection latencies
        mean_latency_ms: Mean detection time
        warps_per_query: Average warps found per query
    """

    name: str
    iterations: int
    total_warps_found: int
    latencies_ms: list[float]
    mean_latency_ms: float
    warps_per_query: float

    def __str__(self) -> str:
        return (
            f"=== {self.name} ===\n"
            f"Iterations: {self.iterations}\n"
            f"Mean latency: {self.mean_latency_ms:.3f}ms\n"
            f"Warps/query: {self.warps_per_query:.1f}"
        )


# ---------------------------------------------------------------------------
# Trimmed Statistics (from M1.9)
# ---------------------------------------------------------------------------


def trimmed_statistics(data: list[float], trim_pct: float = 0.1) -> dict:
    """Calculate trimmed statistics (excluding outliers).

    Args:
        data: List of measurements (e.g., latencies in ms)
        trim_pct: Percentage to trim from each end (default 10%)

    Returns:
        Dict with mean, std, cv, max, min, raw_max, raw_mean
    """
    if not data:
        return {"mean": 0, "std": 0, "cv": 0, "max": 0, "min": 0, "raw_max": 0, "raw_mean": 0}

    trim_count = max(1, int(len(data) * trim_pct))
    sorted_data = sorted(data)

    if len(sorted_data) > 2 * trim_count:
        trimmed = sorted_data[trim_count:-trim_count]
    else:
        trimmed = sorted_data

    mean = statistics.mean(trimmed)
    std = statistics.stdev(trimmed) if len(trimmed) > 1 else 0
    cv = (std / mean * 100) if mean > 0 else 0

    return {
        "mean": mean,
        "std": std,
        "cv": cv,
        "max": max(trimmed),
        "min": min(trimmed),
        "raw_max": max(data),
        "raw_mean": statistics.mean(data),
    }


# ---------------------------------------------------------------------------
# MomentumNavigator Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def m111_navigator() -> MomentumNavigator:
    """MomentumNavigator with all exploits enabled.

    Returns:
        MomentumNavigator configured for M1.11 benchmarks
    """
    return MomentumNavigator(
        d_model=M111_D_MODEL,
        momentum=M111_MOMENTUM,
        initial_temperature=2.0,
        final_temperature=0.5,
        warp_threshold=M111_WARP_THRESHOLD,
        max_speed=10.0,
        attention_radius=M111_ATTENTION_RADIUS,
        convergence_threshold=0.1,
    )


@pytest.fixture(scope="module")
def m111_navigator_no_warps() -> MomentumNavigator:
    """MomentumNavigator with warp lanes disabled (baseline).

    Returns:
        MomentumNavigator without warp lane exploit
    """
    nav = MomentumNavigator(
        d_model=M111_D_MODEL,
        momentum=M111_MOMENTUM,
        attention_radius=M111_ATTENTION_RADIUS,
    )
    nav.disable_exploit("warp_lanes")
    return nav


@pytest.fixture(scope="module")
def m111_navigator_minimal() -> MomentumNavigator:
    """MomentumNavigator with minimal exploits (for baseline comparison).

    Returns:
        MomentumNavigator with only basic momentum
    """
    nav = MomentumNavigator(
        d_model=M111_D_MODEL,
        momentum=M111_MOMENTUM,
        attention_radius=M111_ATTENTION_RADIUS,
    )
    nav.disable_exploit("warp_lanes")
    nav.disable_exploit("circle_jump")
    nav.disable_exploit("attention_ratchet")
    nav.disable_exploit("temperature_surfing")
    return nav


@pytest.fixture
def m111_navigator_factory() -> Callable[..., MomentumNavigator]:
    """Factory for creating navigators with specific exploit configurations.

    Yields:
        Factory function for creating configured MomentumNavigators
    """

    def create_navigator(
        d_model: int = M111_D_MODEL,
        enabled_exploits: Optional[list[str]] = None,
        disabled_exploits: Optional[list[str]] = None,
        **kwargs,
    ) -> MomentumNavigator:
        """Create navigator with specific configuration.

        Args:
            d_model: Embedding dimension
            enabled_exploits: List of exploits to enable (all if None)
            disabled_exploits: List of exploits to disable
            **kwargs: Additional navigator parameters

        Returns:
            Configured MomentumNavigator
        """
        nav = MomentumNavigator(
            d_model=d_model,
            attention_radius=kwargs.get("attention_radius", M111_ATTENTION_RADIUS),
            momentum=kwargs.get("momentum", M111_MOMENTUM),
            **{k: v for k, v in kwargs.items() if k not in ["attention_radius", "momentum"]},
        )

        if disabled_exploits:
            for exploit in disabled_exploits:
                nav.disable_exploit(exploit)

        return nav

    return create_navigator


# ---------------------------------------------------------------------------
# WarpLaneDetector Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def m111_warp_detector() -> WarpLaneDetector:
    """WarpLaneDetector for M1.11 tests.

    Returns:
        WarpLaneDetector with standard configuration
    """
    return WarpLaneDetector(
        similarity_threshold=0.5,
        attention_radius=M111_ATTENTION_RADIUS,
    )


@pytest.fixture(scope="module")
def m111_lod_optimizer() -> LODBoundaryOptimizer:
    """LODBoundaryOptimizer for M1.11 tests.

    Returns:
        LODBoundaryOptimizer with standard boundaries
    """
    return LODBoundaryOptimizer()


@pytest.fixture(scope="module")
def m111_shell_organizer() -> ShellMemoryOrganizer:
    """ShellMemoryOrganizer for M1.11 tests.

    Returns:
        ShellMemoryOrganizer with standard shell radii
    """
    return ShellMemoryOrganizer(attention_radius=M111_ATTENTION_RADIUS)


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m111_test_embeddings() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Generate test embeddings and positions for M1.11.

    Returns:
        Tuple of (query, embeddings, positions) for testing
    """
    torch.manual_seed(42)
    query = torch.randn(M111_D_MODEL)
    embeddings = torch.randn(1000, M111_D_MODEL)
    positions = torch.randn(1000, 3) * 300  # Spread across space

    return query, embeddings, positions


@pytest.fixture
def m111_semantic_embeddings() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Generate embeddings with semantic structure for warp lane testing.

    Creates embeddings where some distant tokens are similar to query,
    enabling proper warp lane detection testing.

    Returns:
        Tuple of (query, embeddings, positions) with semantic structure
    """
    torch.manual_seed(42)
    query = torch.randn(M111_D_MODEL)
    query = query / query.norm()  # Normalize

    # Create 1000 embeddings
    embeddings = torch.randn(1000, M111_D_MODEL)

    # Make some distant tokens similar to query (for warp lanes)
    # Tokens at indices 500-510 will be at distance 150-200 but similar to query
    for i in range(500, 510):
        embeddings[i] = query + torch.randn(M111_D_MODEL) * 0.1  # Very similar

    # Normalize all embeddings
    embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)

    # Create positions - spread across space
    positions = torch.randn(1000, 3) * 300

    # Place the similar tokens at warp-eligible distances (100-300 from origin)
    for i in range(500, 510):
        direction = torch.randn(3)
        direction = direction / direction.norm()
        distance = 150 + torch.rand(1).item() * 50  # 150-200 units
        positions[i] = direction * distance

    return query, embeddings, positions


# ---------------------------------------------------------------------------
# Qdrant Integration Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m111_qdrant_adapter() -> Generator[QdrantAdapter, None, None]:
    """In-memory Qdrant adapter for M1.11 tests.

    Yields:
        QdrantAdapter in memory mode
    """
    adapter = QdrantAdapter(
        collection_name=f"m111_test_{int(time.time() * 1000)}",
        d_model=M111_D_MODEL,
        use_memory=True,
    )

    yield adapter

    adapter.close()


@pytest.fixture
def m111_qdrant_with_data(
    m111_qdrant_adapter: QdrantAdapter,
    m111_semantic_embeddings: tuple[torch.Tensor, torch.Tensor, torch.Tensor],
) -> tuple[QdrantAdapter, torch.Tensor]:
    """Qdrant adapter pre-populated with semantic test data.

    Args:
        m111_qdrant_adapter: Empty adapter
        m111_semantic_embeddings: Test data with semantic structure

    Returns:
        Tuple of (adapter, query) ready for testing
    """
    query, embeddings, positions = m111_semantic_embeddings

    # Store embeddings
    m111_qdrant_adapter.store(embeddings, positions)

    return m111_qdrant_adapter, query


@pytest.fixture
def m111_qdrant_container() -> Generator[Optional[QdrantAdapter], None, None]:
    """Qdrant adapter connecting to Docker container (if available).

    Yields:
        QdrantAdapter connected to container, or None if unavailable
    """
    try:
        adapter = QdrantAdapter(
            collection_name=f"m111_container_test_{int(time.time() * 1000)}",
            d_model=M111_D_MODEL,
            url="http://localhost:6333",
        )
        yield adapter
        adapter.close()
    except Exception:
        yield None


# ---------------------------------------------------------------------------
# Benchmark Runner Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m111_benchmark_runner() -> "M111BenchmarkRunner":
    """Benchmark runner for M1.11 navigation tests.

    Returns:
        M111BenchmarkRunner instance
    """
    return M111BenchmarkRunner()


class M111BenchmarkRunner:
    """Runner for M1.11 navigation benchmarks.

    Provides methods to benchmark:
    - MomentumNavigator with various configurations
    - WarpLaneDetector performance
    - Baseline vs exploits comparison
    """

    def run_navigation_benchmark(
        self,
        navigator: MomentumNavigator,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        iterations: int = 100,
        max_steps: int = 10,
        warmup: int = 5,
    ) -> NavigationBenchmarkResult:
        """Run navigation benchmark.

        Args:
            navigator: MomentumNavigator to benchmark
            query: Query embedding
            embeddings: Context embeddings
            positions: Context positions
            iterations: Number of iterations
            max_steps: Max steps per navigation
            warmup: Warmup iterations

        Returns:
            NavigationBenchmarkResult with timing data
        """
        # Warmup
        for _ in range(warmup):
            navigator.navigate(
                query,
                max_steps=max_steps,
                context_embeddings=embeddings,
                context_positions=positions,
            )

        # Benchmark
        latencies: list[float] = []
        total_steps = 0
        total_warps = 0

        for _ in range(iterations):
            start = time.perf_counter()
            result = navigator.navigate(
                query,
                max_steps=max_steps,
                context_embeddings=embeddings,
                context_positions=positions,
            )
            latencies.append((time.perf_counter() - start) * 1000)
            total_steps += result.steps_taken
            total_warps += result.warp_count

        total_time_s = sum(latencies) / 1000

        return NavigationBenchmarkResult(
            name=f"MomentumNavigator ({len(navigator.get_enabled_exploits())} exploits)",
            iterations=iterations,
            total_steps=total_steps,
            total_warps=total_warps,
            latencies_ms=latencies,
            mean_latency_ms=statistics.mean(latencies),
            max_latency_ms=max(latencies),
            steps_per_second=total_steps / total_time_s if total_time_s > 0 else 0,
            warps_per_iteration=total_warps / iterations,
        )

    def run_warp_detection_benchmark(
        self,
        detector: WarpLaneDetector,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        current_position: torch.Tensor,
        iterations: int = 100,
        warmup: int = 5,
    ) -> WarpLaneBenchmarkResult:
        """Run warp lane detection benchmark.

        Args:
            detector: WarpLaneDetector to benchmark
            query: Query embedding
            embeddings: All embeddings
            positions: All positions
            current_position: Current position
            iterations: Number of iterations
            warmup: Warmup iterations

        Returns:
            WarpLaneBenchmarkResult with timing data
        """
        # Warmup
        for _ in range(warmup):
            detector.find_warp_targets(query, embeddings, positions, current_position)

        # Benchmark
        latencies: list[float] = []
        total_warps = 0

        for _ in range(iterations):
            start = time.perf_counter()
            mask = detector.find_warp_targets(query, embeddings, positions, current_position)
            latencies.append((time.perf_counter() - start) * 1000)
            total_warps += mask.sum().item()

        return WarpLaneBenchmarkResult(
            name="WarpLaneDetector",
            iterations=iterations,
            total_warps_found=int(total_warps),
            latencies_ms=latencies,
            mean_latency_ms=statistics.mean(latencies),
            warps_per_query=total_warps / iterations,
        )

    def compare_exploits(
        self,
        query: torch.Tensor,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        iterations: int = 50,
    ) -> dict:
        """Compare navigation with all exploits vs minimal exploits.

        Args:
            query: Query embedding
            embeddings: Context embeddings
            positions: Context positions
            iterations: Number of iterations

        Returns:
            Dict with comparison results
        """
        # Navigator with all exploits
        nav_all = MomentumNavigator(d_model=query.shape[0])

        # Navigator with minimal exploits
        nav_min = MomentumNavigator(d_model=query.shape[0])
        nav_min.disable_exploit("warp_lanes")
        nav_min.disable_exploit("circle_jump")
        nav_min.disable_exploit("attention_ratchet")

        # Benchmark both
        result_all = self.run_navigation_benchmark(
            nav_all, query, embeddings, positions, iterations=iterations
        )
        result_min = self.run_navigation_benchmark(
            nav_min, query, embeddings, positions, iterations=iterations
        )

        # Calculate speedup (based on steps, not raw time - exploits improve quality)
        steps_ratio = result_min.total_steps / result_all.total_steps if result_all.total_steps > 0 else 1.0

        return {
            "all_exploits": result_all,
            "minimal_exploits": result_min,
            "steps_reduction": 1 - (result_all.total_steps / result_min.total_steps) if result_min.total_steps > 0 else 0,
            "warps_enabled": result_all.total_warps,
            "quality_improvement": steps_ratio,
        }


# ---------------------------------------------------------------------------
# Pytest Marker Configuration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register M1.11 markers."""
    config.addinivalue_line("markers", "m111: M1.11 Strafe Jumping Navigation tests")
    config.addinivalue_line("markers", "m111_benchmark: M1.11 benchmark tests")
    config.addinivalue_line("markers", "m111_integration: M1.11 integration tests")
    config.addinivalue_line("markers", "m111_qdrant: M1.11 Qdrant integration tests")
